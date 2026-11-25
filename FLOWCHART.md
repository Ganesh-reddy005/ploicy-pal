# PDF Processing Flowchart

## Simple Decision Flow

```
                    📄 PDF Uploaded
                          |
                          ↓
            ┌─────────────────────────┐
            │  Open with PyMuPDF      │ ← Always runs first
            │  (fitz.open)            │    (Fast, free)
            └─────────────────────────┘
                          |
                          ↓
            ┌─────────────────────────┐
            │  Extract text           │
            │  text = page.get_text() │
            └─────────────────────────┘
                          |
                          ↓
            ┌─────────────────────────┐
            │  Count characters       │
            │  len(text.strip())      │
            └─────────────────────────┘
                          |
                          ↓
              ┌───────────┴───────────┐
              │                       │
              ↓                       ↓
    ┌──────────────────┐    ┌──────────────────┐
    │  >= 50 chars?    │    │  < 50 chars?     │
    │  TEXT-BASED      │    │  SCANNED         │
    └──────────────────┘    └──────────────────┘
              |                       |
              ↓                       ↓
    ┌──────────────────┐    ┌──────────────────┐
    │  ✅ Use PyMuPDF  │    │  ⚠️ Need OCR      │
    │     text         │    │                  │
    │                  │    │  Render to image │
    │  Time: 10ms     │    │  Call GPT-4V     │
    │  Cost: $0       │    │                  │
    │                  │    │  Time: 3-5s      │
    │                  │    │  Cost: $0.00015  │
    └──────────────────┘    └──────────────────┘
              |                       |
              └───────────┬───────────┘
                          ↓
            ┌─────────────────────────┐
            │  Chunk text             │
            │  (500 words per chunk)  │
            └─────────────────────────┘
                          |
                          ↓
            ┌─────────────────────────┐
            │  Extract entities       │
            │  (GPT-4o-mini)          │
            └─────────────────────────┘
                          |
                          ↓
            ┌─────────────────────────┐
            │  Store in Neo4j         │
            │  (Graph database)       │
            └─────────────────────────┘
                          |
                          ↓
            ┌─────────────────────────┐
            │  Generate embeddings    │
            │  (text-embedding-3)     │
            └─────────────────────────┘
                          |
                          ↓
            ┌─────────────────────────┐
            │  Store in Qdrant        │
            │  (Vector database)      │
            └─────────────────────────┘
                          |
                          ↓
            ┌─────────────────────────┐
            │  ✅ Ready for Q&A       │
            └─────────────────────────┘
```

## Key Points

### The Magic Number: 50
- **>= 50 characters**: Page has readable text → Use PyMuPDF
- **< 50 characters**: Page is image/scan → Use OCR

### Why This Works
1. Text-based pages have **hundreds to thousands** of characters
2. Scanned pages extract **0-20 characters** (artifacts only)
3. 50 is a safe middle ground that catches all scanned pages

### Cost Optimization
```
Text PDF (10 pages):
  PyMuPDF: 10 × $0 = $0
  OCR: 0 × $0.00015 = $0
  Total: $0 ✅

Scanned PDF (10 pages):
  PyMuPDF: 10 × $0 = $0 (detection only)
  OCR: 10 × $0.00015 = $0.0015
  Total: $0.0015 ✅

Mixed PDF (5 text + 5 scanned):
  PyMuPDF: 10 × $0 = $0
  OCR: 5 × $0.00015 = $0.00075
  Total: $0.00075 ✅
```

### Time Optimization
```
PyMuPDF: ~10ms per page
OCR: ~3-5s per page

Text PDF (10 pages): 100ms total
Scanned PDF (10 pages): 30-50s total
Mixed PDF (5+5): 15-25s total
```

## The Smart Part

**No configuration needed!**
- Upload any PDF
- System detects type automatically
- Uses optimal method for each page
- You get best results with lowest cost

**Works for:**
- ✅ Pure text PDFs (most policies)
- ✅ Pure scanned PDFs (older documents)
- ✅ Mixed PDFs (common in real world)
- ✅ Multi-column layouts
- ✅ PDFs with images and text

**Handles edge cases:**
- Garbled text → Detected as < 50 chars → OCR
- Low-quality scans → Higher resolution (2x zoom)
- OCR failures → Graceful degradation
- Empty pages → Skipped with warning
