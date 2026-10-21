"""The catalogue's tag vocabulary.

Both curators read it: Clef scores each tag's `meaning`, and the keyword mock matches its `keywords`.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Tag:
    id: str
    meaning: str
    keywords: frozenset[str]


def tag(id: str, meaning: str, *keywords: str) -> Tag:
    return Tag(id, meaning, frozenset(keywords))


# fmt: off
DOMAIN_TAGS = (
    tag("trading", "Trades, instruments, counterparties, confirmations, or trading books",
        "trade", "trades", "trading", "instrument", "counterparty", "notional"),
    tag("finance", "Money, amounts, currencies, P&L, capital, or financial reporting",
        "finance", "financial", "transaction", "transactions", "amount", "currency", "notional", "payment", "payments"),
    tag("settlements", "Settlement dates, clearing, collateral, or post-trade settlement",
        "settlement", "settlements"),
    tag("transactions", "Transaction records, payments, or transfers",
        "transaction", "transactions"),
    tag("inventory", "Stock levels, SKUs, quantity on hand, or reorder thresholds",
        "inventory", "stock", "sku", "reorder"),
    tag("operations", "Operational processes, warehouse operations, or ops workflows",
        "operations", "warehouse", "logistics", "shipment", "shipments"),
    tag("warehouse", "Warehouse locations or stored stock",
        "warehouse", "warehouses"),
    tag("HR", "Employees, departments, roles, or HR records",
        "hr", "employee", "employees", "payroll", "department"),
    tag("employees", "People who work at the firm, as the data subject",
        "employee", "employees", "staff"),
    tag("customers", "Customers or clients as the data subject",
        "customer", "customers", "client", "clients"),
    tag("products", "Products or SKUs as the data subject"),
    tag("sales", "Sales, orders, revenue, or units sold",
        "sales", "sale", "sold", "revenue", "orders"),
)

PII_TAG = tag(
    "PII",
    "The description names fields that identify a person, such as customer ID, a person's name, or email. "
    "A product name does not count.",
)

CADENCE_TAGS = (
    tag("daily", "The feed or snapshot is produced daily", "daily"),
    tag("weekly", "The feed or snapshot is produced weekly", "weekly"),
    tag("monthly", "The feed or snapshot is produced monthly", "monthly"),
)
# fmt: on

ALL_TAGS = (*DOMAIN_TAGS, PII_TAG, *CADENCE_TAGS)

MAX_TAGS = 5
