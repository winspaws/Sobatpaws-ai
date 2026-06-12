"""Inferensi model symptom -> disease yang sudah dilatih."""
from __future__ import annotations

import json
from functools import lru_cache

import joblib
import numpy as np

from ..config import ARTIFACTS_DIR


@lru_cache(maxsize=16)
def _load(category_slug: str):
    meta_path = ARTIFACTS_DIR / "models" / f"symptom_disease_{category_slug}.meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(
            f"Model untuk '{category_slug}' belum dilatih. Jalankan: "
            f"python -m sobatpaws.ml.train --category {category_slug}"
        )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    model = joblib.load(meta["model_path"])
    return model, meta


def predict_diseases(category_slug: str, symptoms: list[str], top_k: int = 5) -> list[dict]:
    """Prediksi penyakit teratas dari daftar gejala (name_id)."""
    model, meta = _load(category_slug)
    vocab = meta["symptom_vocab"]
    idx = {name: i for i, name in enumerate(vocab)}
    x = np.zeros(len(vocab), dtype=np.float32)
    matched = []
    for s in symptoms:
        if s in idx:
            x[idx[s]] = 1.0
            matched.append(s)

    proba = model.predict_proba(x.reshape(1, -1))[0]
    classes = model.classes_
    order = np.argsort(proba)[::-1][:top_k]
    results = [
        {"disease_slug": str(classes[i]), "confidence": round(float(proba[i]), 4)}
        for i in order
    ]
    return results


if __name__ == "__main__":
    import sys

    cat = sys.argv[1] if len(sys.argv) > 1 else "dog"
    syms = sys.argv[2:] or ["Muntah hebat", "Diare berdarah", "Lemas/lesu"]
    for r in predict_diseases(cat, syms):
        print(r)
