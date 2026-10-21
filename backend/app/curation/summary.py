import json

from pydantic import ValidationError

from app.curation.base import CurationError
from app.schemas import DatasetCreate, SummaryResult

SUMMARY_INSTRUCTIONS = """You write one catalogue summary sentence.

Return a JSON object that matches the provided schema.

Rules:
- one sentence, under 25 words, starts with "A "
- derive it from the name, description, and tags
- do not invent tags or change the tags you were given

Examples:
name: Customer Transactions
description: Contains daily transaction records including transaction ID, customer ID, amount, currency, and timestamp.
tags: finance, transactions, PII, daily
{"summary": "A daily feed of customer transaction records covering amounts, currencies, and timestamps."}

name: Product Inventory
description: Snapshot of warehouse stock levels by SKU, including product name, quantity on hand, and reorder threshold.
tags: inventory, operations, warehouse
{"summary": "A warehouse snapshot tracking stock levels and reorder thresholds per product SKU."}
"""


def summary_user_prompt(payload: DatasetCreate, tags: list[str]) -> str:
    return (
        f"name: {payload.name}\n"
        f"description: {payload.description}\n"
        f"tags: {', '.join(tags)}\n"
        "Write only the one-sentence summary. Do not change the tags."
    )


def parse_summary(text: str) -> str:
    raw = (text or "").strip()
    data: dict | None = None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end > start:
            try:
                parsed = json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                parsed = None
        else:
            parsed = None
    if isinstance(parsed, dict):
        data = parsed
    elif isinstance(parsed, str):
        data = {"summary": parsed}
    if data is None:
        data = {"summary": raw}
    try:
        return SummaryResult.model_validate(data).summary
    except ValidationError as exc:
        raise CurationError("summary failed validation") from exc
