import logging
import uuid
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.schemas import (
    UploadResponse, ChatRequest, ChatResponse, HealthResponse, DocumentStatusResponse, DocumentStatus
)
from app.services.pdf_processor import PDFProcessor
from app.services.graph_service import GraphService
from app.services.vector_service import VectorService
from app.services.rag_engine import RAGEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services
pdf_processor: PDFProcessor = None
graph_service: GraphService = None
vector_service: VectorService = None
rag_engine: RAGEngine = None

# In-memory document status tracking (use Redis in production)
document_status: Dict[str, DocumentStatusResponse] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global pdf_processor, graph_service, vector_service, rag_engine

    logger.info("Starting PolicyPal backend...")

    # Initialize services
    pdf_processor = PDFProcessor()
    graph_service = GraphService()
    vector_service = VectorService()
    rag_engine = RAGEngine()

    # Initialize Qdrant collection
    vector_service.initialize_collection()

    logger.info("PolicyPal backend started successfully")
    yield

    # Cleanup
    logger.info("Shutting down PolicyPal backend...")
    graph_service.close()


app = FastAPI(
    title="PolicyPal API",
    description="Intelligent Insurance Policy Explainer with GraphRAG",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def process_document_background(document_id: str, file_content: bytes, filename: str):
    """Background task to process uploaded document."""
    try:
        # Update status: Extracting text
        document_status[document_id] = DocumentStatusResponse(
            document_id=document_id,
            filename=filename,
            status=DocumentStatus.PROCESSING,
            message="Extracting text from PDF...",
            progress=10,
            created_at=datetime.utcnow()
        )

        # Process PDF
        result = pdf_processor.process_pdf(file_content, filename, document_id)

        # Update status: Building graph
        document_status[document_id] = DocumentStatusResponse(
            document_id=document_id,
            filename=filename,
            status=DocumentStatus.PROCESSING,
            message="Building knowledge graph...",
            progress=40,
            created_at=datetime.utcnow()
        )

        # Extract entities and relationships
        # Convert chunk dicts to DocumentChunk objects
        from app.services.pdf_processor import DocumentChunk
        doc_chunks = []
        for idx, chunk in enumerate(result["chunks"]):
            doc_chunk = DocumentChunk(
                chunk_id=str(uuid.uuid4()),
                document_id=document_id,
                text=chunk["text"],
                page_number=chunk.get("page_number", 0),
                section_title=chunk.get("clause_name") or None,
                chunk_index=idx
            )
            doc_chunks.append(doc_chunk)
        
        extraction_result = graph_service.extract_entities_and_relationships(doc_chunks)

        # Store in Neo4j
        node_ids = graph_service.store_graph(document_id, extraction_result)

        # Update status: Indexing vectors
        document_status[document_id] = DocumentStatusResponse(
            document_id=document_id,
            filename=filename,
            status=DocumentStatus.PROCESSING,
            message="Indexing vector embeddings...",
            progress=70,
            created_at=datetime.utcnow()
        )

        # Prepare chunks for vector storage
        vector_chunks = []
        for i, chunk in enumerate(result["chunks"]):
            neo4j_node_id = node_ids[i] if i < len(node_ids) else ""
            vector_chunks.append({
                "text": chunk["text"],
                "section_id": chunk.get("section_id", ""),
                "clause_number": chunk.get("clause_number", ""),
                "clause_name": chunk.get("clause_name", ""),
                "neo4j_node_id": neo4j_node_id,
                "page_number": chunk.get("page_number", 0)
            })

        # Store in Qdrant (handles empty chunks internally) - async
        if vector_chunks:
            await vector_service.store_chunks(document_id, vector_chunks)
            logger.info(f"Stored {len(vector_chunks)} chunks in Qdrant")
        else:
            logger.warning(f"No chunks to store for document {document_id}")

        # Mark complete
        document_status[document_id] = DocumentStatusResponse(
            document_id=document_id,
            filename=filename,
            status=DocumentStatus.COMPLETED,
            message="Document processed successfully!",
            progress=100,
            created_at=datetime.utcnow()
        )

        logger.info(f"Document {document_id} processed successfully")

    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        document_status[document_id] = DocumentStatusResponse(
            document_id=document_id,
            filename=filename,
            status=DocumentStatus.FAILED,
            message=f"Processing failed: {str(e)}",
            progress=0,
            created_at=datetime.utcnow()
        )


@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a PDF insurance policy document for processing.
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Generate document ID
    document_id = str(uuid.uuid4())
    filename = file.filename

    # Read file content
    file_content = await file.read()

    # Validate file size (max 50MB)
    if len(file_content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")

    # Initialize status
    document_status[document_id] = DocumentStatusResponse(
        document_id=document_id,
        filename=filename,
        status=DocumentStatus.PROCESSING,
        message="Document queued for processing",
        progress=0,
        created_at=datetime.utcnow()
    )

    # Start background processing
    background_tasks.add_task(
        process_document_background,
        document_id,
        file_content,
        filename
    )

    return UploadResponse(
        document_id=document_id,
        filename=filename,
        status=DocumentStatus.PROCESSING,
        message="Document uploaded successfully. Processing started in background."
    )


@app.get("/api/status/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str):
    """Get the processing status of a document."""
    if document_id not in document_status:
        raise HTTPException(status_code=404, detail="Document not found")

    return document_status[document_id]


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_policy(request: ChatRequest):
    """
    Ask a question about an uploaded policy document.
    """
    # Verify document exists and is processed
    if request.document_id not in document_status:
        raise HTTPException(status_code=404, detail="Document not found")

    status = document_status[request.document_id]
    if status.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Document is not ready. Current status: {status.status}"
        )

    # Process query through GraphRAG (async)
    try:
        response = await rag_engine.process_query(
            question=request.question,
            document_id=request.document_id
        )
        return response
    except Exception as e:
        logger.error(f"Chat query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    import datetime

    qdrant_ok = vector_service.health_check()
    neo4j_ok = graph_service.health_check()

    return HealthResponse(
        status="healthy" if (qdrant_ok and neo4j_ok) else "degraded",
        version="1.0.0",
        services={
            "qdrant": "connected" if qdrant_ok else "disconnected",
            "neo4j": "connected" if neo4j_ok else "disconnected"
        }
    )


@app.delete("/api/document/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its data."""
    if document_id not in document_status:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from vector store
    vector_service.delete_document(document_id)

    # Delete from graph store
    graph_service.clear_document(document_id)

    # Remove status
    del document_status[document_id]

    return {"success": True, "message": "Document deleted successfully"}


@app.get("/api/graph/{document_id}")
async def get_graph_data(document_id: str):
    """Get graph visualization data for a document."""
    if document_id not in document_status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        graph_data = graph_service.get_graph_for_visualization(document_id)
        return graph_data
    except Exception as e:
        logger.error(f"Failed to get graph data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)