"""Mapa ciepła: wiersze to pliki, kolumny to zestawy, a kolor pokazuje wartość.

Gdy miara ma punkt „bez zmian”, skala jest rozbieżna: niebieski oznacza mniejszy plik,
czerwony większy, a szary brak zmiany. Rozmiar po kompresji nie ma takiego punktu,
dlatego używa jednego odcienia: im ciemniej, tym większy plik.
"""

from rle_compressor.features.comparison.chart_canvas import (
    MUTED_INK,
    NAME_COLUMN_WIDTH,
    ChartCanvas,
    tooltip_lines,
)
from rle_compressor.features.comparison.model import Comparison, Series
from rle_compressor.features.comparison.value_scale import ValueScale
from rle_compressor.shared.formatting import format_size
from rle_compressor.shared.theme import BACKGROUND, BORDER, TEXT

CELL_HEIGHT = 34
CELL_GAP = 2
LEGEND_Y = 10
COLUMN_TITLE_Y = 42

NEUTRAL = (0xf0, 0xef, 0xec)
GOOD_POLE = (0x1c, 0x5c, 0xab)
BAD_POLE = (0xc9, 0x35, 0x34)
SEQUENTIAL_LIGHT = (0xcd, 0xe2, 0xfb)
SEQUENTIAL_DARK = (0x0d, 0x36, 0x6b)
DARK_INK = "#0b0b0b"
LIGHT_INK = "#ffffff"
LUMINANCE_THRESHOLD = 0.45

DIVERGING_LEGEND = "Niebieski: plik mniejszy   Szary: bez zmian   Czerwony: plik większy"
SEQUENTIAL_LEGEND = "Im ciemniej, tym większy plik po kompresji"


class HeatMap(ChartCanvas):
    def _draw_header(self, comparison: Comparison, width: int) -> None:
        legend = (
            SEQUENTIAL_LEGEND
            if comparison.measure.value.baseline is None
            else DIVERGING_LEGEND
        )
        self.header.create_text(0, LEGEND_Y, text=legend, anchor="w", fill=MUTED_INK)
        self.header.create_text(
            width, LEGEND_Y, text=comparison.measure.value.label, anchor="e", fill=MUTED_INK
        )
        column_width = _column_width(comparison, width)
        for index, series in enumerate(comparison.series):
            self.header.create_text(
                NAME_COLUMN_WIDTH + column_width * (index + 0.5), COLUMN_TITLE_Y,
                text=series.label, anchor="center", fill=TEXT,
            )

    def _draw_plot(self, comparison: Comparison, width: int) -> int:
        column_width = _column_width(comparison, width)
        for row_index, row in enumerate(comparison.rows):
            top = row_index * CELL_HEIGHT
            self.plot.create_text(
                NAME_COLUMN_WIDTH - 12, top + CELL_HEIGHT / 2,
                text=row.file_name, anchor="e", fill=TEXT,
            )
            for column_index, series in enumerate(comparison.series):
                self._draw_cell(comparison, row_index, column_index, series, top, column_width)
        return len(comparison.rows) * CELL_HEIGHT

    def _draw_cell(
        self,
        comparison: Comparison,
        row_index: int,
        column_index: int,
        series: Series,
        top: int,
        column_width: float,
    ) -> None:
        row = comparison.rows[row_index]
        left = NAME_COLUMN_WIDTH + column_index * column_width
        right = left + column_width - CELL_GAP
        bottom = top + CELL_HEIGHT - CELL_GAP
        center = ((left + right) / 2, (top + bottom) / 2)
        cell = row.cells.get(series)

        if cell is None:
            self.plot.create_rectangle(left, top, right, bottom, fill=BACKGROUND, outline=BORDER)
            self.plot.create_text(*center, text="brak", fill=MUTED_INK)
            return

        tag = f"cell-{row_index}-{column_index}"
        color = _cell_color(comparison, cell.value)
        self.plot.create_rectangle(left, top, right, bottom, fill=_as_hex(color), width=0, tags=tag)
        marker = "  najlepszy" if series in row.best_series and len(row.cells) > 1 else ""
        self.plot.create_text(
            *center, text=cell.text + marker, fill=_ink_on(color), tags=tag
        )
        self._bind_hover(
            tag,
            None,
            tooltip_lines(
                row.file_name,
                series,
                cell.text,
                format_size(cell.result.size_before),
                format_size(cell.result.size_after),
            ),
        )


def _column_width(comparison: Comparison, width: int) -> float:
    return (width - NAME_COLUMN_WIDTH) / len(comparison.series)


def _cell_color(comparison: Comparison, value: float) -> tuple[int, int, int]:
    scale = comparison.scale
    if comparison.measure.value.baseline is None:
        return _mix(SEQUENTIAL_LIGHT, SEQUENTIAL_DARK, scale.fraction(value))
    strength = _distance_from_baseline(scale, value)
    return _mix(NEUTRAL, GOOD_POLE if value > scale.baseline else BAD_POLE, strength)


def _distance_from_baseline(scale: ValueScale, value: float) -> float:
    """Oba ramiona skali mają tę samą miarę, aby kolory uczciwie oddawały odległość."""
    position = scale.fraction(value)
    baseline = scale.fraction(scale.baseline)
    longest_arm = max(baseline, 1 - baseline)
    return abs(position - baseline) / longest_arm if longest_arm else 0.0


def _mix(start: tuple[int, int, int], end: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(round(a + (b - a) * amount) for a, b in zip(start, end))


def _as_hex(color: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*color)


def _ink_on(color: tuple[int, int, int]) -> str:
    red, green, blue = (channel / 255 for channel in color)
    luminance = 0.299 * red + 0.587 * green + 0.114 * blue
    return DARK_INK if luminance > LUMINANCE_THRESHOLD else LIGHT_INK
