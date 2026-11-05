"""Model: przygotowuje wyniki testów do porównania według ustawień użytkownika."""

from dataclasses import dataclass
from enum import Enum
from pathlib import PurePath
from typing import Callable

from rle_compressor.features.benchmark.model import BenchmarkResult
from rle_compressor.features.comparison.value_scale import ValueScale
from rle_compressor.features.compression.archive_format import Algorithm
from rle_compressor.features.compression.model import CompressionMode
from rle_compressor.shared.formatting import format_size

BYTES_IN_MIB = 1024 * 1024


@dataclass(frozen=True)
class Series:
    """Zestaw porównywany na wykresie: algorytm w danym trybie."""

    algorithm: Algorithm
    mode: CompressionMode

    @property
    def label(self) -> str:
        return f"{self.algorithm.value}, {self.mode.value.lower()}"


# Stała kolejność: od niej zależy kolor zestawu, więc filtr nie zmienia kolorów pozostałych.
ALL_SERIES = (
    Series(Algorithm.RLE, CompressionMode.LOSSLESS),
    Series(Algorithm.HUFFMAN, CompressionMode.LOSSLESS),
    Series(Algorithm.RLE, CompressionMode.LOSSY),
    Series(Algorithm.HUFFMAN, CompressionMode.LOSSY),
)


def _space_saved_percent(result: BenchmarkResult) -> float:
    return 100 * (1 - result.size_after / result.size_before)


@dataclass(frozen=True)
class MeasureInfo:
    label: str
    read: Callable[[BenchmarkResult], float]
    describe: Callable[[BenchmarkResult], str]
    baseline: float | None  # Wartość oznaczająca „bez zmian”; None, gdy jej nie ma.
    higher_is_better: bool
    supports_log: bool


class Measure(Enum):
    RATIO = MeasureInfo(
        label="Współczynnik kompresji",
        read=lambda result: result.ratio,
        describe=lambda result: f"{result.ratio:.2f}",
        baseline=1.0,
        higher_is_better=True,
        supports_log=True,
    )
    SPACE_SAVED = MeasureInfo(
        label="Oszczędność miejsca [%]",
        read=_space_saved_percent,
        describe=lambda result: f"{_space_saved_percent(result):+.1f} %",
        baseline=0.0,
        higher_is_better=True,
        supports_log=False,
    )
    SIZE_AFTER = MeasureInfo(
        label="Rozmiar po kompresji [MiB]",
        read=lambda result: result.size_after / BYTES_IN_MIB,
        describe=lambda result: format_size(result.size_after),
        baseline=None,
        higher_is_better=False,
        supports_log=True,
    )


class DataKind(Enum):
    ALL = "Wszystkie"
    TEXT = "Tekst"
    IMAGE = "Obrazy"
    AUDIO = "Dźwięk"
    OTHER = "Inne"


_KIND_OF_SUFFIX = {
    ".txt": DataKind.TEXT,
    ".png": DataKind.IMAGE,
    ".jpg": DataKind.IMAGE,
    ".jpeg": DataKind.IMAGE,
    ".bmp": DataKind.IMAGE,
    ".mp3": DataKind.AUDIO,
    ".wav": DataKind.AUDIO,
}


class SortOrder(Enum):
    BEST_RESULT = "Od najlepszego wyniku"
    FILE_NAME = "Według nazwy pliku"


class ChartView(Enum):
    BARS = "Słupki"
    HEAT_MAP = "Mapa ciepła"
    TABLE = "Tabela"


@dataclass(frozen=True)
class ComparisonSettings:
    series: tuple[Series, ...]
    measure: Measure
    data_kind: DataKind
    sort_order: SortOrder
    use_log_scale: bool
    view: ChartView


@dataclass(frozen=True)
class Cell:
    value: float
    text: str
    result: BenchmarkResult


@dataclass(frozen=True)
class Row:
    file_name: str
    cells: dict[Series, Cell]
    best_series: frozenset[Series]


@dataclass(frozen=True)
class Comparison:
    series: tuple[Series, ...]
    measure: Measure
    rows: list[Row]
    scale: ValueScale
    wins: dict[Series, int]


def build_comparison(
    results: list[BenchmarkResult], settings: ComparisonSettings
) -> Comparison | None:
    """Zwraca None, gdy ustawienia nie obejmują żadnego wyniku."""
    info = settings.measure.value
    selected = tuple(series for series in ALL_SERIES if series in settings.series)
    rows = _build_rows(results, selected, settings)
    if not rows:
        return None

    values = [cell.value for row in rows for cell in row.cells.values()]
    use_log = settings.use_log_scale and info.supports_log
    wins = {
        series: sum(series in row.best_series for row in rows)
        for series in selected
    }
    return Comparison(
        series=selected,
        measure=settings.measure,
        rows=_sorted_rows(rows, settings),
        scale=ValueScale.for_values(values, info.baseline, use_log),
        wins=wins,
    )


def data_kind_of(file_name: str) -> DataKind:
    return _KIND_OF_SUFFIX.get(PurePath(file_name).suffix.lower(), DataKind.OTHER)


def _build_rows(
    results: list[BenchmarkResult], selected: tuple[Series, ...], settings: ComparisonSettings
) -> list[Row]:
    info = settings.measure.value
    cells_by_file: dict[str, dict[Series, Cell]] = {}
    for result in results:
        series = Series(result.algorithm, result.mode)
        if series in selected and _matches_kind(result.file_name, settings.data_kind):
            cell = Cell(info.read(result), info.describe(result), result)
            cells_by_file.setdefault(result.file_name, {})[series] = cell
    return [
        Row(file_name, cells, _best_series(cells, info))
        for file_name, cells in cells_by_file.items()
    ]


def _matches_kind(file_name: str, kind: DataKind) -> bool:
    return kind is DataKind.ALL or data_kind_of(file_name) is kind


def _best_series(cells: dict[Series, Cell], info: MeasureInfo) -> frozenset[Series]:
    pick = max if info.higher_is_better else min
    best_value = pick(cell.value for cell in cells.values())
    return frozenset(series for series, cell in cells.items() if cell.value == best_value)


def _sorted_rows(rows: list[Row], settings: ComparisonSettings) -> list[Row]:
    if settings.sort_order is SortOrder.FILE_NAME:
        return sorted(rows, key=lambda row: row.file_name)

    info = settings.measure.value
    pick = max if info.higher_is_better else min
    return sorted(
        rows,
        key=lambda row: pick(cell.value for cell in row.cells.values()),
        reverse=info.higher_is_better,
    )
