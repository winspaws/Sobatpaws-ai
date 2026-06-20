#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sobatpaws data-generation pipeline.

Expands the curated seed catalogs (scripts/catalogs.py) into a large,
schema-conformant dataset for the Sobatpaws DBML model and writes it to
data/generated/ as CSV, ready to bulk-load into PostgreSQL.

Outputs (data/generated/):
  animal_categories.csv
  breeds.csv
  breed_variants.csv
  breed_traits.csv
  diseases.csv
  diagnostic_methods.csv
  treatments.csv
  products.csv
  breed_clinical_matrix.csv      <- the ~580k-row relational matrix
  load.sql                       <- Postgres \copy loader
  summary.json                   <- per-table + per-category row counts

Deterministic: re-running produces identical output (no randomness).

Usage:
  python3 scripts/generate_dataset.py
  python3 scripts/generate_dataset.py --scale 0.05   # 5% sample for quick tests
"""
import argparse
import csv
import itertools
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import catalogs as C  # noqa: E402

OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "data", "generated"))

_slug_re = re.compile(r"[^a-z0-9]+")


def slugify(text):
    s = _slug_re.sub("-", text.lower()).strip("-")
    return s or "x"


def iter_modifiers(mod):
    """Yield modifier combinations as lists of (token, variant_type)."""
    if mod["mode"] == "combo":
        pool = sorted(mod["pool"])
        vt = mod["variant_type"]
        for r in range(1, mod["max_r"] + 1):
            for combo in itertools.combinations(pool, r):
                yield [(tok, vt) for tok in combo]
    elif mod["mode"] == "product":
        axes = mod["axes"]
        pools = [sorted(a["pool"]) for a in axes]
        vts = [a["variant_type"] for a in axes]
        for combo in itertools.product(*pools):
            yield [(combo[i], vts[i]) for i in range(len(combo))]
    else:
        raise ValueError("unknown mod mode: %s" % mod["mode"])


def expand_category(cat_slug, bases, target):
    """Round-robin across bases, slicing to `target` leaf taxa.

    Returns list of leaf dicts: {base, tokens:[(tok,vt)], name}.
    """
    gens = [(base, iter_modifiers(base["mod"])) for base in bases]
    leaves = []
    exhausted = set()
    while len(leaves) < target and len(exhausted) < len(gens):
        for idx, (base, gen) in enumerate(gens):
            if idx in exhausted:
                continue
            try:
                tokens = next(gen)
            except StopIteration:
                exhausted.add(idx)
                continue
            suffix = " ".join(tok for tok, _ in tokens)
            leaves.append({
                "base": base,
                "tokens": tokens,
                "name": (base["name"] + " " + suffix).strip(),
            })
            if len(leaves) >= target:
                break
    return leaves


def build_clinical_masters():
    """Assign stable ids to diseases, diagnostics, treatments, products."""
    diseases, diagnostics, treatments, products = {}, {}, {}, {}

    def ensure(d, key, value):
        if key not in d:
            d[key] = {"id": len(d) + 1, "value": value}
        return d[key]["id"]

    for cat_slug, pool in C.CLINICAL.items():
        for dis in pool:
            ensure(diseases, dis["slug"], dis)
            for dx in dis["diagnostics"]:
                ensure(diagnostics, dx[0], dx)
            tx = dis["treatment"]
            ensure(treatments, tx[0], tx)
            for pr in dis["products"]:
                ensure(products, pr[0], pr)
    return diseases, diagnostics, treatments, products


def write_clinical_relations(dis_m, dx_id, tx_id):
    """Export symptoms, disease_symptoms, disease_diagnostics, disease_treatments."""
    symptoms = {}
    dsym_rows = []
    ddx_rows = []
    dtx_rows = []
    dsym_id = ddx_id = dtx_id = 0

    def ensure_symptom(sym):
        key = sym["slug"]
        if key not in symptoms:
            symptoms[key] = {
                "id": len(symptoms) + 1,
                "slug": sym["slug"],
                "name": sym.get("name", sym["name_id"]),
                "name_id": sym["name_id"],
                "body_system": sym["body_system"],
                "is_red_flag": bool(sym.get("is_red_flag", False)),
            }
        return symptoms[key]["id"]

    for v in sorted(dis_m.values(), key=lambda x: x["id"]):
        d = v["value"]
        d_id = v["id"]
        for sym in d.get("symptoms", []):
            sid = ensure_symptom(sym)
            dsym_id += 1
            sev = "moderate"
            if d["severity"] in ("severe", "critical"):
                sev = "severe"
            elif d["severity"] == "mild":
                sev = "mild"
            dsym_rows.append([dsym_id, d_id, sid,
                              sym.get("frequency", "high"), sev])
        for i, dx in enumerate(d.get("diagnostics", [])):
            ddx_id += 1
            ddx_rows.append([ddx_id, d_id, dx_id[dx[0]],
                             "true" if i == 0 else "false", i + 1, ""])
        dtx_id += 1
        dtx_rows.append([dtx_id, d_id, tx_id[d["treatment"][0]], 1,
                         d["severity"], "", d["treatment"][1]])

    with open(os.path.join(OUT_DIR, "symptoms.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "slug", "name", "name_id", "body_system", "is_red_flag"])
        for s in sorted(symptoms.values(), key=lambda x: x["id"]):
            w.writerow([s["id"], s["slug"], s["name"], s["name_id"],
                        s["body_system"], str(s["is_red_flag"]).lower()])

    with open(os.path.join(OUT_DIR, "disease_symptoms.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "disease_id", "symptom_id", "frequency", "typical_severity"])
        for row in dsym_rows:
            w.writerow(row)

    with open(os.path.join(OUT_DIR, "disease_diagnostics.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "disease_id", "diagnostic_method_id", "is_gold_standard",
                    "step_order", "expected_finding"])
        for row in ddx_rows:
            w.writerow(row)

    with open(os.path.join(OUT_DIR, "disease_treatments.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "disease_id", "treatment_id", "line_of_therapy",
                    "severity_target", "efficacy_note", "recommendation"])
        for row in dtx_rows:
            w.writerow(row)

    return len(symptoms), len(dsym_rows), len(ddx_rows), len(dtx_rows)


def num(v):
    return "" if v is None else v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0,
                    help="scale factor for targets (e.g. 0.05 for a quick sample)")
    ap.add_argument("--taxonomy", choices=["default", "large"], default="default",
                    help="default ~1.1k ras (300k total); large ~29k ras (jutaan baris)")
    args = ap.parse_args()
    targets = C.TARGETS_LARGE if args.taxonomy == "large" else C.TARGETS

    os.makedirs(OUT_DIR, exist_ok=True)

    dis_m, dx_m, tx_m, pr_m = build_clinical_masters()
    dx_id = {k: v["id"] for k, v in dx_m.items()}
    tx_id = {k: v["id"] for k, v in tx_m.items()}
    pr_id = {k: v["id"] for k, v in pr_m.items()}
    dis_id = {k: v["id"] for k, v in dis_m.items()}

    # ---- Write master clinical tables ----
    with open(os.path.join(OUT_DIR, "diagnostic_methods.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "slug", "name", "name_id", "type"])
        for k, v in sorted(dx_m.items(), key=lambda kv: kv[1]["id"]):
            s, n, nid, t = v["value"]
            w.writerow([v["id"], s, n, nid, t])

    with open(os.path.join(OUT_DIR, "treatments.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "slug", "name", "name_id", "type", "requires_vet"])
        for k, v in sorted(tx_m.items(), key=lambda kv: kv[1]["id"]):
            s, n, nid, t = v["value"]
            w.writerow([v["id"], s, n, nid, t, "true"])

    with open(os.path.join(OUT_DIR, "products.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "sku", "name", "brand", "kind", "active_ingredient", "form"])
        for k, v in sorted(pr_m.items(), key=lambda kv: kv[1]["id"]):
            sku, n, brand, kind, ai, form = v["value"]
            w.writerow([v["id"], sku, n, brand, kind, ai, form])

    with open(os.path.join(OUT_DIR, "diseases.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "slug", "name", "name_id", "etiology", "body_system",
                    "default_severity", "is_contagious", "is_zoonotic", "is_emergency"])
        for k, v in sorted(dis_m.items(), key=lambda kv: kv[1]["id"]):
            d = v["value"]
            w.writerow([v["id"], d["slug"], d["name"], d["name_id"], d["etiology"],
                        d["body_system"], d["severity"],
                        str(d["contagious"]).lower(), str(d["zoonotic"]).lower(),
                        str(d["emergency"]).lower()])

    n_sym, n_dsym, n_ddx, n_dtx = write_clinical_relations(dis_m, dx_id, tx_id)

    # ---- Categories (mirror data/categories.json ids) ----
    with open(os.path.join(OUT_DIR, "animal_categories.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "slug"])
        for slug, cid in sorted(C.CATEGORY_IDS.items(), key=lambda kv: kv[1]):
            w.writerow([cid, slug])

    # ---- Expand taxa + emit breeds/variants/traits + matrix ----
    breeds_f = open(os.path.join(OUT_DIR, "breeds.csv"), "w", newline="")
    variants_f = open(os.path.join(OUT_DIR, "breed_variants.csv"), "w", newline="")
    traits_f = open(os.path.join(OUT_DIR, "breed_traits.csv"), "w", newline="")
    matrix_f = open(os.path.join(OUT_DIR, "breed_clinical_matrix.csv"), "w", newline="")

    bw = csv.writer(breeds_f)
    vw = csv.writer(variants_f)
    tw = csv.writer(traits_f)
    mw = csv.writer(matrix_f)

    bw.writerow(["id", "category_id", "slug", "name", "name_id", "origin_country",
                 "size_class", "weight_kg_min", "weight_kg_max", "height_cm_min",
                 "height_cm_max", "lifespan_years_min", "lifespan_years_max",
                 "temperament", "coat_type", "care_level"])
    vw.writerow(["id", "breed_id", "name", "variant_type", "is_recognized"])
    tw.writerow(["id", "breed_id", "trait_key", "trait_value"])
    mw.writerow(["id", "category_id", "breed_id", "variant_id", "disease_id",
                 "diagnostic_method_id", "treatment_id", "product_id", "risk",
                 "severity", "is_gold_standard_dx", "line_of_therapy",
                 "prevalence_pct", "is_hereditary"])

    breed_id = 0
    variant_id = 0
    trait_id = 0
    matrix_id = 0
    per_cat_counts = {}
    used_slugs = set()

    DPT = C.DISEASES_PER_TAXON
    DXP = C.DIAGNOSTICS_PER_DISEASE
    PRP = C.PRODUCTS_PER_DISEASE

    for cat_slug in sorted(targets.keys()):
        bases = C.TAXA.get(cat_slug, [])
        if not bases:
            continue
        cid = C.CATEGORY_IDS[cat_slug]
        target = max(1, int(round(targets[cat_slug] * args.scale)))
        leaves = expand_category(cat_slug, bases, target)
        per_cat_counts[cat_slug] = len(leaves)

        clinical_pool = C.CLINICAL.get(cat_slug, [])
        pool_len = len(clinical_pool)

        for leaf_idx, leaf in enumerate(leaves):
            base = leaf["base"]
            breed_id += 1
            slug = "%s-%s" % (cat_slug, slugify(leaf["name"]))
            if slug in used_slugs:
                slug = "%s-%d" % (slug, breed_id)
            used_slugs.add(slug)

            wmin, wmax = base["weight"]
            hmin, hmax = (base["height"] if base["height"] else ("", ""))
            lmin, lmax = base["lifespan"]
            bw.writerow([breed_id, cid, slug, leaf["name"], leaf["name"], base["origin"],
                         base["size_class"], wmin, wmax, num(hmin), num(hmax),
                         lmin, lmax, base["temperament"], base["coat_type"],
                         base["care_level"]])

            first_variant_id = ""
            for tok, vt in leaf["tokens"]:
                variant_id += 1
                if first_variant_id == "":
                    first_variant_id = variant_id
                vw.writerow([variant_id, breed_id, tok, vt, "true"])

            for tkey, tval in base["traits"]:
                trait_id += 1
                tw.writerow([trait_id, breed_id, tkey, tval])

            # ---- medical matrix fan-out ----
            if pool_len == 0:
                continue
            for k in range(DPT):
                dis = clinical_pool[(leaf_idx + k) % pool_len]
                d_id = dis_id[dis["slug"]]
                t_id = tx_id[dis["treatment"][0]]
                is_hered = "true" if dis["etiology"] == "genetic_congenital" else "false"
                prev = num(dis.get("prevalence"))
                dxs = dis["diagnostics"][:DXP]
                prs = dis["products"][:PRP]
                for di, dx in enumerate(dxs):
                    for pr in prs:
                        matrix_id += 1
                        mw.writerow([
                            matrix_id, cid, breed_id, first_variant_id, d_id,
                            dx_id[dx[0]], t_id, pr_id[pr[0]], dis["risk"],
                            dis["severity"], "true" if di == 0 else "false",
                            1, prev, is_hered,
                        ])

    for fh in (breeds_f, variants_f, traits_f, matrix_f):
        fh.close()

    # ---- load.sql ----
    tables = [
        "animal_categories", "diseases", "symptoms", "diagnostic_methods", "treatments",
        "products", "disease_symptoms", "disease_diagnostics", "disease_treatments",
        "breeds", "breed_variants", "breed_traits", "breed_clinical_matrix",
    ]
    with open(os.path.join(OUT_DIR, "load.sql"), "w") as f:
        f.write("-- Bulk loader for Sobatpaws generated dataset (PostgreSQL).\n")
        f.write("-- Prereq: schema created via `dbml2sql dbml/schema.dbml --postgres`.\n")
        f.write("-- Run from the data/generated/ directory: psql -d sobatpaws -f load.sql\n")
        f.write("BEGIN;\n")
        for t in tables:
            # Only load the columns we generated; others use table defaults.
            with open(os.path.join(OUT_DIR, t + ".csv")) as cf:
                header = cf.readline().strip()
            f.write("\\copy %s(%s) FROM '%s.csv' WITH (FORMAT csv, HEADER true);\n"
                    % (t, header, t))
        f.write("COMMIT;\n")

    # ---- summary ----
    def count_rows(name):
        with open(os.path.join(OUT_DIR, name)) as cf:
            return sum(1 for _ in cf) - 1

    summary = {
        "scale": args.scale,
        "tables": {t: count_rows(t + ".csv") for t in tables},
        "per_category_taxa": per_cat_counts,
        "totals": {
            "master_taxa_breeds": breed_id,
            "breed_variants": variant_id,
            "relational_matrix_rows": matrix_id,
        },
        "fanout_per_taxon": DPT * DXP * PRP,
    }
    with open(os.path.join(OUT_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # ---- report ----
    print("=" * 64)
    print("SOBATPAWS DATASET GENERATION  (scale=%.3f)" % args.scale)
    print("=" * 64)
    print("Master taxa (breeds) by category:")
    for cat in sorted(per_cat_counts):
        print("  %-12s %8d" % (cat, per_cat_counts[cat]))
    print("-" * 64)
    print("  %-12s %8d" % ("TOTAL TAXA", breed_id))
    print("  %-12s %8d" % ("variants", variant_id))
    print("  %-12s %8d" % ("traits", trait_id))
    print("=" * 64)
    print("Clinical masters: %d diseases, %d symptoms, %d disease_symptoms,"
          % (len(dis_m), n_sym, n_dsym))
    print("  %d diagnostics, %d disease_diagnostics, %d treatments, %d disease_treatments,"
          % (len(dx_m), n_ddx, len(tx_m), n_dtx))
    print("  %d products" % len(pr_m))
    print("Fan-out per taxon: %d diseases x %d dx x %d products = %d rows"
          % (DPT, DXP, PRP, DPT * DXP * PRP))
    print("=" * 64)
    print("RELATIONAL MATRIX ROWS: %d" % matrix_id)
    print("=" * 64)
    print("Output written to: %s" % OUT_DIR)


if __name__ == "__main__":
    main()
