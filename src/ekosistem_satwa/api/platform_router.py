"""API Smart Data Platform — surface machine-readable untuk AI agent."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..platform.doctor import run_doctor
from ..platform.manifest import PLATFORM_MANIFEST, PIPELINE_PRESETS, get_pipeline_steps, get_step
from ..platform.pipeline import run_preset, run_step, run_steps
from ..platform.registry import load_registry, refresh_registry
from .auth import require_admin

router = APIRouter(prefix="/api/platform", tags=["Smart Data Platform"])


class PipelineRunRequest(BaseModel):
    step: str | None = Field(default=None, description="satu langkah pipeline")
    steps: list[str] = Field(default_factory=list, description="beberapa langkah berurutan")
    preset: str | None = Field(default=None, description="preset: ml_ready, full_synthetic, ...")
    continue_on_error: bool = False


@router.get("/manifest")
def platform_manifest() -> dict:
    """Kontrak platform lengkap untuk AI agent (data tracks, pipeline, guidelines)."""
    return {
        **PLATFORM_MANIFEST,
        "pipeline_steps": get_pipeline_steps(),
        "endpoints": {
            "doctor": "/api/platform/doctor",
            "registry": "/api/platform/registry",
            "pipeline_list": "/api/platform/pipeline",
            "pipeline_run": "POST /api/platform/pipeline/run (admin)",
        },
    }


@router.get("/doctor")
def platform_doctor() -> dict:
    """Diagnostik kesehatan sistem — JSON terstruktur untuk agent."""
    return run_doctor()


@router.get("/registry")
def platform_registry(refresh: bool = False) -> dict:
    """Registry lineage data + model ML."""
    if refresh:
        return refresh_registry()
    reg = load_registry()
    return reg if reg else refresh_registry()


@router.get("/pipeline")
def pipeline_catalog() -> dict:
    """Daftar langkah & preset pipeline."""
    return {
        "steps": get_pipeline_steps(),
        "presets": PIPELINE_PRESETS,
    }


@router.post("/pipeline/run", dependencies=[Depends(require_admin)])
def pipeline_run(req: PipelineRunRequest) -> dict:
    """Jalankan langkah/preset pipeline (admin). Output JSON untuk agent."""
    if req.preset:
        return run_preset(req.preset, stop_on_error=not req.continue_on_error)
    if req.step:
        return run_step(req.step)
    if req.steps:
        return run_steps(req.steps, stop_on_error=not req.continue_on_error)
    raise HTTPException(400, "Berikan step, steps, atau preset.")


@router.get("/pipeline/{step_id}")
def pipeline_step_detail(step_id: str) -> dict:
    """Detail satu langkah pipeline."""
    step = get_step(step_id)
    if not step:
        raise HTTPException(404, f"Step '{step_id}' tidak ditemukan.")
    return step
