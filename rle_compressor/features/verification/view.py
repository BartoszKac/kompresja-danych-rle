"""Widok: panel weryfikacji SHA-256."""

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable

from rle_compressor.features.verification.model import VerificationResult
from rle_compressor.shared.file_picker import ask_for_file
from rle_compressor.shared.theme import SUCCESS
from rle_compressor.shared.widgets import FileRow, StatusLabel

PANEL_PADDING = 14
COLUMN_GAP = 6
ROW_SPACING = 10
HASH_LABEL_WIDTH = 16


class VerificationView(ttk.LabelFrame):
    def __init__(self, parent: tk.Misc, initial_dir: Path) -> None:
        super().__init__(parent, text="3. Weryfikacja SHA-256", padding=PANEL_PADDING)
        self._initial_dir = initial_dir

        files = ttk.Frame(self)
        files.pack(fill="x")
        files.columnconfigure((0, 1), weight=1, uniform="files")
        self._original_row = FileRow(files, "Oryginał")
        self._original_row.grid(row=0, column=0, sticky="ew", padx=(0, COLUMN_GAP))
        self._restored_row = FileRow(files, "Po dekompresji")
        self._restored_row.grid(row=0, column=1, sticky="ew", padx=(COLUMN_GAP, 0))

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(ROW_SPACING, 4))
        self._verify_button = ttk.Button(actions, text="Sprawdź zgodność", style="Accent.TButton")
        self._verify_button.pack(side="left")
        self._status = StatusLabel(actions)
        self._status.pack(side="left", fill="x", expand=True, padx=(ROW_SPACING, 0))
        self._hashes = ttk.Label(self, font="TkFixedFont", justify="left")
        self._hashes.pack(anchor="w")

    def bind_actions(
        self,
        on_choose_original: Callable[[], None],
        on_choose_restored: Callable[[], None],
        on_verify: Callable[[], None],
    ) -> None:
        self._original_row.set_command(on_choose_original)
        self._restored_row.set_command(on_choose_restored)
        self._verify_button.configure(command=on_verify)

    def ask_for_original(self) -> Path | None:
        return ask_for_file(self, "Wybierz oryginalny plik", self._initial_dir)

    def ask_for_restored(self) -> Path | None:
        return ask_for_file(self, "Wybierz plik po dekompresji", self._initial_dir)

    def show_original(self, path: Path) -> None:
        self._original_row.set_path(path)

    def show_restored(self, path: Path) -> None:
        self._restored_row.set_path(path)

    def show_result(self, result: VerificationResult) -> None:
        if result.is_identical:
            self._status.show_message("ZGODNE: pliki są identyczne.")
            self._status.configure(foreground=SUCCESS)
        else:
            self._status.show_error("NIEZGODNE: pliki się różnią.")
        self._hashes.configure(
            text=f"{'Oryginał:':<{HASH_LABEL_WIDTH}}{result.original_sha256}\n"
            f"{'Po dekompresji:':<{HASH_LABEL_WIDTH}}{result.restored_sha256}"
        )

    def show_error(self, message: str) -> None:
        self._status.show_error(message)
        self._hashes.configure(text="")

    def set_busy(self, busy: bool) -> None:
        self._verify_button.configure(state="disabled" if busy else "normal")
        self._original_row.set_enabled(not busy)
        self._restored_row.set_enabled(not busy)
