import re
from dataclasses import dataclass

ACRONYMS = {"pii": "PII", "hr": "HR"}
PUNCTUATION_RE = re.compile(r"[^\w\s/+-]+")
SPACES_RE = re.compile(r"\s+")

MAX_TAGS = 5
NOUL_THRESHOLD = 0.55


@dataclass(frozen=True)
class TagSpec:
    id: str
    meaning: str


TAG_REGISTRY: tuple[TagSpec, ...] = (
    TagSpec("finance", "Money, amounts, currencies, P&L, capital, or financial reporting"),
    TagSpec("trading", "Trades, instruments, counterparties, confirmations, or trading books"),
    TagSpec("settlements", "Settlement dates, clearing, collateral, or post-trade settlement"),
    TagSpec("transactions", "Transaction records, payments, or transfers"),
    TagSpec("inventory", "Stock levels, SKUs, quantity on hand, or reorder thresholds"),
    TagSpec("operations", "Operational processes, warehouse operations, or ops workflows"),
    TagSpec("warehouse", "Warehouse locations or stored stock"),
    TagSpec("HR", "Employees, departments, roles, or HR records"),
    TagSpec("employees", "People who work at the firm, as the data subject"),
    TagSpec("customers", "Customers or clients as the data subject"),
    TagSpec("products", "Products or SKUs as the data subject"),
    TagSpec(
        "PII",
        "The description names people-identifying fields such as customer ID, name, or email — not merely a product name",
    ),
    TagSpec("daily", "The feed or snapshot is produced daily"),
    TagSpec("weekly", "The feed or snapshot is produced weekly"),
    TagSpec("monthly", "The feed or snapshot is produced monthly"),
)


def catalogue_tag_ids() -> frozenset[str]:
    return frozenset(spec.id for spec in TAG_REGISTRY)


def normalize_tags(tags: list[str], limit: int = MAX_TAGS) -> list[str]:
    if not isinstance(tags, list):
        raise ValueError("tags must be a list")

    seen: set[str] = set()
    normalised: list[str] = []
    for raw in tags:
        if not isinstance(raw, str):
            continue
        cleaned = SPACES_RE.sub(" ", PUNCTUATION_RE.sub("", raw)).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        label = ACRONYMS.get(key, key)
        if label in seen:
            continue
        seen.add(label)
        normalised.append(label)
        if len(normalised) == limit:
            break
    return normalised
