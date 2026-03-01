"""
Quality Assessment Module for Lab Report Processing

Provides image/document quality analysis to predict OCR success
and generate actionable improvement suggestions.
"""

from PIL import Image, ImageStat
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class QualityScore:
    """Quality assessment scores for a document/image"""
    resolution_score: float  # 0.0 to 1.0
    contrast_score: float    # 0.0 to 1.0
    sharpness_score: float   # 0.0 to 1.0
    overall_score: float     # 0.0 to 1.0
    ocr_confidence: float    # Estimated OCR success probability


def assess_image(image_path: str) -> Dict:
    """
    Comprehensive image quality analysis
    
    Args:
        image_path: Path to image file
        
    Returns:
        Dictionary with quality scores and suggestions
    """
    try:
        import io
        with open(image_path, 'rb') as f:
            img_data = f.read()
        img = Image.open(io.BytesIO(img_data))
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate individual quality metrics
        resolution = _assess_resolution(img)
        contrast = _assess_contrast(img)
        sharpness = _estimate_sharpness(img)
        
        # Calculate overall score (weighted average)
        overall = (resolution * 0.3 + contrast * 0.3 + sharpness * 0.4)
        
        # Estimate OCR confidence based on quality
        ocr_conf = _estimate_ocr_confidence(overall, resolution, contrast)
        
        quality = QualityScore(
            resolution_score=resolution,
            contrast_score=contrast,
            sharpness_score=sharpness,
            overall_score=overall,
            ocr_confidence=ocr_conf
        )
        
        # Generate suggestions
        suggestions = suggest_improvements(quality, img)
            
        return {
            "resolution_score": quality.resolution_score,
            "contrast_score": quality.contrast_score,
            "sharpness_score": quality.sharpness_score,
            "overall_score": quality.overall_score,
            "ocr_confidence": quality.ocr_confidence,
            "suggestions": suggestions
        }
        
    except Exception as e:
        print(f"Quality assessment error: {e}")
        # Return default medium quality
        return {
            "resolution_score": 0.7,
            "contrast_score": 0.7,
            "sharpness_score": 0.7,
            "overall_score": 0.7,
            "ocr_confidence": 0.7,
            "suggestions": ["Could not assess image quality. Proceeding with analysis."]
        }


def _assess_resolution(img: Image.Image) -> float:
    """
    Assess image resolution quality
    
    Returns score from 0.0 (very low) to 1.0 (excellent)
    """
    width, height = img.size
    total_pixels = width * height
    
    # Resolution benchmarks for medical documents
    if total_pixels >= 4000000:  # ~2000x2000 or higher
        return 1.0
    elif total_pixels >= 2000000:  # ~1400x1400
        return 0.9
    elif total_pixels >= 1000000:  # ~1000x1000
        return 0.8
    elif total_pixels >= 500000:   # ~700x700
        return 0.6
    elif total_pixels >= 300000:   # ~550x550
        return 0.4
    else:
        return 0.2


def _assess_contrast(img: Image.Image) -> float:
    """
    Assess image contrast quality
    
    Returns score from 0.0 (very low) to 1.0 (excellent)
    """
    try:
        # Convert to grayscale for contrast analysis
        gray = img.convert('L')
        stat = ImageStat.Stat(gray)
        
        # Standard deviation is a good indicator of contrast
        std_dev = stat.stddev[0]
        
        # Normalize (typical range 0-100, but can be higher)
        # Good medical documents typically have std_dev 40-80
        if std_dev >= 60:
            return 1.0
        elif std_dev >= 40:
            return 0.8
        elif std_dev >= 25:
            return 0.6
        elif std_dev >= 15:
            return 0.4
        else:
            return 0.2
            
    except Exception as e:
        print(f"Contrast assessment error: {e}")
        return 0.7  # Default medium


def _estimate_sharpness(img: Image.Image) -> float:
    """
    Estimate image sharpness using Laplacian variance
    
    Returns score from 0.0 (very blurry) to 1.0 (sharp)
    """
    try:
        # Convert to grayscale
        gray = img.convert('L')
        
        # Resize for faster processing if too large
        if gray.size[0] * gray.size[1] > 2000000:
            gray.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
        
        # Convert to numpy array
        np_img = np.array(gray)
        
        # Calculate Laplacian variance (simple sharpness metric)
        laplacian = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
        
        # Convolve
        from scipy import signal
        filtered = signal.convolve2d(np_img, laplacian, mode='valid')
        variance = np.var(filtered)
        
        # Normalize (typical sharp images have variance > 100)
        if variance >= 500:
            return 1.0
        elif variance >= 200:
            return 0.8
        elif variance >= 100:
            return 0.6
        elif variance >= 50:
            return 0.4
        else:
            return 0.2
            
    except Exception as e:
        # Fallback if scipy not available or error occurs
        print(f"Sharpness estimation error: {e}")
        return 0.7  # Default medium


def _estimate_ocr_confidence(overall: float, resolution: float, contrast: float) -> float:
    """
    Estimate OCR success probability based on quality metrics
    
    Args:
        overall: Overall quality score
        resolution: Resolution score
        contrast: Contrast score
        
    Returns:
        Estimated OCR confidence (0.0 to 1.0)
    """
    # OCR is particularly sensitive to resolution and contrast
    ocr_conf = (overall * 0.4 + resolution * 0.3 + contrast * 0.3)
    
    # Apply minimum floor (always some chance of success)
    return max(0.3, min(1.0, ocr_conf))


def suggest_improvements(quality: QualityScore, img: Image.Image) -> List[str]:
    """
    Generate actionable suggestions for improving document quality
    
    Args:
        quality: QualityScore object
        img: PIL Image object
        
    Returns:
        List of suggestion strings
    """
    suggestions = []
    
    # Resolution suggestions
    if quality.resolution_score < 0.5:
        suggestions.append("Image resolution is low. Try scanning at 300 DPI or higher.")
    
    # Contrast suggestions
    if quality.contrast_score < 0.5:
        suggestions.append("Low contrast detected. Ensure good lighting or adjust scanner settings.")
    
    # Sharpness suggestions
    if quality.sharpness_score < 0.5:
        suggestions.append("Image appears blurry. Hold camera steady or use scanner for best results.")
    
    # Overall quality suggestions
    if quality.overall_score < 0.4:
        suggestions.append("Consider re-scanning or re-photographing the document for better results.")
    
    # Image size suggestions
    width, height = img.size
    if width < 800 or height < 800:
        suggestions.append("Image dimensions are small. Use a higher resolution camera or scanner.")
    
    # Rotation detection (basic heuristic)
    aspect_ratio = width / height if height > 0 else 1.0
    if aspect_ratio > 1.5 or aspect_ratio < 0.67:
        suggestions.append("Document may need rotation. Use rotation controls if text appears sideways.")
    
    # If everything looks good
    if not suggestions:
        suggestions.append("Document quality is excellent. Ready for analysis.")
    
    return suggestions


def detect_rotation(image_path: str) -> int:
    """
    Detect if image needs rotation (basic implementation)
    
    Returns:
        Suggested rotation in degrees (0, 90, 180, 270)
    """
    # Placeholder - advanced rotation detection would use:
    # - Text orientation detection
    # - Hough line transform
    # - ML-based orientation classifier
    
    # For now, return 0 (no rotation suggested)
    # This can be enhanced later with pytesseract.image_to_osd()
    return 0


def apply_image_enhancements(img: Image.Image) -> Image.Image:
    """
    Apply automatic image enhancements for better OCR
    
    Args:
        img: PIL Image object
        
    Returns:
        Enhanced PIL Image
    """
    from PIL import ImageEnhance
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)  # 30% contrast boost
    
    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.2)  # 20% sharpness boost
    
    return img
