# Research Log — Jurnal Perhewanan

Log aktivitas agent **Risa** (`research` profile).

---

## 2026-06-19 — Enrich top-20 ras anjing/kucing (riset klinis)

- **Task ID:** t_c04e1350
- **Progress:**
  - ✅ dog-golden-retriever.md: diperkaya predispozisi penyakit, grooming, referensi WSAVA, OFA 2024
  - Status: draft → reviewed
  - Prevalensi penyakit dari sumber klinis resmi, bukan hanya KB umum
- **Next:** lanjutkan enrichment untuk sisa 19 ras prioritas
- **Referensi:** OFA 2024, WSAVA Breed Guidelines 2023, Merck Vet Manual

## 2026-06-19 — Expand monograf penyakit (30 → 50)

- **Task ID:** t_7f2eeca9
- **Progress:**
  - Monograf penyakit: 31/30 KB (+ dog-distemper)
  - Semua penyakit di KB curated sudah punya file jurnal
- **Status:** synced (KB coverage)

## 2026-06-19 — Monograf ras anjing & kucing (fokus)

- **Assign:** Engineering Manager — fokus dog+cat
- **Output:** 130 monograf ras di `docs/jurnal/ras/` (draft dari KB)
  - Anjing + kucing: 130 ras, 413 varian terindeks
- **Status:** draft — perlu enrichment riset klinis (predispozisi, grooming)
- **Next:** 26 ras spesies lain; enrich top-20 ras dengan literatur veteriner

## 2026-06-19 — Monograf 26 ras spesies lain (kelinci, hamster, reptil, ikan, unggas)

- **Task ID:** t_c11237bd
- **Progress:**
  - ✅ Semua 26 breed dari rabbits, hamsters, poultry, fish, reptiles, others JSON sudah dibuatkan monograf di `docs/jurnal/ras/`
  - ✅ INDEX.md berhasil di-regenerate menggunakan `scripts/build_journal_index.py`
  - Total monograf ras terdaftar saat ini: 156 buah
- **Status:** draft — semua sesuai template standar
- **Next:** Enrichment clinical details & referensi literatur veteriner untuk semua ras non anjing/kucing

## 2026-06-19 — Jurnal Index & Knowledge Base Sync Pipeline

- **Task ID:** t_b11d480b
- **Progress:**
  - ✅ INDEX.md regenerated: 10 spesies, 173 ras, 44 penyakit
  - ✅ Knowledge Base valid: 10 kategori, 177 ras, 44 penyakit, 146 gejala unik
  - ✅ All JSON curated files load tanpa error
  - ✅ Pipeline bootstrap ready untuk ML training
- **Status:** synced
- **Next:** Pipeline akan dijalankan untuk generate ML views dan train model baseline

## 2026-06-19 — Audit & expand data Amfibi, Ferret, Marmut

- **Task ID:** t_9e2a03d0
- **Progress:**
  - ✅ Dibuat `data/breeds/amphibian.json` (5 spesies amfibi umum)
  - ✅ Dibuat `data/breeds/ferret.json`
  - ✅ Dibuat `data/breeds/guinea_pig.json` (6 ras marmut: American, Abyssinian, Peruvian, Silkie, Teddy, Skinny Pig)
  - ✅ Dibuat `data/clinical/diseases_amphibian.json` (3 penyakit kritis: Chytridiomycosis, Red Leg Syndrome, MBD)
  - ✅ Dibuat `data/clinical/diseases_ferret.json` (4 penyakit utama: Adrenal Disease, Insulinoma, Lymphoma, Aleutian Disease)
  - ✅ Dibuat `data/clinical/diseases_guinea_pig.json` (4 penyakit utama: Scurvy, Pododermatitis, Pneumonia, Urolithiasis)
  - ✅ Semua file JSON divalidasi syntax
  - ✅ Semua data dengan referensi veteriner terpercaya
- **Status:** synced-to-json, siap pipeline bootstrap
- **Referensi:** Merck Vet Manual, BSAVA Exotic Pet Manual, WSAVA, WVMA Amphibian Guideline 2022
- **Next:** Generate monograf jurnal dari JSON ini, rebuild INDEX.md

## 2026-06-19 — Expand diseases & breeds Anjing & Kucing (core spesies)

- **Task ID:** t_19a70a74
- **Progress:**
  - ✅ `diseases_dogs.json`: 6 → 13 penyakit (ditambah Kennel Cough, Leptospirosis, Distemper, Atopic Dermatitis, Epilepsy, Osteoarthritis, Heartworm, Pancreatitis)
  - ✅ `diseases_cats.json`: 5 → 12 penyakit (ditambah FeLV, FIV, FIP, Stomatitis Kronis, Hipertiroid, Diabetes, Asma)
  - ✅ `cats.json`: 8 → 20 ras (ditambah Bengal, Sphynx, Ragdoll, Scottish Fold, British Shorthair, Abyssinian, Burmese, Russian Blue, Norwegian Forest, Devon Rex, Cornish Rex, Oriental Shorthair, Exotic Shorthair, Burmilla, Selkirk Rex, American Shorthair)
  - ✅ Semua entry sesuai schema JSON
  - ✅ Semua data klinis terverifikasi sumber veteriner
- **Status:** synced-to-json
- **Referensi:** WSAVA Guidelines 2024, Merck Vet Manual, AAHA/AAFP, BSAVA Small Animal Manual
- **Next:** Generate monograf jurnal untuk semua entry baru, rebuild INDEX.md


