# PolicyPal - Intelligent Insurance Policy Explainer

A full-stack web application that uses Graph-based Retrieval-Augmented Generation (GraphRAG) to help users understand their insurance policies. Upload PDF documents and ask questions in plain English to get accurate answers with exact clause citations.

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend       │────▶│   Databases     │
│   (Next.js)     │     │   (FastAPI)     │     │                 │
│                 │     │                 │     │  ┌───────────┐  │
│  • PdfUpload    │     │  • PDF Processor│     │  │  Neo4j    │  │
│  • ChatSection  │     │  • Graph Service│     │  │  (Graph)  │  │
│  • CitationCard │     │  • Vector Svc   │     │  └───────────┘  │
│                 │     │  • RAG Engine   │     │  ┌───────────┐  │
│                 │     │                 │     │  │  Qdrant   │  │
└─────────────────┘     └─────────────────┘     │  │ (Vector)  │  │
                                                │  └───────────┘  │
                                                └─────────────────┘
```

## 🚀 Features

- **PDF Upload & Processing**: Drag-and-drop PDF upload with text extraction (PyMuPDF) and OCR fallback (GPT-4o-mini Vision)
- **GraphRAG Pipeline**: Hybrid retrieval combining vector search (Qdrant) + graph traversal (Neo4j)
- **Entity Extraction**: Automatic extraction of Sections, Clauses, Conditions, Exclusions, Waiting Periods, Benefits
- **Citation Cards**: Interactive expandable citations showing exact policy text
- **Real-time Status**: Live processing status (Extracting → Graph Building → Indexing)
- **Conversational Chat**: Multi-turn Q&A with context awareness

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, Lucide Icons |
| Backend | FastAPI, Python 3.10+, Pydantic, Uvicorn |
| Vector DB | Qdrant (via qdrant-client) |
| Graph DB | Neo4j (via neo4j Python driver) |
| LLM/Embeddings | OpenRouter API (GPT-4o-mini, text-embedding-3-small) |
| PDF Processing | PyMuPDF (fitz), pdf2image, Pillow |

## 📁 Project Structure

```
policypal/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point & API routes
│   │   ├── config.py            # Environment configuration
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic models
│   │   └── services/
│   │       ├── pdf_processor.py # PDF text extraction & OCR
│   │       ├── graph_service.py # Neo4j graph operations
│   │       ├── vector_service.py# Qdrant vector operations
│   │       └── rag_engine.py    # GraphRAG query pipeline
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         # Main dashboard
│   │   │   ├── layout.tsx       # Root layout
│   │   │   └── globals.css      # Global styles
│   │   └── components/
│   │       ├── PdfUpload.tsx    # Drag-drop upload component
│   │       ├── ChatSection.tsx  # Chat interface
│   │       └── CitationCard.tsx # Citation display
│   ├── package.json
│   └── tailwind.config.js
└── README.md
```

## ⚙️ Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Neo4j (local or AuraDB)
- Qdrant (local or cloud)
- OpenRouter API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment (optional)
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run development server
npm run dev
```

### Environment Variables

**Backend (.env)**
```env
# OpenRouter
OPENROUTER_API_KEY=your_openrouter_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_key
QDRANT_COLLECTION=policy_chunks
VECTOR_SIZE=1536

# App
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
MAX_FILE_SIZE=52428800
```

**Frontend (.env.local)**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload PDF for processing |
| GET | `/api/status/{document_id}` | Check processing status |
| POST | `/api/chat` | Ask question about policy |
| GET | `/api/health` | Health check (Qdrant + Neo4j) |
| DELETE | `/api/document/{document_id}` | Delete document data |

### Example Requests

**Upload PDF**
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@policy.pdf"
```

**Chat**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"document_id": "uuid", "question": "Does this cover dental?"}'
```

**Response**
```json
{
  "answer": "Yes, dental surgery is covered under Section 3.2...",
  "citations": [
    {
      "section_id": "Section 3",
      "clause_name": "Clause 3.2 - Dental Coverage",
      "text_snippet": "Dental surgery up to ₹50,000 per year..."
    }
  ]
}
```

## 🔄 GraphRAG Pipeline

1. **Ingestion**
   - Extract text per page (PyMuPDF)
   - OCR fallback for scanned pages (GPT-4o-mini Vision)
   - Chunk by sections/clauses with overlap
   - Extract entities & relationships via LLM
   - Store nodes/edges in Neo4j
   - Embed chunks & store in Qdrant with metadata

2. **Query**
   - Vector search in Qdrant (top-k chunks)
   - Extract Neo4j node IDs from results
   - 1-hop graph traversal for connected conditions/exclusions/waiting periods
   - Combine vector + graph context
   - Generate structured response via LLM

## 🎨 UI Components

- **PdfUpload**: Drag-drop zone with progress steps
- **ChatSection**: Message bubbles with citations
- **CitationCard**: Expandable cards with clause text
- **Health Badges**: Live DB connection status

## 📝 License

MIT License - feel free to use for personal or commercial projects.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a PR

## 📧 Support

For issues and questions, please open a GitHub issue.