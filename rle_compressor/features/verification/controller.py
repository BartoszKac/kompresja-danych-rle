"""Kontroler: reaguje na przyciski weryfikacji."""

from pathlib import Path

from rle_compressor.features.verification import model
from rle_compressor.features.verification.model import VerificationResult


class VerificationController:
    def __init__(self, view, tasks) -> None:
        self._view = view
        self._tasks = tasks
        self._original: Path | None = None
        self._restored: Path | None = None
        view.bind_actions(
            on_choose_original=self.choose_original,
            on_choose_restored=self.choose_restored,
            on_verify=self.verify,
        )

    def prefill(self, original: Path | None, restored: Path) -> None:
        """Podstawia pliki z poprzednich kroków, aby użytkownik nie wybierał ich ręcznie."""
        if original is not None:
            self._original = original
            self._view.show_original(original)
        self._restored = restored
        self._view.show_restored(restored)

    def choose_original(self) -> None:
        original = self._view.ask_for_original()
        if original is not None:
            self._original = original
            self._view.show_original(original)

    def choose_restored(self) -> None:
        restored = self._view.ask_for_restored()
        if restored is not None:
            self._restored = restored
            self._view.show_restored(restored)

    def verify(self) -> None:
        if self._original is None or self._restored is None:
            self._view.show_error("Wybierz oryginał i plik po dekompresji.")
            return

        original, restored = self._original, self._restored
        self._view.set_busy(True)
        self._tasks.run(
            work=lambda: model.verify_files(original, restored),
            on_success=self._verification_finished,
            on_error=self._verification_failed,
        )

    def _verification_finished(self, result: VerificationResult) -> None:
        self._view.set_busy(False)
        self._view.show_result(result)

    def _verification_failed(self, error: Exception) -> None:
        self._view.set_busy(False)
        self._view.show_error(f"Weryfikacja nie powiodła się: {error}")
