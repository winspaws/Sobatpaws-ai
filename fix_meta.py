#!/usr/bin/env python3
"""Fix hardcoded model paths in meta.json files."""
import json, pathlib

models_dir = pathlib.Path("artifacts/models")
for meta_file in sorted(models_dir.glob("*.meta.json")):
    meta = json.loads(meta_file.read_text())
    slug = meta["category_slug"]
    meta["model_path"] = f"/app/artifacts/models/symptom_disease_{slug}.joblib"
    meta_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"Fixed: {meta_file.name}")
print("Done")
