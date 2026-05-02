from fastapi import APIRouter, UploadFile, File, HTTPException
from src.services.ocr_service import OCRService
from src.schemas.ocr import OCRResponse

router = APIRouter()

@router.post("/extract", response_model=OCRResponse)
async def run_ocr(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
    
    try:
        file_bytes = await file.read()
        tokens, full_text = OCRService.extract_tokens(file_bytes)
        
        response = OCRResponse(
            filename=file.filename,
            total_tokens=len(tokens),
            tokens=tokens,
            full_text=full_text,
            language="eng"
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")