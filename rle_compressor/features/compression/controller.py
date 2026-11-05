"""Kontroler: reaguje na przyciski kompresji i dekompresji."""

from pathlib import Path
from typing import Callable

from rle_compressor.features.compression import model
from rle_compressor.features.compression.model import CompressionReport, DecompressionReport

OnRestored = Callable[[Path | None, Path], None]


class CompressionController:
    def __init__(self, view, tasks, output_dir: Path, on_restored: OnRestored) -> None:
        self._view = view
        self._tasks = tasks
        self._output_dir = output_dir
        self._on_restored = on_restored
        self._source: Path | None = None
        self._archive: Path | None = None
        self._archive_origin: Path | None = None
        view.bind_actions(
            on_choose_source=self.choose_source,
            on_compress=self.compress,
            on_choose_archive=self.choose_archive,
            on_decompress=self.decompress,
        )

    def choose_source(self) -> None:
        source = self._view.ask_for_source()
        if source is not None:
            self._source = source
            self._view.show_source(source)

    def choose_archive(self) -> None:
        archive = self._view.ask_for_archive()
        if archive is not None:
            self._archive = archive
            self._archive_origin = None
            self._view.show_archive(archive)

    def compress(self) -> None:
        if self._source is None:
            self._view.show_compression_error("Najpierw wybierz plik do kompresji.")
            return

        source = self._source
        mode = self._view.selected_mode()
        algorithm = self._view.selected_algorithm()
        self._view.set_busy(True)
        self._tasks.run(
            work=lambda: model.compress_file(source, self._output_dir, mode, algorithm),
            on_success=self._compression_finished,
            on_error=self._compression_failed,
        )

    def decompress(self) -> None:
        if self._archive is None:
            self._view.show_decompression_error("Najpierw wybierz plik .rle lub .huf.")
            return

        archive = self._archive
        self._view.set_busy(True)
        self._tasks.run(
            work=lambda: model.decompress_file(archive, self._output_dir),
            on_success=self._decompression_finished,
            on_error=self._decompression_failed,
        )

    def _compression_finished(self, report: CompressionReport) -> None:
        self._view.set_busy(False)
        self._archive = report.archive
        self._archive_origin = report.source
        self._view.show_archive(report.archive)
        self._view.show_compression_report(report)

    def _compression_failed(self, error: Exception) -> None:
        self._view.set_busy(False)
        self._view.show_compression_error(f"Kompresja nie powiodła się: {error}")

    def _decompression_finished(self, report: DecompressionReport) -> None:
        self._view.set_busy(False)
        self._view.show_decompression_report(report)
        self._on_restored(self._archive_origin, report.restored)

    def _decompression_failed(self, error: Exception) -> None:
        self._view.set_busy(False)
        self._view.show_decompression_error(f"Dekompresja nie powiodła się: {error}")
