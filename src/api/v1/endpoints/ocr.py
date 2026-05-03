import logging
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from src.services.ocr_service import OCRService
from src.schemas.ocr import OCRResponse, OCRToken
from src.core.exceptions import (
    InvalidImageError,
    OCRProcessingError,
)

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/tiff", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/extract", response_model=OCRResponse)
async def run_ocr(file: UploadFile = File(...)):
    """
    Extract text from an uploaded image using OCR.
    
    Args:
        file: Image file to process (JPEG, PNG, TIFF, or WebP)
        
    Returns:
        OCRResponse with extracted tokens and full text
        
    Raises:
        HTTPException: For validation or processing errors
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        logger.warning(
            f"Invalid content type: {file.content_type} for file {file.filename}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )
    
    if not file.filename:
        logger.warning("Upload request missing filename")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename"
        )
    
    try:
        file_bytes = await file.read()
        
        if len(file_bytes) > MAX_FILE_SIZE:
            logger.warning(f"File {file.filename} exceeds size limit")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
            )
        
        if not file_bytes:
            logger.warning(f"Empty file uploaded: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )
        
        tokens: List[dict] = []
        full_text: str = ""
        
        try:
            tokens, full_text = OCRService.extract_tokens(file_bytes)
        except InvalidImageError as e:
            logger.error(f"Invalid image error for {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except OCRProcessingError as e:
            logger.error(f"OCR processing error for {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        
        response = OCRResponse(
            filename=file.filename,
            total_tokens=len(tokens),
            tokens=[OCRToken(**token) for token in tokens],
            full_text=full_text
        )
        
        logger.info(f"Successfully processed {file.filename}: {len(tokens)} tokens extracted")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request"
        )