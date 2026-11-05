"""Kontrolery testujemy bez Tk: widok zastępuje atrapa, a zadania wykonują się od razu."""

import io
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock

from rle_compressor.features.benchmark.controller import BenchmarkController
from rle_compressor.features.compression.archive_format import Algorithm
from rle_compressor.features.compression.controller import CompressionController
from rle_compressor.features.compression.model import CompressionMode
from rle_compressor.features.verification.controller import VerificationController


class ImmediateTaskRunner:
    def run(self, work, on_success, on_error):
        try:
            result = work()
        except Exception as error:
            on_error(error)
        else:
            on_success(result)


class ControllerTestCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.tasks = ImmediateTaskRunner()


class CompressionControllerTest(ControllerTestCase):
    def setUp(self):
        super().setUp()
        self.view = Mock()
        self.view.selected_mode.return_value = CompressionMode.LOSSLESS
        self.view.selected_algorithm.return_value = Algorithm.RLE
        self.on_restored = Mock()
        self.output = self.directory / "out"
        self.controller = CompressionController(
            self.view, self.tasks, self.output, self.on_restored
        )
        self.source = self.directory / "data.bin"
        self.source.write_bytes(b"a" * 1000)

    def choose_source(self):
        self.view.ask_for_source.return_value = self.source
        self.controller.choose_source()

    def test_compress_without_file_shows_error(self):
        self.controller.compress()
        self.view.show_compression_error.assert_called_once()
        self.view.set_busy.assert_not_called()

    def test_cancelled_dialog_changes_nothing(self):
        self.view.ask_for_source.return_value = None
        self.controller.choose_source()
        self.view.show_source.assert_not_called()

    def test_compress_shows_report_and_prepares_decompression(self):
        self.choose_source()

        self.controller.compress()

        report = self.view.show_compression_report.call_args.args[0]
        self.assertEqual(report.size_before, 1000)
        self.view.show_archive.assert_called_once_with(report.archive)
        self.view.set_busy.assert_called_with(False)

    def test_full_cycle_passes_both_files_to_verification(self):
        self.choose_source()
        self.controller.compress()

        self.controller.decompress()

        restored = self.view.show_decompression_report.call_args.args[0].restored
        self.on_restored.assert_called_once_with(self.source, restored)
        self.assertEqual(restored.read_bytes(), self.source.read_bytes())

    def test_manually_chosen_archive_has_unknown_original(self):
        self.choose_source()
        self.controller.compress()
        archive = self.view.show_archive.call_args.args[0]
        self.view.ask_for_archive.return_value = archive
        self.controller.choose_archive()

        self.controller.decompress()

        self.assertIsNone(self.on_restored.call_args.args[0])

    def test_selected_algorithm_is_used_and_decompression_detects_it(self):
        self.choose_source()
        self.view.selected_algorithm.return_value = Algorithm.HUFFMAN

        self.controller.compress()
        self.controller.decompress()

        report = self.view.show_compression_report.call_args.args[0]
        self.assertEqual(report.algorithm, Algorithm.HUFFMAN)
        self.assertEqual(report.archive.suffix, ".huf")
        restored = self.view.show_decompression_report.call_args.args[0].restored
        self.assertEqual(restored.read_bytes(), self.source.read_bytes())

    def test_lossy_mode_for_unsupported_file_shows_error_and_unlocks_view(self):
        self.choose_source()
        self.view.selected_mode.return_value = CompressionMode.LOSSY

        self.controller.compress()

        self.view.show_compression_error.assert_called_once()
        self.view.show_compression_report.assert_not_called()
        self.view.set_busy.assert_called_with(False)

    def test_corrupted_archive_shows_error_and_unlocks_view(self):
        broken = self.directory / "broken.rle"
        broken.write_bytes(b"not an archive at all")
        self.view.ask_for_archive.return_value = broken
        self.controller.choose_archive()

        self.controller.decompress()

        self.view.show_decompression_error.assert_called_once()
        self.view.set_busy.assert_called_with(False)
        self.on_restored.assert_not_called()


class VerificationControllerTest(ControllerTestCase):
    def setUp(self):
        super().setUp()
        self.view = Mock()
        self.controller = VerificationController(self.view, self.tasks)

    def write_file(self, name, content):
        path = self.directory / name
        path.write_bytes(content)
        return path

    def test_verify_without_files_shows_error(self):
        self.controller.verify()
        self.view.show_error.assert_called_once()

    def test_prefill_then_verify_reports_match(self):
        self.controller.prefill(self.write_file("a", b"x"), self.write_file("b", b"x"))

        self.controller.verify()

        self.assertTrue(self.view.show_result.call_args.args[0].is_identical)

    def test_prefill_without_original_keeps_previous_choice(self):
        original = self.write_file("a", b"x")
        self.view.ask_for_original.return_value = original
        self.controller.choose_original()

        self.controller.prefill(None, self.write_file("b", b"x"))
        self.controller.verify()

        self.assertTrue(self.view.show_result.call_args.args[0].is_identical)

    def test_missing_file_shows_error(self):
        self.controller.prefill(self.directory / "missing", self.write_file("b", b"x"))

        self.controller.verify()

        self.view.show_error.assert_called_once()
        self.view.set_busy.assert_called_with(False)


class BenchmarkControllerTest(ControllerTestCase):
    def setUp(self):
        super().setUp()
        self.view = Mock()

    def test_missing_directory_shows_error(self):
        controller = BenchmarkController(self.view, self.tasks, self.directory / "missing")
        controller.run()
        self.view.show_error.assert_called_once()

    def test_empty_directory_shows_error(self):
        controller = BenchmarkController(self.view, self.tasks, self.directory)
        controller.run()
        self.view.show_error.assert_called_once()

    def test_results_reach_view(self):
        (self.directory / "sample.bin").write_bytes(b"abc")
        controller = BenchmarkController(self.view, self.tasks, self.directory)

        controller.run()

        results = self.view.show_results.call_args.args[0]
        self.assertEqual({result.file_name for result in results}, {"sample.bin"})

    def test_message_counts_files_not_table_rows(self):
        wav = io.BytesIO()
        with wave.open(wav, "wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(1)
            writer.setframerate(8000)
            writer.writeframes(bytes(100))
        (self.directory / "sound.wav").write_bytes(wav.getvalue())
        controller = BenchmarkController(self.view, self.tasks, self.directory)

        controller.run()

        self.assertEqual(len(self.view.show_results.call_args.args[0]), 4)
        self.assertIn("Przetestowano plików: 1.", self.view.show_message.call_args.args[0])

    def test_results_are_passed_on_for_comparison(self):
        (self.directory / "sample.bin").write_bytes(b"abc")
        on_results = Mock()
        controller = BenchmarkController(self.view, self.tasks, self.directory, on_results)

        controller.run()

        self.assertEqual(on_results.call_args.args[0], self.view.show_results.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
