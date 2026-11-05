import unittest

from rle_compressor.features.compression.archive_format import HEADER, pack, unpack
from rle_compressor.features.compression.rle_codec import CorruptedDataError


class ArchiveFormatTest(unittest.TestCase):
    def test_round_trip(self):
        self.assertEqual(unpack(pack(b"aaabbc")), b"aaabbc")

    def test_empty_file_round_trip(self):
        self.assertEqual(unpack(pack(b"")), b"")

    def test_foreign_file_is_rejected(self):
        with self.assertRaises(CorruptedDataError):
            unpack(b"To nie jest archiwum RLE")

    def test_too_short_file_is_rejected(self):
        with self.assertRaises(CorruptedDataError):
            unpack(b"RLE1")

    def test_truncated_archive_is_rejected(self):
        archive = pack(b"aaabbc")
        with self.assertRaises(CorruptedDataError):
            unpack(archive[: HEADER.size + 2])


if __name__ == "__main__":
    unittest.main()
