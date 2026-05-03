"""Custom exceptions for the OCR API."""


class OCRException(Exception):
    """Base exception for OCR-related errors."""
    pass


class InvalidImageError(OCRException):
    """Raised when the image file is invalid or corrupted."""
    pass


class OCRProcessingError(OCRException):
    """Raised when OCR processing fails."""
    pass


class FileSizeError(OCRException):
    """Raised when the uploaded file exceeds size limits."""
    pass
