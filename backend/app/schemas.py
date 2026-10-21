from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.curation.tags import normalize_tags


class DatasetCreate(BaseModel):
    name: str
    owner: str = ""
    description: str

    @field_validator("name", "description")
    @classmethod
    def required_not_blank(cls, value: str, info) -> str:
        if value is None or not str(value).strip():
            raise ValueError(f"{info.field_name} is required and cannot be blank")
        return str(value).strip()

    @field_validator("owner")
    @classmethod
    def strip_owner(cls, value: str | None) -> str:
        return (value or "").strip()


class CurationResult(BaseModel):
    """Structured curator output. The LLM agent validates against this model."""

    tags: list[str] = Field(min_length=3, max_length=6)
    summary: str

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, value: list[str]) -> list[str]:
        tags = normalize_tags(value, limit=6)
        if not 3 <= len(tags) <= 6:
            raise ValueError("tags must contain between 3 and 6 labels")
        return tags

    @field_validator("summary")
    @classmethod
    def clean_summary(cls, value: str) -> str:
        text = str(value or "").strip()
        if not text.startswith("A "):
            raise ValueError("summary must be one sentence starting with 'A '")
        if text.count(".") > 1:
            raise ValueError("summary must be a single sentence")
        words = text.rstrip(".").split()
        if not (3 <= len(words) <= 25):
            raise ValueError("summary must be one sentence under 25 words")
        return text if text.endswith(".") else f"{text}."


class Dataset(BaseModel):
    id: str
    name: str
    owner: str
    description: str
    tags: list[str]
    summary: str
    curation_status: Literal["ok", "failed"] = "ok"


class ErrorResponse(BaseModel):
    error: str
