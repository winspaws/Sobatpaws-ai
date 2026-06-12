#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sobatpaws operational + ML + AI data generator (stage 2).

Builds on the taxonomy/clinical dataset produced by generate_dataset.py and
populates the remaining schema domains with referentially-consistent,
deterministic synthetic data:

  Operational : organizations, users, pet_owners, pets, clinical_cases,
                case_symptoms, case_diagnoses, case_treatments
  Clinical xtra: symptoms, disease_symptoms  (masters missing from stage 1)
  ML          : data_sources, ml_datasets, dataset_sources, feature_definitions,
                dataset_features, ml_models, ml_predictions, ml_feedback
  AI          : ai_providers, ai_prompt_templates, ai_conversations,
                ai_requests, ai_suggestions

Each clinical case is built around ONE primary disease drawn from the pet's
category pool, so its symptoms / diagnosis / treatment / ML prediction / AI
suggestion all line up (good signal for the ML task, realistic joins).

Deterministic: fixed RNG seed -> identical output every run.

Usage:
  python3 scripts/generate_operational.py            # full (~1.8M rows)
  python3 scripts/generate_operational.py --scale 0.02
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import catalogs as C  # noqa: E402

OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "data", "generated"))
SEED = 42
EPOCH = dt.date(2023, 1, 1)


# ---------------------------------------------------------------------------
# Vocab pools
# ---------------------------------------------------------------------------
CITIES = [
    ("Jakarta", "DKI Jakarta"), ("Surabaya", "Jawa Timur"), ("Bandung", "Jawa Barat"),
    ("Medan", "Sumatera Utara"), ("Semarang", "Jawa Tengah"), ("Makassar", "Sulawesi Selatan"),
    ("Denpasar", "Bali"), ("Yogyakarta", "DI Yogyakarta"), ("Tangerang", "Banten"),
    ("Bekasi", "Jawa Barat"), ("Depok", "Jawa Barat"), ("Malang", "Jawa Timur"),
    ("Palembang", "Sumatera Selatan"), ("Bogor", "Jawa Barat"), ("Batam", "Kepulauan Riau"),
]
ORG_TYPES = ["vet_clinic", "vet_hospital", "independent_vet", "pet_shop",
             "pet_grooming", "shelter", "breeder", "laboratory"]
ORG_NAME_PREFIX = ["Klinik Hewan", "RSH", "Vet", "PetCare", "Satwa", "Hewan Sehat",
                   "Animal Clinic", "Petshop", "Groomingku", "Shelter", "Breeder",
                   "Lab Diagnostik"]
ORG_NAME_SUFFIX = ["Sejahtera", "Bahagia", "Lestari", "Mandiri", "Prima", "Utama",
                   "Sentosa", "Nusantara", "Bersama", "Asri", "Jaya", "Mulia"]
ROLES = ["vet", "vet", "vet", "vet_tech", "vet_tech", "groomer", "cashier", "admin"]
FIRST = ["Andi", "Budi", "Citra", "Dewi", "Eka", "Fajar", "Gita", "Hadi", "Indah",
         "Joko", "Kartika", "Lina", "Maya", "Nanda", "Oki", "Putri", "Rangga",
         "Sari", "Tono", "Umi", "Vino", "Wati", "Yusuf", "Zahra", "Bagus", "Rina"]
LAST = ["Santoso", "Wijaya", "Pratama", "Lestari", "Nugroho", "Halim", "Saputra",
        "Permata", "Kusuma", "Hartono", "Maulana", "Anggraini", "Setiawan",
        "Rahmawati", "Gunawan", "Sihombing", "Tanjung", "Siregar"]
PET_NAMES = ["Milo", "Luna", "Bella", "Max", "Coco", "Oreo", "Mochi", "Kitty",
             "Bruno", "Cleo", "Simba", "Nala", "Rocky", "Lucky", "Snowy", "Boba",
             "Caramel", "Ginger", "Pixel", "Shadow", "Tofu", "Momo", "Pinky", "Bobby"]
COMPLAINTS = [
    "Tidak mau makan sejak 2 hari", "Lemas dan kurang aktif", "Muntah berulang",
    "Diare", "Gatal-gatal & garuk terus", "Bersin & ingusan", "Pincang kaki belakang",
    "Sesak napas", "Mata berair", "Sering minum & pipis", "Benjolan di kulit",
    "Demam & menggigil", "Bulu rontok berlebihan", "Susah pipis",
]

SYMPTOMS = [
    ("lethargy", "Lethargy", "Lemas", "systemic"),
    ("anorexia", "Anorexia", "Tidak nafsu makan", "digestive"),
    ("vomiting", "Vomiting", "Muntah", "digestive"),
    ("diarrhea", "Diarrhea", "Diare", "digestive"),
    ("fever", "Fever", "Demam", "systemic"),
    ("coughing", "Coughing", "Batuk", "respiratory"),
    ("sneezing", "Sneezing", "Bersin", "respiratory"),
    ("dyspnea", "Difficult breathing", "Sesak napas", "respiratory"),
    ("nasal-discharge", "Nasal discharge", "Ingus/leleran hidung", "respiratory"),
    ("itching", "Itching", "Gatal", "integumentary"),
    ("hair-loss", "Hair loss", "Kerontokan bulu", "integumentary"),
    ("skin-lesion", "Skin lesion", "Lesi kulit", "integumentary"),
    ("scaly-skin", "Scaly skin", "Kulit bersisik", "integumentary"),
    ("limping", "Limping", "Pincang", "musculoskeletal"),
    ("weakness", "Weakness", "Kelemahan", "musculoskeletal"),
    ("seizure", "Seizure", "Kejang", "nervous"),
    ("head-tilt", "Head tilt", "Kepala miring", "nervous"),
    ("polyuria", "Increased urination", "Banyak pipis", "urinary"),
    ("polydipsia", "Increased thirst", "Banyak minum", "urinary"),
    ("dysuria", "Straining to urinate", "Susah/mengejan pipis", "urinary"),
    ("hematuria", "Blood in urine", "Kencing berdarah", "urinary"),
    ("weight-loss", "Weight loss", "Penurunan berat badan", "systemic"),
    ("dehydration", "Dehydration", "Dehidrasi", "systemic"),
    ("pale-gums", "Pale gums", "Gusi pucat", "cardiovascular"),
    ("murmur", "Heart murmur", "Bising jantung", "cardiovascular"),
    ("ocular-discharge", "Ocular discharge", "Mata berair", "ophthalmic"),
    ("ear-discharge", "Ear discharge", "Leleran telinga", "auditory"),
    ("swelling", "Swelling/mass", "Bengkak/benjolan", "integumentary"),
    ("jaundice", "Jaundice", "Kuning (jaundice)", "digestive"),
    ("abdominal-pain", "Abdominal pain", "Nyeri perut", "digestive"),
    ("regurgitation", "Regurgitation", "Regurgitasi", "digestive"),
    ("bloating", "Bloating", "Kembung", "digestive"),
    ("discharge-eye", "Conjunctivitis", "Konjungtivitis", "ophthalmic"),
    ("overgrown-teeth", "Overgrown teeth", "Gigi tumbuh berlebih", "dental"),
    ("drooling", "Drooling", "Ngiler berlebih", "dental"),
    ("feather-plucking", "Feather plucking", "Mencabuti bulu", "behavioral"),
]

FEATURE_KEYS = [
    ("breed_id", "categorical"), ("category_id", "categorical"), ("age_years", "numeric"),
    ("weight_kg", "numeric"), ("sex", "categorical"), ("is_neutered", "boolean"),
    ("temperature_c", "numeric"), ("heart_rate", "numeric"), ("resp_rate", "numeric"),
    ("symptom_count", "numeric"), ("body_system", "categorical"), ("is_emergency", "boolean"),
    ("season", "categorical"), ("city", "categorical"), ("prior_visits", "numeric"),
    ("vaccination_status", "categorical"), ("diet_type", "categorical"),
    ("symptom_vector", "embedding"), ("chief_complaint", "text"), ("risk_score", "numeric"),
]
ML_TASKS = ["disease_classification", "symptom_to_disease", "risk_prediction",
            "triage_severity", "treatment_recommendation", "breed_identification"]
ALGOS = ["xgboost", "random_forest", "lightgbm", "logistic_regression",
         "neural_net", "transformer"]
DS_TYPES = ["clinical_case", "manual_entry", "imported_csv", "external_api",
            "lab_result", "literature", "partner_clinic"]
AI_PROVIDERS = [("OpenAI GPT", "openai", "gpt-4o"), ("Anthropic Claude", "anthropic", "claude-3-5-sonnet"),
                ("Google Gemini", "google_gemini", "gemini-1.5-pro"),
                ("Azure OpenAI", "azure_openai", "gpt-4o"), ("Local Llama", "local_llm", "llama-3-70b")]
CASE_STATUS = ["recovered", "recovered", "treatment", "diagnosed", "closed",
               "referred", "in_progress", "open"]
VERDICTS = ["correct", "correct", "correct", "partially_correct", "incorrect"]


def slug_hash(text, n):
    return int(hashlib.md5(text.encode()).hexdigest(), 16) % n


def d_iso(rng, span_days=900):
    return (EPOCH + dt.timedelta(days=rng.randint(0, span_days))).isoformat()


def ts_iso(rng, span_days=900):
    base = EPOCH + dt.timedelta(days=rng.randint(0, span_days),
                                seconds=rng.randint(0, 86399))
    return base.strftime("%Y-%m-%d %H:%M:%S")


def load_id_map(path, key_col="slug", id_col="id"):
    m = {}
    with open(os.path.join(OUT_DIR, path)) as f:
        for r in csv.DictReader(f):
            m[r[key_col]] = int(r[id_col])
    return m


def load_disease_symptom_map(disease_id, disease_slug_by_id):
    """disease slug -> list of symptom_id dari stage-1 disease_symptoms.csv."""
    path = os.path.join(OUT_DIR, "disease_symptoms.csv")
    out = {}
    if not os.path.exists(path):
        return out
    with open(path) as f:
        for r in csv.DictReader(f):
            slug = disease_slug_by_id.get(int(r["disease_id"]))
            if slug:
                out.setdefault(slug, []).append(int(r["symptom_id"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--target-rows", type=int, default=500000,
                    help="target total baris dataset (default 500k)")
    args = ap.parse_args()
    s = args.scale
    target_rows = int(args.target_rows * s)
    rng = random.Random(SEED)

    if not os.path.exists(os.path.join(OUT_DIR, "breeds.csv")):
        sys.exit("ERROR: run generate_dataset.py first (breeds.csv missing).")

    # ---- load masters from stage 1 ----
    disease_id = load_id_map("diseases.csv")
    dx_id = load_id_map("diagnostic_methods.csv")
    tx_id = load_id_map("treatments.csv")
    pr_id = load_id_map("products.csv", key_col="sku")

    # breed_id -> category_id  (and per-category list of breed ids)
    breed_cat = {}
    cat_breeds = {}
    with open(os.path.join(OUT_DIR, "breeds.csv")) as f:
        for r in csv.DictReader(f):
            bid, cid = int(r["id"]), int(r["category_id"])
            breed_cat[bid] = cid
            cat_breeds.setdefault(cid, []).append(bid)
    all_breed_ids = list(breed_cat.keys())

    # category_id -> list of clinical disease dicts (from catalogs)
    cat_clinical = {}
    for cat_slug, pool in C.CLINICAL.items():
        cid = C.CATEGORY_IDS[cat_slug]
        cat_clinical[cid] = pool

    disease_slug_by_id = {v: k for k, v in disease_id.items()}
    stage1_symptoms = os.path.exists(os.path.join(OUT_DIR, "symptoms.csv"))
    stage1_dsym = os.path.exists(os.path.join(OUT_DIR, "disease_symptoms.csv"))

    # disease slug -> symptom ids (stage-1 katalog klinis, atau fallback generik)
    disease_symptom_ids = load_disease_symptom_map(disease_id, disease_slug_by_id)
    n_sym = len(SYMPTOMS)
    disease_symptom_idx = {}
    for slug in disease_id:
        if not disease_symptom_ids.get(slug):
            base = slug_hash(slug, n_sym)
            k = 3 + (slug_hash(slug + "k", 3))
            disease_symptom_idx[slug] = sorted({(base + j * 7) % n_sym for j in range(k)})

    def W(name, header):
        fh = open(os.path.join(OUT_DIR, name), "w", newline="")
        w = csv.writer(fh)
        w.writerow(header)
        return fh, w

    # ---- writers ----
    f_org, w_org = W("organizations.csv",
                     ["id", "slug", "name", "type", "email", "phone", "city", "province", "country"])
    f_usr, w_usr = W("users.csv", ["id", "org_id", "full_name", "email", "role", "license_no"])
    f_own, w_own = W("pet_owners.csv", ["id", "org_id", "full_name", "email", "phone"])
    f_pet, w_pet = W("pets.csv",
                     ["id", "owner_id", "org_id", "name", "category_id", "breed_id",
                      "sex", "is_neutered", "birth_date", "weight_kg"])
    f_sym, w_sym = (None, None)
    f_dsym, w_dsym = (None, None)
    if not stage1_symptoms:
        f_sym, w_sym = W("symptoms.csv",
                         ["id", "slug", "name", "name_id", "body_system", "is_red_flag"])
    if not stage1_dsym:
        f_dsym, w_dsym = W("disease_symptoms.csv",
                           ["id", "disease_id", "symptom_id", "frequency", "typical_severity"])
    f_case, w_case = W("clinical_cases.csv",
                       ["id", "org_id", "pet_id", "vet_id", "visit_date", "chief_complaint",
                        "status", "weight_kg", "temperature_c", "heart_rate", "resp_rate",
                        "is_anonymized"])
    f_cs, w_cs = W("case_symptoms.csv", ["id", "case_id", "symptom_id", "severity", "duration_days"])
    f_cd, w_cd = W("case_diagnoses.csv",
                   ["id", "case_id", "disease_id", "is_confirmed", "is_differential",
                    "confidence", "diagnosed_by"])
    f_ct, w_ct = W("case_treatments.csv",
                   ["id", "case_id", "treatment_id", "product_id", "dosage", "route",
                    "start_date", "end_date"])
    f_ds, w_ds = W("data_sources.csv", ["id", "name", "type", "org_id", "record_count", "reliability"])
    f_dset, w_dset = W("ml_datasets.csv",
                       ["id", "name", "task_type", "version", "row_count", "feature_count", "split_ratio", "status"])
    f_dss, w_dss = W("dataset_sources.csv", ["id", "dataset_id", "data_source_id", "weight"])
    f_feat, w_feat = W("feature_definitions.csv", ["id", "key", "name", "data_type", "source_table", "is_active"])
    f_dsf, w_dsf = W("dataset_features.csv", ["id", "dataset_id", "feature_id", "is_target", "importance"])
    f_model, w_model = W("ml_models.csv",
                         ["id", "name", "task_type", "algorithm", "dataset_id", "version",
                          "status", "trained_at", "created_by"])
    f_pred, w_pred = W("ml_predictions.csv",
                       ["id", "model_id", "case_id", "pet_id", "input_json", "output_json",
                        "predicted_disease_id", "confidence", "latency_ms"])
    f_fb, w_fb = W("ml_feedback.csv",
                   ["id", "prediction_id", "ai_suggestion_id", "case_id", "reviewer_id",
                    "verdict", "corrected_disease_id"])
    f_prov, w_prov = W("ai_providers.csv", ["id", "name", "kind", "default_model", "is_active"])
    f_tmpl, w_tmpl = W("ai_prompt_templates.csv",
                       ["id", "slug", "name", "task_type", "system_prompt", "user_template", "version"])
    f_conv, w_conv = W("ai_conversations.csv", ["id", "org_id", "user_id", "case_id", "pet_id", "title"])
    f_req, w_req = W("ai_requests.csv",
                     ["id", "conversation_id", "provider_id", "prompt_template_id", "model",
                      "status", "request_payload", "response_payload", "prompt_tokens",
                      "completion_tokens", "total_tokens", "cost_usd", "latency_ms"])
    f_sug, w_sug = W("ai_suggestions.csv",
                     ["id", "request_id", "case_id", "pet_id", "suggestion_type", "summary",
                      "suggested_diseases", "is_reviewed"])

    # ---- symptoms master (fallback jika stage-1 belum menulis) ----
    sym_id_by_idx = {i: i + 1 for i in range(n_sym)}  # 0-based idx -> 1-based id
    if w_sym:
        for i, (slug, name, name_id, bs) in enumerate(SYMPTOMS, 1):
            red = "true" if slug in ("dyspnea", "seizure", "hematuria", "jaundice", "pale-gums") else "false"
            w_sym.writerow([i, slug, name, name_id, bs, red])

    if w_dsym:
        dsym_id = 0
        freqs = ["high", "very_high", "moderate", "high", "moderate"]
        for slug, sid in disease_id.items():
            idxs = disease_symptom_idx.get(slug, [])
            for j, idx in enumerate(idxs):
                dsym_id += 1
                w_dsym.writerow([dsym_id, sid, sym_id_by_idx[idx], freqs[j % len(freqs)],
                                 rng.choice(["mild", "moderate", "severe"])])

    def symptoms_for_disease(slug):
        if disease_symptom_ids.get(slug):
            return disease_symptom_ids[slug]
        return [sym_id_by_idx[i] for i in disease_symptom_idx.get(slug, [])]

    # ---- volume config (skala ke target_rows ~300k) ----
    avg_sym_per_case = 8
    case_sym_budget = int(target_rows * 0.50)
    n_cases_est = max(200, case_sym_budget // avg_sym_per_case)
    n_pets = max(10, int(target_rows * 0.0312))
    n_orgs = max(2, min(60, target_rows // 8000))
    n_owners = max(5, n_pets // 5)

    # ---- organizations ----
    org_ids = []
    for i in range(1, n_orgs + 1):
        city, prov = rng.choice(CITIES)
        name = "%s %s %s" % (rng.choice(ORG_NAME_PREFIX), rng.choice(ORG_NAME_SUFFIX), city)
        slug = "org-%d-%s" % (i, name.lower().replace(" ", "-").replace("'", ""))
        otype = rng.choice(ORG_TYPES)
        w_org.writerow([i, slug, name, otype, "org%d@sobatpaws.id" % i,
                        "+62%d" % rng.randint(81000000000, 89999999999), city, prov, "Indonesia"])
        org_ids.append(i)

    # ---- users (3..8 per org) ----
    user_id = 0
    org_vets = {}  # org_id -> [vet user ids]
    for org in org_ids:
        for _ in range(rng.randint(3, 8)):
            user_id += 1
            role = rng.choice(ROLES)
            fn = "%s %s" % (rng.choice(FIRST), rng.choice(LAST))
            lic = "VET-%05d" % user_id if role == "vet" else ""
            w_usr.writerow([user_id, org, fn, "user%d@sobatpaws.id" % user_id, role, lic])
            if role == "vet":
                org_vets.setdefault(org, []).append(user_id)
    for org in org_ids:  # ensure each org has >=1 vet
        if org not in org_vets:
            user_id += 1
            w_usr.writerow([user_id, org, "%s %s" % (rng.choice(FIRST), rng.choice(LAST)),
                            "user%d@sobatpaws.id" % user_id, "vet", "VET-%05d" % user_id])
            org_vets[org] = [user_id]

    # ---- pet owners ----
    for i in range(1, n_owners + 1):
        org = rng.choice(org_ids)
        fn = "%s %s" % (rng.choice(FIRST), rng.choice(LAST))
        w_own.writerow([i, org, fn, "owner%d@mail.id" % i,
                        "+62%d" % rng.randint(81000000000, 89999999999)])

    # ---- pets ----
    pets = []  # (pet_id, org_id, category_id)
    for i in range(1, n_pets + 1):
        owner = rng.randint(1, n_owners)
        org = rng.choice(org_ids)
        bid = rng.choice(all_breed_ids)
        cid = breed_cat[bid]
        sex = rng.choice(["male", "female"])
        w_pet.writerow([i, owner, org, rng.choice(PET_NAMES), cid, bid, sex,
                        rng.choice(["true", "false"]), d_iso(rng, 3650),
                        round(rng.uniform(0.05, 40), 2)])
        pets.append((i, org, cid))

    # ---- ML masters ----
    n_sources = max(2, int(50 * s))
    src_ids = []
    for i in range(1, n_sources + 1):
        w_ds.writerow([i, "Source %d" % i, rng.choice(DS_TYPES),
                       rng.choice(org_ids), rng.randint(1000, 500000),
                       rng.choice(["moderate", "high", "very_high"])])
        src_ids.append(i)

    feat_ids = []
    for i, (key, dtype) in enumerate(FEATURE_KEYS, 1):
        w_feat.writerow([i, key, key.replace("_", " ").title(), dtype, "clinical_cases", "true"])
        feat_ids.append(i)

    n_datasets = max(2, int(20 * s))
    dset_ids = []
    dss_id = 0
    dsf_id = 0
    for i in range(1, n_datasets + 1):
        task = rng.choice(ML_TASKS)
        w_dset.writerow([i, "Dataset %s v%d" % (task, i), task, "v%d" % rng.randint(1, 4),
                         rng.randint(5000, 300000), rng.randint(8, len(feat_ids)),
                         "70/15/15", "ready"])
        dset_ids.append(i)
        for sid in rng.sample(src_ids, min(len(src_ids), rng.randint(2, 4))):
            dss_id += 1
            w_dss.writerow([dss_id, i, sid, round(rng.uniform(0.3, 1.0), 2)])
        chosen = rng.sample(feat_ids, min(len(feat_ids), rng.randint(8, len(feat_ids))))
        target = rng.choice(chosen)
        for fid in chosen:
            dsf_id += 1
            w_dsf.writerow([dsf_id, i, fid, "true" if fid == target else "false",
                            round(rng.uniform(0, 1), 4)])

    n_models = max(2, int(30 * s))
    model_ids = []
    for i in range(1, n_models + 1):
        task = rng.choice(ML_TASKS)
        st = rng.choice(["deployed", "deployed", "trained", "evaluating", "deprecated"])
        w_model.writerow([i, "model-%s-%d" % (task, i), task, rng.choice(ALGOS),
                          rng.choice(dset_ids), "v%d" % rng.randint(1, 5), st,
                          ts_iso(rng), rng.randint(1, max(1, user_id))])
        model_ids.append(i)

    # ---- AI masters ----
    prov_ids = []
    for i, (name, kind, model) in enumerate(AI_PROVIDERS, 1):
        w_prov.writerow([i, name, kind, model, "true"])
        prov_ids.append(i)
    tmpl_ids = []
    for i in range(1, max(2, int(12 * s)) + 1):
        task = rng.choice(ML_TASKS)
        w_tmpl.writerow([i, "tmpl-%d" % i, "Prompt %s %d" % (task, i), task,
                         "Anda asisten dokter hewan. Berikan saran berbasis bukti.",
                         "Gejala: {{symptoms}}. Ras: {{breed}}. Berikan diagnosa banding.",
                         "v%d" % rng.randint(1, 3)])
        tmpl_ids.append(i)

    # ---- clinical cases + downstream fan-out (single pass) ----
    case_id = cs_id = cd_id = ct_id = 0
    pred_id = fb_id = conv_id = req_id = sug_id = 0

    for (pid, org, cid) in pets:
        pool = cat_clinical.get(cid)
        if not pool:
            continue
        for _ in range(rng.randint(1, 4)):
            case_id += 1
            vet = rng.choice(org_vets[org])
            dis = rng.choice(pool)
            d_id = disease_id[dis["slug"]]
            temp = round(rng.uniform(37.5, 41.0), 1)
            w_case.writerow([case_id, org, pid, vet, ts_iso(rng),
                             rng.choice(COMPLAINTS), rng.choice(CASE_STATUS),
                             round(rng.uniform(0.05, 40), 2), temp,
                             rng.randint(60, 220), rng.randint(10, 60), "true"])

            # symptoms tied to the chosen disease (dari katalog stage-1)
            for sym_id in symptoms_for_disease(dis["slug"]):
                cs_id += 1
                w_cs.writerow([cs_id, case_id, sym_id,
                               rng.choice(["mild", "moderate", "severe"]),
                               rng.randint(1, 21)])

            # confirmed diagnosis (+ optional differential)
            cd_id += 1
            w_cd.writerow([cd_id, case_id, d_id, "true", "false",
                           round(rng.uniform(70, 99), 2), vet])
            if rng.random() < 0.3 and len(pool) > 1:
                alt = rng.choice(pool)
                if alt["slug"] != dis["slug"]:
                    cd_id += 1
                    w_cd.writerow([cd_id, case_id, disease_id[alt["slug"]], "false", "true",
                                   round(rng.uniform(20, 60), 2), vet])

            # treatment + product from the disease
            t_id = tx_id[dis["treatment"][0]]
            prod = dis["products"][0] if dis["products"] else None
            ct_id += 1
            w_ct.writerow([ct_id, case_id, t_id, pr_id[prod[0]] if prod else "",
                           "%d mg/kg" % rng.randint(1, 25),
                           rng.choice(["oral", "IM", "IV", "SC", "topikal"]),
                           d_iso(rng), d_iso(rng)])

            # ML prediction (mostly correct, sometimes wrong -> realistic error signal)
            correct = rng.random() < 0.82
            if correct:
                pred_dis = d_id
                conf = round(rng.uniform(75, 99), 2)
            else:
                wrong = rng.choice(pool)
                pred_dis = disease_id[wrong["slug"]]
                conf = round(rng.uniform(40, 74), 2)
            pred_id += 1
            inp = json.dumps({"breed_cat": cid, "temp": temp, "n_symptoms":
                              len(symptoms_for_disease(dis["slug"]))}, ensure_ascii=False)
            outp = json.dumps({"disease_id": pred_dis, "confidence": conf}, ensure_ascii=False)
            w_pred.writerow([pred_id, rng.choice(model_ids), case_id, pid, inp, outp,
                             pred_dis, conf, rng.randint(5, 400)])

            # AI conversation/request/suggestion (subset of cases)
            this_sug = ""
            if rng.random() < 0.25:
                conv_id += 1
                w_conv.writerow([conv_id, org, vet, case_id, pid,
                                 "Konsultasi AI kasus #%d" % case_id])
                for _r in range(rng.randint(1, 3)):
                    req_id += 1
                    pt = rng.randint(200, 1200)
                    ct_tok = rng.randint(100, 800)
                    w_req.writerow([req_id, conv_id, rng.choice(prov_ids), rng.choice(tmpl_ids),
                                    rng.choice([p[2] for p in AI_PROVIDERS]),
                                    rng.choice(["completed", "completed", "failed", "rate_limited"]),
                                    json.dumps({"q": "diagnosa?"}, ensure_ascii=False),
                                    json.dumps({"ok": True}, ensure_ascii=False),
                                    pt, ct_tok, pt + ct_tok,
                                    round((pt + ct_tok) * 0.000003, 6), rng.randint(200, 5000)])
                    if rng.random() < 0.6:
                        sug_id += 1
                        w_sug.writerow([sug_id, req_id, case_id, pid, "disease_classification",
                                        "Kemungkinan %s; sarankan pemeriksaan lanjutan." % dis["name"],
                                        json.dumps([{"disease_id": d_id, "confidence": conf}],
                                                   ensure_ascii=False), "false"])
                        this_sug = sug_id

            # ML feedback (vet review) on a subset of predictions
            if rng.random() < 0.3:
                fb_id += 1
                verdict = "correct" if correct else rng.choice(["incorrect", "partially_correct"])
                corrected = "" if correct else d_id
                w_fb.writerow([fb_id, pred_id, this_sug if this_sug else "", case_id,
                               vet, verdict, corrected])

    close_files = [f_org, f_usr, f_own, f_pet, f_case, f_cs, f_cd, f_ct,
                   f_ds, f_dset, f_dss, f_feat, f_dsf, f_model, f_pred, f_fb, f_prov,
                   f_tmpl, f_conv, f_req, f_sug]
    if f_sym:
        close_files.append(f_sym)
    if f_dsym:
        close_files.append(f_dsym)
    for fh in close_files:
        fh.close()

    # ---- load_all.sql (FK-ordered: stage1 + stage2) ----
    load_order = [
        ("animal_categories", "id,slug"),
        ("organizations", "id,slug,name,type,email,phone,city,province,country"),
        ("users", "id,org_id,full_name,email,role,license_no"),
        ("pet_owners", "id,org_id,full_name,email,phone"),
        ("diseases", "id,slug,name,name_id,etiology,body_system,default_severity,is_contagious,is_zoonotic,is_emergency"),
        ("symptoms", "id,slug,name,name_id,body_system,is_red_flag"),
        ("diagnostic_methods", "id,slug,name,name_id,type"),
        ("treatments", "id,slug,name,name_id,type,requires_vet"),
        ("products", "id,sku,name,brand,kind,active_ingredient,form"),
        ("breeds", "id,category_id,slug,name,name_id,origin_country,size_class,weight_kg_min,weight_kg_max,height_cm_min,height_cm_max,lifespan_years_min,lifespan_years_max,temperament,coat_type,care_level"),
        ("breed_variants", "id,breed_id,name,variant_type,is_recognized"),
        ("breed_traits", "id,breed_id,trait_key,trait_value"),
        ("disease_symptoms", "id,disease_id,symptom_id,frequency,typical_severity"),
        ("disease_diagnostics", "id,disease_id,diagnostic_method_id,is_gold_standard,step_order,expected_finding"),
        ("disease_treatments", "id,disease_id,treatment_id,line_of_therapy,severity_target,efficacy_note,recommendation"),
        ("breed_clinical_matrix", "id,category_id,breed_id,variant_id,disease_id,diagnostic_method_id,treatment_id,product_id,risk,severity,is_gold_standard_dx,line_of_therapy,prevalence_pct,is_hereditary"),
        ("pets", "id,owner_id,org_id,name,category_id,breed_id,sex,is_neutered,birth_date,weight_kg"),
        ("clinical_cases", "id,org_id,pet_id,vet_id,visit_date,chief_complaint,status,weight_kg,temperature_c,heart_rate,resp_rate,is_anonymized"),
        ("case_symptoms", "id,case_id,symptom_id,severity,duration_days"),
        ("case_diagnoses", "id,case_id,disease_id,is_confirmed,is_differential,confidence,diagnosed_by"),
        ("case_treatments", "id,case_id,treatment_id,product_id,dosage,route,start_date,end_date"),
        ("data_sources", "id,name,type,org_id,record_count,reliability"),
        ("ml_datasets", "id,name,task_type,version,row_count,feature_count,split_ratio,status"),
        ("dataset_sources", "id,dataset_id,data_source_id,weight"),
        ("feature_definitions", "id,key,name,data_type,source_table,is_active"),
        ("dataset_features", "id,dataset_id,feature_id,is_target,importance"),
        ("ml_models", "id,name,task_type,algorithm,dataset_id,version,status,trained_at,created_by"),
        ("ai_providers", "id,name,kind,default_model,is_active"),
        ("ai_prompt_templates", "id,slug,name,task_type,system_prompt,user_template,version"),
        ("ai_conversations", "id,org_id,user_id,case_id,pet_id,title"),
        ("ai_requests", "id,conversation_id,provider_id,prompt_template_id,model,status,request_payload,response_payload,prompt_tokens,completion_tokens,total_tokens,cost_usd,latency_ms"),
        ("ai_suggestions", "id,request_id,case_id,pet_id,suggestion_type,summary,suggested_diseases,is_reviewed"),
        ("ml_predictions", "id,model_id,case_id,pet_id,input_json,output_json,predicted_disease_id,confidence,latency_ms"),
        ("ml_feedback", "id,prediction_id,ai_suggestion_id,case_id,reviewer_id,verdict,corrected_disease_id"),
    ]
    with open(os.path.join(OUT_DIR, "load_all.sql"), "w") as f:
        f.write("-- Full FK-ordered loader for the Sobatpaws dataset (PostgreSQL).\n")
        f.write("-- Prereq: dbml2sql dbml/schema.dbml --postgres | psql -d sobatpaws\n")
        f.write("-- Then:   cd data/generated && psql -d sobatpaws -f load_all.sql\n")
        f.write("BEGIN;\n")
        for t, cols in load_order:
            f.write("\\copy %s(%s) FROM '%s.csv' WITH (FORMAT csv, HEADER true);\n" % (t, cols, t))
        f.write("COMMIT;\n")

    # ---- summary + report ----
    def cnt(name):
        p = os.path.join(OUT_DIR, name + ".csv")
        if not os.path.exists(p):
            return 0
        with open(p) as cf:
            return sum(1 for _ in cf) - 1

    stage2 = ["organizations", "users", "pet_owners", "symptoms", "disease_symptoms",
              "pets", "clinical_cases", "case_symptoms", "case_diagnoses", "case_treatments",
              "data_sources", "ml_datasets", "dataset_sources", "feature_definitions",
              "dataset_features", "ml_models", "ml_predictions", "ml_feedback",
              "ai_providers", "ai_prompt_templates", "ai_conversations", "ai_requests",
              "ai_suggestions"]
    stage1 = ["animal_categories", "diseases", "diagnostic_methods", "treatments",
              "products", "breeds", "breed_variants", "breed_traits", "breed_clinical_matrix"]
    counts = {t: cnt(t) for t, _ in load_order}
    grand = sum(counts.values())
    with open(os.path.join(OUT_DIR, "summary_full.json"), "w") as f:
        json.dump({"scale": s, "tables": counts, "grand_total_rows": grand}, f, indent=2)

    print("=" * 64)
    print("SOBATPAWS OPERATIONAL + ML + AI GENERATION (scale=%.3f)" % s)
    print("=" * 64)
    for t in stage2:
        print("  %-22s %10d" % (t, counts.get(t, 0)))
    print("-" * 64)
    s1 = sum(counts[t] for t in stage1)
    s2 = sum(counts[t] for t in stage2)
    print("  %-22s %10d" % ("stage1 (taxonomy+clinical)", s1))
    print("  %-22s %10d" % ("stage2 (this run)", s2))
    print("=" * 64)
    print("  %-22s %10d" % ("GRAND TOTAL ROWS", grand))
    print("=" * 64)


if __name__ == "__main__":
    main()
