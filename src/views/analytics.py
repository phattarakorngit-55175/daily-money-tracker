"""Monthly totals, category breakdown and previous-month comparison."""
from calendar import monthrange
from datetime import date

import flet as ft
from flet_charts import PieChart, PieChartSection

from finance import category_totals, format_money, month_key, month_label, totals
from theme import ACCENT, CARD, EXPENSE, INCOME, MUTED, PALETTE, TEXT, card, label


def shift_month(value: date, delta: int) -> date:
    month_index = value.year * 12 + value.month - 1 + delta
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    return date(year, month, min(value.day, monthrange(year, month)[1]))


def build(app) -> ft.Control:
    selected = app.analytics_month
    items = [t for t in app.transactions if t["date"].startswith(month_key(selected))]
    previous_date = shift_month(selected, -1)
    previous_items = [t for t in app.transactions if t["date"].startswith(month_key(previous_date))]
    current = totals(items)
    previous = totals(previous_items)
    grouped = category_totals(items)

    def select_month(delta: int):
        app.analytics_month = shift_month(app.analytics_month, delta).replace(day=1)
        app.refresh()

    month_picker = ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
        ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, on_click=lambda e: select_month(-1)),
        ft.Text(month_label(selected), size=17, weight=ft.FontWeight.W_600, color=TEXT),
        ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, on_click=lambda e: select_month(1)),
    ])
    summary = ft.Row(spacing=10, controls=[
        card(ft.Column(spacing=7, controls=[label("INCOME", size=10),
            ft.Text(format_money(current["income"], app.currency), size=15, color=INCOME, weight=ft.FontWeight.W_600)]), padding=14),
        card(ft.Column(spacing=7, controls=[label("EXPENSES", size=10),
            ft.Text(format_money(current["expenses"], app.currency), size=15, color=EXPENSE, weight=ft.FontWeight.W_600)]), padding=14),
        card(ft.Column(spacing=7, controls=[label("NET SAVINGS", size=10),
            ft.Text(format_money(current["balance"], app.currency), size=15, color=ACCENT, weight=ft.FontWeight.W_600)]), padding=14),
    ])
    for box in summary.controls:
        box.expand = True

    savings = card(ft.Column(spacing=8, controls=[
        label("MONTHLY COMPARISON", size=11, weight=ft.FontWeight.W_600),
        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[label("Income", size=12),
            ft.Text(f"{format_money(current['income'], app.currency)}  ·  {format_money(previous['income'], app.currency)} prev.", size=12, color=INCOME)]),
        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[label("Expenses", size=12),
            ft.Text(f"{format_money(current['expenses'], app.currency)}  ·  {format_money(previous['expenses'], app.currency)} prev.", size=12, color=EXPENSE)]),
    ]))

    if grouped:
        chart = PieChart(
            sections=[PieChartSection(value=value, color=PALETTE[index % len(PALETTE)], radius=28,
                                      title=(f"{round(value / max(current['expenses'], 1) * 100)}%" if value / max(current["expenses"], 1) >= 0.12 else None),
                                      title_style=ft.TextStyle(color=TEXT, size=10, weight=ft.FontWeight.BOLD))
                      for index, (category, value) in enumerate(grouped)],
            sections_space=3,
            center_space_radius=48,
            center_space_color=CARD,
            height=210,
        )
        category_rows = [ft.Row(spacing=9, controls=[
            ft.Container(width=9, height=9, border_radius=5, bgcolor=PALETTE[index % len(PALETTE)]),
            ft.Text(category, size=12, color=TEXT, expand=True),
            ft.Text(format_money(value, app.currency), size=12, color=TEXT),
        ]) for index, (category, value) in enumerate(grouped)]
        breakdown = card(ft.Column(spacing=12, controls=[
            ft.Text("Spending breakdown", size=16, weight=ft.FontWeight.W_600, color=TEXT),
            ft.Row(vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[chart]),
            *category_rows,
        ]))
    else:
        breakdown = card(ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
            ft.Icon(ft.Icons.PIE_CHART_OUTLINE, color=MUTED, size=28),
            ft.Text("No expenses this month", color=TEXT, size=14),
            label("Your category breakdown will appear here.", size=12),
        ]), padding=22)

    return app.shell("Analytics", "Understand where your money goes", [
        month_picker, summary, savings, breakdown,
    ])
