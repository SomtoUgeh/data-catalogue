import re

from app.curation.base import CurationResult
from app.schemas import DatasetCreate

# A tag is added when any of its keywords appears as a word in the name or description.
# Dict order is the order tags are returned in.
DOMAIN_TAGS = {
    "trading": {"trade", "trades", "trading", "instrument", "counterparty", "notional"},
    "finance": {
        "finance",
        "financial",
        "transaction",
        "transactions",
        "amount",
        "currency",
        "notional",
        "payment",
        "payments",
    },
    "settlements": {"settlement", "settlements"},
    "transactions": {"transaction", "transactions"},
    "inventory": {"inventory", "stock", "sku", "reorder"},
    "operations": {"operations", "warehouse", "logistics", "shipment", "shipments"},
    "warehouse": {"warehouse", "warehouses"},
    "HR": {"hr", "employee", "employees", "payroll", "department"},
    "employees": {"employee", "employees", "staff"},
    "customers": {"customer", "customers", "client", "clients"},
}
CADENCE_TAGS = ("daily", "weekly", "monthly")

# Fields that identify a person. A bare "name" only counts when the dataset is about people,
# so "product name" does not make a dataset PII.
PERSONAL_IDENTIFIER = re.compile(r"\b(?:customer id|email|phone|address|date of birth|passport|salary)")
PEOPLE_WORDS = {"customer", "customers", "client", "clients", "employee", "employees", "staff"}

FIELD_LIST = re.compile(r"\b(?:including|with)\s+(.+)", re.IGNORECASE)
SENTENCE_END = re.compile(r"\.(?:\s|$)")
MAX_SUMMARY_WORDS = 25


class KeywordCurator:
    """Rule-based stand-in for an LLM: tags come from a keyword table, the summary from the description."""

    async def curate(self, dataset: DatasetCreate) -> CurationResult:
        tags = _tags(f"{dataset.name} {dataset.description}".lower())
        return CurationResult(tags=tags, summary=_summary(dataset.description, tags))


def _tags(text: str) -> list[str]:
    words = set(re.findall(r"[a-z0-9]+", text))
    tags = [tag for tag, keywords in DOMAIN_TAGS.items() if words & keywords]
    if PERSONAL_IDENTIFIER.search(text) or ("name" in words and words & PEOPLE_WORDS):
        tags.append("PII")
    tags.extend(cadence for cadence in CADENCE_TAGS if cadence in words)
    return tags[:6] or ["uncategorised"]


def _summary(description: str, tags: list[str]) -> str:
    """Builds "A <cadence> <domain> dataset covering <fields>." from the first sentence."""
    first_sentence = SENTENCE_END.split(description, maxsplit=1)[0].strip()
    fields = FIELD_LIST.search(first_sentence)
    if fields is None:
        return _limit_words(first_sentence)

    cadence = next((tag for tag in tags if tag in CADENCE_TAGS), None)
    domain = next((tag for tag in tags if tag in DOMAIN_TAGS), None)
    label = " ".join(word for word in (cadence, domain, "dataset") if word)
    article = "An" if label[0].lower() in "aeiou" else "A"
    return _limit_words(f"{article} {label} covering {fields.group(1)}")


def _limit_words(sentence: str) -> str:
    words = sentence.split()[:MAX_SUMMARY_WORDS]
    return " ".join(words).rstrip(".,;:") + "."
