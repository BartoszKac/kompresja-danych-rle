"""Poziome słupki: każdy plik ma grupę słupków, po jednym na zestaw."""

from rle_compressor.features.comparison.chart_canvas import (
    BASELINE_COLOR,
    GRID_COLOR,
    MUTED_INK,
    NAME_COLUMN_WIDTH,
    SERIES_COLORS,
    ChartCanvas,
    tooltip_lines,
)
from rle_compressor.features.comparison.model import Cell, Comparison, Row, Series
from rle_compressor.shared.formatting import format_size
from rle_compressor.shared.theme import BACKGROUND, TEXT

BAR_THICKNESS = 12
BAR_GAP = 2
GROUP_GAP = 16
TOP_PADDING = 6
VALUE_LABEL_ROOM = 76
MINIMUM_PLOT_WIDTH = 120
MINIMUM_BAR_LENGTH = 2
LEGEND_Y = 10
AXIS_TITLE_Y = 10
TICK_LABEL_Y = 42


class BarChart(ChartCanvas):
    def _draw_header(self, comparison: Comparison, width: int) -> None:
        self._draw_legend(comparison, LEGEND_Y)
        self.header.create_text(
            width, AXIS_TITLE_Y, text=_axis_title(comparison), anchor="e", fill=MUTED_INK
        )
        for tick in comparison.scale.ticks():
            self.header.create_text(
                self._x_of(comparison, tick, width), TICK_LABEL_Y,
                text=f"{tick:g}", anchor="center", fill=MUTED_INK,
            )

    def _draw_plot(self, comparison: Comparison, width: int) -> int:
        height = TOP_PADDING + sum(_group_height(row, comparison) for row in comparison.rows)
        self._draw_grid(comparison, width, height)

        y = TOP_PADDING
        for row_index, row in enumerate(comparison.rows):
            self._draw_group(comparison, row, row_index, y, width)
            y += _group_height(row, comparison)
        return height

    def _draw_grid(self, comparison: Comparison, width: int, height: int) -> None:
        for tick in comparison.scale.ticks():
            x = self._x_of(comparison, tick, width)
            self.plot.create_line(x, 0, x, height, fill=GRID_COLOR)
        baseline_x = self._x_of(comparison, comparison.scale.baseline, width)
        self.plot.create_line(baseline_x, 0, baseline_x, height, fill=BASELINE_COLOR)

    def _draw_group(
        self, comparison: Comparison, row: Row, row_index: int, top: int, width: int
    ) -> None:
        present = [series for series in comparison.series if series in row.cells]
        bars_height = len(present) * (BAR_THICKNESS + BAR_GAP) - BAR_GAP
        self.plot.create_text(
            NAME_COLUMN_WIDTH - 12, top + bars_height / 2,
            text=row.file_name, anchor="e", fill=TEXT,
        )
        for bar_index, series in enumerate(present):
            bar_top = top + bar_index * (BAR_THICKNESS + BAR_GAP)
            tag = f"bar-{row_index}-{bar_index}"
            self._draw_bar(comparison, row, series, bar_top, width, tag)

    def _draw_bar(
        self, comparison: Comparison, row: Row, series: Series, top: int, width: int, tag: str
    ) -> None:
        cell = row.cells[series]
        baseline_x = self._x_of(comparison, comparison.scale.baseline, width)
        tip_x = self._x_of(comparison, cell.value, width)
        grows_right = tip_x >= baseline_x
        if abs(tip_x - baseline_x) < MINIMUM_BAR_LENGTH:
            tip_x = baseline_x + MINIMUM_BAR_LENGTH * (1 if grows_right else -1)

        # Szerszy, niewidoczny obszar ułatwia najechanie na cienki słupek.
        hover_area = self.plot.create_rectangle(
            NAME_COLUMN_WIDTH, top - 1, width, top + BAR_THICKNESS + 1,
            fill=BACKGROUND, width=0, tags=tag,
        )
        self.plot.tag_lower(hover_area)
        self._draw_rounded_bar(baseline_x, tip_x, top, SERIES_COLORS[series], tag)
        self._bind_hover(tag, hover_area, _cell_tooltip(row.file_name, series, cell))

        if series in row.best_series:
            self.plot.create_text(
                tip_x + (6 if grows_right else -6), top + BAR_THICKNESS / 2,
                text=cell.text, anchor="w" if grows_right else "e", fill=TEXT,
                state="disabled",
            )

    def _draw_rounded_bar(self, baseline_x: float, tip_x: float, top: int, color: str, tag: str) -> None:
        """Przy osi koniec jest prosty, a przy wartości zaokrąglony."""
        radius = BAR_THICKNESS / 2
        direction = 1 if tip_x >= baseline_x else -1
        if abs(tip_x - baseline_x) <= radius:
            body_end = tip_x
        else:
            body_end = tip_x - direction * radius
            self.plot.create_oval(
                tip_x - BAR_THICKNESS if direction > 0 else tip_x,
                top,
                tip_x if direction > 0 else tip_x + BAR_THICKNESS,
                top + BAR_THICKNESS,
                fill=color, width=0, tags=tag,
            )
        self.plot.create_rectangle(
            baseline_x, top, body_end, top + BAR_THICKNESS, fill=color, width=0, tags=tag
        )

    def _x_of(self, comparison: Comparison, value: float, width: int) -> float:
        left = NAME_COLUMN_WIDTH + VALUE_LABEL_ROOM
        plot_width = max(width - left - VALUE_LABEL_ROOM, MINIMUM_PLOT_WIDTH)
        return left + plot_width * comparison.scale.fraction(value)


def _group_height(row: Row, comparison: Comparison) -> int:
    present = sum(series in row.cells for series in comparison.series)
    return present * (BAR_THICKNESS + BAR_GAP) - BAR_GAP + GROUP_GAP


def _axis_title(comparison: Comparison) -> str:
    title = comparison.measure.value.label
    return f"{title}, skala logarytmiczna" if comparison.scale.is_log else title


def _cell_tooltip(file_name: str, series: Series, cell: Cell) -> list[str]:
    return tooltip_lines(
        file_name,
        series,
        cell.text,
        format_size(cell.result.size_before),
        format_size(cell.result.size_after),
    )
