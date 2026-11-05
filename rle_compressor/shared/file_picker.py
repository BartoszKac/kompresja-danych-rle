"""Okno wyboru pliku po polsku, ograniczone do katalogu roboczego.

Na Linuksie standardowe okno Tk wygląda archaicznie i ma angielskie napisy, dlatego
tam używamy tego okna. Windows i macOS mają własne, systemowe okno wyboru pliku.
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from rle_compressor.shared.formatting import format_size
from rle_compressor.shared.theme import BORDER, ERROR
from rle_compressor.shared.widgets import ScrollableTable

DIALOG_WIDTH = 620
DIALOG_HEIGHT = 460
TABLE_VISIBLE_ROWS = 7
FOLDER_MARK = "📁  "


def ask_for_file(parent: tk.Misc, title: str, initial_dir: Path) -> Path | None:
    if parent.tk.call("tk", "windowingsystem") != "x11":
        chosen = filedialog.askopenfilename(parent=parent, title=title, initialdir=initial_dir)
        return Path(chosen) if chosen else None

    dialog = FilePickerDialog(parent, title, initial_dir)
    parent.wait_window(dialog)
    return dialog.chosen_file


class FilePickerDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, title: str, root_dir: Path) -> None:
        super().__init__(parent, background=BORDER)
        self.title(title)
        self.chosen_file: Path | None = None
        self._root_dir = root_dir.resolve()
        self._current_dir = self._root_dir
        self._entries: dict[str, Path] = {}

        self._build(title)
        self._show_directory(self._root_dir)
        self._center_over(parent)
        self.transient(parent.winfo_toplevel())
        self.bind("<Escape>", lambda _event: self.destroy())
        self.wait_visibility()
        self.grab_set()
        self.focus_set()

    def _build(self, title: str) -> None:
        body = ttk.Frame(self, padding=16)
        body.pack(fill="both", expand=True, padx=1, pady=1)

        ttk.Label(body, text=title).pack(anchor="w")

        location = ttk.Frame(body)
        location.pack(fill="x", pady=(10, 8))
        self._up_button = ttk.Button(location, text="↑ W górę", command=self._go_up)
        self._up_button.pack(side="left")
        self._location_label = ttk.Label(location, style="Muted.TLabel")
        self._location_label.pack(side="left", padx=10)

        scrollable = ScrollableTable(
            body, columns=("size",), selectmode="browse", height=TABLE_VISIBLE_ROWS
        )
        scrollable.pack(fill="both", expand=True)
        self._table = scrollable.table
        self._table.heading("#0", text="Nazwa", anchor="w")
        self._table.heading("size", text="Rozmiar", anchor="e")
        self._table.column("size", width=110, stretch=False, anchor="e")
        self._table.bind("<Double-1>", lambda _event: self._open_selection())
        self._table.bind("<Return>", lambda _event: self._open_selection())
        self._table.bind("<<TreeviewSelect>>", lambda _event: self._clear_error())

        self._error = ttk.Label(body, foreground=ERROR)
        self._error.pack(anchor="w", pady=(6, 0))

        actions = ttk.Frame(body)
        actions.pack(fill="x", pady=(6, 0))
        ttk.Button(
            actions, text="Wybierz", style="Accent.TButton", command=self._open_selection
        ).pack(side="right")
        ttk.Button(actions, text="Anuluj", command=self.destroy).pack(side="right", padx=8)

    def _show_directory(self, directory: Path) -> None:
        self._clear_error()
        try:
            children = sorted(
                (path for path in directory.iterdir() if not path.name.startswith(".")),
                key=lambda path: (path.is_file(), path.name.lower()),
            )
        except OSError as error:
            self._error.configure(text=f"Nie można otworzyć katalogu: {error}")
            return

        self._current_dir = directory
        self._location_label.configure(text=str(directory))
        self._up_button.configure(state="normal" if directory != self._root_dir else "disabled")
        self._table.delete(*self._table.get_children())
        self._entries = {}
        for path in children:
            item = self._add_row(path)
            self._entries[item] = path

    def _add_row(self, path: Path) -> str:
        if path.is_dir():
            return self._table.insert("", "end", text=FOLDER_MARK + path.name, values=("",))
        return self._table.insert(
            "", "end", text=path.name, values=(format_size(path.stat().st_size),)
        )

    def _go_up(self) -> None:
        self._show_directory(self._current_dir.parent)

    def _open_selection(self) -> None:
        selection = self._table.selection()
        if not selection:
            self._error.configure(text="Zaznacz plik na liście.")
            return

        path = self._entries[selection[0]]
        if path.is_dir():
            self._show_directory(path)
        else:
            self.chosen_file = path
            self.destroy()

    def _clear_error(self) -> None:
        self._error.configure(text="")

    def _center_over(self, parent: tk.Misc) -> None:
        window = parent.winfo_toplevel()
        x = window.winfo_rootx() + (window.winfo_width() - DIALOG_WIDTH) // 2
        y = window.winfo_rooty() + (window.winfo_height() - DIALOG_HEIGHT) // 2
        self.geometry(f"{DIALOG_WIDTH}x{DIALOG_HEIGHT}+{max(x, 0)}+{max(y, 0)}")
