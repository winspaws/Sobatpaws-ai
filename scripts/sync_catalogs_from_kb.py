#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sinkronkan vocabulary klinis catalogs.py dari knowledge base JSON curated.

Menghasilkan scripts/_kb_clinical_overlay.py (auto-generated) berisi penyakit
dari data/clinical/*.json yang belum ada di CLINICAL catalogs (match by slug).

Jalankan:
  PYTHONPATH=src python3 scripts/sync_catalogs_from_kb.py
  PYTHONPATH=src python3 scripts/sync_catalogs_from_kb.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
OUT = SCRIPTS / "_kb_clinical_overlay.py"

sys.path.insert(0, str(ROOT / "src"))

from sobatpaws.data_loader import load_knowledge_base  # noqa: E402

# Impor catalogs setelah path OK
sys.path.insert(0, str(SCRIPTS))
import catalogs  # noqa: E402


_SEVERITY_MAP = {
    "critical": "critical",
    "severe": "severe",
    "moderate": "moderate",
    "mild": "mild",
}

_RISK_DEFAULT = "moderate"


def _catalog_slugs() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for cat, diseases in catalogs.CLINICAL.items():
        out.setdefault(cat, set()).update(d.get("slug") for d in diseases)
    return out


def _kb_to_catalog_disease(d: dict) -> dict:
    """Konversi penyakit KB ke dict minimal kompatibel generate_dataset."""
    prev = None
    for bs in d.get("breed_susceptibility") or []:
        if bs.get("prevalence_pct") is not None:
            prev = int(bs["prevalence_pct"])
            break
    sev = _SEVERITY_MAP.get(d.get("default_severity") or "moderate", "moderate")
    return {
        "slug": d["slug"],
        "name": d.get("name") or d["slug"],
        "name_id": d.get("name_id") or d.get("name") or d["slug"],
        "etiology": d.get("etiology") or "idiopathic",
        "body_system": d.get("body_system") or "systemic",
        "severity": sev,
        "risk": _RISK_DEFAULT,
        "contagious": bool(d.get("is_contagious")),
        "zoonotic": bool(d.get("is_zoonotic")),
        "emergency": bool(d.get("is_emergency")),
        "prevalence": prev,
        "diagnostics": [catalogs.DX_PHYS],
        "treatment": catalogs.TX_SUPPORT,
        "products": [catalogs.PR_ABX],
        "_from_kb": True,
    }


def build_overlay() -> tuple[dict[str, list[dict]], dict[str, int]]:
    kb = load_knowledge_base()
    existing = _catalog_slugs()
    overlay: dict[str, list[dict]] = {}
    stats = {"kb_diseases": len(kb.diseases), "added": 0, "already_in_catalog": 0}

    for d in kb.diseases:
        cat = d.get("category_slug")
        if not cat:
            continue
        slug = d["slug"]
        if slug in existing.get(cat, set()):
            stats["already_in_catalog"] += 1
            continue
        overlay.setdefault(cat, []).append(_kb_to_catalog_disease(d))
        stats["added"] += 1

    return overlay, stats


def write_overlay(overlay: dict[str, list[dict]], stats: dict[str, int]) -> None:
    lines = [
        '"""AUTO-GENERATED — jangan edit manual.',
        "",
        "Regenerate:",
        "  PYTHONPATH=src python3 scripts/sync_catalogs_from_kb.py",
        '"""',
        "",
        f"# kb_diseases={stats['kb_diseases']} added={stats['added']} "
        f"already_in_catalog={stats['already_in_catalog']}",
        "",
        "KB_CLINICAL_OVERLAY = ",
        json.dumps(overlay, ensure_ascii=False, indent=2),
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Cetak statistik saja")
    args = ap.parse_args()

    overlay, stats = build_overlay()
    print(json.dumps({"stats": stats, "categories_with_overlay": list(overlay.keys())},
                     ensure_ascii=False, indent=2))

    if args.dry_run:
        return

    write_overlay(overlay, stats)
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
