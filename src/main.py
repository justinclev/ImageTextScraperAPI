import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request

from src.api.v1.api import api_router
from src.core.observability import configure_logging
from src.core.request_context import reset_request_id, set_request_id

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Image Text Scraper API",
    description="Image scraper for extracting text from images using OCR technology.",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api/v1")


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    token = set_request_id(request_id)
    started_at = time.perf_counter()

    logger.info(
        "request_started",
        extra={
            "event": "request_started",
            "method": request.method,
            "path": request.url.path,
        },
    )

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info(
            "request_completed",
            extra={
                "event": "request_completed",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
    except Exception:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.exception(
            "request_failed",
            extra={
                "event": "request_failed",
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
        )
        raise
    finally:
        reset_request_id(token)

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy", "message": "API is up and running!", "version": app.version}