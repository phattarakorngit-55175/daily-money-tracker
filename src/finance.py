"""Pure finance calculations and validation helpers."""
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

EXPENSE_CATEGORIES = [
    "Food", "Transport", "Shopping", "Bills", "Education",
    "Entertainment", "Health", "Other",
]
INCOME_CATEGORIES = ["Salary", "Allowance", "Investment", "Other"]


def to_minor_units(raw: str) -> int:
    try:
        value = Decimal(raw.strip().replace(",", ""))
    except (InvalidOperation, AttributeError):
        raise ValueError("Enter a valid amount.")
    if not value.is_finite() or value <= 0:
        raise ValueError("Amount must be greater than zero.")
    if value > Decimal("999999999.99"):
        raise ValueError("Amount is too large.")
    minor_units = int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if minor_units <= 0:
        raise ValueError("Amount must be at least 0.01.")
    return minor_units


def format_money(minor_units: int, currency: str = "THB") -> str:
    amount = Decimal(int(minor_units)) / 100
    symbol = "฿" if currency == "THB" else "$"
    return f"{symbol}{amount:,.2f}"


def month_key(value: date) -> str:
    return value.strftime("%Y-%m")


def month_label(value: date) -> str:
    return value.strftime("%B %Y")


def totals(transactions: list[dict]) -> dict[str, int]:
    income = sum(t["amount"] for t in transactions if t["type"] == "income")
    expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
    return {"income": income, "expenses": expenses, "balance": income - expenses}


def category_totals(transactions: list[dict]) -> list[tuple[str, int]]:
    totals_by_category: dict[str, int] = {}
    for item in transactions:
        if item["type"] == "expense":
            totals_by_category[item["category"]] = totals_by_category.get(item["category"], 0) + item["amount"]
    return sorted(totals_by_category.items(), key=lambda pair: pair[1], reverse=True)
