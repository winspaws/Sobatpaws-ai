"""Training model symptom -> disease (baseline) untuk Sobatpaws.

Melatih classifier per kategori spesies (kosakata gejala berbeda per spesies)
dan menyimpan artefak + metadata (vocab, label) untuk inferensi.

Jalankan:
    python -m sobatpaws.ml.train            # latih semua kategori
    python -m sobatpaws.ml.train --category dog
"""
from __future__ import annotations

import argparse
import json

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, top_k_accuracy_score
from sklearn.model_selection import train_test_split

from ..config import ARTIFACTS_DIR
from ..data_loader import load_knowledge_base
from .dataset_builder import (
    DatasetBuildConfig,
    build_symptom_disease_dataset,
    clinical_rows_to_dataframe,
    merge_clinical_cases,
)
from .views_loader import load_view_clinical_rows

TRAINING_SOURCES = ("kb", "views", "hybrid")


def _build_training_df(
    category_slug: str,
    *,
    source: str = "kb",
    samples_per_disease: int = 80,
    clinical_rows: list[dict] | None = None,
    max_view_cases: int | None = None,
) -> tuple["pd.DataFrame", int, int]:
    """Bangun DataFrame latih sesuai sumber data."""
    import pandas as pd

    kb = load_knowledge_base()
    df = pd.DataFrame()
    view_rows = 0
    real_rows = 0

    if source in ("kb", "hybrid"):
        df = build_symptom_disease_dataset(
            kb,
            DatasetBuildConfig(
                category_slug=category_slug,
                samples_per_disease=samples_per_disease,
            ),
        )

    if source in ("views", "hybrid"):
        vrows = load_view_clinical_rows(category_slug, max_cases=max_view_cases)
        view_rows = len(vrows)
        if vrows:
            if source == "views":
                df = clinical_rows_to_dataframe(vrows)
            else:
                df = merge_clinical_cases(df, vrows, source_label="synthetic_cases")

    if clinical_rows:
        rows_cat = [
            r for r in clinical_rows
            if not category_slug or r.get("category_slug") == category_slug
        ]
        if rows_cat:
            df = merge_clinical_cases(
                df, rows_cat, source_label="clinical_real", expand_vocab=True,
            )
            real_rows = len(rows_cat)

    return df, view_rows, real_rows


def train_category_model(
    category_slug: str,
    samples_per_disease: int = 80,
    clinical_rows: list[dict] | None = None,
    source: str = "kb",
    max_view_cases: int | None = None,
) -> dict:
    """Latih model symptom->disease untuk satu kategori.

    Bila `clinical_rows` diberikan (label emas dari input dokter), data nyata
    tsb digabungkan ke dataset sintetis sebagai bahan pembelajaran tambahan.
    """
    if source not in TRAINING_SOURCES:
        return {
            "category": category_slug,
            "status": "skipped",
            "reason": f"source tidak valid: {source}",
        }

    df, view_rows, real_rows = _build_training_df(
        category_slug,
        source=source,
        samples_per_disease=samples_per_disease,
        clinical_rows=clinical_rows,
        max_view_cases=max_view_cases,
    )

    if df.empty or df["disease_slug"].nunique() < 2:
        return {"category": category_slug, "status": "skipped",
                "reason": "butuh >=2 penyakit dengan gejala",
                "training_source": source, "view_rows": view_rows}

    feat_cols = [c for c in df.columns if c.startswith("sym::")]
    X = df[feat_cols].to_numpy()
    y = df["disease_slug"].to_numpy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    clf = RandomForestClassifier(
        n_estimators=300, max_depth=None, n_jobs=-1, random_state=42
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    proba = clf.predict_proba(X_test)
    classes = list(clf.classes_)
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "f1_macro": round(float(f1_score(y_test, y_pred, average="macro")), 4),
        "n_classes": len(classes),
        "n_features": len(feat_cols),
        "n_samples": int(len(df)),
    }
    if len(classes) > 3:
        try:
            metrics["top3_accuracy"] = round(float(
                top_k_accuracy_score(y_test, proba, k=3, labels=classes)), 4)
        except Exception:
            pass

    out_dir = ARTIFACTS_DIR / "models"
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / f"symptom_disease_{category_slug}.joblib"
    meta_path = out_dir / f"symptom_disease_{category_slug}.meta.json"
    joblib.dump(clf, model_path)
    meta = {
        "category_slug": category_slug,
        "task_type": "symptom_to_disease",
        "algorithm": "random_forest",
        "symptom_vocab": [c[len("sym::"):] for c in feat_cols],
        "classes": classes,
        "metrics": metrics,
        "real_case_rows": real_rows,
        "view_case_rows": view_rows,
        "training_source": source,
        "model_path": str(model_path),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    try:
        from ..platform.model_registry_pg import sync_models_to_postgres
        sync_models_to_postgres(category_slug=category_slug)
    except Exception:  # noqa: BLE001
        pass
    return {
        "category": category_slug,
        "status": "trained",
        **metrics,
        "real_case_rows": real_rows,
        "view_case_rows": view_rows,
        "training_source": source,
        "model_path": str(model_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", default=None,
                        help="slug kategori; kosong = semua")
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument(
        "--source",
        choices=TRAINING_SOURCES,
        default="kb",
        help="kb=synthetic JSON; views=synthetic CSV; hybrid=gabungan",
    )
    parser.add_argument(
        "--max-view-cases",
        type=int,
        default=None,
        help="batas baris kasus synthetic (views/hybrid); kosong=semua",
    )
    args = parser.parse_args()

    kb = load_knowledge_base()
    cats = ([args.category] if args.category
            else sorted({d.get("category_slug") for d in kb.diseases if d.get("category_slug")}))
    print(f"Melatih model untuk kategori: {cats} (source={args.source})\n")
    for cat in cats:
        result = train_category_model(
            cat,
            args.samples,
            source=args.source,
            max_view_cases=args.max_view_cases,
        )
        print(json.dumps(result, ensure_ascii=False))
    try:
        from ..platform.registry import refresh_registry
        refresh_registry()
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    main()
