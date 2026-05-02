from fastapi import APIRouter
from src.api.v1.endpoints import ocr

api_router = APIRouter()

api_router.include_router(ocr.router, prefix="/ocr", tags=["ocr"])