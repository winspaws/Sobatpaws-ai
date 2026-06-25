# Integrasi Ekosistem Satwa — App Vet & Admin Dashboard

Panduan integrasi platform ML/AI Ekosistem Satwa dengan **aplikasi dokter hewan (vet app)** dan **dashboard admin** Ekosistem Satwa.

---

## 1. Arsitektur Integrasi

```
┌─────────────────┐     X-EkosistemSatwa-Key      ┌──────────────────────────────┐
│  App Vet        │ ───────────────────────► │  Ekosistem Satwa API (FastAPI)     │
│  (mobile/web)   │   REST + multipart       │  ML + KB + AI (smart mode)   │
└─────────────────┘                          └──────────────┬───────────────┘
                                                            │
┌─────────────────┐     Admin API Key                     │
│  Admin Dashboard│ ◄─────────────────────────────────────┤
│  /admin.html    │   /admin/* monitoring                 │
└─────────────────┘                                       ▼
                                              PostgreSQL (opsional) + JSONL learning
```

---

## 2. Autentikasi API

Set di `.env`:

```bash
EKOSISTEM_SATWA_VET_API_KEY=sk-vet-your-secret-key
EKOSISTEM_SATWA_ADMIN_API_KEY=sk-admin-your-secret-key
```

Header pada setiap request vet app:

```
X-EkosistemSatwa-Key: sk-vet-your-secret-key
```

Atau: `Authorization: Bearer sk-vet-your-secret-key`

| Role | Akses |
|------|--------|
| **Public** | `GET /health`, `/categories`, `/api/status`, `/api/integration/manifest` |
| **Vet** | `/consultations/*`, `/api/consult`, `/ml/predict`, doctor-input, feedback |
| **Admin** | `/admin/*`, `/learning/retrain`, `/learning/sync-db`, `/learning/sync-models-db`, `/api/platform/*` |

> Bila kunci **tidak diset**, auth dinonaktifkan (mode dev lokal).

---

## 3. Alur Integrasi App Vet (Recommended)

### a) Onboarding — baca manifest

```http
GET /api/integration/manifest
```

Mengembalikan kontrak API, alur recommended, tips efisiensi token.

### b) Muat master data (cache di app)

```http
GET /categories
GET /categories/dog/breeds
GET /api/symptoms?category=dog
```

### c) Mulai konsultasi (sesi)

Kirim **semua ID entitas** dari app Ekosistem Satwa agar ML/AI, learning loop, dan PostgreSQL selaras:

| Field | DB | Wajib |
|-------|-----|-------|
| `org_id` | organizations.id | Opsional |
| `vet_id` | users.id (dokter) | **Ya** |
| `owner_id` / `customer_id` | pet_owners.id | **Ya** |
| `pet_id` | pets.id | **Ya** |
| `case_id` | clinical_cases.id | Opsional |
| `external_consultation_id` | ID app utama | Disarankan |

Kontrak lengkap: `GET /api/integration/id-schema`

```http
POST /consultations
Content-Type: application/json
X-EkosistemSatwa-Key: sk-vet-...

{
  "consultation_id": "sp-consult-20250612-0042",
  "context": {
    "org_id": 1,
    "vet_id": 42,
    "owner_id": 1001,
    "customer_id": 1001,
    "pet_id": 500,
    "case_id": 8801,
    "external_consultation_id": "sp-consult-20250612-0042",
    "external_refs": {
      "appointment_id": "apt-991",
      "invoice_id": "inv-5521"
    },
    "category_slug": "dog",
    "breed_slug": "dog-golden-retriever",
    "age_years": 3,
    "weight_kg": 28
  },
  "intake": {
    "channel": "chat",
    "text": "Anjing muntah hebat dan diare berdarah sejak kemarin",
    "is_first_contact": true
  }
}
```

Response menyertakan `entities` — bundle ID untuk disimpan/di-sync ke app utama:

```json
{
  "consultation_id": "sp-consult-20250612-0042",
  "entities": {
    "consultation_id": "sp-consult-20250612-0042",
    "external_consultation_id": "sp-consult-20250612-0042",
    "org_id": 1,
    "vet_id": 42,
    "owner_id": 1001,
    "pet_id": 500,
    "case_id": 8801
  },
  "suggestion": { "...": "..." }
}
```

Lookup sesi dari ID app utama:

```http
GET /api/integration/consultations/by-external/sp-consult-20250612-0042
GET /api/integration/entities/sp-consult-20250612-0042
GET /api/integration/consultations?vet_id=42&pet_id=500
```



### g) Sinkronisasi Entity Mapping (Sync/Lookup/Registry)

Endpoint tambahan untuk skenario di mana app utama perlu:
1. **Pre-register** entity mapping SEBELUM konsultasi dimulai
2. **Bulk lookup** banyak ID sekaligus (untuk sync batch)
3. **Dump seluruh registry** untuk inisialisasi sync ke DB utama

#### POST /api/integration/sync — Register/Upsert Entity Mapping

Gunakan endpoint ini untuk mendaftarkan mapping entity ID dari app utama
**sebelum** konsultasi dimulai. Berguna untuk:
- App yang ingin memisahkan langkah "pendaftaran entity" dan "mulai konsultasi"
- Sync batch dari DB utama ke AI session

```http
POST /api/integration/sync
Content-Type: application/json
X-EkosistemSatwa-Key: sk-vet-...

{
  "external_consultation_id": "app-2025-0626-0001",
  "vet_id": 42,
  "owner_id": 1001,
  "customer_id": 1001,
  "pet_id": 500,
  "case_id": 8801,
  "org_id": 1,
  "external_refs": {
    "appointment_id": "APT-2025-0626-0001",
    "invoice_id": "INV-5521"
  }
}
```

Response:
```json
{
  "status": "synced",
  "consultation_id": "app-2025-0626-0001",
  "external_consultation_id": "app-2025-0626-0001",
  "entities": {
    "consultation_id": "app-2025-0626-0001",
    "external_consultation_id": "app-2025-0626-0001",
    "org_id": 1,
    "vet_id": 42,
    "owner_id": 1001,
    "customer_id": 1001,
    "pet_id": 500,
    "case_id": 8801,
    "external_refs": {
      "appointment_id": "APT-2025-0626-0001",
      "invoice_id": "INV-5521"
    }
  },
  "registered_at": "2025-06-26T04:30:00+00:00",
  "session_active": false
}
```

**Catatan:**
- Field `external_consultation_id` disarankan tapi opsional
- Jika tidak ada `consultation_id` maupun `external_consultation_id`, server akan generate UUID baru
- Jika `external_consultation_id` sudah pernah terdaftar, mapping akan di-update (upsert)

#### POST /api/integration/lookup — Bulk Lookup

Lookup banyak ID sekaligus untuk sync batch:

```http
POST /api/integration/lookup
Content-Type: application/json
X-EkosistemSatwa-Key: sk-vet-...

{
  "external_consultation_ids": [
    "app-2025-0626-0001",
    "app-2025-0626-0002",
    "id-tidak-ada"
  ],
  "consultation_ids": ["uuid-sesi-ai-123"]
}
```

Response:
```json
{
  "total": 4,
  "found": 2,
  "not_found_count": 2,
  "not_found": ["id-tidak-ada", "uuid-sesi-ai-123"],
  "results": {
    "app-2025-0626-0001": {
      "consultation_id": "app-2025-0626-0001",
      "external_consultation_id": "app-2025-0626-0001",
      "entities": { "vet_id": 42, "owner_id": 1001, ... }
    },
    "app-2025-0626-0002": {
      "consultation_id": "...",
      "entities": { ... },
      "session_active": true
    },
    "id-tidak-ada": null,
    "uuid-sesi-ai-123": null
  }
}
```

#### GET /api/integration/entity-registry — Dump Semua Mapping

Ambil seluruh entity registry untuk inisialisasi sync atau backup:

```http
GET /api/integration/entity-registry
GET /api/integration/entity-registry?vet_id=42&limit=100
GET /api/integration/entity-registry?owner_id=1001&offset=50&limit=50
GET /api/integration/entity-registry?pet_id=500
GET /api/integration/entity-registry?org_id=1
```

**Query Parameters:**
| Param | Type | Default | Deskripsi |
|-------|------|---------|-----------|
| `vet_id` | int | null | Filter by dokter |
| `owner_id` | int | null | Filter by pemilik hewan |
| `customer_id` | int | null | Alias untuk owner_id |
| `pet_id` | int | null | Filter by hewan |
| `org_id` | int | null | Filter by organisasi/klinik |
| `limit` | int | 50 | Max records per page (max 500) |
| `offset` | int | 0 | Pagination offset |

Response:
```json
{
  "count": 42,
  "offset": 0,
  "limit": 50,
  "registry": [
    {
      "consultation_id": "app-2025-0626-0001",
      "external_consultation_id": "app-2025-0626-0001",
      "vet_id": 42,
      "owner_id": 1001,
      "pet_id": 500,
      "case_id": 8801,
      "org_id": 1,
      "external_refs": { ... },
      "registered_at": "2025-06-26T04:30:00+00:00"
    },
    ...
  ],
  "schema": {
    "description": "ID entitas Ekosistem Satwa...",
    "fields": { ... }
  }
}
```

#### Ringkasan Endpoint Sync

| Endpoint | Method | Use Case |
|----------|--------|----------|
| `/api/integration/sync` | POST | Daftarkan/update entity mapping (upsert) |
| `/api/integration/lookup` | POST | Bulk lookup entities by ID |
| `/api/integration/entity-registry` | GET | Dump/filter semua mapping dengan pagination |
| `/api/integration/entities/{id}` | GET | Get single entity by consultation_id |
| `/api/integration/consultations/by-external/{id}` | GET | Get single entity by external_consultation_id |


### d) Giliran lanjutan / media

```http
POST /consultations/{id}/turns
POST /consultations/{id}/media   (multipart: file, modality, channel)
```

### e) Simpan keputusan dokter (gold label)

```http
POST /consultations/{id}/doctor-input
{
  "confirmed_disease_slug": "dog-parvovirus",
  "clinical_notes": "Parvo confirmed via rapid test",
  "confirmed_symptoms": ["Muntah hebat", "Diare berdarah"]
}
```

### f) Feedback saran AI

```http
POST /consultations/{id}/feedback
{ "verdict": "correct" }
```

---

## 4. Shortcut tanpa sesi

```http
POST /api/consult
POST /ml/predict
```

Cocok untuk triage cepat tanpa learning loop.

---

## 5. Admin Dashboard

Buka: **http://localhost:8000/admin.html**

| Panel | Endpoint backend |
|-------|------------------|
| KPI sistem | `GET /admin/overview` |
| Token & biaya AI | `GET /admin/ai/usage` |
| Status integrasi | `GET /admin/integration/status` |
| Audit learning | `GET /admin/learning/events` |

Isi **Admin API Key** di header dashboard bila auth aktif.

### Smart Data Platform (orchestrator)

```http
GET  /api/platform/manifest
GET  /api/platform/doctor
GET  /api/platform/registry?refresh=true
POST /api/platform/pipeline/run   {"preset": "learning_loop"}
POST /learning/sync-models-db     # sync ml_models → PostgreSQL
```

Training ML (`python -m ekosistem_satwa.ml.train`):

| `--source` | Data |
|------------|------|
| `kb` | Synthetic dari JSON curated |
| `views` | Kasus synthetic CSV / ML views |
| `hybrid` | KB + kasus synthetic (disarankan) |

Setelah edit `data/clinical/*.json`, jalankan `python scripts/sync_catalogs_from_kb.py` agar generator synthetic selaras.

---

## 6. AI Agent — Maksimal & Hemat Token

### Prinsip desain

1. **Diagnosa utama = ML + Knowledge Base** (tanpa LLM, gratis, offline-capable)
2. **LLM hanya augmentasi** — ringkasan natural + pertanyaan lanjutan
3. **Mode `smart`** (default) — lewati LLM bila keyakinan sudah tinggi

### Environment efisiensi

```bash
# Mode: smart | always | never
EKOSISTEM_SATWA_AI_AUGMENTATION_MODE=smart

# Lewati LLM augment bila confidence top disease >= 0.82
EKOSISTEM_SATWA_AI_SKIP_LLM_CONFIDENCE=0.82

# Max output token per panggilan LLM (default 800, bukan 1500)
EKOSISTEM_SATWA_AI_MAX_TOKENS=800

# Cache respons identik (detik, default 3600)
EKOSISTEM_SATWA_AI_CACHE_TTL_SEC=3600

# Budget harian token (0 = unlimited)
EKOSISTEM_SATWA_AI_DAILY_TOKEN_BUDGET=50000
```

### Tips integrasi vet app (hemat kredit)

| Praktik | Penghematan |
|---------|-------------|
| Ekstrak gejala di device, kirim `symptoms[]` terstruktur | Hindari vision/STT |
| STT di device → `pretranscribed_text` | Hindari Whisper API |
| Gunakan `/ml/predict` untuk triage cepat | Zero LLM |
| Mode `smart` + confidence tinggi | Skip augmentation otomatis |
| Cache TTL aktif | Request identik = 0 token |

### Observability

Setiap panggilan LLM dicatat ke `artifacts/learning/ai_requests.jsonl`:
- `prompt_tokens`, `completion_tokens`, `cost_usd`, `latency_ms`
- `cached`, `skipped`, `skip_reason`

Monitor via `GET /admin/ai/usage`.

---

## 7. Koneksi Anthropic / Claude (AI Agent Eksternal)

### Konfigurasi `.env`

```bash
EKOSISTEM_SATWA_AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-3-5-sonnet-latest
# atau claude-sonnet-4-20250514 / model terbaru di console Anthropic
```

### Verifikasi koneksi

```http
GET  /api/agent/providers/status          # status konfigurasi (tanpa ping)
POST /api/agent/providers/anthropic/test # uji live ke Claude API (admin key)
POST /api/agent/providers/test            # uji semua provider
```

Response sukses:
```json
{
  "id": "anthropic",
  "name": "Anthropic Claude",
  "model": "claude-3-5-sonnet-latest",
  "connected": true,
  "latency_ms": 842,
  "response_preview": "{\"status\":\"ok\"...}"
}
```

### Aktivasi sebagai provider utama

```http
POST /api/agent/providers/anthropic/activate
X-EkosistemSatwa-Key: <admin-key>
```

### Fallback chain

Bila provider utama gagal, sistem otomatis fallback:
```
primary → provider lain yang configured (openai, anthropic, local)
```

Atur urutan via env:
```bash
EKOSISTEM_SATWA_AI_FALLBACK_CHAIN=anthropic,openai,local
```

### Chat agent via Claude (app vet)

```http
POST /api/agent/conversations/{consultation_id}/chat
{
  "message": "Apakah perlu rujungan darurat?",
  "provider_id": "anthropic"
}
```

Field `provider_id` opsional — default pakai provider primary.

---

## 8. OpenAPI

Dokumentasi interaktif: **http://localhost:8000/docs**

Tag endpoint:
- **Integrasi Vet App** — `/api/integration/*`
- **Admin Dashboard** — `/admin/*`

---

## 8. Checklist Production

- [ ] Set `EKOSISTEM_SATWA_VET_API_KEY` dan `EKOSISTEM_SATWA_ADMIN_API_KEY`
- [ ] Set `EKOSISTEM_SATWA_LEARNING_BACKEND=both` + PostgreSQL
- [ ] Set `EKOSISTEM_SATWA_AI_AUGMENTATION_MODE=smart`
- [ ] Set `EKOSISTEM_SATWA_AI_DAILY_TOKEN_BUDGET` sesuai paket kredit
- [ ] Vet app kirim `org_id`, `user_id`, `pet_id` di setiap konsultasi
- [ ] Monitor `/admin/overview` secara berkala
