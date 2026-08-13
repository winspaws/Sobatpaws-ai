"""Ringkasan klinis dari KB+ML tanpa LLM — hemat token, tetap efektif."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("ekosistem_satwa.ai.kb_brief")

SPECIES_SLUG = {
    "dog": "dog", "anjing": "dog", "canine": "dog",
    "cat": "cat", "kucing": "cat", "feline": "cat",
    "rabbit": "rabbit", "kelinci": "rabbit",
    "hamster": "hamster",
    "poultry": "poultry", "ayam": "poultry", "unggas": "poultry",
    "fish": "fish", "ikan": "fish",
    "reptile": "reptile", "reptil": "reptile",
    "ferret": "ferret",
    "guinea_pig": "guinea_pig", "marmut": "guinea_pig",
}


def infer_category_slug(pet_context: dict | None, text: str = "") -> str:
    src = pet_context or {}
    raw = str(src.get("species") or src.get("category_slug") or "").lower().strip()
    if raw in SPECIES_SLUG:
        return SPECIES_SLUG[raw]
    blob = f"{raw} {text}".lower()
    for key, slug in SPECIES_SLUG.items():
        if key in blob:
            return slug
    return "dog"


def build_symptom_brief(
    text: str,
    *,
    pet_name: str = "Si Kecil",
    pet_context: dict | None = None,
    category_slug: str | None = None,
    top_k: int = 3,
) -> dict[str, Any] | None:
    """Jika keluhan mengandung gejala KB, kembalikan respons ter-ground tanpa LLM."""
    try:
        from ..data_loader import load_knowledge_base
        from .schemas import ConsultationContext, IntakeResult
        from .symptom_extractor import SymptomExtractor
        from .suggestion_engine import SuggestionEngine
    except Exception as exc:  # noqa: BLE001
        logger.debug("kb_brief import failed: %s", exc)
        return None

    slug = category_slug or infer_category_slug(pet_context, text)
    try:
        kb = load_knowledge_base()
        extractor = SymptomExtractor(kb, category_slug=slug)
        symptoms = extractor.extract(text or "")
        if len(symptoms) < 1:
            return None
        intake = IntakeResult(complaint_text=text or "", symptoms=symptoms)
        breed = None
        if pet_context:
            breed = pet_context.get("breed_slug") or pet_context.get("breed")
        ctx = ConsultationContext(
            category_slug=slug,
            breed_slug=str(breed) if breed else None,
            age_years=pet_context.get("age_years") if pet_context else None,
            weight_kg=pet_context.get("weight_kg") if pet_context else None,
        )
        engine = SuggestionEngine(kb)
        suggestion = engine.suggest(ctx, intake, top_k=top_k, use_llm=False)
    except Exception as exc:  # noqa: BLE001
        logger.debug("kb_brief failed: %s", exc)
        return None

    diseases = suggestion.suggested_diseases[:top_k]
    if not diseases:
        return None
    lines = []
    for i, d in enumerate(diseases, 1):
        flag = " (perlu perhatian segera)" if d.is_emergency else ""
        conf = int(round((d.confidence or 0) * 100))
        lines.append(f"{i}. {d.name_id or d.disease_slug} (~{conf}%){flag}")
    symptom_names = [s.name_id or s.name for s in symptoms[:6] if s.name_id or s.name]
    red = suggestion.red_flags[:3] if suggestion.red_flags else []
    extra = ""
    if red:
        extra = "\nRed flag: " + "; ".join(red)
    text_out = (
        f"Berdasarkan keluhan {pet_name}, gejala terdeteksi: "
        f"{', '.join(symptom_names) or 'beberapa gejala'}.\n\n"
        f"Kemungkinan (bukan diagnosis):\n" + "\n".join(lines)
        + extra
        + "\n\nIni pendukung keputusan. Diagnosa akhir oleh dokter hewan."
    )
    return {
        "text": text_out,
        "suggestions": [
            "Konsultasi dokter",
            "Tambah detail gejala",
            "Unggah foto jika ada",
        ],
        "cta": [
            {"type": "teleconsult", "label": "💬 Konsultasi Dokter", "endpoint": "/api/v1/teleconsult"},
        ],
        "disclaimer": "Prediksi ML+KB bersifat probabilistik, bukan diagnosis.",
        "token_mode": "kb_ml",
        "token_reason": "symptom_grounded",
        "kb_diseases": [
            {"slug": d.disease_slug, "name": d.name_id, "confidence": d.confidence}
            for d in diseases
        ],
        "symptoms": symptom_names,
    }
