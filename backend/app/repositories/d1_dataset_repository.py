import json
from typing import Any

from app.repositories.dataset_repository import SEED_DATASETS
from app.runtime import unwrap
from app.schemas import Dataset

_SELECT_COLUMNS = "id, name, owner, description, tags, summary, curation_status"


def _field(row: Any, key: str) -> Any:
    if row is None:
        return None
    if isinstance(row, dict):
        return row.get(key)
    return getattr(row, key, None)


def _rows(result: Any) -> list[Any]:
    if result is None:
        return []
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return list(result.get("results") or [])
    results = getattr(result, "results", None)
    if results is None:
        return []
    return list(results)


class D1DatasetRepository:
    def __init__(self, db: Any) -> None:
        self._db = db

    def list_all(self) -> list[Dataset]:
        self._ensure_seed()
        result = self._query(f"SELECT {_SELECT_COLUMNS} FROM datasets ORDER BY id ASC")
        return [self._to_dataset(row) for row in _rows(result)]

    def add(self, dataset: Dataset) -> Dataset:
        self._insert(dataset)
        return dataset.model_copy()

    def delete(self, dataset_id: str) -> Dataset | None:
        self._ensure_seed()
        if not dataset_id.isdigit():
            return None
        row = self._first(f"SELECT {_SELECT_COLUMNS} FROM datasets WHERE id = ?", int(dataset_id))
        if row is None:
            return None
        self._execute("DELETE FROM datasets WHERE id = ?", int(dataset_id))
        return self._to_dataset(row)

    def next_id(self) -> str:
        self._ensure_seed()
        row = self._first("SELECT seq FROM sqlite_sequence WHERE name = 'datasets'")
        if row is None:
            row = self._first("SELECT COALESCE(MAX(id), 0) AS seq FROM datasets")
        return str(int(_field(row, "seq") or 0) + 1)

    def _ensure_seed(self) -> None:
        row = self._first("SELECT COUNT(*) AS n FROM datasets")
        if int(_field(row, "n") or 0) > 0:
            return
        try:
            self._execute("DELETE FROM sqlite_sequence WHERE name = 'datasets'")
        except Exception:
            pass
        for item in SEED_DATASETS:
            self._insert(item)

    def _insert(self, dataset: Dataset) -> None:
        self._execute(
            "INSERT INTO datasets (id, name, owner, description, tags, summary, curation_status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            int(dataset.id),
            dataset.name,
            dataset.owner,
            dataset.description,
            json.dumps(dataset.tags),
            dataset.summary,
            dataset.curation_status,
        )

    def _to_dataset(self, row: Any) -> Dataset:
        tags = _field(row, "tags")
        if isinstance(tags, str):
            tags = json.loads(tags)
        return Dataset(
            id=str(_field(row, "id")),
            name=str(_field(row, "name")),
            owner=str(_field(row, "owner")),
            description=str(_field(row, "description")),
            tags=list(tags or []),
            summary=str(_field(row, "summary")),
            curation_status=_field(row, "curation_status") or "ok",
        )

    def _prepare(self, sql: str, *binds: Any) -> Any:
        stmt = unwrap(self._db.prepare(sql))
        if binds:
            stmt = unwrap(stmt.bind(*binds))
        return stmt

    def _query(self, sql: str, *binds: Any) -> Any:
        return unwrap(self._prepare(sql, *binds).all())

    def _first(self, sql: str, *binds: Any) -> Any:
        return unwrap(self._prepare(sql, *binds).first())

    def _execute(self, sql: str, *binds: Any) -> Any:
        return unwrap(self._prepare(sql, *binds).run())
