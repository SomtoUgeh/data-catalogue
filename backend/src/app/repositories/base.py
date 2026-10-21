from typing import Protocol

from app.schemas import Dataset, DatasetFields


class DatasetStore(Protocol):
    """Storage for datasets. The store assigns ids, which increase with each new dataset."""

    async def list_page(self, limit: int, before: int | None) -> list[Dataset]:
        """Returns up to `limit` datasets, newest first, with ids below `before` when it is given."""
        ...

    async def add(self, fields: DatasetFields) -> Dataset: ...

    async def delete(self, dataset_id: str) -> Dataset | None:
        """Removes and returns the dataset, or returns None when the id is unknown."""
        ...
