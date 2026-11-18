"""Reusable transaction row/card."""
import flet as ft
from finance import format_money
from theme import CARD, EXPENSE, INCOME, MUTED, TEXT


def build(app, item: dict, *, compact: bool = False) -> ft.Control:
    is_income = item["type"] == "income"
    tone = INCOME if is_income else EXPENSE
    amount = format_money(item["amount"], app.currency)
    note = item.get("note", "").strip()
    detail = f"{note} · {item['date']}" if note else item["date"]
    info = ft.Column(tight=True, spacing=4, controls=[
        ft.Text(item["category"], size=14, weight=ft.FontWeight.W_600, color=TEXT),
        ft.Text(detail, size=11, color=MUTED, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
    ])
    row = ft.Row(vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12, controls=[
        ft.Container(width=40, height=40, border_radius=14, bgcolor=f"{tone}22", alignment=ft.Alignment.CENTER,
                     content=ft.Icon(ft.Icons.TRENDING_UP if is_income else ft.Icons.TRENDING_DOWN, color=tone, size=19)),
        ft.Column(expand=True, spacing=0, controls=[info]),
        ft.Text(("+" if is_income else "−") + amount, size=14, color=tone, weight=ft.FontWeight.W_600),
    ])
    if not compact:
        row.controls.append(ft.IconButton(icon=ft.Icons.EDIT_OUTLINED, icon_size=17, tooltip="Edit transaction",
                                          on_click=lambda e: app.open_transaction(item)))
        row.controls.append(ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_size=17, icon_color=EXPENSE,
                                          tooltip="Delete transaction", on_click=lambda e: app.confirm_delete(item)))
    return ft.Container(content=row, bgcolor=CARD, border_radius=16, padding=12)
