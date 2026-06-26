"""Utilitas preprocessing gambar untuk modul vision."""
from __future__ import annotations

import io
import logging

from .schemas import ImageMetadata

logger = logging.getLogger("ekosistem_satwa.vision.image")

MAX_DIMENSION = 2048
MAX_BYTES = 10 * 1024 * 1024

try:
    from PIL import Image, UnidentifiedImageError

    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False
    Image = None  # type: ignore[misc, assignment]
    UnidentifiedImageError = Exception  # type: ignore[misc, assignment]


def pil_available() -> bool:
    return _PIL_AVAILABLE


def validate_image_bytes(data: bytes, max_bytes: int = MAX_BYTES) -> None:
    if not data:
        raise ValueError("Data gambar kosong")
    if len(data) > max_bytes:
        raise ValueError(f"Gambar terlalu besar (maks {max_bytes // (1024 * 1024)} MB)")


def preprocess_image(
    data: bytes,
    mime_type: str | None = None,
    *,
    max_dimension: int = MAX_DIMENSION,
) -> tuple[bytes, str, ImageMetadata]:
    """Validasi, baca metadata, dan resize jika perlu. Kembalikan bytes siap LLM."""
    validate_image_bytes(data)
    if not _PIL_AVAILABLE:
        meta = ImageMetadata(width=0, height=0, format=None, mode=None, was_resized=False)
        return data, mime_type or "image/jpeg", meta

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except UnidentifiedImageError as exc:
        raise ValueError("Format gambar tidak dikenali") from exc

    width, height = img.size
    was_resized = False
    if max(width, height) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        was_resized = True

    out_mime = mime_type or _format_to_mime(img.format)
    buf = io.BytesIO()
    save_fmt = _mime_to_pil_format(out_mime)
    img.convert("RGB").save(buf, format=save_fmt, quality=90)
    out_bytes = buf.getvalue()

    meta = ImageMetadata(
        width=img.size[0],
        height=img.size[1],
        format=img.format,
        mode=str(img.mode),
        was_resized=was_resized,
    )
    return out_bytes, out_mime, meta


def _format_to_mime(fmt: str | None) -> str:
    mapping = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp", "GIF": "image/gif"}
    return mapping.get((fmt or "").upper(), "image/jpeg")


def _mime_to_pil_format(mime: str) -> str:
    mapping = {
        "image/jpeg": "JPEG",
        "image/png": "PNG",
        "image/webp": "WEBP",
        "image/gif": "GIF",
    }
    return mapping.get(mime, "JPEG")
