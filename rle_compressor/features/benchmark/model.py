"""Model: pełny cykl kompresja–dekompresja–weryfikacja dla każdego pliku w katalogu."""

import tempfile
from dataclasses import dataclass
from pathlib import Path

from rle_compressor.features.compression.archive_format import Algorithm
from rle_compressor.features.compression.lossy_filter import UnsupportedForLossyError
from rle_compressor.features.compression.model import (
    CompressionMode,
    compress_file,
    decompress_file,
)
from rle_compressor.features.verification.model import verify_files


@dataclass(frozen=True)
class BenchmarkResult:
    file_name: str
    algorithm: Algorithm
    mode: CompressionMode
    size_before: int
    size_after: int
    ratio: float
    is_identical: bool

    @property
    def verdict(self) -> str:
        if self.is_identical:
            return "zgodne"
        if self.mode is CompressionMode.LOSSY:
            return "różne (stratna)"
        return "NIEZGODNE"


def run_benchmark(samples_dir: Path) -> list[BenchmarkResult]:
    results: list[BenchmarkResult] = []
    with tempfile.TemporaryDirectory() as temporary_dir:
        for sample in sorted(samples_dir.iterdir()):
            if sample.is_file():
                for algorithm in Algorithm:
                    results.extend(_test_sample(sample, Path(temporary_dir), algorithm))
    return results


def _test_sample(sample: Path, work_dir: Path, algorithm: Algorithm) -> list[BenchmarkResult]:
    results = [_run_cycle(sample, work_dir, CompressionMode.LOSSLESS, algorithm)]
    try:
        results.append(_run_cycle(sample, work_dir, CompressionMode.LOSSY, algorithm))
    except UnsupportedForLossyError:
        pass  # Tryb stratny dotyczy tylko WAV i BMP, pozostałe pliki mają mniej wierszy.
    return results


def _run_cycle(
    sample: Path, work_dir: Path, mode: CompressionMode, algorithm: Algorithm
) -> BenchmarkResult:
    compression = compress_file(sample, work_dir, mode, algorithm)
    decompression = decompress_file(compression.archive, work_dir)
    verification = verify_files(sample, decompression.restored)
    return BenchmarkResult(
        file_name=sample.name,
        algorithm=algorithm,
        mode=mode,
        size_before=compression.size_before,
        size_after=compression.size_after,
        ratio=compression.ratio,
        is_identical=verification.is_identical,
    )
