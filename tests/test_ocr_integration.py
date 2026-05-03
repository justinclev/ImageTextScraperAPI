import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"
client = TestClient(app)


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="tesseract not installed")
def test_extract_real_sample_image_returns_tokens():
    image_path = FIXTURES_DIR / "sample_hello.png"
    with image_path.open("rb") as file_handle:
        response = client.post(
            "/api/v1/ocr/extractTokens",
            files={"file": ("sample_hello.png", file_handle, "image/png")},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"] == "sample_hello.png"
    assert payload["total_tokens"] > 0
    assert len(payload["full_text"].strip()) > 0
    assert "x-request-id" in response.headers


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="tesseract not installed")
def test_extract_real_sample_image_contains_expected_text_fragment():
    image_path = FIXTURES_DIR / "sample_hello.png"
    with image_path.open("rb") as file_handle:
        response = client.post(
            "/api/v1/ocr/extractTokens",
            files={"file": ("sample_hello.png", file_handle, "image/png")},
        )

    assert response.status_code == 200
    full_text_normalized = response.json()["full_text"].upper()
    assert "HELLO" in full_text_normalized
