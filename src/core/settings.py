import os
from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class Settings:
    max_file_size_bytes: int = int(os.getenv("MAX_FILE_SIZE_BYTES", str(10 * 1024 * 1024)))
    ocr_timeout_seconds: int = int(os.getenv("OCR_TIMEOUT_SECONDS", "8"))
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    allowed_content_types: FrozenSet[str] = frozenset(
        {
            "image/jpeg",
            "image/png",
            "image/tiff",
            "image/webp",
        }
    )


settings = Settings()
