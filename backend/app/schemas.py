from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.curation.tags import normalize_tags

TRADE_CONFIRMATIONS_CREATE = {
    "name": "Trade Confirmations",
    "owner": "Middle Office",
    "description": (
        "Daily export of confirmed trades including instrument type, "
        "counterparty, notional value, and settlement date."
    ),
}

TRADE_CONFIRMATIONS_DATASET = {
    "id": "4",
    "name": "Trade Confirmations",
    "owner": "Middle Office",
    "description": TRADE_CONFIRMATIONS_CREATE["description"],
    "tags": ["trading", "finance", "settlements", "daily"],
    "summary": "A daily export of confirmed trades covering counterparties and settlements.",
    "curation_status": "ok",
}

VALIDATION_ERROR_EXAMPLE = {"error": "name is required"}
NOT_FOUND_ERROR_EXAMPLE = {"error": "Dataset with id 'missing' was not found."}


class DatasetCreate(BaseModel):
    """Body for registering a dataset. Name and description are required."""

    model_config = ConfigDict(
        title="DatasetCreate",
        json_schema_extra={"examples": [TRADE_CONFIRMATIONS_CREATE]},
    )

    name: str = Field(examples=["Trade Confirmations"])
    owner: str = Field(default="", examples=["Middle Office"])
    description: str = Field(
        examples=[TRADE_CONFIRMATIONS_CREATE["description"]],
    )

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

    model_config = ConfigDict(title="CurationResult")

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
    """A registered catalogue entry, including curator tags and summary."""

    model_config = ConfigDict(
        title="Dataset",
        json_schema_extra={"examples": [TRADE_CONFIRMATIONS_DATASET]},
    )

    id: str = Field(examples=["4"])
    name: str = Field(examples=["Trade Confirmations"])
    owner: str = Field(examples=["Middle Office"])
    description: str = Field(examples=[TRADE_CONFIRMATIONS_CREATE["description"]])
    tags: list[str] = Field(examples=[["trading", "finance", "settlements", "daily"]])
    summary: str = Field(
        examples=["A daily export of confirmed trades covering counterparties and settlements."],
    )
    curation_status: Literal["ok", "failed"] = Field(
        default="ok",
        examples=["ok"],
        description="ok when the curator returned tags/summary; failed when placeholders were saved.",
    )


class ErrorResponse(BaseModel):
    """API error body. Always `{ \"error\": \"...\" }` — never FastAPI's default 422 shape."""

    model_config = ConfigDict(
        title="ErrorResponse",
        json_schema_extra={
            "examples": [VALIDATION_ERROR_EXAMPLE, NOT_FOUND_ERROR_EXAMPLE],
        },
    )

    error: str = Field(examples=["name is required"])
