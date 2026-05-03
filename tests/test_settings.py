import pytest
from pydantic import ValidationError

from src.core.settings import Settings


def test_settings_reads_uppercase_env_vars(monkeypatch):
    monkeypatch.setenv("MAX_FILE_SIZE_BYTES", "2048")
    monkeypatch.setenv("OCR_TIMEOUT_SECONDS", "12")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "55")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "90")

    configured_settings = Settings()

    assert configured_settings.max_file_size_bytes == 2048
    assert configured_settings.ocr_timeout_seconds == 12
    assert configured_settings.rate_limit_requests == 55
    assert configured_settings.rate_limit_window_seconds == 90


def test_settings_parses_csv_allowed_content_types(monkeypatch):
    monkeypatch.setenv("ALLOWED_CONTENT_TYPES", "image/png, image/jpeg, image/webp")

    configured_settings = Settings()

    assert configured_settings.allowed_content_types == frozenset(
        {"image/png", "image/jpeg", "image/webp"}
    )


@pytest.mark.parametrize(
    ("env_name", "env_value"),
    [
        ("MAX_FILE_SIZE_BYTES", "0"),
        ("OCR_TIMEOUT_SECONDS", "0"),
        ("RATE_LIMIT_REQUESTS", "0"),
        ("RATE_LIMIT_WINDOW_SECONDS", "0"),
    ],
)
def test_settings_rejects_non_positive_numeric_values(monkeypatch, env_name, env_value):
    monkeypatch.setenv(env_name, env_value)

    with pytest.raises(ValidationError):
        Settings()
