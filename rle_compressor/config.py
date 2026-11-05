"""Ścieżki katalogów roboczych programu."""

import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("RLE_DATA_DIR", "data"))
SAMPLES_DIR = DATA_DIR / "samples"
OUTPUT_DIR = DATA_DIR / "output"
