# PolicyPal Changelog

## [1.0.1] - 2024 Latest Fixes

### 🐛 Critical Fixes

#### Backend
- **Fixed**: Qdrant "Index required for document_id" error
  - Added `PayloadSchemaType.KEYWORD` index creation
  - Auto-creates index on collection initialization
  - Added `reset_qdrant.py` utility script

- **Fixed**: RAG Engine NoneType error
  - Added null check for LLM response content
  - Better error handling for empty responses
  - Validation for citation objects

- **Fixed**: PDF processing "bad filename" error
  - Changed to accept bytes instead of file path
  - Uses in-memory PDF processing with `fitz.open(stream=...)`

- **Fixed**: GraphService method call mismatch
  - Corrected to use `extract_entities_and_relationships()`
  - Added proper DocumentChunk conversion

- **Fixed**: Schema validation errors
  - Added missing `filename`, `created_at` fields
  - Changed status to use `DocumentStatus` enum
  - Fixed `Citation` schema to match RAG output

#### Frontend
- **Fixed**: Upload progress not updating
  - Added real-time polling with proper cleanup
  - Shows progress from 0% → 100%
  - 5-minute timeout protection

### ✨ New Features

#### UI Improvements
- **Multi-step processing indicator**
  - 4 visual steps with icons
  - Shows: Inactive → Active (spinning) → Complete (checkmark)
  - Real-time progress updates

- **Enhanced health status badges**
  - Green badges when services connected
  - Red badges when disconnected
  - Smooth color transitions

- **Better upload feedback**
  - Animated spinner during upload
  - Status messages with icons
  - Improved progress visualization

#### New Utilities
- `reset_qdrant.py` - Recreate collection with proper indexes
- `QUICK_START.md` - Fast setup guide
- `SETUP_GUIDE.md` - Comprehensive setup instructions
- `UI_IMPROVEMENTS.md` - UI enhancement documentation

### 📦 Package Updates

#### Backend
- fastapi: 0.109.0 → 0.115.6
- uvicorn: 0.27.0 → 0.34.0
- pydantic: 2.5.3 → 2.10.5
- openai: 1.12.0 → 1.59.8
- pymupdf: 1.23.12 → 1.25.2
- qdrant-client: 1.9.1 → 1.12.3
- neo4j: 5.15.0 → 5.28.0

#### Frontend
- next: 16.2.10 → 16.3.0
- react: 19.2.4 → 19.2.8
- react-dom: 19.2.4 → 19.2.8
- lucide-react: 1.25.0 → 1.31.0

### 🎨 UI Changes

#### Colors
- Success/Connected: Green (`bg-green-50`, `text-green-700`)
- Error/Disconnected: Red (`bg-red-50`, `text-red-700`)
- Active: Dark gray (`bg-gray-900`)
- Inactive: Light gray (`bg-gray-100`, `text-gray-400`)

#### Components
- Added `ProcessingStep` component with 3 visual states
- Improved health badge styling
- Enhanced upload progress display
- Smoother animations throughout

### 🔧 Configuration

#### New Environment Variables
- All existing variables remain the same
- No breaking changes to configuration

#### Database Schema
- Qdrant: Now requires `document_id` keyword index
- Neo4j: No schema changes
- Run `reset_qdrant.py` to apply index

### 📝 Documentation

#### New Files
- `QUICK_START.md` - Get started in 5 minutes
- `SETUP_GUIDE.md` - Complete setup instructions
- `FIXES_APPLIED.md` - All fixes documented
- `UI_IMPROVEMENTS.md` - UI enhancement details
- `CHANGELOG.md` - This file

#### Updated Files
- `README.md` - Updated architecture details

### 🚀 Migration Guide

If upgrading from initial version:

1. **Update packages:**
   ```bash
   cd backend && pip install -r requirements.txt --upgrade
   cd frontend && npm install
   ```

2. **Fix Qdrant index:**
   ```bash
   cd backend
   python reset_qdrant.py
   ```

3. **Restart services:**
   ```bash
   # Backend
   uvicorn app.main:app --reload
   
   # Frontend
   npm run dev
   ```

### ⚠️ Breaking Changes
- None! All changes are backwards compatible.
- Existing uploaded documents will continue to work.
- Only Qdrant collection needs index update (automatic).

### 🐛 Known Issues
- None at this time

### 🔮 Future Improvements
- [ ] Add conversation history support
- [ ] Support multiple document upload
- [ ] Add document comparison feature
- [ ] Implement user authentication
- [ ] Add export functionality for Q&A
- [ ] Support more file formats (DOCX, TXT)
- [ ] Add admin dashboard for document management
- [ ] Implement caching for faster responses

---

## [1.0.0] - Initial Release

### Features
- PDF upload and processing
- GraphRAG pipeline (Neo4j + Qdrant)
- Entity extraction using GPT-4o-mini
- Vector search with Qdrant
- Graph traversal with Neo4j
- Chat interface with citations
- Health monitoring
- Real-time processing status

---

**For detailed setup instructions, see QUICK_START.md or SETUP_GUIDE.md**
