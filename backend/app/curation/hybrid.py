from app.curation.base import Curator
from app.curation.classifier import ClassifierCurator
from app.curation.keyword import KeywordCurator, summarise_dataset
from app.curation.llm import LlmCurator
from app.schemas import CurationResult, DatasetCreate


class HybridCurator(Curator):
    """Jev (or Clef) picks tags. The LLM writes the summary. Keyword fills gaps."""

    def __init__(
        self,
        classifier: ClassifierCurator,
        summarizer: LlmCurator | None = None,
        fallback: Curator | None = None,
    ) -> None:
        self.classifier = classifier
        self.summarizer = summarizer
        self.fallback = fallback or KeywordCurator()

    def curate(self, payload: DatasetCreate, dataset_id: str = "") -> CurationResult:
        try:
            tags = self.classifier.classify(payload, dataset_id=dataset_id)
        except Exception:
            return self.fallback.curate(payload, dataset_id=dataset_id)

        if self.summarizer is not None:
            try:
                summary = self.summarizer.summarise(payload, tags, dataset_id=dataset_id)
                return CurationResult(tags=tags, summary=summary)
            except Exception:
                pass

        return CurationResult(tags=tags, summary=summarise_dataset(payload, tags))
