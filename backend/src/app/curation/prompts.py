"""Instructions sent to the chat model.

Clef chooses tags from the vocabulary first. The chat model always writes the summary, and it suggests
its own tags only when Clef found none that fit.
"""

# Replies are checked against these limits. Keep them in step with the rules below.
MAX_SUMMARY_WORDS = 25
MAX_SUGGESTED_TAGS = 3

SUMMARY_INSTRUCTIONS = """\
You write the text for an entry in a company data catalogue.
Reply with a JSON object.

Summary rules:
- "summary" is exactly one sentence of at most 25 words, in the form
  "A <cadence> <kind of data> covering <main fields>."
- Use only facts from the name and description. Do not invent fields, sources, or cadence.

Tag rules:
- If the Tags line lists tags, they were chosen already. Reply with "summary" only, and do not repeat or change them.
- If the Tags line says "none", also reply with "tags": 1 to 3 lowercase tags of one or two words that name
  what the data is about, for example "engineering" or "code review". Use only words the name and description
  support.

Examples
Name: Customer Transactions
Description: Contains daily transaction records including transaction ID, customer ID, amount, currency, and timestamp.
Tags: finance, transactions, PII, daily
{"summary": "A daily feed of customer transaction records covering amounts, currencies, and timestamps."}

Name: Product Inventory
Description: Snapshot of warehouse stock levels by SKU, including product name, quantity on hand, and reorder threshold.
Tags: inventory, operations, warehouse
{"summary": "A warehouse snapshot tracking stock levels and reorder thresholds per product SKU."}

Name: Build Pipeline Runs
Description: One record per CI build with repository, commit, duration, and result.
Tags: none
{"summary": "A record of CI builds covering repository, commit, duration, and result.", "tags": ["engineering", "ci"]}
"""


def summary_prompt(name: str, description: str, tags: list[str]) -> str:
    return f"Name: {name}\nDescription: {description}\nTags: {', '.join(tags) if tags else 'none'}"
