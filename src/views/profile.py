"""Profile metrics, theme/currency settings, backup and data reset."""
import flet as ft

from finance import category_totals, format_money, totals
from theme import ACCENT, CARD, EXPENSE, INCOME, MUTED, TEXT, card, label


def build(app) -> ft.Control:
    all_totals = totals(app.transactions)
    spending = category_totals(app.transactions)
    most_expensive = spending[0][0] if spending else "—"
    metric_items = [
        ("Transactions", str(len(app.transactions)), ft.Icons.RECEIPT_LONG, ACCENT),
        ("Lifetime income", format_money(all_totals["income"], app.currency), ft.Icons.TRENDING_UP, INCOME),
        ("Lifetime expenses", format_money(all_totals["expenses"], app.currency), ft.Icons.TRENDING_DOWN, EXPENSE),
        ("Net savings", format_money(all_totals["balance"], app.currency), ft.Icons.SAVINGS, ACCENT),
    ]
    metric_grid = ft.Column(spacing=10, controls=[])
    for index in range(0, len(metric_items), 2):
        row = ft.Row(spacing=10, controls=[])
        for title, value, icon, color in metric_items[index:index + 2]:
            row.controls.append(card(ft.Row(spacing=10, controls=[
                ft.Icon(icon, color=color, size=20),
                ft.Column(expand=True, spacing=5, controls=[label(title, size=11),
                    ft.Text(value, color=TEXT, size=14, weight=ft.FontWeight.W_600, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)]),
            ]), padding=14))
            row.controls[-1].expand = True
        metric_grid.controls.append(row)

    theme_switch = ft.Switch(label="Light appearance", value=app.light_theme, on_change=app.change_theme)
    currency_picker = ft.Dropdown(label="Currency", value=app.currency,
        options=[ft.DropdownOption(text="THB"), ft.DropdownOption(text="USD")], on_select=app.change_currency)

    async def backup():
        try:
            data = await app.storage.export_data()
            await app.file_picker.save_file(dialog_title="Save backup", file_name="daily-money-tracker-backup.json",
                                            allowed_extensions=["json"], src_bytes=data.encode("utf-8"))
        except Exception as exc:
            app.notice(f"Backup could not be saved: {exc}")

    async def apply_backup(raw: str):
        try:
            count = await app.storage.import_data(raw)
            await app.load_settings()
            app.page.pop_dialog()
            await app.reload()
            app.notice(f"Restored {count} transaction" + ("s." if count != 1 else "."))
        except Exception as exc:
            app.page.pop_dialog()
            app.notice(f"Restore failed: {exc}")

    def confirm_restore(raw: str):
        async def accept_restore():
            await apply_backup(raw)

        app.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Replace current data?"),
            content=ft.Text("Restoring this backup replaces the transactions and preferences currently stored on this device."),
            actions=[ft.TextButton(content="Cancel", on_click=lambda e: app.page.pop_dialog()),
                     ft.Button(content="Restore backup", bgcolor=ACCENT, color=TEXT,
                               on_click=accept_restore)],
        ))

    async def restore():
        try:
            files = await app.file_picker.pick_files(dialog_title="Choose a backup", allowed_extensions=["json"],
                                                      allow_multiple=False, with_data=True)
            if not files:
                return
            if files[0].bytes is None:
                raise ValueError("The selected backup could not be read.")
            confirm_restore(files[0].bytes.decode("utf-8"))
        except Exception as exc:
            app.notice(f"Restore failed: {exc}")

    async def clear_everything():
        await app.storage.clear_all()
        await app.reload()
        app.page.pop_dialog()

    def confirm_clear():
        app.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Clear all data?"),
            content=ft.Text("This permanently deletes all transactions from this device. Export a backup first if you may need them."),
            actions=[ft.TextButton(content="Cancel", on_click=lambda e: app.page.pop_dialog()),
                     ft.Button(content="Delete everything", bgcolor=EXPENSE, color=TEXT, on_click=clear_everything)],
        ))

    settings_card = card(ft.Column(spacing=14, controls=[
        ft.Text("Preferences", size=16, color=TEXT, weight=ft.FontWeight.W_600),
        theme_switch,
        currency_picker,
    ]))
    data_card = card(ft.Column(spacing=8, controls=[
        ft.Text("Your data", size=16, color=TEXT, weight=ft.FontWeight.W_600),
        ft.TextButton(content=ft.Row(spacing=10, controls=[ft.Icon(ft.Icons.UPLOAD_FILE, color=ACCENT), ft.Text("Back up data", color=TEXT)]), on_click=backup),
        ft.TextButton(content=ft.Row(spacing=10, controls=[ft.Icon(ft.Icons.DOWNLOAD, color=ACCENT), ft.Text("Restore from backup", color=TEXT)]), on_click=restore),
        ft.TextButton(content=ft.Row(spacing=10, controls=[ft.Icon(ft.Icons.DELETE_OUTLINE, color=EXPENSE), ft.Text("Clear all data", color=EXPENSE)]), on_click=lambda e: confirm_clear()),
    ]))

    return app.shell("Profile", "Your account and preferences", [
        card(ft.Row(spacing=13, controls=[
            ft.Container(width=52, height=52, border_radius=18, bgcolor=f"{ACCENT}24", alignment=ft.Alignment.CENTER,
                         content=ft.Icon(ft.Icons.ACCOUNT_CIRCLE, color=ACCENT, size=30)),
            ft.Column(spacing=4, controls=[ft.Text("Personal finances", color=TEXT, size=16, weight=ft.FontWeight.W_600),
                                           label("Your data stays on this device", size=12)]),
        ])),
        metric_grid,
        card(ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
            ft.Column(spacing=4, controls=[label("TOP SPENDING CATEGORY", size=10),
                ft.Text(most_expensive, color=TEXT, size=15, weight=ft.FontWeight.W_600)]),
            ft.Icon(ft.Icons.CATEGORY, color=ACCENT, size=23),
        ])),
        settings_card,
        data_card,
    ])
