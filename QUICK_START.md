# PolicyPal Quick Start Guide

## 🚀 First Time Setup

### 1. Fix Qdrant Index (Required!)
```bash
cd backend
python reset_qdrant.py
```
**When prompted, type `y` to recreate the collection.**

### 2. Start Backend
```bash
cd backend
uvicorn app.main:app --reload
```
Backend runs at: http://localhost:8000

### 3. Start Frontend
```bash
cd frontend
npm run dev
```
Frontend runs at: http://localhost:3000

---

## 🎯 Quick Test

1. Open http://localhost:3000
2. Check health badges:
   - ✅ Green = Connected
   - ❌ Red = Disconnected
3. Upload a PDF (drag & drop or click)
4. Watch the processing steps:
   - 📄 Extracting text (0-10%)
   - 🕸️ Building graph (10-40%)
   - 🔍 Indexing (40-70%)
   - ✅ Ready (70-100%)
5. Ask questions when complete!

---

## ⚠️ Common Issues

### "Index required for document_id"
```bash
cd backend
python reset_qdrant.py
```

### Backend won't start
- Check `.env` file exists with all variables
- Verify OpenRouter API key is valid
- Ensure Neo4j and Qdrant are accessible

### Frontend can't connect
- Backend must be running on port 8000
- Check browser console for CORS errors

### Processing stuck
- Check backend terminal for error logs
- Verify OpenRouter API has credits
- Try with a smaller PDF first

---

## 📊 What to Expect

### Processing Times (typical 10-page policy):
- Upload: 1-2 seconds
- Extraction: 5-10 seconds
- Graph building: 10-20 seconds
- Indexing: 10-15 seconds
- **Total: 30-60 seconds**

### Database Usage:
- **Qdrant**: Stores text embeddings (vectors)
- **Neo4j**: Stores entities & relationships (graph)
- Both needed for full GraphRAG functionality

---

## 🎨 UI Features

### Header
- App name with icon
- Real-time health badges (Qdrant, Neo4j)
- Loading spinner when checking health

### Upload Screen
- Drag & drop zone
- File validation (PDF only, max 50MB)
- Upload button with progress

### Processing Screen
- Animated spinner with progress %
- 4-step progress indicator
- Smooth transitions between steps
- Real-time status messages

### Chat Screen
- Message history
- Suggested questions
- Expandable citations
- Copy citation text
- Timestamp on messages

---

## 📝 Example Questions

Try these after uploading a policy:

- "What does this policy cover?"
- "What are the exclusions?"
- "What is the waiting period?"
- "How do I file a claim?"
- "Are pre-existing conditions covered?"
- "What is the maximum coverage amount?"

---

## 🔧 Environment Variables

### Backend `.env` (Required)
```env
OPENROUTER_API_KEY=sk-or-v1-xxx
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_key
```

### Frontend `.env.local` (Optional)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🎓 Tips

1. **Use real insurance PDFs** for best results
2. **Start with smaller files** (5-10 pages) for testing
3. **Check backend logs** for detailed processing info
4. **Try different question styles** to see how RAG responds
5. **Expand citations** to see source text

---

## 📞 Need Help?

1. Check `SETUP_GUIDE.md` for detailed setup
2. Review `FIXES_APPLIED.md` for known issues
3. Check backend terminal logs for errors
4. Verify all environment variables are set
5. Ensure databases are running and accessible

---

## ✅ Success Checklist

- [ ] `reset_qdrant.py` completed successfully
- [ ] Backend starts without errors
- [ ] Frontend builds and runs
- [ ] Health badges show green (both Qdrant & Neo4j)
- [ ] Can upload PDF successfully
- [ ] Processing completes to 100%
- [ ] Chat interface loads
- [ ] Questions return answers with citations
- [ ] Citations expand/collapse correctly

---

**Ready to go!** 🎉

Upload a policy PDF and start asking questions!
