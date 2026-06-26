#!/usr/bin/env python3
"""Verify all Sobatpaws endpoints after deploy."""
import json, urllib.request, time

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
            f"{BASE}{path}", data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
        )
        r = urllib.request.urlopen(req)
        return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

time.sleep(5)

print("=== 1. Health ===")
h = get("/health")
print(f"Status: {h.get('status')}, Diseases: {h.get('knowledge_base',{}).get('diseases')}")

print("\n=== 2. ML Predict (dog) ===")
p = post("/ml/predict", {"category_slug":"dog","symptoms":["Muntah hebat","Diare berdarah","Lemas/lesu"]})
if "error" in p:
    print(f"ERROR: {p['error']}")
else:
    print(f"Top: {p['predictions'][0]['name_id']} ({p['predictions'][0]['confidence']*100:.0f}%)")

print("\n=== 3. Single-shot Consult ===")
c = post("/api/consult", {"category_slug":"dog","symptoms":["Muntah hebat","Diare berdarah","Lemas/lesu"]})
if "error" in c:
    print(f"ERROR: {c['error']}")
else:
    print(f"Emergency: {c.get('is_emergency')}, Summary: {str(c.get('summary',''))[:120]}")

print("\n=== 4. Platform Doctor ===")
d = get("/api/platform/doctor")
print(f"Status: {d.get('status')}")

print("\n=== 5. Integration Manifest ===")
m = get("/api/integration/manifest")
print(f"Platform: {m.get('platform')}, Version: {m.get('api_version')}")

print("\n=== ALL DONE ===")
