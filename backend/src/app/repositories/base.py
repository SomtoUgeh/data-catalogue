from typing import Protocol

from app.schemas import Dataset, DatasetFields


class DatasetStore(Protocol):
    """Storage for datasets. The store assigns ids."""

    async def list(self) -> list[Dataset]: ...

    async def add(self, fields: DatasetFields) -> Dataset: ...

    async def delete(self, dataset_id: str) -> Dataset | None:
        """Removes and returns the dataset, or returns None when the id is unknown."""
        ...
