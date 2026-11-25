# PolicyPal Setup Guide

## Quick Start (If Qdrant index error occurs)

If you see this error:
```
Index required but not found for "document_id"
```

Run this command:
```bash
cd backend
python reset_qdrant.py
```

Then restart your backend server.

---

## Complete Setup Instructions

### 1. Backend Setup

```bash
cd backend

# Install/upgrade dependencies
pip install -r requirements.txt --upgrade

# Configure environment variables
cp .env.example .env
# Edit .env with your credentials (see below)

# Optional: Reset Qdrant collection with proper indexes
python reset_qdrant.py

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Optional: Configure API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev
```

---

## Environment Variables

### Backend `.env`

```env
# OpenRouter API
OPENROUTER_API_KEY=sk-or-v1-xxx
OPENAI_MODEL=openai/gpt-4o-mini
OPENAI_EMBEDDING_MODEL=openai/text-embedding-3-small

# Neo4j Graph Database
NEO4J_URI=bolt://localhost:7687
# OR Neo4j AuraDB:
# NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Qdrant Vector Database
QDRANT_URL=http://localhost:6333
# OR Qdrant Cloud:
# QDRANT_URL=https://xxx.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_key
QDRANT_COLLECTION=policy_pal_documents
VECTOR_SIZE=1536

# App Config
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
MAX_FILE_SIZE=52428800
```

### Frontend `.env.local` (optional)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Running the Services

### Option 1: Local Development

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Access at: http://localhost:3000

### Option 2: Production Build

**Backend:**
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run build
npm start
```

---

## Database Setup

### Neo4j

**Option A: Docker (Local)**
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/yourpassword \
  neo4j:latest
```

**Option B: Neo4j AuraDB (Cloud)**
1. Sign up at https://neo4j.com/cloud/aura/
2. Create a free instance
3. Copy connection URI and credentials
4. Update `.env` with AuraDB credentials

### Qdrant

**Option A: Docker (Local)**
```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```

**Option B: Qdrant Cloud**
1. Sign up at https://qdrant.tech/
2. Create a cluster
3. Copy API URL and key
4. Update `.env` with Qdrant Cloud credentials

---

## Troubleshooting

### Issue: "Index required but not found for document_id"
**Solution:**
```bash
cd backend
python reset_qdrant.py
```

### Issue: Neo4j connection failed
**Check:**
- Neo4j is running: `docker ps` or check Neo4j Desktop
- Credentials are correct in `.env`
- URI format is correct (bolt:// for local, neo4j+s:// for AuraDB)

### Issue: OpenRouter API errors
**Check:**
- API key is valid in `.env`
- Account has credits
- Model names are correct: `openai/gpt-4o-mini`, `openai/text-embedding-3-small`

### Issue: Frontend can't connect to backend
**Check:**
- Backend is running on port 8000
- CORS is configured (already set in `main.py`)
- `NEXT_PUBLIC_API_URL` matches backend URL

### Issue: PDF upload fails with "bad filename"
**This is fixed** - ensure you're using the latest code

### Issue: Processing stuck at a certain percentage
**Check backend logs:**
```bash
# Backend terminal shows detailed progress
# Common issues:
# - OpenRouter API rate limits
# - Neo4j connection timeout
# - Qdrant storage issues
```

---

## Testing the Application

1. **Upload a PDF:**
   - Drag and drop or click to browse
   - Max size: 50MB
   - Format: PDF only

2. **Monitor Processing:**
   - Watch progress bar: 0% → 10% → 40% → 70% → 100%
   - Status messages update in real-time
   - Should complete in 30-60 seconds for typical policy

3. **Ask Questions:**
   - Try suggested questions
   - Ask about coverage, exclusions, waiting periods
   - Check citations expand/collapse correctly

4. **Verify Citations:**
   - Each answer should include source citations
   - Citations show section ID, clause name, and text snippet
   - Click to expand and see full text

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Check backend health |
| POST | `/api/upload` | Upload PDF document |
| GET | `/api/status/{document_id}` | Get processing status |
| POST | `/api/chat` | Ask question about policy |
| DELETE | `/api/document/{document_id}` | Delete document |

### Example: Test Health
```bash
curl http://localhost:8000/api/health
```

### Example: Chat
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "your-document-id",
    "question": "What does this policy cover?"
  }'
```

---

## Project Structure

```
PolicyPal/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app & routes
│   │   ├── config.py            # Configuration
│   │   ├── models/schemas.py    # Pydantic models
│   │   └── services/
│   │       ├── pdf_processor.py    # PDF extraction
│   │       ├── graph_service.py    # Neo4j operations
│   │       ├── vector_service.py   # Qdrant operations
│   │       └── rag_engine.py       # GraphRAG pipeline
│   ├── requirements.txt
│   ├── reset_qdrant.py         # Qdrant setup utility
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx
│   │   │   ├── layout.tsx
│   │   │   └── globals.css
│   │   └── components/
│   │       ├── PdfUpload.tsx
│   │       ├── ChatSection.tsx
│   │       └── CitationCard.tsx
│   ├── package.json
│   └── .env.local
├── README.md
├── FIXES_APPLIED.md
└── SETUP_GUIDE.md (this file)
```

---

## Support

For issues:
1. Check backend logs for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure databases (Neo4j, Qdrant) are running
4. Check API keys are valid and have credits
5. Review FIXES_APPLIED.md for known issues

Happy coding! 🚀
