"""Wspólny wygląd programu: kolory, czcionki i style widżetów ttk."""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

BACKGROUND = "#ffffff"
SUBTLE_BACKGROUND = "#f4f6f8"
BORDER = "#d9dee4"
TEXT = "#1f2933"
MUTED_TEXT = "#667085"
DISABLED_TEXT = "#98a2b3"
ACCENT = "#2563eb"
ACCENT_HOVER = "#1d4ed8"
ACCENT_DISABLED = "#a9c1f5"
ERROR = "#b42318"
SUCCESS = "#067647"

PREFERRED_FONTS = ("Segoe UI", "Inter", "DejaVu Sans")
PREFERRED_FIXED_FONTS = ("Cascadia Mono", "Consolas", "DejaVu Sans Mono")
FONT_SIZE = 11
FIXED_FONT_SIZE = 10
TABLE_ROW_HEIGHT = 32
TAB_PADDING = (18, 9)


def apply_theme(root: tk.Tk) -> None:
    root.configure(background=BACKGROUND)
    _configure_fonts(root)

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=BACKGROUND, foreground=TEXT, bordercolor=BORDER)
    _style_buttons(style)
    _style_notebook(style)
    _style_panels_and_inputs(style)
    _style_table(style)


def _configure_fonts(root: tk.Tk) -> None:
    installed = set(tkfont.families(root))
    family = next((name for name in PREFERRED_FONTS if name in installed), None)
    fixed_family = next((name for name in PREFERRED_FIXED_FONTS if name in installed), None)

    for font_name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
        font = tkfont.nametofont(font_name, root=root)
        font.configure(size=FONT_SIZE, weight="normal")
        if family:
            font.configure(family=family)

    fixed_font = tkfont.nametofont("TkFixedFont", root=root)
    fixed_font.configure(size=FIXED_FONT_SIZE)
    if fixed_family:
        fixed_font.configure(family=fixed_family)


def _style_buttons(style: ttk.Style) -> None:
    style.configure(
        "TButton",
        background=BACKGROUND,
        foreground=TEXT,
        bordercolor=BORDER,
        lightcolor=BACKGROUND,
        darkcolor=BACKGROUND,
        focuscolor=BACKGROUND,
        padding=(14, 7),
    )
    style.map(
        "TButton",
        background=[("disabled", BACKGROUND), ("active", SUBTLE_BACKGROUND)],
        lightcolor=[("active", SUBTLE_BACKGROUND)],
        darkcolor=[("active", SUBTLE_BACKGROUND)],
        foreground=[("disabled", DISABLED_TEXT)],
    )
    style.configure(
        "Accent.TButton",
        background=ACCENT,
        foreground=BACKGROUND,
        bordercolor=ACCENT,
        lightcolor=ACCENT,
        darkcolor=ACCENT,
        focuscolor=ACCENT,
    )
    style.map(
        "Accent.TButton",
        background=[("disabled", ACCENT_DISABLED), ("active", ACCENT_HOVER)],
        bordercolor=[("disabled", ACCENT_DISABLED), ("active", ACCENT_HOVER)],
        lightcolor=[("disabled", ACCENT_DISABLED), ("active", ACCENT_HOVER)],
        darkcolor=[("disabled", ACCENT_DISABLED), ("active", ACCENT_HOVER)],
        foreground=[("disabled", BACKGROUND)],
    )


def _style_notebook(style: ttk.Style) -> None:
    style.configure(
        "TNotebook",
        background=BACKGROUND,
        bordercolor=BACKGROUND,
        lightcolor=BACKGROUND,
        darkcolor=BACKGROUND,
        tabmargins=(0, 0, 0, 0),
    )
    style.configure(
        "TNotebook.Tab",
        background=SUBTLE_BACKGROUND,
        foreground=MUTED_TEXT,
        bordercolor=BORDER,
        lightcolor=SUBTLE_BACKGROUND,
        focuscolor=SUBTLE_BACKGROUND,
        padding=TAB_PADDING,
    )
    # Motyw clam domyślnie zmienia rozmiar aktywnej karty, dlatego ujednolicamy oba stany.
    style.map(
        "TNotebook.Tab",
        background=[("selected", BACKGROUND)],
        foreground=[("selected", ACCENT)],
        lightcolor=[("selected", BACKGROUND)],
        focuscolor=[("selected", BACKGROUND)],
        padding=[("selected", TAB_PADDING)],
        expand=[("selected", (0, 0, 0, 0))],
    )


def _style_panels_and_inputs(style: ttk.Style) -> None:
    style.configure(
        "TLabelframe",
        background=BACKGROUND,
        bordercolor=BORDER,
        lightcolor=BACKGROUND,
        darkcolor=BACKGROUND,
        relief="solid",
        borderwidth=1,
    )
    style.configure("TLabelframe.Label", background=BACKGROUND, foreground=TEXT)
    style.configure("Muted.TLabel", foreground=MUTED_TEXT)
    style.configure(
        "TRadiobutton",
        background=BACKGROUND,
        foreground=TEXT,
        focuscolor=BACKGROUND,
        indicatorcolor=BACKGROUND,
    )
    style.map(
        "TRadiobutton",
        background=[("active", BACKGROUND)],
        indicatorcolor=[("selected", ACCENT)],
    )
    style.configure(
        "TCheckbutton",
        background=BACKGROUND,
        foreground=TEXT,
        focuscolor=BACKGROUND,
        indicatorcolor=BACKGROUND,
    )
    style.map(
        "TCheckbutton",
        background=[("active", BACKGROUND)],
        foreground=[("disabled", DISABLED_TEXT)],
        indicatorcolor=[("selected", ACCENT)],
    )
    style.configure(
        "TCombobox",
        fieldbackground=BACKGROUND,
        background=BACKGROUND,
        foreground=TEXT,
        arrowcolor=MUTED_TEXT,
        bordercolor=BORDER,
        lightcolor=BACKGROUND,
        darkcolor=BACKGROUND,
        padding=4,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", BACKGROUND)],
        background=[("active", SUBTLE_BACKGROUND)],
        selectbackground=[("readonly", BACKGROUND)],
        selectforeground=[("readonly", TEXT)],
    )
    style.configure(
        "TEntry",
        fieldbackground=SUBTLE_BACKGROUND,
        bordercolor=BORDER,
        lightcolor=SUBTLE_BACKGROUND,
        darkcolor=SUBTLE_BACKGROUND,
        padding=6,
    )
    style.map("TEntry", fieldbackground=[("readonly", SUBTLE_BACKGROUND)])
    style.configure(
        "TProgressbar",
        background=ACCENT,
        troughcolor=BACKGROUND,
        bordercolor=BACKGROUND,
        lightcolor=ACCENT,
        darkcolor=ACCENT,
    )


def _style_table(style: ttk.Style) -> None:
    style.configure(
        "Treeview",
        background=BACKGROUND,
        fieldbackground=BACKGROUND,
        foreground=TEXT,
        bordercolor=BORDER,
        rowheight=TABLE_ROW_HEIGHT,
    )
    style.map(
        "Treeview",
        background=[("selected", SUBTLE_BACKGROUND)],
        foreground=[("selected", TEXT)],
    )
    style.configure(
        "Treeview.Heading",
        background=SUBTLE_BACKGROUND,
        foreground=MUTED_TEXT,
        bordercolor=BORDER,
        lightcolor=SUBTLE_BACKGROUND,
        darkcolor=SUBTLE_BACKGROUND,
        relief="flat",
        padding=(8, 7),
    )
    style.map("Treeview.Heading", background=[("active", SUBTLE_BACKGROUND)])
