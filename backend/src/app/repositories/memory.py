"""In-memory DatasetStore for local runs and tests (see base.py for the interface)."""

from app.schemas import Dataset, DatasetFields


class InMemoryDatasetStore:
    """Keeps datasets in a dict. Used for local runs and tests; data resets with the process."""

    def __init__(self, seed: list[Dataset]) -> None:
        self._datasets = {dataset.id: dataset for dataset in seed}
        self._last_id = max((int(dataset.id) for dataset in seed), default=0)

    async def list_page(self, limit: int, before: int | None) -> list[Dataset]:
        newest_first = sorted(self._datasets.values(), key=lambda dataset: int(dataset.id), reverse=True)
        return [dataset for dataset in newest_first if before is None or int(dataset.id) < before][:limit]

    async def add(self, fields: DatasetFields) -> Dataset:
        self._last_id += 1
        dataset = Dataset(id=str(self._last_id), **fields.model_dump())
        self._datasets[dataset.id] = dataset
        return dataset

    async def delete(self, dataset_id: str) -> Dataset | None:
        return self._datasets.pop(dataset_id, None)
