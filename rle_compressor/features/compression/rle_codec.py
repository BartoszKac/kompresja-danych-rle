"""Algorytm RLE (Run-Length Encoding).

Każdą serię jednakowych bajtów zapisujemy jako dwa bajty: liczność i wartość.
Przykład: AAAAB (41 41 41 41 42) staje się parami (4, 41) (1, 42).
"""

MAX_RUN_LENGTH = 255  # Tyle mieści się w jednym bajcie liczności.
BYTES_PER_PAIR = 2


class CorruptedDataError(ValueError):
    """Dane nie są poprawnym wynikiem kompresji."""


def encode(data: bytes) -> bytes:
    encoded = bytearray()
    position = 0
    while position < len(data):
        run_length = _run_length_at(data, position)
        encoded.append(run_length)
        encoded.append(data[position])
        position += run_length
    return bytes(encoded)


def decode(encoded: bytes) -> bytes:
    if len(encoded) % BYTES_PER_PAIR != 0:
        raise CorruptedDataError("Dane RLE muszą składać się z pełnych par bajtów.")

    decoded = bytearray()
    for position in range(0, len(encoded), BYTES_PER_PAIR):
        run_length = encoded[position]
        value = encoded[position + 1]
        if run_length == 0:
            raise CorruptedDataError("Seria RLE nie może mieć długości 0.")
        decoded.extend(bytes((value,)) * run_length)
    return bytes(decoded)


def _run_length_at(data: bytes, start: int) -> int:
    """Liczy jednakowe bajty od pozycji `start`, najwyżej MAX_RUN_LENGTH."""
    limit = min(start + MAX_RUN_LENGTH, len(data))
    position = start + 1
    while position < limit and data[position] == data[start]:
        position += 1
    return position - start
