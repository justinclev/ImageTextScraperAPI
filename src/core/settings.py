from typing import Annotated, FrozenSet

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEFAULT_ALLOWED_CONTENT_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/tiff",
        "image/webp",
    }
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        frozen=True,
        extra="ignore",
    )

    max_file_size_bytes: int = Field(
        default=10 * 1024 * 1024,
        validation_alias="MAX_FILE_SIZE_BYTES",
        gt=0,
    )
    ocr_timeout_seconds: int = Field(
        default=8,
        validation_alias="OCR_TIMEOUT_SECONDS",
        gt=0,
    )
    rate_limit_requests: int = Field(
        default=20,
        validation_alias="RATE_LIMIT_REQUESTS",
        gt=0,
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        validation_alias="RATE_LIMIT_WINDOW_SECONDS",
        gt=0,
    )
    allowed_content_types: Annotated[FrozenSet[str], NoDecode] = Field(
        default_factory=lambda: DEFAULT_ALLOWED_CONTENT_TYPES,
        validation_alias="ALLOWED_CONTENT_TYPES",
    )

    @field_validator("allowed_content_types", mode="before")
    @classmethod
    def parse_allowed_content_types(cls, value: object) -> object:
        if isinstance(value, str):
            return frozenset(
                item.strip()
                for item in value.split(",")
                if item.strip()
            )
        return value

    @field_validator("allowed_content_types")
    @classmethod
    def validate_allowed_content_types(cls, value: FrozenSet[str]) -> FrozenSet[str]:
        if not value:
            msg = "allowed_content_types must contain at least one MIME type"
            raise ValueError(msg)

        invalid_content_types = [item for item in value if "/" not in item]
        if invalid_content_types:
            msg = "allowed_content_types entries must be valid MIME types"
            raise ValueError(msg)

        return value


settings = Settings()
