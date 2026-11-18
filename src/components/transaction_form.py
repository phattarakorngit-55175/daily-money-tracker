"""Add/edit transaction dialog with validation and a calendar picker."""
from datetime import date, datetime

import flet as ft

from finance import EXPENSE_CATEGORIES, INCOME_CATEGORIES, to_minor_units
from theme import ACCENT, CARD, EXPENSE, INCOME, MUTED, TEXT


def open_form(app, item: dict | None = None) -> None:
    editing = item is not None
    transaction_type = item["type"] if editing else "expense"
    initial_date = item["date"] if editing else date.today().isoformat()
    amount_field = ft.TextField(label="Amount", value=(f"{item['amount'] / 100:.2f}" if editing else ""),
                                prefix=ft.Text("฿ " if app.currency == "THB" else "$ "),
                                keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)
    type_field = ft.Dropdown(label="Transaction type", value=transaction_type.title(), options=[
        ft.DropdownOption(text="Expense"), ft.DropdownOption(text="Income")
    ])
    category_field = ft.Dropdown(label="Category", value=(item["category"] if editing else "Food"),
                                 options=[ft.DropdownOption(text=value) for value in (INCOME_CATEGORIES if transaction_type == "income" else EXPENSE_CATEGORIES)])
    note_field = ft.TextField(label="Note (optional)", value=(item.get("note", "") if editing else ""), max_length=120)
    date_field = ft.TextField(label="Date", value=initial_date, read_only=True, expand=True)
    error_text = ft.Text("", color=EXPENSE, size=12)

    def update_categories(e):
        selected_type = e.control.value.lower()
        categories = INCOME_CATEGORIES if selected_type == "income" else EXPENSE_CATEGORIES
        category_field.options = [ft.DropdownOption(text=value) for value in categories]
        category_field.value = categories[0]
        app.page.update()

    type_field.on_select = update_categories

    def show_calendar():
        current = datetime.fromisoformat(date_field.value)
        picker = ft.DatePicker(
            value=current,
            current_date=datetime.now(),
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
            on_change=lambda e: picked_date(e),
        )
        app.page.show_dialog(picker)

    def picked_date(e):
        value = e.control.value
        if value:
            date_field.value = value.astimezone().date().isoformat()
            app.page.update()

    async def save():
        try:
            amount = to_minor_units(amount_field.value or "")
            parsed_date = datetime.strptime(date_field.value, "%Y-%m-%d").date()
            selected_type = type_field.value.lower()
            valid = INCOME_CATEGORIES if selected_type == "income" else EXPENSE_CATEGORIES
            if category_field.value not in valid:
                raise ValueError("Choose a category for this transaction.")
            record = {
                "id": item.get("id") if editing else None,
                "type": selected_type,
                "amount": amount,
                "category": category_field.value,
                "note": (note_field.value or "").strip(),
                "date": parsed_date.isoformat(),
                "created_at": item.get("created_at") if editing else None,
            }
            await app.storage.save_transaction(record)
            app.page.pop_dialog()
            await app.reload()
        except ValueError as exc:
            error_text.value = str(exc)
            app.page.update()
        except Exception:
            error_text.value = "The transaction could not be saved. Please try again."
            app.page.update()

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Edit transaction" if editing else "New transaction", color=TEXT),
        content=ft.Column(tight=True, spacing=12, controls=[
            type_field, amount_field, category_field, note_field,
            ft.Row(spacing=8, controls=[date_field, ft.IconButton(icon=ft.Icons.CALENDAR_TODAY,
                icon_color=ACCENT, tooltip="Choose date", on_click=lambda e: show_calendar())]),
            error_text,
        ]),
        actions=[
            ft.TextButton(content="Cancel", on_click=lambda e: app.page.pop_dialog()),
            ft.Button(content="Save transaction", icon=ft.Icons.CHECK, bgcolor=ACCENT,
                      color=TEXT, on_click=save),
        ],
        bgcolor=CARD,
    )
    app.page.show_dialog(dialog)
