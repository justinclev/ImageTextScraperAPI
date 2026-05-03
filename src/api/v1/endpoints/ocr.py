import logging
from typing import List

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from src.core.exceptions import (
    InvalidImageError,
    OCRProcessingError,
)
from src.core.metrics import record_ocr_outcome
from src.core.rate_limiter import check_ocr_rate_limit
from src.core.settings import settings
from src.schemas.ocr import OCRResponse, OCRToken
from src.services.ocr_service import OCRService

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_CONTENT_TYPES = settings.allowed_content_types
MAX_FILE_SIZE = settings.max_file_size_bytes


@router.post("/extractTokens", response_model=OCRResponse)
async def run_ocr(request: Request, file: UploadFile = File(...)):
    """
    Extract text from an uploaded image using OCR.
    
    Args:
        file: Image file to process (JPEG, PNG, TIFF, or WebP)
        
    Returns:
        OCRResponse with extracted tokens and full text
        
    Raises:
        HTTPException: For validation or processing errors
    """
    client_key = request.client.host if request.client else "unknown"
    is_allowed, retry_after_seconds = check_ocr_rate_limit(client_key)
    if not is_allowed:
        record_ocr_outcome("rate_limited")
        logger.warning(
            "rate_limited",
            extra={
                "event": "rate_limited",
                "client_key": client_key,
                "retry_after_seconds": retry_after_seconds,
                "path": request.url.path,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please retry later.",
            headers={"Retry-After": str(retry_after_seconds)},
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        record_ocr_outcome("invalid_content_type")
        logger.warning(
            "invalid_content_type",
            extra={
                "event": "invalid_content_type",
                "content_type": file.content_type,
                "uploaded_filename": file.filename,
                "path": request.url.path,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )
    
    if not file.filename:
        record_ocr_outcome("missing_filename")
        logger.warning(
            "missing_filename",
            extra={
                "event": "missing_filename",
                "path": request.url.path,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename"
        )
    
    try:
        file_bytes = await file.read()
        
        if len(file_bytes) > MAX_FILE_SIZE:
            record_ocr_outcome("file_too_large")
            logger.warning(
                "file_too_large",
                extra={
                    "event": "file_too_large",
                    "uploaded_filename": file.filename,
                    "file_size": len(file_bytes),
                    "max_file_size": MAX_FILE_SIZE,
                    "path": request.url.path,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
            )
        
        if not file_bytes:
            record_ocr_outcome("empty_file")
            logger.warning(
                "empty_file",
                extra={
                    "event": "empty_file",
                    "uploaded_filename": file.filename,
                    "path": request.url.path,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )
        
        tokens: List[dict] = []
        full_text: str = ""
        
        try:
            tokens, full_text = OCRService.extract_tokens(file_bytes)
        except InvalidImageError as e:
            record_ocr_outcome("invalid_image")
            logger.error(
                "invalid_image",
                extra={
                    "event": "invalid_image",
                    "uploaded_filename": file.filename,
                    "error": str(e),
                    "path": request.url.path,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except OCRProcessingError as e:
            record_ocr_outcome("ocr_error")
            logger.error(
                "ocr_processing_error",
                extra={
                    "event": "ocr_processing_error",
                    "uploaded_filename": file.filename,
                    "error": str(e),
                    "path": request.url.path,
                },
            )
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
        
        logger.info(
            "ocr_processed",
            extra={
                "event": "ocr_processed",
                "uploaded_filename": file.filename,
                "tokens": len(tokens),
                "path": request.url.path,
            },
        )
        record_ocr_outcome("success")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        record_ocr_outcome("unexpected_error")
        logger.exception(
            "unexpected_ocr_error",
            extra={
                "event": "unexpected_ocr_error",
                "uploaded_filename": file.filename,
                "error": str(e),
                "path": request.url.path,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request"
        )