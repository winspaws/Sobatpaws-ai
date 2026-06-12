#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validator for the generated Sobatpaws dataset.

Single source of truth = dbml/schema.dbml. This tool:
  * parses every Enum from the DBML and checks generated enum-typed columns
    only contain values inside their domain;
  * checks primary-key uniqueness (id column) per table;
  * checks declared unique constraints (slugs, composite matrix key, etc.);
  * checks every foreign key resolves to an existing parent row
    (NULL/empty allowed for nullable columns);
  * checks breed<->category consistency on pets and the matrix;
  * writes manifest.json (sha256 + row_count + header per CSV).

Exit code 0 = all checks pass, 1 = at least one violation (CI-friendly).

Usage:
  python3 scripts/validate_dataset.py
"""
import csv
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "data", "generated"))
SCHEMA = os.path.normpath(os.path.join(HERE, "..", "dbml", "schema.dbml"))

csv.field_size_limit(10_000_000)

# ---------------------------------------------------------------------------
# Table configuration: pk, foreign keys, enum columns, unique constraints.
# fk: (column, ref_table, ref_col, nullable)
# enum: (column, enum_name)
# unique: list of columns (single) or tuples (composite)
# ---------------------------------------------------------------------------
TABLES = {
    "animal_categories": {"pk": "id", "unique": ["slug"]},
    "diseases": {"pk": "id", "unique": ["slug"],
                 "enum": [("etiology", "disease_etiology"), ("body_system", "body_system"),
                          ("default_severity", "severity_level")]},
    "symptoms": {"pk": "id", "unique": ["slug"], "enum": [("body_system", "body_system")]},
    "diagnostic_methods": {"pk": "id", "unique": ["slug"], "enum": [("type", "diagnostic_type")]},
    "treatments": {"pk": "id", "unique": ["slug"], "enum": [("type", "treatment_type")]},
    "products": {"pk": "id", "unique": ["sku"], "enum": [("kind", "product_kind")]},
    "breeds": {"pk": "id", "unique": ["slug"], "enum": [("size_class", "size_class")],
               "fk": [("category_id", "animal_categories", "id", False)]},
    "breed_variants": {"pk": "id", "fk": [("breed_id", "breeds", "id", False)]},
    "breed_traits": {"pk": "id", "fk": [("breed_id", "breeds", "id", False)]},
    "disease_symptoms": {"pk": "id",
                         "fk": [("disease_id", "diseases", "id", False),
                                ("symptom_id", "symptoms", "id", False)],
                         "enum": [("frequency", "risk_level"), ("typical_severity", "severity_level")]},
    "breed_clinical_matrix": {
        "pk": "id",
        "unique": [("breed_id", "disease_id", "diagnostic_method_id", "product_id")],
        "enum": [("risk", "risk_level"), ("severity", "severity_level")],
        "fk": [("category_id", "animal_categories", "id", False),
               ("breed_id", "breeds", "id", False),
               ("variant_id", "breed_variants", "id", True),
               ("disease_id", "diseases", "id", False),
               ("diagnostic_method_id", "diagnostic_methods", "id", False),
               ("treatment_id", "treatments", "id", False),
               ("product_id", "products", "id", True)]},
    "organizations": {"pk": "id", "unique": ["slug"], "enum": [("type", "org_type")]},
    "users": {"pk": "id", "unique": ["email"], "fk": [("org_id", "organizations", "id", True)]},
    "pet_owners": {"pk": "id", "fk": [("org_id", "organizations", "id", True)]},
    "pets": {"pk": "id",
             "fk": [("owner_id", "pet_owners", "id", True), ("org_id", "organizations", "id", True),
                    ("category_id", "animal_categories", "id", False), ("breed_id", "breeds", "id", True)]},
    "clinical_cases": {"pk": "id", "enum": [("status", "case_status")],
                       "fk": [("org_id", "organizations", "id", False),
                              ("pet_id", "pets", "id", False), ("vet_id", "users", "id", True)]},
    "case_symptoms": {"pk": "id", "enum": [("severity", "severity_level")],
                      "fk": [("case_id", "clinical_cases", "id", False),
                             ("symptom_id", "symptoms", "id", False)]},
    "case_diagnoses": {"pk": "id",
                       "fk": [("case_id", "clinical_cases", "id", False),
                              ("disease_id", "diseases", "id", True),
                              ("diagnosed_by", "users", "id", True)]},
    "case_treatments": {"pk": "id",
                        "fk": [("case_id", "clinical_cases", "id", False),
                               ("treatment_id", "treatments", "id", True),
                               ("product_id", "products", "id", True)]},
    "data_sources": {"pk": "id", "enum": [("type", "data_source_type"), ("reliability", "risk_level")],
                     "fk": [("org_id", "organizations", "id", True)]},
    "ml_datasets": {"pk": "id", "enum": [("task_type", "ml_task_type")]},
    "dataset_sources": {"pk": "id",
                        "fk": [("dataset_id", "ml_datasets", "id", False),
                               ("data_source_id", "data_sources", "id", False)]},
    "feature_definitions": {"pk": "id", "unique": ["key"]},
    "dataset_features": {"pk": "id",
                         "fk": [("dataset_id", "ml_datasets", "id", False),
                                ("feature_id", "feature_definitions", "id", False)]},
    "ml_models": {"pk": "id", "enum": [("task_type", "ml_task_type"), ("status", "ml_model_status")],
                  "fk": [("dataset_id", "ml_datasets", "id", True), ("created_by", "users", "id", True)]},
    "ai_providers": {"pk": "id", "enum": [("kind", "ai_provider_kind")]},
    "ai_prompt_templates": {"pk": "id"},
    "ai_conversations": {"pk": "id",
                         "fk": [("org_id", "organizations", "id", True), ("user_id", "users", "id", True),
                                ("case_id", "clinical_cases", "id", True), ("pet_id", "pets", "id", True)]},
    "ai_requests": {"pk": "id", "enum": [("status", "ai_request_status")],
                    "fk": [("conversation_id", "ai_conversations", "id", True),
                           ("provider_id", "ai_providers", "id", False),
                           ("prompt_template_id", "ai_prompt_templates", "id", True)]},
    "ai_suggestions": {"pk": "id",
                       "fk": [("request_id", "ai_requests", "id", True),
                              ("case_id", "clinical_cases", "id", True), ("pet_id", "pets", "id", True)]},
    "ml_predictions": {"pk": "id",
                       "fk": [("model_id", "ml_models", "id", False),
                              ("case_id", "clinical_cases", "id", True), ("pet_id", "pets", "id", True),
                              ("predicted_disease_id", "diseases", "id", True)]},
    "ml_feedback": {"pk": "id", "enum": [("verdict", "feedback_verdict")],
                    "fk": [("prediction_id", "ml_predictions", "id", True),
                           ("ai_suggestion_id", "ai_suggestions", "id", True),
                           ("case_id", "clinical_cases", "id", True),
                           ("reviewer_id", "users", "id", True),
                           ("corrected_disease_id", "diseases", "id", True)]},
}


def parse_enums(path):
    txt = open(path, encoding="utf-8").read()
    enums = {}
    for m in re.finditer(r"Enum\s+(\w+)\s*\{([^}]*)\}", txt):
        name, body = m.group(1), m.group(2)
        vals = set()
        for line in body.splitlines():
            line = re.sub(r"//.*", "", line).strip()
            if line:
                vals.add(line.split()[0])
        enums[name] = vals
    return enums


def path_for(table):
    return os.path.join(OUT_DIR, table + ".csv")


_id_cache = {}


def id_set(table):
    if table in _id_cache:
        return _id_cache[table]
    s = set()
    with open(path_for(table)) as f:
        r = csv.DictReader(f)
        for row in r:
            s.add(row["id"])
    _id_cache[table] = s
    return s


def main():
    if not os.path.exists(path_for("breeds")):
        sys.exit("ERROR: generated dataset not found. Run the generators first.")

    enums = parse_enums(SCHEMA)
    failures = []   # (table, check, detail)
    manifest = {}
    grand = 0

    # Pre-load referenced parent id-sets (lazy, cached).
    for table, cfg in TABLES.items():
        for (_c, ref, _rc, _n) in cfg.get("fk", []):
            id_set(ref)

    for table, cfg in TABLES.items():
        p = path_for(table)
        if not os.path.exists(p):
            failures.append((table, "missing_file", p))
            continue

        pk = cfg.get("pk", "id")
        fks = cfg.get("fk", [])
        enum_cols = cfg.get("enum", [])
        uniques = cfg.get("unique", [])

        parents = {ref: id_set(ref) for (_c, ref, _rc, _n) in fks}
        enum_domains = []
        for col, ename in enum_cols:
            if ename not in enums:
                failures.append((table, "unknown_enum", ename))
            else:
                enum_domains.append((col, ename, enums[ename]))

        pk_seen = set()
        uniq_seen = {tuple(u) if isinstance(u, tuple) else (u,): set() for u in uniques}
        counts = {"pk_dup": 0, "fk": 0, "enum": 0, "unique": 0, "rows": 0}
        samples = {}
        sha = hashlib.sha256()
        header = None

        with open(p, "rb") as fb:
            for chunk in iter(lambda: fb.read(1 << 20), b""):
                sha.update(chunk)

        with open(p, newline="") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            for row in reader:
                counts["rows"] += 1
                # PK uniqueness
                v = row.get(pk, "")
                if v in pk_seen:
                    counts["pk_dup"] += 1
                    samples.setdefault("pk_dup", v)
                else:
                    pk_seen.add(v)
                # FK
                for (col, ref, _rc, nullable) in fks:
                    val = row.get(col, "")
                    if val == "" or val is None:
                        if not nullable:
                            counts["fk"] += 1
                            samples.setdefault("fk", "%s empty (not null)" % col)
                        continue
                    if val not in parents[ref]:
                        counts["fk"] += 1
                        samples.setdefault("fk", "%s=%s not in %s" % (col, val, ref))
                # enum domain
                for (col, ename, domain) in enum_domains:
                    val = row.get(col, "")
                    if val and val not in domain:
                        counts["enum"] += 1
                        samples.setdefault("enum", "%s=%s not in %s" % (col, val, ename))
                # unique constraints
                for u in uniques:
                    cols = u if isinstance(u, tuple) else (u,)
                    key = tuple(row.get(c, "") for c in cols)
                    bag = uniq_seen[cols]
                    if key in bag:
                        counts["unique"] += 1
                        samples.setdefault("unique:%s" % str(cols), str(key))
                    else:
                        bag.add(key)

        grand += counts["rows"]
        manifest[table] = {"rows": counts["rows"], "sha256": sha.hexdigest(),
                           "header": header}

        for kind in ("pk_dup", "fk", "enum", "unique"):
            if counts[kind]:
                failures.append((table, kind, "%d violations (e.g. %s)"
                                 % (counts[kind], samples.get(kind) or
                                    next((v for k, v in samples.items() if k.startswith(kind)), "?"))))

    # breed <-> category consistency (pets & matrix)
    breed_cat = {}
    with open(path_for("breeds")) as f:
        for r in csv.DictReader(f):
            breed_cat[r["id"]] = r["category_id"]
    for tbl in ("pets", "breed_clinical_matrix"):
        bad = 0
        with open(path_for(tbl)) as f:
            for r in csv.DictReader(f):
                b = r.get("breed_id", "")
                if b and breed_cat.get(b) != r.get("category_id"):
                    bad += 1
        if bad:
            failures.append((tbl, "breed_category_mismatch", "%d rows" % bad))

    manifest_meta = {"grand_total_rows": grand, "tables": manifest}
    with open(os.path.join(OUT_DIR, "manifest.json"), "w") as f:
        json.dump(manifest_meta, f, indent=2)

    # ---- report ----
    print("=" * 70)
    print("SOBATPAWS DATASET VALIDATION")
    print("=" * 70)
    print("Enums parsed from schema.dbml: %d" % len(enums))
    print("Tables validated            : %d" % len(TABLES))
    print("Grand total rows            : %d" % grand)
    print("-" * 70)
    if not failures:
        print("RESULT: PASS  — all PK / FK / unique / enum-domain checks clean.")
        print("Manifest written: data/generated/manifest.json")
        print("=" * 70)
        return 0
    print("RESULT: FAIL — %d issue group(s):" % len(failures))
    for tbl, kind, detail in failures:
        print("  [%s] %s: %s" % (tbl, kind, detail))
    print("=" * 70)
    return 1


if __name__ == "__main__":
    sys.exit(main())
