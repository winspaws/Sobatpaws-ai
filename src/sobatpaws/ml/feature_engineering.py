"""Feature engineering & feature store helper untuk Sobatpaws.

Mendefinisikan fitur yang dipakai model risiko/diagnosa, dan utilitas untuk
membangun vektor fitur dari objek pet + gejala.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..data_loader import KnowledgeBase

RISK_ORDINAL = {
    "very_low": 0, "low": 1, "moderate": 2, "high": 3, "very_high": 4, None: 2,
}
SIZE_ORDINAL = {"toy": 0, "small": 1, "medium": 2, "large": 3, "giant": 4, None: 2}


@dataclass
class FeatureDefinition:
    """Definisi 1 fitur untuk feature store (selaras tabel feature_definitions)."""

    key: str
    name: str
    data_type: str  # numeric | categorical | boolean | multihot
    source_table: str
    transform: str = ""
    description: str = ""


# Registry fitur inti (bisa di-seed ke tabel feature_definitions)
FEATURE_REGISTRY: list[FeatureDefinition] = [
    FeatureDefinition("age_years", "Umur (tahun)", "numeric", "pets",
                      "now - birth_date", "Umur memengaruhi banyak risiko penyakit"),
    FeatureDefinition("weight_kg", "Berat badan (kg)", "numeric", "pets", "",
                      "Indikator kondisi tubuh & dosis"),
    FeatureDefinition("sex", "Jenis kelamin", "categorical", "pets", "one-hot", ""),
    FeatureDefinition("is_neutered", "Steril/kastrasi", "boolean", "pets", "", ""),
    FeatureDefinition("size_class_ord", "Kelas ukuran (ordinal)", "numeric",
                      "breeds", "ordinal(size_class)", ""),
    FeatureDefinition("breed_risk_score", "Skor risiko ras", "numeric",
                      "breed_disease_susceptibility",
                      "agg(prevalence * risk)", "Beban risiko genetik ras"),
    FeatureDefinition("symptom_multihot", "Vektor gejala", "multihot",
                      "case_symptoms", "multi-hot encode", "Fitur utama diagnosa"),
    FeatureDefinition("vital_temp_c", "Suhu tubuh (C)", "numeric",
                      "clinical_cases", "", ""),
    FeatureDefinition("vital_hr", "Detak jantung", "numeric", "clinical_cases", "", ""),
    FeatureDefinition("vital_rr", "Laju napas", "numeric", "clinical_cases", "", ""),
]


def breed_risk_profile(kb: KnowledgeBase, breed_slug: str) -> dict[str, float]:
    """Skor risiko penyakit untuk satu ras: {disease_slug: skor 0..1}.

    Skor = (ordinal risk / 4) digabung dengan prevalence_pct bila ada.
    """
    profile: dict[str, float] = {}
    for d in kb.diseases:
        for s in d.get("breed_susceptibility", []):
            if s.get("breed_slug") == breed_slug:
                risk_ord = RISK_ORDINAL.get(s.get("risk"), 2) / 4.0
                prev = s.get("prevalence_pct")
                prev_norm = (prev / 100.0) if isinstance(prev, (int, float)) else None
                score = max(risk_ord, prev_norm) if prev_norm is not None else risk_ord
                profile[d["slug"]] = round(score, 3)
    return dict(sorted(profile.items(), key=lambda kv: kv[1], reverse=True))


def build_pet_feature_vector(
    kb: KnowledgeBase,
    *,
    age_years: float | None,
    weight_kg: float | None,
    sex: str | None,
    is_neutered: bool | None,
    breed_slug: str | None,
    symptoms: list[str],
    symptom_vocab: list[str],
    vitals: dict | None = None,
) -> np.ndarray:
    """Bangun vektor fitur numerik untuk satu pet (dipakai model risiko)."""
    vitals = vitals or {}
    breed = kb.breed_by_slug(breed_slug) if breed_slug else None
    size_ord = SIZE_ORDINAL.get(breed.get("size_class") if breed else None, 2)
    risk_profile = breed_risk_profile(kb, breed_slug) if breed_slug else {}
    breed_risk_score = max(risk_profile.values()) if risk_profile else 0.0

    base = [
        float(age_years or 0),
        float(weight_kg or 0),
        1.0 if (sex or "").lower() == "male" else 0.0,
        1.0 if is_neutered else 0.0,
        float(size_ord),
        float(breed_risk_score),
        float(vitals.get("temperature_c") or 0),
        float(vitals.get("heart_rate") or 0),
        float(vitals.get("resp_rate") or 0),
    ]
    sym_set = set(symptoms)
    sym_vec = [1.0 if v in sym_set else 0.0 for v in symptom_vocab]
    return np.array(base + sym_vec, dtype=np.float32)


if __name__ == "__main__":
    from ..data_loader import load_knowledge_base

    kb = load_knowledge_base()
    print("Profil risiko ras dog-german-shepherd:")
    for slug, score in breed_risk_profile(kb, "dog-german-shepherd").items():
        print(f"  {slug}: {score}")
