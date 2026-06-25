"""API analisis gambar & video — untuk mobile app dan agent AI."""
from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ..vision.analyzer import VisionService, get_vision_service
from ..vision.schemas import (
    VisionAnalysisRequest,
    VisionAnalysisResult,
    VisionCapabilities,
    VisionFocus,
)
from .auth import require_vet

router = APIRouter(prefix="/api/vision", tags=["Vision Analysis"])


class VideoAnalysisJsonRequest(BaseModel):
    base64_data: str
    mime_type: str | None = "video/mp4"
    category_slug: str | None = None
    focus: VisionFocus = VisionFocus.general
    max_frames: int = Field(default=5, ge=1, le=12)
    consultation_id: str | None = None
    external_media_id: str | None = None


def _vision() -> VisionService:
    return get_vision_service()


@router.get("/capabilities", response_model=VisionCapabilities)
def vision_capabilities() -> VisionCapabilities:
    """Discovery endpoint — mobile app cek dukungan gambar/video sebelum upload."""
    return _vision().capabilities()


@router.post("/analyze", response_model=VisionAnalysisResult, dependencies=[Depends(require_vet)])
def analyze_image_json(req: VisionAnalysisRequest) -> VisionAnalysisResult:
    """Analisis gambar dari JSON (base64). Cocok untuk mobile app & agent."""
    try:
        return _vision().analyze_image_base64(
            req.base64_data,
            mime_type=req.mime_type,
            category_slug=req.category_slug,
            breed_slug=req.breed_slug,
            focus=req.focus,
            consultation_id=req.consultation_id,
            external_media_id=req.external_media_id,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc


@router.post("/analyze/upload", response_model=VisionAnalysisResult, dependencies=[Depends(require_vet)])
async def analyze_image_upload(
    file: UploadFile = File(...),
    category_slug: str | None = Form(None),
    breed_slug: str | None = Form(None),
    focus: VisionFocus = Form(VisionFocus.general),
    consultation_id: str | None = Form(None),
    external_media_id: str | None = Form(None),
) -> VisionAnalysisResult:
    """Analisis gambar via multipart upload — praktis dari kamera mobile."""
    raw = await file.read()
    try:
        return _vision().analyze_image(
            raw,
            mime_type=file.content_type,
            category_slug=category_slug,
            breed_slug=breed_slug,
            focus=focus,
            consultation_id=consultation_id,
            external_media_id=external_media_id,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc


@router.post("/analyze/video", response_model=VisionAnalysisResult, dependencies=[Depends(require_vet)])
async def analyze_video_upload(
    file: UploadFile = File(...),
    category_slug: str | None = Form(None),
    focus: VisionFocus = Form(VisionFocus.general),
    max_frames: int = Form(5),
    consultation_id: str | None = Form(None),
    external_media_id: str | None = Form(None),
) -> VisionAnalysisResult:
    """Analisis video — ekstrak keyframe lalu analisa spesies, luka, dan lesi."""
    raw = await file.read()
    try:
        return _vision().analyze_video(
            raw,
            mime_type=file.content_type,
            category_slug=category_slug,
            focus=focus,
            max_frames=max_frames,
            consultation_id=consultation_id,
            external_media_id=external_media_id,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc


@router.post("/analyze/video/json", response_model=VisionAnalysisResult, dependencies=[Depends(require_vet)])
def analyze_video_json(req: VideoAnalysisJsonRequest) -> VisionAnalysisResult:
    """Analisis video dari base64 (untuk integrasi agent)."""
    try:
        raw = base64.b64decode(req.base64_data)
    except (ValueError, TypeError) as exc:
        raise HTTPException(400, "base64_data tidak valid") from exc
    try:
        return _vision().analyze_video(
            raw,
            mime_type=req.mime_type,
            category_slug=req.category_slug,
            focus=req.focus,
            max_frames=req.max_frames,
            consultation_id=req.consultation_id,
            external_media_id=req.external_media_id,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
