"""Zamiana liczb na tekst czytelny dla użytkownika."""

BYTES_IN_UNIT = 1024
LARGER_UNITS = ("KiB", "MiB", "GiB", "TiB")


def format_size(size_in_bytes: int) -> str:
    if size_in_bytes < BYTES_IN_UNIT:
        return f"{size_in_bytes} B"

    size = float(size_in_bytes)
    for unit in LARGER_UNITS:
        size /= BYTES_IN_UNIT
        if size < BYTES_IN_UNIT:
            break
    return f"{size:.2f} {unit}"


def describe_ratio(ratio: float) -> str:
    if ratio > 1:
        effect = "plik zmniejszony"
    elif ratio < 1:
        effect = "plik powiększony"
    else:
        effect = "rozmiar bez zmian"
    return f"{ratio:.3f} ({effect})"
