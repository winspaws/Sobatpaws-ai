"""Intake multimodal: tangkap & normalisasi input dari tools aplikasi dokter.

Sumber input saat user mulai konsultasi (chat / video):
- text        : ketikan keluhan
- audio       : tangkapan mikrofon -> transkrip (LLMClient.transcribe / klien)
- image       : tangkapan kamera / foto -> deskripsi temuan (LLMClient.describe_image)
- video_frame : frame dari sesi video -> sama seperti image

Output: IntakeResult berisi keluhan ter-normalisasi + observasi media + daftar
gejala terstruktur (siap untuk model ML & grounding).
"""
from __future__ import annotations

import base64
import logging

from ..data_loader import KnowledgeBase
from ..vision.analyzer import VisionService, get_vision_service
from ..vision.schemas import VisionFocus
from .llm import LLMClient
from .schemas import (
    ExtractedSymptom,
    IntakeModality,
    IntakePayload,
    IntakeResult,
    MediaObservation,
    MediaPayload,
    StructuredVisionOutput,
)
from .symptom_extractor import SymptomExtractor

logger = logging.getLogger("ekosistem_satwa.ai.intake")


class IntakeProcessor:
    """Memproses IntakePayload menjadi IntakeResult yang siap dianalisa."""

    def __init__(
        self,
        kb: KnowledgeBase,
        category_slug: str | None = None,
        llm: LLMClient | None = None,
        vision: VisionService | None = None,
    ):
        self.kb = kb
        self.category_slug = category_slug
        self.llm = llm or LLMClient()
        self.vision = vision or get_vision_service()
        self.extractor = SymptomExtractor(kb, category_slug)

    def process(self, payload: IntakePayload) -> IntakeResult:
        observations: list[MediaObservation] = []
        text_parts: list[str] = []

        if payload.text:
            text_parts.append(payload.text.strip())

        for media in payload.media:
            obs = self._process_media(media)
            if obs:
                observations.append(obs)
                if obs.text:
                    text_parts.append(obs.text.strip())

        complaint = " ".join(p for p in text_parts if p).strip()
        symptoms = self._extract_symptoms(complaint, observations)

        return IntakeResult(
            complaint_text=complaint,
            observations=observations,
            symptoms=symptoms,
            channel=payload.channel,
        )

    # ---- pemrosesan per-media --------------------------------------------
    def _process_media(self, media: MediaPayload) -> MediaObservation | None:
        # Klien sudah melakukan transkripsi/anotasi sendiri.
        if media.pretranscribed_text:
            return MediaObservation(
                modality=media.modality,
                text=media.pretranscribed_text.strip(),
                source="client",
                confidence=None,
            )

        raw = self._decode(media)
        if raw is None:
            logger.info("Media tanpa data biner di-skip (modality=%s)", media.modality)
            return None

        if media.modality == IntakeModality.audio:
            text = self.llm.transcribe(raw, media.mime_type)
            if text:
                return MediaObservation(
                    modality=media.modality, text=text, source="speech_to_text"
                )
            return None

        if media.modality in (IntakeModality.image, IntakeModality.video_frame):
            focus = VisionFocus.wound if media.modality == IntakeModality.video_frame else VisionFocus.general
            try:
                result = self.vision.analyze_image(
                    raw,
                    mime_type=media.mime_type,
                    category_slug=self.category_slug,
                    focus=focus,
                )
                structured_result = result.to_media_observation_dict()
                raw_desc = result.raw_description
                return MediaObservation(
                    modality=media.modality,
                    text=raw_desc,
                    source="vision_module",
                    confidence=None,
                    structured=structured_result,
                    structured_model="VisionAnalysisResult",
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Vision module failed, falling back to LLM: %s", exc)

            # Fallback: direct LLM vision (legacy path)
            structured_result = None
            try:
                structured_result = self.llm.describe_image(
                    raw, media.mime_type, structured=True
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Structured vision failed, falling back to text-only: %s", exc
                )

            # Case 1: Got valid dict (structured output)
            if isinstance(structured_result, dict):
                # Use raw_description for backward compatibility with symptom_extractor
                raw_desc = structured_result.get("raw_description", "")
                if not raw_desc:
                    # Fallback: generate description from structured data
                    species = structured_result.get("species_detected") or "hewan"
                    raw_desc = f"Gambar menunjukkan {species}."
                    lesions = structured_result.get("lesions", [])
                    if lesions:
                        lesion_descs = []
                        for lesion in lesions[:3]:
                            loc = lesion.get("location", "lokasi tidak jelas")
                            typ = lesion.get("type", "lesi")
                            sev = lesion.get("severity", "")
                            desc = lesion.get("description", "")
                            lesion_descs.append(
                                f"{typ} {sev} di {loc}: {desc}" if sev
                                else f"{typ} di {loc}: {desc}"
                            )
                        raw_desc += " " + "; ".join(lesion_descs) + "."

                return MediaObservation(
                    modality=media.modality,
                    text=raw_desc,
                    source="vision_structured",
                    confidence=None,
                    structured=structured_result,
                    structured_model="StructuredVisionOutput",
                )

            # Case 2: Structured returned string (fallback - JSON parsing failed)
            if isinstance(structured_result, str) and structured_result.strip():
                logger.info(
                    "Structured vision returned text (JSON parse failed), using as description"
                )
                return MediaObservation(
                    modality=media.modality,
                    text=structured_result.strip(),
                    source="vision",  # Mark as regular since structured failed
                    confidence=None,
                )

            # Case 3: Structured failed entirely or returned None - fallback to text-only
            logger.info("Falling back to text-only vision description")
            desc = self.llm.describe_image(raw, media.mime_type, structured=False)
            if desc:
                return MediaObservation(
                    modality=media.modality, text=desc, source="vision"
                )
            return None

        return None

    @staticmethod
    def _decode(media: MediaPayload) -> bytes | None:
        if not media.base64_data:
            return None
        try:
            return base64.b64decode(media.base64_data)
        except (ValueError, TypeError):
            logger.warning("base64 tidak valid untuk modality=%s", media.modality)
            return None

    # ---- ekstraksi gejala -------------------------------------------------
    def _extract_symptoms(
        self, complaint: str, observations: list[MediaObservation]
    ) -> list[ExtractedSymptom]:
        combined = complaint
        # gabungkan deskripsi vision untuk peluang menangkap gejala visual
        vision_text = " ".join(
            o.text for o in observations
            if o.modality in (IntakeModality.image, IntakeModality.video_frame)
        )
        if vision_text:
            combined = f"{combined} {vision_text}".strip()

        if not combined:
            return []
        return self.extractor.extract(combined)
