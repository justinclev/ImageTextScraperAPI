from fastapi.testclient import TestClient

from src.api.v1.endpoints import ocr as ocr_endpoint
from src.core.exceptions import InvalidImageError, OCRProcessingError
from src.main import app

client = TestClient(app)


def test_extract_success(monkeypatch):
    def fake_extract_tokens(_: bytes):
        return (
            [{"text": "hello", "confidence": 98.5, "x": 1, "y": 2, "width": 3, "height": 4}],
            "hello",
        )

    monkeypatch.setattr(ocr_endpoint.OCRService, "extract_tokens", fake_extract_tokens)

    response = client.post(
        "/api/v1/ocr/extractTokens",
        files={"file": ("test.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "test.png"
    assert body["total_tokens"] == 1
    assert body["full_text"] == "hello"
    assert body["tokens"][0]["text"] == "hello"
    assert "x-request-id" in response.headers


def test_extract_rejects_invalid_content_type():
    response = client.post(
        "/api/v1/ocr/extractTokens",
        files={"file": ("test.txt", b"not-image", "text/plain")},
    )

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_extract_rejects_empty_file():
    response = client.post(
        "/api/v1/ocr/extractTokens",
        files={"file": ("empty.png", b"", "image/png")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty"


def test_extract_rejects_oversized_file():
    payload = b"a" * (ocr_endpoint.MAX_FILE_SIZE + 1)

    response = client.post(
        "/api/v1/ocr/extractTokens",
        files={"file": ("big.png", payload, "image/png")},
    )

    assert response.status_code == 413
    assert "File size exceeds maximum limit" in response.json()["detail"]


def test_extract_invalid_image_error_maps_to_400(monkeypatch):
    def fake_extract_tokens(_: bytes):
        raise InvalidImageError("Corrupted image")

    monkeypatch.setattr(ocr_endpoint.OCRService, "extract_tokens", fake_extract_tokens)

    response = client.post(
        "/api/v1/ocr/extractTokens",
        files={"file": ("bad.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Corrupted image"


def test_extract_processing_error_maps_to_500(monkeypatch):
    def fake_extract_tokens(_: bytes):
        raise OCRProcessingError("OCR engine failure")

    monkeypatch.setattr(ocr_endpoint.OCRService, "extract_tokens", fake_extract_tokens)

    response = client.post(
        "/api/v1/ocr/extractTokens",
        files={"file": ("bad.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "OCR engine failure"


def test_extract_echoes_supplied_request_id(monkeypatch):
    def fake_extract_tokens(_: bytes):
        return (
            [{"text": "hello", "confidence": 98.5, "x": 1, "y": 2, "width": 3, "height": 4}],
            "hello",
        )

    monkeypatch.setattr(ocr_endpoint.OCRService, "extract_tokens", fake_extract_tokens)

    response = client.post(
        "/api/v1/ocr/extractTokens",
        files={"file": ("test.png", b"fake-image-bytes", "image/png")},
        headers={"X-Request-ID": "req-test-123"},
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-test-123"


def test_extract_rate_limited_maps_to_429(monkeypatch):
    monkeypatch.setattr(ocr_endpoint, "check_ocr_rate_limit", lambda _: (False, 7))

    response = client.post(
        "/api/v1/ocr/extractTokens",
        files={"file": ("test.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 429
    assert response.json()["detail"] == "Rate limit exceeded. Please retry later."
    assert response.headers["retry-after"] == "7"


def test_extract_timeout_error_maps_to_500(monkeypatch):
    def fake_extract_tokens(_: bytes):
        raise OCRProcessingError("OCR processing timed out")

    monkeypatch.setattr(ocr_endpoint.OCRService, "extract_tokens", fake_extract_tokens)

    response = client.post(
        "/api/v1/ocr/extractTokens",
        files={"file": ("slow.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "OCR processing timed out"


def test_metrics_endpoint_exposes_prometheus_counters(monkeypatch):
    def fake_extract_tokens(_: bytes):
        return (
            [{"text": "hello", "confidence": 98.5, "x": 1, "y": 2, "width": 3, "height": 4}],
            "hello",
        )

    monkeypatch.setattr(ocr_endpoint.OCRService, "extract_tokens", fake_extract_tokens)

    _ = client.post(
        "/api/v1/ocr/extractTokens",
        files={"file": ("sample.png", b"fake-image-bytes", "image/png")},
    )

    metrics_response = client.get("/metrics")

    assert metrics_response.status_code == 200
    assert "http_requests_total" in metrics_response.text
    assert "ocr_requests_total" in metrics_response.text
