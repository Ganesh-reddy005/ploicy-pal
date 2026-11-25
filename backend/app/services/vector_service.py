import uuid
import logging
import asyncio
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue,
    PayloadSchemaType, CreateFieldIndex
)
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class VectorService:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key
        )
        self.openai_client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.collection_name = settings.qdrant_collection
        self.embedding_model = settings.openai_embedding_model
        self.vector_size = settings.vector_size
        self.batch_size = 10  # Process 10 embeddings concurrently

    def initialize_collection(self):
        """Create collection if it doesn't exist and ensure payload indexes."""
        try:
            collections = self.client.get_collections().collections
            collection_exists = any(c.name == self.collection_name for c in collections)
            
            if not collection_exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
            
            # Create payload index for document_id (required for filtering)
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="document_id",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                logger.info("Created payload index for document_id")
            except Exception as e:
                # Index might already exist
                logger.debug(f"Payload index creation skipped: {e}")
                
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise

    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenRouter (async)."""
        try:
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts concurrently."""
        try:
            # Process in batches to avoid rate limits
            all_embeddings = []
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                # Create concurrent tasks for this batch
                tasks = [self.get_embedding(text) for text in batch]
                batch_embeddings = await asyncio.gather(*tasks)
                all_embeddings.extend(batch_embeddings)
                logger.info(f"Generated embeddings for batch {i//self.batch_size + 1}/{(len(texts)-1)//self.batch_size + 1}")
            return all_embeddings
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise

    async def store_chunks(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Store text chunks with embeddings in Qdrant (async).
        Each chunk should have: text, section_id, clause_number, clause_name, neo4j_node_id
        Returns list of point IDs.
        """
        self.initialize_collection()

        # Filter out empty chunks
        valid_chunks = [c for c in chunks if c.get("text", "").strip()]
        
        if not valid_chunks:
            logger.warning(f"No valid chunks to store for document {document_id}")
            return []

        # Extract texts and generate embeddings concurrently
        texts = [chunk["text"] for chunk in valid_chunks]
        logger.info(f"Generating {len(texts)} embeddings concurrently...")
        embeddings = await self.get_embeddings_batch(texts)

        # Prepare points
        points = []
        point_ids = []

        for chunk, embedding in zip(valid_chunks, embeddings):
            point_id = str(uuid.uuid4())
            point_ids.append(point_id)

            # Prepare payload
            payload = {
                "document_id": document_id,
                "text": chunk["text"],
                "section_id": chunk.get("section_id", ""),
                "clause_number": chunk.get("clause_number", ""),
                "clause_name": chunk.get("clause_name", ""),
                "neo4j_node_id": chunk.get("neo4j_node_id", ""),
                "page_number": chunk.get("page_number", 0)
            }

            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            ))

        # Batch upsert
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        logger.info(f"Stored {len(points)} chunks for document {document_id}")
        return point_ids

    async def search(
        self,
        query: str,
        document_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks using vector similarity (async).
        Returns list of chunks with scores and payloads.
        """
        query_embedding = await self.get_embedding(query)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            ),
            limit=limit,
            with_payload=True
        )

        chunks = []
        for hit in results:
            chunks.append({
                "id": hit.id,
                "score": hit.score,
                "text": hit.payload.get("text", ""),
                "section_id": hit.payload.get("section_id", ""),
                "clause_number": hit.payload.get("clause_number", ""),
                "clause_name": hit.payload.get("clause_name", ""),
                "neo4j_node_id": hit.payload.get("neo4j_node_id", ""),
                "page_number": hit.payload.get("page_number", 0)
            })

        return chunks

    def delete_document(self, document_id: str):
        """Delete all chunks for a document."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )
        logger.info(f"Deleted chunks for document {document_id}")

    def health_check(self) -> bool:
        """Check Qdrant connectivity."""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False