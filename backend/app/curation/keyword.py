import re

from app.curation.base import Curator
from app.schemas import CurationResult, DatasetCreate

# First matching keyword in the name or description assigns the tag.
# Order is the tag order we want reviewers to see.
KEYWORD_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("trading", ("trade", "trades", "trading", "counterparty", "notional", "instrument")),
    ("finance", ("finance", "currency", "amount", "notional", "transaction", "transactions")),
    ("settlements", ("settlement", "settlements", "settle")),
    ("transactions", ("transaction", "transactions")),
    ("inventory", ("inventory", "sku", "stock", "reorder")),
    ("warehouse", ("warehouse",)),
    ("operations", ("operations", "warehouse", "ops")),
    ("HR", ("employee", "employees", "hr", "department")),
    ("employees", ("employee", "employees")),
    ("daily", ("daily",)),
    ("weekly", ("weekly",)),
    ("monthly", ("monthly",)),
]

# People-identifying fields — "product name" alone should not trip this.
PII_PATTERNS = (
    r"\bcustomer id\b",
    r"\bemail\b",
    r"\bphone\b",
    r"\bssn\b",
    r"\bpii\b",
    r"\bemployees?\b.*\bname\b",
    r"\bname\b.*\b(department|role|office)\b",
)


class KeywordCurator(Curator):
    """Rule-table mock used when no LLM key is configured."""

    def curate(self, payload: DatasetCreate, dataset_id: str = "") -> CurationResult:
        haystack = f"{payload.name} {payload.description}".lower()
        words = set(re.findall(r"[a-z0-9]+", haystack))

        tags: list[str] = []
        for tag, keywords in KEYWORD_RULES:
            if any(keyword in words for keyword in keywords) and tag not in tags:
                tags.append(tag)

        if any(re.search(pattern, haystack) for pattern in PII_PATTERNS) and "PII" not in tags:
            tags.append("PII")

        if len(tags) < 3:
            for extra in ("catalogue", "dataset", "uncategorised"):
                if extra not in tags:
                    tags.append(extra)
                if len(tags) == 3:
                    break

        return CurationResult(tags=tags[:6], summary=_summarise(payload, tags))


def _summarise(payload: DatasetCreate, tags: list[str]) -> str:
    first_clause = payload.description.strip().split(".")[0].strip()
    if not first_clause:
        first_clause = payload.name
    words = first_clause.split()
    if len(words) > 18:
        first_clause = " ".join(words[:18])

    cadence = next((item for item in ("daily", "weekly", "monthly") if item in tags), None)
    lowered = first_clause[0].lower() + first_clause[1:] if first_clause else payload.name

    if cadence and lowered.startswith(cadence):
        return f"A {lowered}."
    if cadence:
        return f"A {cadence} catalogue entry for {payload.name}: {first_clause}."
    return f"A catalogue entry for {payload.name}: {first_clause}."
