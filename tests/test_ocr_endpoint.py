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
        "/api/v1/ocr/extract",
        files={"file": ("test.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "test.png"
    assert body["total_tokens"] == 1
    assert body["full_text"] == "hello"
    assert body["tokens"][0]["text"] == "hello"


def test_extract_rejects_invalid_content_type():
    response = client.post(
        "/api/v1/ocr/extract",
        files={"file": ("test.txt", b"not-image", "text/plain")},
    )

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_extract_rejects_empty_file():
    response = client.post(
        "/api/v1/ocr/extract",
        files={"file": ("empty.png", b"", "image/png")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty"


def test_extract_rejects_oversized_file():
    payload = b"a" * (ocr_endpoint.MAX_FILE_SIZE + 1)

    response = client.post(
        "/api/v1/ocr/extract",
        files={"file": ("big.png", payload, "image/png")},
    )

    assert response.status_code == 413
    assert "File size exceeds maximum limit" in response.json()["detail"]


def test_extract_invalid_image_error_maps_to_400(monkeypatch):
    def fake_extract_tokens(_: bytes):
        raise InvalidImageError("Corrupted image")

    monkeypatch.setattr(ocr_endpoint.OCRService, "extract_tokens", fake_extract_tokens)

    response = client.post(
        "/api/v1/ocr/extract",
        files={"file": ("bad.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Corrupted image"


def test_extract_processing_error_maps_to_500(monkeypatch):
    def fake_extract_tokens(_: bytes):
        raise OCRProcessingError("OCR engine failure")

    monkeypatch.setattr(ocr_endpoint.OCRService, "extract_tokens", fake_extract_tokens)

    response = client.post(
        "/api/v1/ocr/extract",
        files={"file": ("bad.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "OCR engine failure"
