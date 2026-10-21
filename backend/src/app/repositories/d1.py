import json
from typing import Any

from app.schemas import Dataset, DatasetFields

COLUMNS = "id, name, owner, description, tags, summary, curation_status"


class D1DatasetStore:
    """Stores datasets in a Cloudflare D1 (SQLite) table. See migrations/ for the schema and seed rows.

    `db` is the D1 binding from the Worker env. The workers SDK converts query arguments and results
    between Python and JavaScript, so rows arrive as plain dicts.
    """

    def __init__(self, db: Any) -> None:
        self._db = db

    async def list_page(self, limit: int, before: int | None) -> list[Dataset]:
        # Keyset pagination on the primary key: each page costs one index range scan, however deep it is.
        if before is None:
            statement = self._db.prepare(f"SELECT {COLUMNS} FROM datasets ORDER BY id DESC LIMIT ?").bind(limit)
        else:
            query = f"SELECT {COLUMNS} FROM datasets WHERE id < ? ORDER BY id DESC LIMIT ?"
            statement = self._db.prepare(query).bind(before, limit)
        result = await statement.all()
        return [_to_dataset(row) for row in result["results"]]

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
        return _to_dataset(row)

    async def delete(self, dataset_id: str) -> Dataset | None:
        statement = self._db.prepare(f"DELETE FROM datasets WHERE id = ? RETURNING {COLUMNS}")
        row = await statement.bind(dataset_id).first()
        return None if row is None else _to_dataset(row)


def _to_dataset(row: dict[str, Any]) -> Dataset:
    return Dataset(**{**row, "id": str(row["id"]), "tags": json.loads(row["tags"])})
