"""Kodowanie Huffmana: częste bajty dostają krótkie kody, a rzadkie długie.

Zapisany wynik to:
- tabela 256 bajtów: długość kodu każdej możliwej wartości bajtu (0 = bajt nie występuje),
- ciąg bitów: kody kolejnych bajtów, dopełnione zerami do pełnego bajtu.

Same długości wystarczą, ponieważ kody są kanoniczne: koder i dekoder wyznaczają je
z długości tą samą metodą, więc nie trzeba zapisywać całego drzewa.
"""

import heapq
from collections import Counter

from rle_compressor.features.compression.rle_codec import CorruptedDataError

SYMBOL_COUNT = 256
BITS_IN_BYTE = 8
TREE_ROOT = 0


def encode(data: bytes) -> bytes:
    lengths = _code_lengths(data)
    bit_strings = _as_bit_strings(_canonical_codes(lengths))
    bit_text = "".join(bit_strings[value] for value in data)
    return bytes(lengths) + _bit_text_to_bytes(bit_text)


def decode(encoded: bytes, expected_size: int) -> bytes:
    if len(encoded) < SYMBOL_COUNT:
        raise CorruptedDataError("Brak tabeli kodów Huffmana.")

    lengths = list(encoded[:SYMBOL_COUNT])
    tree = _build_decoding_tree(lengths)
    decoded = bytearray()
    if expected_size == 0:
        return bytes(decoded)

    node = TREE_ROOT
    for byte in encoded[SYMBOL_COUNT:]:
        for shift in range(BITS_IN_BYTE - 1, -1, -1):
            node = tree[node][(byte >> shift) & 1]
            if node is None:
                raise CorruptedDataError("Ciąg bitów zawiera nieznany kod Huffmana.")
            if node < 0:
                decoded.append(_symbol_of_leaf(node))
                if len(decoded) == expected_size:
                    return bytes(decoded)
                node = TREE_ROOT
    raise CorruptedDataError("Ciąg bitów Huffmana skończył się przedwcześnie.")


def _code_lengths(data: bytes) -> list[int]:
    """Algorytm Huffmana: łączymy dwie najrzadsze grupy, aż zostanie jedna.

    Każde połączenie wydłuża o 1 bit kod wszystkich bajtów w łączonych grupach.
    Elementy kolejki to (liczba wystąpień, wyróżnik remisów, bajty w grupie).
    """
    lengths = [0] * SYMBOL_COUNT
    counts = Counter(data)
    if len(counts) == 1:
        lengths[next(iter(counts))] = 1  # Jedyny bajt też potrzebuje kodu, choć drzewo nie ma rozgałęzień.
        return lengths

    queue = [(count, symbol, [symbol]) for symbol, count in counts.items()]
    heapq.heapify(queue)
    while len(queue) > 1:
        first_count, tie_breaker, first_group = heapq.heappop(queue)
        second_count, _, second_group = heapq.heappop(queue)
        merged_group = first_group + second_group
        for symbol in merged_group:
            lengths[symbol] += 1
        heapq.heappush(queue, (first_count + second_count, tie_breaker, merged_group))
    return lengths


def _canonical_codes(lengths: list[int]) -> dict[int, tuple[int, int]]:
    """Nadaje kody po kolei: najpierw krótsze, a przy równej długości mniejsze bajty."""
    used_symbols = sorted(
        (symbol for symbol in range(SYMBOL_COUNT) if lengths[symbol] > 0),
        key=lambda symbol: (lengths[symbol], symbol),
    )
    codes: dict[int, tuple[int, int]] = {}
    code = 0
    previous_length = 0
    for symbol in used_symbols:
        code <<= lengths[symbol] - previous_length
        codes[symbol] = (code, lengths[symbol])
        previous_length = lengths[symbol]
        code += 1
    return codes


def _as_bit_strings(codes: dict[int, tuple[int, int]]) -> dict[int, str]:
    return {symbol: format(code, f"0{length}b") for symbol, (code, length) in codes.items()}


def _bit_text_to_bytes(bit_text: str) -> bytes:
    if not bit_text:
        return b""
    padding = -len(bit_text) % BITS_IN_BYTE
    padded = bit_text + "0" * padding
    return int(padded, 2).to_bytes(len(padded) // BITS_IN_BYTE, "big")


def _build_decoding_tree(lengths: list[int]) -> list[list[int | None]]:
    """Każdy węzeł to [dziecko dla bitu 0, dziecko dla bitu 1]; liść ma ujemny numer."""
    _reject_impossible_lengths(lengths)
    tree: list[list[int | None]] = [[None, None]]
    for symbol, (code, length) in _canonical_codes(lengths).items():
        node = TREE_ROOT
        for shift in range(length - 1, 0, -1):
            bit = (code >> shift) & 1
            if tree[node][bit] is None:
                tree.append([None, None])
                tree[node][bit] = len(tree) - 1
            node = tree[node][bit]
        tree[node][code & 1] = _leaf_of_symbol(symbol)
    return tree


def _reject_impossible_lengths(lengths: list[int]) -> None:
    """Kody o takich długościach muszą mieścić się w drzewie (nierówność Krafta)."""
    longest = max(lengths)
    if sum(1 << (longest - length) for length in lengths if length > 0) > 1 << longest:
        raise CorruptedDataError("Tabela kodów Huffmana jest uszkodzona.")


def _leaf_of_symbol(symbol: int) -> int:
    return -symbol - 1


def _symbol_of_leaf(leaf: int) -> int:
    return -leaf - 1
