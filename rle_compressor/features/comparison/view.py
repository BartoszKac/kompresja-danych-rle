"""Widok: ustawienia porównania oraz wykres, mapa ciepła albo tabela."""

import tkinter as tk
from enum import Enum
from tkinter import ttk
from typing import Callable

from rle_compressor.features.comparison.bar_chart import BarChart
from rle_compressor.features.comparison.heat_map import HeatMap
from rle_compressor.features.comparison.model import (
    ALL_SERIES,
    ChartView,
    Comparison,
    ComparisonSettings,
    DataKind,
    Measure,
    Series,
    SortOrder,
)
from rle_compressor.shared.widgets import ScrollableTable

TAB_PADDING = 14
ROW_SPACING = 8
CONTROL_GAP = 14
SERIES_SELECTED_AT_START = ALL_SERIES[:2]
FILE_COLUMN_WIDTH = 240
VALUE_COLUMN_WIDTH = 150
BEST_COLUMN_WIDTH = 240
NO_VALUE = "–"
BEST_SEPARATOR = " / "


class ComparisonView(ttk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padding=TAB_PADDING)
        self._on_change: Callable[[], None] = lambda: None
        self._build_series_row()
        self._build_settings_row()
        self._summary = ttk.Label(self, style="Muted.TLabel")
        self._summary.pack(anchor="w", pady=(0, ROW_SPACING))

        self._message = ttk.Label(self, style="Muted.TLabel", anchor="nw")
        self._bar_chart = BarChart(self)
        self._heat_map = HeatMap(self)
        self._table_frame = ScrollableTable(self, show="headings")
        self._visible_content: tk.Misc | None = None

    def bind_actions(self, on_change: Callable[[], None]) -> None:
        self._on_change = on_change

    def current_settings(self) -> ComparisonSettings:
        return ComparisonSettings(
            series=tuple(series for series, chosen in self._series_chosen.items() if chosen.get()),
            measure=_enum_with_label(Measure, self._measure.get()),
            data_kind=DataKind(self._data_kind.get()),
            sort_order=SortOrder(self._sort_order.get()),
            use_log_scale=self._use_log_scale.get(),
            view=ChartView[self._view.get()],
        )

    def set_log_scale_available(self, available: bool) -> None:
        self._log_scale_button.configure(state="normal" if available else "disabled")

    def show_message(self, text: str) -> None:
        self._summary.configure(text="")
        self._message.configure(text=text)
        self._show_only(self._message)

    def show_comparison(self, comparison: Comparison, view: ChartView) -> None:
        self._summary.configure(text=_summary_text(comparison))
        if view is ChartView.BARS:
            self._show_only(self._bar_chart)
            self._bar_chart.draw(comparison)
        elif view is ChartView.HEAT_MAP:
            self._show_only(self._heat_map)
            self._heat_map.draw(comparison)
        else:
            self._show_only(self._table_frame)
            self._fill_table(comparison)

    def _show_only(self, content: tk.Misc) -> None:
        if self._visible_content is content:
            return
        if self._visible_content is not None:
            self._visible_content.pack_forget()
        content.pack(fill="both", expand=True)
        self._visible_content = content

    def _build_series_row(self) -> None:
        row = ttk.Frame(self)
        row.pack(fill="x", pady=(0, ROW_SPACING))
        ttk.Label(row, text="Porównaj:", style="Muted.TLabel").pack(side="left", padx=(0, CONTROL_GAP))
        self._series_chosen: dict[Series, tk.BooleanVar] = {}
        for series in ALL_SERIES:
            chosen = tk.BooleanVar(value=series in SERIES_SELECTED_AT_START)
            self._series_chosen[series] = chosen
            ttk.Checkbutton(
                row, text=series.label, variable=chosen, command=self._changed
            ).pack(side="left", padx=(0, CONTROL_GAP))

    def _build_settings_row(self) -> None:
        row = ttk.Frame(self)
        row.pack(fill="x", pady=(0, ROW_SPACING))
        self._measure = self._add_combobox(row, "Miara:", [m.value.label for m in Measure], 24)
        self._data_kind = self._add_combobox(row, "Dane:", [k.value for k in DataKind], 9)
        self._sort_order = self._add_combobox(row, "Kolejność:", [s.value for s in SortOrder], 19)

        self._use_log_scale = tk.BooleanVar(value=True)
        self._log_scale_button = ttk.Checkbutton(
            row, text="Skala log.", variable=self._use_log_scale, command=self._changed
        )
        self._log_scale_button.pack(side="left", padx=(0, CONTROL_GAP))

        self._view = tk.StringVar(value=ChartView.BARS.name)
        for view in ChartView:
            ttk.Radiobutton(
                row, text=view.value, value=view.name, variable=self._view, command=self._changed
            ).pack(side="left", padx=(0, 8))

    def _add_combobox(
        self, row: ttk.Frame, label: str, options: list[str], width: int
    ) -> tk.StringVar:
        ttk.Label(row, text=label, style="Muted.TLabel").pack(side="left", padx=(0, 4))
        selected = tk.StringVar(value=options[0])
        box = ttk.Combobox(row, textvariable=selected, values=options, state="readonly", width=width)
        box.pack(side="left", padx=(0, CONTROL_GAP))
        box.bind("<<ComboboxSelected>>", lambda _event: self._changed())
        return selected

    def _changed(self) -> None:
        self._on_change()

    def _fill_table(self, comparison: Comparison) -> None:
        table = self._table_frame.table
        column_ids = ["file", *(series.label for series in comparison.series), "best"]
        table.delete(*table.get_children())
        table.configure(columns=column_ids)
        table.heading("file", text="Plik", anchor="w")
        table.column("file", width=FILE_COLUMN_WIDTH, anchor="w")
        for series in comparison.series:
            table.heading(series.label, text=series.label, anchor="e")
            table.column(series.label, width=VALUE_COLUMN_WIDTH, anchor="e")
        table.heading("best", text="Najlepszy", anchor="w")
        table.column("best", width=BEST_COLUMN_WIDTH, anchor="w")

        for row in comparison.rows:
            values = [
                row.cells[series].text if series in row.cells else NO_VALUE
                for series in comparison.series
            ]
            best = BEST_SEPARATOR.join(
                series.label for series in comparison.series if series in row.best_series
            )
            table.insert("", "end", values=(row.file_name, *values, best))


def _enum_with_label(enum_class: type[Enum], label: str) -> Enum:
    return next(member for member in enum_class if member.value.label == label)


def _summary_text(comparison: Comparison) -> str:
    total = len(comparison.rows)
    if len(comparison.series) < 2:
        return f"Plików: {total}. Zaznacz drugi zestaw, aby zobaczyć porównanie."
    wins = "   ".join(
        f"{series.label}: {comparison.wins[series]} z {total}" for series in comparison.series
    )
    return f"Najlepszy wynik w pliku (remis liczy się dla obu):   {wins}"
