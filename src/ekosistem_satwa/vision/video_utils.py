"""Ekstraksi frame dari video untuk analisis vision."""
from __future__ import annotations

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("ekosistem_satwa.vision.video")

MAX_VIDEO_BYTES = 50 * 1024 * 1024

try:
    import cv2  # type: ignore[import-untyped]

    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False
    cv2 = None  # type: ignore[assignment]


@dataclass
class ExtractedFrame:
    index: int
    timestamp_ms: float
    image_bytes: bytes
    mime_type: str = "image/jpeg"


def cv2_available() -> bool:
    return _CV2_AVAILABLE


def validate_video_bytes(data: bytes, max_bytes: int = MAX_VIDEO_BYTES) -> None:
    if not data:
        raise ValueError("Data video kosong")
    if len(data) > max_bytes:
        raise ValueError(f"Video terlalu besar (maks {max_bytes // (1024 * 1024)} MB)")


def extract_keyframes(
    video_bytes: bytes,
    *,
    max_frames: int = 5,
    mime_type: str | None = None,
) -> tuple[list[ExtractedFrame], float | None, int | None]:
    """Ambil frame merata dari video. Butuh opencv-python-headless."""
    validate_video_bytes(video_bytes)
    if not _CV2_AVAILABLE:
        raise RuntimeError(
            "Ekstraksi video membutuhkan opencv-python-headless. "
            "Alternatif: kirim frame individual sebagai video_frame via API."
        )

    suffix = _suffix_for_mime(mime_type)
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name

    frames: list[ExtractedFrame] = []
    duration_ms: float | None = None
    total_frames: int | None = None

    try:
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            raise ValueError("Tidak dapat membaca file video")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        fps = float(cap.get(cv2.CAP_PROP_FPS)) or 25.0
        if total_frames > 0:
            duration_ms = (total_frames / fps) * 1000.0

        if total_frames <= 0:
            # Fallback: baca frame demi frame sampai max_frames
            idx = 0
            while len(frames) < max_frames:
                ok, frame = cap.read()
                if not ok:
                    break
                ts = (idx / fps) * 1000.0
                frames.append(_encode_frame(frame, idx, ts))
                idx += 1
        else:
            step = max(1, total_frames // max_frames)
            indices = list(range(0, total_frames, step))[:max_frames]
            for i, frame_idx in enumerate(indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ok, frame = cap.read()
                if not ok:
                    continue
                ts = (frame_idx / fps) * 1000.0
                frames.append(_encode_frame(frame, i, ts))

        cap.release()
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if not frames:
        raise ValueError("Tidak ada frame yang dapat diekstrak dari video")

    return frames, duration_ms, total_frames


def _encode_frame(frame, index: int, timestamp_ms: float) -> ExtractedFrame:
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        raise ValueError(f"Gagal encode frame {index}")
    return ExtractedFrame(
        index=index,
        timestamp_ms=timestamp_ms,
        image_bytes=buf.tobytes(),
        mime_type="image/jpeg",
    )


def _suffix_for_mime(mime: str | None) -> str:
    mapping = {
        "video/mp4": ".mp4",
        "video/quicktime": ".mov",
        "video/webm": ".webm",
        "video/x-msvideo": ".avi",
    }
    return mapping.get(mime or "", ".mp4")
