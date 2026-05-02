from pydantic import BaseModel
from typing import List

class OCRToken(BaseModel):
    text: str
    confidence: float
    x: int
    y: int
    width: int
    height: int

class OCRResponse(BaseModel):
    filename: str
    total_tokens: int
    tokens: List[OCRToken]
    full_text: str