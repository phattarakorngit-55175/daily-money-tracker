"""Persistent transaction storage: SQLite on devices, preferences in web preview."""
import json
import logging
import os
import sqlite3
from datetime import datetime

import flet as ft

from finance import EXPENSE_CATEGORIES, INCOME_CATEGORIES

log = logging.getLogger(f"app.{__name__}")
WEB_KEY = "daily_money_tracker_state_v1"


class FinanceStorage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.web = bool(page.web)
        self.prefs = None
        self.db = None

    async def initialize(self) -> None:
        if self.web:
            self.prefs = ft.SharedPreferences()
            if not await self.prefs.contains_key(WEB_KEY):
                await self.prefs.set(WEB_KEY, json.dumps({"transactions": [], "settings": {}}))
            return
        paths = ft.StoragePaths()
        directory = await paths.get_application_documents_directory()
        os.makedirs(directory, exist_ok=True)
        self.db = sqlite3.connect(os.path.join(directory, "daily_money_tracker.sqlite3"))
        self.db.row_factory = sqlite3.Row
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                amount INTEGER NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                date TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )"""
        )
        self.db.commit()
        log.info("SQLite store ready at application documents directory")

    async def _web_state(self) -> dict:
        raw = await self.prefs.get(WEB_KEY)
        try:
            state = json.loads(raw) if isinstance(raw, str) else {}
        except (ValueError, TypeError):
            state = {}
        return {"transactions": state.get("transactions", []), "settings": state.get("settings", {})}

    async def _save_web_state(self, state: dict) -> None:
        await self.prefs.set(WEB_KEY, json.dumps(state, ensure_ascii=False))

    async def list_transactions(self) -> list[dict]:
        if self.web:
            state = await self._web_state()
            return sorted(state["transactions"], key=lambda t: (t["date"], t["created_at"]), reverse=True)
        rows = self.db.execute("SELECT * FROM transactions ORDER BY date DESC, created_at DESC, id DESC").fetchall()
        return [dict(row) for row in rows]

    async def save_transaction(self, item: dict) -> int:
        created_at = item.get("created_at") or datetime.now().isoformat(timespec="seconds")
        values = (item["type"], int(item["amount"]), item["category"], item.get("note", ""), item["date"])
        if self.web:
            state = await self._web_state()
            items = state["transactions"]
            if item.get("id") is not None:
                for index, old in enumerate(items):
                    if int(old["id"]) == int(item["id"]):
                        items[index] = {**item, "amount": int(item["amount"]), "created_at": item.get("created_at", old["created_at"])}
                        await self._save_web_state(state)
                        return int(item["id"])
            next_id = max((int(t["id"]) for t in items), default=0) + 1
            items.append({"id": next_id, "type": values[0], "amount": values[1], "category": values[2], "note": values[3], "date": values[4], "created_at": created_at})
            await self._save_web_state(state)
            return next_id
        if item.get("id") is not None:
            self.db.execute(
                "UPDATE transactions SET type=?, amount=?, category=?, note=?, date=? WHERE id=?",
                (*values, int(item["id"])),
            )
            transaction_id = int(item["id"])
        else:
            cursor = self.db.execute(
                "INSERT INTO transactions(type, amount, category, note, date, created_at) VALUES(?,?,?,?,?,?)",
                (*values, created_at),
            )
            transaction_id = int(cursor.lastrowid)
        self.db.commit()
        return transaction_id

    async def delete_transaction(self, transaction_id: int) -> None:
        if self.web:
            state = await self._web_state()
            state["transactions"] = [t for t in state["transactions"] if int(t["id"]) != int(transaction_id)]
            await self._save_web_state(state)
        else:
            self.db.execute("DELETE FROM transactions WHERE id=?", (int(transaction_id),))
            self.db.commit()

    async def get_setting(self, key: str, default=None):
        if self.web:
            return (await self._web_state())["settings"].get(key, default)
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    async def set_setting(self, key: str, value: str) -> None:
        if self.web:
            state = await self._web_state()
            state["settings"][key] = value
            await self._save_web_state(state)
        else:
            self.db.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (key, str(value)))
            self.db.commit()

    async def export_data(self) -> str:
        transactions = await self.list_transactions()
        if self.web:
            settings = (await self._web_state())["settings"]
        else:
            settings = {row["key"]: row["value"] for row in self.db.execute("SELECT key, value FROM settings")}
        return json.dumps({"format": "daily-money-tracker", "version": 1, "transactions": transactions, "settings": settings}, ensure_ascii=False, indent=2)

    async def import_data(self, raw: str) -> int:
        data = json.loads(raw)
        if data.get("format") != "daily-money-tracker" or not isinstance(data.get("transactions"), list):
            raise ValueError("This file is not a Daily Money Tracker backup.")
        allowed_types = {"income", "expense"}
        clean = []
        for index, item in enumerate(data["transactions"]):
            if item.get("type") not in allowed_types or not 0 < int(item.get("amount", 0)) <= 99_999_999_999:
                raise ValueError("Backup contains an invalid transaction.")
            categories = INCOME_CATEGORIES if item["type"] == "income" else EXPENSE_CATEGORIES
            if item.get("category") not in categories:
                raise ValueError("Backup contains an unknown transaction category.")
            datetime.strptime(item["date"], "%Y-%m-%d")
            clean.append({
                "id": int(item.get("id", index + 1)), "type": item["type"],
                "amount": int(item["amount"]), "category": str(item["category"]),
                "note": str(item.get("note", "")), "date": item["date"],
                "created_at": str(item.get("created_at") or datetime.now().isoformat(timespec="seconds")),
            })
        settings = data.get("settings", {}) if isinstance(data.get("settings", {}), dict) else {}
        if self.web:
            await self._save_web_state({"transactions": clean, "settings": settings})
        else:
            with self.db:
                self.db.execute("DELETE FROM transactions")
                self.db.executemany(
                    "INSERT INTO transactions(id, type, amount, category, note, date, created_at) VALUES(?,?,?,?,?,?,?)",
                    [(t["id"], t["type"], t["amount"], t["category"], t["note"], t["date"], t["created_at"]) for t in clean],
                )
                self.db.execute("DELETE FROM settings")
                self.db.executemany("INSERT INTO settings(key, value) VALUES(?,?)", [(str(k), str(v)) for k, v in settings.items()])
        return len(clean)

    async def clear_all(self) -> None:
        if self.web:
            state = await self._web_state()
            state["transactions"] = []
            await self._save_web_state(state)
        else:
            self.db.execute("DELETE FROM transactions")
            self.db.commit()
