"""Punkt wejścia: `python -m rle_compressor [benchmark [KATALOG]]`."""

import argparse
from pathlib import Path

from rle_compressor.config import SAMPLES_DIR


def main() -> None:
    arguments = _parse_arguments()
    if arguments.command == "benchmark":
        from rle_compressor.features.benchmark.cli import print_benchmark

        print_benchmark(arguments.samples_dir)
    else:
        # Import dopiero tutaj: tryb benchmark ma działać bez biblioteki Tk i ekranu.
        from rle_compressor.app import run_gui

        run_gui()


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="rle_compressor")
    commands = parser.add_subparsers(dest="command")
    benchmark = commands.add_parser("benchmark", help="testuje wszystkie pliki z katalogu")
    benchmark.add_argument("samples_dir", nargs="?", type=Path, default=SAMPLES_DIR)
    return parser.parse_args()


if __name__ == "__main__":
    main()
