from typing import List

from pydantic import BaseModel


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