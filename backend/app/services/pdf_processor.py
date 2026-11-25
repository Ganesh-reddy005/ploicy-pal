import fitz  # PyMuPDF
import pdf2image
import base64
import io
import uuid
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    text: str
    page_number: int
    section_title: Optional[str]
    chunk_index: int


class PDFProcessor:
    def __init__(self):
        self.chunk_size = 500
        self.chunk_overlap = 100
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

    def extract_text_from_pdf(self, pdf_path: str) -> List[Tuple[int, str, Optional[str]]]:
        """
        Extract text from PDF using PyMuPDF.
        Returns list of (page_number, text, section_title)
        """
        doc = fitz.open(pdf_path)
        pages_data = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            # Try to extract section title from first few lines
            section_title = None
            lines = text.strip().split('\n')
            for line in lines[:5]:
                line = line.strip()
                if line and line.isupper() and len(line) < 100:
                    section_title = line
                    break

            pages_data.append((page_num + 1, text, section_title))

        doc.close()
        return pages_data

    def extract_images_from_pdf(self, pdf_path: str) -> List[Tuple[int, str]]:
        """
        Extract images from PDF pages for OCR.
        Returns list of (page_number, base64_image)
        """
        images = []
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
            img_data = pix.tobytes("png")
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            images.append((page_num + 1, img_base64))

        doc.close()
        return images

    def ocr_image_with_gpt4v(self, img_base64: str) -> str:
        """
        Use GPT-4o-mini Vision via OpenRouter for OCR.
        """
        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Extract ALL text from this insurance/banking policy document page. 

INSTRUCTIONS:
1. Preserve the exact text, structure, and formatting
2. Include headers, section numbers, clause numbers
3. Maintain paragraph breaks and bullet points
4. Include all fine print and footnotes
5. Preserve numerical values and percentages exactly
6. Keep special characters and symbols
7. Return ONLY the extracted text, no commentary

Be thorough and accurate - this is a legal document."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""

    def extract_text_with_ocr_fallback(self, pdf_path: str) -> List[Tuple[int, str, Optional[str]]]:
        """
        Extract text from PDF, using OCR fallback for pages with little text.
        """
        pages_data = self.extract_text_from_pdf(pdf_path)

        # Check if any page has very little text (likely scanned)
        needs_ocr = []
        for page_num, text, section_title in pages_data:
            if len(text.strip()) < 100:
                needs_ocr.append(page_num)

        if needs_ocr:
            logger.info(f"Pages {needs_ocr} have little text, using OCR fallback")
            images = self.extract_images_from_pdf(pdf_path)

            for page_num, img_base64 in images:
                if page_num in needs_ocr:
                    try:
                        ocr_text = self.ocr_image_with_gpt4v(img_base64)
                        # Try to extract section title from OCR text
                        section_title = None
                        lines = ocr_text.strip().split('\n')
                        for line in lines[:5]:
                            line = line.strip()
                            if line and line.isupper() and len(line) < 100:
                                section_title = line
                                break

                        # Update the page data
                        for i, (pn, text, st) in enumerate(pages_data):
                            if pn == page_num:
                                pages_data[i] = (page_num, ocr_text, section_title)
                                break
                    except Exception as e:
                        logger.error(f"OCR failed for page {page_num}: {e}")

        return pages_data

    def _chunk_text(self, text: str, page_number: int, section_title: Optional[str] = None) -> List[DocumentChunk]:
        """
        Split text into overlapping chunks.
        """
        chunks = []
        words = text.split()

        if len(words) <= self.chunk_size:
            chunk_id = str(uuid.uuid4())
            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                document_id="",
                text=text,
                page_number=page_number,
                section_title=section_title,
                chunk_index=0
            ))
            return chunks

        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            chunk_id = str(uuid.uuid4())
            chunk_index = i // (self.chunk_size - self.chunk_overlap)

            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                document_id="",
                text=chunk_text,
                page_number=page_number,
                section_title=section_title,
                chunk_index=chunk_index
            ))

        return chunks

    def process_pdf(self, pdf_content: bytes, filename: str, document_id: str = "") -> dict:
        """
        Process a PDF from bytes and return chunks.
        
        Args:
            pdf_content: PDF file content as bytes
            filename: Original filename for logging
            document_id: Optional document ID to assign to chunks
            
        Returns:
            dict with 'full_text' and 'chunks' keys
        """
        logger.info(f"Processing PDF: {filename}")

        # Open PDF from bytes instead of file path
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        
        full_text = ""
        pages_data = []
        scanned_pages = []

        # First pass: extract text and identify scanned pages
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            # Check if page is likely scanned (very little text)
            if len(text.strip()) < 50:
                scanned_pages.append(page_num)
                logger.info(f"Page {page_num + 1} appears to be scanned, will use OCR")

            # Try to extract section title from first few lines
            section_title = None
            lines = text.strip().split('\n')
            for line in lines[:5]:
                line = line.strip()
                if line and line.isupper() and len(line) < 100:
                    section_title = line
                    break

            pages_data.append({
                "page_number": page_num + 1,
                "text": text,
                "section_title": section_title
            })
            full_text += text + "\n"

        # Second pass: OCR for scanned pages
        if scanned_pages:
            logger.info(f"Running OCR on {len(scanned_pages)} scanned pages...")
            for page_num in scanned_pages:
                try:
                    page = doc[page_num]
                    # Higher resolution for better OCR
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_data = pix.tobytes("png")
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    
                    # OCR with GPT-4o-mini Vision
                    ocr_text = self.ocr_image_with_gpt4v(img_base64)
                    
                    if ocr_text and len(ocr_text.strip()) > 50:
                        # Extract section title from OCR text
                        section_title = None
                        lines = ocr_text.strip().split('\n')
                        for line in lines[:5]:
                            line = line.strip()
                            if line and line.isupper() and len(line) < 100:
                                section_title = line
                                break
                        
                        # Update page data with OCR text
                        pages_data[page_num]["text"] = ocr_text
                        pages_data[page_num]["section_title"] = section_title
                        full_text += ocr_text + "\n"
                        logger.info(f"OCR successful for page {page_num + 1}")
                    else:
                        logger.warning(f"OCR returned minimal text for page {page_num + 1}")
                        
                except Exception as e:
                    logger.error(f"OCR failed for page {page_num + 1}: {e}")

        doc.close()

        # Chunk the text
        chunks = []
        for page_data in pages_data:
            # Skip pages with no meaningful text
            if not page_data["text"].strip() or len(page_data["text"].strip()) < 20:
                logger.warning(f"Skipping page {page_data['page_number']} - insufficient text")
                continue
                
            page_chunks = self._chunk_text(
                page_data["text"],
                page_data["page_number"],
                page_data["section_title"]
            )
            for chunk in page_chunks:
                chunk.document_id = document_id
            chunks.extend(page_chunks)

        logger.info(f"Created {len(chunks)} chunks from {len(pages_data)} pages ({len(scanned_pages)} scanned)")
        
        # Return empty lists if no chunks created
        if not chunks:
            logger.error("No chunks created from PDF - document may be completely unreadable")
            return {
                "full_text": full_text or "No text could be extracted from this document.",
                "chunks": []
            }
        
        return {
            "full_text": full_text,
            "chunks": [
                {
                    "text": c.text,
                    "page_number": c.page_number,
                    "section_id": f"page_{c.page_number}",
                    "clause_number": "",
                    "clause_name": c.section_title or "",
                }
                for c in chunks
            ]
        }