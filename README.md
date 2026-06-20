# 🐾 Sobatpaws — Veterinary Backend AI Services

**Backend AI Services** untuk dokter hewan — REST API, ML inference, dan AI suggestion engine yang diintegrasikan oleh aplikasi eksternal (Android, iOS, Web, App Vet pihak ketiga).

**Repo:** [github.com/winspaws/Sobatpaws-ai](https://github.com/winspaws/Sobatpaws-ai) · **API version:** `0.3.0`

> ⚠️ Sobatpaws **bukan aplikasi full-stack**. Kami menyediakan backend API + AI services.
> Aplikasi frontend (mobile/web) dikembangkan oleh tim aplikasi eksternal yang mengintegrasikan
> endpoint Sobatpaws untuk menerima input customer dan menampilkan saran AI ke dokter.

Mendukung **dokter hewan (vets), klinik hewan, dan petshop** dalam mengolah & menganalisa
data klinis menjadi saran diagnosa, tindakan, dan rekomendasi pengobatan.

> ⚠️ **Disclaimer medis:** Seluruh data & output bersifat **pendukung keputusan**
> klinis untuk tenaga profesional. **Diagnosa dan resep final wajib oleh dokter
> hewan berlisensi.** Dosis adalah panduan umum dan harus diverifikasi sesuai
> spesies, berat badan, dan kondisi pasien.

---

## Quick Links

| Resource | Link |
|----------|------|
| Swagger UI | `/docs` |
| ReDoc | `/redoc` |
| API Documentation | [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) |
| Request/Response Examples | [`docs/API_EXAMPLES.md`](docs/API_EXAMPLES.md) |
| Postman Collection | [`docs/Sobatpaws_API.postman_collection.json`](docs/Sobatpaws_API.postman_collection.json) |
| Deployment Guide | [`docs/deployment.md`](docs/deployment.md) |
| AI Agent Guide | [`AGENTS.md`](AGENTS.md) |
| Jurnal Perhewanan | [`docs/jurnal/INDEX.md`](docs/jurnal/INDEX.md) |

---

## 1. Apa yang ada di dalam platform ini

| Lapisan | Isi | Lokasi |
|---|---|---|
| **Skema Data** | 5 domain (taxonomy, clinical, operational, ML, AI) dalam DBML | `dbml/schema.dbml` |
| **Sumber Data** | Kategori spesies, ras + varian + traits, penyakit + gejala + diagnosa + tindakan + produk | `data/` |
| **Seed SQL** | Generator JSON → PostgreSQL INSERT | `src/sobatpaws/seed_generator.py` → `seed/seed.sql` |
| **Pembelajaran (ML)** | Dataset builder, feature engineering, training, inference | `src/sobatpaws/ml/` |
| **Smart Data Platform** | Orkestrator pipeline, doctor, registry lineage (agent-friendly) | `src/sobatpaws/platform/` + `AGENTS.md` |
| **API** | REST (FastAPI v0.3.0): data, ML, AI, konsultasi, integrasi, platform, admin | `src/sobatpaws/api/` |
| **Dokumentasi Integrasi** | API reference, contoh request/response, Postman | `docs/` |
| **Riset & Jurnal** | Monograf spesies, ras, penyakit (130+ ras terdokumentasi) | `docs/jurnal/` |

### Cakupan data saat ini

| Item | Jumlah | Catatan |
|------|--------|---------|
| Kategori spesies | **10** | dog, cat, rabbit, hamster, poultry, fish, reptile, amphibian, ferret, guinea_pig |
| Ras/breed | **177** | dengan varian (warna/pola/morph/ukuran) & traits untuk fitur ML |
| Penyakit (KB curated) | **44** | gejala, diagnosa, tindakan, produk — per spesies |
| Gejala unik | **207** | dapat diobservasi klinis |
| Model ML terlatih | **10** | RandomForest per kategori spesies (`artifacts/models/`) |
| Dataset sintetik | **500K baris** | `data/generated/` — untuk validasi & bulk training |
| Jurnal riset | **130+ ras**, **30 penyakit** | `docs/jurnal/` — sync dari KB via `scripts/build_journal_index.py` |

**Menambah data** = tambahkan entri JSON di `data/`, lalu jalankan ulang generator seed & training. Tidak perlu mengubah kode inti.

---

## 2. Arsitektur

```
┌──────────────────────────────────────────────────────────┐
│  APLIKASI EKSTERNAL (Android / iOS / Web / App Vet 3rd)  │
│  - Input: teks, mic, kamera                              │
│  - UI/UX: tampilkan saran AI ke dokter                   │
│  - Kelola data customer, pet, appointment                │
└────────────────────────┬─────────────────────────────────┘
                         │ REST API / JSON
                         ▼
┌──────────────────────────────────────────────────────────┐
│  SOBATPAWS BACKEND API (FastAPI 0.3.0)                   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │              KNOWLEDGE BASE (JSON)               │    │
│  │  data_loader.py → KnowledgeBase (in-mem)         │    │
│  │  (kategori, ras, varian, penyakit)               │    │
│  └────────────────────┬─────────────────────────────┘    │
│                       │                                  │
│         ┌─────────────▼─────────────┐                    │
│         │    ML Pipeline            │                    │
│         │  dataset → train → model  │                    │
│         │  (RandomForest per sp.)   │                    │
│         └─────────────┬─────────────┘                    │
│                       │ predict (symptom→disease)        │
│                       ▼                                  │
│  ┌──────────────────────────────────────────────────┐    │
│  │         AI Suggestion Engine (RAG)               │    │
│  │  retrieve (ML + KB + breed risk)                 │    │
│  │  → ground (KB) → safety guardrail                │    │
│  │  → LLM synthesis (opsional, mode smart)          │    │
│  │  → structured JSON                               │    │
│  └────────────────────┬─────────────────────────────┘    │
│                       │                                  │
│  ┌────────────────────┴─────────────────────────────┐    │
│  │              REST API ENDPOINTS                   │    │
│  │  Core │ Integration │ Platform │ Agent │ Admin   │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Learning Loop (human-in-the-loop)               │    │
│  │  doctor feedback → gold labels → retrain ML      │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

Prinsip kunci: **Retrieval-Augmented Generation (RAG)** — AI tidak mengarang;
ia di-*ground* pada knowledge base terstruktur, diperkuat prediksi ML, dan
dilindungi **safety guardrail** kontraindikasi obat per spesies.

Mode **`smart`** melewati LLM bila ML + KB sudah yakin (hemat token).

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
├── clinical/
│   ├── diseases_dogs.json       # penyakit + gejala + diagnosa + tindakan + produk
│   ├── diseases_cats.json
│   ├── diseases_rabbits.json    diseases_hamsters.json
│   ├── diseases_poultry.json    diseases_fish.json
│   ├── diseases_reptiles.json   diseases_exotic_others.json
│   └── extensions/
│       └── medication_kb.json   # knowledge base obat per spesies
├── generated/                   # dataset sintetik (gitignored, regenerate via scripts/)
└── ml_views/                    # view ML terkompresi (Parquet/gzip-CSV)

docs/jurnal/                     # monograf riset per spesies, ras, penyakit
├── INDEX.md                     # auto-generated index
├── spesies/  ras/  penyakit/
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

---

## 5. Cara Menjalankan

### Prasyarat
- Python **3.10+** disarankan (di 3.9 paket `eval_type_backport` otomatis dipakai).
- (Opsional) PostgreSQL untuk memuat seed & learning store.
- (Opsional) Ollama / vLLM untuk inferensi LLM lokal.

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
# → categories: 10, breeds: 177, diseases: 44, unique_symptoms: 207
```

### b) Generate seed SQL & muat ke DB
```bash
python -m sobatpaws.seed_generator           # → seed/seed.sql
psql "$DATABASE_URL" -f seed/schema.sql       # buat tabel
psql "$DATABASE_URL" -f seed/seed.sql         # isi data
```

### c) Latih model ML (symptom → disease)
```bash
python -m sobatpaws.ml.train                 # semua kategori (10 model)
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
./run.sh              # default port 8000
./run.sh 8080         # port lain
# Dashboard verifikasi : http://localhost:8000/
# Dokumentasi API      : http://localhost:8000/docs
```

Atau manual:
```bash
uvicorn sobatpaws.api.main:app --reload --app-dir src
```

### f) Retraining dari input dokter
```bash
python -m sobatpaws.ml.retrain
python -m sobatpaws.ml.retrain --category cat
curl -X POST http://localhost:8000/learning/retrain \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: YOUR_ADMIN_KEY' \
  -d '{"category":"cat"}'
```

### g) Learning store ke PostgreSQL (opsional)
```bash
psql "$DATABASE_URL" -f seed/learning.sql
export SOBATPAWS_LEARNING_BACKEND=both
python -m sobatpaws.ai.learning_store --sync-db
```

### h) Export dataset ke Excel
```bash
python3 scripts/generate_all.py          # generate CSV dulu (jika belum)
python3 scripts/export_excel.py          # full export → data/excel/
python3 scripts/export_excel.py --sample-only
python3 scripts/export_excel.py --learning-only
# Unduh via API: GET /exports/excel  →  GET /exports/excel/Sobatpaws_08_Learning.xlsx
```

### i) Resample dataset bulk (500K baris)
```bash
python3 scripts/resample_dataset_500k.py
# Output: data/generated/Dataset_Kesehatan_Hewan_500K_Rows.csv
```

### j) Build index jurnal riset
```bash
python3 scripts/build_journal_index.py   # → docs/jurnal/INDEX.md
```

---

## 6. API Endpoints

Dokumentasi lengkap: [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md)

### Core (`main.py`)

| Method | Path | Auth | Deskripsi |
|--------|------|------|-----------|
| GET | `/health` | — | Status sistem (KB, LLM, learning store) |
| GET | `/api/status` | — | Status detail backend, AI, ML, DB |
| GET | `/categories`, `/breeds/{slug}`, `/diseases/{slug}` | — | Master data knowledge base |
| GET | `/api/stats/breakdown`, `/api/stats/breeds`, `/api/symptoms` | — | Statistik & lookup gejala |
| POST | `/api/consult` | Vet | Single-shot consult (teks/gejala → saran AI) |
| POST | `/ml/predict` | — | Prediksi cepat symptom → disease |
| POST | `/consultations` | Vet | Mulai sesi konsultasi multimodal |
| POST | `/consultations/{id}/turns` | Vet | Giliran lanjutan (gejala kumulatif) |
| POST | `/consultations/{id}/media` | Vet | Upload audio (mic) / gambar (kamera) |
| POST | `/consultations/{id}/doctor-input` | Vet | Simpan keputusan dokter |
| POST | `/consultations/{id}/feedback` | Vet | Penilaian dokter atas saran AI |
| GET | `/learning/export`, `/learning/stats` | — | Ekspor gold labels & statistik |
| POST | `/learning/retrain`, `/learning/sync-db` | Admin | Retrain ML & sync ke PostgreSQL |
| POST | `/api/dataset/upload` | — | Upload dataset CSV |
| GET | `/exports/excel`, `/exports/excel/{filename}` | — | Unduh workbook Excel |

### Integrasi Vet App (`/api/integration`)

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/manifest` | Kontrak integrasi untuk tim developer app |
| GET | `/id-schema` | Skema ID entitas (vet, owner, pet, case) |
| GET | `/entities/{consultation_id}` | Lookup bundle ID entitas |
| GET | `/consultations/by-external/{external_id}` | Lookup by ID eksternal |
| GET | `/consultations` | Filter konsultasi by vet/pet/owner |
| GET | `/capabilities` | Fitur yang tersedia |

### Smart Data Platform (`/api/platform`)

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/manifest` | Kontrak agent-friendly |
| GET | `/doctor` | Health check pipeline |
| GET | `/registry` | Lineage registry |
| GET | `/pipeline` | Daftar step pipeline |
| POST | `/pipeline/run` | Jalankan pipeline (Admin) |

### AI Agent (`/api/agent`)

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/providers`, `/providers/status` | Daftar & status provider LLM |
| POST | `/providers/{id}/activate` | Aktifkan provider (Admin) |
| GET | `/conversations`, `/suggestions` | Riwayat sesi & saran AI |
| POST | `/conversations/{id}/doctor-input` | Input dokter via agent API |

### Admin Dashboard (`/api/admin`)

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/overview` | Ringkasan sistem |
| GET | `/ai/usage` | Penggunaan token LLM |
| GET | `/learning/events` | Event pembelajaran |
| GET | `/integration/status` | Status integrasi |

### Autentikasi

Endpoint bertanda **Vet** membutuhkan header `X-API-Key` dengan `SOBATPAWS_VET_API_KEY`.
Endpoint **Admin** membutuhkan `SOBATPAWS_ADMIN_API_KEY`.

---

## 7. Pipeline ML

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

## 8. AI Wrapping

- **`ai/wrapper.py`** — `LLMClient` provider-agnostic (OpenAI / Anthropic / local Ollama /
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

Provider LLM didukung via env: `local` (Ollama), `openai`, `anthropic` — dengan fallback chain
(`SOBATPAWS_AI_FALLBACK_CHAIN=local,openai,anthropic`).

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

## 9. Testing

```bash
# Semua test
pytest tests/ -v

# Integration tests (API endpoints)
pytest tests/test_api_integration.py -v

# Unit tests (session store, consultation service)
pytest tests/test_session_store_unit.py tests/test_consultation_service.py -v
```

Test menggunakan `conftest.py` dengan fixture FastAPI TestClient dan isolasi session store.

---

## 10. Dukungan untuk tiap pengguna

| Pengguna | Manfaat |
|---|---|
| **Dokter hewan / klinik** | Triage darurat, diagnosa banding, langkah pemeriksaan & tindakan, panduan dosis dengan guardrail keselamatan. |
| **Petshop** | Edukasi ras & penyakit umum, rekomendasi produk (suplemen/antiparasit/pakan resep), peramalan permintaan stok. |
| **Tim integrasi app** | Manifest API, skema ID entitas, Postman collection, contoh request/response siap pakai. |
| **Data/ML engineer** | Skema siap-pakai, feature store, dataset builder, registry model & prediksi, loop feedback. |

---

## 11. Roadmap

- [x] REST API FastAPI dengan konsultasi multimodal
- [x] ML pipeline (RandomForest per spesies, 10 model)
- [x] Integration endpoints untuk app vet eksternal
- [x] Smart Data Platform + AGENTS.md
- [x] Docker Compose production stack
- [x] API documentation + Postman collection
- [x] Jurnal riset perhewanan (130+ ras terdokumentasi)
- [x] Integration tests
- [ ] Perluas KB penyakit (target ratusan per spesies)
- [ ] Model triage-severity & treatment-recommendation
- [ ] Embedding + vector search untuk RAG literatur
- [ ] Integrasi gambar (klasifikasi lesi kulit / identifikasi ras)
- [ ] Modul peramalan permintaan inventory petshop

---

## 12. Lisensi & etika data

Data kurasi bersifat edukatif. Saat menambah data klinis nyata, lakukan
**anonimisasi** (`clinical_cases.is_anonymized`) dan patuhi regulasi privasi.
Penyakit unggas menular tertentu (mis. ND/AI) **wajib dilaporkan** ke dinas
peternakan setempat.

---

## 13. Deployment (Production)

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Host                          │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │  sobatpaws-  │    │  sobatpaws-  │    │ sobatpaws- │ │
│  │  api         │───▶│  db          │    │ pgadmin    │ │
│  │  (port 8080) │    │  (port 5432) │    │ (port 5050)│ │
│  │              │    │              │    │ (debug)    │ │
│  └──────────────┘    └──────────────┘    └────────────┘ │
│         │                                                │
│         ▼                                                │
│  ┌──────────────┐                                        │
│  │  host.docker │  (Ollama / vLLM for local inference)   │
│  │  .internal   │  extra_hosts + OLLAMA_HOST=0.0.0.0    │
│  └──────────────┘                                        │
└─────────────────────────────────────────────────────────┘
```

### Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build (builder + runtime slim image, uid 1000) |
| `docker-compose.prod.yml` | Production stack: API + PostgreSQL + pgAdmin (debug profile) |
| `.env.production` | Environment variable template (copy to `.env`) |
| `docs/deployment.md` | Full deployment guide (build, seed, backup, rollback) |

### Quick Start

```bash
# 1. Clone repo
git clone https://github.com/winspaws/Sobatpaws-ai.git
cd Sobatpaws-ai

# 2. Copy env template and fill secrets
cp .env.production .env
# Edit .env — set API keys, passwords, etc.

# 3. Build and start
docker compose -f docker-compose.prod.yml up -d

# 4. Verify health
curl http://localhost:8080/health

# 5. Check logs
docker compose -f docker-compose.prod.yml logs -f api
```

### Production Notes

| Item | Detail |
|------|--------|
| **Port mapping** | Host `:8080` → container `:8000` |
| **Ollama access** | `extra_hosts: host.docker.internal:host-gateway` + Ollama bind `0.0.0.0:11434` |
| **httpx pin** | `httpx<0.28` di `requirements.txt` (kompatibilitas openai SDK 1.30.1) |
| **LLM fallback** | `SOBATPAWS_AI_FALLBACK_CHAIN=local,openai,anthropic` |
| **pgAdmin** | Hanya jalan dengan profile debug: `docker compose --profile debug up -d` |

### Resource Limits

| Service | CPU Limit | Memory Limit |
|---------|-----------|-------------|
| API | 2.0 cores | 2 GB |
| PostgreSQL | 1.0 core | 1 GB |
| pgAdmin (debug) | — | 256 MB |

ML inference (RandomForest) is CPU-bound. Expect ~100–500 ms per prediction.

### Health Check

```bash
curl http://localhost:8080/health
# → {"status":"ok","llm_available":true,"knowledge_base":{...}}
```

Container-level HEALTHCHECK runs every 30s:
```bash
docker inspect --format='{{.State.Health.Status}}' sobatpaws-api
```

### Full Guide

See [`docs/deployment.md`](docs/deployment.md) for detailed instructions covering:
- Build & deploy steps
- Database seeding (first deploy)
- ML model training
- Backup & restore (DB + artifacts)
- Rollback procedure
- Troubleshooting
- Security notes
