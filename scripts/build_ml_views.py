#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build flat, ML-ready training views from the generated relational dataset.

The relational tables are great for storage/integrity but ML pipelines want
denormalized feature tables. This joins the generated CSVs into:

  ml_view_disease_classification : one row per clinical_case, with pet/breed
        features + the CONFIRMED diagnosis as label (task: disease_classification
        / symptom_to_disease / triage_severity).
  ml_view_breed_disease_risk     : one row per (breed, disease) from the
        clinical matrix with risk/prevalence/hereditary flags (task:
        risk_prediction / breed susceptibility lookup).

Output goes to data/ml_views/. Writes Parquet when pyarrow is available,
otherwise falls back to gzip-compressed CSV (pure stdlib) so it always runs.

Usage:
  python3 scripts/build_ml_views.py
"""
import csv
import datetime as dt
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.normpath(os.path.join(HERE, "..", "data", "generated"))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "ml_views"))

csv.field_size_limit(10_000_000)

try:
    import pyarrow as pa  # noqa
    import pyarrow.parquet as pq  # noqa
    HAVE_PARQUET = True
except Exception:
    HAVE_PARQUET = False


def g(name):
    return os.path.join(GEN, name)


def parse_date(s):
    if not s:
        return None
    s = s.split(" ")[0]
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        return None


class Sink:
    """Collects rows and writes Parquet (if available) else gzip-CSV."""

    def __init__(self, name, header):
        self.name = name
        self.header = header
        self.rows = []

    def add(self, row):
        self.rows.append(row)

    def flush(self):
        os.makedirs(OUT, exist_ok=True)
        if HAVE_PARQUET:
            cols = {h: [] for h in self.header}
            for r in self.rows:
                for h, v in zip(self.header, r):
                    cols[h].append(v)
            table = pa.table(cols)
            path = os.path.join(OUT, self.name + ".parquet")
            pq.write_table(table, path, compression="snappy")
            return path, len(self.rows)
        path = os.path.join(OUT, self.name + ".csv.gz")
        with gzip.open(path, "wt", newline="") as f:
            w = csv.writer(f)
            w.writerow(self.header)
            w.writerows(self.rows)
        return path, len(self.rows)


def build_disease_classification():
    # --- load lookups ---
    cat_slug = {}
    with open(g("animal_categories.csv")) as f:
        for r in csv.DictReader(f):
            cat_slug[r["id"]] = r["slug"]

    breeds = {}
    with open(g("breeds.csv")) as f:
        for r in csv.DictReader(f):
            breeds[r["id"]] = (r["name"], r["size_class"], r["origin_country"],
                               r["lifespan_years_min"], r["lifespan_years_max"])

    diseases = {}
    with open(g("diseases.csv")) as f:
        for r in csv.DictReader(f):
            diseases[r["id"]] = (r["slug"], r["etiology"], r["body_system"],
                                 r["default_severity"], r["is_emergency"])

    pets = {}
    with open(g("pets.csv")) as f:
        for r in csv.DictReader(f):
            pets[r["id"]] = (r["breed_id"], r["category_id"], r["sex"],
                             r["is_neutered"], r["birth_date"], r["weight_kg"])

    # confirmed diagnosis per case
    case_label = {}
    with open(g("case_diagnoses.csv")) as f:
        for r in csv.DictReader(f):
            if r["is_confirmed"] == "true":
                case_label[r["case_id"]] = r["disease_id"]

    # symptom count per case
    sym_count = {}
    with open(g("case_symptoms.csv")) as f:
        for r in csv.DictReader(f):
            sym_count[r["case_id"]] = sym_count.get(r["case_id"], 0) + 1

    header = ["case_id", "category_id", "category_slug", "breed_id", "breed_name",
              "size_class", "origin_country", "lifespan_years_min", "lifespan_years_max",
              "sex", "is_neutered", "age_years", "weight_kg", "temperature_c",
              "heart_rate", "resp_rate", "symptom_count", "case_status",
              "label_disease_id", "label_disease_slug", "label_etiology",
              "label_body_system", "label_severity", "label_is_emergency"]
    sink = Sink("ml_view_disease_classification", header)

    skipped = 0
    with open(g("clinical_cases.csv")) as f:
        for r in csv.DictReader(f):
            cid_case = r["id"]
            label = case_label.get(cid_case)
            pet = pets.get(r["pet_id"])
            if label is None or pet is None or label not in diseases:
                skipped += 1
                continue
            breed_id, category_id, sex, neutered, birth, weight = pet
            bn, size_class, origin, lmin, lmax = breeds.get(breed_id, ("", "", "", "", ""))
            dslug, det, dbs, dsev, demg = diseases[label]
            # age at visit
            bd = parse_date(birth)
            vd = parse_date(r["visit_date"])
            if bd and vd:
                age = max(0.0, round((vd - bd).days / 365.25, 2))
            else:
                age = ""
            sink.add([cid_case, category_id, cat_slug.get(category_id, ""), breed_id, bn,
                      size_class, origin, lmin, lmax, sex, neutered, age, weight,
                      r["temperature_c"], r["heart_rate"], r["resp_rate"],
                      sym_count.get(cid_case, 0), r["status"], label, dslug, det,
                      dbs, dsev, demg])
    return sink, skipped


def build_breed_disease_risk():
    header = ["breed_id", "category_id", "disease_id", "risk", "severity",
              "prevalence_pct", "is_hereditary"]
    sink = Sink("ml_view_breed_disease_risk", header)
    seen = set()
    with open(g("breed_clinical_matrix.csv")) as f:
        for r in csv.DictReader(f):
            key = (r["breed_id"], r["disease_id"])
            if key in seen:
                continue
            seen.add(key)
            sink.add([r["breed_id"], r["category_id"], r["disease_id"], r["risk"],
                      r["severity"], r["prevalence_pct"], r["is_hereditary"]])
    return sink


def build_symptom_disease_cases():
    """Satu baris per kasus: gejala + label penyakit terkonfirmasi (ML train bridge)."""
    cat_slug = {}
    with open(g("animal_categories.csv")) as f:
        for r in csv.DictReader(f):
            cat_slug[r["id"]] = r["slug"]

    diseases = {}
    with open(g("diseases.csv")) as f:
        for r in csv.DictReader(f):
            diseases[r["id"]] = (r["slug"], r.get("name_id") or r["slug"])

    symptom_name = {}
    with open(g("symptoms.csv")) as f:
        for r in csv.DictReader(f):
            symptom_name[r["id"]] = r.get("name_id") or r.get("name") or r["slug"]

    pets = {}
    with open(g("pets.csv")) as f:
        for r in csv.DictReader(f):
            pets[r["id"]] = cat_slug.get(r["category_id"], "")

    case_label = {}
    with open(g("case_diagnoses.csv")) as f:
        for r in csv.DictReader(f):
            if r["is_confirmed"] == "true":
                case_label[r["case_id"]] = r["disease_id"]

    case_symptoms = {}
    with open(g("case_symptoms.csv")) as f:
        for r in csv.DictReader(f):
            cid = r["case_id"]
            sid = symptom_name.get(r["symptom_id"])
            if sid:
                case_symptoms.setdefault(cid, []).append(sid)

    case_pet = {}
    with open(g("clinical_cases.csv")) as f:
        for r in csv.DictReader(f):
            case_pet[r["id"]] = r["pet_id"]

    header = ["case_id", "category_slug", "disease_slug", "disease_name_id",
              "symptom_count", "symptoms_json"]
    sink = Sink("ml_view_symptom_disease_cases", header)
    skipped = 0
    for case_id, disease_id in case_label.items():
        pet_id = case_pet.get(case_id)
        if not pet_id:
            skipped += 1
            continue
        cat = pets.get(pet_id, "")
        meta = diseases.get(disease_id)
        symptoms = case_symptoms.get(case_id, [])
        if not meta or not symptoms:
            skipped += 1
            continue
        dslug, dname = meta
        sink.add([case_id, cat, dslug, dname, len(symptoms),
                  json.dumps(symptoms, ensure_ascii=False)])
    return sink, skipped


def main():
    if not os.path.exists(g("clinical_cases.csv")):
        sys.exit("ERROR: run the generators first (clinical_cases.csv missing).")

    print("=" * 64)
    print("BUILD ML VIEWS  (format: %s)" % ("Parquet/snappy" if HAVE_PARQUET
                                            else "gzip-CSV fallback — pip install pyarrow for Parquet"))
    print("=" * 64)

    dc_sink, skipped = build_disease_classification()
    p1, n1 = dc_sink.flush()
    print("  disease_classification : %8d rows  -> %s" % (n1, os.path.basename(p1)))
    print("                           (%d cases skipped: no confirmed label)" % skipped)

    risk_sink = build_breed_disease_risk()
    p2, n2 = risk_sink.flush()
    print("  breed_disease_risk     : %8d rows  -> %s" % (n2, os.path.basename(p2)))

    sym_sink, sym_skipped = build_symptom_disease_cases()
    p3, n3 = sym_sink.flush()
    print("  symptom_disease_cases  : %8d rows  -> %s" % (n3, os.path.basename(p3)))
    print("                           (%d cases skipped: no label/symptoms)" % sym_skipped)
    print("=" * 64)
    print("Output dir: %s" % OUT)


if __name__ == "__main__":
    main()
