# 📘 Ekosistem Satwa API Documentation

> **Base URL:** `http://43.129.56.221:8080`
> **Version:** 0.3.0 (OAS 3.1)
> **Swagger UI:** [`/docs`](http://43.129.56.221:8080/docs)
> **ReDoc:** [`/redoc`](http://43.129.56.221:8080/redoc)
> **OpenAPI JSON:** [`/openapi.json`](http://43.129.56.221:8080/openapi.json)
> **Postman Collection:** [`EkosistemSatwa_API.postman_collection.json`](./EkosistemSatwa_API.postman_collection.json)

---

## 📋 Daftar Isi

1. [Tentang Ekosistem Satwa API](#1-tentang-ekosistem-satwa-api)
2. [Autentikasi](#2-autentikasi)
3. [Flow Integrasi Utama](#3-flow-integrasi-utama)
4. [Endpoint Reference](#4-endpoint-reference)
   - [4.1 System & Health](#41-system--health)
   - [4.2 Master Data (Knowledge Base)](#42-master-data-knowledge-base)
   - [4.3 Konsultasi (Multimodal)](#43-konsultasi-multimodal)
   - [4.4 AI Agent](#44-ai-agent)
   - [4.5 ML Prediction](#45-ml-prediction)
   - [4.6 Single-Shot Consult](#46-single-shot-consult)
   - [4.7 Learning Loop](#47-learning-loop)
   - [4.8 Integrasi Vet App](#48-integrasi-vet-app)
   - [4.9 Smart Data Platform](#49-smart-data-platform)
   - [4.10 Data Analysis & Simulation](#410-data-analysis--simulation)
   - [4.11 Upload & Auto-Ingest](#411-upload--auto-ingest)
   - [4.12 Admin Dashboard](#412-admin-dashboard)
   - [4.13 Dataset & Exports](#413-dataset--exports)
5. [Schema Reference](#5-schema-reference)
6. [Postman Collection](#6-postman-collection)
7. [Error Handling](#7-error-handling)
8. [Rate Limits & Best Practices](#8-rate-limits--best-practices)

---

## 1. Tentang Ekosistem Satwa API

**Ekosistem Satwa** adalah Backend AI Services untuk dokter hewan — menyediakan REST API, ML inference, dan AI suggestion engine yang diintegrasikan oleh aplikasi eksternal (Android, iOS, Web, App Vet pihak ketiga).

### Arsitektur

```
APLIKASI EKSTERNAL (Android / iOS / Web / App Vet 3rd)
         │
         ▼
┌─────────────────────────────────────────────┐
│         EKOSISTEM SATWA BACKEND API                │
│                                              │
│  Knowledge Base (JSON) → ML Pipeline → AI    │
│  Suggestion Engine (RAG) → Safety Guardrail  │
│                                              │
│  REST Endpoints:                             │
│  Input API │ AI/ML │ Integration │ Platform  │
│                                              │
│  Learning Loop (doctor feedback → retrain)   │
└─────────────────────────────────────────────┘
```

### Prinsip Kerja

| Prinsip | Penjelasan |
|---------|-----------|
| **RAG-based** | AI tidak mengarang — di-*ground* pada knowledge base terstruktur |
| **ML-first** | RandomForest per spesies untuk prediksi symptom→disease |
| **Safety guardrail** | Kontraindikasi obat per spesies (hard-rule) |
| **Smart augmentation** | Mode `smart` melewati LLM bila ML+KB sudah yakin (hemat token) |
| **Human-in-the-loop** | Feedback dokter → gold labels → retrain ML |

### Cakupan Data

| Item | Jumlah |
|------|--------|
| Kategori spesies | 10 (dog, cat, rabbit, hamster, poultry, fish, reptile, amphibian, ferret, guinea_pig) |
| Ras/Breed | 160+ |
| Penyakit | 347+ (tersebar per spesies) |
| Gejala unik | 130+ |
| Dataset sintetik | 557.410 baris |

---

## 2. Autentikasi

Saat ini autentikasi bersifat **opsional** (development mode). Untuk production, gunakan header:

```
X-EkosistemSatwa-Key: <your_vet_api_key>
```

Atau header alternatif:

```
Authorization: Bearer <your_token>
```

> **Catatan:** Endpoint admin (`/admin/*`) dan pipeline (`POST /api/platform/pipeline/run`) memerlukan `X-EkosistemSatwa-Key` atau `Authorization` dengan level admin.

---

## 3. Flow Integrasi Utama

### Flow Lengkap Konsultasi

```
1. GET  /health                          → Cek koneksi & status sistem
2. GET  /api/integration/id-schema       → Kontrak ID entitas
3. GET  /categories                      → Muat daftar spesies
4. GET  /categories/{slug}/breeds        → Muat daftar ras per spesies
5. POST /consultations                   → Mulai sesi konsultasi
   (context: org_id, vet_id, owner_id, pet_id)
6. POST /consultations/{id}/turns        → Kirim teks tambahan (opsional)
7. POST /consultations/{id}/media        → Upload audio/gambar (opsional)
8. Tampilkan AISuggestion ke dokter
9. POST /consultations/{id}/doctor-input → Simpan keputusan dokter
10. POST /consultations/{id}/feedback    → Penilaian saran AI
11. POST /learning/retrain               → Retrain ML dari gold labels
```

### Flow Cepat (Single-Shot)

```
POST /api/consult       → Saran klinis langsung, tanpa sesi
POST /ml/predict        → Prediksi ML cepat, tanpa LLM
```

---

## 4. Endpoint Reference

### 4.1 System & Health

#### `GET /health`

Cek status sistem secara cepat.

**Response `200`:**

```json
{
  "status": "ok",
  "llm_available": true,
  "knowledge_base": {
    "categories": 10,
    "breeds": 177,
    "diseases": 44,
    "unique_symptoms": 146
  },
  "learning_store": {
    "consultation": 70,
    "intake": 83,
    "suggestion": 83,
    "doctor_input": 8,
    "feedback": 9
  }
}
```

#### `GET /api/status`

Status terpadu seluruh komponen (data, AI, ML, DB, token usage).

**Response `200`:** JSON dengan status detail per komponen.

---

### 4.2 Master Data (Knowledge Base)

#### `GET /categories`

Daftar semua kategori spesies.

**Response `200`:**

```json
[
  {
    "slug": "dog",
    "name": "Dog",
    "name_id": "Anjing",
    "species_class": "mammal",
    "scientific_name": "Canis lupus familiaris",
    "description": "Mamalia karnivora domestikasi paling umum...",
    "avg_lifespan_years_min": 10,
    "avg_lifespan_years_max": 16
  },
  {
    "slug": "cat",
    "name": "Cat",
    "name_id": "Kucing",
    "species_class": "mammal",
    "scientific_name": "Felis catus",
    "description": "Mamalia karnivora obligat...",
    "avg_lifespan_years_min": 12,
    "avg_lifespan_years_max": 18
  }
]
```

#### `GET /categories/{slug}/breeds`

Daftar ras untuk satu spesies.

**Parameters:**
| Name | In | Type | Required |
|------|----|------|----------|
| `slug` | path | string | ✅ |

#### `GET /breeds/{slug}`

Detail satu ras.

**Parameters:**
| Name | In | Type | Required |
|------|----|------|----------|
| `slug` | path | string | ✅ |

#### `GET /diseases/{slug}`

Detail satu penyakit.

**Parameters:**
| Name | In | Type | Required |
|------|----|------|----------|
| `slug` | path | string | ✅ |

#### `GET /api/symptoms`

Daftar gejala unik, opsional difilter per kategori.

**Parameters:**
| Name | In | Type | Required |
|------|----|------|----------|
| `category` | query | string | ❌ |

#### `GET /api/stats/breakdown`

Rincian jumlah data: ras, varian, traits, penyakit + analitik varian.

#### `GET /api/stats/breeds`

Daftar ras dengan ringkasan varian/traits.

**Parameters:**
| Name | In | Type | Required |
|------|----|------|----------|
| `category` | query | string | ❌ |
| `q` | query | string | ❌ |
| `sort` | query | string | ❌ |
| `limit` | query | integer | ❌ |

---

### 4.3 Konsultasi (Multimodal)

#### `POST /consultations`

Mulai sesi konsultasi baru. Memproses keluhan pertama (text/audio/image) → saran AI.

**Headers (opsional):**
```
X-EkosistemSatwa-Key: <api_key>
Content-Type: application/json
```

**Request Body:**

```json
{
  "context": {
    "vet_id": 1,
    "owner_id": 100,
    "pet_id": 200,
    "category_slug": "cat",
    "breed_slug": "cat-persian",
    "age_years": 3,
    "sex": "male",
    "weight_kg": 4.5,
    "external_consultation_id": "ext-20250619-001"
  },
  "intake": {
    "channel": "chat",
    "text": "Kucing saya muntah hebat dan tidak mau makan sejak kemarin",
    "is_first_contact": true,
    "author_role": "owner"
  }
}
```

**Response `200`:**

```json
{
  "consultation_id": "ext-20250619-001",
  "intake": {
    "complaint_text": "Kucing saya muntah hebat dan tidak mau makan sejak kemarin",
    "observations": [],
    "symptoms": [
      {
        "name_id": "Muntah",
        "name": "Vomiting",
        "body_system": "digestive",
        "is_red_flag": false,
        "score": 0.95,
        "matched_text": "muntah"
      },
      {
        "name_id": "Nafsu makan menurun",
        "name": "Poor appetite",
        "body_system": "digestive",
        "is_red_flag": false,
        "score": 0.8,
        "matched_text": "tidak mau makan"
      }
    ],
    "channel": "chat",
    "created_at": "2026-06-19T13:00:56.632184Z"
  },
  "suggestion": {
    "suggestion_type": "symptom_to_disease",
    "summary": "Berdasarkan gejala terdeteksi, kemungkinan teratas: ...",
    "follow_up_questions": [
      "Sudah berapa lama gejala ini berlangsung?",
      "Apakah nafsu makan & minum berubah?"
    ],
    "suggested_diseases": [
      {
        "disease_slug": "cat-fpv-panleukopenia",
        "name_id": "Panleukopenia (Distemper Kucing)",
        "confidence": 0.784,
        "rationale": "Cocok dengan gejala: Muntah hebat, Diare hebat",
        "is_emergency": true,
        "source": "ml+knowledge_base"
      }
    ],
    "suggested_diagnostics": [
      {
        "name": "PCR feses",
        "type": "pcr_molecular",
        "step_order": 2,
        "is_gold_standard": true,
        "expected_finding": "DNA FPV",
        "for_disease": "cat-fpv-panleukopenia"
      }
    ],
    "suggested_treatments": [...],
    "suggested_products": [...],
    "red_flags": [...],
    "safety_warnings": [...],
    "references": [...],
    "is_emergency": true,
    "generated_by": "rule_based",
    "disclaimer": "Output ini bersifat pendukung keputusan klinis...",
    "created_at": "2026-06-19T13:00:56.632184Z"
  },
  "suggestion_id": "uuid-xxx",
  "entities": {
    "vet_id": 1,
    "owner_id": 100,
    "pet_id": 200,
    "consultation_id": "ext-20250619-001"
  }
}
```

#### `GET /consultations/{consultation_id}`

Detail sesi konsultasi.

**Parameters:**
| Name | In | Type | Required |
|------|----|------|----------|
| `consultation_id` | path | string | ✅ |

#### `POST /consultations/{consultation_id}/turns`

Giliran lanjutan dalam sesi (chat/video) → saran diperbarui kumulatif.

**Request Body:**

```json
{
  "intake": {
    "channel": "chat",
    "text": "Sekarang kucing saya juga diare",
    "is_first_contact": false,
    "author_role": "owner"
  }
}
```

#### `POST /consultations/{consultation_id}/media`

Upload media mentah (mic/kamera) sebagai multipart → proses & saran.

**Request (multipart/form-data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | ✅ | File audio/gambar |
| `modality` | string | ❌ | `audio`, `image`, `video_frame` |
| `channel` | string | ❌ | `chat`, `video`, `voice`, `in_person` |

> **Tip:** Gunakan `pretranscribed_text` di JSON bila STT sudah di device — hemat token Whisper.

#### `POST /consultations/{consultation_id}/doctor-input`

Simpan keputusan dokter (diagnosa/tindakan/resep) sebagai **gold label** untuk retraining.

**Request Body:**

```json
{
  "confirmed_disease_slug": "cat-fpv-panleukopenia",
  "differential_disease_slugs": ["cat-ckd"],
  "confirmed_symptoms": ["Muntah", "Diare hebat", "Nafsu makan menurun"],
  "diagnostics_ordered": ["PCR feses", "CBC"],
  "treatments_given": ["Terapi suportif rawat inap parvo"],
  "products_prescribed": ["Maropitant (Cerenia)"],
  "clinical_notes": "Pasien menunjukkan gejala klasik FPV. PCR positif.",
  "outcome": "recovering",
  "confidence": 95
}
```

#### `POST /consultations/{consultation_id}/feedback`

Penilaian dokter atas saran AI (human-in-the-loop).

**Request Body:**

```json
{
  "suggestion_ref": "uuid-xxx",
  "verdict": "correct",
  "corrected_disease_slug": "cat-fpv-panleukopenia",
  "comment": "Saran sangat membantu, diagnosa sesuai",
  "reviewer_id": 1
}
```

| Field | Type | Required | Values |
|-------|------|----------|--------|
| `verdict` | string | ✅ | `correct`, `partially_correct`, `incorrect`, `not_applicable` |

---

### 4.4 AI Agent

#### `POST /api/agent/conversations/{consultation_id}/chat`

Chat interaktif dengan agent AI (konteks klinis ringkas, hemat token).

**Request Body:**

```json
{
  "message": "Apa tindakan pertama untuk kucing dengan gejala ini?",
  "provider_id": "anthropic"
}
```

**Response `200`:**

```json
{
  "consultation_id": "ext-20250619-001",
  "reply": "Tindakan pertama: stabilisasi pasien...",
  "follow_up_questions": ["Sudah cek suhu?"],
  "provider_used": "anthropic"
}
```

#### `POST /api/agent/conversations/{consultation_id}/doctor-input`

Satu endpoint: input klinis dokter + feedback opsional (VetInputForm).

#### `POST /api/agent/conversations/{consultation_id}/feedback`

Feedback saran AI via agent endpoint.

#### `POST /api/agent/conversations/{consultation_id}/vet-record`

Rekam medis lengkap dari dokter (VetInputForm).

#### `GET /api/agent/conversations`

Daftar sesi percakapan agent.

#### `GET /api/agent/conversations/{consultation_id}`

Detail satu percakapan agent.

#### `GET /api/agent/suggestions`

Daftar saran AI.

**Parameters:**
| Name | In | Type | Required |
|------|----|------|----------|
| `consultation_id` | query | string | ❌ |
| `reviewed` | query | boolean | ❌ |
| `limit` | query | integer | ❌ |

#### `POST /api/agent/suggestions/{suggestion_id}/review`

Review saran AI.

#### `GET /api/agent/providers`

Daftar provider LLM yang terdaftar.

#### `POST /api/agent/providers`

Tambah/update provider LLM.

#### `POST /api/agent/providers/{provider_id}/activate`

Aktifkan satu provider.

#### `GET /api/agent/providers/status`

Status konfigurasi provider eksternal.

#### `POST /api/agent/providers/test`

Uji koneksi live ke provider AI.

**Parameters:**
| Name | In | Type | Required |
|------|----|------|----------|
| `provider_id` | query | string | ❌ |

#### `POST /api/agent/providers/{provider_id}/test`

Uji koneksi live ke satu provider spesifik.

#### `GET /api/agent/usage`

Penggunaan token & biaya agent.

---

### 4.5 ML Prediction

#### `POST /ml/predict`

Prediksi symptom → disease langsung dari model ML (tanpa LLM).

**Request Body:**

```json
{
  "category_slug": "dog",
  "symptoms": ["Muntah hebat", "Diare berdarah", "Lemas/lesu"],
  "top_k": 5
}
```

**Response `200`:**

```json
{
  "predictions": [
    {
      "disease_slug": "dog-parvovirus",
      "name_id": "Parvovirus (Parvo)",
      "confidence": 0.94,
      "is_emergency": true
    },
    {
      "disease_slug": "dog-canine-distemper",
      "name_id": "Canine Distemper",
      "confidence": 0.72,
      "is_emergency": true
    }
  ],
  "model": "RandomForest",
  "category": "dog",
  "n_classes": 105
}
```

---

### 4.6 Single-Shot Consult

#### `POST /api/consult`

Saran klinis terstruktur single-shot (RAG: ML + KB + LLM opsional). Tanpa sesi, tanpa learning loop.

**Request Body:**

```json
{
  "category_slug": "dog",
  "breed_slug": "dog-golden-retriever",
  "age_years": 2,
  "weight_kg": 30,
  "sex": "male",
  "complaint_text": "Anjing saya lemas, muntah, dan diare berdarah",
  "symptoms": ["Muntah hebat", "Diare berdarah", "Lemas/lesu"],
  "top_k": 5
}
```

---

### 4.7 Learning Loop

#### `GET /learning/export`

Ekspor baris siap-latih (gold labels) dari input dokter untuk retraining ML.

#### `GET /learning/stats`

Statistik event pembelajaran + info backend.

#### `POST /learning/retrain`

Eksekusi retraining: latih ulang model dari input dokter (gold rows).

**Request Body:**

```json
{
  "category": "cat",
  "samples_per_disease": 100
}
```

#### `POST /learning/sync-db`

Migrasi event JSONL lokal ke PostgreSQL (`learning_events`). Idempotent.

#### `POST /learning/sync-models-db`

Sinkronkan artefak ML lokal ke tabel PostgreSQL `ml_models`.

---

### 4.8 Integrasi Vet App

#### `GET /api/integration/id-schema`

Kontrak ID entitas untuk tim developer Ekosistem Satwa.

**Response `200`:** Dokumentasi lengkap field ID yang harus dikirim di `ConsultationContext`.

#### `GET /api/integration/manifest`

Kontrak integrasi lengkap — dipakai app vet saat onboarding. Berisi recommended flow, endpoints, entity IDs, dan konfigurasi.

#### `GET /api/integration/health`

Health check autentikasi vet app.

#### `GET /api/integration/capabilities`

Kemampuan AI yang tersedia untuk app vet.

#### `GET /api/integration/entities/{consultation_id}`

Ambil bundle ID entitas untuk satu sesi konsultasi.

**Parameters:**
| Name | In | Type | Required |
|------|----|------|----------|
| `consultation_id` | path | string | ✅ |

#### `GET /api/integration/consultations/by-external/{external_id}`

Lookup sesi AI dari ID konsultasi app Ekosistem Satwa utama.

**Parameters:**
| Name | In | Type | Required |
|------|----|------|----------|
| `external_id` | path | string | ✅ |

#### `GET /api/integration/consultations`

Daftar sesi AI terfilter by ID entitas Ekosistem Satwa.

**Parameters:**
| Name | In | Type | Required |
|------|----|------|----------|
| `vet_id` | query | int | ❌ |
| `owner_id` | query | int | ❌ |
| `customer_id` | query | int | ❌ |
| `pet_id` | query | int | ❌ |
| `org_id` | query | int | ❌ |
| `limit` | query | integer | ❌ |

---

### 4.9 Smart Data Platform

#### `GET /api/platform/manifest`

Kontrak platform lengkap untuk AI agent (data tracks, pipeline, guidelines).

#### `GET /api/platform/doctor`

Diagnostik kesehatan sistem — JSON terstruktur untuk agent. Berisi `status`, `checks[]`, `recommended_next`.

#### `GET /api/platform/registry`

Registry lineage data + model ML.

**Parameters:**
| Name | In | Type | Required |
|------|----|------|----------|
| `refresh` | query | boolean | ❌ |

#### `GET /api/platform/pipeline`

Daftar langkah & preset pipeline.

#### `POST /api/platform/pipeline/run`

Jalankan langkah/preset pipeline (admin). Output JSON untuk agent.

**Request Body:**

```json
{
  "preset": "ml_ready",
  "continue_on_error": false
}
```

**Preset tersedia:**
| Preset | Langkah | Penggunaan |
|--------|---------|------------|
| `agent_bootstrap` | validate_kb → train_ml → refresh_registry | Setup cepat agent |
| `ml_ready` | validate_kb → train_ml → refresh_registry | Sebelum uji AI/ML |
| `full_synthetic` | generate → validate → ml_views → registry | Dataset bulk |
| `learning_loop` | retrain_ml → export_learning → registry | Setelah input dokter |
| `ci_sample` | generate (sample) → validate → ml_views | CI |

#### `GET /api/platform/pipeline/{step_id}`

Detail satu langkah pipeline.

---

### 4.10 Data Analysis & Simulation

#### `GET /api/analysis/status`

Status modul analisis dan NLP.

#### `POST /api/analysis/text`

Analisis teks lengkap: NLP tokenization + keyword extraction + symptom extraction + LLM.

**Request Body:**

```json
{
  "text": "Kucing saya muntah dan diare",
  "category_slug": "cat"
}
```

#### `POST /api/analysis/tokenize`

Tokenisasi dan POS tagging teks.

#### `POST /api/analysis/keywords`

Ekstrak keywords dari teks.

#### `GET /api/analysis/tables`

Daftar semua tabel dataset sintetik.

#### `GET /api/analysis/tables/{table_name}`

Detail satu tabel dataset.

#### `GET /api/analysis/diseases/distribution`

Distribusi penyakit dari dataset.

#### `GET /api/analysis/symptoms/analysis`

Analisis gejala dari dataset.

#### `POST /api/analysis/cross-analysis`

Analisis silang dua tabel.

**Request Body:**

```json
{
  "table_a": "consultations",
  "table_b": "diagnoses",
  "join_column": "consultation_id"
}
```

#### `GET /api/analysis/uploads`

Ringkasan file yang diupload.

#### `POST /api/analysis/simulate`

Simulasi kasus klinis dari knowledge base.

**Request Body:**

```json
{
  "category_slug": "dog",
  "disease_slug": "dog-parvovirus",
  "n_cases": 10
}
```

#### `POST /api/analysis/simulate/compare`

Bandingkan performa ML vs KB-grounding.

#### `POST /api/analysis/llm/analyze`

Analisis dengan LLM — complaint / differential / treatment.

**Request Body:**

```json
{
  "text": "Kucing muntah 3 hari, tidak mau makan, lesu",
  "category_slug": "cat",
  "analysis_type": "differential"
}
```

| `analysis_type` | Deskripsi |
|----------------|-----------|
| `complaint` | Analisis keluhan |
| `differential` | Diagnosa banding |
| `treatment` | Rekomendasi tindakan |

#### `GET /api/analysis/llm/status`

Status ketersediaan LLM.

#### `POST /api/analysis/pipeline/full`

Pipeline analisis sistem lengkap.

---

### 4.11 Upload & Auto-Ingest

#### `POST /api/ingest/upload`

Upload file (CSV/Excel/PDF/JSON/dll) — auto-detect, analyze, classify. Tanpa batas ukuran file.

**Request (multipart/form-data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | ✅ | File to upload |
| `description` | string | ❌ | Deskripsi file |
| `category` | string | ❌ | Kategori data |
| `auto_analyze` | boolean | ❌ | Auto-analyze setelah upload |

#### `GET /api/ingest/formats`

Daftar format file yang didukung.

#### `GET /api/ingest/uploads`

Daftar file yang sudah diupload.

#### `POST /api/ingest/reingest/{filename}`

Re-ingest ulang file yang sudah diupload.

#### `GET /api/ingest/analyze/{filename}`

Analisis file yang sudah diupload.

---

### 4.12 Admin Dashboard

Semua endpoint admin memerlukan `X-EkosistemSatwa-Key` atau `Authorization` level admin.

#### `GET /admin/overview`

Ringkasan sistem untuk dashboard admin.

#### `GET /admin/ai/usage`

Detail penggunaan token & biaya LLM.

#### `GET /admin/learning/events`

Event pembelajaran terbaru (audit trail).

**Parameters:**
| Name | In | Type | Required |
|------|----|------|----------|
| `kind` | query | string | ❌ |
| `limit` | query | integer | ❌ |

#### `GET /admin/integration/status`

Status integrasi untuk app vet & layanan eksternal.

#### `POST /admin/ai/budget/reset`

Reset counter budget harian (admin only, in-memory).

---

### 4.13 Dataset & Exports

#### `POST /api/dataset/upload`

Upload dataset (CSV/PDF/Excel/TXT/JSON) untuk analisis & training.

**Request (multipart/form-data):**
| Field | Type | Required |
|-------|------|----------|
| `file` | file | ✅ |
| `description` | string | ❌ |
| `category` | string | ❌ |

#### `GET /api/dataset/list`

Daftar semua dataset yang sudah diupload.

#### `GET /exports/excel`

Daftar file Excel yang tersedia.

#### `GET /exports/excel/{filename}`

Unduh workbook Excel.

**Parameters:**
| Name | In | Type | Required |
|------|----|------|----------|
| `filename` | path | string | ✅ |

---

## 5. Schema Reference

### ConsultationContext

Dikirim di setiap `POST /consultations` untuk mengidentifikasi entitas.

| Field | Type | Required | DB Source | Deskripsi |
|-------|------|----------|-----------|-----------|
| `vet_id` | int | ✅ | `users.id` | Dokter yang menangani |
| `owner_id` / `customer_id` | int | ✅ | `pet_owners.id` | Pemilik hewan |
| `pet_id` | int | ✅ | `pets.id` | Pasien hewan |
| `org_id` | int | ❌ | `organizations.id` | Klinik/cabang |
| `case_id` | int | ❌ | `clinical_cases.id` | Kasus klinis |
| `external_consultation_id` | string | ❌ | - | ID dari app utama untuk lookup |
| `category_slug` | string | ❌ | - | Spesies: dog, cat, rabbit, ... |
| `breed_slug` | string | ❌ | - | Ras |
| `age_years` | float | ❌ | - | Usia |
| `weight_kg` | float | ❌ | - | Berat badan |
| `sex` | string | ❌ | - | `male`, `female`, `unknown` |
| `is_neutered` | boolean | ❌ | - | Status steril |
| `temperature_c` | float | ❌ | - | Suhu tubuh |
| `heart_rate` | int | ❌ | - | Denyut jantung |
| `resp_rate` | int | ❌ | - | Frekuensi napas |

### AISuggestion

Struktur response saran AI.

| Field | Type | Deskripsi |
|-------|------|-----------|
| `suggestion_type` | string | `symptom_to_disease` |
| `summary` | string | Ringkasan klinis |
| `follow_up_questions` | string[] | Pertanyaan lanjutan untuk dokter |
| `suggested_diseases` | SuggestedDisease[] | Diagnosa banding |
| `suggested_diagnostics` | SuggestedDiagnostic[] | Pemeriksaan yang disarankan |
| `suggested_treatments` | SuggestedTreatment[] | Tindakan terapi |
| `suggested_products` | SuggestedProduct[] | Produk/rekomendasi |
| `red_flags` | string[] | Tanda bahaya |
| `safety_warnings` | string[] | Peringatan keamanan obat |
| `references` | string[] | Referensi klinis |
| `is_emergency` | boolean | Indikasi darurat |
| `generated_by` | string | `rule_based` atau `llm_augmented` |
| `disclaimer` | string | Disclaimer medis |

### SuggestedDisease

| Field | Type | Deskripsi |
|-------|------|-----------|
| `disease_slug` | string | Slug penyakit |
| `name_id` | string | Nama dalam Bahasa Indonesia |
| `confidence` | float | Keyakinan 0..1 |
| `rationale` | string | Alasan klinis |
| `is_emergency` | boolean | Darurat? |
| `source` | string | `ml`, `knowledge_base`, `llm`, `ml+knowledge_base` |

### SuggestedDiagnostic

| Field | Type | Deskripsi |
|-------|------|-----------|
| `name` | string | Nama pemeriksaan |
| `type` | string | `blood_test`, `imaging_ultrasound`, `pcr_molecular`, `serology`, `urinalysis`, `physical_exam`, dll |
| `step_order` | int | Urutan prioritas |
| `is_gold_standard` | boolean | Gold standard? |
| `expected_finding` | string | Temuan yang diharapkan |
| `for_disease` | string | Disease slug terkait |

### DoctorInput

| Field | Type | Required | Deskripsi |
|-------|------|----------|-----------|
| `confirmed_disease_slug` | string | ❌ | Diagnosa final dokter |
| `differential_disease_slugs` | string[] | ❌ | Diagnosa banding |
| `confirmed_symptoms` | string[] | ❌ | Gejala yang dikonfirmasi |
| `diagnostics_ordered` | string[] | ❌ | Pemeriksaan dilakukan |
| `treatments_given` | string[] | ❌ | Tindakan diberikan |
| `products_prescribed` | string[] | ❌ | Produk diresepkan |
| `clinical_notes` | string | ❌ | Catatan klinis |
| `outcome` | string | ❌ | Hasil: `recovering`, `recovered`, `referred`, `deceased`, `euthanized`, `lost_to_followup` |
| `confidence` | int | ❌ | Keyakinan dokter 0..100 |

### SuggestionFeedback

| Field | Type | Required | Deskripsi |
|-------|------|----------|-----------|
| `verdict` | string | ✅ | `correct`, `partially_correct`, `incorrect`, `not_applicable` |
| `corrected_disease_slug` | string | ❌ | Koreksi diagnosa |
| `comment` | string | ❌ | Komentar dokter |
| `reviewer_id` | int | ❌ | ID reviewer |

---

## 6. Postman Collection

Kami menyediakan Postman Collection lengkap yang bisa di-import langsung ke Postman.

**File:** [`EkosistemSatwa_API.postman_collection.json`](./EkosistemSatwa_API.postman_collection.json)

### Cara Import

1. Buka Postman
2. Klik **Import** → **Upload Files**
3. Pilih file `EkosistemSatwa_API.postman_collection.json`
4. Set **Base URL** variable: `http://43.129.56.221:8080`

### Isi Collection

Collection mencakup semua endpoint dengan:
- Contoh request body
- Pre-filled parameters
- Variables untuk base URL dan consultation ID
- Organized by folder sesuai kategori endpoint

---

## 7. Error Handling

Semua error mengembalikan format JSON:

```json
{
  "detail": [
    {
      "loc": ["body", "context", "vet_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### HTTP Status Codes

| Code | Deskripsi |
|------|-----------|
| `200` | Success |
| `201` | Created |
| `400` | Bad Request — validasi gagal |
| `401` | Unauthorized — API key salah/tidak ada |
| `403` | Forbidden — tidak punya akses |
| `404` | Not Found — resource tidak ditemukan |
| `422` | Unprocessable Entity — validasi request body gagal |
| `500` | Internal Server Error |

### Common Errors & Solutions

| Error | Penyebab | Solusi |
|-------|----------|--------|
| `422 field required` | Field wajib tidak dikirim | Cek schema request body |
| `ML predict 404` | Model belum dilatih | Jalankan `POST /api/platform/pipeline/run` dengan preset `ml_ready` |
| `Saran AI kosong` | Gejala tidak terdeteksi | Pastikan teks keluhan jelas |
| `gold_rows = 0` | Dokter belum input | `POST /consultations/{id}/doctor-input` |

---

## 8. Rate Limits & Best Practices

### Best Practices

1. **Gunakan `POST /api/consult` untuk single-shot** — lebih cepat, tanpa overhead sesi
2. **Gunakan `POST /ml/predict` untuk ML-only** — tanpa LLM, lebih hemat
3. **Mode Smart Augmentation** — Kirim `pretranscribed_text` / gejala terstruktur untuk minim panggilan vision/STT
4. **Cache master data** — `GET /categories` dan `GET /categories/{slug}/breeds` jarang berubah
5. **Learning loop** — Selalu kirim `doctor-input` dan `feedback` untuk meningkatkan kualitas model

### Token Efficiency

| Mode | Deskripsi | Kapan pakai |
|------|-----------|-------------|
| `smart` (default) | Lewati LLM bila ML+KB yakin | Hemat token, recommended |
| `always` | Selalu pakai LLM | Butuh reasoning mendalam |
| `never` | Rule-based only | Development/testing |

### Batasan

- ML inference: ~100-500ms per prediksi (CPU-bound RandomForest)
- Upload file: tanpa batas ukuran (production: reverse proxy limit)
- Learning store: JSONL default, PostgreSQL opsional

---

> **Butuh bantuan?** Lihat [README.md](../README.md) untuk setup lokal, [AGENTS.md](../AGENTS.md) untuk panduan AI agent, atau buka [`/docs`](http://43.129.56.221:8080/docs) untuk Swagger UI interaktif.
