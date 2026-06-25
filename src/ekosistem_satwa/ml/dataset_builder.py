"""Pembangun dataset ML dari knowledge base + (opsional) clinical_cases.

Tugas utama: membangun dataset untuk task `symptom_to_disease`.

Strategi:
1. KNOWLEDGE-BASED (synthetic): tiap penyakit punya daftar gejala berbobot
   (frequency). Kita bangkitkan sampel sintetis dengan sampling gejala
   menurut probabilitas frekuensinya. Ini memberi "cold-start" dataset sebelum
   data klinis nyata cukup banyak.
2. CLINICAL (real): bila tersedia ekspor `clinical_cases` (case_symptoms +
   case_diagnoses), gabungkan sebagai data emas (label terkonfirmasi vet).

Output: pandas.DataFrame multi-hot gejala + kolom target (disease_slug) +
metadata (category_slug, source).
"""
from __future__ import annotations

import random
from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..data_loader import KnowledgeBase, load_knowledge_base

# Peta frekuensi (risk_level) -> probabilitas kemunculan gejala
FREQ_TO_PROB = {
    "very_high": 0.95,
    "high": 0.80,
    "moderate": 0.50,
    "low": 0.20,
    "very_low": 0.08,
    None: 0.50,
}


@dataclass
class DatasetBuildConfig:
    samples_per_disease: int = 60
    noise_symptom_prob: float = 0.03   # peluang gejala "asing" muncul (noise)
    random_seed: int = 42
    category_slug: str | None = None    # bila diisi, batasi ke satu spesies


def _symptom_vocabulary(kb: KnowledgeBase, category_slug: str | None) -> list[str]:
    """Daftar gejala unik (pakai name_id sebagai key fitur, fallback name)."""
    vocab: list[str] = []
    seen: set[str] = set()
    diseases = (
        kb.diseases_for_category(category_slug) if category_slug else kb.diseases
    )
    for d in diseases:
        for s in d.get("symptoms", []):
            key = s.get("name_id") or s.get("name")
            if key and key not in seen:
                seen.add(key)
                vocab.append(key)
    return vocab


def build_symptom_disease_dataset(
    kb: KnowledgeBase | None = None,
    config: DatasetBuildConfig | None = None,
) -> pd.DataFrame:
    """Bangun dataset multi-hot gejala -> penyakit (synthetic, knowledge-based)."""
    kb = kb or load_knowledge_base()
    config = config or DatasetBuildConfig()
    rng = random.Random(config.random_seed)

    vocab = _symptom_vocabulary(kb, config.category_slug)
    vocab_index = {name: i for i, name in enumerate(vocab)}

    diseases = (
        kb.diseases_for_category(config.category_slug)
        if config.category_slug
        else kb.diseases
    )

    rows: list[dict] = []
    for disease in diseases:
        sym_probs = []
        for s in disease.get("symptoms", []):
            key = s.get("name_id") or s.get("name")
            if key in vocab_index:
                sym_probs.append((key, FREQ_TO_PROB.get(s.get("frequency"), 0.5)))
        if not sym_probs:
            continue

        for _ in range(config.samples_per_disease):
            vec = np.zeros(len(vocab), dtype=np.int8)
            for key, prob in sym_probs:
                if rng.random() < prob:
                    vec[vocab_index[key]] = 1
            # injeksi noise (gejala tak terkait)
            for i in range(len(vocab)):
                if vec[i] == 0 and rng.random() < config.noise_symptom_prob:
                    vec[i] = 1
            # pastikan minimal 1 gejala
            if vec.sum() == 0 and sym_probs:
                vec[vocab_index[sym_probs[0][0]]] = 1

            row = {f"sym::{name}": int(vec[i]) for i, name in enumerate(vocab)}
            row["disease_slug"] = disease["slug"]
            row["disease_name_id"] = disease.get("name_id") or disease.get("name")
            row["category_slug"] = disease.get("category_slug")
            row["source"] = "synthetic_kb"
            rows.append(row)

    df = pd.DataFrame(rows)
    return df


def merge_clinical_cases(
    df: pd.DataFrame,
    clinical_rows: list[dict],
    *,
    expand_vocab: bool = True,
    source_label: str | None = None,
) -> pd.DataFrame:
    """Gabungkan data klinis (nyata atau synthetic cases) ke dataset.

    clinical_rows: list of {"symptoms": [name_id, ...], "disease_slug": str,
                            "category_slug": str}
    """
    if not clinical_rows:
        return df

    sym_cols = [c for c in df.columns if c.startswith("sym::")]
    sym_keys = {c[len("sym::"):]: c for c in sym_cols}

    if expand_vocab:
        extra: set[str] = set()
        for case in clinical_rows:
            for s in case.get("symptoms", []):
                if s and s not in sym_keys:
                    extra.add(s)
        for s in sorted(extra):
            col = f"sym::{s}"
            sym_cols.append(col)
            sym_keys[s] = col
            if not df.empty:
                df[col] = 0

    if df.empty:
        df = pd.DataFrame(columns=sym_cols + [
            "disease_slug", "disease_name_id", "category_slug", "source",
        ])

    new_rows = []
    for case in clinical_rows:
        row = {c: 0 for c in sym_cols}
        for s in case.get("symptoms", []):
            col = sym_keys.get(s)
            if col:
                row[col] = 1
        row["disease_slug"] = case["disease_slug"]
        row["disease_name_id"] = case.get("disease_name_id", case["disease_slug"])
        row["category_slug"] = case.get("category_slug")
        row["source"] = source_label or case.get("source") or "clinical_real"
        new_rows.append(row)
    return pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True).fillna(0)


def clinical_rows_to_dataframe(clinical_rows: list[dict]) -> pd.DataFrame:
    """Bangun DataFrame multi-hot hanya dari clinical_rows (tanpa synthetic KB)."""
    return merge_clinical_cases(pd.DataFrame(), clinical_rows, expand_vocab=True)


if __name__ == "__main__":
    df = build_symptom_disease_dataset()
    print(f"Dataset shape: {df.shape}")
    print(f"Jumlah kelas penyakit: {df['disease_slug'].nunique()}")
    print(df["category_slug"].value_counts())
