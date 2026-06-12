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


def _load_diseases() -> list[dict]:
    diseases: list[dict] = []
    for path in sorted(CLINICAL_DIR.glob("diseases_*.json")):
        payload = _read_json(path)
        default_cat = payload.get("category_slug")
        file_disclaimer = payload.get("disclaimer")
        for d in payload.get("diseases", []):
            # category_slug bisa di level file atau di level disease (file gabungan)
            cat = d.get("category_slug", default_cat)
            diseases.append({
                **d,
                "category_slug": cat,
                "_category_disclaimer": d.get("_category_disclaimer", file_disclaimer),
            })
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
