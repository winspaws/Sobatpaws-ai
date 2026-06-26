#!/usr/bin/env python3
"""Verify Sobatpaws API endpoints."""
import json, urllib.request

BASE = "http://localhost:8000"

def get(path):
    try:
        r = urllib.request.urlopen(f"{BASE}{path}")
        return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def post(path, data):
    try:
        req = urllib.request.Request(
            f"{BASE}{path}",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        r = urllib.request.urlopen(req)
        return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

print("=== 1. Health ===")
h = get("/health")
print(json.dumps(h, indent=2))

print("\n=== 2. Categories ===")
cats = get("/categories")
print(f"{len(cats)} categories:")
for c in cats:
    print(f"  - {c['slug']}")

print("\n=== 3. API Status ===")
s = get("/api/status")
print(f"Backend: {s['backend']['ok']}, Data: {s['data']['ok']}, AI: {s['ai']['ok']}, ML: {s['ml']['ok']}, All OK: {s.get('all_ok')}")

print("\n=== 4. Integration Manifest ===")
m = get("/api/integration/manifest")
print(f"Platform: {m['platform']}, Version: {m['api_version']}")

print("\n=== 5. ML Predict (dog) ===")
p = post("/ml/predict", {"category": "dog", "symptoms": ["Muntah hebat", "Diare berdarah", "Lemas/lesu"]})
print(json.dumps(p, indent=2))

print("\n=== 6. OpenAPI docs ===")
try:
    r = urllib.request.urlopen(f"{BASE}/docs")
    print(f"HTTP {r.status} - OK")
except Exception as e:
    print(f"Error: {e}")

print("\n=== ALL CHECKS DONE ===")
