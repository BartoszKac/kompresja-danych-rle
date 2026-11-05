"""Etap stratny: upraszcza dźwięk WAV i obraz BMP tak, aby powstały długie serie bajtów.

Właściwą kompresję nadal wykonuje RLE. Tutaj trwale usuwamy szczegóły, a wynik
pozostaje poprawnym plikiem WAV lub BMP, który można odtworzyć albo otworzyć.

Dwa zabiegi:
- kwantyzacja: wartości zaokrąglamy do wielokrotności kroku (dźwięk znosi mniejszy krok niż obraz),
- podtrzymanie: każdą HOLD_LENGTH-tą wartość powtarzamy w miejsce kolejnych.

Inne pliki są odrzucane. W tekście zmieniłoby to treść, a bajty JPG, PNG i MP3 są już
zakodowane, więc ich zmiana uszkodziłaby plik.
"""

import io
import struct
import wave

AUDIO_QUANTIZATION_STEP = 4
IMAGE_QUANTIZATION_STEP = 16
HOLD_LENGTH = 4
MAX_BYTE = 255

BYTES_PER_PIXEL = 3
BITS_PER_PIXEL_24 = 24
BMP_UNCOMPRESSED = 0
BMP_ROW_ALIGNMENT = 4
BMP_HEADER = struct.Struct("<2s8xI4xiiHHI")
SIGN_BIT = 0x80

# Udział kanałów w jasności piksela, w 1/256: oko najsilniej reaguje na zieleń.
BLUE_WEIGHT, GREEN_WEIGHT, RED_WEIGHT = 29, 150, 77
WEIGHT_SHIFT = 8


def _quantization_table(step: int) -> bytes:
    return bytes(min(round(value / step) * step, MAX_BYTE) for value in range(256))


_AUDIO_QUANTIZATION = _quantization_table(AUDIO_QUANTIZATION_STEP)
_IMAGE_QUANTIZATION = _quantization_table(IMAGE_QUANTIZATION_STEP)


class UnsupportedForLossyError(ValueError):
    """Tego pliku nie można skompresować stratnie."""

    def __init__(self) -> None:
        super().__init__(
            "tryb stratny obsługuje tylko dźwięk WAV (8 lub 16 bitów) i obraz BMP (24 bity). "
            "Dla pozostałych plików wybierz tryb bezstratny."
        )


def simplify(data: bytes) -> bytes:
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return _simplify_wav(data)
    if data[:2] == b"BM":
        return _simplify_bmp(data)
    raise UnsupportedForLossyError()


def _simplify_wav(data: bytes) -> bytes:
    """Zapisuje pierwszy kanał jako uproszczony dźwięk mono, 8 bitów."""
    try:
        with wave.open(io.BytesIO(data)) as reader:
            channels = reader.getnchannels()
            sample_width = reader.getsampwidth()
            frame_rate = reader.getframerate()
            frames = reader.readframes(reader.getnframes())
    except (wave.Error, EOFError) as error:
        raise UnsupportedForLossyError() from error

    samples = _first_channel_as_8_bit(frames, channels, sample_width)
    simplified = _hold_values(samples).translate(_AUDIO_QUANTIZATION)

    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(1)
        writer.setframerate(frame_rate)
        writer.writeframes(simplified)
    return output.getvalue()


def _first_channel_as_8_bit(frames: bytes, channels: int, sample_width: int) -> bytes:
    frame_size = channels * sample_width
    if sample_width == 1:
        return frames[::frame_size]
    if sample_width == 2:
        # WAV 16-bit ma próbki ze znakiem, a WAV 8-bit bez znaku: bierzemy starszy bajt i przesuwamy zakres.
        high_bytes = frames[1::frame_size]
        return bytes(value ^ SIGN_BIT for value in high_bytes)
    raise UnsupportedForLossyError()


def _simplify_bmp(data: bytes) -> bytes:
    """Zamienia kolory pikseli na uproszczone odcienie szarości; rozmiar obrazu się nie zmienia."""
    if len(data) < BMP_HEADER.size:
        raise UnsupportedForLossyError()

    _, pixels_start, width, height, _, bits_per_pixel, compression = BMP_HEADER.unpack_from(data)
    row_size = (width * BYTES_PER_PIXEL + BMP_ROW_ALIGNMENT - 1) // BMP_ROW_ALIGNMENT * BMP_ROW_ALIGNMENT
    pixels_end = pixels_start + row_size * abs(height)
    if bits_per_pixel != BITS_PER_PIXEL_24 or compression != BMP_UNCOMPRESSED or len(data) < pixels_end:
        raise UnsupportedForLossyError()

    simplified = bytearray(data)
    for row_start in range(pixels_start, pixels_end, row_size):
        row_end = row_start + width * BYTES_PER_PIXEL
        brightness = _row_brightness(data[row_start:row_end])
        gray = _hold_values(brightness).translate(_IMAGE_QUANTIZATION)
        for channel in range(BYTES_PER_PIXEL):
            simplified[row_start + channel:row_end:BYTES_PER_PIXEL] = gray
    return bytes(simplified)


def _row_brightness(row: bytes) -> bytes:
    """W pliku BMP kolejność kanałów to niebieski, zielony, czerwony."""
    return bytes(
        (BLUE_WEIGHT * blue + GREEN_WEIGHT * green + RED_WEIGHT * red) >> WEIGHT_SHIFT
        for blue, green, red in zip(row[0::3], row[1::3], row[2::3])
    )


def _hold_values(values: bytes) -> bytes:
    held = bytearray(values)
    for start in range(0, len(values), HOLD_LENGTH):
        block_length = len(values[start:start + HOLD_LENGTH])
        held[start:start + block_length] = values[start:start + 1] * block_length
    return bytes(held)
