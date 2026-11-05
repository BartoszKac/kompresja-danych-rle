"""Kontroler: uruchamia testy i przekazuje wyniki do widoku."""

from pathlib import Path
from typing import Callable

from rle_compressor.features.benchmark.model import BenchmarkResult, run_benchmark


class BenchmarkController:
    def __init__(
        self,
        view,
        tasks,
        samples_dir: Path,
        on_results: Callable[[list[BenchmarkResult]], None] = lambda _results: None,
    ) -> None:
        self._view = view
        self._tasks = tasks
        self._samples_dir = samples_dir
        self._on_results = on_results
        view.bind_actions(on_run=self.run)
        view.show_message(f"Katalog z danymi testowymi: {samples_dir}")

    def run(self) -> None:
        if not self._samples_dir.is_dir():
            self._view.show_error(f"Brak katalogu z danymi testowymi: {self._samples_dir}")
            return

        self._view.set_busy(True)
        self._view.show_message("Trwa testowanie…")
        self._tasks.run(
            work=lambda: run_benchmark(self._samples_dir),
            on_success=self._benchmark_finished,
            on_error=self._benchmark_failed,
        )

    def _benchmark_finished(self, results: list[BenchmarkResult]) -> None:
        self._view.set_busy(False)
        self._view.show_results(results)
        if results:
            file_count = len({result.file_name for result in results})
            self._view.show_message(
                f"Przetestowano plików: {file_count}. "
                "Porównaj wyniki w zakładce „Wykresy i porównania”."
            )
            self._on_results(results)
        else:
            self._view.show_error(f"Katalog {self._samples_dir} jest pusty.")

    def _benchmark_failed(self, error: Exception) -> None:
        self._view.set_busy(False)
        self._view.show_error(f"Test nie powiódł się: {error}")
