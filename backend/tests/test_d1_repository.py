from app.repositories.d1_dataset_repository import D1DatasetRepository
from app.repositories.dataset_repository import SEED_DATASETS
from app.schemas import Dataset

TRADE = Dataset(
    id="4",
    name="Trade Confirmations",
    owner="Middle Office",
    description="Daily export of confirmed trades.",
    tags=["trading", "finance", "daily"],
    summary="A daily export of confirmed trades covering counterparties and settlements.",
    curation_status="ok",
)


class FakeStatement:
    def __init__(self, db: "FakeD1", sql: str, binds: tuple = ()) -> None:
        self.db = db
        self.sql = sql
        self.binds = binds

    def bind(self, *binds: object) -> "FakeStatement":
        return FakeStatement(self.db, self.sql, binds)

    def all(self) -> dict:
        return {"results": self.db.select(self.sql, self.binds)}

    def first(self) -> dict | None:
        rows = self.db.select(self.sql, self.binds)
        return rows[0] if rows else None

    def run(self) -> dict:
        self.db.execute(self.sql, self.binds)
        return {"success": True}


class FakeD1:
    def __init__(self) -> None:
        self.rows: dict[int, dict] = {}
        self.seq = 0

    def prepare(self, sql: str) -> FakeStatement:
        return FakeStatement(self, sql)

    def select(self, sql: str, binds: tuple) -> list[dict]:
        text = " ".join(sql.split())
        if "FROM sqlite_sequence" in text:
            if not self.rows and self.seq == 0:
                return []
            return [{"seq": self.seq}]
        if "COUNT(*)" in text:
            return [{"n": len(self.rows)}]
        if "COALESCE(MAX(id)" in text:
            return [{"seq": max(self.rows) if self.rows else 0}]
        if "WHERE id = ?" in text:
            dataset_id = int(binds[0])
            row = self.rows.get(dataset_id)
            return [row] if row else []
        return [self.rows[key] for key in sorted(self.rows)]

    def execute(self, sql: str, binds: tuple) -> None:
        text = " ".join(sql.split())
        if text.startswith("INSERT"):
            dataset_id = int(binds[0])
            self.rows[dataset_id] = {
                "id": dataset_id,
                "name": binds[1],
                "owner": binds[2],
                "description": binds[3],
                "tags": binds[4],
                "summary": binds[5],
                "curation_status": binds[6],
            }
            self.seq = max(self.seq, dataset_id)
            return
        if "sqlite_sequence" in text and text.startswith("DELETE"):
            self.seq = 0
            return
        if text.startswith("DELETE"):
            self.rows.pop(int(binds[0]), None)


def test_d1_lists_the_three_brief_seeds() -> None:
    repo = D1DatasetRepository(FakeD1())
    rows = repo.list_all()
    assert [item.id for item in rows] == [item.id for item in SEED_DATASETS]
    assert [item.name for item in rows] == [item.name for item in SEED_DATASETS]
    customer = next(item for item in rows if item.id == "1")
    assert customer.tags == ["finance", "transactions", "PII", "daily"]
    assert customer.owner == "Finance Team"


def test_d1_add_delete_and_next_id_do_not_reuse_ids() -> None:
    repo = D1DatasetRepository(FakeD1())
    assert repo.next_id() == "4"
    saved = repo.add(TRADE)
    assert saved.id == "4"
    assert any(item.id == "4" for item in repo.list_all())

    deleted = repo.delete("1")
    assert deleted is not None
    assert deleted.id == "1"
    assert all(item.id != "1" for item in repo.list_all())
    assert repo.next_id() == "5"
    assert repo.delete("missing") is None
