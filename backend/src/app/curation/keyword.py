import re

from app.curation.base import CurationResult
from app.curation.tags import CADENCE_TAGS, DOMAIN_TAGS, MAX_TAGS, PII_TAG
from app.schemas import DatasetCreate

# Fields that identify a person. A bare "name" only counts when the dataset is about people,
# so "product name" does not make a dataset PII.
PERSONAL_IDENTIFIER = re.compile(r"\b(?:customer id|email|phone|address|date of birth|passport|salary)")
PEOPLE_WORDS = {"customer", "customers", "client", "clients", "employee", "employees", "staff"}

FIELD_LIST = re.compile(r"\b(?:including|with)\s+(.+)", re.IGNORECASE)
SENTENCE_END = re.compile(r"\.(?:\s|$)")
MAX_SUMMARY_WORDS = 25


class KeywordCurator:
    """Rule-based stand-in for the AI curator: tags come from the vocabulary's keywords, the summary from the text."""

    async def curate(self, dataset: DatasetCreate) -> CurationResult:
        tags = _tags(f"{dataset.name} {dataset.description}".lower())
        return CurationResult(tags=tags, summary=_summary(dataset.description, tags))


def _tags(text: str) -> list[str]:
    words = set(re.findall(r"[a-z0-9]+", text))
    tags = [tag.id for tag in DOMAIN_TAGS if words & tag.keywords]
    if PERSONAL_IDENTIFIER.search(text) or ("name" in words and words & PEOPLE_WORDS):
        tags.append(PII_TAG.id)
    tags.extend(tag.id for tag in CADENCE_TAGS if words & tag.keywords)
    return tags[:MAX_TAGS] or ["uncategorised"]


def _summary(description: str, tags: list[str]) -> str:
    """Builds "A <cadence> <domain> dataset covering <fields>." from the first sentence."""
    first_sentence = SENTENCE_END.split(description, maxsplit=1)[0].strip()
    fields = FIELD_LIST.search(first_sentence)
    if fields is None:
        return _limit_words(first_sentence)

    cadence = next((tag for tag in tags if tag in {t.id for t in CADENCE_TAGS}), None)
    domain = next((tag for tag in tags if tag in {t.id for t in DOMAIN_TAGS}), None)
    label = " ".join(word for word in (cadence, domain, "dataset") if word)
    article = "An" if label[0].lower() in "aeiou" else "A"
    return _limit_words(f"{article} {label} covering {fields.group(1)}")


def _limit_words(sentence: str) -> str:
    words = sentence.split()[:MAX_SUMMARY_WORDS]
    return " ".join(words).rstrip(".,;:") + "."
