"""Wspólna podstawa wykresów: stały nagłówek, przewijany obszar rysowania i dymek."""

import tkinter as tk
from tkinter import ttk

from rle_compressor.features.comparison.model import ALL_SERIES, Comparison, Series
from rle_compressor.shared.theme import BACKGROUND, BORDER, SUBTLE_BACKGROUND, TEXT

# Barwy sprawdzone walidatorem daltonizmu. Kolor należy do zestawu, nie do pozycji na liście.
SERIES_COLORS = {
    ALL_SERIES[0]: "#2a78d6",
    ALL_SERIES[1]: "#eb6834",
    ALL_SERIES[2]: "#1baf7a",
    ALL_SERIES[3]: "#eda100",
}

GRID_COLOR = "#e1e0d9"
BASELINE_COLOR = "#98968e"
MUTED_INK = "#667085"
NAME_COLUMN_WIDTH = 240
HEADER_HEIGHT = 54
SWATCH_SIZE = 10
TOOLTIP_TAG = "tooltip"
TOOLTIP_PADDING = 6
TOOLTIP_OFFSET = 14
WHEEL_UNITS = 2


class ChartCanvas(ttk.Frame):
    """Podklasa rysuje wykres w metodach `_draw_header` i `_draw_plot`."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self._comparison: Comparison | None = None
        self.header = tk.Canvas(self, height=HEADER_HEIGHT, background=BACKGROUND, highlightthickness=0)
        self.header.pack(fill="x")
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        self.plot = tk.Canvas(body, background=BACKGROUND, highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.plot.yview)
        self.plot.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.plot.pack(side="left", fill="both", expand=True)
        self.plot.bind("<Configure>", lambda _event: self._redraw())
        self.plot.bind("<Button-4>", lambda _event: self.plot.yview_scroll(-WHEEL_UNITS, "units"))
        self.plot.bind("<Button-5>", lambda _event: self.plot.yview_scroll(WHEEL_UNITS, "units"))
        self.plot.bind(
            "<MouseWheel>",
            lambda event: self.plot.yview_scroll(-WHEEL_UNITS if event.delta > 0 else WHEEL_UNITS, "units"),
        )

    def draw(self, comparison: Comparison) -> None:
        self._comparison = comparison
        self.plot.yview_moveto(0)
        self._redraw()

    def _redraw(self) -> None:
        if self._comparison is None:
            return
        self.header.delete("all")
        self.plot.delete("all")
        width = self.plot.winfo_width()
        self._draw_header(self._comparison, width)
        height = self._draw_plot(self._comparison, width)
        self.plot.configure(scrollregion=(0, 0, width, height))

    def _draw_header(self, comparison: Comparison, width: int) -> None:
        raise NotImplementedError

    def _draw_plot(self, comparison: Comparison, width: int) -> int:
        """Rysuje wykres i zwraca jego wysokość."""
        raise NotImplementedError

    def _draw_legend(self, comparison: Comparison, y: int) -> None:
        x = 0
        for series in comparison.series:
            self.header.create_rectangle(
                x, y - SWATCH_SIZE // 2, x + SWATCH_SIZE, y + SWATCH_SIZE // 2,
                fill=SERIES_COLORS[series], width=0,
            )
            label = self.header.create_text(
                x + SWATCH_SIZE + 6, y, text=series.label, anchor="w", fill=TEXT
            )
            x = self.header.bbox(label)[2] + 18

    def _bind_hover(self, tag: str, target: int | None, lines: list[str]) -> None:
        """Dymek i podświetlenie po najechaniu; `target` to prostokąt podświetlany."""

        def show(event: tk.Event) -> None:
            if target is not None:
                self.plot.itemconfigure(target, fill=SUBTLE_BACKGROUND)
            self._show_tooltip(event, lines)

        def hide(_event: tk.Event) -> None:
            if target is not None:
                self.plot.itemconfigure(target, fill=BACKGROUND)
            self.plot.delete(TOOLTIP_TAG)

        self.plot.tag_bind(tag, "<Enter>", show)
        self.plot.tag_bind(tag, "<Motion>", show)
        self.plot.tag_bind(tag, "<Leave>", hide)

    def _show_tooltip(self, event: tk.Event, lines: list[str]) -> None:
        self.plot.delete(TOOLTIP_TAG)
        x = self.plot.canvasx(event.x) + TOOLTIP_OFFSET
        y = self.plot.canvasy(event.y) + TOOLTIP_OFFSET
        text = self.plot.create_text(
            x, y, text="\n".join(lines), anchor="nw", fill=TEXT, tags=TOOLTIP_TAG, state="disabled"
        )
        left, top, right, bottom = self.plot.bbox(text)
        view_right = self.plot.canvasx(self.plot.winfo_width())
        view_bottom = self.plot.canvasy(self.plot.winfo_height())
        shift_x = min(0, view_right - right - 2 * TOOLTIP_PADDING)
        shift_y = min(0, view_bottom - bottom - 2 * TOOLTIP_PADDING)
        self.plot.move(text, shift_x, shift_y)
        background = self.plot.create_rectangle(
            left + shift_x - TOOLTIP_PADDING,
            top + shift_y - TOOLTIP_PADDING,
            right + shift_x + TOOLTIP_PADDING,
            bottom + shift_y + TOOLTIP_PADDING,
            fill=BACKGROUND,
            outline=BORDER,
            tags=TOOLTIP_TAG,
            state="disabled",
        )
        self.plot.tag_lower(background, text)


def tooltip_lines(file_name: str, series: Series, text: str, size_before: str, size_after: str) -> list[str]:
    """Najpierw wartość, potem to, czego dotyczy."""
    return [text, series.label, file_name, f"{size_before} → {size_after}"]
