# Knowledge Base (KB) Ekosistem Satwa

> Dokumentasi resmi Knowledge Base veteriner Ekosistem Satwa dengan pipeline ekspansi otomatis menuju **350,000+ penyakit**.

---

## Ringkasan

| Item | Nilai |
|------|-------|
| **Current Diseases** | 5,013 |
| **Target** | 350,000 |
| **Auto-Expand** | Setiap 10 menit |
| **Spesies** | 11 kategori |
| **Format** | JSON (curated truth) |

```
## Knowledge Base
- Total Diseases: 5,013 → 350,000 (auto-expand setiap 10 menit)
- Species: 11
- Expansion Pipeline: expand_knowledge_base.py → sync → deploy → git push
```

---

## Pipeline Ekspansi KB

### Alur Lengkap

```
┌─────────────────────────────────────────────────────────────────────┐
│                    KB EXPANSION PIPELINE                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │ expand_      │───▶│ expand_      │───▶│ sync_        │          │
│  │ knowledge_   │    │ other_       │    │ catalogs_    │          │
│  │ base.py      │    │ species.py   │    │ from_kb.py   │          │
│  │ (dog+cat)    │    │ (others)     │    │ (vocabulary) │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│         │                   │                   │                     │
│         └───────────────────┴───────────────────┘                     │
│                             │                                           │
│                             ▼                                           │
│                    ┌──────────────┐                                     │
│                    │ seed_        │                                     │
│                    │ generator.py │───▶ PostgreSQL / seed.sql         │
│                    │              │                                     │
│                    └──────────────┘                                     │
│                             │                                           │
│                             ▼                                           │
│                    ┌──────────────┐                                     │
│                    │  git push    │───▶ Production                     │
│                    │              │                                     │
│                    └──────────────┘                                     │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Step-by-Step Pipeline

| Step | Script | Lokasi | Fungsi |
|------|--------|--------|--------|
| 1 | `expand_knowledge_base.py` | `scripts/` | Generate penyakit baru untuk **dog & cat** dengan gejala, diagnosa, tindakan, obat lengkap |
| 2 | `expand_other_species.py` | `scripts/` | Ekspansi untuk **8 spesies lainnya** (rabbit, hamster, poultry, fish, reptile, amphibian, ferret, guinea_pig, exotic) |
| 3 | `sync_catalogs_from_kb.py` | `scripts/` | Sinkronisasi vocabulary penyakit/gejala dari curated JSON ke `catalogs.py` untuk synthetic data generator |
| 4 | `_run_expansion_local.py` | `scripts/` | **Runner lokal** untuk development — menjalankan semua script di atas dengan path lokal yang benar |
| 5 | `seed_generator.py` | `src/ekosistem_satwa/` | Generate `seed/seed.sql` dari JSON KB untuk import ke PostgreSQL |
| 6 | `git push` | - | Deploy ke production (triggered oleh cron atau manual) |

---

## Daftar Script KB

### 1. `scripts/expand_knowledge_base.py`

Script utama untuk ekspansi penyakit dog & cat. Berisi `EXPANDED_DISEASES` — dictionary besar dengan definisi penyakit yang sangat detail.

**Fitur per penyakit:**
- `slug`, `name`, `name_id` (nama internasional + lokal)
- `etiology`: infectious_viral, bacterial, parasitic, endocrine, degenerative, neoplastic, allergic, etc.
- `body_system`: digestive, respiratory, neurologic, cardiovascular, urinary, etc.
- `is_contagious`, `is_zoonotic` (penting untuk keselamatan)
- `is_emergency`, `default_severity` (triage)
- `overview`, `causes`, `prevention`, `prognosis`
- `symptoms[]`: setiap gejala punya `name`, `name_id`, `body_system`, `frequency`, `is_red_flag`, `is_pathognomonic`
- `diagnostics[]`: `name`, `name_id`, `category` (rapid_test, molecular, laboratory, imaging), `sensitivity`
- `treatments[]`: `type` (supportive_care, pharmacological, surgical, rehabilitation, dietary, biological), `name`, `protocol`
- `medications[]`: `name`, `category`, `dosage`, `route`, `contraindications[]`
- `referrals[]`: spesialis yang dirujuk

**Cara menjalankan:**
```bash
# via runner lokal (recommended)
.venv/bin/python scripts/_run_expansion_local.py

# atau langsung (perlu adjust path)
python scripts/expand_knowledge_base.py
```

### 2. `scripts/expand_other_species.py`

Ekspansi untuk spesies selain dog & cat. Struktur `EXPANSIONS` sama dengan `EXPANDED_DISEASES` tapi per file JSON.

**Spesies yang dicakup:**
- `diseases_rabbits.json`
- `diseases_hamsters.json`
- `diseases_poultry.json`
- `diseases_fish.json`
- `diseases_reptiles.json`
- `diseases_amphibian.json`
- `diseases_ferret.json`
- `diseases_guinea_pig.json`
- `diseases_exotic_others.json`

### 3. `scripts/sync_catalogs_from_kb.py`

Sinkronisasi vocabulary dari curated JSON ke `scripts/catalogs.py` yang digunakan oleh generator synthetic dataset.

**Yang disinkronkan:**
- Daftar nama penyakit
- Daftar gejala unik
- Mapping gejala → penyakit
- Body system categories

### 4. `scripts/_run_expansion_local.py`

**Runner development** yang menyesuaikan path dari `/app/data` (Docker) ke path lokal `./data/`.

```python
# Yang dilakukan script ini:
1. Baca expand_knowledge_base.py
2. Replace BASE = '/app/data' → BASE = './data'
3. Execute untuk mendapatkan EXPANDED_DISEASES
4. Merge ke existing diseases_dogs.json, diseases_cats.json
5. Lakukan hal sama untuk expand_other_species.py
6. Print summary: new, updated, total per spesies
```

---

## Spesies yang Didukung (11)

| Spesies | Slug | File JSON | Contoh Penyakit |
|---------|------|-----------|-----------------|
| 🐶 Anjing | `dog` | `diseases_dogs.json` | Parvovirus, Distemper, Hip Dysplasia, Heartworm, Diabetes, Epilepsi |
| 🐱 Kucing | `cat` | `diseases_cats.json` | FPV Panleukopenia, Feline Leukemia, CKD, FLUTD, HCM, Dermatofitosis |
| 🐰 Kelinci | `rabbit` | `diseases_rabbits.json` | Snuffles (Pasteurellosis), GI Stasis, Dental Malocclusion |
| 🐹 Hamster | `hamster` | `diseases_hamsters.json` | Wet Tail, Diabetes Mellitus, Cheek Pouch Impaction |
| 🐔 Unggas | `poultry` | `diseases_poultry.json` | Newcastle Disease, Coccidiosis, Egg Binding |
| 🐟 Ikan | `fish` | `diseases_fish.json` | Ich (White Spot), Fin Rot, Dropsy |
| 🦎 Reptil | `reptile` | `diseases_reptiles.json` | Metabolic Bone Disease, Respiratory Infection, Shell Rot |
| 🐸 Amfibi | `amphibian` | `diseases_amphibian.json` | Chytridiomycosis, Red Leg Syndrome |
| 🦊 Ferret | `ferret` | `diseases_ferret.json` | Insulinoma, Adrenal Disease, Aleutian Disease |
| 🐹 Marmut | `guinea_pig` | `diseases_guinea_pig.json` | Scurvy (Vit C deficiency), Bumblefoot |
| 🌴 Eksotis | `exotic` | `diseases_exotic_others.json` | Spesies eksotis lainnya |

---

## Struktur Data Penyakit

Setiap penyakit di KB adalah JSON **self-contained** dengan semua informasi klinis yang dibutuhkan AI Suggestion Engine.

```json
{
  "slug": "dog-parvovirus",
  "name": "Canine Parvovirus Enteritis",
  "name_id": "Parvovirus (Parvo)",
  
  "etiology": "infectious_viral",
  "body_system": "digestive",
  "is_contagious": true,
  "is_zoonotic": false,
  "default_severity": "critical",
  "is_emergency": true,
  
  "overview": "Infeksi virus sangat menular menyerang sel usus dan sumsum tulang...",
  "causes": "Virus CPV-2 menyebar via feses, kontak langsung...",
  "prevention": "Vaksinasi DHPP lengkap, sanitasi disinfektan...",
  "prognosis": "Tanpa terapi mortalitas tinggi; dengan rawat inap survival 70-90%.",
  
  "symptoms": [
    {
      "name": "Bloody diarrhea",
      "name_id": "Diare berdarah",
      "body_system": "digestive",
      "frequency": "very_high",
      "is_red_flag": true,
      "is_pathognomonic": true
    }
  ],
  
  "diagnostics": [
    {
      "name": "Fecal ELISA Parvo test",
      "name_id": "Tes ELISA feses Parvo",
      "category": "rapid_test",
      "sensitivity": "high"
    }
  ],
  
  "treatments": [
    {
      "type": "supportive_care",
      "name": "Terapi suportif rawat inap parvo",
      "protocol": "IV fluids (Lactated Ringer's), antiemetics, antibiotics..."
    }
  ],
  
  "medications": [
    {
      "name": "Maropitant (Cerenia)",
      "category": "antiemetic",
      "dosage": "1 mg/kg SC/PO q24h",
      "route": "SC/PO",
      "contraindications": ["Hepatic impairment"]
    }
  ],
  
  "referrals": ["Internal Medicine Specialist", "Emergency & Critical Care Specialist"]
}
```

### Field Categories

| Field | Nilai yang mungkin |
|-------|-------------------|
| `etiology` | infectious_viral, infectious_bacterial, parasitic, fungal, endocrine, metabolic, degenerative, neoplastic, inflammatory, allergic, genetic_developmental, traumatic, toxic, idiopathic |
| `body_system` | digestive, respiratory, neurologic, cardiovascular, urinary, reproductive, musculoskeletal, integumentary, ophthalmic, hematologic, lymphatic, endocrine, systemic |
| `frequency` | very_high, high, moderate, low |
| `default_severity` | critical, severe, moderate, mild |
| `treatment.type` | supportive_care, pharmacological, surgical, rehabilitation, dietary, biological, topical |
| `diagnostics.category` | rapid_test, molecular, laboratory, imaging, pathology, physical, allergy, dietary, monitoring |

---

## Lokasi File KB

```
data/
├── categories.json              # 11 kategori spesies
├── breeds/
│   ├── dogs.json
│   ├── cats.json
│   ├── rabbits.json
│   ├── hamsters.json
│   ├── poultry.json
│   ├── fish.json
│   ├── reptiles.json
│   └── others.json
└── clinical/
    ├── diseases_dogs.json           # 🐶
    ├── diseases_cats.json           # 🐱
    ├── diseases_rabbits.json        # 🐰
    ├── diseases_hamsters.json       # 🐹
    ├── diseases_poultry.json        # 🐔
    ├── diseases_fish.json           # 🐟
    ├── diseases_reptiles.json       # 🦎
    ├── diseases_amphibian.json      # 🐸
    ├── diseases_ferret.json         # 🦊
    ├── diseases_guinea_pig.json     # 🐹
    ├── diseases_exotic_others.json  # 🌴
    └── extensions/
        └── medication_kb.json        # KB obat per spesies
```

---

## Auto-Expand Mechanism

KB diekspansi secara **otomatis setiap 10 menit** via cron job.

### Cron Schedule

```bash
# Crontab entry (contoh)
*/10 * * * * cd /app && .venv/bin/python scripts/_run_expansion_local.py && git add data/ && git commit -m "auto: KB expansion $(date +%Y%m%d-%H%M)" && git push
```

### Yang terjadi setiap run:

1. **Generate baru** — penyakit baru ditambahkan dari template `EXPANDED_DISEASES`
2. **Update existing** — penyakit yang sudah ada diperbarui dengan informasi lebih lengkap
3. **Merge otomatis** — tidak ada overwrite; existing slug dipertahankan dan di-update
4. **Sync catalog** — vocabulary disinkron ke generator synthetic
5. **Commit & Push** — otomatis ke repository

### Development vs Production

| Environment | Runner | Path |
|-------------|--------|------|
| **Development** | `_run_expansion_local.py` | `./data/` |
| **Production (Docker)** | langsung `expand_knowledge_base.py` | `/app/data/` |

---

## Cara Menjalankan Manual

### Full Expansion (Development)

```bash
cd "/Users/winnerharry/Naincode AI Dept/projects/sobatpaws-ai"

# Jalankan runner lokal
.venv/bin/python scripts/_run_expansion_local.py
```

### Generate Seed SQL

```bash
export PYTHONPATH=src
python -m ekosistem_satwa.seed_generator
# Output: seed/seed.sql
```

### Cek Stats KB

```bash
export PYTHONPATH=src
python -m ekosistem_satwa.data_loader
# Output: categories: 11, breeds: 177, diseases: N, unique_symptoms: N
```

---

## Target 350,000 Penyakit

### Breakdown Target

| Spesies | Target Penyakit |
|---------|-----------------|
| Anjing (dog) | 50,000 |
| Kucing (cat) | 50,000 |
| Kelinci | 30,000 |
| Hamster | 25,000 |
| Unggas | 40,000 |
| Ikan | 45,000 |
| Reptil | 30,000 |
| Amfibi | 20,000 |
| Ferret | 20,000 |
| Marmut | 20,000 |
| Eksotis | 20,000 |
| **TOTAL** | **350,000** |

### Strategi Ekspansi

1. **Template-based generation** — `EXPANDED_DISEASES` berisi template penyakit yang divariasikan
2. **Per kombinasi** — penyakit × spesies × ras × varian
3. **Gejala kombinatorial** — setiap penyakit punya banyak kombinasi gejala
4. **Severity levels** — mild, moderate, severe, critical untuk setiap penyakit
5. **Age-specific variants** — pediatric, adult, geriatric presentation

---

## Integrasi dengan AI Engine

KB adalah **sumber kebenaran (ground truth)** untuk:

1. **ML Training** — `ml/train.py` menggunakan gejala dari KB untuk fitur
2. **RAG Retrieval** — `ai/suggestion_engine.py` retrieve dari KB
3. **Safety Guardrail** — `ai/safety.py` menggunakan kontraindikasi dari `medication_kb.json`
4. **Seed Database** — `seed_generator.py` generate SQL untuk PostgreSQL

---

## Related Files

| File | Keterangan |
|------|-----------|
| `README.md` | Ringkasan KB di section "Knowledge Base Expansion" |
| `docs/jurnal/` | Monograf riset per penyakit (human-readable) |
| `scripts/catalogs.py` | Vocabulary untuk synthetic generator |
| `src/ekosistem_satwa/data_loader.py` | Loader KB ke memory |
| `src/ekosistem_satwa/seed_generator.py` | JSON → SQL |
| `src/ekosistem_satwa/ai/safety.py` | Guardrail dari medication_kb.json |

---

## Changelog

| Tanggal | Perubahan |
|---------|-----------|
| 2026-06-27 | Dokumentasi KB dibuat. Update: 5,013 → 350,000 target, 11 spesies, auto-expand 10 menit |

---

*Terakhir diperbarui: 27 Juni 2026*
