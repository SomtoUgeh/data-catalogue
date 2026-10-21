import json
from typing import Any

from app.cloudflare import to_py
from app.schemas import Dataset, DatasetFields

COLUMNS = "id, name, owner, description, tags, summary, curation_status"


class D1DatasetStore:
    """Stores datasets in a Cloudflare D1 (SQLite) table. See migrations/ for the schema and seed rows."""

    def __init__(self, db: Any) -> None:
        self._db = db

    async def list(self) -> list[Dataset]:
        result = await self._db.prepare(f"SELECT {COLUMNS} FROM datasets ORDER BY id").all()
        return [_to_dataset(row) for row in to_py(result.results)]

    async def add(self, fields: DatasetFields) -> Dataset:
        row = await (
            self._db.prepare(
                "INSERT INTO datasets (name, owner, description, tags, summary, curation_status) "
                f"VALUES (?, ?, ?, ?, ?, ?) RETURNING {COLUMNS}"
            )
            .bind(
                fields.name,
                fields.owner,
                fields.description,
                json.dumps(fields.tags),
                fields.summary,
                fields.curation_status,
            )
            .first()
        )
        return _to_dataset(to_py(row))

    async def delete(self, dataset_id: str) -> Dataset | None:
        statement = self._db.prepare(f"DELETE FROM datasets WHERE id = ? RETURNING {COLUMNS}")
        row = await statement.bind(dataset_id).first()
        return None if row is None else _to_dataset(to_py(row))


def _to_dataset(row: dict[str, Any]) -> Dataset:
    return Dataset(**{**row, "id": str(row["id"]), "tags": json.loads(row["tags"])})
