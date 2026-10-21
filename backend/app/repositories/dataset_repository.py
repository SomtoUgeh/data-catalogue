from threading import Lock

from app.schemas import Dataset

SEED_DATASETS = [
    Dataset(
        id="1",
        name="Customer Transactions",
        owner="Finance Team",
        description=(
            "Contains daily transaction records including transaction ID, "
            "customer ID, amount, currency, and timestamp."
        ),
        tags=["finance", "transactions", "PII", "daily"],
        summary="A daily feed of customer transaction records covering amounts, currencies, and timestamps.",
        curation_status="ok",
    ),
    Dataset(
        id="2",
        name="Product Inventory",
        owner="Operations Team",
        description=(
            "Snapshot of warehouse stock levels by SKU, including product name, "
            "quantity on hand, and reorder threshold."
        ),
        tags=["inventory", "operations", "warehouse"],
        summary="A warehouse snapshot tracking stock levels and reorder thresholds per product SKU.",
        curation_status="ok",
    ),
    Dataset(
        id="3",
        name="Employee Directory",
        owner="HR Team",
        description=(
            "List of current employees with name, department, role, and office location. "
            "Updated weekly."
        ),
        tags=["HR", "PII", "employees", "weekly"],
        summary="A weekly-refreshed directory of employees including role, department, and location.",
        curation_status="ok",
    ),
]


class DatasetRepository:
    """In-memory store. Fine for the take-home; swap this class for a database later."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._items: dict[str, Dataset] = {}
        self._next_id = 1
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self._items = {item.id: item.model_copy() for item in SEED_DATASETS}
            self._next_id = max(int(item_id) for item_id in self._items) + 1

    def list_all(self) -> list[Dataset]:
        with self._lock:
            return [item.model_copy() for item in self._items.values()]

    def add(self, dataset: Dataset) -> Dataset:
        with self._lock:
            self._items[dataset.id] = dataset.model_copy()
            return dataset.model_copy()

    def delete(self, dataset_id: str) -> Dataset | None:
        with self._lock:
            item = self._items.pop(dataset_id, None)
            return item.model_copy() if item else None

    def next_id(self) -> str:
        with self._lock:
            dataset_id = str(self._next_id)
            self._next_id += 1
            return dataset_id
