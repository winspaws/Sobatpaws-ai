# 🐾 Sobatpaws — Veterinary ML & AI Data Platform

Platform **sumber data + pembelajaran mesin (ML) + AI wrapping** untuk mendukung
**dokter hewan (vets), klinik hewan, dan petshop** dalam mengolah & menganalisa
data klinis menjadi saran diagnosa, tindakan, dan rekomendasi pengobatan.

> ⚠️ **Disclaimer medis:** Seluruh data & output bersifat **pendukung keputusan**
> klinis untuk tenaga profesional. **Diagnosa dan resep final wajib oleh dokter
> hewan berlisensi.** Dosis adalah panduan umum dan harus diverifikasi sesuai
> spesies, berat badan, dan kondisi pasien.

---

## 1. Apa yang ada di dalam platform ini

| Lapisan | Isi | Lokasi |
|---|---|---|
| **Skema Data** | 5 domain (taxonomy, clinical, operational, ML, AI) dalam DBML | `dbml/schema.dbml` |
| **Sumber Data** | Kategori spesies, ras + varian + traits, penyakit + gejala + diagnosa + tindakan + produk | `data/` |
| **Seed SQL** | Generator JSON → PostgreSQL INSERT | `src/sobatpaws/seed_generator.py` → `seed/seed.sql` |
| **Pembelajaran (ML)** | Dataset builder, feature engineering, training, inference | `src/sobatpaws/ml/` |
| **Smart Data Platform** | Orkestrator pipeline, doctor, registry lineage (agent-friendly) | `src/sobatpaws/platform/` + `AGENTS.md` |
| **API** | REST (FastAPI): data, ML, AI, konsultasi, platform, agent | `src/sobatpaws/api/main.py` |

Cakupan data saat ini (dapat terus diperluas):
- **10 kategori** spesies: anjing, kucing, kelinci, hamster, unggas, ikan, reptil, amfibi, ferret, marmut.
- **160+ ras/breed** dengan varian (warna/pola/morph/ukuran) & traits untuk fitur ML.
- **30+ penyakit** umum & rentan per hewan, lengkap dengan **gejala, metode diagnosa, langkah tindakan, dan produk pengobatan**.
- **130+ gejala** unik yang dapat diobservasi.

---

## 2. Arsitektur

```
                ┌──────────────────────────────────────────────┐
   data/*.json  │   data_loader.py  →  KnowledgeBase (in-mem)   │
 (single source │      (kategori, ras, varian, penyakit)        │
   of truth)    └───────────────┬──────────────┬───────────────┘
                                │              │
                  ┌─────────────▼───┐    ┌─────▼───────────────┐
                  │ seed_generator  │    │     ML pipeline     │
                  │  → seed.sql     │    │ dataset → train →   │
                  │  (PostgreSQL)   │    │ model (RandomForest)│
                  └─────────────────┘    └─────────┬───────────┘
                                                   │ predict (symptom→disease)
   dbml/schema.dbml ──(dbml2sql)──► schema.sql     │
                                                   ▼
                          ┌────────────────────────────────────┐
                          │       AI Suggestion Engine          │
   AI provider (LLM) ◄────┤  retrieve (ML + KB + breed risk)    │
   openai/anthropic/mock  │  → ground (KB) → safety guardrail   │
                          │  → LLM synthesis → structured JSON  │
                          └─────────────────┬──────────────────┘
                                            ▼
                                  FastAPI  /ai/suggest
```

Prinsip kunci: **Retrieval-Augmented Generation (RAG)** — AI tidak mengarang;
ia di-*ground* pada knowledge base terstruktur, diperkuat prediksi ML, dan
dilindungi **safety guardrail** kontraindikasi obat per spesies.

### Smart Data Platform (terintegrasi)

```
┌─────────────────────────────────────────────────────────────────┐
│  AGENTS.md + GET /api/platform/manifest  (kontrak AI agent)      │
└────────────────────────────┬────────────────────────────────────┘
                             │
    ┌────────────────────────┼────────────────────────┐
    ▼                        ▼                        ▼
 curated JSON           synthetic CSV            learning loop
 (runtime truth)        (bulk/validate)          (gold → retrain)
    │                        │                        │
    └──────────── platform/doctor ────────────────────┘
                 platform/pipeline + registry
                             │
              ML train ──► AI suggest ──► API vet/agent
```

```bash
python -m sobatpaws.platform.doctor              # cek kesehatan sistem
python -m sobatpaws.platform.pipeline --preset ml_ready
python -m sobatpaws.platform.registry --refresh
```

Lihat **AGENTS.md** untuk panduan lengkap AI agent.

---

## 3. Model Data (DBML)

`dbml/schema.dbml` mencakup 5 domain:

1. **Taxonomy** — `animal_categories`, `breeds`, `breed_variants`, `breed_traits`
2. **Clinical** — `diseases`, `symptoms`, `disease_symptoms`, `diagnostic_methods`,
   `disease_diagnostics`, `treatments`, `disease_treatments`, `products`,
   `treatment_products`, `breed_disease_susceptibility`, `product_species_safety`
3. **Operational** — `organizations` (vet/klinik/petshop), `users`, `pet_owners`,
   `pets`, `clinical_cases`, `case_symptoms`, `case_diagnoses`, `case_treatments`
4. **ML** — `data_sources`, `ml_datasets`, `dataset_sources`, `feature_definitions`,
   `dataset_features`, `ml_models`, `ml_predictions`, `ml_feedback`
5. **AI** — `ai_providers`, `ai_prompt_templates`, `ai_conversations`,
   `ai_requests`, `ai_suggestions`

Render diagram: tempel isi `schema.dbml` ke [dbdiagram.io](https://dbdiagram.io).

Kompilasi ke SQL:
```bash
npx -p @dbml/cli dbml2sql dbml/schema.dbml --postgres -o seed/schema.sql
```

---

## 4. Struktur Sumber Data

```
data/
├── categories.json              # 10 kategori spesies
├── breeds/
│   ├── dogs.json  cats.json  rabbits.json  hamsters.json
│   ├── poultry.json  fish.json  reptiles.json  others.json
└── clinical/
    ├── diseases_dogs.json       # penyakit + gejala + diagnosa + tindakan + produk
    ├── diseases_cats.json
    ├── diseases_rabbits.json    diseases_hamsters.json
    ├── diseases_poultry.json    diseases_fish.json
    ├── diseases_reptiles.json   diseases_exotic_others.json
```

Setiap penyakit bersifat **self-contained** (contoh ringkas):
```jsonc
{
  "slug": "dog-parvovirus",
  "name_id": "Parvovirus (Parvo)",
  "etiology": "infectious_viral",
  "is_emergency": true,
  "breed_susceptibility": [{ "breed_slug": "dog-rottweiler", "risk": "high", "prevalence_pct": 12 }],
  "symptoms": [{ "name_id": "Diare berdarah", "frequency": "very_high", "is_pathognomonic": true }],
  "diagnostics": [{ "name": "PCR feses", "type": "pcr_molecular", "is_gold_standard": true }],
  "treatments": [{
    "name": "Terapi suportif rawat inap parvo",
    "procedure_steps": "...langkah tindakan...",
    "products": [{ "name": "Maropitant (Cerenia)", "active_ingredient": "Maropitant citrate",
                   "route": "SC/IV", "dosage_guide": "1 mg/kg SID" }]
  }]
}
```

**Menambah data** = cukup tambahkan entri JSON, lalu jalankan ulang generator
seed & training. Tidak perlu mengubah kode.

---

## 5. Cara Menjalankan

### Prasyarat
- Python **3.10+** disarankan (di 3.9 paket `eval_type_backport` otomatis dipakai).
- (Opsional) PostgreSQL untuk memuat seed.

### Instalasi
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # isi kunci AI bila ada
export PYTHONPATH=src
```

### a) Validasi data & lihat statistik
```bash
python -m sobatpaws.data_loader
```

### b) Generate seed SQL & muat ke DB
```bash
python -m sobatpaws.seed_generator           # → seed/seed.sql
psql "$DATABASE_URL" -f seed/schema.sql       # buat tabel
psql "$DATABASE_URL" -f seed/seed.sql         # isi data
```

### c) Latih model ML (symptom → disease)
```bash
python -m sobatpaws.ml.train                 # semua kategori
python -m sobatpaws.ml.train --category dog  # satu kategori
```
Artefak tersimpan di `artifacts/models/`.

### d) Prediksi cepat
```bash
python -m sobatpaws.ml.predict dog "Muntah hebat" "Diare berdarah" "Lemas/lesu"
# → dog-parvovirus (0.94), ...
```

### e) Jalankan API + Dashboard Verifikasi
```bash
uvicorn sobatpaws.api.main:app --reload --app-dir src
# Dashboard verifikasi : http://localhost:8000/      (web/index.html)
# Dokumentasi API      : http://localhost:8000/docs
#
# Endpoint utama:
#   GET  /health, /api/status              status sistem (data/AI/ML/DB)
#   GET  /categories, /breeds/{slug}, ...  data master knowledge base
#   POST /api/consult                      saran klinis single-shot (teks bebas/gejala)
#   POST /ml/predict                       prediksi cepat symptom -> disease
#   POST /consultations                    mulai sesi konsultasi multimodal (chat/video)
#   POST /consultations/{id}/turns         giliran lanjutan (gejala kumulatif)
#   POST /consultations/{id}/media         unggah audio (mic) / gambar (kamera)
#   POST /consultations/{id}/doctor-input  simpan keputusan dokter (bahan pembelajaran)
#   POST /consultations/{id}/feedback      penilaian dokter atas saran AI
#   GET  /learning/export                  ekspor data gold untuk retraining
#   POST /learning/retrain                 latih ulang model dari input dokter
#   GET  /learning/stats                   statistik event pembelajaran
#   POST /learning/sync-db                 migrasi JSONL → PostgreSQL (learning_events)
#   GET  /exports/excel                    daftar workbook Excel (data/excel/)
#   GET  /exports/excel/{filename}         unduh .xlsx
```

Atau pakai skrip singkat:
```bash
./run.sh    # http://localhost:8000
```

### f) Retraining dari input dokter
```bash
python -m sobatpaws.ml.retrain
python -m sobatpaws.ml.retrain --category cat
curl -X POST http://localhost:8000/learning/retrain -H 'Content-Type: application/json' -d '{"category":"cat"}'
```

### g) Learning store ke PostgreSQL (opsional)
```bash
psql "$DATABASE_URL" -f seed/learning.sql
export SOBATPAWS_LEARNING_BACKEND=both
python -m sobatpaws.ai.learning_store --sync-db
```

### h) Export dataset ke Excel
```bash
pip install openpyxl   # sudah ada di requirements.txt
python3 scripts/generate_all.py          # generate CSV dulu (jika belum)
python3 scripts/export_excel.py          # full export → data/excel/
python3 scripts/export_excel.py --sample-only      # cepat: ringkasan + masters
python3 scripts/export_excel.py --learning-only    # konsultasi + gold rows dokter
# Unduh via API: GET /exports/excel  →  GET /exports/excel/Sobatpaws_08_Learning.xlsx
```

---

## 6. Pipeline ML

- **`ml/dataset_builder.py`** — membangun dataset `symptom → disease`. Strategi
  *cold-start*: membangkitkan sampel sintetis dari bobot frekuensi gejala di KB,
  lalu dapat digabung dengan **data klinis nyata** (`clinical_cases`) sebagai
  label emas (`merge_clinical_cases`).
- **`ml/feature_engineering.py`** — feature store + `breed_risk_profile()` (skor
  risiko penyakit per ras) + pembentuk vektor fitur pet (umur, BB, vital, gejala).
- **`ml/train.py`** — melatih `RandomForestClassifier` **per kategori spesies**
  (kosakata gejala berbeda), menyimpan model + metadata (vocab, kelas, metrik).
- **`ml/predict.py`** — inferensi top-K penyakit dari daftar gejala.

Task ML yang didukung skema (`ml_task_type`): klasifikasi penyakit, symptom→disease,
prediksi risiko, triage severity, rekomendasi tindakan, identifikasi ras,
deteksi anomali, dan **peramalan permintaan** (untuk inventory petshop).

### Loop pembelajaran berkelanjutan (human-in-the-loop)
1. Konsultasi multimodal (teks/mic/kamera) → saran AI ke dokter.
2. Dokter menyimpan **diagnosa final** + feedback → `LearningStore` (JSONL / PostgreSQL).
3. `ml/retrain.py` menggabungkan label emas dokter ke dataset latih → model diperbarui.
4. Kualitas prediksi meningkat seiring data klinis terkumpul.

Komponen: `ai/learning_store.py`, `ai/consultation.py`, `ml/retrain.py`.

---

## 7. AI Wrapping

- **`ai/wrapper.py`** — `LLMClient` provider-agnostic (OpenAI / Anthropic /
  mode `mock` tanpa kunci). Mencatat token, biaya, latensi (selaras `ai_requests`).
- **`ai/prompts.py`** — template prompt terversi (selaras `ai_prompt_templates`).
- **`ai/schemas.py`** — output **terstruktur** (Pydantic) → `ai_suggestions`.
- **`ai/suggestion_engine.py`** — orkestrasi RAG:
  retrieve (ML + KB overlap + breed risk) → ground (KB) → **safety** → LLM → JSON.
- **`ai/safety.py`** — **guardrail keselamatan (hard-rule)**: kontraindikasi obat
  per spesies, mis.:
  - 🐱 Kucing: **paracetamol, permethrin, ibuprofen = FATAL**.
  - 🐰 Kelinci & 🐹 rodensia & 🐹 marmut: **penicillin/amoxicillin/clindamycin oral = fatal**.
  - 🐶 Anjing: **xylitol toksik**.

Tanpa kunci API, engine tetap berfungsi penuh dalam **mode rule-based**
(ML + KB), sehingga aman untuk pengembangan/offline.

Contoh penggunaan:
```python
from sobatpaws.ai.schemas import SuggestionRequest
from sobatpaws.ai.suggestion_engine import suggest

resp = suggest(SuggestionRequest(
    category_slug="dog", breed_slug="dog-rottweiler", age_years=0.4,
    symptoms=["Muntah hebat", "Diare berdarah", "Lemas/lesu", "Dehidrasi"],
))
print(resp.is_emergency, resp.summary)
for h in resp.suggested_diseases: print(h.name_id, h.confidence)
```

---

## 8. Dukungan untuk tiap pengguna

| Pengguna | Manfaat |
|---|---|
| **Dokter hewan / klinik** | Triage darurat, diagnosa banding, langkah pemeriksaan & tindakan, panduan dosis dengan guardrail keselamatan. |
| **Petshop** | Edukasi ras & penyakit umum, rekomendasi produk (suplemen/antiparasit/pakan resep), peramalan permintaan stok. |
| **Data/ML engineer** | Skema siap-pakai, feature store, dataset builder, registry model & prediksi, loop feedback. |

---

## 9. Roadmap singkat
- [ ] Tambah data ras & penyakit (target ratusan penyakit per spesies).
- [ ] Model triage-severity & treatment-recommendation.
- [ ] Embedding + vector search untuk RAG literatur.
- [ ] Integrasi gambar (klasifikasi lesi kulit / identifikasi ras).
- [ ] Modul peramalan permintaan inventory petshop.

---

## 10. Lisensi & etika data
Data kurasi bersifat edukatif. Saat menambah data klinis nyata, lakukan
**anonimisasi** (`clinical_cases.is_anonymized`) dan patuhi regulasi privasi.
Penyakit unggas menular tertentu (mis. ND/AI) **wajib dilaporkan** ke dinas
peternakan setempat.
