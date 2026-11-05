import random
import unittest

from rle_compressor.features.compression.rle_codec import (
    MAX_RUN_LENGTH,
    CorruptedDataError,
    decode,
    encode,
)


class EncodeTest(unittest.TestCase):
    def test_empty_data_stays_empty(self):
        self.assertEqual(encode(b""), b"")

    def test_run_becomes_count_and_value(self):
        self.assertEqual(encode(b"AAAAB"), bytes((4, 65, 1, 66)))

    def test_run_longer_than_limit_is_split(self):
        self.assertEqual(
            encode(b"A" * (MAX_RUN_LENGTH + 1)),
            bytes((MAX_RUN_LENGTH, 65, 1, 65)),
        )

    def test_data_without_runs_doubles_in_size(self):
        data = bytes(range(100))
        self.assertEqual(len(encode(data)), 2 * len(data))


class RoundTripTest(unittest.TestCase):
    def test_restores_original_data(self):
        generator = random.Random(1)
        cases = {
            "empty": b"",
            "single byte": b"x",
            "exactly the limit": b"a" * MAX_RUN_LENGTH,
            "limit plus one": b"a" * (MAX_RUN_LENGTH + 1),
            "every byte value": bytes(range(256)),
            "zero bytes": bytes(1000),
            "random": generator.randbytes(10_000),
        }
        for name, data in cases.items():
            with self.subTest(name):
                self.assertEqual(decode(encode(data)), data)


class DecodeErrorsTest(unittest.TestCase):
    def test_incomplete_pair_is_rejected(self):
        with self.assertRaises(CorruptedDataError):
            decode(b"\x01\x41\x02")

    def test_zero_run_length_is_rejected(self):
        with self.assertRaises(CorruptedDataError):
            decode(b"\x00\x41")


if __name__ == "__main__":
    unittest.main()
