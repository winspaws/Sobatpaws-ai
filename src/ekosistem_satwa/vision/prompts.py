"""Prompt klinis untuk analisis gambar & video hewan."""
from __future__ import annotations

from .schemas import VisionFocus

_BASE_FIELDS = """
Field JSON yang WAJIB ada:
- species_detected: salah satu dari [dog, cat, rabbit, hamster, poultry, fish, reptile, amphibian, ferret, guinea_pig] atau null
- breed_hints: list string kemiripan ras (maks 3)
- age_estimate_min_years, age_estimate_max_years: angka atau null
- age_confidence: float 0.0-1.0
- lesions: list object {location, type, severity (mild|moderate|severe), description, confidence}
- red_flags: list string (pale_mucosa, respiratory_distress, active_bleeding, seizures, trauma_parah, cyanosis, unconscious)
- extracted_symptoms: list string gejala terlihat
- raw_description: deskripsi natural lengkap Bahasa Indonesia untuk dokter
- animal_form: object {
    body_condition_score (1-9 atau null),
    posture, gait_notes, coat_condition, visible_morphology, sex_estimate, confidence
  }
- wound: object {
    present (bool),
    wound_type, size_estimate, depth, bleeding, discharge, healing_stage,
    location, description, confidence
  }
"""

_FOCUS_HINTS: dict[VisionFocus, str] = {
    VisionFocus.general: "Analisa menyeluruh: spesies, bentuk tubuh, kondisi kulit/bulu, dan lesi/luka yang terlihat.",
    VisionFocus.wound: (
        "FOKUS UTAMA: identifikasi dan karakterisasi LUKA — jenis, ukuran, kedalaman, "
        "perdarahan, sekret, lokasi anatomis, dan stadium penyembuhan."
    ),
    VisionFocus.dermatology: (
        "FOKUS UTAMA: temuan dermatologis — eritema, alopecia, papul, pustul, kerak, "
        "skala, ulser, bengkak, dan distribusi lesi."
    ),
    VisionFocus.morphology: (
        "FOKUS UTAMA: identifikasi spesies/ras, estimasi umur, postur, bentuk tubuh, "
        "kondisi bulu, dan morfologi yang terlihat."
    ),
}


def build_structured_vision_prompt(
    *,
    focus: VisionFocus = VisionFocus.general,
    context_species: str | None = None,
    context_breed: str | None = None,
) -> str:
    """Bangun prompt vision terstruktur sesuai fokus analisis."""
    parts = [
        "Anda adalah dokter hewan ahli dermatologi, bedah, dan morfologi hewan.",
        _FOCUS_HINTS[focus],
        "Output JSON VALID SAJA — tanpa markdown, tanpa penjelasan di luar JSON.",
        _BASE_FIELDS,
    ]
    if context_species:
        parts.insert(1, f"Spesies yang diketahui dari rekam medis: {context_species}.")
    if context_breed:
        parts.insert(2 if context_species else 1, f"Ras yang diketahui: {context_breed}.")
    parts.append("Jika tidak yakin, gunakan null atau array kosong. JANGAN mendiagnosa definitif.")
    return "\n".join(parts)
