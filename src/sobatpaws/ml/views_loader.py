"""Muat baris kasus klinis dari synthetic CSV / ML views untuk training.

Menjembatani jalur synthetic_csv → ML train (symptom→disease) dengan format
clinical_rows yang kompatibel dengan dataset_builder.merge_clinical_cases().
"""
from __future__ import annotations

import csv
import gzip
import json
import random
from collections import defaultdict
from pathlib import Path

from ..config import GENERATED_DIR, ML_VIEWS_DIR


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _read_gz_csv(path: Path) -> list[dict[str, str]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _load_view_file(category_slug: str | None, max_cases: int | None) -> list[dict] | None:
    """Coba baca ml_view_symptom_disease_cases (Parquet atau gzip-CSV)."""
    base = ML_VIEWS_DIR / "ml_view_symptom_disease_cases"
    rows_raw: list[dict] | None = None

    parquet = base.with_suffix(".parquet")
    if parquet.exists():
        try:
            import pandas as pd

            df = pd.read_parquet(parquet)
            rows_raw = df.to_dict(orient="records")
        except Exception:
            rows_raw = None

    if rows_raw is None:
        gz = base.with_suffix(".csv.gz")
        if gz.exists():
            rows_raw = _read_gz_csv(gz)

    if not rows_raw:
        return None

    out: list[dict] = []
    for r in rows_raw:
        cat = r.get("category_slug") or ""
        if category_slug and cat != category_slug:
            continue
        symptoms_raw = r.get("symptoms_json") or r.get("symptoms") or "[]"
        if isinstance(symptoms_raw, str):
            try:
                symptoms = json.loads(symptoms_raw)
            except json.JSONDecodeError:
                symptoms = [s for s in symptoms_raw.split("|") if s]
        else:
            symptoms = list(symptoms_raw)
        out.append({
            "symptoms": symptoms,
            "disease_slug": r["disease_slug"],
            "disease_name_id": r.get("disease_name_id") or r["disease_slug"],
            "category_slug": cat,
            "source": "synthetic_views",
            "case_id": r.get("case_id"),
        })

    if max_cases and len(out) > max_cases:
        rng = random.Random(42)
        out = rng.sample(out, max_cases)
    return out


def load_clinical_rows_from_generated(
    category_slug: str | None = None,
    max_cases: int | None = None,
    seed: int = 42,
) -> list[dict]:
    """Bangun clinical_rows dari data/generated/*.csv (confirmed diagnosis + gejala)."""
    cases_csv = GENERATED_DIR / "clinical_cases.csv"
    if not cases_csv.exists():
        return []

    cat_slug: dict[str, str] = {}
    for r in _read_csv(GENERATED_DIR / "animal_categories.csv"):
        cat_slug[r["id"]] = r["slug"]

    disease_meta: dict[str, tuple[str, str]] = {}
    for r in _read_csv(GENERATED_DIR / "diseases.csv"):
        disease_meta[r["id"]] = (r["slug"], r.get("name_id") or r["slug"])

    symptom_name: dict[str, str] = {}
    for r in _read_csv(GENERATED_DIR / "symptoms.csv"):
        symptom_name[r["id"]] = r.get("name_id") or r.get("name") or r["slug"]

    pet_cat: dict[str, str] = {}
    for r in _read_csv(GENERATED_DIR / "pets.csv"):
        pet_cat[r["id"]] = cat_slug.get(r["category_id"], "")

    case_label: dict[str, str] = {}
    for r in _read_csv(GENERATED_DIR / "case_diagnoses.csv"):
        if r.get("is_confirmed") == "true":
            case_label[r["case_id"]] = r["disease_id"]

    case_symptoms: dict[str, list[str]] = defaultdict(list)
    for r in _read_csv(GENERATED_DIR / "case_symptoms.csv"):
        sid = symptom_name.get(r["symptom_id"])
        if sid:
            case_symptoms[r["case_id"]].append(sid)

    case_pet: dict[str, str] = {}
    for r in _read_csv(cases_csv):
        case_pet[r["id"]] = r["pet_id"]

    rows: list[dict] = []
    for case_id, disease_id in case_label.items():
        pet_id = case_pet.get(case_id)
        if not pet_id:
            continue
        cat = pet_cat.get(pet_id, "")
        if category_slug and cat != category_slug:
            continue
        meta = disease_meta.get(disease_id)
        if not meta:
            continue
        symptoms = case_symptoms.get(case_id, [])
        if not symptoms:
            continue
        dslug, dname = meta
        rows.append({
            "symptoms": symptoms,
            "disease_slug": dslug,
            "disease_name_id": dname,
            "category_slug": cat,
            "source": "synthetic_cases",
            "case_id": case_id,
        })

    if max_cases and len(rows) > max_cases:
        rng = random.Random(seed)
        rows = rng.sample(rows, max_cases)
    return rows


def load_view_clinical_rows(
    category_slug: str | None = None,
    max_cases: int | None = None,
    seed: int = 42,
) -> list[dict]:
    """Muat clinical rows: utamakan ML view, fallback ke generated CSV."""
    from_view = _load_view_file(category_slug, max_cases)
    if from_view is not None:
        return from_view
    return load_clinical_rows_from_generated(category_slug, max_cases, seed=seed)
