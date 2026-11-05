"""Widok: tabela wyników testów."""

import tkinter as tk
from tkinter import ttk
from typing import Callable

from rle_compressor.features.benchmark.model import BenchmarkResult
from rle_compressor.shared.formatting import describe_ratio, format_size
from rle_compressor.shared.widgets import BusyBar, ScrollableTable, StatusLabel

TAB_PADDING = 14
ROW_SPACING = 10
COLUMNS = (
    ("file", "Plik", 230, "w"),
    ("algorithm", "Algorytm", 80, "w"),
    ("mode", "Tryb", 90, "w"),
    ("before", "Przed", 100, "e"),
    ("after", "Po", 100, "e"),
    ("ratio", "Współczynnik", 220, "e"),
    ("verdict", "SHA-256", 130, "center"),
)


class BenchmarkView(ttk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padding=TAB_PADDING)
        self._run_button = ttk.Button(self, text="Uruchom testy", style="Accent.TButton")
        self._run_button.pack(anchor="w")
        self._status = StatusLabel(self)
        self._status.pack(fill="x", pady=ROW_SPACING)
        self._progress = BusyBar(self)
        self._progress.pack(fill="x", pady=(0, ROW_SPACING))
        scrollable = ScrollableTable(
            self, columns=[column[0] for column in COLUMNS], show="headings"
        )
        scrollable.pack(fill="both", expand=True)
        self._table = scrollable.table
        for column_id, heading, width, anchor in COLUMNS:
            self._table.heading(column_id, text=heading, anchor=anchor)
            self._table.column(column_id, width=width, anchor=anchor)

    def bind_actions(self, on_run: Callable[[], None]) -> None:
        self._run_button.configure(command=on_run)

    def show_results(self, results: list[BenchmarkResult]) -> None:
        self._table.delete(*self._table.get_children())
        for result in results:
            self._table.insert("", "end", values=_as_row(result))

    def show_message(self, message: str) -> None:
        self._status.show_message(message)

    def show_error(self, message: str) -> None:
        self._status.show_error(message)

    def set_busy(self, busy: bool) -> None:
        self._run_button.configure(state="disabled" if busy else "normal")
        self._progress.set_busy(busy)


def _as_row(result: BenchmarkResult) -> tuple[str, ...]:
    return (
        result.file_name,
        result.algorithm.value,
        result.mode.value,
        format_size(result.size_before),
        format_size(result.size_after),
        describe_ratio(result.ratio),
        result.verdict,
    )
