import asyncio

import pytest

from app.curation.keyword import KeywordCurator
from app.schemas import DatasetCreate


def curate(name: str, description: str) -> tuple[list[str], str]:
    result = asyncio.run(KeywordCurator().curate(DatasetCreate(name=name, description=description)))
    return result.tags, result.summary


@pytest.mark.parametrize(
    ("name", "description", "expected_tags"),
    [
        (
            "Employee Directory",
            "List of current employees with name, department, role, and office location. Updated weekly.",
            ["HR", "employees", "PII", "weekly"],
        ),
        (
            "Customer Contacts",
            "Customer email addresses and phone numbers.",
            ["customers", "PII"],
        ),
        (
            "Product Inventory",
            "Snapshot of warehouse stock levels by SKU, including product name and reorder threshold.",
            ["inventory", "operations", "warehouse"],
        ),
        ("Device Sales", "Smartphone sales by region.", ["sales"]),
        ("Misc", "Assorted notes.", ["uncategorised"]),
    ],
)
def test_tags_follow_the_keyword_rules(name: str, description: str, expected_tags: list[str]) -> None:
    tags, _ = curate(name, description)

    assert tags == expected_tags


def test_summary_falls_back_to_the_first_sentence_without_a_field_list() -> None:
    _, summary = curate("Misc", "Assorted notes from the team. Updated rarely.")

    assert summary == "Assorted notes from the team."


def test_summary_is_one_sentence_of_at_most_25_words_for_long_descriptions() -> None:
    _, summary = curate("Logs", "Application logs from service v1.2 with " + "field, " * 80 + "and level")

    assert summary.startswith("A dataset covering field, field")
    assert summary.endswith(".")
    assert len(summary.split()) == 25
