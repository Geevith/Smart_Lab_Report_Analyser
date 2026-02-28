import pdfplumber
import os
import logging
from typing import Dict

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Gemini Vision OCR (primary fallback when Tesseract unavailable)
# ─────────────────────────────────────────────────────────────

def _extract_text_with_gemini_vision(file_path: str) -> str:
    """
    Use Gemini Vision (multimodal) to extract all text from an image.
    This is the primary fallback when Tesseract OCR is not installed.
    Returns extracted text string, or empty string on failure.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        log.warning("Gemini Vision fallback skipped: GEMINI_API_KEY not set")
        return ""

    try:
        from google import genai
        from PIL import Image as PILImage

        client = genai.Client(api_key=api_key)

        # Open and normalise image (PIL Image can be passed directly to google-genai)
        img = PILImage.open(file_path)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        prompt = (
            "You are an OCR system. Extract ALL text from this medical document image EXACTLY as it appears. "
            "Preserve the structure, headings, bullet points, patient details, and all numeric values. "
            "Do NOT summarize or interpret — just transcribe every word and number visible in the image. "
            "Output ONLY the raw extracted text with no extra commentary."
        )

        # Pass PIL Image directly — this is the correct format for google-genai SDK
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, img],
        )
        extracted = response.text.strip()
        log.info("Gemini Vision OCR extracted %d characters", len(extracted))
        return extracted

    except Exception as e:
        import traceback
        log.error("Gemini Vision OCR failed: %s\n%s", e, traceback.format_exc())
        return ""



# ─────────────────────────────────────────────────────────────
# PDF Extraction
# ─────────────────────────────────────────────────────────────

def extract_from_pdf(file_path: str) -> Dict:
    """
    Extracts text from a PDF file with multi-page support and quality tracking.
    """
    result = {
        'text': '',
        'pages': [],
        'page_count': 0,
        'errors': []
    }

    try:
        with pdfplumber.open(file_path) as pdf:
            result['page_count'] = len(pdf.pages)

            for i, page in enumerate(pdf.pages, 1):
                try:
                    extracted = page.extract_text()
                    if extracted:
                        page_text = extracted.strip()
                        result['pages'].append({
                            'page_number': i,
                            'text': page_text,
                            'char_count': len(page_text),
                            'success': True
                        })
                        result['text'] += page_text + "\n\n"
                    else:
                        result['pages'].append({
                            'page_number': i,
                            'text': '',
                            'char_count': 0,
                            'success': False,
                            'error': 'No text extracted'
                        })
                        result['errors'].append(f"Page {i}: No text extracted")
                except Exception as e:
                    result['pages'].append({
                        'page_number': i,
                        'text': '',
                        'char_count': 0,
                        'success': False,
                        'error': str(e)
                    })
                    result['errors'].append(f"Page {i}: {str(e)}")
                    log.error("Error extracting PDF page %d: %s", i, e)

    except Exception as e:
        result['errors'].append(f"PDF opening error: {str(e)}")
        log.error("Error opening PDF: %s", e)

    return result


# ─────────────────────────────────────────────────────────────
# Image Extraction (Tesseract → Gemini Vision fallback)
# ─────────────────────────────────────────────────────────────

def extract_from_image(file_path: str, rotation: int = 0) -> Dict:
    """
    Extracts text from an image file.

    Strategy:
      1. Try pytesseract (fast, local OCR)
      2. If Tesseract not installed or returns empty → fall back to Gemini Vision
    """
    result = {
        'text': '',
        'pages': [],
        'page_count': 1,
        'errors': [],
        'rotation_applied': rotation
    }

    text = ""
    source_used = "none"

    # ── Step 1: Try Tesseract ───────────────────────────────
    try:
        import pytesseract
        from PIL import Image

        image = Image.open(file_path)
        if rotation in [90, 180, 270]:
            image = image.rotate(-rotation, expand=True)

        text = pytesseract.image_to_string(image).strip()
        if text:
            source_used = "tesseract"
            log.info("Tesseract extracted %d characters", len(text))
        else:
            log.warning("Tesseract returned empty text, trying Gemini Vision")

    except Exception as tesseract_err:
        log.warning("Tesseract unavailable (%s), falling back to Gemini Vision", tesseract_err)

    # ── Step 2: Gemini Vision fallback ─────────────────────
    if not text:
        text = _extract_text_with_gemini_vision(file_path)
        if text:
            source_used = "gemini_vision"
        else:
            result['errors'].append("Both Tesseract and Gemini Vision failed to extract text")

    # ── Build result ────────────────────────────────────────
    result['text'] = text
    result['pages'].append({
        'page_number': 1,
        'text': text,
        'char_count': len(text),
        'success': bool(text),
        'source': source_used
    })

    if not text:
        result['pages'][0]['error'] = "No text could be extracted"

    return result


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def extract_text(file_path: str, rotation: int = 0) -> str:
    """Legacy function — maintained for backward compatibility."""
    if file_path.lower().endswith('.pdf'):
        return extract_from_pdf(file_path)['text']
    elif file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp')):
        return extract_from_image(file_path, rotation)['text']
    return "Unsupported file format."


def extract_text_enhanced(file_path: str, rotation: int = 0) -> Dict:
    """
    Enhanced extraction with full metadata and error recovery.
    Falls back to Gemini Vision if Tesseract fails.
    """
    if file_path.lower().endswith('.pdf'):
        result = extract_from_pdf(file_path)
    elif file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp')):
        result = extract_from_image(file_path, rotation)
    else:
        return {
            'text': '',
            'pages': [],
            'page_count': 0,
            'errors': ['Unsupported file format'],
            'success_rate': 0.0
        }

    successful_pages = sum(1 for p in result['pages'] if p.get('success', False))
    total_pages = result['page_count']
    result['success_rate'] = (successful_pages / total_pages * 100) if total_pages > 0 else 0

    return result
