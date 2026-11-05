"""Widok: panele kompresji i dekompresji, ułożone obok siebie."""

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable

from rle_compressor.features.compression.archive_format import Algorithm
from rle_compressor.features.compression.model import (
    CompressionMode,
    CompressionReport,
    DecompressionReport,
)
from rle_compressor.shared.file_picker import ask_for_file
from rle_compressor.shared.formatting import describe_ratio, format_size
from rle_compressor.shared.widgets import BusyBar, FileRow, StatusLabel

PANEL_PADDING = 14
PANEL_GAP = 12
ROW_SPACING = 10
CHOICE_LABEL_WIDTH = 9


class CompressionView(ttk.Frame):
    def __init__(self, parent: tk.Misc, initial_dir: Path) -> None:
        super().__init__(parent)
        self._initial_dir = initial_dir
        self.columnconfigure((0, 1), weight=1, uniform="panels")
        self._build_compression_panel()
        self._build_decompression_panel()
        self._progress = BusyBar(self)
        self._progress.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(PANEL_GAP, 0))

    def bind_actions(
        self,
        on_choose_source: Callable[[], None],
        on_compress: Callable[[], None],
        on_choose_archive: Callable[[], None],
        on_decompress: Callable[[], None],
    ) -> None:
        self._source_row.set_command(on_choose_source)
        self._compress_button.configure(command=on_compress)
        self._archive_row.set_command(on_choose_archive)
        self._decompress_button.configure(command=on_decompress)

    def selected_mode(self) -> CompressionMode:
        return CompressionMode[self._mode.get()]

    def selected_algorithm(self) -> Algorithm:
        return Algorithm[self._algorithm.get()]

    def ask_for_source(self) -> Path | None:
        return ask_for_file(self, "Wybierz plik do kompresji", self._initial_dir)

    def ask_for_archive(self) -> Path | None:
        return ask_for_file(self, "Wybierz plik .rle lub .huf", self._initial_dir)

    def show_source(self, path: Path) -> None:
        self._source_row.set_path(path)

    def show_archive(self, path: Path) -> None:
        self._archive_row.set_path(path)

    def show_compression_report(self, report: CompressionReport) -> None:
        self._compression_status.show_message(
            f"Rozmiar przed: {format_size(report.size_before)}   "
            f"Rozmiar po: {format_size(report.size_after)}\n"
            f"Współczynnik kompresji: {describe_ratio(report.ratio)}\n"
            f"Zapisano: {report.archive}"
        )

    def show_compression_error(self, message: str) -> None:
        self._compression_status.show_error(message)

    def show_decompression_report(self, report: DecompressionReport) -> None:
        lines = [
            f"Odtworzono {format_size(report.restored_size)} z {format_size(report.archive_size)}",
            f"Zapisano: {report.restored}",
        ]
        if report.is_lossy:
            lines.append("Tryb stratny: plik różni się od oryginału, tak ma być.")
        self._decompression_status.show_message("\n".join(lines))

    def show_decompression_error(self, message: str) -> None:
        self._decompression_status.show_error(message)

    def set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self._compress_button.configure(state=state)
        self._decompress_button.configure(state=state)
        self._source_row.set_enabled(not busy)
        self._archive_row.set_enabled(not busy)
        self._progress.set_busy(busy)

    def _build_compression_panel(self) -> None:
        panel = self._add_panel("1. Kompresja", column=0, right_gap=PANEL_GAP // 2)
        self._source_row = FileRow(panel, "Plik do kompresji")
        self._source_row.pack(fill="x")
        self._algorithm = self._add_choice(
            panel,
            "Algorytm:",
            ((Algorithm.RLE, "RLE"), (Algorithm.HUFFMAN, "Huffman")),
        )
        self._mode = self._add_choice(
            panel,
            "Tryb:",
            (
                (CompressionMode.LOSSLESS, "Bezstratna (każdy plik)"),
                (CompressionMode.LOSSY, "Stratna (tylko WAV i BMP)"),
            ),
        )
        self._compress_button = ttk.Button(panel, text="Kompresuj", style="Accent.TButton")
        self._compress_button.pack(anchor="w", pady=ROW_SPACING)
        self._compression_status = StatusLabel(panel)
        self._compression_status.pack(fill="x")

    def _build_decompression_panel(self) -> None:
        panel = self._add_panel("2. Dekompresja", column=1, left_gap=PANEL_GAP // 2)
        self._archive_row = FileRow(panel, "Plik skompresowany (.rle lub .huf)")
        self._archive_row.pack(fill="x")
        self._decompress_button = ttk.Button(panel, text="Dekompresuj", style="Accent.TButton")
        self._decompress_button.pack(anchor="w", pady=ROW_SPACING)
        self._decompression_status = StatusLabel(panel)
        self._decompression_status.pack(fill="x")

    def _add_choice(self, panel: ttk.LabelFrame, label: str, options: tuple) -> tk.StringVar:
        """Dodaje wiersz przełączników; pierwsza opcja jest domyślna."""
        selected = tk.StringVar(value=options[0][0].name)
        row = ttk.Frame(panel)
        row.pack(fill="x", pady=(ROW_SPACING, 0))
        ttk.Label(row, text=label, style="Muted.TLabel", width=CHOICE_LABEL_WIDTH).pack(side="left")
        for option, description in options:
            ttk.Radiobutton(row, text=description, value=option.name, variable=selected).pack(
                side="left", padx=(0, ROW_SPACING)
            )
        return selected

    def _add_panel(
        self, title: str, column: int, left_gap: int = 0, right_gap: int = 0
    ) -> ttk.LabelFrame:
        panel = ttk.LabelFrame(self, text=title, padding=PANEL_PADDING)
        panel.grid(row=0, column=column, sticky="nsew", padx=(left_gap, right_gap))
        return panel
