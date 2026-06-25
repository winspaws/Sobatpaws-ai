#!/usr/bin/env python3
"""Verify ML inference and training state."""
import sys
sys.path.insert(0, 'src')

import json
from pathlib import Path

# 1. Check model meta files
ARTIFACTS = Path("artifacts/models")

print("=" * 60)
print("MODEL TRAINING SUMMARY")
print("=" * 60)

models_info = []
for meta_path in sorted(ARTIFACTS.glob("*.meta.json")):
    meta = json.loads(meta_path.read_text())
    info = {
        "category": meta["category_slug"],
        "source": meta.get("training_source", "unknown"),
        "accuracy": meta["metrics"]["accuracy"],
        "n_classes": meta["metrics"]["n_classes"],
        "n_samples": meta["metrics"]["n_samples"],
        "view_rows": meta.get("view_case_rows", 0),
        "real_rows": meta.get("real_case_rows", 0),
    }
    models_info.append(info)
    print(f"{info['category']:12} | acc={info['accuracy']:.2%} | classes={info['n_classes']:2} | samples={info['n_samples']:5} | source={info['source']}")

# 2. Test inference for dog
print("\n" + "=" * 60)
print("TESTING INFERENCE: dog with symptoms [Muntah hebat, Diare berdarah, Lemas/lesu]")
print("=" * 60)

from ekosistem_satwa.ml.predict import predict_diseases

results = predict_diseases(
    category_slug="dog",
    symptoms=["Muntah hebat", "Diare berdarah", "Lemas/lesu"],
    top_k=5,
)

for i, r in enumerate(results, 1):
    print(f"  {i}. {r['disease_slug']}: {r['confidence']:.1%}")

# 3. Test inference for cat
print("\n" + "=" * 60)
print("TESTING INFERENCE: cat with symptoms [Nafas sesak, Batuk, Bersin]")
print("=" * 60)

results_cat = predict_diseases(
    category_slug="cat",
    symptoms=["Nafas sesak", "Batuk", "Bersin"],
    top_k=5,
)

for i, r in enumerate(results_cat, 1):
    print(f"  {i}. {r['disease_slug']}: {r['confidence']:.1%}")

# 4. Check platform registry
print("\n" + "=" * 60)
print("PLATFORM REGISTRY SUMMARY")
print("=" * 60)
registry_path = Path("artifacts/platform_registry.json")
if registry_path.exists():
    reg = json.loads(registry_path.read_text())
    curated = reg.get("data_tracks", {}).get("curated_json", {}).get("stats", {})
    print(f"Curated KB: {curated.get('categories')} categories, {curated.get('breeds')} breeds, {curated.get('diseases')} diseases, {curated.get('unique_symptoms')} unique symptoms")
    ml_views = reg.get("data_tracks", {}).get("ml_views", {})
    print(f"ML Views exist: {ml_views.get('exists')}")
    learning = reg.get("data_tracks", {}).get("learning", {}).get("stats", {})
    if learning:
        print(f"Learning loop: {learning.get('consultation')} consultations, {learning.get('doctor_input')} doctor gold labels")
    
    # Model stats from registry
    print("\nModels from registry (10 total):")
    for m in reg.get("models", []):
        print(f"  {m['category_slug']:12} | acc={m['metrics']['accuracy']:.2%} | samples={m['metrics']['n_samples']:5}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
