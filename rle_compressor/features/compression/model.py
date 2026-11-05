"""Model: kompresja i dekompresja plików na dysku."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from rle_compressor.features.compression import archive_format, lossy_filter
from rle_compressor.features.compression.archive_format import Algorithm

ARCHIVE_SUFFIXES = {
    Algorithm.RLE: ".rle",
    Algorithm.HUFFMAN: ".huf",
}
LOSSY_NAME_MARK = ".stratna"
COMPRESSED_SUBDIR = "compressed"
RESTORED_SUBDIR = "restored"


class CompressionMode(Enum):
    LOSSLESS = "Bezstratna"
    LOSSY = "Stratna"


@dataclass(frozen=True)
class CompressionReport:
    source: Path
    archive: Path
    size_before: int
    size_after: int
    mode: CompressionMode = CompressionMode.LOSSLESS
    algorithm: Algorithm = Algorithm.RLE

    @property
    def ratio(self) -> float:
        """Współczynnik kompresji: rozmiar przed / rozmiar po."""
        return self.size_before / self.size_after


@dataclass(frozen=True)
class DecompressionReport:
    archive: Path
    restored: Path
    archive_size: int
    restored_size: int

    @property
    def is_lossy(self) -> bool:
        return LOSSY_NAME_MARK in self.archive.name


def compress_file(
    source: Path,
    output_dir: Path,
    mode: CompressionMode = CompressionMode.LOSSLESS,
    algorithm: Algorithm = Algorithm.RLE,
) -> CompressionReport:
    original = source.read_bytes()
    data_to_pack = lossy_filter.simplify(original) if mode is CompressionMode.LOSSY else original
    archive_bytes = archive_format.pack(data_to_pack, algorithm)

    file_name = _output_name(source, mode) + ARCHIVE_SUFFIXES[algorithm]
    archive = output_dir / COMPRESSED_SUBDIR / file_name
    _write_file(archive, archive_bytes)
    return CompressionReport(source, archive, len(original), len(archive_bytes), mode, algorithm)


def decompress_file(archive: Path, output_dir: Path) -> DecompressionReport:
    archive_bytes = archive.read_bytes()
    restored_bytes = archive_format.unpack(archive_bytes)

    restored = output_dir / RESTORED_SUBDIR / _original_name(archive)
    _write_file(restored, restored_bytes)
    return DecompressionReport(archive, restored, len(archive_bytes), len(restored_bytes))


def _output_name(source: Path, mode: CompressionMode) -> str:
    """Wynik stratny ma inną nazwę, aby nie nadpisać wyniku bezstratnego."""
    if mode is CompressionMode.LOSSY:
        return f"{source.stem}{LOSSY_NAME_MARK}{source.suffix}"
    return source.name


def _original_name(archive: Path) -> str:
    if archive.suffix in ARCHIVE_SUFFIXES.values():
        return archive.stem
    return archive.name


def _write_file(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
