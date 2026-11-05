"""Wykonywanie długich operacji w tle, tak aby okno programu nie zamarzało."""

import queue
import threading
import tkinter as tk
from typing import Any, Callable

POLL_INTERVAL_MS = 50


class TkTaskRunner:
    """Liczy w osobnym wątku, a wynik przekazuje z powrotem do wątku Tk.

    Tylko wątek główny może dotykać widżetów, dlatego wynik trafia do kolejki,
    którą wątek główny regularnie sprawdza.
    """

    def __init__(self, widget: tk.Misc) -> None:
        self._widget = widget

    def run(
        self,
        work: Callable[[], Any],
        on_success: Callable[[Any], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        finished: queue.SimpleQueue = queue.SimpleQueue()

        def work_in_background() -> None:
            try:
                finished.put((on_success, work()))
            except Exception as error:  # Każdy błąd musi dotrzeć do okna, inaczej zostałoby zablokowane.
                finished.put((on_error, error))

        threading.Thread(target=work_in_background, daemon=True).start()
        self._wait_for_result(finished)

    def _wait_for_result(self, finished: queue.SimpleQueue) -> None:
        try:
            callback, value = finished.get_nowait()
        except queue.Empty:
            self._widget.after(POLL_INTERVAL_MS, self._wait_for_result, finished)
        else:
            callback(value)
