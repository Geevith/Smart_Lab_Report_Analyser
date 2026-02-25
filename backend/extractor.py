import pdfplumber
import pytesseract
from PIL import Image
import os
from typing import Dict, List, Tuple


def extract_from_pdf(file_path: str) -> Dict:
    """
    Extracts text from a PDF file with multi-page support and quality tracking.
    
    Returns:
        Dictionary with:
        - 'text': Combined text from all pages
        - 'pages': List of page texts
        - 'page_count': Number of pages processed
        - 'errors': List of error messages for failed pages
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
                    error_msg = f"Page {i}: {str(e)}"
                    result['pages'].append({
                        'page_number': i,
                        'text': '',
                        'char_count': 0,
                        'success': False,
                        'error': str(e)
                    })
                    result['errors'].append(error_msg)
                    print(f"Error extracting PDF page {i}: {e}")
                    
    except Exception as e:
        result['errors'].append(f"PDF opening error: {str(e)}")
        print(f"Error opening PDF: {e}")
        
    return result


def extract_from_image(file_path: str, rotation: int = 0) -> Dict:
    """
    Extracts text from an image file using pytesseract with optional rotation.
    
    Args:
        file_path: Path to image file
        rotation: Rotation angle in degrees (0, 90, 180, 270)
        
    Returns:
        Dictionary with text and metadata
    """
    result = {
        'text': '',
        'pages': [],
        'page_count': 1,
        'errors': [],
        'rotation_applied': rotation
    }
    
    try:
        image = Image.open(file_path)
        
        # Apply rotation if specified
        if rotation in [90, 180, 270]:
            image = image.rotate(-rotation, expand=True)  # Negative for clockwise
        
        # Extract text
        text = pytesseract.image_to_string(image)
        
        result['text'] = text
        result['pages'].append({
            'page_number': 1,
            'text': text,
            'char_count': len(text),
            'success': True
        })
        
    except Exception as e:
        error_msg = f"Image extraction error: {str(e)}"
        result['errors'].append(error_msg)
        result['pages'].append({
            'page_number': 1,
            'text': '',
            'char_count': 0,
            'success': False,
            'error': str(e)
        })
        print(f"Error extracting Image: {e}")
        
    return result


def extract_text(file_path: str, rotation: int = 0) -> str:
    """
    Legacy function: Determines file type and extracts text (simple version).
    
    Maintained for backward compatibility.
    """
    if file_path.lower().endswith('.pdf'):
        result = extract_from_pdf(file_path)
        return result['text']
    elif file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
        result = extract_from_image(file_path, rotation)
        return result['text']
    else:
        return "Unsupported file format."


def extract_text_enhanced(file_path: str, rotation: int = 0) -> Dict:
    """
    Enhanced extraction with full metadata and error recovery.
    
    Args:
        file_path: Path to file
        rotation: Rotation angle for images (0, 90, 180, 270)
        
    Returns:
        Dictionary with:
        - text: Combined text
        - pages: Per-page details
        - page_count: Number of pages
        - errors: List of errors
        - success_rate: Percentage of successfully processed pages
    """
    if file_path.lower().endswith('.pdf'):
        result = extract_from_pdf(file_path)
    elif file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
        result = extract_from_image(file_path, rotation)
    else:
        return {
            'text': '',
            'pages': [],
            'page_count': 0,
            'errors': ['Unsupported file format'],
            'success_rate': 0.0
        }
    
    # Calculate success rate
    successful_pages = sum(1 for p in result['pages'] if p.get('success', False))
    total_pages = result['page_count']
    result['success_rate'] = (successful_pages / total_pages * 100) if total_pages > 0 else 0
    
    return result
