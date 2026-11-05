"""Wypisanie wyników testów w terminalu jako tabela Markdown."""

import sys
from pathlib import Path

from rle_compressor.features.benchmark.model import run_benchmark
from rle_compressor.shared.formatting import format_size


def print_benchmark(samples_dir: Path) -> None:
    if not samples_dir.is_dir():
        sys.exit(f"Brak katalogu z danymi testowymi: {samples_dir}")

    print("| Plik | Algorytm | Tryb | Przed | Po | Współczynnik | SHA-256 |")
    print("|---|---|---|---:|---:|---:|---|")
    for result in run_benchmark(samples_dir):
        print(
            f"| {result.file_name} | {result.algorithm.value} | {result.mode.value} "
            f"| {format_size(result.size_before)} "
            f"| {format_size(result.size_after)} | {result.ratio:.3f} | {result.verdict} |"
        )
