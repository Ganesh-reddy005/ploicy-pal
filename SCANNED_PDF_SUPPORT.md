# Scanned PDF Support & Enhanced RAG

## Overview

PolicyPal now supports both types of PDFs:
1. **Standard PDFs** - Text-based documents (processed with PyMuPDF)
2. **Scanned PDFs** - Image-based documents (processed with OCR via GPT-4o-mini Vision)

## How It Works

### Automatic Detection
The system automatically detects scanned pages:
- Pages with < 50 characters are marked as scanned
- OCR is triggered only for pages that need it
- Efficient processing of mixed documents (some text, some scanned)

### Processing Pipeline

#### Standard PDF Pages
```
PDF → PyMuPDF → Text Extraction → Chunking → Embedding → Storage
```

#### Scanned PDF Pages
```
PDF → PyMuPDF → Detect Low Text → Render to Image (2x resolution)
    → GPT-4o-mini Vision OCR → Text Extraction → Chunking → Embedding → Storage
```

### OCR Configuration
- **Model**: openai/gpt-4o-mini (via OpenRouter)
- **Resolution**: 2x zoom for better accuracy
- **Max Tokens**: 4000 per page
- **Format**: PNG images, base64 encoded

## Enhanced RAG with General Knowledge

### Two-Source Approach

PolicyPal now combines:
1. **Document-specific information** (primary)
2. **General insurance/banking knowledge** (supplementary)

### Response Strategy

#### Document-First
```
User: "What's covered?"
Answer: "According to your policy, [specific coverage from document]. 
Typically, insurance policies also cover [general info]."
```

#### General Knowledge When Needed
```
User: "What is a pre-existing condition?"
Answer: "A pre-existing condition is [general definition]. 
In your policy, [specific handling if mentioned in document]."
```

#### Hybrid Explanations
```
User: "How do I file a claim?"
Answer: "Your policy states [specific process from document].
Generally, you should also [best practices from general knowledge]."
```

### Clear Source Attribution

The system makes it clear what comes from where:
- **"According to your policy..."** = Document-specific
- **"Typically..."** / **"Generally..."** = General knowledge
- **"However, check with your provider"** = Recommendation for verification

## Prompt Engineering

### OCR Prompt Features
- Preserves exact structure and formatting
- Includes headers, section numbers, clause numbers
- Captures fine print and footnotes
- Maintains numerical accuracy
- Keeps special characters

### RAG Prompt Features
- Two-tiered knowledge hierarchy
- Clear source attribution
- Plain language explanations
- Actionable advice
- Educational approach

## Error Handling

### Empty Chunks Prevention
- Filters out chunks with < 20 characters
- Skips pages with insufficient text
- Logs warnings for skipped pages
- Prevents "Empty update request" errors

### OCR Failure Handling
- Graceful degradation if OCR fails
- Continues processing other pages
- Logs detailed error messages
- Returns best-effort results

### Validation
- Checks for valid chunks before storage
- Validates embedding generation
- Ensures non-empty responses

## Usage Examples

### Scanned PDF Upload
```python
# Automatic - no special handling needed
# System detects and processes scanned pages automatically
```

### Mixed Document
```
Page 1: Standard text → PyMuPDF
Page 2: Scanned → OCR
Page 3: Standard text → PyMuPDF
Page 4: Scanned → OCR
```

### General Knowledge Queries

**Without document context:**
```
Q: "What is term life insurance?"
A: "Term life insurance is [general explanation with industry standards]"
```

**With document context:**
```
Q: "What is term life insurance?"
A: "Your policy is a term life insurance which means [specific details from doc].
Term life insurance generally [general explanation]."
```

## API Cost Considerations

### OCR Costs
- GPT-4o-mini Vision: ~$0.00015 per page (average)
- Only charged for scanned pages
- Efficient batch processing

### Embedding Costs
- text-embedding-3-small: ~$0.00002 per 1K tokens
- Applied to all chunks regardless of source

### Chat Costs
- GPT-4o-mini: ~$0.00015 per request
- Enhanced prompts use slightly more tokens
- Better answers justify the minimal increase

## Performance

### Standard PDF (10 pages)
- Processing time: ~30 seconds
- Mostly text extraction and graph building

### Scanned PDF (10 pages)
- Processing time: ~60-90 seconds
- Additional OCR time per page: ~3-5 seconds

### Mixed PDF (5 text + 5 scanned)
- Processing time: ~45-60 seconds
- OCR only on needed pages

## Best Practices

### For Users
1. Upload high-quality scans (300+ DPI)
2. Ensure pages are properly oriented
3. Use PDF format (not JPG/PNG)
4. Keep files under 50MB

### For Developers
1. Monitor OCR success rates
2. Check logs for skipped pages
3. Validate chunk counts
4. Test with various PDF types

## Troubleshooting

### "Processing failed: Empty update request"
**Cause**: No text extracted from any page
**Solution**: 
- Check if PDF is readable
- Verify OpenRouter API key has vision model access
- Check logs for OCR errors
- Try a different PDF

### OCR Returns Minimal Text
**Cause**: Poor scan quality or complex layout
**Solution**:
- Increase image resolution (already 2x)
- Check page orientation
- Verify scan quality
- Try re-scanning document

### Slow Processing
**Cause**: Many scanned pages
**Expected**: 3-5 seconds per scanned page
**Normal**: Mixed documents process faster than fully scanned

## Configuration

### Environment Variables
```env
# OCR Model (must support vision)
OPENAI_MODEL=openai/gpt-4o-mini

# Max resolution for OCR
# Higher = better quality, slower processing
PDF_OCR_ZOOM=2  # default: 2x
```

### Thresholds
```python
# In pdf_processor.py
MIN_TEXT_FOR_STANDARD = 50      # chars per page
MIN_TEXT_FOR_CHUNK = 20         # chars per chunk
OCR_ZOOM_FACTOR = 2             # image resolution multiplier
```

## Future Enhancements

Potential improvements:
- [ ] Support for multi-column layouts
- [ ] Table extraction and parsing
- [ ] Handwriting recognition
- [ ] Form field detection
- [ ] Multi-language OCR
- [ ] Batch OCR optimization
- [ ] Caching of OCR results

## Examples

### Sample Questions That Work Well

**Document-Specific:**
- "What is my coverage limit?"
- "What are the exclusions?"
- "What is the waiting period?"

**General Knowledge:**
- "What is a deductible?"
- "How does coinsurance work?"
- "What is a claim process?"

**Hybrid:**
- "How does my waiting period compare to industry standards?"
- "Are my exclusions typical?"
- "Is my coverage comprehensive?"

---

**Note**: The enhanced RAG system maintains accuracy while being more helpful and educational for users.
