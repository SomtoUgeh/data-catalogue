"""Instructions sent to the summary model. Tags are chosen separately by Clef, so the model only writes the sentence."""

SUMMARY_INSTRUCTIONS = """\
You write the one-sentence summary for an entry in a company data catalogue.
Reply with a JSON object with one key, "summary".

Rules:
- Exactly one sentence of at most 25 words, in the form "A <cadence> <kind of data> covering <main fields>."
- Use only facts from the name and description. Do not invent fields, sources, or cadence.
- The tags were chosen already. Do not list or change them.

Examples
Name: Customer Transactions
Description: Contains daily transaction records including transaction ID, customer ID, amount, currency, and timestamp.
Tags: finance, transactions, PII, daily
{"summary": "A daily feed of customer transaction records covering amounts, currencies, and timestamps."}

Name: Product Inventory
Description: Snapshot of warehouse stock levels by SKU, including product name, quantity on hand, and reorder threshold.
Tags: inventory, operations, warehouse
{"summary": "A warehouse snapshot tracking stock levels and reorder thresholds per product SKU."}
"""


def summary_prompt(name: str, description: str, tags: list[str]) -> str:
    return f"Name: {name}\nDescription: {description}\nTags: {', '.join(tags)}"
