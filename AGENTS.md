# AGENTS.md — Panduan AI Agent untuk Sobatpaws

Dokumen ini adalah **titik masuk utama** bagi AI coding agent (Cursor, CI bot, integrasi otomatis) agar bekerja maksimal di repo ini.

## 1. Apa itu Sobatpaws?

Platform **Smart Data + ML + AI** untuk dokter hewan:
- Knowledge base klinis (JSON) → grounding AI + training ML
- Konsultasi multimodal (teks/mic/kamera) → saran klinis terstruktur
- Learning loop (input dokter → gold labels → retrain)
- Dataset synthetic skala besar (CSV) untuk validasi skema & analytics

## 2. Tiga jalur data (WAJIB dipahami)

| Track | Lokasi | Peran | Agent boleh edit? |
|-------|--------|-------|-------------------|
| **curated_json** | `data/categories.json`, `data/breeds/`, `data/clinical/` | Sumber kebenaran runtime (AI, ML train, seed SQL) | ✅ Ya |
| **synthetic_csv** | `data/generated/`, `data/ml_views/` | Bulk data, validasi DBML, Excel, ML views | ❌ Regenerate saja |
| **learning_loop** | `artifacts/learning/`, `artifacts/models/` | Konsultasi + retrain | ❌ Jangan edit manual |

**Aturan emas:** Perubahan klinis → edit JSON curated → `seed` + `train_ml` + `refresh_registry`.

**Integrasi app utama:** Selalu kirim `vet_id`, `owner_id`/`customer_id`, `pet_id`, dan `external_consultation_id` di `ConsultationContext`. Response API memuat field `entities` untuk sync balik ke DB Sobatpaws.

## 3. Titik masuk machine-readable (prioritas agent)

```http
GET  /api/integration/id-schema   # Kontrak ID entitas (vet, pelanggan, pet, ...)
GET  /api/platform/manifest       # Kontrak platform lengkap
GET  /api/platform/doctor       # Diagnostik kesehatan sistem (JSON)
GET  /api/platform/registry     # Lineage model + data
GET  /api/platform/pipeline     # Daftar langkah & preset
POST /api/platform/pipeline/run # Jalankan pipeline (admin key)
GET  /api/integration/manifest  # Kontrak app vet
GET  /api/agent/providers       # Provider LLM terdaftar
```

CLI setara:
```bash
export PYTHONPATH=src
python -m sobatpaws.platform.doctor
python -m sobatpaws.platform.pipeline --list
python -m sobatpaws.platform.pipeline --preset ml_ready
python -m sobatpaws.platform.registry --refresh
```

## 4. Pipeline presets

| Preset | Langkah | Kapan dipakai |
|--------|---------|---------------|
| `agent_bootstrap` | validate_kb → train_ml → refresh_registry | Setup cepat agent |
| `ml_ready` | sama | Sebelum uji AI/ML |
| `full_synthetic` | generate → validate → ml_views → registry | Dataset bulk |
| `learning_loop` | retrain_ml → export_learning → registry | Setelah input dokter |
| `ci_sample` | generate (sample) → validate → ml_views | CI |

## 5. Struktur kode inti

```
src/sobatpaws/
├── data_loader.py          # KnowledgeBase dari JSON
├── platform/               # Smart Data Platform (ORCHESTRATOR)
│   ├── manifest.py         # Pipeline steps + agent guidelines
│   ├── doctor.py           # Health check JSON
│   ├── pipeline.py         # Run steps/presets
│   ├── pipeline.py         # Run steps/presets
│   ├── registry.py         # Model + data lineage
│   └── model_registry_pg.py # Sync ml_models → PostgreSQL
├── ml/
│   ├── train.py            # --source kb|views|hybrid
│   └── views_loader.py     # Bridge synthetic CSV → training
├── ai/                     # RAG + LLM + consultation + agent_manager
└── api/                    # FastAPI (main, platform, agent, admin)
```

## 6. Alur kerja agent yang direkomendasikan

### A. Bootstrap proyek
1. `python -m sobatpaws.platform.doctor` → baca `recommended_next`
2. `python -m sobatpaws.platform.pipeline --preset agent_bootstrap`
3. `./run.sh` → verifikasi `GET /health`

### B. Tambah penyakit/gejala
1. Edit `data/clinical/diseases_{species}.json`
2. `python scripts/sync_catalogs_from_kb.py` (sinkron vocabulary synthetic)
3. `python -m sobatpaws.seed_generator`
4. `python -m sobatpaws.ml.train --category {slug} --source hybrid`
5. `python -m sobatpaws.platform.registry --refresh`

### B2. Training dari synthetic CSV (ML views)
```bash
python scripts/build_ml_views.py   # ml_view_symptom_disease_cases
python -m sobatpaws.ml.train --source views --category dog
python -m sobatpaws.ml.train --source hybrid --max-view-cases 2000
```

### C. Uji konsultasi AI
1. `POST /consultations` dengan `ConsultationContext` + `IntakePayload`
2. Tampilkan `AISuggestion` ke dokter
3. `POST /consultations/{id}/doctor-input` (gold label)
4. `POST /learning/retrain` atau `python -m sobatpaws.ml.retrain`

### D. Agent AI interaktif (hemat token)
- Gunakan `POST /api/agent/conversations/{id}/chat` (bukan raw LLM)
- Provider: `GET /api/agent/providers`, aktivasi via admin
- Mode `SOBATPAWS_AI_AUGMENTATION_MODE=smart` melewati LLM bila ML+KB yakin

## 7. Zona aman vs berbahaya

**Aman:**
- `data/clinical/*.json`, `data/breeds/*.json`
- `src/sobatpaws/ai/safety.py` (guardrail obat)
- `src/sobatpaws/platform/*`
- `web/index.html`, `web/admin.html`

**Hati-hati:**
- `dbml/schema.dbml` → sync dengan `scripts/validate_dataset.py`
- `scripts/catalogs.py` → jalankan `scripts/sync_catalogs_from_kb.py` setelah edit JSON curated

**Jangan:**
- Commit `.env`, API keys
- Edit `data/generated/*.csv` manual
- Force push / destructive git

## 8. Environment variables penting

| Variable | Default | Fungsi |
|----------|---------|--------|
| `PYTHONPATH` | `src` | Wajib untuk import sobatpaws |
| `SOBATPAWS_AI_PROVIDER` | openai | openai / anthropic / local |
| `SOBATPAWS_AI_AUGMENTATION_MODE` | smart | smart / always / never |
| `SOBATPAWS_LEARNING_BACKEND` | jsonl | jsonl / postgres / both |
| `SOBATPAWS_VET_API_KEY` | - | Auth app vet |
| `SOBATPAWS_ADMIN_API_KEY` | - | Admin + pipeline run |
| `DATABASE_URL` | postgresql://... | PostgreSQL (learning + ml_models) |

## 9. Output terstruktur untuk agent

Semua endpoint platform & doctor mengembalikan **JSON** dengan:
- `status`: healthy | degraded | success | failed
- `checks` / `results`: array detail
- `recommended_next`: langkah perintah siap jalankan

Registry (`artifacts/platform_registry.json`):
- `data_tracks.curated_json.stats`
- `models[]` dengan metrics per kategori
- `lineage` menjelaskan sumber training

## 10. Troubleshooting cepat

| Gejala | Perbaikan |
|--------|-----------|
| ML predict 404 | `python -m sobatpaws.ml.train --category {cat}` |
| Saran AI kosong | Cek gejala terdeteksi; perlu teks keluhan jelas |
| synthetic manifest missing | `python scripts/generate_all.py --scale 0.05` |
| gold_rows = 0 | Dokter harus `POST .../doctor-input` dengan `confirmed_disease_slug` |
| platform_router import error | Pastikan `from .platform_router import router` di main.py |

## 11. Referensi

- README.md — dokumentasi manusia
- docs/INTEGRATION.md — integrasi app vet
- dbml/schema.dbml — skema database
- OpenAPI: http://localhost:8000/docs
