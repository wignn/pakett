"""
OCR Service.
Server-side OCR processing using Tesseract.
"""

import io
import logging
from typing import Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Result of OCR processing."""
    text: str
    confidence: float
    language: str
    preprocessing_applied: list


class OCRService:
    """
    Server-side OCR service using Tesseract.
    
    Includes image preprocessing for better OCR accuracy:
    - Grayscale conversion
    - Contrast enhancement
    - Denoising
    - Deskewing (optional)
    """
    
    def __init__(self):
        """Initialize OCR service."""
        self.language = settings.tesseract_lang
        self.confidence_threshold = settings.ocr_confidence_threshold
    
    def preprocess_image(
        self,
        image: Image.Image,
        enhance_contrast: bool = True,
        denoise: bool = True,
        sharpen: bool = True
    ) -> Tuple[Image.Image, list]:
        """
        Preprocess image for better OCR accuracy.
        
        Args:
            image: PIL Image to preprocess
            enhance_contrast: Whether to enhance contrast
            denoise: Whether to apply denoising
            sharpen: Whether to sharpen the image
            
        Returns:
            Tuple of (processed_image, list of preprocessing steps applied)
        """
        steps = []
        processed = image.copy()
        
        # Convert to RGB if necessary (handle RGBA, etc.)
        if processed.mode not in ('L', 'RGB'):
            processed = processed.convert('RGB')
            steps.append("convert_rgb")
        
        # Convert to grayscale
        if processed.mode != 'L':
            processed = processed.convert('L')
            steps.append("grayscale")
        
        # Enhance contrast
        if enhance_contrast:
            enhancer = ImageEnhance.Contrast(processed)
            processed = enhancer.enhance(1.5)
            steps.append("contrast_enhance")
        
        # Apply slight sharpening
        if sharpen:
            processed = processed.filter(ImageFilter.SHARPEN)
            steps.append("sharpen")
        
        # Denoise using median filter
        if denoise:
            processed = processed.filter(ImageFilter.MedianFilter(size=3))
            steps.append("denoise")
        
        # Binarization (threshold)
        threshold = 128
        processed = processed.point(lambda x: 255 if x > threshold else 0, mode='1')
        processed = processed.convert('L')  # Convert back to grayscale
        steps.append("binarize")
        
        return processed, steps
    
    def extract_text(
        self,
        image: Image.Image,
        preprocess: bool = True
    ) -> OCRResult:
        """
        Extract text from an image using Tesseract OCR.
        
        Args:
            image: PIL Image to process
            preprocess: Whether to apply preprocessing
            
        Returns:
            OCRResult with extracted text and metadata
        """
        preprocessing_steps = []
        
        if preprocess:
            image, preprocessing_steps = self.preprocess_image(image)
        
        try:
            # Get OCR data with confidence scores
            data = pytesseract.image_to_data(
                image,
                lang=self.language,
                output_type=pytesseract.Output.DICT,
                config='--psm 6'  # Assume uniform block of text
            )
            
            # Extract text and calculate average confidence
            texts = []
            confidences = []
            
            for i, conf in enumerate(data['conf']):
                if conf != -1:  # -1 means no text detected
                    text = data['text'][i].strip()
                    if text:
                        texts.append(text)
                        confidences.append(conf)
            
            full_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Normalize confidence to 0-1 range
            normalized_confidence = avg_confidence / 100.0
            
            return OCRResult(
                text=full_text,
                confidence=normalized_confidence,
                language=self.language,
                preprocessing_applied=preprocessing_steps
            )
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            raise
    
    def extract_text_from_bytes(
        self,
        image_bytes: bytes,
        preprocess: bool = True
    ) -> OCRResult:
        """
        Extract text from image bytes.
        
        Args:
            image_bytes: Raw image bytes
            preprocess: Whether to apply preprocessing
            
        Returns:
            OCRResult with extracted text
        """
        image = Image.open(io.BytesIO(image_bytes))
        return self.extract_text(image, preprocess=preprocess)
    
    def extract_text_from_file(
        self,
        file_path: str,
        preprocess: bool = True
    ) -> OCRResult:
        """
        Extract text from an image file.
        
        Args:
            file_path: Path to image file
            preprocess: Whether to apply preprocessing
            
        Returns:
            OCRResult with extracted text
        """
        image = Image.open(file_path)
        return self.extract_text(image, preprocess=preprocess)
    
    def is_low_confidence(self, confidence: float) -> bool:
        """Check if confidence is below threshold."""
        return confidence < self.confidence_threshold


# Singleton instance
_ocr_instance: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    """Get singleton OCR service instance."""
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = OCRService()
    return _ocr_instance
