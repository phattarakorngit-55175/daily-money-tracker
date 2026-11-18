"""Home dashboard."""
import flet as ft

from components.transaction_card import build as transaction_card
from finance import format_money, month_key, month_label, totals
from theme import ACCENT, CARD, EXPENSE, INCOME, MUTED, TEXT, card, label


def build(app) -> ft.Control:
    transactions = app.transactions
    total = totals(transactions)
    month_items = [item for item in transactions if item["date"].startswith(month_key(app.today))]
    month_total = totals(month_items)
    recent = transactions[:4]
    hero = card(ft.Column(spacing=14, controls=[
        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
            label("TOTAL BALANCE", size=11, color="#D7E0FF", weight=ft.FontWeight.W_600),
            ft.Container(padding=8, border_radius=12, bgcolor="#FFFFFF1A",
                         content=ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, color=TEXT, size=19)),
        ]),
        ft.Text(format_money(total["balance"], app.currency), size=32, weight=ft.FontWeight.BOLD, color=TEXT),
        ft.Row(spacing=8, controls=[
            ft.Icon(ft.Icons.CALENDAR_MONTH, color="#D7E0FF", size=15),
            label(month_label(app.today), size=12, color="#D7E0FF"),
        ]),
    ]), color=ACCENT)
    stats = ft.Row(spacing=12, controls=[
        card(ft.Column(spacing=8, controls=[label("INCOME", size=11),
            ft.Text(format_money(month_total["income"], app.currency), size=17, color=INCOME, weight=ft.FontWeight.W_600),
            label("This month", size=11)]), padding=15),
        card(ft.Column(spacing=8, controls=[label("EXPENSES", size=11),
            ft.Text(format_money(month_total["expenses"], app.currency), size=17, color=EXPENSE, weight=ft.FontWeight.W_600),
            label("This month", size=11)]), padding=15),
    ])
    for stat_card in stats.controls:
        stat_card.expand = True
    recent_section = ft.Column(spacing=10, controls=[
        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
            ft.Text("Recent transactions", size=17, weight=ft.FontWeight.W_600, color=TEXT),
            ft.TextButton(content="See all", on_click=lambda e: app.navigate(1)),
        ]),
        *(transaction_card(app, item, compact=True) for item in recent),
    ]) if recent else card(ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
        ft.Icon(ft.Icons.RECEIPT_LONG, color=MUTED, size=28),
        ft.Text("No transactions yet", size=15, color=TEXT, weight=ft.FontWeight.W_600),
        label("Add your first income or expense to get started.", size=12),
        ft.Button(content="Add transaction", icon=ft.Icons.ADD, bgcolor=ACCENT, color=TEXT,
                  on_click=lambda e: app.open_transaction()),
    ]), padding=22)
    body = [hero, stats, recent_section]
    return app.shell("Good day", "Your money at a glance", body,
                     action=ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE, icon_color=ACCENT,
                                          tooltip="Add transaction", on_click=lambda e: app.open_transaction()))
