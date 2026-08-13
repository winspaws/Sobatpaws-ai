#!/usr/bin/env python3
"""Smoke test Pawnia + health untuk Sobatpaws serve-ready check.

    PYTHONPATH=src python scripts/smoke_pawnia.py
    PYTHONPATH=src python scripts/smoke_pawnia.py --base http://127.0.0.1:8000
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


CASES = [
    {
        "name": "greeting",
        "payload": {"message": "Halo", "pet_context": {"name": "Milo", "species": "cat"}},
        "expect_agent": "pet_companion",
        "max_risk": 30,
        "expect_token_mode": "template",
    },
    {
        "name": "nutrition",
        "payload": {
            "message": "Rekomendasi makanan untuk kucing Persia alergi ayam",
            "pet_context": {"name": "Milo", "species": "cat", "breed": "Persian", "age_years": 3},
        },
        "expect_agent": "nutrition_advisor",
        "max_risk": 40,
    },
    {
        "name": "symptoms_kb",
        "payload": {
            "message": "Anjing saya muntah dan diare sejak kemarin, lemas tidak mau makan",
            "pet_context": {"name": "Bobby", "species": "dog", "age_years": 3},
        },
        "expect_agent": "pet_companion",
        "max_risk": 60,
        "expect_token_mode": "kb_ml",
    },
    {
        "name": "emergency",
        "payload": {
            "message": "Tolong! Anjing saya kejang-kejang dan tidak sadar!",
            "pet_context": {"name": "Bobby", "species": "dog", "age_years": 4},
        },
        "expect_agent": "triage_emergency",
        "min_risk": 80,
        "expect_escalated": True,
        "expect_token_mode": "template",
    },
]


def get_json(url: str, timeout: float = 20) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_json(url: str, payload: dict, timeout: float = 30) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base = args.base.rstrip("/")
    failed = 0

    try:
        health = get_json(f"{base}/health")
    except urllib.error.URLError as exc:
        print(f"FAIL  server tidak merespons {base}: {exc}")
        return 2

    if health.get("status") != "ok":
        print(f"FAIL  /health = {health}")
        failed += 1
    else:
        print(f"OK    /health llm={health.get('llm_available')}")

    status = get_json(f"{base}/api/v1/ai/status")
    needed = ("pawnia_available", "memory_available", "knowledge_available")
    for key in needed:
        if not status.get(key):
            print(f"FAIL  /api/v1/ai/status.{key}={status.get(key)}")
            failed += 1
        else:
            print(f"OK    status.{key}=true")

    manifest = get_json(f"{base}/api/integration/manifest")
    if not manifest.get("endpoints", {}).get("pawnia_chat"):
        print(f"FAIL  manifest tanpa pawnia_chat: {list(manifest.get('endpoints', {}))}")
        failed += 1
    else:
        print("OK    /api/integration/manifest")

    for case in CASES:
        try:
            out = post_json(f"{base}/api/v1/ai/chat", case["payload"])
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  {case['name']}: {exc}")
            failed += 1
            continue
        agent = out.get("agent")
        risk = int(out.get("risk_score") or 0)
        escalated = bool(out.get("escalated"))
        ok = True
        if case.get("expect_agent") and agent != case["expect_agent"]:
            ok = False
        if "min_risk" in case and risk < case["min_risk"]:
            ok = False
        if "max_risk" in case and risk > case["max_risk"]:
            ok = False
        if case.get("expect_escalated") and not escalated:
            ok = False
        token_mode = (out.get("response") or {}).get("token_mode") or (out.get("context_used") or {}).get("token_mode")
        if case.get("expect_token_mode") and token_mode != case["expect_token_mode"]:
            ok = False
        mark = "OK   " if ok else "FAIL "
        if not ok:
            failed += 1
        mode = (out.get("response") or {}).get("token_mode", "?")
        print(f"{mark} {case['name']}: agent={agent} risk={risk} escalated={escalated} token={mode}")

    if failed:
        print(f"\n{failed} check gagal")
        return 1
    print("\nSemua smoke test lulus — ready to serve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
