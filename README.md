# 🐾 Ekosistem Satwa — Veterinary Backend AI Services

**Backend AI Services** untuk dokter hewan — REST API, ML inference, multi-agent AI Orchestrator, dan ekosistem smart veterinary yang diintegrasikan oleh aplikasi eksternal (Android, iOS, Web, App Vet pihak ketiga).

**Repo:** [github.com/winspaws/Sobatpaws-ai](https://github.com/winspaws/Sobatpaws-ai) · **API version:** `v2.2.0`

> ⚠️ Ekosistem Satwa **bukan aplikasi full-stack**. Kami menyediakan backend API + AI services.
> Aplikasi frontend (mobile/web) dikembangkan oleh tim aplikasi eksternal yang mengintegrasikan
> endpoint Ekosistem Satwa untuk menerima input customer dan menampilkan saran AI ke dokter.

Mendukung **dokter hewan (vets), klinik hewan, dan petshop** dalam mengolah & menganalisa
data klinis menjadi saran diagnosa, tindakan, dan rekomendasi pengobatan.

> ⚠️ **Disclaimer medis:** Seluruh data & output bersifat **pendukung keputusan**
> klinis untuk tenaga profesional. **Diagnosa dan resep final wajib oleh dokter
> hewan berlisensi.** Dosis adalah panduan umum dan harus diverifikasi sesuai
> spesies, berat badan, dan kondisi pasien.

---

## Daftar Isi

- [Quick Links](#quick-links)
- [1. Arsitektur Sistem](#1-arsitektur-sistem)
- [2. Pawnia AI Orchestrator](#2-pawnia-ai-orchestrator)
- [3. Services & Pipeline](#3-services--pipeline)
- [4. API Endpoints](#4-api-endpoints)
- [5. Model Data](#5-model-data)
- [6. Knowledge Base & Data](#6-knowledge-base--data)
- [7. Cara Menjalankan](#7-cara-menjalankan)
- [8. Deployment (Production)](#8-deployment-production)
- [9. Testing](#9-testing)
- [10. Roadmap](#10-roadmap)
- [11. Integrasi sobat-paws](#11-integrasi-sobat-paws)
- [12. Lisensi & Etika Data](#12-lisensi--etika-data)

---

## Quick Links

| Resource | Link |
|----------|------|
| Swagger UI | `/docs` |
| ReDoc | `/redoc` |
| API Documentation | [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) |
| Request/Response Examples | [`docs/API_EXAMPLES.md`](docs/API_EXAMPLES.md) |
| Postman Collection | [`docs/EkosistemSatwa_API.postman_collection.json`](docs/EkosistemSatwa_API.postman_collection.json) |
| Deployment Guide | [`docs/deployment.md`](docs/deployment.md) |
| **Pawnia AI Companion** | [`PAWNIA.md`](PAWNIA.md) — Soul, Role & Architecture |
| AI Agent Guide | [`AGENTS.md`](AGENTS.md) |
| Jurnal Perhewanan | [`docs/jurnal/INDEX.md`](docs/jurnal/INDEX.md) |
| Integration Guide | [`docs/INTEGRATION.md`](docs/INTEGRATION.md) |
| Admin Panel Integration | [`docs/INTEGRATION_ADMIN_PANEL.md`](docs/INTEGRATION_ADMIN_PANEL.md) |
| **Integrasi sobat-paws** | [`docs/INTEGRASI_SOBATPAWS_PAWNIA.md`](docs/INTEGRASI_SOBATPAWS_PAWNIA.md) — Panduan integrasi admin panel & mobile |
| Alignment Analysis | [`docs/ALIGNMENT_ANALYSIS.md`](docs/ALIGNMENT_ANALYSIS.md) |

---

## 1. Arsitektur Sistem

```
+----------------------------------------------------------------------+
|                      APLIKASI EKSTERNAL                              |
|  (Android / iOS / Web / App Vet 3rd / Telegram)                      |
|  Input: teks, mic, kamera, gambar, video                             |
+----------------------------------+-----------------------------------+
                                   | REST API / JSON / Multipart
                                   v
+----------------------------------------------------------------------+
|                    EKOSISTEM SATWA BACKEND API                        |
|                                                                       |
|  +--------------------------------------------------------------+   |
|  |                    PAWNIA AI ORCHESTRATOR                      |   |
|  |  +----------+  +----------+  +----------+  +--------------+ |   |
|  |  |  Intent  |-> |  Risk    |-> |  Context |-> |  Agent       | |   |
|  |  | Detection|  | Classify |  |  Loader  |  |  Routing     | |   |
|  |  +----------+  +----------+  +----------+  +------+-------+ |   |
|  |                                                     |         |   |
|  |  +--------------------------------------------------+-------+ |   |
|  |  |              9 AGENT SPESIALIS                   |       | |   |
|  |  |  Companion | Emergency | VetEsc | Vision | ...   |       | |   |
|  |  +----------------------------------------------------------+ |   |
|  +--------------------------------------------------------------+   |
|                                                                       |
|  +--------------+  +--------------+  +--------------+  +----------+ |
|  |  EMR Service |  |Memory Service|  | RAG Pipeline |  |  Vision  | |
|  |  (PostgreSQL)|  | (STM + LTM)  |  | (Embeddings) |  | Analysis | |
|  +--------------+  +--------------+  +--------------+  +----------+ |
|                                                                       |
|  +--------------+  +--------------+  +----------------------------+ |
|  |  Notification|  |  Telegram    |  |  ML Pipeline (10 models)   | |
|  |  Service     |  |  Bot        |  |  RandomForest per species  | |
|  +--------------+  +--------------+  +----------------------------+ |
|                                                                       |
|  +--------------------------------------------------------------+   |
|  |              LEARNING LOOP (human-in-the-loop)                |   |
|  |  Doctor Feedback -> Gold Labels -> Retrain ML -> Registry    |   |
|  +--------------------------------------------------------------+   |
+----------------------------------------------------------------------+
```

### Komponen Utama

| Lapisan | Isi | Lokasi |
|---------|-----|--------|
| **AI Orchestrator** | Pawnia - 9 agent, intent detection, risk classification, safety layer | `src/ekosistem_satwa/ai/pawnia_orchestrator.py` |
| **AI Gateway** | Entry point REST untuk Pawnia | `src/ekosistem_satwa/api/ai_gateway_router.py` |
| **EMR Service** | 13 SQLAlchemy models, CRUD, pet context | `src/ekosistem_satwa/emr/` |
| **Memory Service** | Short-term (TTL 24h) + Long-term (permanent) | `src/ekosistem_satwa/ai/memory_store.py` |
| **RAG Pipeline** | Embeddings + Vector Store + Knowledge retrieval | `src/ekosistem_satwa/knowledge/` |
| **Vision Analysis** | Image/video analysis, skin lesion, breed ID | `src/ekosistem_satwa/vision/` |
| **Telegram Bot** | MTProto user-bot (Telethon) | `src/ekosistem_satwa/telegram/` |
| **ML Pipeline** | 10 RandomForest models per species | `src/ekosistem_satwa/ml/` |
| **Safety Layer** | Guardrails: poison rules, dosage refusal, tone boundaries | `src/ekosistem_satwa/ai/safety.py` |
| **Agent Manager** | 9 specialized agent routing & response generation | `src/ekosistem_satwa/ai/agent_manager.py` |
| **Smart Data Platform** | Orchestrator pipeline, doctor, registry lineage | `src/ekosistem_satwa/platform/` |
| **API Routers** | 14 router files (FastAPI) | `src/ekosistem_satwa/api/` |

---

## 2. Pawnia AI Orchestrator

Pawnia adalah **AI Orchestrator** - pusat kecerdasan yang mengoordinasikan **9 agent spesialis**. Setiap input user melewati pipeline 5-langkah:

```
User Input
   |
   +- 1. Intent Detection ---> 9 intent categories, threshold >70%
   |     (emergency, vision, behavior, nutrition, meal, medication, companion, dll.)
   |
   +- 2. Risk Classification ---> Scoring engine (0-100)
   |     Critical (71-100) -> Emergency Agent
   |     High (51-70) -> Vet Escalation
   |     Medium (31-50) -> Agent + Observasi
   |     Low (0-30) -> Agent normal + Edukasi
   |
   +- 3. Context Loading ---> 3 pilar informasi
   |     - Proprietary Context (pet profile, EMR dari EMR Service)
   |     - Memory Context (short-term + long-term dari Memory Service)
   |     - Knowledge Base (RAG dari Knowledge Service)
   |
   +- 4. Agent Routing ---> Decision tree
   |     Emergency > All | Image -> Vision | Confidence <60% -> Vet Escalation
   |
   +- 5. Response Generation ---> Template per agent + Safety Layer
   |     - Safety: poison ingestion rules, NO dosage, NO definitive diagnosis
   |     - Medical disclaimer always included
   |
   +- 6. Response ---> Structured JSON ke aplikasi
```

### 9 Agent Spesialis

| # | Agent | Trigger | Contoh Input |
|---|-------|---------|-------------|
| 1 | **Pet Companion** | Sapaan umum, fallback | "Halo", "Cara merawat kucing" |
| 2 | **Triage & Emergency** | Kata kunci emergency, Risk >70 | "Kejang", "Pendarahan", "Tidak sadar" |
| 3 | **Vet Escalation** | Confidence <60%, minta dokter | "Saya mau konsultasi dengan dokter" |
| 4 | **Vision Screening** | Upload foto/gambar | [Foto kulit/mata/telinga] |
| 5 | **Behavior Insight** | Gangguan perilaku klinis | "Agresif", "Pincang", "Gelisah" |
| 6 | **Behavior Fun** | AI Pet Translator, mood | "Mood kucing saya?" |
| 7 | **Nutrition Advisor** | Diet, alergi, suplemen | "Makanan untuk obesitas" |
| 8 | **Meal Planner** | Jadwal makan, porsi | "Buat jadwal makan kucing" |
| 9 | **Medication Adherence** | Vaksin, obat, reminder | "Jadwal vaksinasi" |

### AI Gateway Endpoint

**`POST /api/v1/ai/chat`** - Entry point utama untuk semua interaksi user.

```json
// Request
{
  "message": "Kucing saya muntah dan lemas",
  "session_id": "uuid-xxx",
  "pet_id": "uuid-pet",
  "image_base64": null
}

// Response
{
  "agent": "triage_emergency",
  "confidence": 0.92,
  "risk_score": 85,
  "risk_level": "critical",
  "response": {
    "text": "...",
    "suggestions": [...],
    "cta": "Segera bawa ke klinik hewan terdekat",
    "disclaimer": "..."
  },
  "context_used": {
    "intent_detection": {...},
    "risk_classification": {...},
    "memory": {...},
    "proprietary": {...}
  },
  "escalated": true,
  "conversation_id": "uuid-xxx"
}
```

Dokumentasi lengkap Pawnia: [`PAWNIA.md`](PAWNIA.md)

---

## 3. Services & Pipeline

### 3.1 EMR Service (`src/ekosistem_satwa/emr/`)

Medical record management dengan PostgreSQL. 13 SQLAlchemy models:

| Model | Deskripsi |
|-------|-----------|
| `User` | Pemilik hewan / dokter |
| `Pet` | Data dasar hewan |
| `PetProfile` | Profil medis lengkap |
| `EMRRecord` | Rekam medis elektronik |
| `Vaccination` | Riwayat vaksinasi |
| `Medication` | Obat-obatan |
| `Consultation` | Sesi konsultasi |
| `ConversationThread` | Thread percakapan AI |
| `ConversationMessage` | Pesan dalam thread |
| `AIMemory` | Memori AI jangka panjang |
| `Recommendation` | Rekomendasi sistem |
| `Notification` | Notifikasi & reminder |
| `AuditLog` | Log audit |

**Key API:** `get_pet_context(pet_id)` - agregasi data pet untuk AI Gateway.

### 3.2 Memory Service (`src/ekosistem_satwa/ai/memory_store.py`)

| Tipe | Storage | TTL | Fungsi |
|------|---------|-----|--------|
| **Short-term** | JSONL + in-memory cache | 24 jam inactivity | Active conversation state, last intent, recent messages |
| **Long-term** | PostgreSQL (`ai_memory` table) | Permanent | User preferences, pet history summary, dietary notes |

### 3.3 RAG Pipeline (`src/ekosistem_satwa/knowledge/`)

| Module | Fungsi |
|--------|--------|
| `embeddings.py` | OpenAI text-embedding-3-small (fallback Ollama) |
| `vector_store.py` | In-memory vector store with JSON persistence |
| `rag.py` | Retrieval-Augmented Generation pipeline |

### 3.4 Vision Analysis (`src/ekosistem_satwa/vision/`)

| Module | Fungsi |
|--------|--------|
| `analyzer.py` | Image analysis: skin lesions, eye/ear issues, breed identification |
| `image_utils.py` | Image preprocessing, resize, normalize |
| `video_utils.py` | Video frame extraction |

### 3.5 Telegram Bot (`src/ekosistem_satwa/telegram/`)

MTProto user-bot menggunakan Telethon (ConnectionTcpFull). Berjalan sebagai container terpisah (`pawnia-telegram`).

### 3.6 ML Pipeline (`src/ekosistem_satwa/ml/`)

| Komponen | Fungsi |
|----------|--------|
| `dataset_builder.py` | Build dataset symptom->disease (cold-start + clinical merge) |
| `feature_engineering.py` | Feature store + breed_risk_profile |
| `train.py` | RandomForestClassifier per species (10 models) |
| `predict.py` | Top-K disease inference |
| `retrain.py` | Retrain with doctor feedback (gold labels) |

### 3.7 Learning Loop (Human-in-the-Loop)

```
Consultation -> AI Suggestion -> Doctor Feedback -> Gold Labels -> Retrain ML -> Model Registry
```

### 3.8 Safety Layer (`src/ekosistem_satwa/ai/safety.py`)

| Rule | Behavior |
|------|----------|
| **NO prescription dosage** | Refuses dosage for prescription meds |
| **NO home remedies** | No ramuan rumah, minyak kayu putih, madu |
| **Poison ingestion** | JANGAN sarankan memuntahkan -> LANGSUNG Emergency |
| **NO definitive diagnosis** | Always uses probabilistic language |
| **Medical disclaimer** | Always included in responses |
| **Tone boundary** | Dilarang "tidak usah khawatir", slang kasual |
| **Drug contraindications** | Kucing: paracetamol/permethrin/ibuprofen = FATAL |
| | Kelinci/rodensia: penicillin/amoxicillin oral = fatal |

---

## 4. API Endpoints

### 4.1 Pawnia AI Gateway (`/api/v1/ai`)

| Method | Path | Deskripsi |
|--------|------|-----------|
| POST | `/api/v1/ai/chat` | Main entry - text + optional image |
| POST | `/api/v1/ai/chat/multipart` | Multipart form + file upload |
| POST | `/api/v1/ai/chat/simple` | Query-based testing |
| GET | `/api/v1/ai/status` | Pawnia system status (9 agents) |

### 4.2 EMR (`/api/v1`)

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/api/v1/pets?user_id=X` | Daftar pets by user |
| GET | `/api/v1/pets/{id}` | Detail pet |
| GET | `/api/v1/pets/{pet_id}/context` | Consolidated pet context for AI |
| GET | `/api/v1/pets/{pet_id}/consultations` | AI consultation history |
| POST | `/api/v1/pets/{pet_id}/sync` | Trigger EMR->Memory sync |
| POST | `/api/v1/users/{user_id}/sync-all` | Batch sync all pets |
| GET | `/api/v1/emr/{petId}` | EMR records |
| POST | `/api/v1/emr/{petId}` | Create EMR record |
| GET | `/api/v1/vaccinations/{petId}` | Vaccination history |
| POST | `/api/v1/vaccinations/{petId}` | Add vaccination |

### 4.3 Memory (`/api/v1/memory`)

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/api/v1/memory/context` | Load context for AI Gateway |
| POST | `/api/v1/memory/save-conversation` | Save conversation to memory |

### 4.4 Knowledge / RAG (`/api/v1/knowledge`)

| Method | Path | Deskripsi |
|--------|------|-----------|
| POST | `/api/v1/knowledge/query` | Query knowledge base (RAG) |
| GET | `/api/v1/knowledge/stats` | Knowledge base statistics |
| POST | `/api/v1/knowledge/reindex` | Reindex all sources |


---

## 4.5 Integration Endpoints (Admin Panel)

Endpoint khusus untuk integrasi dengan **sobatpaws-admin** (PetPro Admin Panel).
Semua endpoint menggunakan JWT auth (compatible dengan cookie-based auth admin panel).

### AI Pre-Screening
```http
POST /api/v1/integration/appointment/screening
?species=cat&breed=cat-persian&age_years=3
&symptoms=muntah,lemas,tidak mau makan&duration_days=2
```

Response:
```json
{
  "success": true,
  "data": {
    "risk_level": "high",
    "risk_score": 65,
    "agent": "triage_emergency",
    "confidence": 0.85,
    "suggested_specialist": "dokter_hewan_umum",
    "urgency": "within_24h",
    "ai_summary": "...",
    "escalated": false,
    "suggestions": [...],
    "cta": [...],
    "disclaimer": "..."
  }
}
```

### Pet Medical History
```http
GET /api/v1/integration/customer/{external_id}/medical-history?pet_id={pet_id}
```

Returns: pet profile, vaccinations, active medications, chronic conditions, allergies.

### Product Recommendation
```http
POST /api/v1/integration/product/recommend
?species=dog&breed=dog-golden&age_years=5&condition=obesitas
```

Returns: AI-powered product suggestions based on pet condition.

### Integration Health
```http
GET /api/v1/integration/health
```

### Authentication
| Method | Header |
|--------|--------|
| JWT Bearer | `Authorization: Bearer *** |
| JWT Cookie | `access_token=<token>` (cookie) |
| API Key | `X-EkosistemSatwa-Key: <key>` |

### Dokumen Lengkap
- [`docs/ALIGNMENT_ANALYSIS.md`](docs/ALIGNMENT_ANALYSIS.md) — Gap analysis & alignment plan
- [`docs/INTEGRATION_ADMIN_PANEL.md`](docs/INTEGRATION_ADMIN_PANEL.md) — Admin panel integration guide

---

## 4.6 EMR Endpoints

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/api/v1/pets?user_id=X` | Daftar pets by user |
| GET | `/api/v1/pets/{id}` | Detail pet |
| GET | `/api/v1/pets/{pet_id}/context` | Consolidated pet context for AI |
| GET | `/api/v1/pets/{pet_id}/consultations` | AI consultation history |
| POST | `/api/v1/pets/{pet_id}/sync` | Trigger EMR->Memory sync |
| POST | `/api/v1/users/{user_id}/sync-all` | Batch sync all pets |
| GET | `/api/v1/emr/{petId}` | EMR records |
| POST | `/api/v1/emr/{petId}` | Create EMR record |
| GET | `/api/v1/vaccinations/{petId}` | Vaccination history |
| POST | `/api/v1/vaccinations/{petId}` | Add vaccination |
| GET | `/api/v1/emr/health` | EMR service health |


### 4.7 Core API (`main.py`)

| Method | Path | Auth | Deskripsi |
|--------|------|------|-----------|
| GET | `/health` | - | Status sistem |
| GET | `/api/status` | - | Status detail backend, AI, ML, DB |
| GET | `/categories` | - | Daftar kategori spesies |
| GET | `/breeds/{slug}` | - | Ras per spesies |
| GET | `/diseases/{slug}` | - | Detail penyakit |
| POST | `/api/consult` | Vet | Single-shot consult |
| POST | `/ml/predict` | - | Prediksi symptom->disease |
| POST | `/consultations` | Vet | Mulai sesi konsultasi |
| POST | `/consultations/{id}/turns` | Vet | Giliran lanjutan |
| POST | `/consultations/{id}/feedback` | Vet | Feedback saran AI |
| POST | `/learning/retrain` | Admin | Retrain ML |
| GET | `/exports/excel` | - | Unduh workbook Excel |

### 4.8 Integration (`/api/integration`)

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/manifest` | Kontrak integrasi untuk developer app |
| GET | `/id-schema` | Skema ID entitas |
| GET | `/entities/{consultation_id}` | Lookup bundle ID |
| GET | `/capabilities` | Fitur yang tersedia |

### 4.9 Platform (`/api/platform`)

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/manifest` | Kontrak agent-friendly |
| GET | `/doctor` | Health check pipeline |
| GET | `/registry` | Lineage registry |
| GET | `/pipeline` | Daftar step pipeline |
| POST | `/pipeline/run` | Jalankan pipeline (Admin) |

### 4.10 Agent (`/api/agent`)

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/providers` | Daftar provider LLM |
| GET | `/providers/status` | Status provider |
| GET | `/conversations` | Riwayat sesi |
| GET | `/suggestions` | Riwayat saran AI |

### 4.11 Notification (`/api/v1/notifications`)

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/api/v1/notifications/{user_id}` | Get user notifications |
| POST | `/api/v1/notifications` | Create notification |
| PUT | `/api/v1/notifications/{id}/read` | Mark as read |

### 4.12 Admin (`/api/admin`)

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/overview` | Ringkasan sistem |
| GET | `/ai/usage` | Penggunaan token LLM |
| GET | `/learning/events` | Event pembelajaran |

### Autentikasi

| Header | Untuk |
|--------|-------|
| `X-API-Key` (Vet key) | Endpoint bertanda **Vet** |
| `X-API-Key` (Admin key) | Endpoint bertanda **Admin** |
| `X-EkosistemSatwa-Key` | Pawnia Client Library auth |

---

## 5. Model Data

`dbml/schema.dbml` mencakup 5 domain:

1. **Taxonomy** - `animal_categories`, `breeds`, `breed_variants`, `breed_traits`
2. **Clinical** - `diseases`, `symptoms`, `disease_symptoms`, `diagnostic_methods`, `treatments`, `products`, `breed_disease_susceptibility`, `product_species_safety`
3. **Operational** - `organizations`, `users`, `pet_owners`, `pets`, `clinical_cases`, `case_symptoms`, `case_diagnoses`, `case_treatments`
4. **ML** - `data_sources`, `ml_datasets`, `dataset_sources`, `feature_definitions`, `dataset_features`, `ml_models`, `ml_predictions`, `ml_feedback`
5. **AI** - `ai_providers`, `ai_prompt_templates`, `ai_conversations`, `ai_requests`, `ai_suggestions`

Render diagram: tempel isi `schema.dbml` ke [dbdiagram.io](https://dbdiagram.io).

---

## 6. Knowledge Base & Data

### Cakupan Data

| Item | Jumlah | Catatan |
|------|--------|---------|
| Kategori spesies | **11** | dog, cat, rabbit, hamster, poultry, fish, reptile, amphibian, ferret, guinea_pig, others |
| Ras/breed | **177** | dengan varian & traits untuk fitur ML |
| **Diseases (Active)** | **11000** | 1.000 per spesies untuk performa API |
| **Diseases (Generated)** | **315,000+** | Full archive siap dimuat kapan saja |
| **Auto-Expansion** | ✅ Setiap 10 menit | Cron menuju target 350.000 diseases |
| Gejala unik | **207** | dapat diobservasi klinis |
| AI Agents | **9** | Orchestrator multi-agent Pawnia |
| Model ML terlatih | **3** | Triage, Treatment, Forecasting |
| Dataset sintetik | **500K baris** | Untuk validasi & bulk training |
| Jurnal riset | **130+ ras**, **30 penyakit** | Monograf terdokumentasi |
| AI Providers | **5** | OpenAI, Anthropic, SumoPod, Qwen, Local |

## Expansion Pipeline
```bash
# Auto-expand setiap 10 menit via cron
scripts/generate_diseases_massive.py    # Generate → 350K target
scripts/sync_catalogs_from_kb.py        # Sync ke format KB
scripts/auto_deploy_kb.sh               # Deploy + Push otomatis
```

### Struktur Data

```
data/
+-- categories.json              # 10 kategori spesies
+-- breeds/
|   +-- dogs.json  cats.json  rabbits.json  hamsters.json
|   +-- poultry.json  fish.json  reptiles.json  others.json
+-- clinical/
|   +-- diseases_dogs.json       # penyakit + gejala + diagnosa + tindakan + produk
|   +-- diseases_cats.json
|   +-- diseases_rabbits.json    diseases_hamsters.json
|   +-- diseases_poultry.json    diseases_fish.json
|   +-- diseases_reptiles.json   diseases_exotic_others.json
|   +-- extensions/
|       +-- medication_kb.json   # knowledge base obat per spesies
+-- generated/                   # dataset sintetik (gitignored)
+-- ml_views/                    # view ML terkompresi (Parquet/gzip-CSV)

docs/jurnal/                     # monograf riset per spesies, ras, penyakit
+-- INDEX.md                     # auto-generated index
+-- spesies/  ras/  penyakit/
```

---

## 7. Cara Menjalankan

### Prasyarat

- Python **3.10+** (3.9 dengan `eval_type_backport`)
- (Opsional) PostgreSQL untuk seed & learning store
- (Opsional) Ollama / vLLM untuk inferensi LLM lokal

### Instalasi

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
export PYTHONPATH=src
```

### a) Validasi data

```bash
python -m ekosistem_satwa.data_loader
# -> categories: 10, breeds: 177, diseases: 44, unique_symptoms: 207
```

### b) Generate seed SQL

```bash
python -m ekosistem_satwa.seed_generator           # -> seed/seed.sql
psql "$DATABASE_URL" -f seed/schema.sql
psql "$DATABASE_URL" -f seed/seed.sql
```

### c) Latih model ML

```bash
python -m ekosistem_satwa.ml.train                 # semua kategori (10 model)
python -m ekosistem_satwa.ml.train --category dog  # satu kategori
```

### d) Prediksi cepat

```bash
python -m ekosistem_satwa.ml.predict dog "Muntah hebat" "Diare berdarah" "Lemas/lesu"
# -> dog-parvovirus (0.94), ...
```

### e) Jalankan API Server

```bash
./run.sh              # default port 8000
./run.sh 8080         # port lain
```

Atau manual:
```bash
uvicorn ekosistem_satwa.api.main:app --reload --app-dir src
```

**Akses:**
- Dashboard: http://localhost:8000/
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### f) Coba AI Gateway (Pawnia)

```bash
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "Kucing saya muntah dan lemas", "pet_id": "test-123"}'
```

### g) Pipeline Platform

```bash
python -m ekosistem_satwa.platform.doctor
python -m ekosistem_satwa.platform.pipeline --preset ml_ready
python -m ekosistem_satwa.platform.registry --refresh
```

### h) Export Excel & Build Jurnal

```bash
python3 scripts/generate_all.py
python3 scripts/export_excel.py
python3 scripts/build_journal_index.py
```

---

## 8. Konfigurasi Provider AI

Ekosistem Satwa mendukung multiple AI provider dengan failover chain.

### Provider yang Didukung

| Provider | Type | Model Default | API Key |
|----------|------|---------------|---------|
| **SumoPod** 🏆 | custom | `deepseek-v4-pro` | `SUMOPOD_AI_API_KEY` |
| **Local** (Ollama) | local_llm | `llama3.2` | - (Ollama default) |

### Konfigurasi via providers.json

File `artifacts/ai/providers.json` mengatur provider aktif:

```json
{
  "providers": [
    {"id": "sumopod", "kind": "custom", "base_url": "https://ai.sumopod.com/v1",
     "default_model": "deepseek-v4-pro", "is_primary": true},
    {"id": "local", "kind": "local_llm", "base_url": "http://host.docker.internal:11434/v1",
     "default_model": "llama3.2", "is_primary": false}
  ]
}
```

### Priority & Fallback
1. **SumoPod** (primary) — deepseek-v4-pro untuk semua request AI
2. **Ollama local** (fallback) — llama3.2 jika SumoPod unreachable

### Menambah Provider Baru
Via Admin Dashboard → tab **🤖 AI Providers** → klik **Add Provider**.

## 9. Deployment (Production)

### Architecture

```
+----------------------------------------------------------------+
|                     Docker Host (VPS)                            |
|                                                                  |
|  +--------------+    +--------------+    +--------------------+ |
|  |  sobatpaws-  |    |  sobatpaws-  |    |  pawnia-          | |
|  |  api         |--> |  db          |    |  telegram          | |
|  |  (port 8080) |    |  (port 5432) |    |  (bot)             | |
|  +--------------+    +--------------+    +--------------------+ |
|         |                                                       |
|         v                                                       |
|  +--------------+                                               |
|  |  host.docker |  (Ollama / vLLM for local inference)         |
|  |  .internal   |  extra_hosts + OLLAMA_HOST=0.0.0.0          |
|  +--------------+                                               |
+----------------------------------------------------------------+
```

### Quick Start

```bash
git clone https://github.com/winspaws/Sobatpaws-ai.git
cd Sobatpaws-ai
cp .env.production .env
docker compose -f docker-compose.prod.yml up -d
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/ai/status
```

### Resource Limits

| Service | CPU | Memory |
|---------|-----|--------|
| API | 2.0 cores | 2 GB |
| PostgreSQL | 1.0 core | 1 GB |

Full guide: [`docs/deployment.md`](docs/deployment.md)

---

## 9. Testing

```bash
# Semua test
pytest tests/ -v

# Pawnia Orchestrator (755+ lines)
pytest tests/test_pawnia_orchestrator.py -v

# EMR Service (19 tests)
pytest tests/test_emr_service.py -v

# API Integration
pytest tests/test_api_integration.py -v
```

---

## 10. Roadmap

### Selesai (Sprint 1-3)
- REST API FastAPI + ML pipeline (10 models)
- Pawnia AI Orchestrator - 9 agent multi-agent system
- AI Gateway - POST /api/v1/ai/chat
- EMR Service - 13 SQLAlchemy models, PostgreSQL
- Memory Service - STM (TTL 24h) + LTM (permanent)
- RAG Pipeline - Embeddings + Vector Store
- Vision Analysis - Image/video analysis
- Notification Service - Smart reminders
- Safety Layer - Poison rules, dosage refusal
- PostgreSQL VIEWs - 3 reporting views
- Prompt Engineering & RAG Tuning - Safety score 1.00

### Selesai (Sprint 4 - Admin Panel Integration)
- JWT Auth Middleware (Bearer + Cookie + API Key dual auth)
- 9 Integration Endpoints untuk admin panel (screening, medical history, dashboard, vision, safety, learning loop)
- Data Model Alignment (User: first_name, last_name, address, avatar_url, dob; Pet: color, microchip)
- Alembic Migration 002 (upgrade/downgrade/idempotent)
- Learning Loop Dashboard (stats + retrain trigger)
- Vision Analysis for Admin (skin lesion upload endpoint)
- Safety Layer Integration (5 kontraindikasi: species, drug interaction, condition, age, breed MDR1)
- Dashboard AI Insights (species distribution, disease trends, breed risk profiles)
- Integration Endpoint Tests
- CRITICAL FIX: Dockerfile CMD path was using old sobatpaws.api.main, now fixed to ekosistem_satwa.api.main

### Dalam Pengerjaan (Sprint 5 - Knowledge Expansion) 🚀
- Perluas KB penyakit dari 44 -> ratusan per spesies (sedang dikerjakan research)
- Triage-Severity ML Model
- Vector Search untuk RAG literatur
- Retrain ML Models with expanded KB

---

## 11. Integrasi sobat-paws

Ekosistem Satwa API menyediakan **9 Integration Endpoints** untuk diintegrasikan ke aplikasi sobat-paws (admin panel, mobile app, web).

### Dokumen Integrasi

| Dokumen | Deskripsi |
|---------|-----------|
| [`docs/INTEGRASI_SOBATPAWS_PAWNIA.md`](docs/INTEGRASI_SOBATPAWS_PAWNIA.md) | **Panduan integrasi** — step-by-step integrasi admin panel & mobile |
| [`docs/INTEGRATION_ADMIN_PANEL.md`](docs/INTEGRATION_ADMIN_PANEL.md) | Analisis gap & rencana integrasi sobatpaws-admin (17 modul) |
| [`docs/INTEGRATION.md`](docs/INTEGRATION.md) | Panduan integrasi vet app & legacy systems |
| [`docs/ALIGNMENT_ANALYSIS.md`](docs/ALIGNMENT_ANALYSIS.md) | Alignment score per domain (Auth, Data Model, API) |

### Endpoints Tersedia

| Endpoint | Fungsi | Auth |
|----------|--------|------|
| `POST /api/v1/integration/appointment/screening` | AI Pre-Screening | JWT/API Key |
| `GET /api/v1/integration/customer/{id}/medical-history` | Riwayat medis pet | JWT/API Key |
| `POST /api/v1/integration/product/recommend` | Rekomendasi produk | JWT/API Key |
| `GET /api/v1/integration/dashboard/insights` | AI Dashboard Insights | JWT/API Key |
| `POST /api/v1/integration/vision/skin-lesion` | Analisis lesi kulit | JWT/API Key |
| `POST /api/v1/integration/safety/check-contraindication` | Cek kontraindikasi obat | JWT/API Key |
| `GET /api/v1/integration/learning-loop/stats` | Stats feedback ML | JWT/API Key |
| `POST /api/v1/integration/learning-loop/trigger-retrain` | Trigger retrain | JWT/API Key |
| `GET /api/v1/integration/health` | Health check | Public |

> VPS: `43.129.56.221:8080` | Semua endpoint live dengan 9 Pawnia agents

## 12. Lisensi & Etika Data

Data kurasi bersifat edukatif. Saat menambah data klinis nyata, lakukan
**anonimisasi** (`clinical_cases.is_anonymized`) dan patuhi regulasi privasi.
Penyakit unggas menular tertentu (mis. ND/AI) **wajib dilaporkan** ke dinas
peternakan setempat.

---

## Pawnia - The Soul of Ekosistem Satwa

> *"The Empathetic Veterinary Guide"* - Pemandu Kesehatan Hewan yang Empatik, Edukatif, dan Protektif

Baca selengkapnya: [`PAWNIA.md`](PAWNIA.md)

---

*Ekosistem Satwa v2.2.0 - Naincode AI Dept - 2026 | Sprint 4 ✅ Admin Panel Integration | Sprint 5 🚀 Knowledge Expansion*