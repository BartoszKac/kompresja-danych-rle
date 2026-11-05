import random
import tempfile
import unittest
from pathlib import Path

from rle_compressor.features.compression.archive_format import Algorithm, pack, unpack
from rle_compressor.features.compression.huffman_codec import SYMBOL_COUNT, decode, encode
from rle_compressor.features.compression.model import compress_file, decompress_file
from rle_compressor.features.compression.rle_codec import CorruptedDataError


def code_lengths_of(data: bytes) -> list[int]:
    return list(encode(data)[:SYMBOL_COUNT])


class CodeLengthsTest(unittest.TestCase):
    def test_abrakadabra_takes_23_bits(self):
        data = b"ABRAKADABRA"
        lengths = code_lengths_of(data)

        self.assertEqual(sum(lengths[value] for value in data), 23)
        self.assertEqual(lengths[ord("A")], 1)

    def test_frequent_byte_never_gets_longer_code_than_rare_one(self):
        lengths = code_lengths_of(b"a" * 100 + b"b" * 10 + b"c")
        self.assertLessEqual(lengths[ord("a")], lengths[ord("b")])
        self.assertLessEqual(lengths[ord("b")], lengths[ord("c")])

    def test_single_byte_value_gets_one_bit_code(self):
        lengths = code_lengths_of(b"zzzz")
        self.assertEqual(lengths[ord("z")], 1)
        self.assertEqual(sum(lengths), 1)

    def test_encoded_data_has_table_and_packed_bits(self):
        self.assertEqual(len(encode(b"z" * 16)), SYMBOL_COUNT + 2)


class RoundTripTest(unittest.TestCase):
    def test_restores_original_data(self):
        generator = random.Random(1)
        cases = {
            "empty": b"",
            "single byte": b"x",
            "one value": b"a" * 1000,
            "two values": b"ab" * 500,
            "every byte value": bytes(range(256)),
            "skewed": b"a" * 5000 + bytes(range(256)),
            "random": generator.randbytes(20_000),
            "abrakadabra": b"ABRAKADABRA",
        }
        for name, data in cases.items():
            with self.subTest(name):
                self.assertEqual(decode(encode(data), len(data)), data)

    def test_fibonacci_frequencies_with_very_long_codes(self):
        """Taki rozkład daje najdłuższe możliwe kody."""
        data = bytearray()
        previous, current = 1, 1
        for symbol in range(22):
            data.extend(bytes((symbol,)) * current)
            previous, current = current, previous + current
        self.assertEqual(decode(encode(bytes(data)), len(data)), bytes(data))
        self.assertGreater(max(code_lengths_of(bytes(data))), 16)


class CompressionEffectTest(unittest.TestCase):
    def test_shrinks_text_without_runs(self):
        phrase = b"Kompresja bezstratna odtwarza dane co do bitu. " * 200
        self.assertLess(len(encode(phrase)), len(phrase))


class DecodeErrorsTest(unittest.TestCase):
    def test_missing_table_is_rejected(self):
        with self.assertRaises(CorruptedDataError):
            decode(bytes(10), 1)

    def test_impossible_code_lengths_are_rejected(self):
        table = bytearray(SYMBOL_COUNT)
        table[:3] = (1, 1, 1)  # Trzy kody 1-bitowe nie mogą istnieć.
        with self.assertRaises(CorruptedDataError):
            decode(bytes(table) + b"\x00", 1)

    def test_too_few_bits_are_rejected(self):
        encoded = encode(b"abcabc")
        with self.assertRaises(CorruptedDataError):
            decode(encoded, 1000)

    def test_unknown_code_is_rejected(self):
        table = bytearray(SYMBOL_COUNT)
        table[ord("a")] = 1  # Jedyny kod to 0, więc bit 1 jest nieznany.
        with self.assertRaises(CorruptedDataError):
            decode(bytes(table) + b"\xff", 1)


class ArchiveAndFilesTest(unittest.TestCase):
    def test_archive_remembers_algorithm(self):
        for algorithm in Algorithm:
            with self.subTest(algorithm):
                self.assertEqual(unpack(pack(b"aaabbc", algorithm)), b"aaabbc")

    def test_huffman_file_round_trip_uses_own_suffix(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "tekst.txt"
            source.write_bytes(b"ala ma kota " * 500)
            output = Path(directory) / "out"

            report = compress_file(source, output, algorithm=Algorithm.HUFFMAN)
            restored = decompress_file(report.archive, output).restored

            self.assertEqual(report.archive.name, "tekst.txt.huf")
            self.assertGreater(report.ratio, 1)
            self.assertEqual(restored.name, "tekst.txt")
            self.assertEqual(restored.read_bytes(), source.read_bytes())


if __name__ == "__main__":
    unittest.main()
