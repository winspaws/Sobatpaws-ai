#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export the generated Sobatpaws dataset to Excel (.xlsx).

Excel limits: max 1,048,576 rows per sheet (including header). Tables that
exceed this are split across multiple sheets automatically.

Output (default: data/excel/):
  Sobatpaws_00_Summary.xlsx          ringkasan + manifest
  Sobatpaws_01_Taxonomy.xlsx         kategori, ras, varian, traits
  Sobatpaws_02_Clinical_Masters.xlsx penyakit, gejala, diagnosa, obat
  Sobatpaws_03_Clinical_Matrix.xlsx  matriks relasi (590k baris)
  Sobatpaws_04_Operational.xlsx      org, user, owner, pet, kasus
  Sobatpaws_05_Case_Details.xlsx     gejala/diagnosa/tindakan per kasus
  Sobatpaws_06_ML_AI.xlsx            dataset, model, prediksi, AI
  Sobatpaws_07_ML_Views.xlsx         tabel fitur siap latih (jika ada)
  Sobatpaws_08_Learning.xlsx         konsultasi AI + input dokter (gold rows)

Usage:
  python3 scripts/export_excel.py
  python3 scripts/export_excel.py --max-rows 50000   # batasi baris per sheet
  python3 scripts/export_excel.py --sample-only      # ringkasan + masters saja
  python3 scripts/export_excel.py --learning-only    # hanya bahan pembelajaran
"""
import argparse
import json
import os
import re
import sys
import time

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.normpath(os.path.join(HERE, "..", "data", "generated"))
MLV = os.path.normpath(os.path.join(HERE, "..", "data", "ml_views"))
LEARNING = os.path.normpath(os.path.join(HERE, "..", "artifacts", "learning"))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "excel"))

EXCEL_MAX_ROWS = 1_048_576          # incl. header -> max 1,048,575 data rows
SHEET_NAME_MAX = 31


def safe_sheet(name, part=0):
    s = re.sub(r"[\[\]\*\?/\\:]", "_", name)[:SHEET_NAME_MAX - 4]
    if part:
        s = "%s_%d" % (s[:SHEET_NAME_MAX - 6], part)
    return s


def read_csv(path, max_rows=None):
    if not os.path.exists(path):
        return None
    nrows = max_rows - 1 if max_rows else None  # reserve 1 for header
    return pd.read_csv(path, nrows=nrows, low_memory=False)


def write_table(writer, table, max_rows=None):
    path = os.path.join(GEN, table + ".csv")
    if not os.path.exists(path):
        return 0
    total = sum(1 for _ in open(path, encoding="utf-8")) - 1
    if max_rows and total > max_rows - 1:
        df = read_csv(path, max_rows)
        df.to_excel(writer, sheet_name=safe_sheet(table), index=False)
        return len(df)

    chunk = EXCEL_MAX_ROWS - 1
    if total <= chunk:
        df = pd.read_csv(path, low_memory=False)
        df.to_excel(writer, sheet_name=safe_sheet(table), index=False)
        return len(df)

    header = pd.read_csv(path, nrows=0).columns.tolist()
    part = 1
    written = 0
    for start in range(0, total, chunk):
        df = pd.read_csv(path, skiprows=range(1, start + 1), nrows=chunk,
                         names=header, header=None, low_memory=False)
        df.to_excel(writer, sheet_name=safe_sheet(table, part), index=False)
        written += len(df)
        part += 1
    return written


def write_gzip_csv(writer, gz_name, sheet):
    import gzip
    path = os.path.join(MLV, gz_name)
    if not os.path.exists(path):
        return 0
    with gzip.open(path, "rt") as f:
        df = pd.read_csv(f, nrows=EXCEL_MAX_ROWS - 1)
    df.to_excel(writer, sheet_name=safe_sheet(sheet), index=False)
    return len(df)


def build_summary():
    rows = []
    manifest_path = os.path.join(GEN, "manifest.json")
    if os.path.exists(manifest_path):
        m = json.load(open(manifest_path))
        for t, info in sorted(m.get("tables", {}).items()):
            rows.append({"table": t, "rows": info["rows"], "sha256": info["sha256"][:16]})
        rows.append({"table": "GRAND TOTAL", "rows": m.get("grand_total_rows", ""),
                     "sha256": ""})
    else:
        for f in sorted(os.listdir(GEN)):
            if f.endswith(".csv"):
                n = sum(1 for _ in open(os.path.join(GEN, f))) - 1
                rows.append({"table": f.replace(".csv", ""), "rows": n, "sha256": ""})
    return pd.DataFrame(rows)


def read_jsonl(path):
    """Baca file JSONL menjadi list of dict."""
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def jsonl_to_df(filename, flatten_keys=None):
    """Muat JSONL ke DataFrame; flatten_keys: nested dict -> kolom JSON string."""
    rows = read_jsonl(os.path.join(LEARNING, filename))
    if not rows:
        return pd.DataFrame()
    flat = []
    for r in rows:
        row = dict(r)
        for k in flatten_keys or []:
            if k in row and isinstance(row[k], (dict, list)):
                row[k] = json.dumps(row[k], ensure_ascii=False)
        flat.append(row)
    return pd.DataFrame(flat)


def build_gold_rows_df():
    """Baris siap-latih dari input dokter (mirror learning_store.export_clinical_rows)."""
    consult_ctx = {
        r["consultation_id"]: r.get("context", {})
        for r in read_jsonl("consultations.jsonl")
    }
    consult_intake = {}
    for r in read_jsonl("intake_events.jsonl"):
        cid = r["consultation_id"]
        consult_intake.setdefault(cid, [])
        for s in r.get("symptoms", []):
            nid = s.get("name_id") if isinstance(s, dict) else None
            if nid:
                consult_intake[cid].append(nid)

    gold = []
    for di in read_jsonl("doctor_inputs.jsonl"):
        disease = di.get("confirmed_disease_slug")
        if not disease:
            continue
        cid = di.get("consultation_id")
        ctx = consult_ctx.get(cid, {})
        symptoms = di.get("confirmed_symptoms") or consult_intake.get(cid, [])
        symptoms = sorted(set(s for s in symptoms if s))
        if not symptoms:
            continue
        gold.append({
            "consultation_id": cid,
            "category_slug": ctx.get("category_slug"),
            "disease_slug": disease,
            "symptoms": ", ".join(symptoms),
            "symptom_count": len(symptoms),
            "clinical_notes": di.get("clinical_notes"),
            "vet_id": di.get("vet_id"),
            "source": "doctor_confirmed",
        })
    return pd.DataFrame(gold)


def export_learning_workbook():
    """Export jejak konsultasi & pembelajaran ke Sobatpaws_08_Learning.xlsx."""
    path = os.path.join(OUT, "Sobatpaws_08_Learning.xlsx")
    os.makedirs(OUT, exist_ok=True)
    if not os.path.isdir(LEARNING):
        print("  (skip) artifacts/learning/ belum ada")
        return 0

    sheets = {
        "consultations": jsonl_to_df("consultations.jsonl", ["context"]),
        "intake_events": jsonl_to_df("intake_events.jsonl", ["symptoms", "observations"]),
        "suggestions": jsonl_to_df("suggestions.jsonl", ["suggestion"]),
        "doctor_inputs": jsonl_to_df("doctor_inputs.jsonl"),
        "feedback": jsonl_to_df("feedback.jsonl"),
        "gold_rows_retrain": build_gold_rows_df(),
    }
    t0 = time.time()
    total = 0
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        for name, df in sheets.items():
            if df.empty:
                df = pd.DataFrame([{"note": "Belum ada data"}])
            df.to_excel(w, sheet_name=safe_sheet(name), index=False)
            total += len(df)
    print("  %-40s %8d rows  (%.1fs)" % ("Sobatpaws_08_Learning.xlsx", total, time.time() - t0))
    return total


def export_workbook(filename, tables, max_rows=None, extra_sheets=None):
    path = os.path.join(OUT, filename)
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    counts = {}
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        for table in tables:
            n = write_table(w, table, max_rows)
            if n:
                counts[table] = n
        if extra_sheets:
            for name, df in extra_sheets.items():
                df.to_excel(w, sheet_name=safe_sheet(name), index=False)
                counts[name] = len(df)
    print("  %-40s %8d rows  (%.1fs)" % (filename, sum(counts.values()), time.time() - t0))
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-rows", type=int, default=None,
                    help="Max rows per table (for lighter exports)")
    ap.add_argument("--sample-only", action="store_true",
                    help="Export summary + masters only (fast)")
    ap.add_argument("--learning-only", action="store_true",
                    help="Export konsultasi AI + input dokter saja (Sobatpaws_08)")
    args = ap.parse_args()

    if args.learning_only:
        print("=" * 70)
        print("EXPORT LEARNING DATA -> EXCEL")
        print("Output: %s" % OUT)
        print("=" * 70)
        export_learning_workbook()
        print("=" * 70)
        return

    if not os.path.exists(os.path.join(GEN, "breeds.csv")):
        sys.exit("ERROR: dataset not found. Run: python3 scripts/generate_all.py")

    print("=" * 70)
    print("EXPORT SOBATPAWS DATASET -> EXCEL")
    print("Output: %s" % OUT)
    if args.max_rows:
        print("Row cap per table: %d" % args.max_rows)
    print("=" * 70)

    t0 = time.time()

    # 00 Summary
    summary_df = build_summary()
    readme = pd.DataFrame([
        {"item": "Platform", "value": "Sobatpaws Veterinary ML & AI Data Platform"},
        {"item": "Format", "value": "Excel .xlsx (openpyxl)"},
        {"item": "Source", "value": "data/generated/*.csv"},
        {"item": "Note", "value": "Tabel >1M baris otomatis di-split ke sheet _2, _3, ..."},
        {"item": "Regenerate", "value": "python3 scripts/generate_all.py"},
    ])
    export_workbook("Sobatpaws_00_Summary.xlsx", [],
                      extra_sheets={"README": readme, "Table_Summary": summary_df})

    if args.sample_only:
        export_workbook("Sobatpaws_01_Taxonomy.xlsx",
                        ["animal_categories", "breeds", "breed_variants", "breed_traits"],
                        args.max_rows)
        export_workbook("Sobatpaws_02_Clinical_Masters.xlsx",
                        ["diseases", "symptoms", "diagnostic_methods", "treatments",
                         "products", "disease_symptoms"],
                        args.max_rows)
        print("=" * 70)
        print("Sample export done in %.1fs" % (time.time() - t0))
        return

    export_workbook("Sobatpaws_01_Taxonomy.xlsx",
                    ["animal_categories", "breeds", "breed_variants", "breed_traits"],
                    args.max_rows)
    export_workbook("Sobatpaws_02_Clinical_Masters.xlsx",
                    ["diseases", "symptoms", "diagnostic_methods", "treatments",
                     "products", "disease_symptoms"],
                    args.max_rows)
    export_workbook("Sobatpaws_03_Clinical_Matrix.xlsx",
                    ["breed_clinical_matrix"], args.max_rows)
    export_workbook("Sobatpaws_04_Operational.xlsx",
                    ["organizations", "users", "pet_owners", "pets", "clinical_cases"],
                    args.max_rows)
    export_workbook("Sobatpaws_05_Case_Details.xlsx",
                    ["case_symptoms", "case_diagnoses", "case_treatments"],
                    args.max_rows)
    export_workbook("Sobatpaws_06_ML_AI.xlsx",
                    ["data_sources", "ml_datasets", "dataset_sources",
                     "feature_definitions", "dataset_features", "ml_models",
                     "ml_predictions", "ml_feedback", "ai_providers",
                     "ai_prompt_templates", "ai_conversations", "ai_requests",
                     "ai_suggestions"],
                    args.max_rows)

    # ML views (gzip CSV or parquet)
    mlv_path = os.path.join(OUT, "Sobatpaws_07_ML_Views.xlsx")
    os.makedirs(OUT, exist_ok=True)
    t_mlv = time.time()
    with pd.ExcelWriter(mlv_path, engine="openpyxl") as w:
        n_total = 0
        for gz, sheet in [("ml_view_disease_classification.csv.gz", "disease_classification"),
                            ("ml_view_breed_disease_risk.csv.gz", "breed_disease_risk")]:
            n = write_gzip_csv(w, gz, sheet)
            if n:
                n_total += n
        pq = os.path.join(MLV, "ml_view_disease_classification.parquet")
        if n_total == 0 and os.path.exists(pq):
            pd.read_parquet(pq).to_excel(w, sheet_name="disease_classification", index=False)
            n_total += len(pd.read_parquet(pq))
    if os.path.exists(mlv_path):
        print("  %-40s %8d rows  (%.1fs)" % ("Sobatpaws_07_ML_Views.xlsx", n_total, time.time() - t_mlv))

    export_learning_workbook()

    print("=" * 70)
    print("Export selesai in %.1fs" % (time.time() - t0))
    print("Folder: %s" % OUT)
    for f in sorted(os.listdir(OUT)):
        if f.endswith(".xlsx"):
            mb = os.path.getsize(os.path.join(OUT, f)) / (1024 * 1024)
            print("  %s  (%.1f MB)" % (f, mb))
    print("=" * 70)


if __name__ == "__main__":
    main()
