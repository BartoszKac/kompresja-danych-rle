"""Format pliku wynikowego: nagłówek, po którym następują dane skompresowane.

Nagłówek (12 bajtów): znacznik algorytmu (4 B) i rozmiar oryginału (8 B, big-endian).
Znacznik mówi, którym algorytmem dekompresować, a rozmiar pozwala wykryć plik
uszkodzony lub ucięty.
"""

import struct
from enum import Enum

from rle_compressor.features.compression import huffman_codec, rle_codec
from rle_compressor.features.compression.rle_codec import CorruptedDataError

HEADER = struct.Struct(">4sQ")


class Algorithm(Enum):
    RLE = "RLE"
    HUFFMAN = "Huffman"


_MAGIC = {
    Algorithm.RLE: b"RLE1",
    Algorithm.HUFFMAN: b"HUF1",
}
_ALGORITHM_OF_MAGIC = {magic: algorithm for algorithm, magic in _MAGIC.items()}


def pack(original: bytes, algorithm: Algorithm = Algorithm.RLE) -> bytes:
    header = HEADER.pack(_MAGIC[algorithm], len(original))
    if algorithm is Algorithm.HUFFMAN:
        return header + huffman_codec.encode(original)
    return header + rle_codec.encode(original)


def unpack(archive: bytes) -> bytes:
    if len(archive) < HEADER.size:
        raise CorruptedDataError("Plik jest za krótki, aby zawierać nagłówek.")

    magic, expected_size = HEADER.unpack_from(archive)
    algorithm = _ALGORITHM_OF_MAGIC.get(magic)
    if algorithm is None:
        raise CorruptedDataError("To nie jest plik utworzony przez ten program.")

    payload = archive[HEADER.size:]
    if algorithm is Algorithm.HUFFMAN:
        return huffman_codec.decode(payload, expected_size)

    original = rle_codec.decode(payload)
    if len(original) != expected_size:
        raise CorruptedDataError(
            f"Oczekiwano {expected_size} B danych, a odtworzono {len(original)} B."
        )
    return original
