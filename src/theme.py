"""Shared visual palette and reusable finance UI primitives."""
import flet as ft

BG = "#0F1420"
CARD = "#1A2132"
CARD_ALT = "#222B3F"
ACCENT = "#5B84FF"
INCOME = "#3DD68C"
EXPENSE = "#FF6B6B"
TEXT = "#F4F6FB"
MUTED = "#98A2B7"
OUTLINE = "#30394D"
PALETTE = [ACCENT, INCOME, "#FFC857", "#B48CFF", "#FF8F70", "#54C6EB", "#F275B5", "#A7B0C0"]


def setup(page: ft.Page, light: bool = False) -> None:
    page.theme = ft.Theme(color_scheme_seed=ACCENT)
    page.dark_theme = ft.Theme(color_scheme_seed=ACCENT)
    page.theme_mode = ft.ThemeMode.LIGHT if light else ft.ThemeMode.DARK
    page.bgcolor = "#F4F6FA" if light else BG
    page.padding = 0
    page.spacing = 0
    page.title = "Daily Money Tracker"


def card(content: ft.Control, *, padding: int = 18, color: str = CARD) -> ft.Container:
    return ft.Container(
        content=content,
        bgcolor=color,
        border_radius=20,
        padding=padding,
    )


def label(text: str, *, size: int = 13, color: str = MUTED, weight=None) -> ft.Text:
    return ft.Text(text, size=size, color=color, weight=weight or ft.FontWeight.NORMAL)
