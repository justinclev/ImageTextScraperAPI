from fastapi import FastAPI

from src.api.v1.api import api_router

app = FastAPI(
    title="Image Text Scraper API",
    description="Image scraper for extracting text from images using OCR technology.",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy", "message": "API is up and running!", "version": app.version}