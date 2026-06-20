"""Subpaket AI wrapping Sobatpaws.

Dua jalur yang saling melengkapi:
- single-shot suggestion : schemas.SuggestionRequest/Response + wrapper.LLMClient
  + prompts + safety (kontraindikasi obat per spesies).
- konsultasi multimodal  : intake mic/kamera/teks -> suggestion_engine ->
  learning_store, diorkestrasi oleh consultation.ConsultationService.

Semua komponen degradasi anggun tanpa kunci API (pakai model ML + grounding KB).
"""

from .schemas import (  # noqa: F401
    # single-shot
    SuggestionRequest,
    SuggestionResponse,
    DiseaseHypothesis,
    DiagnosticStep,
    TreatmentSuggestion,
    ProductSuggestion,
    DEFAULT_DISCLAIMER,
    # konsultasi multimodal
    ConsultationContext,
    ConsultationChannel,
    IntakeModality,
    IntakePayload,
    IntakeResult,
    MediaPayload,
    AISuggestion,
    DoctorInput,
    SuggestionFeedback,
)

__all__ = [
    "SuggestionRequest",
    "SuggestionResponse",
    "DiseaseHypothesis",
    "DiagnosticStep",
    "TreatmentSuggestion",
    "ProductSuggestion",
    "DEFAULT_DISCLAIMER",
    "ConsultationContext",
    "ConsultationChannel",
    "IntakeModality",
    "IntakePayload",
    "IntakeResult",
    "MediaPayload",
    "AISuggestion",
    "DoctorInput",
    "SuggestionFeedback",
]
