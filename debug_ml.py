#!/usr/bin/env python3
"""Debug ML predict."""
import sys, json
sys.path.insert(0, "/app/src")
from sobatpaws.ml.predict import predict_diseases
try:
    r = predict_diseases("dog", ["Muntah hebat", "Diare berdarah", "Lemas/lesu"])
    print(json.dumps(r, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
