"""Widżety używane w kilku widokach."""

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable

from rle_compressor.shared.theme import ERROR, TEXT


class FileRow(ttk.Frame):
    """Wybór pliku: etykieta, a pod nią ścieżka i przycisk."""

    def __init__(self, parent: tk.Misc, label: str) -> None:
        super().__init__(parent)
        self._path = tk.StringVar()
        ttk.Label(self, text=label, style="Muted.TLabel").pack(anchor="w", pady=(0, 4))
        controls = ttk.Frame(self)
        controls.pack(fill="x")
        self._button = ttk.Button(controls, text="Wybierz…")
        self._button.pack(side="right", padx=(8, 0))
        ttk.Entry(controls, textvariable=self._path, state="readonly").pack(
            side="left", fill="x", expand=True
        )

    def set_command(self, on_choose: Callable[[], None]) -> None:
        self._button.configure(command=on_choose)

    def set_path(self, path: Path) -> None:
        self._path.set(str(path))

    def set_enabled(self, enabled: bool) -> None:
        self._button.configure(state="normal" if enabled else "disabled")


class StatusLabel(ttk.Label):
    """Komunikat o wyniku lub błędzie; zawija tekst do szerokości panelu."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, justify="left")
        self.bind("<Configure>", lambda event: self.configure(wraplength=event.width))

    def show_message(self, text: str) -> None:
        self.configure(text=text, foreground=TEXT)

    def show_error(self, text: str) -> None:
        self.configure(text=text, foreground=ERROR)


class ScrollableTable(ttk.Frame):
    """Tabela z pionowym paskiem przewijania; sama tabela jest w polu `table`."""

    def __init__(self, parent: tk.Misc, **table_options) -> None:
        super().__init__(parent)
        self.table = ttk.Treeview(self, **table_options)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.table.pack(side="left", fill="both", expand=True)


class BusyBar(ttk.Progressbar):
    """Pasek postępu: animowany podczas pracy, pusty w spoczynku."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, mode="determinate", value=0)

    def set_busy(self, busy: bool) -> None:
        if busy:
            self.configure(mode="indeterminate")
            self.start()
        else:
            self.stop()
            self.configure(mode="determinate", value=0)
