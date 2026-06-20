"""Retraining loop — eksekusi pembelajaran dari input dokter.

Menutup siklus human-in-the-loop Sobatpaws:
    konsultasi -> input/koreksi dokter (LearningStore) -> gold rows -> RETRAIN.

Alur:
1. Ambil baris emas (doctor-confirmed) dari LearningStore.export_clinical_rows().
2. Kelompokkan per kategori spesies.
3. Latih ulang model symptom->disease tiap kategori, menggabungkan data nyata
   tsb ke dataset sintetis (knowledge-based) sebagai bahan pembelajaran tambahan.
4. Bersihkan cache inferensi agar model baru langsung dipakai.

Jalankan:
    python -m sobatpaws.ml.retrain                 # semua kategori dgn data dokter
    python -m sobatpaws.ml.retrain --category cat  # satu kategori
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict

from ..ai.learning_store import LearningStore, get_store
from .train import train_category_model


def retrain_from_learning_store(
    store: LearningStore | None = None,
    category: str | None = None,
    samples_per_disease: int = 80,
) -> dict:
    """Latih ulang model memakai gold rows dari learning store.

    Kembalikan ringkasan: kategori yang dilatih, jumlah kasus dokter terpakai,
    dan metrik per model.
    """
    store = store or get_store()
    gold_rows = store.export_clinical_rows()

    by_category: dict[str, list[dict]] = defaultdict(list)
    for r in gold_rows:
        cat = r.get("category_slug")
        if cat:
            by_category[cat].append(r)

    # kategori target: yang punya data dokter; bila --category dipakai, batasi.
    target_cats = (
        [category] if category else sorted(by_category.keys())
    )
    if not target_cats:
        return {
            "status": "no_data",
            "message": "Belum ada input dokter terkonfirmasi untuk retraining.",
            "gold_rows": 0,
        }

    results = []
    for cat in target_cats:
        rows = by_category.get(cat, [])
        res = train_category_model(
            cat, samples_per_disease=samples_per_disease, clinical_rows=rows
        )
        results.append(res)

    # model baru -> kosongkan cache inferensi
    try:
        from .predict import _load

        _load.cache_clear()
    except Exception:  # noqa: BLE001
        pass

    try:
        from ..platform.registry import refresh_registry
        refresh_registry()
    except Exception:  # noqa: BLE001
        pass

    return {
        "status": "retrained",
        "gold_rows": len(gold_rows),
        "categories": target_cats,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Retrain dari input dokter (gold).")
    parser.add_argument("--category", default=None, help="slug kategori; kosong = semua")
    parser.add_argument("--samples", type=int, default=80)
    args = parser.parse_args()

    summary = retrain_from_learning_store(
        category=args.category, samples_per_disease=args.samples
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
