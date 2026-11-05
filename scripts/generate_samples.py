"""Tworzy pliki testowe różnego rodzaju w katalogu data/samples (wymaga ffmpeg).

Część plików sprzyja RLE (długie serie bajtów), a część celowo nie, aby pokazać różnicę.
"""

import random
import string
import subprocess

from rle_compressor.config import SAMPLES_DIR

TEXT_SIZE = 1024 * 1024
RANDOM_SEED = 2026
RUN_LENGTH = 200
PHRASE = "Kompresja bezstratna odtwarza dane co do bitu. "

TABLE_ROWS = 6000
TABLE_COLUMN_WIDTH = 50
BINARY_BLOCK_COUNT = 256
BINARY_BLOCK_SIZE = 4096
BINARY_RECORD_SIZE = 32

IMAGE_SIZE = "1280x720"
SCAN_LINE_COUNT = 30
SCAN_LINE_SPACING = 22
SCAN_MARGIN = 100
SCAN_LINE_WIDTH = 1080
SCAN_LINE_HEIGHT = 8

VIDEO_SOURCE = f"testsrc2=size={IMAGE_SIZE}"
NOISY_PHOTO_SOURCE = f"mandelbrot=size={IMAGE_SIZE},noise=alls=25:allf=t"
SMOOTH_PHOTO_SOURCE = f"mandelbrot=size={IMAGE_SIZE}"

# Sam sinus byłby nierealistyczny: enkoder MP3 dopełniałby ramki zerami, co sztucznie pomaga RLE.
AUDIO_SOURCE = (
    "anoisesrc=color=pink:amplitude=0.3:duration=30:sample_rate=44100:seed=2026[noise];"
    "sine=frequency=220:duration=30:sample_rate=44100[tone];"
    "[noise][tone]amix=inputs=2"
)
# Co 4 sekundy pół sekundy tonu, a poza tym cisza.
AUDIO_WITH_SILENCE_SOURCE = (
    "aevalsrc='if(lt(mod(t,4),0.5),0.5*sin(440*2*PI*t),0)':duration=30:sample_rate=44100"
)


def main() -> None:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    write_text_samples()
    write_binary_sample()
    write_image_samples()
    write_audio_samples()
    print(f"Pliki testowe zapisano w {SAMPLES_DIR}")


def write_text_samples() -> None:
    generator = random.Random(RANDOM_SEED)
    random_text = "".join(generator.choices(string.ascii_letters + string.digits, k=TEXT_SIZE))
    write_text("tekst_losowy.txt", random_text)

    letters = "".join(letter * RUN_LENGTH for letter in string.ascii_uppercase)
    write_text("tekst_serie_znakow.txt", letters * (TEXT_SIZE // len(letters)))

    write_text("tekst_powtarzana_fraza.txt", PHRASE * (TEXT_SIZE // len(PHRASE)))

    write_text("tekst_tabela_wyrownana.txt", aligned_table(generator))


def aligned_table(generator: random.Random) -> str:
    separator = "-" * (3 * TABLE_COLUMN_WIDTH) + "\n"
    rows = [separator]
    for row_number in range(TABLE_ROWS):
        rows.append(
            f"{row_number:<{TABLE_COLUMN_WIDTH}}"
            f"{generator.randint(0, 99):<{TABLE_COLUMN_WIDTH}}"
            f"{generator.randint(0, 99):>{TABLE_COLUMN_WIDTH}}\n"
        )
        rows.append(separator)
    return "".join(rows)


def write_text(file_name: str, text: str) -> None:
    (SAMPLES_DIR / file_name).write_text(text, encoding="ascii")


def write_binary_sample() -> None:
    """Dane w stylu obrazu dysku: krótkie rekordy i długie obszary zer."""
    generator = random.Random(RANDOM_SEED)
    padding = bytes(BINARY_BLOCK_SIZE - BINARY_RECORD_SIZE)
    blocks = [generator.randbytes(BINARY_RECORD_SIZE) + padding for _ in range(BINARY_BLOCK_COUNT)]
    (SAMPLES_DIR / "dane_z_zerami.bin").write_bytes(b"".join(blocks))


def write_image_samples() -> None:
    run_ffmpeg(VIDEO_SOURCE, "-frames:v", "1", "obraz.png")
    run_ffmpeg(NOISY_PHOTO_SOURCE, "-frames:v", "1", "-q:v", "3", "zdjecie.jpg")
    run_ffmpeg(scanned_page_source(), "-frames:v", "1", "-pix_fmt", "bgr24", "skan_dokumentu.bmp")
    run_ffmpeg(SMOOTH_PHOTO_SOURCE, "-frames:v", "1", "-pix_fmt", "bgr24", "obraz_kolorowy.bmp")


def scanned_page_source() -> str:
    """Biała strona z czarnymi paskami w miejscu wierszy tekstu."""
    lines = ",".join(
        f"drawbox=x={SCAN_MARGIN}:y={SCAN_MARGIN + index * SCAN_LINE_SPACING}"
        f":w={SCAN_LINE_WIDTH}:h={SCAN_LINE_HEIGHT}:color=black:t=fill"
        for index in range(SCAN_LINE_COUNT)
    )
    return f"color=white:size={IMAGE_SIZE},{lines}"


def write_audio_samples() -> None:
    run_ffmpeg(AUDIO_SOURCE, "-b:a", "192k", "muzyka.mp3")
    run_ffmpeg(AUDIO_SOURCE, "dzwiek.wav")
    run_ffmpeg(AUDIO_WITH_SILENCE_SOURCE, "dzwiek_z_cisza.wav")


def run_ffmpeg(source: str, *options: str) -> None:
    *encoder_options, file_name = options
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", source,
            *encoder_options,
            str(SAMPLES_DIR / file_name),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
