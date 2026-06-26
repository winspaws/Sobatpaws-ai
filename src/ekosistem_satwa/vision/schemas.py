"""Skema input/output modul vision — siap dikonsumsi mobile app & agent AI."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from ..ai.schemas import StructuredVisionOutput, VisionLesion


class VisionFocus(str, Enum):
    """Area fokus analisis — mobile app bisa pilih sesuai konteks UI."""

    general = "general"
    wound = "wound"
    dermatology = "dermatology"
    morphology = "morphology"


class VisionMediaType(str, Enum):
    image = "image"
    video = "video"
    video_frame = "video_frame"


class WoundAssessment(BaseModel):
    """Penilaian luka terstruktur dari tampilan visual."""

    present: bool = False
    wound_type: str | None = Field(
        None,
        description="laceration | puncture | abrasion | bite_wound | surgical | abscess_open | burn | ulcer",
    )
    size_estimate: str | None = Field(
        None, description="small | medium | large, atau estimasi cm"
    )
    depth: str | None = Field(
        None, description="superficial | partial_thickness | full_thickness | unknown"
    )
    bleeding: str | None = Field(None, description="none | minor | active")
    discharge: str | None = Field(
        None, description="none | serous | purulent | hemorrhagic | unknown"
    )
    healing_stage: str | None = Field(
        None, description="acute | subacute | chronic | granulating | unknown"
    )
    location: str | None = None
    description: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class AnimalFormAssessment(BaseModel):
    """Penilaian bentuk tubuh, postur, dan kondisi fisik hewan."""

    body_condition_score: float | None = Field(
        None, ge=1.0, le=9.0, description="estimasi skor kondisi tubuh 1-9"
    )
    posture: str | None = Field(None, description="normal | hunched | recumbent | limping | abnormal")
    gait_notes: str | None = None
    coat_condition: str | None = Field(
        None, description="normal | dull | matted | alopecia | ectoparasites_suspected"
    )
    visible_morphology: str | None = Field(
        None, description="deskripsi bentuk tubuh, proporsi, ukuran relatif"
    )
    sex_estimate: str | None = Field(None, description="male | female | unknown")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ImageMetadata(BaseModel):
    """Metadata teknis gambar setelah preprocessing."""

    width: int
    height: int
    format: str | None = None
    mode: str | None = None
    was_resized: bool = False


class FrameAnalysis(BaseModel):
    """Hasil analisis satu frame (untuk video)."""

    frame_index: int
    timestamp_ms: float | None = None
    species_detected: str | None = None
    lesions: list[VisionLesion] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    raw_description: str = ""
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class VisionAnalysisRequest(BaseModel):
    """Request analisis vision dari mobile app / agent (JSON + base64)."""

    base64_data: str = Field(..., description="Data gambar/frame ter-encode base64")
    mime_type: str | None = Field(default="image/jpeg")
    category_slug: str | None = Field(
        None, description="Spesies diketahui (dog, cat, ...) — meningkatkan akurasi"
    )
    breed_slug: str | None = None
    focus: VisionFocus = VisionFocus.general
    consultation_id: str | None = None
    external_media_id: str | None = Field(
        None, description="ID media dari app mobile untuk sync balik"
    )


class VideoAnalysisRequest(BaseModel):
    """Opsi analisis video."""

    category_slug: str | None = None
    focus: VisionFocus = VisionFocus.general
    max_frames: int = Field(default=5, ge=1, le=12)
    consultation_id: str | None = None
    external_media_id: str | None = None


class VisionAnalysisResult(BaseModel):
    """Output terpadu analisis vision — untuk mobile UI & agent AI."""

    media_type: VisionMediaType
    species_detected: str | None = None
    breed_hints: list[str] = Field(default_factory=list)
    age_estimate_min_years: float | None = None
    age_estimate_max_years: float | None = None
    age_confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    animal_form: AnimalFormAssessment | None = None
    wound: WoundAssessment | None = None
    lesions: list[VisionLesion] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    extracted_symptoms: list[str] = Field(
        default_factory=list, description="Gejala terdeteksi (istilah umum)"
    )
    kb_symptom_matches: list[str] = Field(
        default_factory=list, description="Gejala yang cocok ke name_id knowledge base"
    )
    raw_description: str = ""

    frames: list[FrameAnalysis] = Field(default_factory=list)
    frames_analyzed: int = 0
    frames_total: int | None = None
    duration_ms: float | None = None

    image_metadata: ImageMetadata | None = None
    processing_time_ms: float | None = None
    analysis_source: str = Field(
        default="llm_structured",
        description="llm_structured | llm_text | ensemble",
    )
    structured: StructuredVisionOutput | None = None
    external_media_id: str | None = None
    focus: VisionFocus = VisionFocus.general

    model_config = {"protected_namespaces": ()}

    def to_media_observation_dict(self) -> dict[str, Any]:
        """Serialisasi ringkas untuk IntakeProcessor / agent."""
        return {
            "species_detected": self.species_detected,
            "breed_hints": self.breed_hints,
            "lesions": [l.model_dump() for l in self.lesions],
            "red_flags": self.red_flags,
            "extracted_symptoms": self.extracted_symptoms,
            "kb_symptom_matches": self.kb_symptom_matches,
            "animal_form": self.animal_form.model_dump() if self.animal_form else None,
            "wound": self.wound.model_dump() if self.wound else None,
            "raw_description": self.raw_description,
            "frames_analyzed": self.frames_analyzed,
            "analysis_source": self.analysis_source,
        }


class VisionCapabilities(BaseModel):
    """Kemampuan modul vision — untuk discovery oleh mobile app."""

    version: str = "1.0.0"
    image_supported: bool = True
    video_supported: bool = False
    video_backend: str | None = None
    max_image_bytes: int = 10 * 1024 * 1024
    max_video_bytes: int = 50 * 1024 * 1024
    supported_image_mimes: list[str] = Field(
        default_factory=lambda: ["image/jpeg", "image/png", "image/webp", "image/gif"]
    )
    supported_video_mimes: list[str] = Field(
        default_factory=lambda: [
            "video/mp4",
            "video/quicktime",
            "video/webm",
            "video/x-msvideo",
        ]
    )
    focus_modes: list[str] = Field(default_factory=lambda: [f.value for f in VisionFocus])
    llm_vision_available: bool = False
    max_video_frames: int = 12
