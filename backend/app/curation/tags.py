import re

ACRONYMS = {"pii": "PII", "hr": "HR"}
PUNCTUATION_RE = re.compile(r"[^\w\s/+-]+")
SPACES_RE = re.compile(r"\s+")


def normalize_tags(tags: list[str], limit: int = 6) -> list[str]:
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
