#!/usr/bin/env python3
"""Test Sobatpaws ML predict and consult endpoints."""
import json, urllib.request

BASE = "http://localhost:8000"

def post(path, data):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
    )
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

# Test ML predict
print("=== ML Predict (dog) ===")
try:
    r = post("/ml/predict", {"category_slug": "dog", "symptoms": ["Muntah hebat", "Diare berdarah", "Lemas/lesu"]})
    print(json.dumps(r, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")

# Test single-shot consult
print("\n=== Single-shot Consult (dog) ===")
try:
    r = post("/api/consult", {"category_slug": "dog", "symptoms": ["Muntah hebat", "Diare berdarah", "Lemas/lesu"]})
    print(json.dumps(r, indent=2, ensure_ascii=False)[:2000])
except Exception as e:
    print(f"Error: {e}")

# Test platform doctor
print("\n=== Platform Doctor ===")
try:
    r = json.loads(urllib.request.urlopen(f"{BASE}/api/platform/doctor").read())
    print(f"Status: {r.get('status')}")
    for c in r.get("checks", []):
        print(f"  {c.get('name')}: {c.get('status')} - {c.get('message', '')}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== DONE ===")
