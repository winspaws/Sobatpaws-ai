"""Generator seed SQL (PostgreSQL) dari knowledge base JSON -> seed/seed.sql.

Menghasilkan INSERT untuk tabel taxonomy & clinical sesuai dbml/schema.dbml:
animal_categories, breeds, breed_variants, breed_traits, diseases,
disease_species, breed_disease_susceptibility, symptoms, disease_symptoms,
diagnostic_methods, disease_diagnostics, treatments, disease_treatments,
products, treatment_products.

Jalankan:
    python -m ekosistem_satwa.seed_generator
    psql "$DATABASE_URL" -f seed/seed.sql      # untuk memuat
"""
from __future__ import annotations

from .config import SEED_DIR
from .data_loader import KnowledgeBase, load_knowledge_base


def q(val) -> str:
    """Quote nilai untuk SQL (None -> NULL)."""
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float)):
        return str(val)
    return "'" + str(val).replace("'", "''") + "'"


class IdRegistry:
    """Penomor ID deterministik per tabel + map slug/name -> id."""

    def __init__(self):
        self._counters: dict[str, int] = {}
        self.maps: dict[str, dict] = {}

    def next(self, table: str) -> int:
        self._counters[table] = self._counters.get(table, 0) + 1
        return self._counters[table]

    def get_or_create(self, table: str, key: str) -> tuple[int, bool]:
        m = self.maps.setdefault(table, {})
        if key in m:
            return m[key], False
        m[key] = self.next(table)
        return m[key], True


def generate_sql(kb: KnowledgeBase | None = None) -> str:
    kb = kb or load_knowledge_base()
    ids = IdRegistry()
    out: list[str] = []
    out.append("-- Ekosistem Satwa seed data (auto-generated). Jangan edit manual.")
    out.append("BEGIN;")

    # ---- animal_categories ----
    out.append("\n-- animal_categories")
    for c in kb.categories:
        cid, _ = ids.get_or_create("animal_categories", c["slug"])
        out.append(
            "INSERT INTO animal_categories (id, slug, name, name_id, species_class, "
            "scientific_name, description, avg_lifespan_years_min, avg_lifespan_years_max) "
            f"VALUES ({cid}, {q(c['slug'])}, {q(c['name'])}, {q(c['name_id'])}, "
            f"{q(c['species_class'])}, {q(c.get('scientific_name'))}, {q(c.get('description'))}, "
            f"{q(c.get('avg_lifespan_years_min'))}, {q(c.get('avg_lifespan_years_max'))});"
        )

    # ---- breeds + variants + traits ----
    out.append("\n-- breeds, breed_variants, breed_traits")
    for b in kb.breeds:
        cid = ids.maps["animal_categories"].get(b["category_slug"])
        if cid is None:
            continue
        bid, _ = ids.get_or_create("breeds", b["slug"])
        breed_name = b.get("name") or b.get("common_name")
        out.append(
            "INSERT INTO breeds (id, category_id, slug, name, name_id, origin_country, "
            "size_class, weight_kg_min, weight_kg_max, height_cm_min, height_cm_max, "
            "lifespan_years_min, lifespan_years_max, temperament, coat_type, care_level, description) "
            f"VALUES ({bid}, {cid}, {q(b['slug'])}, {q(breed_name)}, {q(b.get('name_id'))}, "
            f"{q(b.get('origin_country'))}, {q(b.get('size_class'))}, {q(b.get('weight_kg_min'))}, "
            f"{q(b.get('weight_kg_max'))}, {q(b.get('height_cm_min'))}, {q(b.get('height_cm_max'))}, "
            f"{q(b.get('lifespan_years_min'))}, {q(b.get('lifespan_years_max'))}, "
            f"{q(b.get('temperament'))}, {q(b.get('coat_type'))}, {q(b.get('care_level'))}, "
            f"{q(b.get('description'))});"
        )
        for v in b.get("variants", []):
            vid = ids.next("breed_variants")
            out.append(
                "INSERT INTO breed_variants (id, breed_id, name, variant_type, hex_color, is_recognized) "
                f"VALUES ({vid}, {bid}, {q(v['name'])}, {q(v.get('variant_type'))}, "
                f"{q(v.get('hex_color'))}, {q(v.get('is_recognized', True))});"
            )
        for t in b.get("traits", []):
            tid = ids.next("breed_traits")
            out.append(
                "INSERT INTO breed_traits (id, breed_id, trait_key, trait_value, numeric_value, unit) "
                f"VALUES ({tid}, {bid}, {q(t['trait_key'])}, {q(t.get('trait_value'))}, "
                f"{q(t.get('numeric_value'))}, {q(t.get('unit'))});"
            )

    # ---- diseases + relasi ----
    out.append("\n-- diseases & relations")
    diag_methods: dict[str, int] = {}
    treatments: dict[str, int] = {}
    products: dict[str, int] = {}
    symptoms: dict[str, int] = {}

    for d in kb.diseases:
        did, is_new = ids.get_or_create("diseases", d["slug"])
        disease_name = d.get("name") or d.get("common_name")
        body_sys = d.get("body_system") or "systemic"
        severity = d.get("default_severity")
        # Map severity to valid enum values
        sev_map = {"high": "severe", "low": "mild", "very_low": "mild", "very_high": "critical"}
        if severity in sev_map:
            severity = sev_map[severity]
        if is_new:
            out.append(
                "INSERT INTO diseases (id, slug, name, name_id, etiology, body_system, "
                "is_contagious, is_zoonotic, default_severity, overview, causes, prevention, "
                "prognosis, is_emergency) "
                f"VALUES ({did}, {q(d['slug'])}, {q(disease_name)}, {q(d.get('name_id'))}, "
                f"{q(d['etiology'])}, {q(body_sys)}, {q(d.get('is_contagious', False))}, "
                f"{q(d.get('is_zoonotic', False))}, {q(severity)}, "
                f"{q(d.get('overview'))}, {q(d.get('causes'))}, {q(d.get('prevention'))}, "
                f"{q(d.get('prognosis'))}, {q(d.get('is_emergency', False))});"
            )
            # disease_species
            cid = ids.maps["animal_categories"].get(d.get("category_slug"))
            if cid:
                dsid = ids.next("disease_species")
                out.append(
                    "INSERT INTO disease_species (id, disease_id, category_id) "
                    f"VALUES ({dsid}, {did}, {cid});"
                )

        # breed_disease_susceptibility
        for s in d.get("breed_susceptibility", []):
            bid = ids.maps["breeds"].get(s.get("breed_slug"))
            if not bid:
                continue
            sid = ids.next("breed_disease_susceptibility")
            out.append(
                "INSERT INTO breed_disease_susceptibility (id, breed_id, disease_id, risk, "
                "prevalence_pct, is_hereditary, age_onset, notes) "
                f"VALUES ({sid}, {bid}, {did}, {q(s['risk'])}, {q(s.get('prevalence_pct'))}, "
                f"{q(s.get('is_hereditary', False))}, {q(s.get('age_onset'))}, {q(s.get('notes'))});"
            )

        # symptoms + disease_symptoms
        for sym in d.get("symptoms", []):
            key = sym.get("name") or sym.get("name_id")
            slug = (key or "").lower().replace(" ", "-")[:150]
            sym_id, new_sym = ids.get_or_create("symptoms", slug)
            if new_sym:
                sym_bs = sym.get("body_system")
                # Normalize body_system to valid enum
                bs_map = {
                    "oral": "dental", "mulut": "dental", "gigi": "dental",
                    "kulit": "integumentary", "skin": "integumentary",
                    "pencernaan": "digestive", "pernapasan": "respiratory",
                    "syaraf": "nervous", "saraf": "nervous", "neurological": "nervous",
                    "muskuloskeletal": "musculoskeletal", "tulang": "musculoskeletal",
                    "endokrin": "endocrine", "hormon": "endocrine",
                    "mata": "ophthalmic", "telinga": "auditory",
                    "darah": "hematologic", "kekebalan": "immune",
                    "perilaku": "behavioral", "perkemihan": "urinary",
                    "reproduksi": "reproductive", "kardiovaskular": "cardiovascular",
                }
                if sym_bs and sym_bs.lower() in bs_map:
                    sym_bs = bs_map[sym_bs.lower()]
                out.append(
                    "INSERT INTO symptoms (id, slug, name, name_id, body_system, is_red_flag) "
                    f"VALUES ({sym_id}, {q(slug)}, {q(sym.get('name'))}, {q(sym.get('name_id'))}, "
                    f"{q(sym_bs)}, {q(sym.get('is_red_flag', False))});"
                )
            link = ids.next("disease_symptoms")
            out.append(
                "INSERT INTO disease_symptoms (id, disease_id, symptom_id, frequency, "
                "is_pathognomonic) "
                f"VALUES ({link}, {did}, {sym_id}, {q(sym.get('frequency'))}, "
                f"{q(sym.get('is_pathognomonic', False))});"
            )

        # diagnostics
        for dg in d.get("diagnostics", []):
            slug = dg["name"].lower().replace(" ", "-")[:150]
            dgid, new_dg = ids.get_or_create("diagnostic_methods", slug)
            if new_dg:
                dg_type = dg.get("type", "physical_exam")
                dt_map = {"anamnesis": "history_taking", "history": "history_taking"}
                if dg_type and dg_type.lower() in dt_map:
                    dg_type = dt_map[dg_type.lower()]
                out.append(
                    "INSERT INTO diagnostic_methods (id, slug, name, type) "
                    f"VALUES ({dgid}, {q(slug)}, {q(dg['name'])}, {q(dg_type)});"
                )
            link = ids.next("disease_diagnostics")
            out.append(
                "INSERT INTO disease_diagnostics (id, disease_id, diagnostic_method_id, "
                "is_gold_standard, step_order, expected_finding) "
                f"VALUES ({link}, {did}, {dgid}, {q(dg.get('is_gold_standard', False))}, "
                f"{q(dg.get('step_order'))}, {q(dg.get('expected_finding'))});"
            )

        # treatments + products
        for tx in d.get("treatments", []):
            slug = tx["name"].lower().replace(" ", "-")[:150]
            txid, new_tx = ids.get_or_create("treatments", slug)
            if new_tx:
                out.append(
                    "INSERT INTO treatments (id, slug, name, type, description, procedure_steps) "
                    f"VALUES ({txid}, {q(slug)}, {q(tx['name'])}, {q(tx.get('type', 'pharmacological'))}, "
                    f"{q(tx.get('recommendation'))}, {q(tx.get('procedure_steps'))});"
                )
            link = ids.next("disease_treatments")
            out.append(
                "INSERT INTO disease_treatments (id, disease_id, treatment_id, line_of_therapy, "
                "recommendation) "
                f"VALUES ({link}, {did}, {txid}, {q(tx.get('line_of_therapy'))}, "
                f"{q(tx.get('recommendation'))});"
            )
            for p in tx.get("products", []):
                pslug = (p["name"]).lower().replace(" ", "-")[:150]
                pid, new_p = ids.get_or_create("products", pslug)
                if new_p:
                    pk = p.get("kind", "medication")
                    pk_map = {"supportive": "supplement", "dietary": "food_prescription"}
                    if pk and pk.lower() in pk_map:
                        pk = pk_map[pk.lower()]
                    out.append(
                        "INSERT INTO products (id, name, kind, active_ingredient, description) "
                        f"VALUES ({pid}, {q(p['name'])}, {q(pk)}, "
                        f"{q(p.get('active_ingredient'))}, {q(p.get('cautions'))});"
                    )
                link = ids.next("treatment_products")
                out.append(
                    "INSERT INTO treatment_products (id, treatment_id, product_id, dosage_guide, "
                    "route, cautions) "
                    f"VALUES ({link}, {txid}, {pid}, {q(p.get('dosage_guide'))}, "
                    f"{q(p.get('route'))}, {q(p.get('cautions'))});"
                )

    # reset sequence agar serial lanjut setelah ID manual
    out.append("\n-- sinkronkan sequence")
    for table in ["animal_categories", "breeds", "breed_variants", "breed_traits",
                  "diseases", "disease_species", "breed_disease_susceptibility",
                  "symptoms", "disease_symptoms", "diagnostic_methods",
                  "disease_diagnostics", "treatments", "disease_treatments",
                  "products", "treatment_products"]:
        out.append(
            f"SELECT setval(pg_get_serial_sequence('{table}','id'), "
            f"COALESCE((SELECT MAX(id) FROM {table}), 1));"
        )

    out.append("COMMIT;")
    return "\n".join(out) + "\n"


def main() -> None:
    sql = generate_sql()
    path = SEED_DIR / "seed.sql"
    path.write_text(sql, encoding="utf-8")
    n = sql.count("INSERT INTO")
    print(f"Seed SQL ditulis ke {path} ({n} baris INSERT).")


if __name__ == "__main__":
    main()
