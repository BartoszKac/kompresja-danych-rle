"""Kontroler: po każdej zmianie ustawień odświeża wykres lub tabelę."""

from rle_compressor.features.benchmark.model import BenchmarkResult
from rle_compressor.features.comparison.model import build_comparison


class ComparisonController:
    def __init__(self, view) -> None:
        self._view = view
        self._results: list[BenchmarkResult] = []
        view.bind_actions(on_change=self.refresh)
        self.refresh()

    def set_results(self, results: list[BenchmarkResult]) -> None:
        self._results = results
        self.refresh()

    def refresh(self) -> None:
        settings = self._view.current_settings()
        self._view.set_log_scale_available(settings.measure.value.supports_log)

        if not self._results:
            self._view.show_message("Najpierw uruchom testy w zakładce „Testy na różnych danych”.")
            return
        if not settings.series:
            self._view.show_message("Zaznacz co najmniej jeden zestaw do porównania.")
            return

        comparison = build_comparison(self._results, settings)
        if comparison is None:
            self._view.show_message("Brak wyników dla tych ustawień.")
        else:
            self._view.show_comparison(comparison, settings.view)
