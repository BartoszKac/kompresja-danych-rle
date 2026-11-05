"""Model: porównanie oryginału i pliku po dekompresji."""

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VerificationResult:
    original_sha256: str
    restored_sha256: str

    @property
    def is_identical(self) -> bool:
        return self.original_sha256 == self.restored_sha256


def verify_files(original: Path, restored: Path) -> VerificationResult:
    if original.resolve() == restored.resolve():
        raise ValueError("Wybrano dwa razy ten sam plik, więc porównanie nic nie sprawdza.")
    return VerificationResult(sha256_of_file(original), sha256_of_file(restored))


def sha256_of_file(path: Path) -> str:
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()
