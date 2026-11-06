"""Generates image / non-image files for upload tests (Pillow is already a project dependency)."""
import os
from pathlib import Path

from PIL import Image


def make_image(path: Path, fmt: str = "PNG", size: tuple[int, int] = (64, 48), color=(200, 80, 40)) -> Path:
    Image.new("RGB", size, color).save(path, format=fmt)
    return path


def make_large_png(path: Path, min_bytes: int = 3_300_000) -> Path:
    """Random noise does not compress, so a ~1200x1200 PNG is safely above 3 MB."""
    side = 1200
    Image.frombytes("RGB", (side, side), os.urandom(side * side * 3)).save(path, format="PNG")
    assert path.stat().st_size > min_bytes
    return path
