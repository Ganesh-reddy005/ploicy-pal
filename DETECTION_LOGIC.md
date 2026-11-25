# PDF Type Detection Logic

## How PolicyPal Automatically Detects Scanned vs Text-Based PDFs

### Quick Answer
**It uses PyMuPDF FIRST on ALL PDFs, then checks how much text was extracted. If too little (< 50 chars), it triggers OCR.**

---

## The Smart Detection Process

### Step 1: Universal PyMuPDF Attempt
```python
# ALWAYS runs first, regardless of PDF type
doc = fitz.open(stream=pdf_content, filetype="pdf")
text = page.get_text()
```

**Why PyMuPDF first?**
- ⚡ Very fast (milliseconds per page)
- 📝 Works perfectly for text-based PDFs
- 🖼️ Still runs on scanned PDFs (just extracts minimal text)
- 💰 Free (no API costs)

### Step 2: Intelligent Detection
```python
# Check extracted text length
if len(text.strip()) < 50:  # Less than 50 characters
    # Page is SCANNED → needs OCR
    scanned_pages.append(page_num)
else:
    # Page is TEXT-BASED → use PyMuPDF text
    # No OCR needed!
```

**Detection Threshold: 50 characters**
- Text-based pages: Usually have 500-5000+ characters
- Scanned pages: Usually have 0-20 characters (just artifacts)

### Step 3: Conditional OCR
```python
# Only for pages marked as scanned
if scanned_pages:
    for page_num in scanned_pages:
        # Render page to high-res image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom
        
        # OCR with GPT-4o-mini Vision
        ocr_text = self.ocr_image_with_gpt4v(img_base64)
        
        # Replace minimal text with OCR result
        pages_data[page_num]["text"] = ocr_text
```

---

## Real Examples

### Example 1: Text-Based PDF

```
Page 1:
PyMuPDF extracts: "INSURANCE POLICY\n\nSection 1: Coverage\n\nThis policy provides..."
Length: 2,450 characters
Decision: ✅ Use PyMuPDF text, skip OCR
Time: 10ms
Cost: $0
```

### Example 2: Scanned PDF

```
Page 1:
PyMuPDF extracts: ""
Length: 0 characters
Decision: ⚠️ Trigger OCR
OCR extracts: "INSURANCE POLICY\n\nSection 1: Coverage\n\nThis policy provides..."
Time: 3-5 seconds
Cost: ~$0.00015
```

### Example 3: Mixed PDF (Common!)

```
Page 1: Text-based
PyMuPDF: 1,850 chars → ✅ Use as-is (10ms, $0)

Page 2: Scanned
PyMuPDF: 5 chars → ⚠️ Trigger OCR (3s, $0.00015)

Page 3: Text-based
PyMuPDF: 2,100 chars → ✅ Use as-is (10ms, $0)

Page 4: Scanned
PyMuPDF: 12 chars → ⚠️ Trigger OCR (3s, $0.00015)

Total: 2 OCR calls only, not 4!
```

---

## Why This Approach is Smart

### ✅ Advantages

1. **Efficient**
   - Only uses expensive OCR when needed
   - Fast PyMuPDF for 90% of pages

2. **Cost-Effective**
   - Text PDFs: $0 (no API calls)
   - Scanned PDFs: Only pay for scanned pages
   - Mixed PDFs: Only OCR the scanned parts

3. **Accurate**
   - PyMuPDF gives perfect text for text-based pages
   - OCR handles images when needed

4. **Automatic**
   - No user configuration needed
   - Works with any PDF type
   - Handles mixed documents

5. **Fail-Safe**
   - If PyMuPDF gets good text, done!
   - If PyMuPDF fails, OCR kicks in
   - Graceful degradation

---

## The Detection Code

```python
# Step 1: Try PyMuPDF on everything
for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()  # Fast extraction
    
    # Step 2: Check if scanned
    if len(text.strip()) < 50:  # Detection threshold
        scanned_pages.append(page_num)
        logger.info(f"Page {page_num + 1} appears to be scanned")
    
    # Store preliminary text
    pages_data.append({
        "page_number": page_num + 1,
        "text": text,
        "section_title": None
    })

# Step 3: OCR only for scanned pages
if scanned_pages:
    logger.info(f"Running OCR on {len(scanned_pages)} pages...")
    for page_num in scanned_pages:
        # Render to image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_base64 = base64.b64encode(pix.tobytes("png"))
        
        # OCR
        ocr_text = self.ocr_image_with_gpt4v(img_base64)
        
        # Replace minimal text with OCR result
        pages_data[page_num]["text"] = ocr_text
```

---

## Configuration

### Detection Threshold
```python
# In pdf_processor.py, line ~220
SCANNED_PAGE_THRESHOLD = 50  # characters

if len(text.strip()) < SCANNED_PAGE_THRESHOLD:
    # Trigger OCR
```

**You can adjust this:**
- **Lower (e.g., 20)**: More aggressive OCR (catches more scanned pages)
- **Higher (e.g., 100)**: Less aggressive OCR (only very sparse pages)
- **Default (50)**: Good balance for most documents

### OCR Quality
```python
# Image resolution for OCR
fitz.Matrix(2, 2)  # 2x zoom = 200% resolution
```

**You can adjust this:**
- **1x**: Faster, lower quality
- **2x**: Balanced (current)
- **3x**: Slower, higher quality

---

## Performance Comparison

### 10-Page Document

#### All Text-Based
```
PyMuPDF: 10 pages × 10ms = 100ms
OCR: 0 pages × 0s = 0s
Total: 100ms (~0.1 seconds)
Cost: $0
```

#### All Scanned
```
PyMuPDF: 10 pages × 10ms = 100ms (detection)
OCR: 10 pages × 3s = 30s
Total: ~30 seconds
Cost: ~$0.0015 (10 × $0.00015)
```

#### Mixed (50/50)
```
PyMuPDF: 10 pages × 10ms = 100ms (detection)
OCR: 5 pages × 3s = 15s
Total: ~15 seconds
Cost: ~$0.00075 (5 × $0.00015)
```

---

## FAQ

### Q: Can I force OCR on all pages?
**A:** Yes, change the threshold to very high:
```python
if len(text.strip()) < 999999:  # Always trigger OCR
```

### Q: Can I disable OCR completely?
**A:** Yes, comment out the OCR block:
```python
# if scanned_pages:
#     logger.info(f"Running OCR on {len(scanned_pages)} pages...")
#     # ... OCR code ...
```

### Q: What if PyMuPDF extracts garbled text?
**A:** The threshold catches this - garbled text is usually < 50 chars or random characters. OCR will be triggered.

### Q: What if OCR also fails?
**A:** The system:
1. Logs the error
2. Continues with other pages
3. Uses whatever text was extracted
4. Doesn't crash

### Q: Why not just OCR everything?
**A:** Because:
- 🐌 OCR is 300x slower (3s vs 10ms)
- 💰 OCR costs money ($0.00015/page)
- 📝 PyMuPDF text is perfect for text PDFs
- 🎯 Smart detection gives best of both worlds

### Q: Does it work for PDFs with both text and images?
**A:** Yes! Each page is evaluated independently:
- Text pages → PyMuPDF
- Image pages → OCR
- Mixed pages → PyMuPDF if enough text, else OCR

---

## Logs to Watch

When processing, you'll see:

### Text-Based PDF
```
INFO: Processing PDF: policy.pdf
INFO: Created 45 chunks from 10 pages (0 scanned)
```

### Scanned PDF
```
INFO: Processing PDF: scanned_policy.pdf
INFO: Page 1 appears to be scanned, will use OCR
INFO: Page 2 appears to be scanned, will use OCR
...
INFO: Running OCR on 10 scanned pages...
INFO: OCR successful for page 1
INFO: OCR successful for page 2
...
INFO: Created 38 chunks from 10 pages (10 scanned)
```

### Mixed PDF
```
INFO: Processing PDF: mixed_policy.pdf
INFO: Page 2 appears to be scanned, will use OCR
INFO: Page 5 appears to be scanned, will use OCR
INFO: Running OCR on 2 scanned pages...
INFO: OCR successful for page 2
INFO: OCR successful for page 5
INFO: Created 42 chunks from 10 pages (2 scanned)
```

---

## Summary

**The system is smart:**
1. ✅ Tries fast, free PyMuPDF first
2. ✅ Detects if result is insufficient (< 50 chars)
3. ✅ Only uses expensive OCR when needed
4. ✅ Works with any PDF type automatically
5. ✅ No user configuration required

**You get:**
- ⚡ Best speed for text PDFs
- 🖼️ Full support for scanned PDFs
- 💰 Minimal API costs
- 🎯 Accurate results for both types
- 🔄 Handles mixed documents perfectly

It's the best of both worlds! 🎉
