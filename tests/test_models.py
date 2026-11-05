import tempfile
import unittest
from pathlib import Path

from rle_compressor.features.benchmark.model import run_benchmark
from rle_compressor.features.compression.archive_format import HEADER, Algorithm
from rle_compressor.features.compression.model import compress_file, decompress_file
from rle_compressor.features.verification.model import verify_files


class TemporaryDirectoryTestCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)

    def write_file(self, name: str, content: bytes) -> Path:
        path = self.directory / name
        path.write_bytes(content)
        return path


class CompressionModelTest(TemporaryDirectoryTestCase):
    def test_report_contains_sizes_and_ratio(self):
        source = self.write_file("data.bin", b"a" * 1000)

        report = compress_file(source, self.directory / "out")

        pairs_size = 2 * 4  # 1000 = 255 + 255 + 255 + 235, czyli cztery pary.
        self.assertEqual(report.size_before, 1000)
        self.assertEqual(report.size_after, HEADER.size + pairs_size)
        self.assertEqual(report.archive.stat().st_size, report.size_after)
        self.assertAlmostEqual(report.ratio, 1000 / report.size_after)

    def test_decompression_restores_name_and_content(self):
        source = self.write_file("photo.jpg", b"\x00\x00\xff\x10" * 50)
        output = self.directory / "out"

        archive = compress_file(source, output).archive
        report = decompress_file(archive, output)

        self.assertEqual(report.restored.name, "photo.jpg")
        self.assertEqual(report.restored.read_bytes(), source.read_bytes())


class VerificationModelTest(TemporaryDirectoryTestCase):
    def test_identical_files_match(self):
        first = self.write_file("a", b"same")
        second = self.write_file("b", b"same")
        self.assertTrue(verify_files(first, second).is_identical)

    def test_different_files_do_not_match(self):
        first = self.write_file("a", b"same")
        second = self.write_file("b", b"other")
        self.assertFalse(verify_files(first, second).is_identical)

    def test_known_hash(self):
        first = self.write_file("a", b"abc")
        second = self.write_file("b", b"abc")
        self.assertEqual(
            verify_files(first, second).original_sha256,
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )

    def test_same_path_twice_is_rejected(self):
        file = self.write_file("a", b"same")
        with self.assertRaises(ValueError):
            verify_files(file, file)


class BenchmarkModelTest(TemporaryDirectoryTestCase):
    def test_runs_full_cycle_for_each_file_and_skips_directories(self):
        self.write_file("runs.bin", b"a" * 5000)
        self.write_file("no_runs.bin", bytes(range(256)))
        (self.directory / "subdirectory").mkdir()

        results = run_benchmark(self.directory)

        by_name = {
            result.file_name: result for result in results if result.algorithm is Algorithm.RLE
        }
        self.assertEqual(set(by_name), {"runs.bin", "no_runs.bin"})
        self.assertTrue(all(result.is_identical for result in results))
        self.assertGreater(by_name["runs.bin"].ratio, 1)
        self.assertLess(by_name["no_runs.bin"].ratio, 1)


if __name__ == "__main__":
    unittest.main()
