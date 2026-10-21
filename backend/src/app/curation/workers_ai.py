import json
from typing import Any

from app.cloudflare import to_js, to_py
from app.curation.base import CurationResult
from app.schemas import DatasetCreate

INSTRUCTIONS = """\
You curate entries in a company data catalogue. Given a dataset's name and description, return tags and
a summary as a JSON object with exactly two keys: "tags" (array of strings) and "summary" (string).

Tags (3 to 6):
- Cover the business domain (for example finance, trading, inventory, HR), the subject of the records,
  and the refresh cadence (daily, weekly, monthly) when the description states it.
- Add "PII" only when the description lists fields that identify a person, such as a customer ID,
  a person's name, or an email.
- Use short lowercase words. Keep acronyms uppercase (PII, HR, SKU).
- Do not use the owner's team name as a tag.

Summary:
- Exactly one sentence of at most 25 words, in the form "A <cadence> <kind of data> covering <main fields>."
- Use only facts from the description. Do not invent fields, sources, or cadence.

Examples
Name: Customer Transactions
Description: Contains daily transaction records including transaction ID, customer ID, amount, currency, and timestamp.
{"tags": ["finance", "transactions", "PII", "daily"],
 "summary": "A daily feed of customer transaction records covering amounts, currencies, and timestamps."}

Name: Product Inventory
Description: Snapshot of warehouse stock levels by SKU, including product name, quantity on hand, and reorder threshold.
{"tags": ["inventory", "operations", "warehouse"],
 "summary": "A warehouse snapshot tracking stock levels and reorder thresholds per product SKU."}
"""


class WorkersAiCurator:
    """Asks a Workers AI chat model for tags and a summary.

    The request uses JSON mode with the CurationResult schema, and the reply is validated against the
    same schema. A malformed reply raises, and DatasetService turns that into curation_status "failed".
    """

    def __init__(self, ai: Any, model: str) -> None:
        self._ai = ai
        self._model = model

    async def curate(self, dataset: DatasetCreate) -> CurationResult:
        request = {
            "messages": [
                {"role": "system", "content": INSTRUCTIONS},
                {"role": "user", "content": f"Name: {dataset.name}\nDescription: {dataset.description}"},
            ],
            "response_format": {"type": "json_schema", "json_schema": CurationResult.model_json_schema()},
            "temperature": 0,
        }
        reply = to_py(await self._ai.run(self._model, to_js(request)))
        return parse_reply(reply)


def parse_reply(reply: Any) -> CurationResult:
    """Reads {"response": ...} where the response is the JSON object, or a string containing it."""
    response = reply["response"] if isinstance(reply, dict) else reply
    if isinstance(response, str):
        response = json.loads(response)
    return CurationResult.model_validate(response)
