"""Pemuat data master Sobatpaws dari file JSON menjadi knowledge base in-memory.

Knowledge base ini menjadi sumber kebenaran (single source of truth) untuk:
- seed SQL
- pembangunan dataset ML (symptom -> disease)
- grounding/retrieval untuk AI suggestion engine
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .config import BREEDS_DIR, CLINICAL_DIR, DATA_DIR


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@dataclass
class KnowledgeBase:
    """Representasi gabungan seluruh data master."""

    categories: list[dict] = field(default_factory=list)
    breeds: list[dict] = field(default_factory=list)          # tiap breed punya category_slug
    diseases: list[dict] = field(default_factory=list)        # tiap disease punya category_slug + relasi

    # ---- index lookup ----
    def category_by_slug(self, slug: str) -> dict | None:
        return next((c for c in self.categories if c["slug"] == slug), None)

    def breed_by_slug(self, slug: str) -> dict | None:
        return next((b for b in self.breeds if b["slug"] == slug), None)

    def disease_by_slug(self, slug: str) -> dict | None:
        return next((d for d in self.diseases if d["slug"] == slug), None)

    def breeds_for_category(self, category_slug: str) -> list[dict]:
        return [b for b in self.breeds if b.get("category_slug") == category_slug]

    def diseases_for_category(self, category_slug: str) -> list[dict]:
        return [d for d in self.diseases if d.get("category_slug") == category_slug]

    def diseases_for_breed(self, breed_slug: str) -> list[dict]:
        """Penyakit yang relevan untuk ras tertentu (via susceptibility)."""
        out = []
        for d in self.diseases:
            for s in d.get("breed_susceptibility", []):
                if s.get("breed_slug") == breed_slug:
                    out.append({**d, "_risk": s.get("risk"), "_prevalence_pct": s.get("prevalence_pct")})
                    break
        return out

    # ---- agregasi ----
    def all_symptoms(self) -> dict[str, dict]:
        """Kumpulan unik gejala (key: name_id atau name)."""
        result: dict[str, dict] = {}
        for d in self.diseases:
            for s in d.get("symptoms", []):
                key = s.get("name") or s.get("name_id")
                if key and key not in result:
                    result[key] = {
                        "name": s.get("name"),
                        "name_id": s.get("name_id"),
                        "body_system": s.get("body_system"),
                        "is_red_flag": s.get("is_red_flag", False),
                    }
        return result

    def stats(self) -> dict[str, int]:
        return {
            "categories": len(self.categories),
            "breeds": len(self.breeds),
            "diseases": len(self.diseases),
            "unique_symptoms": len(self.all_symptoms()),
        }


def _load_breeds() -> list[dict]:
    breeds: list[dict] = []
    for path in sorted(BREEDS_DIR.glob("*.json")):
        payload = _read_json(path)
        # Format A: {category_slug, breeds: [...]}
        if "breeds" in payload:
            for b in payload["breeds"]:
                breeds.append({**b, "category_slug": payload["category_slug"]})
        # Format B (others.json): {groups: [{category_slug, breeds: [...]}]}
        for group in payload.get("groups", []):
            for b in group["breeds"]:
                breeds.append({**b, "category_slug": group["category_slug"]})
    return breeds


def _normalize_etiology(etiology: str | None) -> str | None:
    """Map free-text etiology to valid PostgreSQL enum value."""
    if etiology is None:
        return None
    valid_enums = {
        "infectious_viral", "infectious_bacterial", "infectious_fungal",
        "parasitic_internal", "parasitic_external", "genetic_congenital",
        "nutritional", "metabolic", "neoplastic", "traumatic", "toxic",
        "degenerative", "idiopathic", "behavioral", "environmental",
    }
    etiology_lower = etiology.strip().lower()
    # Already valid enum
    if etiology_lower in valid_enums:
        return etiology_lower
    # Keyword-based mapping
    kw_map = [
        ("jamur", "infectious_fungal"),
        ("fungal", "infectious_fungal"),
        ("bakteri", "infectious_bacterial"),
        ("bacterial", "infectious_bacterial"),
        ("virus", "infectious_viral"),
        ("viral", "infectious_viral"),
        ("parvovirus", "infectious_viral"),
        ("parasit", "parasitic_internal"),
        ("kalsium", "nutritional"),
        ("vitamin", "nutritional"),
        ("nutrisi", "nutritional"),
        ("defisiensi", "nutritional"),
        ("nutritional", "nutritional"),
        ("neoplasma", "neoplastic"),
        ("tumor", "neoplastic"),
        ("adenoma", "neoplastic"),
        ("karsinoma", "neoplastic"),
        ("neoplastic", "neoplastic"),
        ("metabolisme", "metabolic"),
        ("metabolic", "metabolic"),
        ("trauma", "traumatic"),
        ("tekanan", "traumatic"),
        ("traumatic", "traumatic"),
        ("genetik", "genetic_congenital"),
        ("genetic", "genetic_congenital"),
        ("degeneratif", "degenerative"),
        ("degenerative", "degenerative"),
        ("perilaku", "behavioral"),
        ("behavioral", "behavioral"),
        ("lingkungan", "environmental"),
        ("environmental", "environmental"),
        ("toksin", "toxic"),
        ("toxic", "toxic"),
        ("idiopatik", "idiopathic"),
        ("idiopathic", "idiopathic"),
    ]
    for kw, mapped in kw_map:
        if kw in etiology_lower:
            return mapped
    return "idiopathic"


def _normalize_disease(d: dict, default_cat: str | None, file_disclaimer: str | None) -> dict:
    """Normalisasi disease dari berbagai format (domestic vs exotic) ke schema standar."""
    cat = d.get("category_slug", default_cat)
    result = {
        **d,
        "category_slug": cat,
        "_category_disclaimer": d.get("_category_disclaimer", file_disclaimer),
    }
    # Exotic diseases use 'common_name' instead of 'name'
    if "name" not in result and "common_name" in result:
        result["name"] = result["common_name"]
    # Normalize etiology to valid enum
    if "etiology" in result:
        result["etiology"] = _normalize_etiology(result["etiology"])
    # Normalize body_system to valid enum
    if "body_system" in result:
        bs_map = {
            "oral": "dental", "mulut": "dental", "gigi": "dental",
            "kulit": "integumentary", "skin": "integumentary",
            "pencernaan": "digestive", "pernapasan": "respiratory",
            "syaraf": "nervous", "saraf": "nervous", "neurological": "nervous",
            "muskuloskeletal": "musculoskeletal", "tulang": "musculoskeletal",
            "endokrin": "endocrine", "hormon": "endocrine",
            "mata": "ophthalmic", "telinga": "auditory",
            "darah": "hematologic", "kekebalan": "immune",
            "perilaku": "behavioral", "perkemihan": "urinary",
            "reproduksi": "reproductive", "kardiovaskular": "cardiovascular",
        }
        bs = result["body_system"]
        if isinstance(bs, str) and bs.lower() in bs_map:
            result["body_system"] = bs_map[bs.lower()]
    # Exotic: 'contagious' -> 'is_contagious'
    if "is_contagious" not in result and "contagious" in result:
        result["is_contagious"] = result["contagious"]
    # Exotic: 'clinical_signs' -> 'symptoms'
    if "symptoms" not in result and "clinical_signs" in result:
        signs = result["clinical_signs"]
        if isinstance(signs, list):
            result["symptoms"] = [{"name": s} if isinstance(s, str) else s for s in signs]
        elif isinstance(signs, str):
            result["symptoms"] = [{"name": signs}]
    # Exotic: 'diagnostic_gold_standard' -> 'diagnostics'
    if "diagnostics" not in result and "diagnostic_gold_standard" in result:
        dgs = result["diagnostic_gold_standard"]
        if isinstance(dgs, list):
            result["diagnostics"] = [{"name": d} if isinstance(d, str) else d for d in dgs]
        elif isinstance(dgs, str):
            result["diagnostics"] = [{"name": dgs, "is_gold_standard": True}]
    # Exotic: 'treatment' -> 'treatments'
    if "treatments" not in result and "treatment" in result:
        tx = result["treatment"]
        if isinstance(tx, list):
            result["treatments"] = [{"name": t} if isinstance(t, str) else t for t in tx]
        elif isinstance(tx, str):
            result["treatments"] = [{"name": tx}]
    return result


def _load_diseases() -> list[dict]:
    diseases: list[dict] = []
    for path in sorted(CLINICAL_DIR.glob("diseases_*.json")):
        payload = _read_json(path)
        default_cat = payload.get("category_slug")
        file_disclaimer = payload.get("disclaimer")
        for d in payload.get("diseases", []):
            diseases.append(_normalize_disease(d, default_cat, file_disclaimer))
    return diseases


def load_knowledge_base() -> KnowledgeBase:
    """Muat seluruh data master menjadi satu KnowledgeBase."""
    categories = _read_json(DATA_DIR / "categories.json")["categories"]
    return KnowledgeBase(
        categories=categories,
        breeds=_load_breeds(),
        diseases=_load_diseases(),
    )


if __name__ == "__main__":
    kb = load_knowledge_base()
    print("Knowledge base loaded:")
    for k, v in kb.stats().items():
        print(f"  - {k}: {v}")
