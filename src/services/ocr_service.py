import io
import logging
from typing import Any, Dict, List, Tuple

import pytesseract
from PIL import Image

from src.core.exceptions import InvalidImageError, OCRProcessingError

logger = logging.getLogger(__name__)


class OCRService:
    """Service for performing OCR operations on images."""
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def extract_tokens(file_bytes: bytes) -> Tuple[List[Dict[str, Any]], str]:
        """
        Extract text tokens from an image file.
        
        Args:
            file_bytes: Raw image file bytes
            
        Returns:
            Tuple of (tokens list, full text string)
            
        Raises:
            FileSizeError: If file exceeds max size
            InvalidImageError: If image cannot be opened
            OCRProcessingError: If OCR processing fails
        """
        if len(file_bytes) > OCRService.MAX_FILE_SIZE:
            logger.error(
                "service_file_too_large",
                extra={
                    "event": "service_file_too_large",
                    "file_size": len(file_bytes),
                    "max_file_size": OCRService.MAX_FILE_SIZE,
                },
            )
            raise OCRProcessingError(
                "File size exceeds maximum limit of "
                f"{OCRService.MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
            )
        
        try:
            image = Image.open(io.BytesIO(file_bytes))
            image.verify()  # Verify it's a valid image
            image = Image.open(io.BytesIO(file_bytes))  # Reopen after verify
        except IOError as e:
            logger.error(
                "invalid_image_payload",
                extra={
                    "event": "invalid_image_payload",
                    "error": str(e),
                },
            )
            raise InvalidImageError("The uploaded file is not a valid image or is corrupted")
        except Exception as e:
            logger.error(
                "unexpected_image_open_error",
                extra={
                    "event": "unexpected_image_open_error",
                    "error": str(e),
                },
            )
            raise InvalidImageError("Failed to process the uploaded image")
        
        try:
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        except pytesseract.TesseractNotFoundError:
            logger.error(
                "tesseract_not_found",
                extra={"event": "tesseract_not_found"},
            )
            raise OCRProcessingError("OCR engine is not properly configured on the server")
        except Exception as e:
            logger.error(
                "ocr_extraction_failed",
                extra={
                    "event": "ocr_extraction_failed",
                    "error": str(e),
                },
            )
            raise OCRProcessingError("Failed to extract text from image")
        
        tokens = []
        full_text_list = []
        
        try:
            for i in range(len(data['text'])):
                word = data['text'][i].strip()
                
                if word:
                    confidence = float(data['conf'][i])
                    # Skip very low confidence tokens
                    if confidence > 0:
                        token = {
                            "text": word,
                            "confidence": confidence,
                            "x": int(data['left'][i]),
                            "y": int(data['top'][i]),
                            "width": int(data['width'][i]),
                            "height": int(data['height'][i])
                        }
                        tokens.append(token)
                        full_text_list.append(word)
        except (KeyError, ValueError, TypeError) as e:
            logger.error(
                "ocr_result_parse_failed",
                extra={
                    "event": "ocr_result_parse_failed",
                    "error": str(e),
                },
            )
            raise OCRProcessingError("Failed to parse OCR results")
        
        logger.info(
            "ocr_tokens_extracted",
            extra={
                "event": "ocr_tokens_extracted",
                "token_count": len(tokens),
                "text_length": len(" ".join(full_text_list)),
            },
        )
        return tokens, " ".join(full_text_list)