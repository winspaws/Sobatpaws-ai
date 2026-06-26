"""Layanan analisis gambar & video — inti modul vision Ekosistem Satwa."""
from __future__ import annotations

import base64
import logging
import time
from functools import lru_cache
from typing import Any

from ..ai.llm import LLMClient
from ..ai.schemas import StructuredVisionOutput, VisionLesion
from ..ai.symptom_extractor import SymptomExtractor
from ..data_loader import KnowledgeBase, load_knowledge_base
from .image_utils import preprocess_image
from .prompts import build_structured_vision_prompt
from .schemas import (
    AnimalFormAssessment,
    FrameAnalysis,
    VisionAnalysisResult,
    VisionCapabilities,
    VisionFocus,
    VisionMediaType,
    WoundAssessment,
)
from .video_utils import cv2_available, extract_keyframes

logger = logging.getLogger("ekosistem_satwa.vision.analyzer")


class VisionService:
    """Analisis klinis gambar & video untuk identifikasi hewan, luka, dan lesi."""

    def __init__(
        self,
        kb: KnowledgeBase | None = None,
        llm: LLMClient | None = None,
    ):
        self.kb = kb or load_knowledge_base()
        self.llm = llm or LLMClient()

    def capabilities(self) -> VisionCapabilities:
        return VisionCapabilities(
            video_supported=cv2_available(),
            video_backend="opencv" if cv2_available() else None,
            llm_vision_available=self.llm.available,
        )

    def analyze_image(
        self,
        image_bytes: bytes,
        *,
        mime_type: str | None = None,
        category_slug: str | None = None,
        breed_slug: str | None = None,
        focus: VisionFocus = VisionFocus.general,
        consultation_id: str | None = None,
        external_media_id: str | None = None,
    ) -> VisionAnalysisResult:
        start = time.time()
        prepared, out_mime, img_meta = preprocess_image(image_bytes, mime_type)

        structured = self._run_structured_vision(
            prepared,
            out_mime,
            focus=focus,
            category_slug=category_slug,
            breed_slug=breed_slug,
            consultation_id=consultation_id,
        )

        result = self._build_result(
            structured=structured,
            media_type=VisionMediaType.image,
            focus=focus,
            category_slug=category_slug,
            image_metadata=img_meta,
            processing_time_ms=(time.time() - start) * 1000,
            external_media_id=external_media_id,
        )
        return result

    def analyze_image_base64(
        self,
        b64: str,
        *,
        mime_type: str | None = None,
        category_slug: str | None = None,
        breed_slug: str | None = None,
        focus: VisionFocus = VisionFocus.general,
        consultation_id: str | None = None,
        external_media_id: str | None = None,
    ) -> VisionAnalysisResult:
        try:
            raw = base64.b64decode(b64)
        except (ValueError, TypeError) as exc:
            raise ValueError("base64_data tidak valid") from exc
        return self.analyze_image(
            raw,
            mime_type=mime_type,
            category_slug=category_slug,
            breed_slug=breed_slug,
            focus=focus,
            consultation_id=consultation_id,
            external_media_id=external_media_id,
        )

    def analyze_video(
        self,
        video_bytes: bytes,
        *,
        mime_type: str | None = None,
        category_slug: str | None = None,
        focus: VisionFocus = VisionFocus.general,
        max_frames: int = 5,
        consultation_id: str | None = None,
        external_media_id: str | None = None,
    ) -> VisionAnalysisResult:
        start = time.time()
        frames, duration_ms, total_frames = extract_keyframes(
            video_bytes, max_frames=max_frames, mime_type=mime_type
        )

        frame_results: list[FrameAnalysis] = []
        aggregated_lesions: list[VisionLesion] = []
        aggregated_red_flags: list[str] = []
        aggregated_symptoms: list[str] = []
        species_votes: dict[str, int] = {}
        descriptions: list[str] = []
        best_structured: dict[str, Any] | None = None
        best_conf = 0.0

        for fr in frames:
            structured = self._run_structured_vision(
                fr.image_bytes,
                fr.mime_type,
                focus=focus,
                category_slug=category_slug,
                consultation_id=consultation_id,
            )
            if not structured:
                continue

            species = structured.get("species_detected")
            if species:
                species_votes[str(species)] = species_votes.get(str(species), 0) + 1

            lesions = _parse_lesions(structured.get("lesions"))
            red_flags = structured.get("red_flags") or []
            symptoms = structured.get("extracted_symptoms") or []
            desc = structured.get("raw_description") or ""

            frame_conf = _structured_confidence(structured)
            frame_results.append(
                FrameAnalysis(
                    frame_index=fr.index,
                    timestamp_ms=fr.timestamp_ms,
                    species_detected=species,
                    lesions=lesions,
                    red_flags=red_flags,
                    raw_description=desc,
                    confidence=frame_conf,
                )
            )
            aggregated_lesions.extend(lesions)
            aggregated_red_flags.extend(red_flags)
            aggregated_symptoms.extend(symptoms)
            if desc:
                descriptions.append(desc)
            if frame_conf >= best_conf:
                best_conf = frame_conf
                best_structured = structured

        if not frame_results:
            raise ValueError("Analisis video gagal — tidak ada frame yang berhasil dianalisa")

        species_detected = max(species_votes, key=species_votes.get) if species_votes else None
        if best_structured and category_slug and not species_detected:
            species_detected = category_slug

        merged = dict(best_structured or {})
        merged["species_detected"] = species_detected or merged.get("species_detected")
        merged["lesions"] = _dedupe_lesions(aggregated_lesions)
        merged["red_flags"] = list(dict.fromkeys(aggregated_red_flags))
        merged["extracted_symptoms"] = list(dict.fromkeys(aggregated_symptoms))
        merged["raw_description"] = _merge_descriptions(descriptions)

        result = self._build_result(
            structured=merged,
            media_type=VisionMediaType.video,
            focus=focus,
            category_slug=category_slug,
            processing_time_ms=(time.time() - start) * 1000,
            external_media_id=external_media_id,
            frames=frame_results,
            frames_analyzed=len(frame_results),
            frames_total=total_frames,
            duration_ms=duration_ms,
        )
        return result

    def _run_structured_vision(
        self,
        image_bytes: bytes,
        mime_type: str,
        *,
        focus: VisionFocus,
        category_slug: str | None,
        breed_slug: str | None = None,
        consultation_id: str | None = None,
    ) -> dict[str, Any] | None:
        if not self.llm.available:
            logger.warning("LLM tidak tersedia — vision analysis dilewati")
            return None

        prompt = build_structured_vision_prompt(
            focus=focus,
            context_species=category_slug,
            context_breed=breed_slug,
        )

        result = self.llm.describe_image(
            image_bytes,
            mime_type,
            prompt=prompt,
            structured=True,
            consultation_id=consultation_id,
        )

        if isinstance(result, dict):
            return result

        if isinstance(result, str) and result.strip():
            return {
                "raw_description": result.strip(),
                "species_detected": category_slug,
                "breed_hints": [],
                "lesions": [],
                "red_flags": [],
                "extracted_symptoms": [],
            }
        return None

    def _build_result(
        self,
        *,
        structured: dict[str, Any] | None,
        media_type: VisionMediaType,
        focus: VisionFocus,
        category_slug: str | None,
        processing_time_ms: float,
        external_media_id: str | None = None,
        image_metadata=None,
        frames: list[FrameAnalysis] | None = None,
        frames_analyzed: int = 0,
        frames_total: int | None = None,
        duration_ms: float | None = None,
    ) -> VisionAnalysisResult:
        data = structured or {}
        species = data.get("species_detected") or category_slug
        lesions = _parse_lesions(data.get("lesions"))
        red_flags = list(data.get("red_flags") or [])
        extracted = list(data.get("extracted_symptoms") or [])
        raw_desc = data.get("raw_description") or _fallback_description(species, lesions)

        animal_form = _parse_animal_form(data.get("animal_form"))
        wound = _parse_wound(data.get("wound"), lesions)

        kb_matches = self._match_kb_symptoms(extracted, raw_desc, category_slug or species)

        structured_model = None
        try:
            structured_model = StructuredVisionOutput(
                species_detected=species,
                breed_hints=data.get("breed_hints") or [],
                age_estimate_min_years=data.get("age_estimate_min_years"),
                age_estimate_max_years=data.get("age_estimate_max_years"),
                age_confidence=float(data.get("age_confidence") or 0.5),
                lesions=lesions,
                red_flags=red_flags,
                extracted_symptoms=extracted,
                raw_description=raw_desc,
                processing_time_ms=processing_time_ms,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("StructuredVisionOutput parse skipped: %s", exc)

        source = "llm_structured" if structured and isinstance(structured, dict) else "llm_text"

        return VisionAnalysisResult(
            media_type=media_type,
            species_detected=species,
            breed_hints=data.get("breed_hints") or [],
            age_estimate_min_years=data.get("age_estimate_min_years"),
            age_estimate_max_years=data.get("age_estimate_max_years"),
            age_confidence=float(data.get("age_confidence") or 0.5),
            animal_form=animal_form,
            wound=wound,
            lesions=lesions,
            red_flags=red_flags,
            extracted_symptoms=extracted,
            kb_symptom_matches=kb_matches,
            raw_description=raw_desc,
            frames=frames or [],
            frames_analyzed=frames_analyzed or (1 if media_type == VisionMediaType.image else 0),
            frames_total=frames_total,
            duration_ms=duration_ms,
            image_metadata=image_metadata,
            processing_time_ms=processing_time_ms,
            analysis_source=source,
            structured=structured_model,
            external_media_id=external_media_id,
            focus=focus,
        )

    def _match_kb_symptoms(
        self,
        extracted: list[str],
        raw_desc: str,
        category_slug: str | None,
    ) -> list[str]:
        if not raw_desc and not extracted:
            return []
        extractor = SymptomExtractor(self.kb, category_slug)
        combined = raw_desc
        if extracted:
            combined = f"{combined} {' '.join(extracted)}".strip()
        matches = extractor.extract(combined)
        return [m.name_id for m in matches]


@lru_cache(maxsize=1)
def get_vision_service() -> VisionService:
    return VisionService()


def _parse_lesions(raw: Any) -> list[VisionLesion]:
    if not raw or not isinstance(raw, list):
        return []
    out: list[VisionLesion] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            out.append(
                VisionLesion(
                    location=str(item.get("location") or "unknown"),
                    type=str(item.get("type") or "lesion"),
                    severity=str(item.get("severity") or "mild"),
                    description=str(item.get("description") or ""),
                    confidence=float(item.get("confidence") or 0.7),
                )
            )
        except Exception:  # noqa: BLE001
            continue
    return out


def _parse_animal_form(raw: Any) -> AnimalFormAssessment | None:
    if not raw or not isinstance(raw, dict):
        return None
    try:
        return AnimalFormAssessment(
            body_condition_score=raw.get("body_condition_score"),
            posture=raw.get("posture"),
            gait_notes=raw.get("gait_notes"),
            coat_condition=raw.get("coat_condition"),
            visible_morphology=raw.get("visible_morphology"),
            sex_estimate=raw.get("sex_estimate"),
            confidence=float(raw.get("confidence") or 0.5),
        )
    except Exception:  # noqa: BLE001
        return None


def _parse_wound(raw: Any, lesions: list[VisionLesion]) -> WoundAssessment | None:
    if raw and isinstance(raw, dict):
        try:
            return WoundAssessment(
                present=bool(raw.get("present")),
                wound_type=raw.get("wound_type"),
                size_estimate=raw.get("size_estimate"),
                depth=raw.get("depth"),
                bleeding=raw.get("bleeding"),
                discharge=raw.get("discharge"),
                healing_stage=raw.get("healing_stage"),
                location=raw.get("location"),
                description=raw.get("description"),
                confidence=float(raw.get("confidence") or 0.5),
            )
        except Exception:  # noqa: BLE001
            pass

    wound_lesions = [
        l for l in lesions
        if any(k in l.type.lower() for k in ("laceration", "ulcer", "wound", "bite", "abscess"))
    ]
    if not wound_lesions:
        return WoundAssessment(present=False, confidence=0.3)

    primary = wound_lesions[0]
    return WoundAssessment(
        present=True,
        wound_type=primary.type,
        location=primary.location,
        description=primary.description,
        confidence=primary.confidence,
    )


def _structured_confidence(data: dict[str, Any]) -> float:
    confs = [float(l.get("confidence", 0.7)) for l in (data.get("lesions") or []) if isinstance(l, dict)]
    if confs:
        return sum(confs) / len(confs)
    return 0.6 if data.get("raw_description") else 0.3


def _dedupe_lesions(lesions: list[VisionLesion]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    out: list[dict] = []
    for l in lesions:
        key = (l.location, l.type)
        if key in seen:
            continue
        seen.add(key)
        out.append(l.model_dump())
    return out


def _merge_descriptions(parts: list[str]) -> str:
    unique = list(dict.fromkeys(p.strip() for p in parts if p.strip()))
    if not unique:
        return ""
    if len(unique) == 1:
        return unique[0]
    return f"Analisis {len(unique)} frame video: " + " | ".join(unique[:3])


def _fallback_description(species: str | None, lesions: list[VisionLesion]) -> str:
    sp = species or "hewan"
    if not lesions:
        return f"Gambar menunjukkan {sp}."
    descs = [f"{l.type} ({l.severity}) di {l.location}" for l in lesions[:3]]
    return f"Gambar menunjukkan {sp}: " + "; ".join(descs) + "."
