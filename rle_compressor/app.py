"""Składa okno programu: tworzy widoki i kontrolery oraz łączy je ze sobą."""

import tkinter as tk
from tkinter import ttk

from rle_compressor.config import DATA_DIR, OUTPUT_DIR, SAMPLES_DIR
from rle_compressor.features.benchmark.controller import BenchmarkController
from rle_compressor.features.benchmark.view import BenchmarkView
from rle_compressor.features.comparison.controller import ComparisonController
from rle_compressor.features.comparison.view import ComparisonView
from rle_compressor.features.compression.controller import CompressionController
from rle_compressor.features.compression.view import CompressionView
from rle_compressor.features.verification.controller import VerificationController
from rle_compressor.features.verification.view import VerificationView
from rle_compressor.shared.task_runner import TkTaskRunner
from rle_compressor.shared.theme import apply_theme

WINDOW_GEOMETRY = "1060x720+0+0"
OUTER_PADDING = 8


def run_gui() -> None:
    root = tk.Tk()
    root.title("Kompresja danych RLE")
    root.geometry(WINDOW_GEOMETRY)
    apply_theme(root)

    tasks = TkTaskRunner(root)
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=OUTER_PADDING, pady=OUTER_PADDING)

    file_tab = ttk.Frame(notebook, padding=OUTER_PADDING)
    notebook.add(file_tab, text="Kompresja pliku")
    benchmark_view = BenchmarkView(notebook)
    notebook.add(benchmark_view, text="Testy na różnych danych")
    comparison_view = ComparisonView(notebook)
    notebook.add(comparison_view, text="Wykresy i porównania")

    compression_view = CompressionView(file_tab, initial_dir=DATA_DIR)
    compression_view.pack(fill="x")
    verification_view = VerificationView(file_tab, initial_dir=DATA_DIR)
    verification_view.pack(fill="x", pady=(OUTER_PADDING, 0))

    verification = VerificationController(verification_view, tasks)
    CompressionController(
        compression_view,
        tasks,
        OUTPUT_DIR,
        on_restored=verification.prefill,
    )
    comparison = ComparisonController(comparison_view)
    BenchmarkController(benchmark_view, tasks, SAMPLES_DIR, on_results=comparison.set_results)

    root.mainloop()
