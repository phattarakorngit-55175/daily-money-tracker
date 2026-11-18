"""Searchable and filterable transaction history."""
import flet as ft

from components.transaction_card import build as transaction_card
from finance import EXPENSE_CATEGORIES, INCOME_CATEGORIES
from theme import ACCENT, CARD, MUTED, TEXT, card, label


def build(app) -> ft.Control:
    search = ft.TextField(label="Search transactions", prefix_icon=ft.Icons.SEARCH,
                          hint_text="Search notes or categories", expand=True)
    type_filter = ft.Dropdown(value="All types", options=[ft.DropdownOption(text=x) for x in ["All types", "Income", "Expense"]],
                              width=138, text_size=12)
    category_filter = ft.Dropdown(value="All categories", options=[ft.DropdownOption(text="All categories")],
                                  width=165, text_size=12)
    sort_filter = ft.Dropdown(value="Newest first", options=[ft.DropdownOption(text=x) for x in ["Newest first", "Oldest first", "Amount: high to low", "Amount: low to high"]],
                              width=180, text_size=12)
    list_slot = ft.Column(spacing=9)
    count_label = ft.Text("", size=12, color=MUTED)

    def update_category_options():
        kind = type_filter.value
        cats = (INCOME_CATEGORIES if kind == "Income" else EXPENSE_CATEGORIES if kind == "Expense"
                else list(dict.fromkeys(INCOME_CATEGORIES + EXPENSE_CATEGORIES)))
        options = ["All categories"] + cats
        category_filter.options = [ft.DropdownOption(text=value) for value in options]
        if category_filter.value not in options:
            category_filter.value = "All categories"

    def render_items():
        update_category_options()
        query = (search.value or "").casefold().strip()
        kind = type_filter.value
        category = category_filter.value
        rows = [item for item in app.transactions
                if (kind == "All types" or item["type"] == kind.lower())
                and (category == "All categories" or item["category"] == category)
                and (not query or query in item["category"].casefold() or query in item.get("note", "").casefold())]
        if sort_filter.value == "Oldest first":
            rows.sort(key=lambda t: (t["date"], t["created_at"]))
        elif sort_filter.value == "Amount: high to low":
            rows.sort(key=lambda t: t["amount"], reverse=True)
        elif sort_filter.value == "Amount: low to high":
            rows.sort(key=lambda t: t["amount"])
        else:
            rows.sort(key=lambda t: (t["date"], t["created_at"]), reverse=True)
        count_label.value = f"{len(rows)} transaction" + ("s" if len(rows) != 1 else "")
        list_slot.controls = [transaction_card(app, item) for item in rows] if rows else [
            card(ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8, controls=[
                ft.Icon(ft.Icons.SEARCH_OFF, size=26, color=MUTED),
                ft.Text("No matching transactions", color=TEXT, size=14),
                label("Try a different search or filter.", size=12),
            ]), padding=22)
        ]

    def on_type(e):
        render_items()
        app.page.update()

    def on_filter(e):
        render_items()
        app.page.update()

    search.on_change = on_filter
    type_filter.on_select = on_type
    category_filter.on_select = on_filter
    sort_filter.on_select = on_filter
    render_items()

    return app.shell("Transactions", "Search, sort and review your activity", [
        ft.Row(spacing=8, controls=[search, ft.IconButton(icon=ft.Icons.ADD, icon_color=ACCENT,
            tooltip="Add transaction", on_click=lambda e: app.open_transaction())]),
        ft.Row(scroll=ft.ScrollMode.AUTO, spacing=8, controls=[type_filter, category_filter]),
        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[label("ACTIVITY", size=11), sort_filter]),
        count_label,
        list_slot,
    ])
