"""Daily Money Tracker application entry point."""
import logging
from datetime import date

import flet as ft

from components.transaction_form import open_form
from finance import format_money
from storage import FinanceStorage
import theme
from views import analytics, home, profile, transactions

LOG_LEVEL = logging.INFO
logging.basicConfig(format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("app").setLevel(LOG_LEVEL)
log = logging.getLogger("app.main")


class MoneyTracker:
    def __init__(self, page: ft.Page):
        self.page = page
        self.storage = FinanceStorage(page)
        self.file_picker = ft.FilePicker()
        self.transactions: list[dict] = []
        self.currency = "THB"
        self.light_theme = False
        self.today = date.today()
        self.analytics_month = self.today.replace(day=1)
        self.tab = 0

    @property
    def content_width(self) -> float:
        return max(280, min(600, float(self.page.width or 420)))

    async def start(self):
        await self.storage.initialize()
        await self.load_settings()
        await self.reload(refresh=False)
        self.page.navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.RECEIPT_LONG, selected_icon=ft.Icons.RECEIPT, label="Transactions"),
                ft.NavigationBarDestination(icon=ft.Icons.INSERT_CHART_OUTLINED, selected_icon=ft.Icons.INSERT_CHART, label="Analytics"),
                ft.NavigationBarDestination(icon=ft.Icons.PERSON_OUTLINE, selected_icon=ft.Icons.PERSON, label="Profile"),
            ],
            selected_index=self.tab,
            bgcolor=theme.CARD,
            indicator_color="#2B3B65",
            on_change=self.on_navigation,
        )
        self.refresh()

    async def load_settings(self):
        currency = await self.storage.get_setting("currency", "THB")
        self.currency = currency if currency in ("THB", "USD") else "THB"
        self.light_theme = await self.storage.get_setting("theme", "dark") == "light"
        theme.setup(self.page, self.light_theme)

    async def reload(self, refresh: bool = True):
        self.transactions = await self.storage.list_transactions()
        if refresh:
            self.refresh()

    def refresh(self):
        screens = [home.build, transactions.build, analytics.build, profile.build]
        self.page.clean()
        self.page.add(screens[self.tab](self))
        self.page.update()

    def shell(self, title: str, subtitle: str, content: list[ft.Control], action: ft.Control | None = None):
        header = ft.Container(
            padding=ft.Padding.only(left=20, right=14, top=13, bottom=12),
            content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Column(spacing=3, controls=[
                    ft.Text(title, size=23, color=theme.TEXT, weight=ft.FontWeight.BOLD),
                    ft.Text(subtitle, size=12, color=theme.MUTED),
                ]),
                action or ft.Container(width=36),
            ]),
        )
        body = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=10, controls=[
            ft.Container(height=4),
            ft.Container(padding=ft.Padding.symmetric(horizontal=18),
                         content=ft.Column(spacing=14, controls=content)),
            ft.Container(height=12),
        ])
        screen = ft.Column(expand=True, spacing=0, controls=[header, body])
        return ft.SafeArea(
            expand=True,
            content=ft.Row(
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[ft.Container(width=self.content_width, content=screen)],
            ),
        )

    def on_navigation(self, e):
        self.tab = e.control.selected_index
        self.refresh()

    def navigate(self, index: int):
        self.tab = index
        self.page.navigation_bar.selected_index = index
        self.refresh()

    def open_transaction(self, item: dict | None = None):
        open_form(self, item)

    def confirm_delete(self, item: dict):
        async def delete():
            await self.storage.delete_transaction(item["id"])
            self.page.pop_dialog()
            await self.reload()

        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete transaction?"),
            content=ft.Text(f"Remove {format_money(item['amount'], self.currency)} · {item['category']} permanently?"),
            actions=[
                ft.TextButton(content="Cancel", on_click=lambda e: self.page.pop_dialog()),
                ft.Button(content="Delete", bgcolor=theme.EXPENSE, color=theme.TEXT, on_click=delete),
            ],
        ))

    def notice(self, message: str):
        self.page.show_dialog(ft.AlertDialog(
            modal=True, content=ft.Text(message),
            actions=[ft.TextButton(content="Close", on_click=lambda e: self.page.pop_dialog())],
        ))

    async def change_theme(self, e):
        self.light_theme = bool(e.control.value)
        await self.storage.set_setting("theme", "light" if self.light_theme else "dark")
        theme.setup(self.page, self.light_theme)
        self.refresh()

    async def change_currency(self, e):
        self.currency = e.control.value
        await self.storage.set_setting("currency", self.currency)
        self.refresh()


async def main(page: ft.Page):
    app = MoneyTracker(page)
    await app.start()


ft.run(main)
