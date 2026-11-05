import io
import random
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from rle_compressor.features.benchmark.model import run_benchmark
from rle_compressor.features.compression.lossy_filter import (
    AUDIO_QUANTIZATION_STEP,
    HOLD_LENGTH,
    IMAGE_QUANTIZATION_STEP,
    UnsupportedForLossyError,
    simplify,
)
from rle_compressor.features.compression.model import (
    CompressionMode,
    compress_file,
    decompress_file,
)

FRAME_RATE = 8000


def make_wav(samples: bytes, sample_width: int = 2, channels: int = 1) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(channels)
        writer.setsampwidth(sample_width)
        writer.setframerate(FRAME_RATE)
        writer.writeframes(samples)
    return output.getvalue()


def make_bmp(width: int, height: int, pixels: bytes, bits_per_pixel: int = 24) -> bytes:
    pixels_start = 54
    file_header = struct.pack("<2sIHHI", b"BM", pixels_start + len(pixels), 0, 0, pixels_start)
    info_header = struct.pack(
        "<IiiHHIIiiII", 40, width, height, 1, bits_per_pixel, 0, len(pixels), 0, 0, 0, 0
    )
    return file_header + info_header + pixels


def read_wav(data: bytes) -> tuple[int, int, int, bytes]:
    with wave.open(io.BytesIO(data)) as reader:
        return (
            reader.getnchannels(),
            reader.getsampwidth(),
            reader.getframerate(),
            reader.readframes(reader.getnframes()),
        )


class SimplifyWavTest(unittest.TestCase):
    def setUp(self):
        self.noise = random.Random(1).randbytes(4000)

    def test_result_is_valid_mono_8_bit_wav_with_same_duration(self):
        channels, width, rate, frames = read_wav(simplify(make_wav(self.noise)))

        self.assertEqual((channels, width, rate), (1, 1, FRAME_RATE))
        self.assertEqual(len(frames), len(self.noise) // 2)

    def test_samples_are_quantized_and_held(self):
        *_, frames = read_wav(simplify(make_wav(self.noise)))

        self.assertTrue(
            all(value % AUDIO_QUANTIZATION_STEP == 0 or value == 255 for value in frames)
        )
        for start in range(0, len(frames), HOLD_LENGTH):
            self.assertEqual(len(set(frames[start:start + HOLD_LENGTH])), 1)

    def test_silence_stays_silence(self):
        *_, frames = read_wav(simplify(make_wav(bytes(1000))))
        self.assertEqual(set(frames), {128})

    def test_stereo_keeps_first_channel_only(self):
        left_and_right = bytes((10, 200)) * 1000
        channels, _, _, frames = read_wav(simplify(make_wav(left_and_right, sample_width=1, channels=2)))

        self.assertEqual(channels, 1)
        self.assertEqual(
            set(frames), {round(10 / AUDIO_QUANTIZATION_STEP) * AUDIO_QUANTIZATION_STEP}
        )

    def test_24_bit_wav_is_rejected(self):
        with self.assertRaises(UnsupportedForLossyError):
            simplify(make_wav(bytes(3000), sample_width=3))


class SimplifyBmpTest(unittest.TestCase):
    WIDTH, HEIGHT = 10, 4
    ROW_SIZE = 32  # 10 pikseli po 3 bajty + 2 bajty wyrównania.

    def make_noise_bmp(self) -> bytes:
        generator = random.Random(2)
        pixels = b"".join(
            generator.randbytes(self.WIDTH * 3) + b"\x00\x00" for _ in range(self.HEIGHT)
        )
        return make_bmp(self.WIDTH, self.HEIGHT, pixels)

    def test_header_and_size_are_preserved(self):
        original = self.make_noise_bmp()
        simplified = simplify(original)

        self.assertEqual(len(simplified), len(original))
        self.assertEqual(simplified[:54], original[:54])

    def test_pixels_become_gray_and_row_padding_is_untouched(self):
        simplified = simplify(self.make_noise_bmp())

        for row in range(self.HEIGHT):
            start = 54 + row * self.ROW_SIZE
            pixels = simplified[start:start + self.WIDTH * 3]
            for blue, green, red in zip(pixels[0::3], pixels[1::3], pixels[2::3]):
                self.assertEqual(blue, green)
                self.assertEqual(green, red)
            self.assertEqual(simplified[start + self.WIDTH * 3:start + self.ROW_SIZE], b"\x00\x00")

    def test_brightness_uses_all_channels(self):
        magenta_pixel = bytes((255, 0, 255))  # Niebieski i czerwony, bez zieleni.
        simplified = simplify(make_bmp(4, 1, magenta_pixel * 4))

        gray = simplified[54]
        self.assertGreater(gray, 0)
        self.assertEqual(gray % IMAGE_QUANTIZATION_STEP, 0)

    def test_black_and_white_image_stays_identical(self):
        black_and_white = (bytes(3) * 4 + b"\xff" * 12) * 2
        original = make_bmp(8, 2, black_and_white)

        self.assertEqual(simplify(original), original)

    def test_palette_bmp_is_rejected(self):
        with self.assertRaises(UnsupportedForLossyError):
            simplify(make_bmp(4, 1, bytes(4), bits_per_pixel=8))

    def test_truncated_bmp_is_rejected(self):
        with self.assertRaises(UnsupportedForLossyError):
            simplify(self.make_noise_bmp()[:-5])


class SimplifyOtherFilesTest(unittest.TestCase):
    def test_other_files_are_rejected(self):
        cases = {
            "text": b"zwykly tekst",
            "jpg": b"\xff\xd8\xff\xe0" + bytes(50),
            "png": b"\x89PNG\r\n\x1a\n" + bytes(50),
            "empty": b"",
        }
        for name, data in cases.items():
            with self.subTest(name), self.assertRaises(UnsupportedForLossyError):
                simplify(data)


class LossyCompressionFileTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.source = self.directory / "noise.wav"
        self.source.write_bytes(make_wav(random.Random(3).randbytes(40_000)))

    def test_lossy_shrinks_noise_where_lossless_grows_it(self):
        output = self.directory / "out"

        lossless = compress_file(self.source, output, CompressionMode.LOSSLESS)
        lossy = compress_file(self.source, output, CompressionMode.LOSSY)

        self.assertLess(lossless.ratio, 1)
        self.assertGreater(lossy.ratio, 1)
        self.assertEqual(lossy.size_before, self.source.stat().st_size)
        self.assertEqual(lossy.archive.name, "noise.stratna.wav.rle")

    def test_restored_file_is_playable_and_differs_from_original(self):
        output = self.directory / "out"
        archive = compress_file(self.source, output, CompressionMode.LOSSY).archive

        restored = decompress_file(archive, output).restored

        self.assertEqual(restored.name, "noise.stratna.wav")
        self.assertNotEqual(restored.read_bytes(), self.source.read_bytes())
        self.assertEqual(read_wav(restored.read_bytes())[0:2], (1, 1))

    def test_benchmark_adds_lossy_row_only_for_supported_files(self):
        samples = self.directory / "samples"
        samples.mkdir()
        (samples / "noise.wav").write_bytes(self.source.read_bytes())
        (samples / "text.txt").write_bytes(b"zwykly tekst")

        results = run_benchmark(samples)

        rows = [
            (result.file_name, result.algorithm.value, result.mode, result.verdict)
            for result in results
        ]
        self.assertEqual(
            rows,
            [
                ("noise.wav", "RLE", CompressionMode.LOSSLESS, "zgodne"),
                ("noise.wav", "RLE", CompressionMode.LOSSY, "różne (stratna)"),
                ("noise.wav", "Huffman", CompressionMode.LOSSLESS, "zgodne"),
                ("noise.wav", "Huffman", CompressionMode.LOSSY, "różne (stratna)"),
                ("text.txt", "RLE", CompressionMode.LOSSLESS, "zgodne"),
                ("text.txt", "Huffman", CompressionMode.LOSSLESS, "zgodne"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
