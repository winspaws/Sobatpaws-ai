# API Request/Response Examples

Contoh request dan response real dari endpoint integrasi Ekosistem Satwa.

---

### Health Check

**GET /health**

**Response:**

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

---

### Integration Manifest

**GET /api/integration/manifest**

**Response:**

```json

{
  "platform": {
    "manifest_url": "http://testserver/api/platform/manifest",
    "doctor_url": "http://testserver/api/platform/doctor",
    "registry_url": "http://testserver/api/platform/registry",
    "pipeline_url": "http://testserver/api/platform/pipeline",
    "agent_api": "http://testserver/api/agent"
  },
  "api_version": "0.3.0",
  "openapi_url": "http://testserver/docs",
  "auth": {
    "enabled": false,
    "vet_key_configured": false,
    "admin_key_configured": false,
    "header": "X-EkosistemSatwa-Key",
    "alt_header": "Authorization: Bearer <key>"
  },
  "client": {
    "role": "public",
    "authenticated": false
  },
  "recommended_flow": [
    "1. GET /health — cek koneksi",
    "2. GET /api/integration/id-schema — kontrak ID entitas (vet, pelanggan, pet, ...)",
    "3. GET /categories + /categories/{slug}/breeds — muat master data",
    "4. POST /consultations — mulai sesi (context: org_id, vet_id, owner_id, pet_id, external_consultation_id)",
    "5. POST /consultations/{id}/turns — kirim teks tambahan",
    "6. POST /consultations/{id}/media — unggah audio/gambar (multipart)",
    "7. Tampilkan suggestion + entities ke dokter (AISuggestion JSON)",
    "8. POST /api/agent/conversations/{id}/vet-record — input dokter lengkap",
    "9. POST /api/agent/conversations/{id}/chat — interaksi agent (hemat token)",
    "10. GET /api/integration/entities/{id} — ambil ID entitas untuk sync ke DB utama",
    "11. POST /consultations/{id}/feedback — penilaian saran AI"
  ],
  "shortcuts": {
    "single_shot": "POST /api/consult — tanpa sesi, tanpa learning loop",
    "ml_only": "POST /ml/predict — prediksi cepat tanpa LLM"
  },
  "token_efficiency": {
    "augmentation_mode": "smart",
    "note": "Mode 'smart' melewati LLM bila ML+KB sudah yakin (hemat token). Kirim pretranscribed_text / gejala terstruktur untuk minim panggilan vision/STT."
  },
  "endpoints": {
    "health": "http://testserver/health",
    "status": "http://testserver/api/status",
    "id_schema": "http://testserver/api/integration/id-schema",
    "entities": "http://testserver/api/integration/entities/{consultation_id}",
    "consultations": "http://testserver/consultations",
    "consultations_by_external": "http://testserver/api/integration/consultations/by-external/{external_id}",
    "categories": "http://testserver/categories",
    "symptoms": "http://testserver/api/symptoms"
  },
  "entity_ids": {
    "description": "ID entitas Ekosistem Satwa — kirim di context saat POST /consultations",
    "fields": {
      "org_id": {
        "type": "int",
        "db": "organizations.id",
        "required": false
      },
      "vet_id": {
        "type": "int",
        "db": "users.id",
        "aliases": [
          "user_id",
          "doctor_id"
        ],
        "required": true,
        "note": "Dokter yang menangani konsultasi"
      },
      "owner_id": {
        "type": "int",
        "db": "pet_owners.id",
        "aliases": [
          "customer_id"
        ],
        "required": true,
        "note": "Pelanggan/pemilik hewan"
      },
      "pet_id": {
        "type": "int",
        "db": "pets.id",
        "required": true
      },
      "case_id": {
        "type": "int",
        "db": "clinical_cases.id",
        "required": false
      },
      "external_consultation_id": {
        "type": "string",
        "note": "ID konsultasi dari app Ekosistem Satwa utama — untuk lookup & sync"
      },
      "consultation_id": {
        "type": "string",
        "note": "ID sesi AI — bisa dikirim saat start atau di-generate server"
      },
      "external_refs": {
        "type": "object",
        "note": "Map ID tambahan: appointment_id, invoice_id, dll."
      }
    },
    "response_field": "entities",
    "lookup_endpoints": [
      "GET /api/integration/entities/{consultation_id}",
      "GET /api/integration/consultations/by-external/{external_id}",
      "GET /api/integration/consultations?vet_id=&pet_id=&owner_id="
    ]
  },
  "headers_required": {
    "X-EkosistemSatwa-Key": false,
    "Content-Type": "application/json"
  },
  "media_upload": {
    "endpoint": "POST /consultations/{id}/media",
    "fields": [
      "file",
      "modality (audio|image|video_frame)",
      "channel"
    ],
    "tip": "Gunakan pretranscribed_text di JSON bila STT sudah di device — hemat token Whisper."
  },
  "learning_backend": "jsonl"
}

```

---

### ID Schema

**GET /api/integration/id-schema**

**Response:**

```json

{
  "description": "ID entitas Ekosistem Satwa — kirim di context saat POST /consultations",
  "fields": {
    "org_id": {
      "type": "int",
      "db": "organizations.id",
      "required": false
    },
    "vet_id": {
      "type": "int",
      "db": "users.id",
      "aliases": [
        "user_id",
        "doctor_id"
      ],
      "required": true,
      "note": "Dokter yang menangani konsultasi"
    },
    "owner_id": {
      "type": "int",
      "db": "pet_owners.id",
      "aliases": [
        "customer_id"
      ],
      "required": true,
      "note": "Pelanggan/pemilik hewan"
    },
    "pet_id": {
      "type": "int",
      "db": "pets.id",
      "required": true
    },
    "case_id": {
      "type": "int",
      "db": "clinical_cases.id",
      "required": false
    },
    "external_consultation_id": {
      "type": "string",
      "note": "ID konsultasi dari app Ekosistem Satwa utama — untuk lookup & sync"
    },
    "consultation_id": {
      "type": "string",
      "note": "ID sesi AI — bisa dikirim saat start atau di-generate server"
    },
    "external_refs": {
      "type": "object",
      "note": "Map ID tambahan: appointment_id, invoice_id, dll."
    }
  },
  "response_field": "entities",
  "lookup_endpoints": [
    "GET /api/integration/entities/{consultation_id}",
    "GET /api/integration/consultations/by-external/{external_id}",
    "GET /api/integration/consultations?vet_id=&pet_id=&owner_id="
  ]
}

```

---

### List Categories

**GET /categories**

**Response:**

```json

[
  {
    "slug": "dog",
    "name": "Dog",
    "name_id": "Anjing",
    "species_class": "mammal",
    "scientific_name": "Canis lupus familiaris",
    "description": "Mamalia karnivora domestikasi paling umum sebagai hewan pendamping & penjaga.",
    "avg_lifespan_years_min": 10,
    "avg_lifespan_years_max": 16
  },
  {
    "slug": "cat",
    "name": "Cat",
    "name_id": "Kucing",
    "species_class": "mammal",
    "scientific_name": "Felis catus",
    "description": "Mamalia karnivora obligat, hewan pendamping populer dengan perilaku teritorial.",
    "avg_lifespan_years_min": 12,
    "avg_lifespan_years_max": 18
  },
  {
    "slug": "rabbit",
    "name": "Rabbit",
    "name_id": "Kelinci",
    "species_class": "mammal",
    "scientific_name": "Oryctolagus cuniculus",
    "description": "Mamalia herbivora lagomorpha, gigi tumbuh terus & saluran cerna sensitif.",
    "avg_lifespan_years_min": 8,
    "avg_lifespan_years_max": 12
  }
]

```

---

### Start Consultation

**POST /consultations**

**Request:**

```json

{
  "context": {
    "vet_id": 1,
    "owner_id": 100,
    "pet_id": 200,
    "category_slug": "cat",
    "breed_slug": "cat-persian",
    "age_years": 3,
    "external_consultation_id": "ext-20250619-001"
  },
  "intake": {
    "channel": "chat",
    "text": "Kucing saya muntah hebat dan tidak mau makan sejak kemarin",
    "is_first_contact": true
  }
}

```

**Response:**

```json

{
  "consultation_id": "ext-20250619-001",
  "intake": {
    "complaint_text": "Kucing saya muntah hebat dan tidak mau makan sejak kemarin",
    "observations": [],
    "symptoms": [
      {
        "name_id": "Diare hebat",
        "name": "Profuse diarrhea",
        "body_system": "digestive",
        "is_red_flag": true,
        "score": 1.0,
        "matched_text": "hebat"
      },
      {
        "name_id": "Muntah",
        "name": "Vomiting",
        "body_system": "digestive",
        "is_red_flag": false,
        "score": 0.95,
        "matched_text": "muntah"
      },
      {
        "name_id": "Muntah hebat",
        "name": "Severe vomiting",
        "body_system": "digestive",
        "is_red_flag": true,
        "score": 0.95,
        "matched_text": "muntah hebat"
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
    "summary": "Berdasarkan 4 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 78%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
    "follow_up_questions": [
      "Sudah berapa lama gejala ini berlangsung?",
      "Apakah nafsu makan & minum berubah?",
      "Apakah ada perubahan pada urin/feses?",
      "Adakah riwayat vaksinasi & pengobatan terakhir?"
    ],
    "suggested_diseases": [
      {
        "disease_slug": "cat-fpv-panleukopenia",
        "name_id": "Panleukopenia (Distemper Kucing)",
        "confidence": 0.784,
        "rationale": "Cocok dengan gejala: Muntah hebat, Diare hebat",
        "is_emergency": true,
        "source": "ml+knowledge_base"
      },
      {
        "disease_slug": "cat-flutd",
        "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
        "confidence": 0.018,
        "rationale": null,
        "is_emergency": true,
        "source": "ml"
      },
      {
        "disease_slug": "cat-ckd",
        "name_id": "Penyakit Ginjal Kronis (CKD)",
        "confidence": 0.34,
        "rationale": "Cocok dengan gejala: Nafsu makan menurun, Muntah",
        "is_emergency": false,
        "source": "ml+knowledge_base"
      },
      {
        "disease_slug": "cat-dermatophytosis-ringworm",
        "name_id": "Ringworm (Jamur Kulit)",
        "confidence": 0.076,
        "rationale": null,
        "is_emergency": false,
        "source": "ml"
      },
      {
        "disease_slug": "cat-hcm",
        "name_id": "Kardiomiopati Hipertrofik (HCM)",
        "confidence": 0.042,
        "rationale": null,
        "is_emergency": false,
        "source": "ml"
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
      },
      {
        "name": "SNAP parvo (cross-reaktif FPV)",
        "type": "serology",
        "step_order": 1,
        "is_gold_standard": false,
        "expected_finding": "Antigen positif pada feses",
        "for_disease": "cat-fpv-panleukopenia"
      },
      {
        "name": "CBC",
        "type": "blood_test",
        "step_order": 3,
        "is_gold_standard": false,
        "expected_finding": "Panleukopenia (semua sel darah putih turun)",
        "for_disease": "cat-fpv-panleukopenia"
      },
      {
        "name": "Urinalisis + sedimen",
        "type": "urinalysis",
        "step_order": 2,
        "is_gold_standard": true,
        "expected_finding": "Kristal struvit/oksalat, darah, pH",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Palpasi kandung kemih",
        "type": "physical_exam",
        "step_order": 1,
        "is_gold_standard": false,
        "expected_finding": "Kandung kemih besar & keras (obstruksi)",
        "for_disease": "cat-flutd"
      },
      {
        "name": "USG / Radiografi",
        "type": "imaging_ultrasound",
        "step_order": 3,
        "is_gold_standard": false,
        "expected_finding": "Batu/urolith, dinding menebal",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Panel ginjal + elektrolit",
        "type": "blood_test",
        "step_order": 4,
        "is_gold_standard": false,
        "expected_finding": "Hiperkalemia & azotemia bila obstruksi",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Panel ginjal (BUN, Creatinine, SDMA)",
        "type": "blood_test",
        "step_order": 1,
        "is_gold_standard": true,
        "expected_finding": "SDMA & kreatinin meningkat",
        "for_disease": "cat-ckd"
      },
      {
        "name": "Urinalisis (USG, UPC)",
        "type": "urinalysis",
        "step_order": 2,
        "is_gold_standard": false,
        "expected_finding": "Urin encer (isostenuria), proteinuria",
        "for_disease": "cat-ckd"
      },
      {
        "name": "Tekanan darah",
        "type": "physical_exam",
        "step_order": 3,
        "is_gold_standard": false,
        "expected_finding": "Hipertensi sistemik",
        "for_disease": "cat-ckd"
      },
      {
        "name": "USG ginjal",
        "type": "imaging_ultrasound",
        "step_order": 4,
        "is_gold_standard": false,
        "expected_finding": "Ginjal mengecil/irregular atau kista (PKD)",
        "for_disease": "cat-ckd"
      },
      {
        "name": "Kultur jamur (DTM) / PCR",
        "type": "culture_sensitivity",
        "step_order": 3,
        "is_gold_standard": true,
        "expected_finding": "Pertumbuhan dermatofit",
        "for_disease": "cat-dermatophytosis-ringworm"
      },
      {
        "name": "Lampu Wood",
        "type": "physical_exam",
        "step_order": 1,
        "is_gold_standard": false,
        "expected_finding": "Fluoresensi hijau apel (M. canis sebagian)",
        "for_disease": "cat-dermatophytosis-ringworm"
      },
      {
        "name": "Trichogram (mikroskop bulu)",
        "type": "cytology",
        "step_order": 2,
        "is_gold_standard": false,
        "expected_finding": "Artrospora pada batang rambut",
        "for_disease": "cat-dermatophytosis-ringworm"
      },
      {
        "name": "Ekokardiografi",
        "type": "imaging_ultrasound",
        "step_order": 1,
        "is_gold_standard": true,
        "expected_finding": "Hipertrofi dinding ventrikel kiri >6mm",
        "for_disease": "cat-hcm"
      },
      {
        "name": "NT-proBNP test",
        "type": "blood_test",
        "step_order": 2,
        "is_gold_standard": false,
        "expected_finding": "Meningkat (skrining)",
        "for_disease": "cat-hcm"
      },
      {
        "name": "Radiografi toraks",
        "type": "imaging_xray",
        "step_order": 3,
        "is_gold_standard": false,
        "expected_finding": "Edema paru/efusi bila gagal jantung",
        "for_disease": "cat-hcm"
      },
      {
        "name": "Tekanan darah & T4",
        "type": "blood_test",
        "step_order": 4,
        "is_gold_standard": false,
        "expected_finding": "Singkirkan hipertiroid/hipertensi",
        "for_disease": "cat-hcm"
      }
    ],
    "suggested_treatments": [
      {
        "name": "Terapi suportif panleukopenia",
        "type": "supportive_care",
        "line_of_therapy": 1,
        "procedure_steps": "1) Isolasi & barrier nursing. 2) Cairan IV + elektrolit + glukosa. 3) Antiemetik. 4) Antibiotik cegah sepsis. 5) Nutrisi dini. 6) Monitor jumlah sel darah.",
        "recommendation": "Tidak ada antivirus spesifik; suportif agresif menentukan survival.",
        "for_disease": "cat-fpv-panleukopenia"
      },
      {
        "name": "Penanganan obstruksi uretra (darurat)",
        "type": "supportive_care",
        "line_of_therapy": 1,
        "procedure_steps": "1) Stabilkan: cairan IV, koreksi hiperkalemia. 2) Sedasi + pasang kateter uretra untuk dekompresi. 3) Bilas kandung kemih. 4) Rawat inap, pantau elektrolit & produksi urin. 5) Analgesik.",
        "recommendation": "Obstruksi = DARURAT; hiperkalemia bisa henti jantung. Segera ke klinik.",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Manajemen FIC non-obstruktif",
        "type": "dietary",
        "line_of_therapy": 1,
        "procedure_steps": "1) Diet urinary (lar­ut struvit / kontrol mineral). 2) Tingkatkan asupan air (makanan basah, fountain). 3) Kurangi stres (pheromone, environmental enrichment). 4) Analgesik jangka pendek.",
        "recommendation": "Fokus hidrasi & manajemen stres untuk cegah kekambuhan.",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Manajemen CKD bertahap (IRIS)",
        "type": "dietary",
        "line_of_therapy": 1,
        "procedure_steps": "1) Diet renal (protein berkualitas terbatas, fosfor rendah). 2) Phosphate binder bila perlu. 3) Kontrol tekanan darah. 4) Terapi cairan subkutan di rumah. 5) Atasi mual & anemia. 6) Monitor berkala.",
        "recommendation": "Diet renal adalah intervensi paling berdampak; mulai sedini mungkin & pantau tiap 3-6 bulan.",
        "for_disease": "cat-ckd"
      },
      {
        "name": "Antijamur topikal + sistemik",
        "type": "pharmacological",
        "line_of_therapy": 1,
        "procedure_steps": "1) Antijamur topikal (lime sulfur/miconazole) seluruh tubuh. 2) Antijamur sistemik (itraconazole) untuk kasus luas. 3) Dekontaminasi lingkungan rutin. 4) Recheck dengan kultur sampai negatif 2x.",
        "recommendation": "Tangani semua hewan kontak + lingkungan; gunakan sarung tangan (zoonosis).",
        "for_disease": "cat-dermatophytosis-ringworm"
      },
      {
        "name": "Manajemen HCM & gagal jantung",
        "type": "pharmacological",
        "line_of_therapy": 1,
        "procedure_steps": "1) Diuretik bila kongesti paru. 2) Pengelolaan ritme/beta-blocker bila indikasi. 3) Antitrombotik cegah ATE. 4) Batasi stres & aktivitas berat. 5) Monitor ekokardiografi berkala.",
        "recommendation": "Cegah pembekuan (ATE) pada atrium kiri membesar; tangani edema paru sebagai darurat.",
        "for_disease": "cat-hcm"
      }
    ],
    "suggested_products": [
      {
        "name": "Cairan IV + elektrolit",
        "kind": "medication",
        "active_ingredient": "Ringer Lactate + KCl",
        "route": "IV",
        "dosage_guide": "Koreksi defisit + maintenance",
        "cautions": "Pantau kalium.",
        "safety_flag": null
      },
      {
        "name": "Maropitant",
        "kind": "medication",
        "active_ingredient": "Maropitant",
        "route": "SC",
        "dosage_guide": "1 mg/kg SID",
        "cautions": "Antiemetik.",
        "safety_flag": null
      },
      {
        "name": "Antibiotik beta-lactam",
        "kind": "medication",
        "active_ingredient": "Ampicillin",
        "route": "IV",
        "dosage_guide": "20 mg/kg q8h",
        "cautions": "Cegah translokasi bakteri.",
        "safety_flag": null
      },
      {
        "name": "Cairan IV (NaCl 0.9%)",
        "kind": "medication",
        "active_ingredient": "Saline",
        "route": "IV",
        "dosage_guide": "Koreksi dehidrasi + diuresis",
        "cautions": "Pantau status jantung.",
        "safety_flag": null
      },
      {
        "name": "Calcium gluconate",
        "kind": "medication",
        "active_ingredient": "Calcium gluconate",
        "route": "IV",
        "dosage_guide": "Proteksi jantung saat hiperkalemia",
        "cautions": "Monitor EKG.",
        "safety_flag": null
      },
      {
        "name": "Buprenorphine",
        "kind": "medication",
        "active_ingredient": "Buprenorphine",
        "route": "oral transmucosal/IV",
        "dosage_guide": "0.02 mg/kg",
        "cautions": "Analgesik aman kucing.",
        "safety_flag": null
      },
      {
        "name": "Diet resep urinary (s/o)",
        "kind": "food_prescription",
        "active_ingredient": "Diet kontrol mineral/pH",
        "route": "oral",
        "dosage_guide": "Sesuai kebutuhan kalori",
        "cautions": "Diet jangka panjang sesuai tipe kristal.",
        "safety_flag": null
      },
      {
        "name": "Feliway (feline pheromone)",
        "kind": "supplement",
        "active_ingredient": "Synthetic pheromone",
        "route": "lingkungan",
        "dosage_guide": "Diffuser ruangan",
        "cautions": "Pendukung, bukan obat.",
        "safety_flag": null
      },
      {
        "name": "Diet resep renal",
        "kind": "food_prescription",
        "active_ingredient": "Diet rendah fosfor & protein terkontrol",
        "route": "oral",
        "dosage_guide": "Sesuai kalori",
        "cautions": "Transisi bertahap agar mau makan.",
        "safety_flag": null
      },
      {
        "name": "Telmisartan / Amlodipine",
        "kind": "medication",
        "active_ingredient": "Telmisartan (proteinuria) / Amlodipine (hipertensi)",
        "route": "oral",
        "dosage_guide": "Sesuai resep & tekanan darah",
        "cautions": "Pantau tekanan darah & ginjal.",
        "safety_flag": null
      },
      {
        "name": "Phosphate binder",
        "kind": "supplement",
        "active_ingredient": "Aluminium hidroksida / chitosan",
        "route": "oral (dengan makan)",
        "dosage_guide": "Sesuai kadar fosfat",
        "cautions": "Diberikan bersama makanan.",
        "safety_flag": null
      },
      {
        "name": "Maropitant / Mirtazapine",
        "kind": "medication",
        "active_ingredient": "Maropitant (mual), Mirtazapine (perangsang nafsu makan)",
        "route": "oral/SC",
        "dosage_guide": "Sesuai BB",
        "cautions": "Mirtazapine dosis kecil pada kucing.",
        "safety_flag": null
      },
      {
        "name": "Itraconazole",
        "kind": "medication",
        "active_ingredient": "Itraconazole",
        "route": "oral",
        "dosage_guide": "5 mg/kg SID (pulse 1 minggu on/off)",
        "cautions": "Monitor hati.",
        "safety_flag": null
      },
      {
        "name": "Lime sulfur dip",
        "kind": "medication",
        "active_ingredient": "Sulfurated lime",
        "route": "topikal",
        "dosage_guide": "2x/minggu",
        "cautions": "Bau menyengat, hindari mata.",
        "safety_flag": null
      },
      {
        "name": "Miconazole/chlorhexidine shampoo",
        "kind": "grooming",
        "active_ingredient": "Miconazole + chlorhexidine",
        "route": "topikal",
        "dosage_guide": "2x/minggu",
        "cautions": "Bilas bersih.",
        "safety_flag": null
      },
      {
        "name": "Furosemide",
        "kind": "medication",
        "active_ingredient": "Furosemide",
        "route": "oral/IV",
        "dosage_guide": "Sesuai derajat kongesti",
        "cautions": "Pantau ginjal & elektrolit.",
        "safety_flag": null
      },
      {
        "name": "Clopidogrel",
        "kind": "medication",
        "active_ingredient": "Clopidogrel",
        "route": "oral",
        "dosage_guide": "18.75 mg/kucing SID",
        "cautions": "Antiplatelet cegah tromboemboli.",
        "safety_flag": null
      },
      {
        "name": "Atenolol",
        "kind": "medication",
        "active_ingredient": "Atenolol",
        "route": "oral",
        "dosage_guide": "Sesuai resep",
        "cautions": "Hati-hati bila gagal jantung dekompensasi.",
        "safety_flag": null
      },
      {
        "name": "Pimobendan (kasus tertentu)",
        "kind": "medication",
        "active_ingredient": "Pimobendan",
        "route": "oral",
        "dosage_guide": "Sesuai resep kardiolog",
        "cautions": "Tidak rutin untuk HCM obstruktif.",
        "safety_flag": null
      }
    ],
    "red_flags": [
      "Muntah hebat",
      "Diare hebat"
    ],
    "safety_warnings": [
      "Data edukatif. Diagnosa & resep final wajib oleh dokter hewan. PERHATIAN: kucing sangat sensitif terhadap banyak obat (paracetamol, permethrin, NSAID dosis anjing = FATAL).",
      "Cairan IV + elektrolit: Pantau kalium.",
      "Maropitant: Antiemetik.",
      "Antibiotik beta-lactam: Cegah translokasi bakteri.",
      "Cairan IV (NaCl 0.9%): Pantau status jantung.",
      "Calcium gluconate: Monitor EKG.",
      "Buprenorphine: Analgesik aman kucing.",
      "Diet resep urinary (s/o): Diet jangka panjang sesuai tipe kristal.",
      "Feliway (feline pheromone): Pendukung, bukan obat.",
      "Diet resep renal: Transisi bertahap agar mau makan.",
      "Telmisartan / Amlodipine: Pantau tekanan darah & ginjal.",
      "Phosphate binder: Diberikan bersama makanan.",
      "Maropitant / Mirtazapine: Mirtazapine dosis kecil pada kucing.",
      "Itraconazole: Monitor hati.",
      "Lime sulfur dip: Bau menyengat, hindari mata.",
      "Miconazole/chlorhexidine shampoo: Bilas bersih.",
      "Furosemide: Pantau ginjal & elektrolit.",
      "Clopidogrel: Antiplatelet cegah tromboemboli.",
      "Atenolol: Hati-hati bila gagal jantung dekompensasi.",
      "Pimobendan (kasus tertentu): Tidak rutin untuk HCM obstruktif.",
      "paracetamol: FATAL untuk kucing (methemoglobinemia). Jangan diberikan.",
      "acetaminophen: FATAL untuk kucing. Jangan diberikan.",
      "permethrin: Sangat toksik untuk kucing (produk anjing). Bisa fatal.",
      "ibuprofen: Toksik; margin keamanan NSAID sangat sempit pada kucing.",
      "aspirin: Metabolisme lambat; hanya dosis sangat hati-hati oleh vet."
    ],
    "references": [
      {
        "type": "disease",
        "slug": "cat-fpv-panleukopenia",
        "name_id": "Panleukopenia (Distemper Kucing)",
        "overview": "Parvovirus kucing menyerang sumsum tulang & usus; sangat fatal pada anak kucing."
      },
      {
        "type": "disease",
        "slug": "cat-flutd",
        "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
        "overview": "Kumpulan kondisi saluran kemih bawah; sumbatan uretra pada jantan adalah DARURAT mematikan."
      },
      {
        "type": "disease",
        "slug": "cat-ckd",
        "name_id": "Penyakit Ginjal Kronis (CKD)",
        "overview": "Penurunan fungsi ginjal progresif, sangat umum pada kucing senior."
      },
      {
        "type": "disease",
        "slug": "cat-dermatophytosis-ringworm",
        "name_id": "Ringworm (Jamur Kulit)",
        "overview": "Infeksi jamur dermatofita pada kulit/bulu; menular ke hewan lain & manusia."
      },
      {
        "type": "disease",
        "slug": "cat-hcm",
        "name_id": "Kardiomiopati Hipertrofik (HCM)",
        "overview": "Penebalan otot ventrikel kiri, penyakit jantung paling umum pada kucing; risiko gagal jantung & tromboemboli."
      }
    ],
    "is_emergency": true,
    "generated_by": "rule_based",
    "disclaimer": "Saran AI bersifat pendukung keputusan klinis dan TIDAK menggantikan pemeriksaan langsung serta penilaian dokter hewan berlisensi. Dosis & produk wajib diverifikasi sesuai spesies, berat badan, dan kondisi pasien.",
    "created_at": "2026-06-19T13:00:57.218553Z"
  },
  "suggestion_id": "b8ada203aaa1462ca957fd11d98168dd",
  "suggestion_ref": "b8ada203aaa1462ca957fd11d98168dd",
  "entities": {
    "consultation_id": "ext-20250619-001",
    "external_consultation_id": "ext-20250619-001",
    "org_id": null,
    "vet_id": 1,
    "owner_id": 100,
    "customer_id": 100,
    "pet_id": 200,
    "case_id": null,
    "external_refs": {}
  }
}

```

---

### Add Turn (Cumulative Symptoms)

**POST /consultations/ext-20250619-001/turns**

**Request:**

```json

{
  "intake": {
    "channel": "chat",
    "text": "Sekarang juga diare berdarah dan lemas sekali"
  }
}

```

**Response:**

```json

{
  "consultation_id": "ext-20250619-001",
  "intake": {
    "complaint_text": "Sekarang juga diare berdarah dan lemas sekali",
    "observations": [],
    "symptoms": [
      {
        "name_id": "Diare hebat",
        "name": "Profuse diarrhea",
        "body_system": "digestive",
        "is_red_flag": true,
        "score": 1.0,
        "matched_text": "hebat"
      },
      {
        "name_id": "Tidak bisa pipis sama sekali",
        "name": "Unable to urinate (blockage)",
        "body_system": "urinary",
        "is_red_flag": true,
        "score": 1.0,
        "matched_text": "sekali"
      },
      {
        "name_id": "Muntah",
        "name": "Vomiting",
        "body_system": "digestive",
        "is_red_flag": false,
        "score": 0.95,
        "matched_text": "muntah"
      },
      {
        "name_id": "Muntah hebat",
        "name": "Severe vomiting",
        "body_system": "digestive",
        "is_red_flag": true,
        "score": 0.95,
        "matched_text": "muntah hebat"
      },
      {
        "name_id": "Lemas",
        "name": "Lethargy",
        "body_system": "systemic",
        "is_red_flag": false,
        "score": 0.95,
        "matched_text": "lemas"
      },
      {
        "name_id": "Nafsu makan menurun",
        "name": "Poor appetite",
        "body_system": "digestive",
        "is_red_flag": false,
        "score": 0.8,
        "matched_text": "tidak mau makan"
      },
      {
        "name_id": "Kencing berdarah",
        "name": "Blood in urine",
        "body_system": "urinary",
        "is_red_flag": false,
        "score": 0.8,
        "matched_text": "berdarah"
      },
      {
        "name_id": "Bulu kusam & lemas",
        "name": "Poor coat / lethargy",
        "body_system": "systemic",
        "is_red_flag": false,
        "score": 0.8,
        "matched_text": "lemas"
      }
    ],
    "channel": "chat",
    "created_at": "2026-06-19T13:00:57.227145Z"
  },
  "suggestion": {
    "suggestion_type": "symptom_to_disease",
    "summary": "Berdasarkan 8 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 66%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
    "follow_up_questions": [
      "Sudah berapa lama gejala ini berlangsung?",
      "Apakah nafsu makan & minum berubah?",
      "Apakah ada perubahan pada urin/feses?",
      "Adakah riwayat vaksinasi & pengobatan terakhir?"
    ],
    "suggested_diseases": [
      {
        "disease_slug": "cat-fpv-panleukopenia",
        "name_id": "Panleukopenia (Distemper Kucing)",
        "confidence": 0.657,
        "rationale": "Cocok dengan gejala: Muntah hebat, Diare hebat",
        "is_emergency": true,
        "source": "ml+knowledge_base"
      },
      {
        "disease_slug": "cat-flutd",
        "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
        "confidence": 0.4408,
        "rationale": "Cocok dengan gejala: Kencing berdarah, Tidak bisa pipis sama sekali",
        "is_emergency": true,
        "source": "ml+knowledge_base"
      },
      {
        "disease_slug": "cat-ckd",
        "name_id": "Penyakit Ginjal Kronis (CKD)",
        "confidence": 0.524,
        "rationale": "Cocok dengan gejala: Nafsu makan menurun, Muntah, Bulu kusam & lemas",
        "is_emergency": false,
        "source": "ml+knowledge_base"
      },
      {
        "disease_slug": "cat-hcm",
        "name_id": "Kardiomiopati Hipertrofik (HCM)",
        "confidence": 0.1552,
        "rationale": "Cocok dengan gejala: Lemas",
        "is_emergency": false,
        "source": "ml+knowledge_base"
      },
      {
        "disease_slug": "cat-dermatophytosis-ringworm",
        "name_id": "Ringworm (Jamur Kulit)",
        "confidence": 0.042,
        "rationale": null,
        "is_emergency": false,
        "source": "ml"
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
      },
      {
        "name": "SNAP parvo (cross-reaktif FPV)",
        "type": "serology",
        "step_order": 1,
        "is_gold_standard": false,
        "expected_finding": "Antigen positif pada feses",
        "for_disease": "cat-fpv-panleukopenia"
      },
      {
        "name": "CBC",
        "type": "blood_test",
        "step_order": 3,
        "is_gold_standard": false,
        "expected_finding": "Panleukopenia (semua sel darah putih turun)",
        "for_disease": "cat-fpv-panleukopenia"
      },
      {
        "name": "Urinalisis + sedimen",
        "type": "urinalysis",
        "step_order": 2,
        "is_gold_standard": true,
        "expected_finding": "Kristal struvit/oksalat, darah, pH",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Palpasi kandung kemih",
        "type": "physical_exam",
        "step_order": 1,
        "is_gold_standard": false,
        "expected_finding": "Kandung kemih besar & keras (obstruksi)",
        "for_disease": "cat-flutd"
      },
      {
        "name": "USG / Radiografi",
        "type": "imaging_ultrasound",
        "step_order": 3,
        "is_gold_standard": false,
        "expected_finding": "Batu/urolith, dinding menebal",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Panel ginjal + elektrolit",
        "type": "blood_test",
        "step_order": 4,
        "is_gold_standard": false,
        "expected_finding": "Hiperkalemia & azotemia bila obstruksi",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Panel ginjal (BUN, Creatinine, SDMA)",
        "type": "blood_test",
        "step_order": 1,
        "is_gold_standard": true,
        "expected_finding": "SDMA & kreatinin meningkat",
        "for_disease": "cat-ckd"
      },
      {
        "name": "Urinalisis (USG, UPC)",
        "type": "urinalysis",
        "step_order": 2,
        "is_gold_standard": false,
        "expected_finding": "Urin encer (isostenuria), proteinuria",
        "for_disease": "cat-ckd"
      },
      {
        "name": "Tekanan darah",
        "type": "physical_exam",
        "step_order": 3,
        "is_gold_standard": false,
        "expected_finding": "Hipertensi sistemik",
        "for_disease": "cat-ckd"
      },
      {
        "name": "USG ginjal",
        "type": "imaging_ultrasound",
        "step_order": 4,
        "is_gold_standard": false,
        "expected_finding": "Ginjal mengecil/irregular atau kista (PKD)",
        "for_disease": "cat-ckd"
      },
      {
        "name": "Ekokardiografi",
        "type": "imaging_ultrasound",
        "step_order": 1,
        "is_gold_standard": true,
        "expected_finding": "Hipertrofi dinding ventrikel kiri >6mm",
        "for_disease": "cat-hcm"
      },
      {
        "name": "NT-proBNP test",
        "type": "blood_test",
        "step_order": 2,
        "is_gold_standard": false,
        "expected_finding": "Meningkat (skrining)",
        "for_disease": "cat-hcm"
      },
      {
        "name": "Radiografi toraks",
        "type": "imaging_xray",
        "step_order": 3,
        "is_gold_standard": false,
        "expected_finding": "Edema paru/efusi bila gagal jantung",
        "for_disease": "cat-hcm"
      },
      {
        "name": "Tekanan darah & T4",
        "type": "blood_test",
        "step_order": 4,
        "is_gold_standard": false,
        "expected_finding": "Singkirkan hipertiroid/hipertensi",
        "for_disease": "cat-hcm"
      },
      {
        "name": "Kultur jamur (DTM) / PCR",
        "type": "culture_sensitivity",
        "step_order": 3,
        "is_gold_standard": true,
        "expected_finding": "Pertumbuhan dermatofit",
        "for_disease": "cat-dermatophytosis-ringworm"
      },
      {
        "name": "Lampu Wood",
        "type": "physical_exam",
        "step_order": 1,
        "is_gold_standard": false,
        "expected_finding": "Fluoresensi hijau apel (M. canis sebagian)",
        "for_disease": "cat-dermatophytosis-ringworm"
      },
      {
        "name": "Trichogram (mikroskop bulu)",
        "type": "cytology",
        "step_order": 2,
        "is_gold_standard": false,
        "expected_finding": "Artrospora pada batang rambut",
        "for_disease": "cat-dermatophytosis-ringworm"
      }
    ],
    "suggested_treatments": [
      {
        "name": "Terapi suportif panleukopenia",
        "type": "supportive_care",
        "line_of_therapy": 1,
        "procedure_steps": "1) Isolasi & barrier nursing. 2) Cairan IV + elektrolit + glukosa. 3) Antiemetik. 4) Antibiotik cegah sepsis. 5) Nutrisi dini. 6) Monitor jumlah sel darah.",
        "recommendation": "Tidak ada antivirus spesifik; suportif agresif menentukan survival.",
        "for_disease": "cat-fpv-panleukopenia"
      },
      {
        "name": "Penanganan obstruksi uretra (darurat)",
        "type": "supportive_care",
        "line_of_therapy": 1,
        "procedure_steps": "1) Stabilkan: cairan IV, koreksi hiperkalemia. 2) Sedasi + pasang kateter uretra untuk dekompresi. 3) Bilas kandung kemih. 4) Rawat inap, pantau elektrolit & produksi urin. 5) Analgesik.",
        "recommendation": "Obstruksi = DARURAT; hiperkalemia bisa henti jantung. Segera ke klinik.",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Manajemen FIC non-obstruktif",
        "type": "dietary",
        "line_of_therapy": 1,
        "procedure_steps": "1) Diet urinary (lar­ut struvit / kontrol mineral). 2) Tingkatkan asupan air (makanan basah, fountain). 3) Kurangi stres (pheromone, environmental enrichment). 4) Analgesik jangka pendek.",
        "recommendation": "Fokus hidrasi & manajemen stres untuk cegah kekambuhan.",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Manajemen CKD bertahap (IRIS)",
        "type": "dietary",
        "line_of_therapy": 1,
        "procedure_steps": "1) Diet renal (protein berkualitas terbatas, fosfor rendah). 2) Phosphate binder bila perlu. 3) Kontrol tekanan darah. 4) Terapi cairan subkutan di rumah. 5) Atasi mual & anemia. 6) Monitor berkala.",
        "recommendation": "Diet renal adalah intervensi paling berdampak; mulai sedini mungkin & pantau tiap 3-6 bulan.",
        "for_disease": "cat-ckd"
      },
      {
        "name": "Manajemen HCM & gagal jantung",
        "type": "pharmacological",
        "line_of_therapy": 1,
        "procedure_steps": "1) Diuretik bila kongesti paru. 2) Pengelolaan ritme/beta-blocker bila indikasi. 3) Antitrombotik cegah ATE. 4) Batasi stres & aktivitas berat. 5) Monitor ekokardiografi berkala.",
        "recommendation": "Cegah pembekuan (ATE) pada atrium kiri membesar; tangani edema paru sebagai darurat.",
        "for_disease": "cat-hcm"
      },
      {
        "name": "Antijamur topikal + sistemik",
        "type": "pharmacological",
        "line_of_therapy": 1,
        "procedure_steps": "1) Antijamur topikal (lime sulfur/miconazole) seluruh tubuh. 2) Antijamur sistemik (itraconazole) untuk kasus luas. 3) Dekontaminasi lingkungan rutin. 4) Recheck dengan kultur sampai negatif 2x.",
        "recommendation": "Tangani semua hewan kontak + lingkungan; gunakan sarung tangan (zoonosis).",
        "for_disease": "cat-dermatophytosis-ringworm"
      }
    ],
    "suggested_products": [
      {
        "name": "Cairan IV + elektrolit",
        "kind": "medication",
        "active_ingredient": "Ringer Lactate + KCl",
        "route": "IV",
        "dosage_guide": "Koreksi defisit + maintenance",
        "cautions": "Pantau kalium.",
        "safety_flag": null
      },
      {
        "name": "Maropitant",
        "kind": "medication",
        "active_ingredient": "Maropitant",
        "route": "SC",
        "dosage_guide": "1 mg/kg SID",
        "cautions": "Antiemetik.",
        "safety_flag": null
      },
      {
        "name": "Antibiotik beta-lactam",
        "kind": "medication",
        "active_ingredient": "Ampicillin",
        "route": "IV",
        "dosage_guide": "20 mg/kg q8h",
        "cautions": "Cegah translokasi bakteri.",
        "safety_flag": null
      },
      {
        "name": "Cairan IV (NaCl 0.9%)",
        "kind": "medication",
        "active_ingredient": "Saline",
        "route": "IV",
        "dosage_guide": "Koreksi dehidrasi + diuresis",
        "cautions": "Pantau status jantung.",
        "safety_flag": null
      },
      {
        "name": "Calcium gluconate",
        "kind": "medication",
        "active_ingredient": "Calcium gluconate",
        "route": "IV",
        "dosage_guide": "Proteksi jantung saat hiperkalemia",
        "cautions": "Monitor EKG.",
        "safety_flag": null
      },
      {
        "name": "Buprenorphine",
        "kind": "medication",
        "active_ingredient": "Buprenorphine",
        "route": "oral transmucosal/IV",
        "dosage_guide": "0.02 mg/kg",
        "cautions": "Analgesik aman kucing.",
        "safety_flag": null
      },
      {
        "name": "Diet resep urinary (s/o)",
        "kind": "food_prescription",
        "active_ingredient": "Diet kontrol mineral/pH",
        "route": "oral",
        "dosage_guide": "Sesuai kebutuhan kalori",
        "cautions": "Diet jangka panjang sesuai tipe kristal.",
        "safety_flag": null
      },
      {
        "name": "Feliway (feline pheromone)",
        "kind": "supplement",
        "active_ingredient": "Synthetic pheromone",
        "route": "lingkungan",
        "dosage_guide": "Diffuser ruangan",
        "cautions": "Pendukung, bukan obat.",
        "safety_flag": null
      },
      {
        "name": "Diet resep renal",
        "kind": "food_prescription",
        "active_ingredient": "Diet rendah fosfor & protein terkontrol",
        "route": "oral",
        "dosage_guide": "Sesuai kalori",
        "cautions": "Transisi bertahap agar mau makan.",
        "safety_flag": null
      },
      {
        "name": "Telmisartan / Amlodipine",
        "kind": "medication",
        "active_ingredient": "Telmisartan (proteinuria) / Amlodipine (hipertensi)",
        "route": "oral",
        "dosage_guide": "Sesuai resep & tekanan darah",
        "cautions": "Pantau tekanan darah & ginjal.",
        "safety_flag": null
      },
      {
        "name": "Phosphate binder",
        "kind": "supplement",
        "active_ingredient": "Aluminium hidroksida / chitosan",
        "route": "oral (dengan makan)",
        "dosage_guide": "Sesuai kadar fosfat",
        "cautions": "Diberikan bersama makanan.",
        "safety_flag": null
      },
      {
        "name": "Maropitant / Mirtazapine",
        "kind": "medication",
        "active_ingredient": "Maropitant (mual), Mirtazapine (perangsang nafsu makan)",
        "route": "oral/SC",
        "dosage_guide": "Sesuai BB",
        "cautions": "Mirtazapine dosis kecil pada kucing.",
        "safety_flag": null
      },
      {
        "name": "Furosemide",
        "kind": "medication",
        "active_ingredient": "Furosemide",
        "route": "oral/IV",
        "dosage_guide": "Sesuai derajat kongesti",
        "cautions": "Pantau ginjal & elektrolit.",
        "safety_flag": null
      },
      {
        "name": "Clopidogrel",
        "kind": "medication",
        "active_ingredient": "Clopidogrel",
        "route": "oral",
        "dosage_guide": "18.75 mg/kucing SID",
        "cautions": "Antiplatelet cegah tromboemboli.",
        "safety_flag": null
      },
      {
        "name": "Atenolol",
        "kind": "medication",
        "active_ingredient": "Atenolol",
        "route": "oral",
        "dosage_guide": "Sesuai resep",
        "cautions": "Hati-hati bila gagal jantung dekompensasi.",
        "safety_flag": null
      },
      {
        "name": "Pimobendan (kasus tertentu)",
        "kind": "medication",
        "active_ingredient": "Pimobendan",
        "route": "oral",
        "dosage_guide": "Sesuai resep kardiolog",
        "cautions": "Tidak rutin untuk HCM obstruktif.",
        "safety_flag": null
      },
      {
        "name": "Itraconazole",
        "kind": "medication",
        "active_ingredient": "Itraconazole",
        "route": "oral",
        "dosage_guide": "5 mg/kg SID (pulse 1 minggu on/off)",
        "cautions": "Monitor hati.",
        "safety_flag": null
      },
      {
        "name": "Lime sulfur dip",
        "kind": "medication",
        "active_ingredient": "Sulfurated lime",
        "route": "topikal",
        "dosage_guide": "2x/minggu",
        "cautions": "Bau menyengat, hindari mata.",
        "safety_flag": null
      },
      {
        "name": "Miconazole/chlorhexidine shampoo",
        "kind": "grooming",
        "active_ingredient": "Miconazole + chlorhexidine",
        "route": "topikal",
        "dosage_guide": "2x/minggu",
        "cautions": "Bilas bersih.",
        "safety_flag": null
      }
    ],
    "red_flags": [
      "Tidak bisa pipis sama sekali",
      "Muntah hebat",
      "Diare hebat"
    ],
    "safety_warnings": [
      "Data edukatif. Diagnosa & resep final wajib oleh dokter hewan. PERHATIAN: kucing sangat sensitif terhadap banyak obat (paracetamol, permethrin, NSAID dosis anjing = FATAL).",
      "Cairan IV + elektrolit: Pantau kalium.",
      "Maropitant: Antiemetik.",
      "Antibiotik beta-lactam: Cegah translokasi bakteri.",
      "Cairan IV (NaCl 0.9%): Pantau status jantung.",
      "Calcium gluconate: Monitor EKG.",
      "Buprenorphine: Analgesik aman kucing.",
      "Diet resep urinary (s/o): Diet jangka panjang sesuai tipe kristal.",
      "Feliway (feline pheromone): Pendukung, bukan obat.",
      "Diet resep renal: Transisi bertahap agar mau makan.",
      "Telmisartan / Amlodipine: Pantau tekanan darah & ginjal.",
      "Phosphate binder: Diberikan bersama makanan.",
      "Maropitant / Mirtazapine: Mirtazapine dosis kecil pada kucing.",
      "Furosemide: Pantau ginjal & elektrolit.",
      "Clopidogrel: Antiplatelet cegah tromboemboli.",
      "Atenolol: Hati-hati bila gagal jantung dekompensasi.",
      "Pimobendan (kasus tertentu): Tidak rutin untuk HCM obstruktif.",
      "Itraconazole: Monitor hati.",
      "Lime sulfur dip: Bau menyengat, hindari mata.",
      "Miconazole/chlorhexidine shampoo: Bilas bersih.",
      "paracetamol: FATAL untuk kucing (methemoglobinemia). Jangan diberikan.",
      "acetaminophen: FATAL untuk kucing. Jangan diberikan.",
      "permethrin: Sangat toksik untuk kucing (produk anjing). Bisa fatal.",
      "ibuprofen: Toksik; margin keamanan NSAID sangat sempit pada kucing.",
      "aspirin: Metabolisme lambat; hanya dosis sangat hati-hati oleh vet."
    ],
    "references": [
      {
        "type": "disease",
        "slug": "cat-fpv-panleukopenia",
        "name_id": "Panleukopenia (Distemper Kucing)",
        "overview": "Parvovirus kucing menyerang sumsum tulang & usus; sangat fatal pada anak kucing."
      },
      {
        "type": "disease",
        "slug": "cat-flutd",
        "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
        "overview": "Kumpulan kondisi saluran kemih bawah; sumbatan uretra pada jantan adalah DARURAT mematikan."
      },
      {
        "type": "disease",
        "slug": "cat-ckd",
        "name_id": "Penyakit Ginjal Kronis (CKD)",
        "overview": "Penurunan fungsi ginjal progresif, sangat umum pada kucing senior."
      },
      {
        "type": "disease",
        "slug": "cat-hcm",
        "name_id": "Kardiomiopati Hipertrofik (HCM)",
        "overview": "Penebalan otot ventrikel kiri, penyakit jantung paling umum pada kucing; risiko gagal jantung & tromboemboli."
      },
      {
        "type": "disease",
        "slug": "cat-dermatophytosis-ringworm",
        "name_id": "Ringworm (Jamur Kulit)",
        "overview": "Infeksi jamur dermatofita pada kulit/bulu; menular ke hewan lain & manusia."
      }
    ],
    "is_emergency": true,
    "generated_by": "rule_based",
    "disclaimer": "Saran AI bersifat pendukung keputusan klinis dan TIDAK menggantikan pemeriksaan langsung serta penilaian dokter hewan berlisensi. Dosis & produk wajib diverifikasi sesuai spesies, berat badan, dan kondisi pasien.",
    "created_at": "2026-06-19T13:00:57.241551Z"
  },
  "suggestion_id": "adf95d3a29b9450fb6c390ba301f71b9",
  "suggestion_ref": "adf95d3a29b9450fb6c390ba301f71b9",
  "entities": {
    "consultation_id": "ext-20250619-001",
    "external_consultation_id": "ext-20250619-001",
    "org_id": null,
    "vet_id": 1,
    "owner_id": 100,
    "customer_id": 100,
    "pet_id": 200,
    "case_id": null,
    "external_refs": {}
  }
}

```

---

### Get Consultation

**GET /consultations/ext-20250619-001**

**Response:**

```json

{
  "consultation_id": "ext-20250619-001",
  "entities": {
    "consultation_id": "ext-20250619-001",
    "external_consultation_id": "ext-20250619-001",
    "org_id": null,
    "vet_id": 1,
    "owner_id": 100,
    "customer_id": 100,
    "pet_id": 200,
    "case_id": null,
    "external_refs": {}
  },
  "conversation": {
    "consultation_id": "ext-20250619-001",
    "org_id": null,
    "user_id": 1,
    "vet_id": 1,
    "owner_id": 100,
    "customer_id": 100,
    "pet_id": 200,
    "case_id": null,
    "external_consultation_id": "ext-20250619-001",
    "external_refs": {},
    "title": "Konsultasi ext-2025",
    "context": {
      "org_id": null,
      "user_id": 1,
      "vet_id": 1,
      "doctor_id": 1,
      "owner_id": 100,
      "customer_id": 100,
      "pet_id": 200,
      "case_id": null,
      "external_consultation_id": "ext-20250619-001",
      "external_refs": {},
      "category_slug": "cat",
      "breed_slug": "cat-persian",
      "age_years": 3.0,
      "weight_kg": null,
      "sex": null,
      "is_neutered": null,
      "temperature_c": null,
      "heart_rate": null,
      "resp_rate": null
    },
    "id": "6bcf507edea64d3d9212248fa4ddb3a0",
    "created_at": "2026-06-19T13:00:57.220106+00:00"
  },
  "context": {
    "org_id": null,
    "user_id": 1,
    "vet_id": 1,
    "doctor_id": 1,
    "owner_id": 100,
    "customer_id": 100,
    "pet_id": 200,
    "case_id": null,
    "external_consultation_id": "ext-20250619-001",
    "external_refs": {},
    "category_slug": "cat",
    "breed_slug": "cat-persian",
    "age_years": 3.0,
    "weight_kg": null,
    "sex": null,
    "is_neutered": null,
    "temperature_c": null,
    "heart_rate": null,
    "resp_rate": null
  },
  "suggestion_count": 2,
  "symptoms": [
    {
      "name_id": "Diare hebat",
      "name": "Profuse diarrhea",
      "body_system": "digestive",
      "is_red_flag": true,
      "score": 1.0,
      "matched_text": "hebat"
    },
    {
      "name_id": "Muntah",
      "name": "Vomiting",
      "body_system": "digestive",
      "is_red_flag": false,
      "score": 0.95,
      "matched_text": "muntah"
    },
    {
      "name_id": "Muntah hebat",
      "name": "Severe vomiting",
      "body_system": "digestive",
      "is_red_flag": true,
      "score": 0.95,
      "matched_text": "muntah hebat"
    },
    {
      "name_id": "Nafsu makan menurun",
      "name": "Poor appetite",
      "body_system": "digestive",
      "is_red_flag": false,
      "score": 0.8,
      "matched_text": "tidak mau makan"
    },
    {
      "name_id": "Tidak bisa pipis sama sekali",
      "name": "Unable to urinate (blockage)",
      "body_system": "urinary",
      "is_red_flag": true,
      "score": 1.0,
      "matched_text": "sekali"
    },
    {
      "name_id": "Lemas",
      "name": "Lethargy",
      "body_system": "systemic",
      "is_red_flag": false,
      "score": 0.95,
      "matched_text": "lemas"
    },
    {
      "name_id": "Kencing berdarah",
      "name": "Blood in urine",
      "body_system": "urinary",
      "is_red_flag": false,
      "score": 0.8,
      "matched_text": "berdarah"
    },
    {
      "name_id": "Bulu kusam & lemas",
      "name": "Poor coat / lethargy",
      "body_system": "systemic",
      "is_red_flag": false,
      "score": 0.8,
      "matched_text": "lemas"
    }
  ],
  "suggestions": [
    {
      "consultation_id": "ext-20250619-001",
      "request_id": null,
      "case_id": null,
      "pet_id": 200,
      "suggestion_type": "symptom_to_disease",
      "summary": "Berdasarkan 8 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 66%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
      "is_emergency": true,
      "is_reviewed": false,
      "generated_by": "rule_based",
      "payload": {
        "suggestion_type": "symptom_to_disease",
        "summary": "Berdasarkan 8 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 66%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
        "follow_up_questions": [
          "Sudah berapa lama gejala ini berlangsung?",
          "Apakah nafsu makan & minum berubah?",
          "Apakah ada perubahan pada urin/feses?",
          "Adakah riwayat vaksinasi & pengobatan terakhir?"
        ],
        "suggested_diseases": [
          {
            "disease_slug": "cat-fpv-panleukopenia",
            "name_id": "Panleukopenia (Distemper Kucing)",
            "confidence": 0.657,
            "rationale": "Cocok dengan gejala: Muntah hebat, Diare hebat",
            "is_emergency": true,
            "source": "ml+knowledge_base"
          },
          {
            "disease_slug": "cat-flutd",
            "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
            "confidence": 0.4408,
            "rationale": "Cocok dengan gejala: Kencing berdarah, Tidak bisa pipis sama sekali",
            "is_emergency": true,
            "source": "ml+knowledge_base"
          },
          {
            "disease_slug": "cat-ckd",
            "name_id": "Penyakit Ginjal Kronis (CKD)",
            "confidence": 0.524,
            "rationale": "Cocok dengan gejala: Nafsu makan menurun, Muntah, Bulu kusam & lemas",
            "is_emergency": false,
            "source": "ml+knowledge_base"
          },
          {
            "disease_slug": "cat-hcm",
            "name_id": "Kardiomiopati Hipertrofik (HCM)",
            "confidence": 0.1552,
            "rationale": "Cocok dengan gejala: Lemas",
            "is_emergency": false,
            "source": "ml+knowledge_base"
          },
          {
            "disease_slug": "cat-dermatophytosis-ringworm",
            "name_id": "Ringworm (Jamur Kulit)",
            "confidence": 0.042,
            "rationale": null,
            "is_emergency": false,
            "source": "ml"
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
          },
          {
            "name": "SNAP parvo (cross-reaktif FPV)",
            "type": "serology",
            "step_order": 1,
            "is_gold_standard": false,
            "expected_finding": "Antigen positif pada feses",
            "for_disease": "cat-fpv-panleukopenia"
          },
          {
            "name": "CBC",
            "type": "blood_test",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Panleukopenia (semua sel darah putih turun)",
            "for_disease": "cat-fpv-panleukopenia"
          },
          {
            "name": "Urinalisis + sedimen",
            "type": "urinalysis",
            "step_order": 2,
            "is_gold_standard": true,
            "expected_finding": "Kristal struvit/oksalat, darah, pH",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Palpasi kandung kemih",
            "type": "physical_exam",
            "step_order": 1,
            "is_gold_standard": false,
            "expected_finding": "Kandung kemih besar & keras (obstruksi)",
            "for_disease": "cat-flutd"
          },
          {
            "name": "USG / Radiografi",
            "type": "imaging_ultrasound",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Batu/urolith, dinding menebal",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Panel ginjal + elektrolit",
            "type": "blood_test",
            "step_order": 4,
            "is_gold_standard": false,
            "expected_finding": "Hiperkalemia & azotemia bila obstruksi",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Panel ginjal (BUN, Creatinine, SDMA)",
            "type": "blood_test",
            "step_order": 1,
            "is_gold_standard": true,
            "expected_finding": "SDMA & kreatinin meningkat",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Urinalisis (USG, UPC)",
            "type": "urinalysis",
            "step_order": 2,
            "is_gold_standard": false,
            "expected_finding": "Urin encer (isostenuria), proteinuria",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Tekanan darah",
            "type": "physical_exam",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Hipertensi sistemik",
            "for_disease": "cat-ckd"
          },
          {
            "name": "USG ginjal",
            "type": "imaging_ultrasound",
            "step_order": 4,
            "is_gold_standard": false,
            "expected_finding": "Ginjal mengecil/irregular atau kista (PKD)",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Ekokardiografi",
            "type": "imaging_ultrasound",
            "step_order": 1,
            "is_gold_standard": true,
            "expected_finding": "Hipertrofi dinding ventrikel kiri >6mm",
            "for_disease": "cat-hcm"
          },
          {
            "name": "NT-proBNP test",
            "type": "blood_test",
            "step_order": 2,
            "is_gold_standard": false,
            "expected_finding": "Meningkat (skrining)",
            "for_disease": "cat-hcm"
          },
          {
            "name": "Radiografi toraks",
            "type": "imaging_xray",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Edema paru/efusi bila gagal jantung",
            "for_disease": "cat-hcm"
          },
          {
            "name": "Tekanan darah & T4",
            "type": "blood_test",
            "step_order": 4,
            "is_gold_standard": false,
            "expected_finding": "Singkirkan hipertiroid/hipertensi",
            "for_disease": "cat-hcm"
          },
          {
            "name": "Kultur jamur (DTM) / PCR",
            "type": "culture_sensitivity",
            "step_order": 3,
            "is_gold_standard": true,
            "expected_finding": "Pertumbuhan dermatofit",
            "for_disease": "cat-dermatophytosis-ringworm"
          },
          {
            "name": "Lampu Wood",
            "type": "physical_exam",
            "step_order": 1,
            "is_gold_standard": false,
            "expected_finding": "Fluoresensi hijau apel (M. canis sebagian)",
            "for_disease": "cat-dermatophytosis-ringworm"
          },
          {
            "name": "Trichogram (mikroskop bulu)",
            "type": "cytology",
            "step_order": 2,
            "is_gold_standard": false,
            "expected_finding": "Artrospora pada batang rambut",
            "for_disease": "cat-dermatophytosis-ringworm"
          }
        ],
        "suggested_treatments": [
          {
            "name": "Terapi suportif panleukopenia",
            "type": "supportive_care",
            "line_of_therapy": 1,
            "procedure_steps": "1) Isolasi & barrier nursing. 2) Cairan IV + elektrolit + glukosa. 3) Antiemetik. 4) Antibiotik cegah sepsis. 5) Nutrisi dini. 6) Monitor jumlah sel darah.",
            "recommendation": "Tidak ada antivirus spesifik; suportif agresif menentukan survival.",
            "for_disease": "cat-fpv-panleukopenia"
          },
          {
            "name": "Penanganan obstruksi uretra (darurat)",
            "type": "supportive_care",
            "line_of_therapy": 1,
            "procedure_steps": "1) Stabilkan: cairan IV, koreksi hiperkalemia. 2) Sedasi + pasang kateter uretra untuk dekompresi. 3) Bilas kandung kemih. 4) Rawat inap, pantau elektrolit & produksi urin. 5) Analgesik.",
            "recommendation": "Obstruksi = DARURAT; hiperkalemia bisa henti jantung. Segera ke klinik.",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Manajemen FIC non-obstruktif",
            "type": "dietary",
            "line_of_therapy": 1,
            "procedure_steps": "1) Diet urinary (lar­ut struvit / kontrol mineral). 2) Tingkatkan asupan air (makanan basah, fountain). 3) Kurangi stres (pheromone, environmental enrichment). 4) Analgesik jangka pendek.",
            "recommendation": "Fokus hidrasi & manajemen stres untuk cegah kekambuhan.",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Manajemen CKD bertahap (IRIS)",
            "type": "dietary",
            "line_of_therapy": 1,
            "procedure_steps": "1) Diet renal (protein berkualitas terbatas, fosfor rendah). 2) Phosphate binder bila perlu. 3) Kontrol tekanan darah. 4) Terapi cairan subkutan di rumah. 5) Atasi mual & anemia. 6) Monitor berkala.",
            "recommendation": "Diet renal adalah intervensi paling berdampak; mulai sedini mungkin & pantau tiap 3-6 bulan.",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Manajemen HCM & gagal jantung",
            "type": "pharmacological",
            "line_of_therapy": 1,
            "procedure_steps": "1) Diuretik bila kongesti paru. 2) Pengelolaan ritme/beta-blocker bila indikasi. 3) Antitrombotik cegah ATE. 4) Batasi stres & aktivitas berat. 5) Monitor ekokardiografi berkala.",
            "recommendation": "Cegah pembekuan (ATE) pada atrium kiri membesar; tangani edema paru sebagai darurat.",
            "for_disease": "cat-hcm"
          },
          {
            "name": "Antijamur topikal + sistemik",
            "type": "pharmacological",
            "line_of_therapy": 1,
            "procedure_steps": "1) Antijamur topikal (lime sulfur/miconazole) seluruh tubuh. 2) Antijamur sistemik (itraconazole) untuk kasus luas. 3) Dekontaminasi lingkungan rutin. 4) Recheck dengan kultur sampai negatif 2x.",
            "recommendation": "Tangani semua hewan kontak + lingkungan; gunakan sarung tangan (zoonosis).",
            "for_disease": "cat-dermatophytosis-ringworm"
          }
        ],
        "suggested_products": [
          {
            "name": "Cairan IV + elektrolit",
            "kind": "medication",
            "active_ingredient": "Ringer Lactate + KCl",
            "route": "IV",
            "dosage_guide": "Koreksi defisit + maintenance",
            "cautions": "Pantau kalium.",
            "safety_flag": null
          },
          {
            "name": "Maropitant",
            "kind": "medication",
            "active_ingredient": "Maropitant",
            "route": "SC",
            "dosage_guide": "1 mg/kg SID",
            "cautions": "Antiemetik.",
            "safety_flag": null
          },
          {
            "name": "Antibiotik beta-lactam",
            "kind": "medication",
            "active_ingredient": "Ampicillin",
            "route": "IV",
            "dosage_guide": "20 mg/kg q8h",
            "cautions": "Cegah translokasi bakteri.",
            "safety_flag": null
          },
          {
            "name": "Cairan IV (NaCl 0.9%)",
            "kind": "medication",
            "active_ingredient": "Saline",
            "route": "IV",
            "dosage_guide": "Koreksi dehidrasi + diuresis",
            "cautions": "Pantau status jantung.",
            "safety_flag": null
          },
          {
            "name": "Calcium gluconate",
            "kind": "medication",
            "active_ingredient": "Calcium gluconate",
            "route": "IV",
            "dosage_guide": "Proteksi jantung saat hiperkalemia",
            "cautions": "Monitor EKG.",
            "safety_flag": null
          },
          {
            "name": "Buprenorphine",
            "kind": "medication",
            "active_ingredient": "Buprenorphine",
            "route": "oral transmucosal/IV",
            "dosage_guide": "0.02 mg/kg",
            "cautions": "Analgesik aman kucing.",
            "safety_flag": null
          },
          {
            "name": "Diet resep urinary (s/o)",
            "kind": "food_prescription",
            "active_ingredient": "Diet kontrol mineral/pH",
            "route": "oral",
            "dosage_guide": "Sesuai kebutuhan kalori",
            "cautions": "Diet jangka panjang sesuai tipe kristal.",
            "safety_flag": null
          },
          {
            "name": "Feliway (feline pheromone)",
            "kind": "supplement",
            "active_ingredient": "Synthetic pheromone",
            "route": "lingkungan",
            "dosage_guide": "Diffuser ruangan",
            "cautions": "Pendukung, bukan obat.",
            "safety_flag": null
          },
          {
            "name": "Diet resep renal",
            "kind": "food_prescription",
            "active_ingredient": "Diet rendah fosfor & protein terkontrol",
            "route": "oral",
            "dosage_guide": "Sesuai kalori",
            "cautions": "Transisi bertahap agar mau makan.",
            "safety_flag": null
          },
          {
            "name": "Telmisartan / Amlodipine",
            "kind": "medication",
            "active_ingredient": "Telmisartan (proteinuria) / Amlodipine (hipertensi)",
            "route": "oral",
            "dosage_guide": "Sesuai resep & tekanan darah",
            "cautions": "Pantau tekanan darah & ginjal.",
            "safety_flag": null
          },
          {
            "name": "Phosphate binder",
            "kind": "supplement",
            "active_ingredient": "Aluminium hidroksida / chitosan",
            "route": "oral (dengan makan)",
            "dosage_guide": "Sesuai kadar fosfat",
            "cautions": "Diberikan bersama makanan.",
            "safety_flag": null
          },
          {
            "name": "Maropitant / Mirtazapine",
            "kind": "medication",
            "active_ingredient": "Maropitant (mual), Mirtazapine (perangsang nafsu makan)",
            "route": "oral/SC",
            "dosage_guide": "Sesuai BB",
            "cautions": "Mirtazapine dosis kecil pada kucing.",
            "safety_flag": null
          },
          {
            "name": "Furosemide",
            "kind": "medication",
            "active_ingredient": "Furosemide",
            "route": "oral/IV",
            "dosage_guide": "Sesuai derajat kongesti",
            "cautions": "Pantau ginjal & elektrolit.",
            "safety_flag": null
          },
          {
            "name": "Clopidogrel",
            "kind": "medication",
            "active_ingredient": "Clopidogrel",
            "route": "oral",
            "dosage_guide": "18.75 mg/kucing SID",
            "cautions": "Antiplatelet cegah tromboemboli.",
            "safety_flag": null
          },
          {
            "name": "Atenolol",
            "kind": "medication",
            "active_ingredient": "Atenolol",
            "route": "oral",
            "dosage_guide": "Sesuai resep",
            "cautions": "Hati-hati bila gagal jantung dekompensasi.",
            "safety_flag": null
          },
          {
            "name": "Pimobendan (kasus tertentu)",
            "kind": "medication",
            "active_ingredient": "Pimobendan",
            "route": "oral",
            "dosage_guide": "Sesuai resep kardiolog",
            "cautions": "Tidak rutin untuk HCM obstruktif.",
            "safety_flag": null
          },
          {
            "name": "Itraconazole",
            "kind": "medication",
            "active_ingredient": "Itraconazole",
            "route": "oral",
            "dosage_guide": "5 mg/kg SID (pulse 1 minggu on/off)",
            "cautions": "Monitor hati.",
            "safety_flag": null
          },
          {
            "name": "Lime sulfur dip",
            "kind": "medication",
            "active_ingredient": "Sulfurated lime",
            "route": "topikal",
            "dosage_guide": "2x/minggu",
            "cautions": "Bau menyengat, hindari mata.",
            "safety_flag": null
          },
          {
            "name": "Miconazole/chlorhexidine shampoo",
            "kind": "grooming",
            "active_ingredient": "Miconazole + chlorhexidine",
            "route": "topikal",
            "dosage_guide": "2x/minggu",
            "cautions": "Bilas bersih.",
            "safety_flag": null
          }
        ],
        "red_flags": [
          "Tidak bisa pipis sama sekali",
          "Muntah hebat",
          "Diare hebat"
        ],
        "safety_warnings": [
          "Data edukatif. Diagnosa & resep final wajib oleh dokter hewan. PERHATIAN: kucing sangat sensitif terhadap banyak obat (paracetamol, permethrin, NSAID dosis anjing = FATAL).",
          "Cairan IV + elektrolit: Pantau kalium.",
          "Maropitant: Antiemetik.",
          "Antibiotik beta-lactam: Cegah translokasi bakteri.",
          "Cairan IV (NaCl 0.9%): Pantau status jantung.",
          "Calcium gluconate: Monitor EKG.",
          "Buprenorphine: Analgesik aman kucing.",
          "Diet resep urinary (s/o): Diet jangka panjang sesuai tipe kristal.",
          "Feliway (feline pheromone): Pendukung, bukan obat.",
          "Diet resep renal: Transisi bertahap agar mau makan.",
          "Telmisartan / Amlodipine: Pantau tekanan darah & ginjal.",
          "Phosphate binder: Diberikan bersama makanan.",
          "Maropitant / Mirtazapine: Mirtazapine dosis kecil pada kucing.",
          "Furosemide: Pantau ginjal & elektrolit.",
          "Clopidogrel: Antiplatelet cegah tromboemboli.",
          "Atenolol: Hati-hati bila gagal jantung dekompensasi.",
          "Pimobendan (kasus tertentu): Tidak rutin untuk HCM obstruktif.",
          "Itraconazole: Monitor hati.",
          "Lime sulfur dip: Bau menyengat, hindari mata.",
          "Miconazole/chlorhexidine shampoo: Bilas bersih.",
          "paracetamol: FATAL untuk kucing (methemoglobinemia). Jangan diberikan.",
          "acetaminophen: FATAL untuk kucing. Jangan diberikan.",
          "permethrin: Sangat toksik untuk kucing (produk anjing). Bisa fatal.",
          "ibuprofen: Toksik; margin keamanan NSAID sangat sempit pada kucing.",
          "aspirin: Metabolisme lambat; hanya dosis sangat hati-hati oleh vet."
        ],
        "references": [
          {
            "type": "disease",
            "slug": "cat-fpv-panleukopenia",
            "name_id": "Panleukopenia (Distemper Kucing)",
            "overview": "Parvovirus kucing menyerang sumsum tulang & usus; sangat fatal pada anak kucing."
          },
          {
            "type": "disease",
            "slug": "cat-flutd",
            "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
            "overview": "Kumpulan kondisi saluran kemih bawah; sumbatan uretra pada jantan adalah DARURAT mematikan."
          },
          {
            "type": "disease",
            "slug": "cat-ckd",
            "name_id": "Penyakit Ginjal Kronis (CKD)",
            "overview": "Penurunan fungsi ginjal progresif, sangat umum pada kucing senior."
          },
          {
            "type": "disease",
            "slug": "cat-hcm",
            "name_id": "Kardiomiopati Hipertrofik (HCM)",
            "overview": "Penebalan otot ventrikel kiri, penyakit jantung paling umum pada kucing; risiko gagal jantung & tromboemboli."
          },
          {
            "type": "disease",
            "slug": "cat-dermatophytosis-ringworm",
            "name_id": "Ringworm (Jamur Kulit)",
            "overview": "Infeksi jamur dermatofita pada kulit/bulu; menular ke hewan lain & manusia."
          }
        ],
        "is_emergency": true,
        "generated_by": "rule_based",
        "disclaimer": "Saran AI bersifat pendukung keputusan klinis dan TIDAK menggantikan pemeriksaan langsung serta penilaian dokter hewan berlisensi. Dosis & produk wajib diverifikasi sesuai spesies, berat badan, dan kondisi pasien.",
        "created_at": "2026-06-19T13:00:57.241551Z"
      },
      "id": "adf95d3a29b9450fb6c390ba301f71b9",
      "created_at": "2026-06-19T13:00:57.242858+00:00"
    },
    {
      "consultation_id": "ext-20250619-001",
      "request_id": null,
      "case_id": null,
      "pet_id": 200,
      "suggestion_type": "symptom_to_disease",
      "summary": "Berdasarkan 4 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 78%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
      "is_emergency": true,
      "is_reviewed": false,
      "generated_by": "rule_based",
      "payload": {
        "suggestion_type": "symptom_to_disease",
        "summary": "Berdasarkan 4 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 78%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
        "follow_up_questions": [
          "Sudah berapa lama gejala ini berlangsung?",
          "Apakah nafsu makan & minum berubah?",
          "Apakah ada perubahan pada urin/feses?",
          "Adakah riwayat vaksinasi & pengobatan terakhir?"
        ],
        "suggested_diseases": [
          {
            "disease_slug": "cat-fpv-panleukopenia",
            "name_id": "Panleukopenia (Distemper Kucing)",
            "confidence": 0.784,
            "rationale": "Cocok dengan gejala: Muntah hebat, Diare hebat",
            "is_emergency": true,
            "source": "ml+knowledge_base"
          },
          {
            "disease_slug": "cat-flutd",
            "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
            "confidence": 0.018,
            "rationale": null,
            "is_emergency": true,
            "source": "ml"
          },
          {
            "disease_slug": "cat-ckd",
            "name_id": "Penyakit Ginjal Kronis (CKD)",
            "confidence": 0.34,
            "rationale": "Cocok dengan gejala: Nafsu makan menurun, Muntah",
            "is_emergency": false,
            "source": "ml+knowledge_base"
          },
          {
            "disease_slug": "cat-dermatophytosis-ringworm",
            "name_id": "Ringworm (Jamur Kulit)",
            "confidence": 0.076,
            "rationale": null,
            "is_emergency": false,
            "source": "ml"
          },
          {
            "disease_slug": "cat-hcm",
            "name_id": "Kardiomiopati Hipertrofik (HCM)",
            "confidence": 0.042,
            "rationale": null,
            "is_emergency": false,
            "source": "ml"
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
          },
          {
            "name": "SNAP parvo (cross-reaktif FPV)",
            "type": "serology",
            "step_order": 1,
            "is_gold_standard": false,
            "expected_finding": "Antigen positif pada feses",
            "for_disease": "cat-fpv-panleukopenia"
          },
          {
            "name": "CBC",
            "type": "blood_test",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Panleukopenia (semua sel darah putih turun)",
            "for_disease": "cat-fpv-panleukopenia"
          },
          {
            "name": "Urinalisis + sedimen",
            "type": "urinalysis",
            "step_order": 2,
            "is_gold_standard": true,
            "expected_finding": "Kristal struvit/oksalat, darah, pH",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Palpasi kandung kemih",
            "type": "physical_exam",
            "step_order": 1,
            "is_gold_standard": false,
            "expected_finding": "Kandung kemih besar & keras (obstruksi)",
            "for_disease": "cat-flutd"
          },
          {
            "name": "USG / Radiografi",
            "type": "imaging_ultrasound",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Batu/urolith, dinding menebal",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Panel ginjal + elektrolit",
            "type": "blood_test",
            "step_order": 4,
            "is_gold_standard": false,
            "expected_finding": "Hiperkalemia & azotemia bila obstruksi",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Panel ginjal (BUN, Creatinine, SDMA)",
            "type": "blood_test",
            "step_order": 1,
            "is_gold_standard": true,
            "expected_finding": "SDMA & kreatinin meningkat",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Urinalisis (USG, UPC)",
            "type": "urinalysis",
            "step_order": 2,
            "is_gold_standard": false,
            "expected_finding": "Urin encer (isostenuria), proteinuria",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Tekanan darah",
            "type": "physical_exam",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Hipertensi sistemik",
            "for_disease": "cat-ckd"
          },
          {
            "name": "USG ginjal",
            "type": "imaging_ultrasound",
            "step_order": 4,
            "is_gold_standard": false,
            "expected_finding": "Ginjal mengecil/irregular atau kista (PKD)",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Kultur jamur (DTM) / PCR",
            "type": "culture_sensitivity",
            "step_order": 3,
            "is_gold_standard": true,
            "expected_finding": "Pertumbuhan dermatofit",
            "for_disease": "cat-dermatophytosis-ringworm"
          },
          {
            "name": "Lampu Wood",
            "type": "physical_exam",
            "step_order": 1,
            "is_gold_standard": false,
            "expected_finding": "Fluoresensi hijau apel (M. canis sebagian)",
            "for_disease": "cat-dermatophytosis-ringworm"
          },
          {
            "name": "Trichogram (mikroskop bulu)",
            "type": "cytology",
            "step_order": 2,
            "is_gold_standard": false,
            "expected_finding": "Artrospora pada batang rambut",
            "for_disease": "cat-dermatophytosis-ringworm"
          },
          {
            "name": "Ekokardiografi",
            "type": "imaging_ultrasound",
            "step_order": 1,
            "is_gold_standard": true,
            "expected_finding": "Hipertrofi dinding ventrikel kiri >6mm",
            "for_disease": "cat-hcm"
          },
          {
            "name": "NT-proBNP test",
            "type": "blood_test",
            "step_order": 2,
            "is_gold_standard": false,
            "expected_finding": "Meningkat (skrining)",
            "for_disease": "cat-hcm"
          },
          {
            "name": "Radiografi toraks",
            "type": "imaging_xray",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Edema paru/efusi bila gagal jantung",
            "for_disease": "cat-hcm"
          },
          {
            "name": "Tekanan darah & T4",
            "type": "blood_test",
            "step_order": 4,
            "is_gold_standard": false,
            "expected_finding": "Singkirkan hipertiroid/hipertensi",
            "for_disease": "cat-hcm"
          }
        ],
        "suggested_treatments": [
          {
            "name": "Terapi suportif panleukopenia",
            "type": "supportive_care",
            "line_of_therapy": 1,
            "procedure_steps": "1) Isolasi & barrier nursing. 2) Cairan IV + elektrolit + glukosa. 3) Antiemetik. 4) Antibiotik cegah sepsis. 5) Nutrisi dini. 6) Monitor jumlah sel darah.",
            "recommendation": "Tidak ada antivirus spesifik; suportif agresif menentukan survival.",
            "for_disease": "cat-fpv-panleukopenia"
          },
          {
            "name": "Penanganan obstruksi uretra (darurat)",
            "type": "supportive_care",
            "line_of_therapy": 1,
            "procedure_steps": "1) Stabilkan: cairan IV, koreksi hiperkalemia. 2) Sedasi + pasang kateter uretra untuk dekompresi. 3) Bilas kandung kemih. 4) Rawat inap, pantau elektrolit & produksi urin. 5) Analgesik.",
            "recommendation": "Obstruksi = DARURAT; hiperkalemia bisa henti jantung. Segera ke klinik.",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Manajemen FIC non-obstruktif",
            "type": "dietary",
            "line_of_therapy": 1,
            "procedure_steps": "1) Diet urinary (lar­ut struvit / kontrol mineral). 2) Tingkatkan asupan air (makanan basah, fountain). 3) Kurangi stres (pheromone, environmental enrichment). 4) Analgesik jangka pendek.",
            "recommendation": "Fokus hidrasi & manajemen stres untuk cegah kekambuhan.",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Manajemen CKD bertahap (IRIS)",
            "type": "dietary",
            "line_of_therapy": 1,
            "procedure_steps": "1) Diet renal (protein berkualitas terbatas, fosfor rendah). 2) Phosphate binder bila perlu. 3) Kontrol tekanan darah. 4) Terapi cairan subkutan di rumah. 5) Atasi mual & anemia. 6) Monitor berkala.",
            "recommendation": "Diet renal adalah intervensi paling berdampak; mulai sedini mungkin & pantau tiap 3-6 bulan.",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Antijamur topikal + sistemik",
            "type": "pharmacological",
            "line_of_therapy": 1,
            "procedure_steps": "1) Antijamur topikal (lime sulfur/miconazole) seluruh tubuh. 2) Antijamur sistemik (itraconazole) untuk kasus luas. 3) Dekontaminasi lingkungan rutin. 4) Recheck dengan kultur sampai negatif 2x.",
            "recommendation": "Tangani semua hewan kontak + lingkungan; gunakan sarung tangan (zoonosis).",
            "for_disease": "cat-dermatophytosis-ringworm"
          },
          {
            "name": "Manajemen HCM & gagal jantung",
            "type": "pharmacological",
            "line_of_therapy": 1,
            "procedure_steps": "1) Diuretik bila kongesti paru. 2) Pengelolaan ritme/beta-blocker bila indikasi. 3) Antitrombotik cegah ATE. 4) Batasi stres & aktivitas berat. 5) Monitor ekokardiografi berkala.",
            "recommendation": "Cegah pembekuan (ATE) pada atrium kiri membesar; tangani edema paru sebagai darurat.",
            "for_disease": "cat-hcm"
          }
        ],
        "suggested_products": [
          {
            "name": "Cairan IV + elektrolit",
            "kind": "medication",
            "active_ingredient": "Ringer Lactate + KCl",
            "route": "IV",
            "dosage_guide": "Koreksi defisit + maintenance",
            "cautions": "Pantau kalium.",
            "safety_flag": null
          },
          {
            "name": "Maropitant",
            "kind": "medication",
            "active_ingredient": "Maropitant",
            "route": "SC",
            "dosage_guide": "1 mg/kg SID",
            "cautions": "Antiemetik.",
            "safety_flag": null
          },
          {
            "name": "Antibiotik beta-lactam",
            "kind": "medication",
            "active_ingredient": "Ampicillin",
            "route": "IV",
            "dosage_guide": "20 mg/kg q8h",
            "cautions": "Cegah translokasi bakteri.",
            "safety_flag": null
          },
          {
            "name": "Cairan IV (NaCl 0.9%)",
            "kind": "medication",
            "active_ingredient": "Saline",
            "route": "IV",
            "dosage_guide": "Koreksi dehidrasi + diuresis",
            "cautions": "Pantau status jantung.",
            "safety_flag": null
          },
          {
            "name": "Calcium gluconate",
            "kind": "medication",
            "active_ingredient": "Calcium gluconate",
            "route": "IV",
            "dosage_guide": "Proteksi jantung saat hiperkalemia",
            "cautions": "Monitor EKG.",
            "safety_flag": null
          },
          {
            "name": "Buprenorphine",
            "kind": "medication",
            "active_ingredient": "Buprenorphine",
            "route": "oral transmucosal/IV",
            "dosage_guide": "0.02 mg/kg",
            "cautions": "Analgesik aman kucing.",
            "safety_flag": null
          },
          {
            "name": "Diet resep urinary (s/o)",
            "kind": "food_prescription",
            "active_ingredient": "Diet kontrol mineral/pH",
            "route": "oral",
            "dosage_guide": "Sesuai kebutuhan kalori",
            "cautions": "Diet jangka panjang sesuai tipe kristal.",
            "safety_flag": null
          },
          {
            "name": "Feliway (feline pheromone)",
            "kind": "supplement",
            "active_ingredient": "Synthetic pheromone",
            "route": "lingkungan",
            "dosage_guide": "Diffuser ruangan",
            "cautions": "Pendukung, bukan obat.",
            "safety_flag": null
          },
          {
            "name": "Diet resep renal",
            "kind": "food_prescription",
            "active_ingredient": "Diet rendah fosfor & protein terkontrol",
            "route": "oral",
            "dosage_guide": "Sesuai kalori",
            "cautions": "Transisi bertahap agar mau makan.",
            "safety_flag": null
          },
          {
            "name": "Telmisartan / Amlodipine",
            "kind": "medication",
            "active_ingredient": "Telmisartan (proteinuria) / Amlodipine (hipertensi)",
            "route": "oral",
            "dosage_guide": "Sesuai resep & tekanan darah",
            "cautions": "Pantau tekanan darah & ginjal.",
            "safety_flag": null
          },
          {
            "name": "Phosphate binder",
            "kind": "supplement",
            "active_ingredient": "Aluminium hidroksida / chitosan",
            "route": "oral (dengan makan)",
            "dosage_guide": "Sesuai kadar fosfat",
            "cautions": "Diberikan bersama makanan.",
            "safety_flag": null
          },
          {
            "name": "Maropitant / Mirtazapine",
            "kind": "medication",
            "active_ingredient": "Maropitant (mual), Mirtazapine (perangsang nafsu makan)",
            "route": "oral/SC",
            "dosage_guide": "Sesuai BB",
            "cautions": "Mirtazapine dosis kecil pada kucing.",
            "safety_flag": null
          },
          {
            "name": "Itraconazole",
            "kind": "medication",
            "active_ingredient": "Itraconazole",
            "route": "oral",
            "dosage_guide": "5 mg/kg SID (pulse 1 minggu on/off)",
            "cautions": "Monitor hati.",
            "safety_flag": null
          },
          {
            "name": "Lime sulfur dip",
            "kind": "medication",
            "active_ingredient": "Sulfurated lime",
            "route": "topikal",
            "dosage_guide": "2x/minggu",
            "cautions": "Bau menyengat, hindari mata.",
            "safety_flag": null
          },
          {
            "name": "Miconazole/chlorhexidine shampoo",
            "kind": "grooming",
            "active_ingredient": "Miconazole + chlorhexidine",
            "route": "topikal",
            "dosage_guide": "2x/minggu",
            "cautions": "Bilas bersih.",
            "safety_flag": null
          },
          {
            "name": "Furosemide",
            "kind": "medication",
            "active_ingredient": "Furosemide",
            "route": "oral/IV",
            "dosage_guide": "Sesuai derajat kongesti",
            "cautions": "Pantau ginjal & elektrolit.",
            "safety_flag": null
          },
          {
            "name": "Clopidogrel",
            "kind": "medication",
            "active_ingredient": "Clopidogrel",
            "route": "oral",
            "dosage_guide": "18.75 mg/kucing SID",
            "cautions": "Antiplatelet cegah tromboemboli.",
            "safety_flag": null
          },
          {
            "name": "Atenolol",
            "kind": "medication",
            "active_ingredient": "Atenolol",
            "route": "oral",
            "dosage_guide": "Sesuai resep",
            "cautions": "Hati-hati bila gagal jantung dekompensasi.",
            "safety_flag": null
          },
          {
            "name": "Pimobendan (kasus tertentu)",
            "kind": "medication",
            "active_ingredient": "Pimobendan",
            "route": "oral",
            "dosage_guide": "Sesuai resep kardiolog",
            "cautions": "Tidak rutin untuk HCM obstruktif.",
            "safety_flag": null
          }
        ],
        "red_flags": [
          "Muntah hebat",
          "Diare hebat"
        ],
        "safety_warnings": [
          "Data edukatif. Diagnosa & resep final wajib oleh dokter hewan. PERHATIAN: kucing sangat sensitif terhadap banyak obat (paracetamol, permethrin, NSAID dosis anjing = FATAL).",
          "Cairan IV + elektrolit: Pantau kalium.",
          "Maropitant: Antiemetik.",
          "Antibiotik beta-lactam: Cegah translokasi bakteri.",
          "Cairan IV (NaCl 0.9%): Pantau status jantung.",
          "Calcium gluconate: Monitor EKG.",
          "Buprenorphine: Analgesik aman kucing.",
          "Diet resep urinary (s/o): Diet jangka panjang sesuai tipe kristal.",
          "Feliway (feline pheromone): Pendukung, bukan obat.",
          "Diet resep renal: Transisi bertahap agar mau makan.",
          "Telmisartan / Amlodipine: Pantau tekanan darah & ginjal.",
          "Phosphate binder: Diberikan bersama makanan.",
          "Maropitant / Mirtazapine: Mirtazapine dosis kecil pada kucing.",
          "Itraconazole: Monitor hati.",
          "Lime sulfur dip: Bau menyengat, hindari mata.",
          "Miconazole/chlorhexidine shampoo: Bilas bersih.",
          "Furosemide: Pantau ginjal & elektrolit.",
          "Clopidogrel: Antiplatelet cegah tromboemboli.",
          "Atenolol: Hati-hati bila gagal jantung dekompensasi.",
          "Pimobendan (kasus tertentu): Tidak rutin untuk HCM obstruktif.",
          "paracetamol: FATAL untuk kucing (methemoglobinemia). Jangan diberikan.",
          "acetaminophen: FATAL untuk kucing. Jangan diberikan.",
          "permethrin: Sangat toksik untuk kucing (produk anjing). Bisa fatal.",
          "ibuprofen: Toksik; margin keamanan NSAID sangat sempit pada kucing.",
          "aspirin: Metabolisme lambat; hanya dosis sangat hati-hati oleh vet."
        ],
        "references": [
          {
            "type": "disease",
            "slug": "cat-fpv-panleukopenia",
            "name_id": "Panleukopenia (Distemper Kucing)",
            "overview": "Parvovirus kucing menyerang sumsum tulang & usus; sangat fatal pada anak kucing."
          },
          {
            "type": "disease",
            "slug": "cat-flutd",
            "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
            "overview": "Kumpulan kondisi saluran kemih bawah; sumbatan uretra pada jantan adalah DARURAT mematikan."
          },
          {
            "type": "disease",
            "slug": "cat-ckd",
            "name_id": "Penyakit Ginjal Kronis (CKD)",
            "overview": "Penurunan fungsi ginjal progresif, sangat umum pada kucing senior."
          },
          {
            "type": "disease",
            "slug": "cat-dermatophytosis-ringworm",
            "name_id": "Ringworm (Jamur Kulit)",
            "overview": "Infeksi jamur dermatofita pada kulit/bulu; menular ke hewan lain & manusia."
          },
          {
            "type": "disease",
            "slug": "cat-hcm",
            "name_id": "Kardiomiopati Hipertrofik (HCM)",
            "overview": "Penebalan otot ventrikel kiri, penyakit jantung paling umum pada kucing; risiko gagal jantung & tromboemboli."
          }
        ],
        "is_emergency": true,
        "generated_by": "rule_based",
        "disclaimer": "Saran AI bersifat pendukung keputusan klinis dan TIDAK menggantikan pemeriksaan langsung serta penilaian dokter hewan berlisensi. Dosis & produk wajib diverifikasi sesuai spesies, berat badan, dan kondisi pasien.",
        "created_at": "2026-06-19T13:00:57.218553Z"
      },
      "id": "b8ada203aaa1462ca957fd11d98168dd",
      "created_at": "2026-06-19T13:00:57.220364+00:00"
    }
  ],
  "messages": [
    {
      "consultation_id": "ext-20250619-001",
      "role": "user",
      "content": "Kucing saya muntah hebat dan tidak mau makan sejak kemarin",
      "meta": {
        "channel": "chat"
      },
      "id": "a8c96f602bf6476e88d0de7cf38ef6cf",
      "created_at": "2026-06-19T13:00:57.220609+00:00"
    },
    {
      "consultation_id": "ext-20250619-001",
      "role": "assistant",
      "content": "Berdasarkan 4 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 78%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
      "meta": {
        "type": "suggestion",
        "suggestion_id": "b8ada203aaa1462ca957fd11d98168dd"
      },
      "id": "24d2fe5ffa9f4123bb028385f951da06",
      "created_at": "2026-06-19T13:00:57.220764+00:00"
    },
    {
      "consultation_id": "ext-20250619-001",
      "role": "user",
      "content": "Sekarang juga diare berdarah dan lemas sekali",
      "meta": {
        "channel": "chat"
      },
      "id": "5b286efa8af1454da73a858449e1986b",
      "created_at": "2026-06-19T13:00:57.242969+00:00"
    },
    {
      "consultation_id": "ext-20250619-001",
      "role": "assistant",
      "content": "Berdasarkan 8 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 66%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
      "meta": {
        "type": "suggestion",
        "suggestion_id": "adf95d3a29b9450fb6c390ba301f71b9"
      },
      "id": "107ba35dcfc24965b467958531e04067",
      "created_at": "2026-06-19T13:00:57.243009+00:00"
    }
  ],
  "latest_suggestion": {
    "suggestion_type": "symptom_to_disease",
    "summary": "Berdasarkan 8 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 66%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
    "follow_up_questions": [
      "Sudah berapa lama gejala ini berlangsung?",
      "Apakah nafsu makan & minum berubah?",
      "Apakah ada perubahan pada urin/feses?",
      "Adakah riwayat vaksinasi & pengobatan terakhir?"
    ],
    "suggested_diseases": [
      {
        "disease_slug": "cat-fpv-panleukopenia",
        "name_id": "Panleukopenia (Distemper Kucing)",
        "confidence": 0.657,
        "rationale": "Cocok dengan gejala: Muntah hebat, Diare hebat",
        "is_emergency": true,
        "source": "ml+knowledge_base"
      },
      {
        "disease_slug": "cat-flutd",
        "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
        "confidence": 0.4408,
        "rationale": "Cocok dengan gejala: Kencing berdarah, Tidak bisa pipis sama sekali",
        "is_emergency": true,
        "source": "ml+knowledge_base"
      },
      {
        "disease_slug": "cat-ckd",
        "name_id": "Penyakit Ginjal Kronis (CKD)",
        "confidence": 0.524,
        "rationale": "Cocok dengan gejala: Nafsu makan menurun, Muntah, Bulu kusam & lemas",
        "is_emergency": false,
        "source": "ml+knowledge_base"
      },
      {
        "disease_slug": "cat-hcm",
        "name_id": "Kardiomiopati Hipertrofik (HCM)",
        "confidence": 0.1552,
        "rationale": "Cocok dengan gejala: Lemas",
        "is_emergency": false,
        "source": "ml+knowledge_base"
      },
      {
        "disease_slug": "cat-dermatophytosis-ringworm",
        "name_id": "Ringworm (Jamur Kulit)",
        "confidence": 0.042,
        "rationale": null,
        "is_emergency": false,
        "source": "ml"
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
      },
      {
        "name": "SNAP parvo (cross-reaktif FPV)",
        "type": "serology",
        "step_order": 1,
        "is_gold_standard": false,
        "expected_finding": "Antigen positif pada feses",
        "for_disease": "cat-fpv-panleukopenia"
      },
      {
        "name": "CBC",
        "type": "blood_test",
        "step_order": 3,
        "is_gold_standard": false,
        "expected_finding": "Panleukopenia (semua sel darah putih turun)",
        "for_disease": "cat-fpv-panleukopenia"
      },
      {
        "name": "Urinalisis + sedimen",
        "type": "urinalysis",
        "step_order": 2,
        "is_gold_standard": true,
        "expected_finding": "Kristal struvit/oksalat, darah, pH",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Palpasi kandung kemih",
        "type": "physical_exam",
        "step_order": 1,
        "is_gold_standard": false,
        "expected_finding": "Kandung kemih besar & keras (obstruksi)",
        "for_disease": "cat-flutd"
      },
      {
        "name": "USG / Radiografi",
        "type": "imaging_ultrasound",
        "step_order": 3,
        "is_gold_standard": false,
        "expected_finding": "Batu/urolith, dinding menebal",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Panel ginjal + elektrolit",
        "type": "blood_test",
        "step_order": 4,
        "is_gold_standard": false,
        "expected_finding": "Hiperkalemia & azotemia bila obstruksi",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Panel ginjal (BUN, Creatinine, SDMA)",
        "type": "blood_test",
        "step_order": 1,
        "is_gold_standard": true,
        "expected_finding": "SDMA & kreatinin meningkat",
        "for_disease": "cat-ckd"
      },
      {
        "name": "Urinalisis (USG, UPC)",
        "type": "urinalysis",
        "step_order": 2,
        "is_gold_standard": false,
        "expected_finding": "Urin encer (isostenuria), proteinuria",
        "for_disease": "cat-ckd"
      },
      {
        "name": "Tekanan darah",
        "type": "physical_exam",
        "step_order": 3,
        "is_gold_standard": false,
        "expected_finding": "Hipertensi sistemik",
        "for_disease": "cat-ckd"
      },
      {
        "name": "USG ginjal",
        "type": "imaging_ultrasound",
        "step_order": 4,
        "is_gold_standard": false,
        "expected_finding": "Ginjal mengecil/irregular atau kista (PKD)",
        "for_disease": "cat-ckd"
      },
      {
        "name": "Ekokardiografi",
        "type": "imaging_ultrasound",
        "step_order": 1,
        "is_gold_standard": true,
        "expected_finding": "Hipertrofi dinding ventrikel kiri >6mm",
        "for_disease": "cat-hcm"
      },
      {
        "name": "NT-proBNP test",
        "type": "blood_test",
        "step_order": 2,
        "is_gold_standard": false,
        "expected_finding": "Meningkat (skrining)",
        "for_disease": "cat-hcm"
      },
      {
        "name": "Radiografi toraks",
        "type": "imaging_xray",
        "step_order": 3,
        "is_gold_standard": false,
        "expected_finding": "Edema paru/efusi bila gagal jantung",
        "for_disease": "cat-hcm"
      },
      {
        "name": "Tekanan darah & T4",
        "type": "blood_test",
        "step_order": 4,
        "is_gold_standard": false,
        "expected_finding": "Singkirkan hipertiroid/hipertensi",
        "for_disease": "cat-hcm"
      },
      {
        "name": "Kultur jamur (DTM) / PCR",
        "type": "culture_sensitivity",
        "step_order": 3,
        "is_gold_standard": true,
        "expected_finding": "Pertumbuhan dermatofit",
        "for_disease": "cat-dermatophytosis-ringworm"
      },
      {
        "name": "Lampu Wood",
        "type": "physical_exam",
        "step_order": 1,
        "is_gold_standard": false,
        "expected_finding": "Fluoresensi hijau apel (M. canis sebagian)",
        "for_disease": "cat-dermatophytosis-ringworm"
      },
      {
        "name": "Trichogram (mikroskop bulu)",
        "type": "cytology",
        "step_order": 2,
        "is_gold_standard": false,
        "expected_finding": "Artrospora pada batang rambut",
        "for_disease": "cat-dermatophytosis-ringworm"
      }
    ],
    "suggested_treatments": [
      {
        "name": "Terapi suportif panleukopenia",
        "type": "supportive_care",
        "line_of_therapy": 1,
        "procedure_steps": "1) Isolasi & barrier nursing. 2) Cairan IV + elektrolit + glukosa. 3) Antiemetik. 4) Antibiotik cegah sepsis. 5) Nutrisi dini. 6) Monitor jumlah sel darah.",
        "recommendation": "Tidak ada antivirus spesifik; suportif agresif menentukan survival.",
        "for_disease": "cat-fpv-panleukopenia"
      },
      {
        "name": "Penanganan obstruksi uretra (darurat)",
        "type": "supportive_care",
        "line_of_therapy": 1,
        "procedure_steps": "1) Stabilkan: cairan IV, koreksi hiperkalemia. 2) Sedasi + pasang kateter uretra untuk dekompresi. 3) Bilas kandung kemih. 4) Rawat inap, pantau elektrolit & produksi urin. 5) Analgesik.",
        "recommendation": "Obstruksi = DARURAT; hiperkalemia bisa henti jantung. Segera ke klinik.",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Manajemen FIC non-obstruktif",
        "type": "dietary",
        "line_of_therapy": 1,
        "procedure_steps": "1) Diet urinary (lar­ut struvit / kontrol mineral). 2) Tingkatkan asupan air (makanan basah, fountain). 3) Kurangi stres (pheromone, environmental enrichment). 4) Analgesik jangka pendek.",
        "recommendation": "Fokus hidrasi & manajemen stres untuk cegah kekambuhan.",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Manajemen CKD bertahap (IRIS)",
        "type": "dietary",
        "line_of_therapy": 1,
        "procedure_steps": "1) Diet renal (protein berkualitas terbatas, fosfor rendah). 2) Phosphate binder bila perlu. 3) Kontrol tekanan darah. 4) Terapi cairan subkutan di rumah. 5) Atasi mual & anemia. 6) Monitor berkala.",
        "recommendation": "Diet renal adalah intervensi paling berdampak; mulai sedini mungkin & pantau tiap 3-6 bulan.",
        "for_disease": "cat-ckd"
      },
      {
        "name": "Manajemen HCM & gagal jantung",
        "type": "pharmacological",
        "line_of_therapy": 1,
        "procedure_steps": "1) Diuretik bila kongesti paru. 2) Pengelolaan ritme/beta-blocker bila indikasi. 3) Antitrombotik cegah ATE. 4) Batasi stres & aktivitas berat. 5) Monitor ekokardiografi berkala.",
        "recommendation": "Cegah pembekuan (ATE) pada atrium kiri membesar; tangani edema paru sebagai darurat.",
        "for_disease": "cat-hcm"
      },
      {
        "name": "Antijamur topikal + sistemik",
        "type": "pharmacological",
        "line_of_therapy": 1,
        "procedure_steps": "1) Antijamur topikal (lime sulfur/miconazole) seluruh tubuh. 2) Antijamur sistemik (itraconazole) untuk kasus luas. 3) Dekontaminasi lingkungan rutin. 4) Recheck dengan kultur sampai negatif 2x.",
        "recommendation": "Tangani semua hewan kontak + lingkungan; gunakan sarung tangan (zoonosis).",
        "for_disease": "cat-dermatophytosis-ringworm"
      }
    ],
    "suggested_products": [
      {
        "name": "Cairan IV + elektrolit",
        "kind": "medication",
        "active_ingredient": "Ringer Lactate + KCl",
        "route": "IV",
        "dosage_guide": "Koreksi defisit + maintenance",
        "cautions": "Pantau kalium.",
        "safety_flag": null
      },
      {
        "name": "Maropitant",
        "kind": "medication",
        "active_ingredient": "Maropitant",
        "route": "SC",
        "dosage_guide": "1 mg/kg SID",
        "cautions": "Antiemetik.",
        "safety_flag": null
      },
      {
        "name": "Antibiotik beta-lactam",
        "kind": "medication",
        "active_ingredient": "Ampicillin",
        "route": "IV",
        "dosage_guide": "20 mg/kg q8h",
        "cautions": "Cegah translokasi bakteri.",
        "safety_flag": null
      },
      {
        "name": "Cairan IV (NaCl 0.9%)",
        "kind": "medication",
        "active_ingredient": "Saline",
        "route": "IV",
        "dosage_guide": "Koreksi dehidrasi + diuresis",
        "cautions": "Pantau status jantung.",
        "safety_flag": null
      },
      {
        "name": "Calcium gluconate",
        "kind": "medication",
        "active_ingredient": "Calcium gluconate",
        "route": "IV",
        "dosage_guide": "Proteksi jantung saat hiperkalemia",
        "cautions": "Monitor EKG.",
        "safety_flag": null
      },
      {
        "name": "Buprenorphine",
        "kind": "medication",
        "active_ingredient": "Buprenorphine",
        "route": "oral transmucosal/IV",
        "dosage_guide": "0.02 mg/kg",
        "cautions": "Analgesik aman kucing.",
        "safety_flag": null
      },
      {
        "name": "Diet resep urinary (s/o)",
        "kind": "food_prescription",
        "active_ingredient": "Diet kontrol mineral/pH",
        "route": "oral",
        "dosage_guide": "Sesuai kebutuhan kalori",
        "cautions": "Diet jangka panjang sesuai tipe kristal.",
        "safety_flag": null
      },
      {
        "name": "Feliway (feline pheromone)",
        "kind": "supplement",
        "active_ingredient": "Synthetic pheromone",
        "route": "lingkungan",
        "dosage_guide": "Diffuser ruangan",
        "cautions": "Pendukung, bukan obat.",
        "safety_flag": null
      },
      {
        "name": "Diet resep renal",
        "kind": "food_prescription",
        "active_ingredient": "Diet rendah fosfor & protein terkontrol",
        "route": "oral",
        "dosage_guide": "Sesuai kalori",
        "cautions": "Transisi bertahap agar mau makan.",
        "safety_flag": null
      },
      {
        "name": "Telmisartan / Amlodipine",
        "kind": "medication",
        "active_ingredient": "Telmisartan (proteinuria) / Amlodipine (hipertensi)",
        "route": "oral",
        "dosage_guide": "Sesuai resep & tekanan darah",
        "cautions": "Pantau tekanan darah & ginjal.",
        "safety_flag": null
      },
      {
        "name": "Phosphate binder",
        "kind": "supplement",
        "active_ingredient": "Aluminium hidroksida / chitosan",
        "route": "oral (dengan makan)",
        "dosage_guide": "Sesuai kadar fosfat",
        "cautions": "Diberikan bersama makanan.",
        "safety_flag": null
      },
      {
        "name": "Maropitant / Mirtazapine",
        "kind": "medication",
        "active_ingredient": "Maropitant (mual), Mirtazapine (perangsang nafsu makan)",
        "route": "oral/SC",
        "dosage_guide": "Sesuai BB",
        "cautions": "Mirtazapine dosis kecil pada kucing.",
        "safety_flag": null
      },
      {
        "name": "Furosemide",
        "kind": "medication",
        "active_ingredient": "Furosemide",
        "route": "oral/IV",
        "dosage_guide": "Sesuai derajat kongesti",
        "cautions": "Pantau ginjal & elektrolit.",
        "safety_flag": null
      },
      {
        "name": "Clopidogrel",
        "kind": "medication",
        "active_ingredient": "Clopidogrel",
        "route": "oral",
        "dosage_guide": "18.75 mg/kucing SID",
        "cautions": "Antiplatelet cegah tromboemboli.",
        "safety_flag": null
      },
      {
        "name": "Atenolol",
        "kind": "medication",
        "active_ingredient": "Atenolol",
        "route": "oral",
        "dosage_guide": "Sesuai resep",
        "cautions": "Hati-hati bila gagal jantung dekompensasi.",
        "safety_flag": null
      },
      {
        "name": "Pimobendan (kasus tertentu)",
        "kind": "medication",
        "active_ingredient": "Pimobendan",
        "route": "oral",
        "dosage_guide": "Sesuai resep kardiolog",
        "cautions": "Tidak rutin untuk HCM obstruktif.",
        "safety_flag": null
      },
      {
        "name": "Itraconazole",
        "kind": "medication",
        "active_ingredient": "Itraconazole",
        "route": "oral",
        "dosage_guide": "5 mg/kg SID (pulse 1 minggu on/off)",
        "cautions": "Monitor hati.",
        "safety_flag": null
      },
      {
        "name": "Lime sulfur dip",
        "kind": "medication",
        "active_ingredient": "Sulfurated lime",
        "route": "topikal",
        "dosage_guide": "2x/minggu",
        "cautions": "Bau menyengat, hindari mata.",
        "safety_flag": null
      },
      {
        "name": "Miconazole/chlorhexidine shampoo",
        "kind": "grooming",
        "active_ingredient": "Miconazole + chlorhexidine",
        "route": "topikal",
        "dosage_guide": "2x/minggu",
        "cautions": "Bilas bersih.",
        "safety_flag": null
      }
    ],
    "red_flags": [
      "Tidak bisa pipis sama sekali",
      "Muntah hebat",
      "Diare hebat"
    ],
    "safety_warnings": [
      "Data edukatif. Diagnosa & resep final wajib oleh dokter hewan. PERHATIAN: kucing sangat sensitif terhadap banyak obat (paracetamol, permethrin, NSAID dosis anjing = FATAL).",
      "Cairan IV + elektrolit: Pantau kalium.",
      "Maropitant: Antiemetik.",
      "Antibiotik beta-lactam: Cegah translokasi bakteri.",
      "Cairan IV (NaCl 0.9%): Pantau status jantung.",
      "Calcium gluconate: Monitor EKG.",
      "Buprenorphine: Analgesik aman kucing.",
      "Diet resep urinary (s/o): Diet jangka panjang sesuai tipe kristal.",
      "Feliway (feline pheromone): Pendukung, bukan obat.",
      "Diet resep renal: Transisi bertahap agar mau makan.",
      "Telmisartan / Amlodipine: Pantau tekanan darah & ginjal.",
      "Phosphate binder: Diberikan bersama makanan.",
      "Maropitant / Mirtazapine: Mirtazapine dosis kecil pada kucing.",
      "Furosemide: Pantau ginjal & elektrolit.",
      "Clopidogrel: Antiplatelet cegah tromboemboli.",
      "Atenolol: Hati-hati bila gagal jantung dekompensasi.",
      "Pimobendan (kasus tertentu): Tidak rutin untuk HCM obstruktif.",
      "Itraconazole: Monitor hati.",
      "Lime sulfur dip: Bau menyengat, hindari mata.",
      "Miconazole/chlorhexidine shampoo: Bilas bersih.",
      "paracetamol: FATAL untuk kucing (methemoglobinemia). Jangan diberikan.",
      "acetaminophen: FATAL untuk kucing. Jangan diberikan.",
      "permethrin: Sangat toksik untuk kucing (produk anjing). Bisa fatal.",
      "ibuprofen: Toksik; margin keamanan NSAID sangat sempit pada kucing.",
      "aspirin: Metabolisme lambat; hanya dosis sangat hati-hati oleh vet."
    ],
    "references": [
      {
        "type": "disease",
        "slug": "cat-fpv-panleukopenia",
        "name_id": "Panleukopenia (Distemper Kucing)",
        "overview": "Parvovirus kucing menyerang sumsum tulang & usus; sangat fatal pada anak kucing."
      },
      {
        "type": "disease",
        "slug": "cat-flutd",
        "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
        "overview": "Kumpulan kondisi saluran kemih bawah; sumbatan uretra pada jantan adalah DARURAT mematikan."
      },
      {
        "type": "disease",
        "slug": "cat-ckd",
        "name_id": "Penyakit Ginjal Kronis (CKD)",
        "overview": "Penurunan fungsi ginjal progresif, sangat umum pada kucing senior."
      },
      {
        "type": "disease",
        "slug": "cat-hcm",
        "name_id": "Kardiomiopati Hipertrofik (HCM)",
        "overview": "Penebalan otot ventrikel kiri, penyakit jantung paling umum pada kucing; risiko gagal jantung & tromboemboli."
      },
      {
        "type": "disease",
        "slug": "cat-dermatophytosis-ringworm",
        "name_id": "Ringworm (Jamur Kulit)",
        "overview": "Infeksi jamur dermatofita pada kulit/bulu; menular ke hewan lain & manusia."
      }
    ],
    "is_emergency": true,
    "generated_by": "rule_based",
    "disclaimer": "Saran AI bersifat pendukung keputusan klinis dan TIDAK menggantikan pemeriksaan langsung serta penilaian dokter hewan berlisensi. Dosis & produk wajib diverifikasi sesuai spesies, berat badan, dan kondisi pasien.",
    "created_at": "2026-06-19T13:00:57.241551Z"
  }
}

```

---

### Record Doctor Input (Gold Label)

**POST /consultations/ext-20250619-001/doctor-input**

**Request:**

```json

{
  "confirmed_disease_slug": "cat-fpv-panleukopenia",
  "confirmed_symptoms": [
    "Muntah hebat",
    "Diare berdarah",
    "Lemas"
  ],
  "clinical_notes": "Panleukopenia confirmed via rapid test. Diberikan terapi suportif: cairan infus, anti muntah, antibiotik."
}

```

**Response:**

```json

{
  "status": "stored",
  "record_id": "a02628b38d7447eda395a2e68be10216"
}

```

---

### Record Feedback

**POST /consultations/ext-20250619-001/feedback**

**Request:**

```json

{
  "verdict": "correct",
  "comment": "Saran AI sangat akurat. Panleukopenia memang menjadi differential diagnosis utama.",
  "reviewer_id": 1
}

```

**Response:**

```json

{
  "status": "stored",
  "record_id": "170c602e298c49afa6c39e314d84ed0c"
}

```

---

### Get Entities

**GET /api/integration/entities/ext-20250619-001**

**Response:**

```json

{
  "consultation_id": "ext-20250619-001",
  "entities": {
    "consultation_id": "ext-20250619-001",
    "external_consultation_id": "ext-20250619-001",
    "org_id": null,
    "vet_id": 1,
    "owner_id": 100,
    "customer_id": 100,
    "pet_id": 200,
    "case_id": null,
    "external_refs": {}
  },
  "source": "registry"
}

```

---

### Lookup by External ID

**GET /api/integration/consultations/by-external/ext-20250619-001**

**Response:**

```json

{
  "consultation_id": "ext-20250619-001",
  "entities": {
    "consultation_id": "ext-20250619-001",
    "external_consultation_id": "ext-20250619-001",
    "org_id": null,
    "vet_id": 1,
    "owner_id": 100,
    "customer_id": 100,
    "pet_id": 200,
    "case_id": null,
    "external_refs": {}
  },
  "conversation": {
    "consultation_id": "ext-20250619-001",
    "org_id": null,
    "user_id": 1,
    "vet_id": 1,
    "owner_id": 100,
    "customer_id": 100,
    "pet_id": 200,
    "case_id": null,
    "external_consultation_id": "ext-20250619-001",
    "external_refs": {},
    "title": "Konsultasi ext-2025",
    "context": {
      "org_id": null,
      "user_id": 1,
      "vet_id": 1,
      "doctor_id": 1,
      "owner_id": 100,
      "customer_id": 100,
      "pet_id": 200,
      "case_id": null,
      "external_consultation_id": "ext-20250619-001",
      "external_refs": {},
      "category_slug": "cat",
      "breed_slug": "cat-persian",
      "age_years": 3.0,
      "weight_kg": null,
      "sex": null,
      "is_neutered": null,
      "temperature_c": null,
      "heart_rate": null,
      "resp_rate": null
    },
    "id": "6bcf507edea64d3d9212248fa4ddb3a0",
    "created_at": "2026-06-19T13:00:57.220106+00:00"
  },
  "context": {
    "org_id": null,
    "user_id": 1,
    "vet_id": 1,
    "doctor_id": 1,
    "owner_id": 100,
    "customer_id": 100,
    "pet_id": 200,
    "case_id": null,
    "external_consultation_id": "ext-20250619-001",
    "external_refs": {},
    "category_slug": "cat",
    "breed_slug": "cat-persian",
    "age_years": 3.0,
    "weight_kg": null,
    "sex": null,
    "is_neutered": null,
    "temperature_c": null,
    "heart_rate": null,
    "resp_rate": null
  },
  "suggestion_count": 2,
  "symptoms": [
    {
      "name_id": "Diare hebat",
      "name": "Profuse diarrhea",
      "body_system": "digestive",
      "is_red_flag": true,
      "score": 1.0,
      "matched_text": "hebat"
    },
    {
      "name_id": "Muntah",
      "name": "Vomiting",
      "body_system": "digestive",
      "is_red_flag": false,
      "score": 0.95,
      "matched_text": "muntah"
    },
    {
      "name_id": "Muntah hebat",
      "name": "Severe vomiting",
      "body_system": "digestive",
      "is_red_flag": true,
      "score": 0.95,
      "matched_text": "muntah hebat"
    },
    {
      "name_id": "Nafsu makan menurun",
      "name": "Poor appetite",
      "body_system": "digestive",
      "is_red_flag": false,
      "score": 0.8,
      "matched_text": "tidak mau makan"
    },
    {
      "name_id": "Tidak bisa pipis sama sekali",
      "name": "Unable to urinate (blockage)",
      "body_system": "urinary",
      "is_red_flag": true,
      "score": 1.0,
      "matched_text": "sekali"
    },
    {
      "name_id": "Lemas",
      "name": "Lethargy",
      "body_system": "systemic",
      "is_red_flag": false,
      "score": 0.95,
      "matched_text": "lemas"
    },
    {
      "name_id": "Kencing berdarah",
      "name": "Blood in urine",
      "body_system": "urinary",
      "is_red_flag": false,
      "score": 0.8,
      "matched_text": "berdarah"
    },
    {
      "name_id": "Bulu kusam & lemas",
      "name": "Poor coat / lethargy",
      "body_system": "systemic",
      "is_red_flag": false,
      "score": 0.8,
      "matched_text": "lemas"
    }
  ],
  "suggestions": [
    {
      "consultation_id": "ext-20250619-001",
      "request_id": null,
      "case_id": null,
      "pet_id": 200,
      "suggestion_type": "symptom_to_disease",
      "summary": "Berdasarkan 8 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 66%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
      "is_emergency": true,
      "is_reviewed": true,
      "generated_by": "rule_based",
      "payload": {
        "suggestion_type": "symptom_to_disease",
        "summary": "Berdasarkan 8 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 66%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
        "follow_up_questions": [
          "Sudah berapa lama gejala ini berlangsung?",
          "Apakah nafsu makan & minum berubah?",
          "Apakah ada perubahan pada urin/feses?",
          "Adakah riwayat vaksinasi & pengobatan terakhir?"
        ],
        "suggested_diseases": [
          {
            "disease_slug": "cat-fpv-panleukopenia",
            "name_id": "Panleukopenia (Distemper Kucing)",
            "confidence": 0.657,
            "rationale": "Cocok dengan gejala: Muntah hebat, Diare hebat",
            "is_emergency": true,
            "source": "ml+knowledge_base"
          },
          {
            "disease_slug": "cat-flutd",
            "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
            "confidence": 0.4408,
            "rationale": "Cocok dengan gejala: Kencing berdarah, Tidak bisa pipis sama sekali",
            "is_emergency": true,
            "source": "ml+knowledge_base"
          },
          {
            "disease_slug": "cat-ckd",
            "name_id": "Penyakit Ginjal Kronis (CKD)",
            "confidence": 0.524,
            "rationale": "Cocok dengan gejala: Nafsu makan menurun, Muntah, Bulu kusam & lemas",
            "is_emergency": false,
            "source": "ml+knowledge_base"
          },
          {
            "disease_slug": "cat-hcm",
            "name_id": "Kardiomiopati Hipertrofik (HCM)",
            "confidence": 0.1552,
            "rationale": "Cocok dengan gejala: Lemas",
            "is_emergency": false,
            "source": "ml+knowledge_base"
          },
          {
            "disease_slug": "cat-dermatophytosis-ringworm",
            "name_id": "Ringworm (Jamur Kulit)",
            "confidence": 0.042,
            "rationale": null,
            "is_emergency": false,
            "source": "ml"
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
          },
          {
            "name": "SNAP parvo (cross-reaktif FPV)",
            "type": "serology",
            "step_order": 1,
            "is_gold_standard": false,
            "expected_finding": "Antigen positif pada feses",
            "for_disease": "cat-fpv-panleukopenia"
          },
          {
            "name": "CBC",
            "type": "blood_test",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Panleukopenia (semua sel darah putih turun)",
            "for_disease": "cat-fpv-panleukopenia"
          },
          {
            "name": "Urinalisis + sedimen",
            "type": "urinalysis",
            "step_order": 2,
            "is_gold_standard": true,
            "expected_finding": "Kristal struvit/oksalat, darah, pH",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Palpasi kandung kemih",
            "type": "physical_exam",
            "step_order": 1,
            "is_gold_standard": false,
            "expected_finding": "Kandung kemih besar & keras (obstruksi)",
            "for_disease": "cat-flutd"
          },
          {
            "name": "USG / Radiografi",
            "type": "imaging_ultrasound",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Batu/urolith, dinding menebal",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Panel ginjal + elektrolit",
            "type": "blood_test",
            "step_order": 4,
            "is_gold_standard": false,
            "expected_finding": "Hiperkalemia & azotemia bila obstruksi",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Panel ginjal (BUN, Creatinine, SDMA)",
            "type": "blood_test",
            "step_order": 1,
            "is_gold_standard": true,
            "expected_finding": "SDMA & kreatinin meningkat",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Urinalisis (USG, UPC)",
            "type": "urinalysis",
            "step_order": 2,
            "is_gold_standard": false,
            "expected_finding": "Urin encer (isostenuria), proteinuria",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Tekanan darah",
            "type": "physical_exam",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Hipertensi sistemik",
            "for_disease": "cat-ckd"
          },
          {
            "name": "USG ginjal",
            "type": "imaging_ultrasound",
            "step_order": 4,
            "is_gold_standard": false,
            "expected_finding": "Ginjal mengecil/irregular atau kista (PKD)",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Ekokardiografi",
            "type": "imaging_ultrasound",
            "step_order": 1,
            "is_gold_standard": true,
            "expected_finding": "Hipertrofi dinding ventrikel kiri >6mm",
            "for_disease": "cat-hcm"
          },
          {
            "name": "NT-proBNP test",
            "type": "blood_test",
            "step_order": 2,
            "is_gold_standard": false,
            "expected_finding": "Meningkat (skrining)",
            "for_disease": "cat-hcm"
          },
          {
            "name": "Radiografi toraks",
            "type": "imaging_xray",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Edema paru/efusi bila gagal jantung",
            "for_disease": "cat-hcm"
          },
          {
            "name": "Tekanan darah & T4",
            "type": "blood_test",
            "step_order": 4,
            "is_gold_standard": false,
            "expected_finding": "Singkirkan hipertiroid/hipertensi",
            "for_disease": "cat-hcm"
          },
          {
            "name": "Kultur jamur (DTM) / PCR",
            "type": "culture_sensitivity",
            "step_order": 3,
            "is_gold_standard": true,
            "expected_finding": "Pertumbuhan dermatofit",
            "for_disease": "cat-dermatophytosis-ringworm"
          },
          {
            "name": "Lampu Wood",
            "type": "physical_exam",
            "step_order": 1,
            "is_gold_standard": false,
            "expected_finding": "Fluoresensi hijau apel (M. canis sebagian)",
            "for_disease": "cat-dermatophytosis-ringworm"
          },
          {
            "name": "Trichogram (mikroskop bulu)",
            "type": "cytology",
            "step_order": 2,
            "is_gold_standard": false,
            "expected_finding": "Artrospora pada batang rambut",
            "for_disease": "cat-dermatophytosis-ringworm"
          }
        ],
        "suggested_treatments": [
          {
            "name": "Terapi suportif panleukopenia",
            "type": "supportive_care",
            "line_of_therapy": 1,
            "procedure_steps": "1) Isolasi & barrier nursing. 2) Cairan IV + elektrolit + glukosa. 3) Antiemetik. 4) Antibiotik cegah sepsis. 5) Nutrisi dini. 6) Monitor jumlah sel darah.",
            "recommendation": "Tidak ada antivirus spesifik; suportif agresif menentukan survival.",
            "for_disease": "cat-fpv-panleukopenia"
          },
          {
            "name": "Penanganan obstruksi uretra (darurat)",
            "type": "supportive_care",
            "line_of_therapy": 1,
            "procedure_steps": "1) Stabilkan: cairan IV, koreksi hiperkalemia. 2) Sedasi + pasang kateter uretra untuk dekompresi. 3) Bilas kandung kemih. 4) Rawat inap, pantau elektrolit & produksi urin. 5) Analgesik.",
            "recommendation": "Obstruksi = DARURAT; hiperkalemia bisa henti jantung. Segera ke klinik.",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Manajemen FIC non-obstruktif",
            "type": "dietary",
            "line_of_therapy": 1,
            "procedure_steps": "1) Diet urinary (lar­ut struvit / kontrol mineral). 2) Tingkatkan asupan air (makanan basah, fountain). 3) Kurangi stres (pheromone, environmental enrichment). 4) Analgesik jangka pendek.",
            "recommendation": "Fokus hidrasi & manajemen stres untuk cegah kekambuhan.",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Manajemen CKD bertahap (IRIS)",
            "type": "dietary",
            "line_of_therapy": 1,
            "procedure_steps": "1) Diet renal (protein berkualitas terbatas, fosfor rendah). 2) Phosphate binder bila perlu. 3) Kontrol tekanan darah. 4) Terapi cairan subkutan di rumah. 5) Atasi mual & anemia. 6) Monitor berkala.",
            "recommendation": "Diet renal adalah intervensi paling berdampak; mulai sedini mungkin & pantau tiap 3-6 bulan.",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Manajemen HCM & gagal jantung",
            "type": "pharmacological",
            "line_of_therapy": 1,
            "procedure_steps": "1) Diuretik bila kongesti paru. 2) Pengelolaan ritme/beta-blocker bila indikasi. 3) Antitrombotik cegah ATE. 4) Batasi stres & aktivitas berat. 5) Monitor ekokardiografi berkala.",
            "recommendation": "Cegah pembekuan (ATE) pada atrium kiri membesar; tangani edema paru sebagai darurat.",
            "for_disease": "cat-hcm"
          },
          {
            "name": "Antijamur topikal + sistemik",
            "type": "pharmacological",
            "line_of_therapy": 1,
            "procedure_steps": "1) Antijamur topikal (lime sulfur/miconazole) seluruh tubuh. 2) Antijamur sistemik (itraconazole) untuk kasus luas. 3) Dekontaminasi lingkungan rutin. 4) Recheck dengan kultur sampai negatif 2x.",
            "recommendation": "Tangani semua hewan kontak + lingkungan; gunakan sarung tangan (zoonosis).",
            "for_disease": "cat-dermatophytosis-ringworm"
          }
        ],
        "suggested_products": [
          {
            "name": "Cairan IV + elektrolit",
            "kind": "medication",
            "active_ingredient": "Ringer Lactate + KCl",
            "route": "IV",
            "dosage_guide": "Koreksi defisit + maintenance",
            "cautions": "Pantau kalium.",
            "safety_flag": null
          },
          {
            "name": "Maropitant",
            "kind": "medication",
            "active_ingredient": "Maropitant",
            "route": "SC",
            "dosage_guide": "1 mg/kg SID",
            "cautions": "Antiemetik.",
            "safety_flag": null
          },
          {
            "name": "Antibiotik beta-lactam",
            "kind": "medication",
            "active_ingredient": "Ampicillin",
            "route": "IV",
            "dosage_guide": "20 mg/kg q8h",
            "cautions": "Cegah translokasi bakteri.",
            "safety_flag": null
          },
          {
            "name": "Cairan IV (NaCl 0.9%)",
            "kind": "medication",
            "active_ingredient": "Saline",
            "route": "IV",
            "dosage_guide": "Koreksi dehidrasi + diuresis",
            "cautions": "Pantau status jantung.",
            "safety_flag": null
          },
          {
            "name": "Calcium gluconate",
            "kind": "medication",
            "active_ingredient": "Calcium gluconate",
            "route": "IV",
            "dosage_guide": "Proteksi jantung saat hiperkalemia",
            "cautions": "Monitor EKG.",
            "safety_flag": null
          },
          {
            "name": "Buprenorphine",
            "kind": "medication",
            "active_ingredient": "Buprenorphine",
            "route": "oral transmucosal/IV",
            "dosage_guide": "0.02 mg/kg",
            "cautions": "Analgesik aman kucing.",
            "safety_flag": null
          },
          {
            "name": "Diet resep urinary (s/o)",
            "kind": "food_prescription",
            "active_ingredient": "Diet kontrol mineral/pH",
            "route": "oral",
            "dosage_guide": "Sesuai kebutuhan kalori",
            "cautions": "Diet jangka panjang sesuai tipe kristal.",
            "safety_flag": null
          },
          {
            "name": "Feliway (feline pheromone)",
            "kind": "supplement",
            "active_ingredient": "Synthetic pheromone",
            "route": "lingkungan",
            "dosage_guide": "Diffuser ruangan",
            "cautions": "Pendukung, bukan obat.",
            "safety_flag": null
          },
          {
            "name": "Diet resep renal",
            "kind": "food_prescription",
            "active_ingredient": "Diet rendah fosfor & protein terkontrol",
            "route": "oral",
            "dosage_guide": "Sesuai kalori",
            "cautions": "Transisi bertahap agar mau makan.",
            "safety_flag": null
          },
          {
            "name": "Telmisartan / Amlodipine",
            "kind": "medication",
            "active_ingredient": "Telmisartan (proteinuria) / Amlodipine (hipertensi)",
            "route": "oral",
            "dosage_guide": "Sesuai resep & tekanan darah",
            "cautions": "Pantau tekanan darah & ginjal.",
            "safety_flag": null
          },
          {
            "name": "Phosphate binder",
            "kind": "supplement",
            "active_ingredient": "Aluminium hidroksida / chitosan",
            "route": "oral (dengan makan)",
            "dosage_guide": "Sesuai kadar fosfat",
            "cautions": "Diberikan bersama makanan.",
            "safety_flag": null
          },
          {
            "name": "Maropitant / Mirtazapine",
            "kind": "medication",
            "active_ingredient": "Maropitant (mual), Mirtazapine (perangsang nafsu makan)",
            "route": "oral/SC",
            "dosage_guide": "Sesuai BB",
            "cautions": "Mirtazapine dosis kecil pada kucing.",
            "safety_flag": null
          },
          {
            "name": "Furosemide",
            "kind": "medication",
            "active_ingredient": "Furosemide",
            "route": "oral/IV",
            "dosage_guide": "Sesuai derajat kongesti",
            "cautions": "Pantau ginjal & elektrolit.",
            "safety_flag": null
          },
          {
            "name": "Clopidogrel",
            "kind": "medication",
            "active_ingredient": "Clopidogrel",
            "route": "oral",
            "dosage_guide": "18.75 mg/kucing SID",
            "cautions": "Antiplatelet cegah tromboemboli.",
            "safety_flag": null
          },
          {
            "name": "Atenolol",
            "kind": "medication",
            "active_ingredient": "Atenolol",
            "route": "oral",
            "dosage_guide": "Sesuai resep",
            "cautions": "Hati-hati bila gagal jantung dekompensasi.",
            "safety_flag": null
          },
          {
            "name": "Pimobendan (kasus tertentu)",
            "kind": "medication",
            "active_ingredient": "Pimobendan",
            "route": "oral",
            "dosage_guide": "Sesuai resep kardiolog",
            "cautions": "Tidak rutin untuk HCM obstruktif.",
            "safety_flag": null
          },
          {
            "name": "Itraconazole",
            "kind": "medication",
            "active_ingredient": "Itraconazole",
            "route": "oral",
            "dosage_guide": "5 mg/kg SID (pulse 1 minggu on/off)",
            "cautions": "Monitor hati.",
            "safety_flag": null
          },
          {
            "name": "Lime sulfur dip",
            "kind": "medication",
            "active_ingredient": "Sulfurated lime",
            "route": "topikal",
            "dosage_guide": "2x/minggu",
            "cautions": "Bau menyengat, hindari mata.",
            "safety_flag": null
          },
          {
            "name": "Miconazole/chlorhexidine shampoo",
            "kind": "grooming",
            "active_ingredient": "Miconazole + chlorhexidine",
            "route": "topikal",
            "dosage_guide": "2x/minggu",
            "cautions": "Bilas bersih.",
            "safety_flag": null
          }
        ],
        "red_flags": [
          "Tidak bisa pipis sama sekali",
          "Muntah hebat",
          "Diare hebat"
        ],
        "safety_warnings": [
          "Data edukatif. Diagnosa & resep final wajib oleh dokter hewan. PERHATIAN: kucing sangat sensitif terhadap banyak obat (paracetamol, permethrin, NSAID dosis anjing = FATAL).",
          "Cairan IV + elektrolit: Pantau kalium.",
          "Maropitant: Antiemetik.",
          "Antibiotik beta-lactam: Cegah translokasi bakteri.",
          "Cairan IV (NaCl 0.9%): Pantau status jantung.",
          "Calcium gluconate: Monitor EKG.",
          "Buprenorphine: Analgesik aman kucing.",
          "Diet resep urinary (s/o): Diet jangka panjang sesuai tipe kristal.",
          "Feliway (feline pheromone): Pendukung, bukan obat.",
          "Diet resep renal: Transisi bertahap agar mau makan.",
          "Telmisartan / Amlodipine: Pantau tekanan darah & ginjal.",
          "Phosphate binder: Diberikan bersama makanan.",
          "Maropitant / Mirtazapine: Mirtazapine dosis kecil pada kucing.",
          "Furosemide: Pantau ginjal & elektrolit.",
          "Clopidogrel: Antiplatelet cegah tromboemboli.",
          "Atenolol: Hati-hati bila gagal jantung dekompensasi.",
          "Pimobendan (kasus tertentu): Tidak rutin untuk HCM obstruktif.",
          "Itraconazole: Monitor hati.",
          "Lime sulfur dip: Bau menyengat, hindari mata.",
          "Miconazole/chlorhexidine shampoo: Bilas bersih.",
          "paracetamol: FATAL untuk kucing (methemoglobinemia). Jangan diberikan.",
          "acetaminophen: FATAL untuk kucing. Jangan diberikan.",
          "permethrin: Sangat toksik untuk kucing (produk anjing). Bisa fatal.",
          "ibuprofen: Toksik; margin keamanan NSAID sangat sempit pada kucing.",
          "aspirin: Metabolisme lambat; hanya dosis sangat hati-hati oleh vet."
        ],
        "references": [
          {
            "type": "disease",
            "slug": "cat-fpv-panleukopenia",
            "name_id": "Panleukopenia (Distemper Kucing)",
            "overview": "Parvovirus kucing menyerang sumsum tulang & usus; sangat fatal pada anak kucing."
          },
          {
            "type": "disease",
            "slug": "cat-flutd",
            "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
            "overview": "Kumpulan kondisi saluran kemih bawah; sumbatan uretra pada jantan adalah DARURAT mematikan."
          },
          {
            "type": "disease",
            "slug": "cat-ckd",
            "name_id": "Penyakit Ginjal Kronis (CKD)",
            "overview": "Penurunan fungsi ginjal progresif, sangat umum pada kucing senior."
          },
          {
            "type": "disease",
            "slug": "cat-hcm",
            "name_id": "Kardiomiopati Hipertrofik (HCM)",
            "overview": "Penebalan otot ventrikel kiri, penyakit jantung paling umum pada kucing; risiko gagal jantung & tromboemboli."
          },
          {
            "type": "disease",
            "slug": "cat-dermatophytosis-ringworm",
            "name_id": "Ringworm (Jamur Kulit)",
            "overview": "Infeksi jamur dermatofita pada kulit/bulu; menular ke hewan lain & manusia."
          }
        ],
        "is_emergency": true,
        "generated_by": "rule_based",
        "disclaimer": "Saran AI bersifat pendukung keputusan klinis dan TIDAK menggantikan pemeriksaan langsung serta penilaian dokter hewan berlisensi. Dosis & produk wajib diverifikasi sesuai spesies, berat badan, dan kondisi pasien.",
        "created_at": "2026-06-19T13:00:57.241551Z"
      },
      "created_at": "2026-06-19T13:00:57.242858+00:00",
      "id": "adf95d3a29b9450fb6c390ba301f71b9",
      "review_note": "Saran AI sangat akurat. Panleukopenia memang menjadi differential diagnosis utama.",
      "reviewed_at": "2026-06-19T13:00:57.264219+00:00",
      "_event": "review_update"
    },
    {
      "consultation_id": "ext-20250619-001",
      "request_id": null,
      "case_id": null,
      "pet_id": 200,
      "suggestion_type": "symptom_to_disease",
      "summary": "Berdasarkan 8 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 66%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
      "is_emergency": true,
      "is_reviewed": false,
      "generated_by": "rule_based",
      "payload": {
        "suggestion_type": "symptom_to_disease",
        "summary": "Berdasarkan 8 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 66%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
        "follow_up_questions": [
          "Sudah berapa lama gejala ini berlangsung?",
          "Apakah nafsu makan & minum berubah?",
          "Apakah ada perubahan pada urin/feses?",
          "Adakah riwayat vaksinasi & pengobatan terakhir?"
        ],
        "suggested_diseases": [
          {
            "disease_slug": "cat-fpv-panleukopenia",
            "name_id": "Panleukopenia (Distemper Kucing)",
            "confidence": 0.657,
            "rationale": "Cocok dengan gejala: Muntah hebat, Diare hebat",
            "is_emergency": true,
            "source": "ml+knowledge_base"
          },
          {
            "disease_slug": "cat-flutd",
            "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
            "confidence": 0.4408,
            "rationale": "Cocok dengan gejala: Kencing berdarah, Tidak bisa pipis sama sekali",
            "is_emergency": true,
            "source": "ml+knowledge_base"
          },
          {
            "disease_slug": "cat-ckd",
            "name_id": "Penyakit Ginjal Kronis (CKD)",
            "confidence": 0.524,
            "rationale": "Cocok dengan gejala: Nafsu makan menurun, Muntah, Bulu kusam & lemas",
            "is_emergency": false,
            "source": "ml+knowledge_base"
          },
          {
            "disease_slug": "cat-hcm",
            "name_id": "Kardiomiopati Hipertrofik (HCM)",
            "confidence": 0.1552,
            "rationale": "Cocok dengan gejala: Lemas",
            "is_emergency": false,
            "source": "ml+knowledge_base"
          },
          {
            "disease_slug": "cat-dermatophytosis-ringworm",
            "name_id": "Ringworm (Jamur Kulit)",
            "confidence": 0.042,
            "rationale": null,
            "is_emergency": false,
            "source": "ml"
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
          },
          {
            "name": "SNAP parvo (cross-reaktif FPV)",
            "type": "serology",
            "step_order": 1,
            "is_gold_standard": false,
            "expected_finding": "Antigen positif pada feses",
            "for_disease": "cat-fpv-panleukopenia"
          },
          {
            "name": "CBC",
            "type": "blood_test",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Panleukopenia (semua sel darah putih turun)",
            "for_disease": "cat-fpv-panleukopenia"
          },
          {
            "name": "Urinalisis + sedimen",
            "type": "urinalysis",
            "step_order": 2,
            "is_gold_standard": true,
            "expected_finding": "Kristal struvit/oksalat, darah, pH",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Palpasi kandung kemih",
            "type": "physical_exam",
            "step_order": 1,
            "is_gold_standard": false,
            "expected_finding": "Kandung kemih besar & keras (obstruksi)",
            "for_disease": "cat-flutd"
          },
          {
            "name": "USG / Radiografi",
            "type": "imaging_ultrasound",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Batu/urolith, dinding menebal",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Panel ginjal + elektrolit",
            "type": "blood_test",
            "step_order": 4,
            "is_gold_standard": false,
            "expected_finding": "Hiperkalemia & azotemia bila obstruksi",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Panel ginjal (BUN, Creatinine, SDMA)",
            "type": "blood_test",
            "step_order": 1,
            "is_gold_standard": true,
            "expected_finding": "SDMA & kreatinin meningkat",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Urinalisis (USG, UPC)",
            "type": "urinalysis",
            "step_order": 2,
            "is_gold_standard": false,
            "expected_finding": "Urin encer (isostenuria), proteinuria",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Tekanan darah",
            "type": "physical_exam",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Hipertensi sistemik",
            "for_disease": "cat-ckd"
          },
          {
            "name": "USG ginjal",
            "type": "imaging_ultrasound",
            "step_order": 4,
            "is_gold_standard": false,
            "expected_finding": "Ginjal mengecil/irregular atau kista (PKD)",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Ekokardiografi",
            "type": "imaging_ultrasound",
            "step_order": 1,
            "is_gold_standard": true,
            "expected_finding": "Hipertrofi dinding ventrikel kiri >6mm",
            "for_disease": "cat-hcm"
          },
          {
            "name": "NT-proBNP test",
            "type": "blood_test",
            "step_order": 2,
            "is_gold_standard": false,
            "expected_finding": "Meningkat (skrining)",
            "for_disease": "cat-hcm"
          },
          {
            "name": "Radiografi toraks",
            "type": "imaging_xray",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Edema paru/efusi bila gagal jantung",
            "for_disease": "cat-hcm"
          },
          {
            "name": "Tekanan darah & T4",
            "type": "blood_test",
            "step_order": 4,
            "is_gold_standard": false,
            "expected_finding": "Singkirkan hipertiroid/hipertensi",
            "for_disease": "cat-hcm"
          },
          {
            "name": "Kultur jamur (DTM) / PCR",
            "type": "culture_sensitivity",
            "step_order": 3,
            "is_gold_standard": true,
            "expected_finding": "Pertumbuhan dermatofit",
            "for_disease": "cat-dermatophytosis-ringworm"
          },
          {
            "name": "Lampu Wood",
            "type": "physical_exam",
            "step_order": 1,
            "is_gold_standard": false,
            "expected_finding": "Fluoresensi hijau apel (M. canis sebagian)",
            "for_disease": "cat-dermatophytosis-ringworm"
          },
          {
            "name": "Trichogram (mikroskop bulu)",
            "type": "cytology",
            "step_order": 2,
            "is_gold_standard": false,
            "expected_finding": "Artrospora pada batang rambut",
            "for_disease": "cat-dermatophytosis-ringworm"
          }
        ],
        "suggested_treatments": [
          {
            "name": "Terapi suportif panleukopenia",
            "type": "supportive_care",
            "line_of_therapy": 1,
            "procedure_steps": "1) Isolasi & barrier nursing. 2) Cairan IV + elektrolit + glukosa. 3) Antiemetik. 4) Antibiotik cegah sepsis. 5) Nutrisi dini. 6) Monitor jumlah sel darah.",
            "recommendation": "Tidak ada antivirus spesifik; suportif agresif menentukan survival.",
            "for_disease": "cat-fpv-panleukopenia"
          },
          {
            "name": "Penanganan obstruksi uretra (darurat)",
            "type": "supportive_care",
            "line_of_therapy": 1,
            "procedure_steps": "1) Stabilkan: cairan IV, koreksi hiperkalemia. 2) Sedasi + pasang kateter uretra untuk dekompresi. 3) Bilas kandung kemih. 4) Rawat inap, pantau elektrolit & produksi urin. 5) Analgesik.",
            "recommendation": "Obstruksi = DARURAT; hiperkalemia bisa henti jantung. Segera ke klinik.",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Manajemen FIC non-obstruktif",
            "type": "dietary",
            "line_of_therapy": 1,
            "procedure_steps": "1) Diet urinary (lar­ut struvit / kontrol mineral). 2) Tingkatkan asupan air (makanan basah, fountain). 3) Kurangi stres (pheromone, environmental enrichment). 4) Analgesik jangka pendek.",
            "recommendation": "Fokus hidrasi & manajemen stres untuk cegah kekambuhan.",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Manajemen CKD bertahap (IRIS)",
            "type": "dietary",
            "line_of_therapy": 1,
            "procedure_steps": "1) Diet renal (protein berkualitas terbatas, fosfor rendah). 2) Phosphate binder bila perlu. 3) Kontrol tekanan darah. 4) Terapi cairan subkutan di rumah. 5) Atasi mual & anemia. 6) Monitor berkala.",
            "recommendation": "Diet renal adalah intervensi paling berdampak; mulai sedini mungkin & pantau tiap 3-6 bulan.",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Manajemen HCM & gagal jantung",
            "type": "pharmacological",
            "line_of_therapy": 1,
            "procedure_steps": "1) Diuretik bila kongesti paru. 2) Pengelolaan ritme/beta-blocker bila indikasi. 3) Antitrombotik cegah ATE. 4) Batasi stres & aktivitas berat. 5) Monitor ekokardiografi berkala.",
            "recommendation": "Cegah pembekuan (ATE) pada atrium kiri membesar; tangani edema paru sebagai darurat.",
            "for_disease": "cat-hcm"
          },
          {
            "name": "Antijamur topikal + sistemik",
            "type": "pharmacological",
            "line_of_therapy": 1,
            "procedure_steps": "1) Antijamur topikal (lime sulfur/miconazole) seluruh tubuh. 2) Antijamur sistemik (itraconazole) untuk kasus luas. 3) Dekontaminasi lingkungan rutin. 4) Recheck dengan kultur sampai negatif 2x.",
            "recommendation": "Tangani semua hewan kontak + lingkungan; gunakan sarung tangan (zoonosis).",
            "for_disease": "cat-dermatophytosis-ringworm"
          }
        ],
        "suggested_products": [
          {
            "name": "Cairan IV + elektrolit",
            "kind": "medication",
            "active_ingredient": "Ringer Lactate + KCl",
            "route": "IV",
            "dosage_guide": "Koreksi defisit + maintenance",
            "cautions": "Pantau kalium.",
            "safety_flag": null
          },
          {
            "name": "Maropitant",
            "kind": "medication",
            "active_ingredient": "Maropitant",
            "route": "SC",
            "dosage_guide": "1 mg/kg SID",
            "cautions": "Antiemetik.",
            "safety_flag": null
          },
          {
            "name": "Antibiotik beta-lactam",
            "kind": "medication",
            "active_ingredient": "Ampicillin",
            "route": "IV",
            "dosage_guide": "20 mg/kg q8h",
            "cautions": "Cegah translokasi bakteri.",
            "safety_flag": null
          },
          {
            "name": "Cairan IV (NaCl 0.9%)",
            "kind": "medication",
            "active_ingredient": "Saline",
            "route": "IV",
            "dosage_guide": "Koreksi dehidrasi + diuresis",
            "cautions": "Pantau status jantung.",
            "safety_flag": null
          },
          {
            "name": "Calcium gluconate",
            "kind": "medication",
            "active_ingredient": "Calcium gluconate",
            "route": "IV",
            "dosage_guide": "Proteksi jantung saat hiperkalemia",
            "cautions": "Monitor EKG.",
            "safety_flag": null
          },
          {
            "name": "Buprenorphine",
            "kind": "medication",
            "active_ingredient": "Buprenorphine",
            "route": "oral transmucosal/IV",
            "dosage_guide": "0.02 mg/kg",
            "cautions": "Analgesik aman kucing.",
            "safety_flag": null
          },
          {
            "name": "Diet resep urinary (s/o)",
            "kind": "food_prescription",
            "active_ingredient": "Diet kontrol mineral/pH",
            "route": "oral",
            "dosage_guide": "Sesuai kebutuhan kalori",
            "cautions": "Diet jangka panjang sesuai tipe kristal.",
            "safety_flag": null
          },
          {
            "name": "Feliway (feline pheromone)",
            "kind": "supplement",
            "active_ingredient": "Synthetic pheromone",
            "route": "lingkungan",
            "dosage_guide": "Diffuser ruangan",
            "cautions": "Pendukung, bukan obat.",
            "safety_flag": null
          },
          {
            "name": "Diet resep renal",
            "kind": "food_prescription",
            "active_ingredient": "Diet rendah fosfor & protein terkontrol",
            "route": "oral",
            "dosage_guide": "Sesuai kalori",
            "cautions": "Transisi bertahap agar mau makan.",
            "safety_flag": null
          },
          {
            "name": "Telmisartan / Amlodipine",
            "kind": "medication",
            "active_ingredient": "Telmisartan (proteinuria) / Amlodipine (hipertensi)",
            "route": "oral",
            "dosage_guide": "Sesuai resep & tekanan darah",
            "cautions": "Pantau tekanan darah & ginjal.",
            "safety_flag": null
          },
          {
            "name": "Phosphate binder",
            "kind": "supplement",
            "active_ingredient": "Aluminium hidroksida / chitosan",
            "route": "oral (dengan makan)",
            "dosage_guide": "Sesuai kadar fosfat",
            "cautions": "Diberikan bersama makanan.",
            "safety_flag": null
          },
          {
            "name": "Maropitant / Mirtazapine",
            "kind": "medication",
            "active_ingredient": "Maropitant (mual), Mirtazapine (perangsang nafsu makan)",
            "route": "oral/SC",
            "dosage_guide": "Sesuai BB",
            "cautions": "Mirtazapine dosis kecil pada kucing.",
            "safety_flag": null
          },
          {
            "name": "Furosemide",
            "kind": "medication",
            "active_ingredient": "Furosemide",
            "route": "oral/IV",
            "dosage_guide": "Sesuai derajat kongesti",
            "cautions": "Pantau ginjal & elektrolit.",
            "safety_flag": null
          },
          {
            "name": "Clopidogrel",
            "kind": "medication",
            "active_ingredient": "Clopidogrel",
            "route": "oral",
            "dosage_guide": "18.75 mg/kucing SID",
            "cautions": "Antiplatelet cegah tromboemboli.",
            "safety_flag": null
          },
          {
            "name": "Atenolol",
            "kind": "medication",
            "active_ingredient": "Atenolol",
            "route": "oral",
            "dosage_guide": "Sesuai resep",
            "cautions": "Hati-hati bila gagal jantung dekompensasi.",
            "safety_flag": null
          },
          {
            "name": "Pimobendan (kasus tertentu)",
            "kind": "medication",
            "active_ingredient": "Pimobendan",
            "route": "oral",
            "dosage_guide": "Sesuai resep kardiolog",
            "cautions": "Tidak rutin untuk HCM obstruktif.",
            "safety_flag": null
          },
          {
            "name": "Itraconazole",
            "kind": "medication",
            "active_ingredient": "Itraconazole",
            "route": "oral",
            "dosage_guide": "5 mg/kg SID (pulse 1 minggu on/off)",
            "cautions": "Monitor hati.",
            "safety_flag": null
          },
          {
            "name": "Lime sulfur dip",
            "kind": "medication",
            "active_ingredient": "Sulfurated lime",
            "route": "topikal",
            "dosage_guide": "2x/minggu",
            "cautions": "Bau menyengat, hindari mata.",
            "safety_flag": null
          },
          {
            "name": "Miconazole/chlorhexidine shampoo",
            "kind": "grooming",
            "active_ingredient": "Miconazole + chlorhexidine",
            "route": "topikal",
            "dosage_guide": "2x/minggu",
            "cautions": "Bilas bersih.",
            "safety_flag": null
          }
        ],
        "red_flags": [
          "Tidak bisa pipis sama sekali",
          "Muntah hebat",
          "Diare hebat"
        ],
        "safety_warnings": [
          "Data edukatif. Diagnosa & resep final wajib oleh dokter hewan. PERHATIAN: kucing sangat sensitif terhadap banyak obat (paracetamol, permethrin, NSAID dosis anjing = FATAL).",
          "Cairan IV + elektrolit: Pantau kalium.",
          "Maropitant: Antiemetik.",
          "Antibiotik beta-lactam: Cegah translokasi bakteri.",
          "Cairan IV (NaCl 0.9%): Pantau status jantung.",
          "Calcium gluconate: Monitor EKG.",
          "Buprenorphine: Analgesik aman kucing.",
          "Diet resep urinary (s/o): Diet jangka panjang sesuai tipe kristal.",
          "Feliway (feline pheromone): Pendukung, bukan obat.",
          "Diet resep renal: Transisi bertahap agar mau makan.",
          "Telmisartan / Amlodipine: Pantau tekanan darah & ginjal.",
          "Phosphate binder: Diberikan bersama makanan.",
          "Maropitant / Mirtazapine: Mirtazapine dosis kecil pada kucing.",
          "Furosemide: Pantau ginjal & elektrolit.",
          "Clopidogrel: Antiplatelet cegah tromboemboli.",
          "Atenolol: Hati-hati bila gagal jantung dekompensasi.",
          "Pimobendan (kasus tertentu): Tidak rutin untuk HCM obstruktif.",
          "Itraconazole: Monitor hati.",
          "Lime sulfur dip: Bau menyengat, hindari mata.",
          "Miconazole/chlorhexidine shampoo: Bilas bersih.",
          "paracetamol: FATAL untuk kucing (methemoglobinemia). Jangan diberikan.",
          "acetaminophen: FATAL untuk kucing. Jangan diberikan.",
          "permethrin: Sangat toksik untuk kucing (produk anjing). Bisa fatal.",
          "ibuprofen: Toksik; margin keamanan NSAID sangat sempit pada kucing.",
          "aspirin: Metabolisme lambat; hanya dosis sangat hati-hati oleh vet."
        ],
        "references": [
          {
            "type": "disease",
            "slug": "cat-fpv-panleukopenia",
            "name_id": "Panleukopenia (Distemper Kucing)",
            "overview": "Parvovirus kucing menyerang sumsum tulang & usus; sangat fatal pada anak kucing."
          },
          {
            "type": "disease",
            "slug": "cat-flutd",
            "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
            "overview": "Kumpulan kondisi saluran kemih bawah; sumbatan uretra pada jantan adalah DARURAT mematikan."
          },
          {
            "type": "disease",
            "slug": "cat-ckd",
            "name_id": "Penyakit Ginjal Kronis (CKD)",
            "overview": "Penurunan fungsi ginjal progresif, sangat umum pada kucing senior."
          },
          {
            "type": "disease",
            "slug": "cat-hcm",
            "name_id": "Kardiomiopati Hipertrofik (HCM)",
            "overview": "Penebalan otot ventrikel kiri, penyakit jantung paling umum pada kucing; risiko gagal jantung & tromboemboli."
          },
          {
            "type": "disease",
            "slug": "cat-dermatophytosis-ringworm",
            "name_id": "Ringworm (Jamur Kulit)",
            "overview": "Infeksi jamur dermatofita pada kulit/bulu; menular ke hewan lain & manusia."
          }
        ],
        "is_emergency": true,
        "generated_by": "rule_based",
        "disclaimer": "Saran AI bersifat pendukung keputusan klinis dan TIDAK menggantikan pemeriksaan langsung serta penilaian dokter hewan berlisensi. Dosis & produk wajib diverifikasi sesuai spesies, berat badan, dan kondisi pasien.",
        "created_at": "2026-06-19T13:00:57.241551Z"
      },
      "id": "adf95d3a29b9450fb6c390ba301f71b9",
      "created_at": "2026-06-19T13:00:57.242858+00:00"
    },
    {
      "consultation_id": "ext-20250619-001",
      "request_id": null,
      "case_id": null,
      "pet_id": 200,
      "suggestion_type": "symptom_to_disease",
      "summary": "Berdasarkan 4 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 78%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
      "is_emergency": true,
      "is_reviewed": false,
      "generated_by": "rule_based",
      "payload": {
        "suggestion_type": "symptom_to_disease",
        "summary": "Berdasarkan 4 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 78%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
        "follow_up_questions": [
          "Sudah berapa lama gejala ini berlangsung?",
          "Apakah nafsu makan & minum berubah?",
          "Apakah ada perubahan pada urin/feses?",
          "Adakah riwayat vaksinasi & pengobatan terakhir?"
        ],
        "suggested_diseases": [
          {
            "disease_slug": "cat-fpv-panleukopenia",
            "name_id": "Panleukopenia (Distemper Kucing)",
            "confidence": 0.784,
            "rationale": "Cocok dengan gejala: Muntah hebat, Diare hebat",
            "is_emergency": true,
            "source": "ml+knowledge_base"
          },
          {
            "disease_slug": "cat-flutd",
            "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
            "confidence": 0.018,
            "rationale": null,
            "is_emergency": true,
            "source": "ml"
          },
          {
            "disease_slug": "cat-ckd",
            "name_id": "Penyakit Ginjal Kronis (CKD)",
            "confidence": 0.34,
            "rationale": "Cocok dengan gejala: Nafsu makan menurun, Muntah",
            "is_emergency": false,
            "source": "ml+knowledge_base"
          },
          {
            "disease_slug": "cat-dermatophytosis-ringworm",
            "name_id": "Ringworm (Jamur Kulit)",
            "confidence": 0.076,
            "rationale": null,
            "is_emergency": false,
            "source": "ml"
          },
          {
            "disease_slug": "cat-hcm",
            "name_id": "Kardiomiopati Hipertrofik (HCM)",
            "confidence": 0.042,
            "rationale": null,
            "is_emergency": false,
            "source": "ml"
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
          },
          {
            "name": "SNAP parvo (cross-reaktif FPV)",
            "type": "serology",
            "step_order": 1,
            "is_gold_standard": false,
            "expected_finding": "Antigen positif pada feses",
            "for_disease": "cat-fpv-panleukopenia"
          },
          {
            "name": "CBC",
            "type": "blood_test",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Panleukopenia (semua sel darah putih turun)",
            "for_disease": "cat-fpv-panleukopenia"
          },
          {
            "name": "Urinalisis + sedimen",
            "type": "urinalysis",
            "step_order": 2,
            "is_gold_standard": true,
            "expected_finding": "Kristal struvit/oksalat, darah, pH",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Palpasi kandung kemih",
            "type": "physical_exam",
            "step_order": 1,
            "is_gold_standard": false,
            "expected_finding": "Kandung kemih besar & keras (obstruksi)",
            "for_disease": "cat-flutd"
          },
          {
            "name": "USG / Radiografi",
            "type": "imaging_ultrasound",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Batu/urolith, dinding menebal",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Panel ginjal + elektrolit",
            "type": "blood_test",
            "step_order": 4,
            "is_gold_standard": false,
            "expected_finding": "Hiperkalemia & azotemia bila obstruksi",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Panel ginjal (BUN, Creatinine, SDMA)",
            "type": "blood_test",
            "step_order": 1,
            "is_gold_standard": true,
            "expected_finding": "SDMA & kreatinin meningkat",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Urinalisis (USG, UPC)",
            "type": "urinalysis",
            "step_order": 2,
            "is_gold_standard": false,
            "expected_finding": "Urin encer (isostenuria), proteinuria",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Tekanan darah",
            "type": "physical_exam",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Hipertensi sistemik",
            "for_disease": "cat-ckd"
          },
          {
            "name": "USG ginjal",
            "type": "imaging_ultrasound",
            "step_order": 4,
            "is_gold_standard": false,
            "expected_finding": "Ginjal mengecil/irregular atau kista (PKD)",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Kultur jamur (DTM) / PCR",
            "type": "culture_sensitivity",
            "step_order": 3,
            "is_gold_standard": true,
            "expected_finding": "Pertumbuhan dermatofit",
            "for_disease": "cat-dermatophytosis-ringworm"
          },
          {
            "name": "Lampu Wood",
            "type": "physical_exam",
            "step_order": 1,
            "is_gold_standard": false,
            "expected_finding": "Fluoresensi hijau apel (M. canis sebagian)",
            "for_disease": "cat-dermatophytosis-ringworm"
          },
          {
            "name": "Trichogram (mikroskop bulu)",
            "type": "cytology",
            "step_order": 2,
            "is_gold_standard": false,
            "expected_finding": "Artrospora pada batang rambut",
            "for_disease": "cat-dermatophytosis-ringworm"
          },
          {
            "name": "Ekokardiografi",
            "type": "imaging_ultrasound",
            "step_order": 1,
            "is_gold_standard": true,
            "expected_finding": "Hipertrofi dinding ventrikel kiri >6mm",
            "for_disease": "cat-hcm"
          },
          {
            "name": "NT-proBNP test",
            "type": "blood_test",
            "step_order": 2,
            "is_gold_standard": false,
            "expected_finding": "Meningkat (skrining)",
            "for_disease": "cat-hcm"
          },
          {
            "name": "Radiografi toraks",
            "type": "imaging_xray",
            "step_order": 3,
            "is_gold_standard": false,
            "expected_finding": "Edema paru/efusi bila gagal jantung",
            "for_disease": "cat-hcm"
          },
          {
            "name": "Tekanan darah & T4",
            "type": "blood_test",
            "step_order": 4,
            "is_gold_standard": false,
            "expected_finding": "Singkirkan hipertiroid/hipertensi",
            "for_disease": "cat-hcm"
          }
        ],
        "suggested_treatments": [
          {
            "name": "Terapi suportif panleukopenia",
            "type": "supportive_care",
            "line_of_therapy": 1,
            "procedure_steps": "1) Isolasi & barrier nursing. 2) Cairan IV + elektrolit + glukosa. 3) Antiemetik. 4) Antibiotik cegah sepsis. 5) Nutrisi dini. 6) Monitor jumlah sel darah.",
            "recommendation": "Tidak ada antivirus spesifik; suportif agresif menentukan survival.",
            "for_disease": "cat-fpv-panleukopenia"
          },
          {
            "name": "Penanganan obstruksi uretra (darurat)",
            "type": "supportive_care",
            "line_of_therapy": 1,
            "procedure_steps": "1) Stabilkan: cairan IV, koreksi hiperkalemia. 2) Sedasi + pasang kateter uretra untuk dekompresi. 3) Bilas kandung kemih. 4) Rawat inap, pantau elektrolit & produksi urin. 5) Analgesik.",
            "recommendation": "Obstruksi = DARURAT; hiperkalemia bisa henti jantung. Segera ke klinik.",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Manajemen FIC non-obstruktif",
            "type": "dietary",
            "line_of_therapy": 1,
            "procedure_steps": "1) Diet urinary (lar­ut struvit / kontrol mineral). 2) Tingkatkan asupan air (makanan basah, fountain). 3) Kurangi stres (pheromone, environmental enrichment). 4) Analgesik jangka pendek.",
            "recommendation": "Fokus hidrasi & manajemen stres untuk cegah kekambuhan.",
            "for_disease": "cat-flutd"
          },
          {
            "name": "Manajemen CKD bertahap (IRIS)",
            "type": "dietary",
            "line_of_therapy": 1,
            "procedure_steps": "1) Diet renal (protein berkualitas terbatas, fosfor rendah). 2) Phosphate binder bila perlu. 3) Kontrol tekanan darah. 4) Terapi cairan subkutan di rumah. 5) Atasi mual & anemia. 6) Monitor berkala.",
            "recommendation": "Diet renal adalah intervensi paling berdampak; mulai sedini mungkin & pantau tiap 3-6 bulan.",
            "for_disease": "cat-ckd"
          },
          {
            "name": "Antijamur topikal + sistemik",
            "type": "pharmacological",
            "line_of_therapy": 1,
            "procedure_steps": "1) Antijamur topikal (lime sulfur/miconazole) seluruh tubuh. 2) Antijamur sistemik (itraconazole) untuk kasus luas. 3) Dekontaminasi lingkungan rutin. 4) Recheck dengan kultur sampai negatif 2x.",
            "recommendation": "Tangani semua hewan kontak + lingkungan; gunakan sarung tangan (zoonosis).",
            "for_disease": "cat-dermatophytosis-ringworm"
          },
          {
            "name": "Manajemen HCM & gagal jantung",
            "type": "pharmacological",
            "line_of_therapy": 1,
            "procedure_steps": "1) Diuretik bila kongesti paru. 2) Pengelolaan ritme/beta-blocker bila indikasi. 3) Antitrombotik cegah ATE. 4) Batasi stres & aktivitas berat. 5) Monitor ekokardiografi berkala.",
            "recommendation": "Cegah pembekuan (ATE) pada atrium kiri membesar; tangani edema paru sebagai darurat.",
            "for_disease": "cat-hcm"
          }
        ],
        "suggested_products": [
          {
            "name": "Cairan IV + elektrolit",
            "kind": "medication",
            "active_ingredient": "Ringer Lactate + KCl",
            "route": "IV",
            "dosage_guide": "Koreksi defisit + maintenance",
            "cautions": "Pantau kalium.",
            "safety_flag": null
          },
          {
            "name": "Maropitant",
            "kind": "medication",
            "active_ingredient": "Maropitant",
            "route": "SC",
            "dosage_guide": "1 mg/kg SID",
            "cautions": "Antiemetik.",
            "safety_flag": null
          },
          {
            "name": "Antibiotik beta-lactam",
            "kind": "medication",
            "active_ingredient": "Ampicillin",
            "route": "IV",
            "dosage_guide": "20 mg/kg q8h",
            "cautions": "Cegah translokasi bakteri.",
            "safety_flag": null
          },
          {
            "name": "Cairan IV (NaCl 0.9%)",
            "kind": "medication",
            "active_ingredient": "Saline",
            "route": "IV",
            "dosage_guide": "Koreksi dehidrasi + diuresis",
            "cautions": "Pantau status jantung.",
            "safety_flag": null
          },
          {
            "name": "Calcium gluconate",
            "kind": "medication",
            "active_ingredient": "Calcium gluconate",
            "route": "IV",
            "dosage_guide": "Proteksi jantung saat hiperkalemia",
            "cautions": "Monitor EKG.",
            "safety_flag": null
          },
          {
            "name": "Buprenorphine",
            "kind": "medication",
            "active_ingredient": "Buprenorphine",
            "route": "oral transmucosal/IV",
            "dosage_guide": "0.02 mg/kg",
            "cautions": "Analgesik aman kucing.",
            "safety_flag": null
          },
          {
            "name": "Diet resep urinary (s/o)",
            "kind": "food_prescription",
            "active_ingredient": "Diet kontrol mineral/pH",
            "route": "oral",
            "dosage_guide": "Sesuai kebutuhan kalori",
            "cautions": "Diet jangka panjang sesuai tipe kristal.",
            "safety_flag": null
          },
          {
            "name": "Feliway (feline pheromone)",
            "kind": "supplement",
            "active_ingredient": "Synthetic pheromone",
            "route": "lingkungan",
            "dosage_guide": "Diffuser ruangan",
            "cautions": "Pendukung, bukan obat.",
            "safety_flag": null
          },
          {
            "name": "Diet resep renal",
            "kind": "food_prescription",
            "active_ingredient": "Diet rendah fosfor & protein terkontrol",
            "route": "oral",
            "dosage_guide": "Sesuai kalori",
            "cautions": "Transisi bertahap agar mau makan.",
            "safety_flag": null
          },
          {
            "name": "Telmisartan / Amlodipine",
            "kind": "medication",
            "active_ingredient": "Telmisartan (proteinuria) / Amlodipine (hipertensi)",
            "route": "oral",
            "dosage_guide": "Sesuai resep & tekanan darah",
            "cautions": "Pantau tekanan darah & ginjal.",
            "safety_flag": null
          },
          {
            "name": "Phosphate binder",
            "kind": "supplement",
            "active_ingredient": "Aluminium hidroksida / chitosan",
            "route": "oral (dengan makan)",
            "dosage_guide": "Sesuai kadar fosfat",
            "cautions": "Diberikan bersama makanan.",
            "safety_flag": null
          },
          {
            "name": "Maropitant / Mirtazapine",
            "kind": "medication",
            "active_ingredient": "Maropitant (mual), Mirtazapine (perangsang nafsu makan)",
            "route": "oral/SC",
            "dosage_guide": "Sesuai BB",
            "cautions": "Mirtazapine dosis kecil pada kucing.",
            "safety_flag": null
          },
          {
            "name": "Itraconazole",
            "kind": "medication",
            "active_ingredient": "Itraconazole",
            "route": "oral",
            "dosage_guide": "5 mg/kg SID (pulse 1 minggu on/off)",
            "cautions": "Monitor hati.",
            "safety_flag": null
          },
          {
            "name": "Lime sulfur dip",
            "kind": "medication",
            "active_ingredient": "Sulfurated lime",
            "route": "topikal",
            "dosage_guide": "2x/minggu",
            "cautions": "Bau menyengat, hindari mata.",
            "safety_flag": null
          },
          {
            "name": "Miconazole/chlorhexidine shampoo",
            "kind": "grooming",
            "active_ingredient": "Miconazole + chlorhexidine",
            "route": "topikal",
            "dosage_guide": "2x/minggu",
            "cautions": "Bilas bersih.",
            "safety_flag": null
          },
          {
            "name": "Furosemide",
            "kind": "medication",
            "active_ingredient": "Furosemide",
            "route": "oral/IV",
            "dosage_guide": "Sesuai derajat kongesti",
            "cautions": "Pantau ginjal & elektrolit.",
            "safety_flag": null
          },
          {
            "name": "Clopidogrel",
            "kind": "medication",
            "active_ingredient": "Clopidogrel",
            "route": "oral",
            "dosage_guide": "18.75 mg/kucing SID",
            "cautions": "Antiplatelet cegah tromboemboli.",
            "safety_flag": null
          },
          {
            "name": "Atenolol",
            "kind": "medication",
            "active_ingredient": "Atenolol",
            "route": "oral",
            "dosage_guide": "Sesuai resep",
            "cautions": "Hati-hati bila gagal jantung dekompensasi.",
            "safety_flag": null
          },
          {
            "name": "Pimobendan (kasus tertentu)",
            "kind": "medication",
            "active_ingredient": "Pimobendan",
            "route": "oral",
            "dosage_guide": "Sesuai resep kardiolog",
            "cautions": "Tidak rutin untuk HCM obstruktif.",
            "safety_flag": null
          }
        ],
        "red_flags": [
          "Muntah hebat",
          "Diare hebat"
        ],
        "safety_warnings": [
          "Data edukatif. Diagnosa & resep final wajib oleh dokter hewan. PERHATIAN: kucing sangat sensitif terhadap banyak obat (paracetamol, permethrin, NSAID dosis anjing = FATAL).",
          "Cairan IV + elektrolit: Pantau kalium.",
          "Maropitant: Antiemetik.",
          "Antibiotik beta-lactam: Cegah translokasi bakteri.",
          "Cairan IV (NaCl 0.9%): Pantau status jantung.",
          "Calcium gluconate: Monitor EKG.",
          "Buprenorphine: Analgesik aman kucing.",
          "Diet resep urinary (s/o): Diet jangka panjang sesuai tipe kristal.",
          "Feliway (feline pheromone): Pendukung, bukan obat.",
          "Diet resep renal: Transisi bertahap agar mau makan.",
          "Telmisartan / Amlodipine: Pantau tekanan darah & ginjal.",
          "Phosphate binder: Diberikan bersama makanan.",
          "Maropitant / Mirtazapine: Mirtazapine dosis kecil pada kucing.",
          "Itraconazole: Monitor hati.",
          "Lime sulfur dip: Bau menyengat, hindari mata.",
          "Miconazole/chlorhexidine shampoo: Bilas bersih.",
          "Furosemide: Pantau ginjal & elektrolit.",
          "Clopidogrel: Antiplatelet cegah tromboemboli.",
          "Atenolol: Hati-hati bila gagal jantung dekompensasi.",
          "Pimobendan (kasus tertentu): Tidak rutin untuk HCM obstruktif.",
          "paracetamol: FATAL untuk kucing (methemoglobinemia). Jangan diberikan.",
          "acetaminophen: FATAL untuk kucing. Jangan diberikan.",
          "permethrin: Sangat toksik untuk kucing (produk anjing). Bisa fatal.",
          "ibuprofen: Toksik; margin keamanan NSAID sangat sempit pada kucing.",
          "aspirin: Metabolisme lambat; hanya dosis sangat hati-hati oleh vet."
        ],
        "references": [
          {
            "type": "disease",
            "slug": "cat-fpv-panleukopenia",
            "name_id": "Panleukopenia (Distemper Kucing)",
            "overview": "Parvovirus kucing menyerang sumsum tulang & usus; sangat fatal pada anak kucing."
          },
          {
            "type": "disease",
            "slug": "cat-flutd",
            "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
            "overview": "Kumpulan kondisi saluran kemih bawah; sumbatan uretra pada jantan adalah DARURAT mematikan."
          },
          {
            "type": "disease",
            "slug": "cat-ckd",
            "name_id": "Penyakit Ginjal Kronis (CKD)",
            "overview": "Penurunan fungsi ginjal progresif, sangat umum pada kucing senior."
          },
          {
            "type": "disease",
            "slug": "cat-dermatophytosis-ringworm",
            "name_id": "Ringworm (Jamur Kulit)",
            "overview": "Infeksi jamur dermatofita pada kulit/bulu; menular ke hewan lain & manusia."
          },
          {
            "type": "disease",
            "slug": "cat-hcm",
            "name_id": "Kardiomiopati Hipertrofik (HCM)",
            "overview": "Penebalan otot ventrikel kiri, penyakit jantung paling umum pada kucing; risiko gagal jantung & tromboemboli."
          }
        ],
        "is_emergency": true,
        "generated_by": "rule_based",
        "disclaimer": "Saran AI bersifat pendukung keputusan klinis dan TIDAK menggantikan pemeriksaan langsung serta penilaian dokter hewan berlisensi. Dosis & produk wajib diverifikasi sesuai spesies, berat badan, dan kondisi pasien.",
        "created_at": "2026-06-19T13:00:57.218553Z"
      },
      "id": "b8ada203aaa1462ca957fd11d98168dd",
      "created_at": "2026-06-19T13:00:57.220364+00:00"
    }
  ],
  "messages": [
    {
      "consultation_id": "ext-20250619-001",
      "role": "user",
      "content": "Kucing saya muntah hebat dan tidak mau makan sejak kemarin",
      "meta": {
        "channel": "chat"
      },
      "id": "a8c96f602bf6476e88d0de7cf38ef6cf",
      "created_at": "2026-06-19T13:00:57.220609+00:00"
    },
    {
      "consultation_id": "ext-20250619-001",
      "role": "assistant",
      "content": "Berdasarkan 4 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 78%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
      "meta": {
        "type": "suggestion",
        "suggestion_id": "b8ada203aaa1462ca957fd11d98168dd"
      },
      "id": "24d2fe5ffa9f4123bb028385f951da06",
      "created_at": "2026-06-19T13:00:57.220764+00:00"
    },
    {
      "consultation_id": "ext-20250619-001",
      "role": "user",
      "content": "Sekarang juga diare berdarah dan lemas sekali",
      "meta": {
        "channel": "chat"
      },
      "id": "5b286efa8af1454da73a858449e1986b",
      "created_at": "2026-06-19T13:00:57.242969+00:00"
    },
    {
      "consultation_id": "ext-20250619-001",
      "role": "assistant",
      "content": "Berdasarkan 8 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 66%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
      "meta": {
        "type": "suggestion",
        "suggestion_id": "adf95d3a29b9450fb6c390ba301f71b9"
      },
      "id": "107ba35dcfc24965b467958531e04067",
      "created_at": "2026-06-19T13:00:57.243009+00:00"
    },
    {
      "consultation_id": "ext-20250619-001",
      "role": "vet",
      "content": "Panleukopenia confirmed via rapid test. Diberikan terapi suportif: cairan infus, anti muntah, antibiotik.",
      "meta": {
        "confirmed_disease": "cat-fpv-panleukopenia",
        "vet_id": 1
      },
      "id": "75072b7806f54c0bb237b3df373b1128",
      "created_at": "2026-06-19T13:00:57.254546+00:00"
    }
  ],
  "latest_suggestion": {
    "suggestion_type": "symptom_to_disease",
    "summary": "Berdasarkan 8 gejala terdeteksi, kemungkinan teratas: Panleukopenia (Distemper Kucing) (keyakinan 66%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR feses.",
    "follow_up_questions": [
      "Sudah berapa lama gejala ini berlangsung?",
      "Apakah nafsu makan & minum berubah?",
      "Apakah ada perubahan pada urin/feses?",
      "Adakah riwayat vaksinasi & pengobatan terakhir?"
    ],
    "suggested_diseases": [
      {
        "disease_slug": "cat-fpv-panleukopenia",
        "name_id": "Panleukopenia (Distemper Kucing)",
        "confidence": 0.657,
        "rationale": "Cocok dengan gejala: Muntah hebat, Diare hebat",
        "is_emergency": true,
        "source": "ml+knowledge_base"
      },
      {
        "disease_slug": "cat-flutd",
        "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
        "confidence": 0.4408,
        "rationale": "Cocok dengan gejala: Kencing berdarah, Tidak bisa pipis sama sekali",
        "is_emergency": true,
        "source": "ml+knowledge_base"
      },
      {
        "disease_slug": "cat-ckd",
        "name_id": "Penyakit Ginjal Kronis (CKD)",
        "confidence": 0.524,
        "rationale": "Cocok dengan gejala: Nafsu makan menurun, Muntah, Bulu kusam & lemas",
        "is_emergency": false,
        "source": "ml+knowledge_base"
      },
      {
        "disease_slug": "cat-hcm",
        "name_id": "Kardiomiopati Hipertrofik (HCM)",
        "confidence": 0.1552,
        "rationale": "Cocok dengan gejala: Lemas",
        "is_emergency": false,
        "source": "ml+knowledge_base"
      },
      {
        "disease_slug": "cat-dermatophytosis-ringworm",
        "name_id": "Ringworm (Jamur Kulit)",
        "confidence": 0.042,
        "rationale": null,
        "is_emergency": false,
        "source": "ml"
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
      },
      {
        "name": "SNAP parvo (cross-reaktif FPV)",
        "type": "serology",
        "step_order": 1,
        "is_gold_standard": false,
        "expected_finding": "Antigen positif pada feses",
        "for_disease": "cat-fpv-panleukopenia"
      },
      {
        "name": "CBC",
        "type": "blood_test",
        "step_order": 3,
        "is_gold_standard": false,
        "expected_finding": "Panleukopenia (semua sel darah putih turun)",
        "for_disease": "cat-fpv-panleukopenia"
      },
      {
        "name": "Urinalisis + sedimen",
        "type": "urinalysis",
        "step_order": 2,
        "is_gold_standard": true,
        "expected_finding": "Kristal struvit/oksalat, darah, pH",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Palpasi kandung kemih",
        "type": "physical_exam",
        "step_order": 1,
        "is_gold_standard": false,
        "expected_finding": "Kandung kemih besar & keras (obstruksi)",
        "for_disease": "cat-flutd"
      },
      {
        "name": "USG / Radiografi",
        "type": "imaging_ultrasound",
        "step_order": 3,
        "is_gold_standard": false,
        "expected_finding": "Batu/urolith, dinding menebal",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Panel ginjal + elektrolit",
        "type": "blood_test",
        "step_order": 4,
        "is_gold_standard": false,
        "expected_finding": "Hiperkalemia & azotemia bila obstruksi",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Panel ginjal (BUN, Creatinine, SDMA)",
        "type": "blood_test",
        "step_order": 1,
        "is_gold_standard": true,
        "expected_finding": "SDMA & kreatinin meningkat",
        "for_disease": "cat-ckd"
      },
      {
        "name": "Urinalisis (USG, UPC)",
        "type": "urinalysis",
        "step_order": 2,
        "is_gold_standard": false,
        "expected_finding": "Urin encer (isostenuria), proteinuria",
        "for_disease": "cat-ckd"
      },
      {
        "name": "Tekanan darah",
        "type": "physical_exam",
        "step_order": 3,
        "is_gold_standard": false,
        "expected_finding": "Hipertensi sistemik",
        "for_disease": "cat-ckd"
      },
      {
        "name": "USG ginjal",
        "type": "imaging_ultrasound",
        "step_order": 4,
        "is_gold_standard": false,
        "expected_finding": "Ginjal mengecil/irregular atau kista (PKD)",
        "for_disease": "cat-ckd"
      },
      {
        "name": "Ekokardiografi",
        "type": "imaging_ultrasound",
        "step_order": 1,
        "is_gold_standard": true,
        "expected_finding": "Hipertrofi dinding ventrikel kiri >6mm",
        "for_disease": "cat-hcm"
      },
      {
        "name": "NT-proBNP test",
        "type": "blood_test",
        "step_order": 2,
        "is_gold_standard": false,
        "expected_finding": "Meningkat (skrining)",
        "for_disease": "cat-hcm"
      },
      {
        "name": "Radiografi toraks",
        "type": "imaging_xray",
        "step_order": 3,
        "is_gold_standard": false,
        "expected_finding": "Edema paru/efusi bila gagal jantung",
        "for_disease": "cat-hcm"
      },
      {
        "name": "Tekanan darah & T4",
        "type": "blood_test",
        "step_order": 4,
        "is_gold_standard": false,
        "expected_finding": "Singkirkan hipertiroid/hipertensi",
        "for_disease": "cat-hcm"
      },
      {
        "name": "Kultur jamur (DTM) / PCR",
        "type": "culture_sensitivity",
        "step_order": 3,
        "is_gold_standard": true,
        "expected_finding": "Pertumbuhan dermatofit",
        "for_disease": "cat-dermatophytosis-ringworm"
      },
      {
        "name": "Lampu Wood",
        "type": "physical_exam",
        "step_order": 1,
        "is_gold_standard": false,
        "expected_finding": "Fluoresensi hijau apel (M. canis sebagian)",
        "for_disease": "cat-dermatophytosis-ringworm"
      },
      {
        "name": "Trichogram (mikroskop bulu)",
        "type": "cytology",
        "step_order": 2,
        "is_gold_standard": false,
        "expected_finding": "Artrospora pada batang rambut",
        "for_disease": "cat-dermatophytosis-ringworm"
      }
    ],
    "suggested_treatments": [
      {
        "name": "Terapi suportif panleukopenia",
        "type": "supportive_care",
        "line_of_therapy": 1,
        "procedure_steps": "1) Isolasi & barrier nursing. 2) Cairan IV + elektrolit + glukosa. 3) Antiemetik. 4) Antibiotik cegah sepsis. 5) Nutrisi dini. 6) Monitor jumlah sel darah.",
        "recommendation": "Tidak ada antivirus spesifik; suportif agresif menentukan survival.",
        "for_disease": "cat-fpv-panleukopenia"
      },
      {
        "name": "Penanganan obstruksi uretra (darurat)",
        "type": "supportive_care",
        "line_of_therapy": 1,
        "procedure_steps": "1) Stabilkan: cairan IV, koreksi hiperkalemia. 2) Sedasi + pasang kateter uretra untuk dekompresi. 3) Bilas kandung kemih. 4) Rawat inap, pantau elektrolit & produksi urin. 5) Analgesik.",
        "recommendation": "Obstruksi = DARURAT; hiperkalemia bisa henti jantung. Segera ke klinik.",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Manajemen FIC non-obstruktif",
        "type": "dietary",
        "line_of_therapy": 1,
        "procedure_steps": "1) Diet urinary (lar­ut struvit / kontrol mineral). 2) Tingkatkan asupan air (makanan basah, fountain). 3) Kurangi stres (pheromone, environmental enrichment). 4) Analgesik jangka pendek.",
        "recommendation": "Fokus hidrasi & manajemen stres untuk cegah kekambuhan.",
        "for_disease": "cat-flutd"
      },
      {
        "name": "Manajemen CKD bertahap (IRIS)",
        "type": "dietary",
        "line_of_therapy": 1,
        "procedure_steps": "1) Diet renal (protein berkualitas terbatas, fosfor rendah). 2) Phosphate binder bila perlu. 3) Kontrol tekanan darah. 4) Terapi cairan subkutan di rumah. 5) Atasi mual & anemia. 6) Monitor berkala.",
        "recommendation": "Diet renal adalah intervensi paling berdampak; mulai sedini mungkin & pantau tiap 3-6 bulan.",
        "for_disease": "cat-ckd"
      },
      {
        "name": "Manajemen HCM & gagal jantung",
        "type": "pharmacological",
        "line_of_therapy": 1,
        "procedure_steps": "1) Diuretik bila kongesti paru. 2) Pengelolaan ritme/beta-blocker bila indikasi. 3) Antitrombotik cegah ATE. 4) Batasi stres & aktivitas berat. 5) Monitor ekokardiografi berkala.",
        "recommendation": "Cegah pembekuan (ATE) pada atrium kiri membesar; tangani edema paru sebagai darurat.",
        "for_disease": "cat-hcm"
      },
      {
        "name": "Antijamur topikal + sistemik",
        "type": "pharmacological",
        "line_of_therapy": 1,
        "procedure_steps": "1) Antijamur topikal (lime sulfur/miconazole) seluruh tubuh. 2) Antijamur sistemik (itraconazole) untuk kasus luas. 3) Dekontaminasi lingkungan rutin. 4) Recheck dengan kultur sampai negatif 2x.",
        "recommendation": "Tangani semua hewan kontak + lingkungan; gunakan sarung tangan (zoonosis).",
        "for_disease": "cat-dermatophytosis-ringworm"
      }
    ],
    "suggested_products": [
      {
        "name": "Cairan IV + elektrolit",
        "kind": "medication",
        "active_ingredient": "Ringer Lactate + KCl",
        "route": "IV",
        "dosage_guide": "Koreksi defisit + maintenance",
        "cautions": "Pantau kalium.",
        "safety_flag": null
      },
      {
        "name": "Maropitant",
        "kind": "medication",
        "active_ingredient": "Maropitant",
        "route": "SC",
        "dosage_guide": "1 mg/kg SID",
        "cautions": "Antiemetik.",
        "safety_flag": null
      },
      {
        "name": "Antibiotik beta-lactam",
        "kind": "medication",
        "active_ingredient": "Ampicillin",
        "route": "IV",
        "dosage_guide": "20 mg/kg q8h",
        "cautions": "Cegah translokasi bakteri.",
        "safety_flag": null
      },
      {
        "name": "Cairan IV (NaCl 0.9%)",
        "kind": "medication",
        "active_ingredient": "Saline",
        "route": "IV",
        "dosage_guide": "Koreksi dehidrasi + diuresis",
        "cautions": "Pantau status jantung.",
        "safety_flag": null
      },
      {
        "name": "Calcium gluconate",
        "kind": "medication",
        "active_ingredient": "Calcium gluconate",
        "route": "IV",
        "dosage_guide": "Proteksi jantung saat hiperkalemia",
        "cautions": "Monitor EKG.",
        "safety_flag": null
      },
      {
        "name": "Buprenorphine",
        "kind": "medication",
        "active_ingredient": "Buprenorphine",
        "route": "oral transmucosal/IV",
        "dosage_guide": "0.02 mg/kg",
        "cautions": "Analgesik aman kucing.",
        "safety_flag": null
      },
      {
        "name": "Diet resep urinary (s/o)",
        "kind": "food_prescription",
        "active_ingredient": "Diet kontrol mineral/pH",
        "route": "oral",
        "dosage_guide": "Sesuai kebutuhan kalori",
        "cautions": "Diet jangka panjang sesuai tipe kristal.",
        "safety_flag": null
      },
      {
        "name": "Feliway (feline pheromone)",
        "kind": "supplement",
        "active_ingredient": "Synthetic pheromone",
        "route": "lingkungan",
        "dosage_guide": "Diffuser ruangan",
        "cautions": "Pendukung, bukan obat.",
        "safety_flag": null
      },
      {
        "name": "Diet resep renal",
        "kind": "food_prescription",
        "active_ingredient": "Diet rendah fosfor & protein terkontrol",
        "route": "oral",
        "dosage_guide": "Sesuai kalori",
        "cautions": "Transisi bertahap agar mau makan.",
        "safety_flag": null
      },
      {
        "name": "Telmisartan / Amlodipine",
        "kind": "medication",
        "active_ingredient": "Telmisartan (proteinuria) / Amlodipine (hipertensi)",
        "route": "oral",
        "dosage_guide": "Sesuai resep & tekanan darah",
        "cautions": "Pantau tekanan darah & ginjal.",
        "safety_flag": null
      },
      {
        "name": "Phosphate binder",
        "kind": "supplement",
        "active_ingredient": "Aluminium hidroksida / chitosan",
        "route": "oral (dengan makan)",
        "dosage_guide": "Sesuai kadar fosfat",
        "cautions": "Diberikan bersama makanan.",
        "safety_flag": null
      },
      {
        "name": "Maropitant / Mirtazapine",
        "kind": "medication",
        "active_ingredient": "Maropitant (mual), Mirtazapine (perangsang nafsu makan)",
        "route": "oral/SC",
        "dosage_guide": "Sesuai BB",
        "cautions": "Mirtazapine dosis kecil pada kucing.",
        "safety_flag": null
      },
      {
        "name": "Furosemide",
        "kind": "medication",
        "active_ingredient": "Furosemide",
        "route": "oral/IV",
        "dosage_guide": "Sesuai derajat kongesti",
        "cautions": "Pantau ginjal & elektrolit.",
        "safety_flag": null
      },
      {
        "name": "Clopidogrel",
        "kind": "medication",
        "active_ingredient": "Clopidogrel",
        "route": "oral",
        "dosage_guide": "18.75 mg/kucing SID",
        "cautions": "Antiplatelet cegah tromboemboli.",
        "safety_flag": null
      },
      {
        "name": "Atenolol",
        "kind": "medication",
        "active_ingredient": "Atenolol",
        "route": "oral",
        "dosage_guide": "Sesuai resep",
        "cautions": "Hati-hati bila gagal jantung dekompensasi.",
        "safety_flag": null
      },
      {
        "name": "Pimobendan (kasus tertentu)",
        "kind": "medication",
        "active_ingredient": "Pimobendan",
        "route": "oral",
        "dosage_guide": "Sesuai resep kardiolog",
        "cautions": "Tidak rutin untuk HCM obstruktif.",
        "safety_flag": null
      },
      {
        "name": "Itraconazole",
        "kind": "medication",
        "active_ingredient": "Itraconazole",
        "route": "oral",
        "dosage_guide": "5 mg/kg SID (pulse 1 minggu on/off)",
        "cautions": "Monitor hati.",
        "safety_flag": null
      },
      {
        "name": "Lime sulfur dip",
        "kind": "medication",
        "active_ingredient": "Sulfurated lime",
        "route": "topikal",
        "dosage_guide": "2x/minggu",
        "cautions": "Bau menyengat, hindari mata.",
        "safety_flag": null
      },
      {
        "name": "Miconazole/chlorhexidine shampoo",
        "kind": "grooming",
        "active_ingredient": "Miconazole + chlorhexidine",
        "route": "topikal",
        "dosage_guide": "2x/minggu",
        "cautions": "Bilas bersih.",
        "safety_flag": null
      }
    ],
    "red_flags": [
      "Tidak bisa pipis sama sekali",
      "Muntah hebat",
      "Diare hebat"
    ],
    "safety_warnings": [
      "Data edukatif. Diagnosa & resep final wajib oleh dokter hewan. PERHATIAN: kucing sangat sensitif terhadap banyak obat (paracetamol, permethrin, NSAID dosis anjing = FATAL).",
      "Cairan IV + elektrolit: Pantau kalium.",
      "Maropitant: Antiemetik.",
      "Antibiotik beta-lactam: Cegah translokasi bakteri.",
      "Cairan IV (NaCl 0.9%): Pantau status jantung.",
      "Calcium gluconate: Monitor EKG.",
      "Buprenorphine: Analgesik aman kucing.",
      "Diet resep urinary (s/o): Diet jangka panjang sesuai tipe kristal.",
      "Feliway (feline pheromone): Pendukung, bukan obat.",
      "Diet resep renal: Transisi bertahap agar mau makan.",
      "Telmisartan / Amlodipine: Pantau tekanan darah & ginjal.",
      "Phosphate binder: Diberikan bersama makanan.",
      "Maropitant / Mirtazapine: Mirtazapine dosis kecil pada kucing.",
      "Furosemide: Pantau ginjal & elektrolit.",
      "Clopidogrel: Antiplatelet cegah tromboemboli.",
      "Atenolol: Hati-hati bila gagal jantung dekompensasi.",
      "Pimobendan (kasus tertentu): Tidak rutin untuk HCM obstruktif.",
      "Itraconazole: Monitor hati.",
      "Lime sulfur dip: Bau menyengat, hindari mata.",
      "Miconazole/chlorhexidine shampoo: Bilas bersih.",
      "paracetamol: FATAL untuk kucing (methemoglobinemia). Jangan diberikan.",
      "acetaminophen: FATAL untuk kucing. Jangan diberikan.",
      "permethrin: Sangat toksik untuk kucing (produk anjing). Bisa fatal.",
      "ibuprofen: Toksik; margin keamanan NSAID sangat sempit pada kucing.",
      "aspirin: Metabolisme lambat; hanya dosis sangat hati-hati oleh vet."
    ],
    "references": [
      {
        "type": "disease",
        "slug": "cat-fpv-panleukopenia",
        "name_id": "Panleukopenia (Distemper Kucing)",
        "overview": "Parvovirus kucing menyerang sumsum tulang & usus; sangat fatal pada anak kucing."
      },
      {
        "type": "disease",
        "slug": "cat-flutd",
        "name_id": "Gangguan Saluran Kemih Bawah (FLUTD)",
        "overview": "Kumpulan kondisi saluran kemih bawah; sumbatan uretra pada jantan adalah DARURAT mematikan."
      },
      {
        "type": "disease",
        "slug": "cat-ckd",
        "name_id": "Penyakit Ginjal Kronis (CKD)",
        "overview": "Penurunan fungsi ginjal progresif, sangat umum pada kucing senior."
      },
      {
        "type": "disease",
        "slug": "cat-hcm",
        "name_id": "Kardiomiopati Hipertrofik (HCM)",
        "overview": "Penebalan otot ventrikel kiri, penyakit jantung paling umum pada kucing; risiko gagal jantung & tromboemboli."
      },
      {
        "type": "disease",
        "slug": "cat-dermatophytosis-ringworm",
        "name_id": "Ringworm (Jamur Kulit)",
        "overview": "Infeksi jamur dermatofita pada kulit/bulu; menular ke hewan lain & manusia."
      }
    ],
    "is_emergency": true,
    "generated_by": "rule_based",
    "disclaimer": "Saran AI bersifat pendukung keputusan klinis dan TIDAK menggantikan pemeriksaan langsung serta penilaian dokter hewan berlisensi. Dosis & produk wajib diverifikasi sesuai spesies, berat badan, dan kondisi pasien.",
    "created_at": "2026-06-19T13:00:57.241551Z"
  },
  "session_active": true
}

```

---

### Single-shot Consult

**POST /api/consult**

**Request:**

```json

{
  "category_slug": "dog",
  "symptoms": [
    "Muntah",
    "Diare",
    "Lemas"
  ],
  "top_k": 3
}

```

**Response:**

```json

{
  "suggestion_type": "symptom_to_disease",
  "summary": "Berdasarkan 3 gejala terdeteksi, kemungkinan teratas: Distemper (Carre) (keyakinan 13%). PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi. Pemeriksaan utama yang disarankan: PCR (swab/urin/darah).",
  "follow_up_questions": [
    "Sudah berapa lama gejala ini berlangsung?",
    "Apakah nafsu makan & minum berubah?",
    "Apakah ada perubahan pada urin/feses?",
    "Adakah riwayat vaksinasi & pengobatan terakhir?"
  ],
  "suggested_diseases": [
    {
      "disease_slug": "dog-canine-distemper",
      "name_id": "Distemper (Carre)",
      "confidence": 0.128,
      "rationale": null,
      "is_emergency": true,
      "source": "ml"
    },
    {
      "disease_slug": "dog-hip-dysplasia",
      "name_id": "Displasia Pinggul",
      "confidence": 0.17,
      "rationale": null,
      "is_emergency": false,
      "source": "ml"
    },
    {
      "disease_slug": "dog-flea-allergy-dermatitis",
      "name_id": "Dermatitis Alergi Kutu",
      "confidence": 0.144,
      "rationale": null,
      "is_emergency": false,
      "source": "ml"
    }
  ],
  "suggested_diagnostics": [
    {
      "name": "PCR (swab/urin/darah)",
      "type": "pcr_molecular",
      "step_order": 1,
      "is_gold_standard": true,
      "expected_finding": "RNA CDV positif",
      "for_disease": "dog-canine-distemper"
    },
    {
      "name": "Pemeriksaan klinis + riwayat vaksin",
      "type": "history_taking",
      "step_order": 2,
      "is_gold_standard": false,
      "expected_finding": "Tanda multisistem pada belum vaksin",
      "for_disease": "dog-canine-distemper"
    },
    {
      "name": "Radiografi panggul (ventrodorsal/PennHIP)",
      "type": "imaging_xray",
      "step_order": 2,
      "is_gold_standard": true,
      "expected_finding": "Subluksasi, remodeling, osteofit",
      "for_disease": "dog-hip-dysplasia"
    },
    {
      "name": "Pemeriksaan ortopedi (Ortolani sign)",
      "type": "physical_exam",
      "step_order": 1,
      "is_gold_standard": false,
      "expected_finding": "Laxity sendi, nyeri ekstensi",
      "for_disease": "dog-hip-dysplasia"
    },
    {
      "name": "Flea combing",
      "type": "physical_exam",
      "step_order": 1,
      "is_gold_standard": true,
      "expected_finding": "Kutu/flea dirt ditemukan",
      "for_disease": "dog-flea-allergy-dermatitis"
    },
    {
      "name": "Sitologi kulit (infeksi sekunder)",
      "type": "cytology",
      "step_order": 2,
      "is_gold_standard": false,
      "expected_finding": "Bakteri/ragi pada pioderma sekunder",
      "for_disease": "dog-flea-allergy-dermatitis"
    }
  ],
  "suggested_treatments": [
    {
      "name": "Terapi suportif distemper",
      "type": "supportive_care",
      "line_of_therapy": 1,
      "procedure_steps": "1) Cairan & nutrisi. 2) Antibiotik cegah infeksi sekunder. 3) Antikonvulsan bila kejang. 4) Nebulisasi & fisioterapi dada. 5) Isolasi.",
      "recommendation": "Tidak ada antivirus spesifik; fokus suportif + cegah komplikasi sekunder.",
      "for_disease": "dog-canine-distemper"
    },
    {
      "name": "Manajemen konservatif osteoarthritis",
      "type": "pharmacological",
      "line_of_therapy": 1,
      "procedure_steps": "1) Kontrol berat badan. 2) NSAID untuk nyeri/inflamasi. 3) Suplemen sendi. 4) Fisioterapi & latihan low-impact (renang). 5) Manajemen lingkungan (alas empuk, hindari lantai licin).",
      "recommendation": "Prioritaskan penurunan berat badan + NSAID jangka terkontrol; evaluasi fungsi hati/ginjal sebelum NSAID panjang.",
      "for_disease": "dog-hip-dysplasia"
    },
    {
      "name": "Koreksi bedah (FHO / Total Hip Replacement)",
      "type": "surgical",
      "line_of_therapy": 2,
      "procedure_steps": "FHO (femoral head ostectomy) pada anjing kecil/menengah; THR (total hip replacement) untuk kasus berat anjing besar.",
      "recommendation": "Rujuk ke spesialis bedah ortopedi bila nyeri tidak terkontrol konservatif.",
      "for_disease": "dog-hip-dysplasia"
    },
    {
      "name": "Kontrol kutu + manajemen gatal",
      "type": "parasite_control",
      "line_of_therapy": 1,
      "procedure_steps": "1) Antiparasit cepat-bunuh + pencegahan bulanan. 2) Perlakukan lingkungan (vakum, cuci alas). 3) Kontrol gatal (kortikosteroid jangka pendek / oclacitinib). 4) Antibiotik bila pioderma sekunder.",
      "recommendation": "Treat semua hewan di rumah & lingkungan; konsistensi pencegahan adalah kunci.",
      "for_disease": "dog-flea-allergy-dermatitis"
    }
  ],
  "suggested_products": [
    {
      "name": "Antibiotik spektrum luas (Doxycycline/Amoxiclav)",
      "kind": "medication",
      "active_ingredient": "Doxycycline",
      "route": "oral",
      "dosage_guide": "5-10 mg/kg",
      "cautions": "Untuk infeksi sekunder.",
      "safety_flag": null
    },
    {
      "name": "Phenobarbital / Diazepam",
      "kind": "medication",
      "active_ingredient": "Phenobarbital",
      "route": "oral/IV",
      "dosage_guide": "Untuk kontrol kejang",
      "cautions": "Monitor sedasi & hati.",
      "safety_flag": null
    },
    {
      "name": "Carprofen (Rimadyl)",
      "kind": "medication",
      "active_ingredient": "Carprofen",
      "route": "oral",
      "dosage_guide": "4.4 mg/kg/hari (terbagi)",
      "cautions": "Monitor GI & hati; jangan kombinasi dengan steroid.",
      "safety_flag": null
    },
    {
      "name": "Glucosamine + Chondroitin",
      "kind": "supplement",
      "active_ingredient": "Glucosamine HCl, Chondroitin sulfate",
      "route": "oral",
      "dosage_guide": "Sesuai berat badan",
      "cautions": "Onset lambat (minggu).",
      "safety_flag": null
    },
    {
      "name": "Omega-3 (EPA/DHA)",
      "kind": "supplement",
      "active_ingredient": "Fish oil",
      "route": "oral",
      "dosage_guide": "Dosis anti-inflamasi sesuai BB",
      "cautions": "Hati-hati pankreatitis.",
      "safety_flag": null
    },
    {
      "name": "Isoxazoline (Afoxolaner/Fluralaner)",
      "kind": "antiparasitic",
      "active_ingredient": "Fluralaner",
      "route": "oral",
      "dosage_guide": "Sesuai BB, tiap 1-3 bulan",
      "cautions": "Hati-hati riwayat kejang.",
      "safety_flag": null
    },
    {
      "name": "Oclacitinib (Apoquel)",
      "kind": "medication",
      "active_ingredient": "Oclacitinib",
      "route": "oral",
      "dosage_guide": "0.4-0.6 mg/kg BID lalu SID",
      "cautions": "Tidak untuk <12 bulan.",
      "safety_flag": null
    },
    {
      "name": "Spot-on lingkungan / IGR",
      "kind": "antiparasitic",
      "active_ingredient": "Insect growth regulator",
      "route": "lingkungan",
      "dosage_guide": "Sesuai label",
      "cautions": "Jauhkan dari ikan/kucing saat aplikasi.",
      "safety_flag": null
    }
  ],
  "red_flags": [],
  "safety_warnings": [
    "Data edukatif untuk mendukung keputusan klinis. Diagnosa & resep final wajib oleh dokter hewan berlisensi. Dosis adalah panduan umum, sesuaikan dengan kondisi pasien.",
    "Antibiotik spektrum luas (Doxycycline/Amoxiclav): Untuk infeksi sekunder.",
    "Phenobarbital / Diazepam: Monitor sedasi & hati.",
    "Carprofen (Rimadyl): Monitor GI & hati; jangan kombinasi dengan steroid.",
    "Glucosamine + Chondroitin: Onset lambat (minggu).",
    "Omega-3 (EPA/DHA): Hati-hati pankreatitis.",
    "Isoxazoline (Afoxolaner/Fluralaner): Hati-hati riwayat kejang.",
    "Oclacitinib (Apoquel): Tidak untuk <12 bulan.",
    "Spot-on lingkungan / IGR: Jauhkan dari ikan/kucing saat aplikasi.",
    "xylitol: Toksik untuk anjing (hipoglikemia/gagal hati).",
    "permethrin: Umumnya aman anjing, tetapi JANGAN aplikasikan ke kucing serumah."
  ],
  "references": [
    {
      "type": "disease",
      "slug": "dog-canine-distemper",
      "name_id": "Distemper (Carre)",
      "overview": "Virus multisistem menyerang saluran napas, cerna, dan saraf; sering fatal pada anak anjing."
    },
    {
      "type": "disease",
      "slug": "dog-hip-dysplasia",
      "name_id": "Displasia Pinggul",
      "overview": "Kelainan perkembangan sendi panggul (acetabulum-femur tidak pas) menyebabkan osteoarthritis & nyeri."
    },
    {
      "type": "disease",
      "slug": "dog-flea-allergy-dermatitis",
      "name_id": "Dermatitis Alergi Kutu",
      "overview": "Reaksi hipersensitivitas terhadap air liur kutu menyebabkan gatal hebat & dermatitis."
    }
  ],
  "is_emergency": true,
  "generated_by": "rule_based",
  "disclaimer": "Saran AI bersifat pendukung keputusan klinis dan TIDAK menggantikan pemeriksaan langsung serta penilaian dokter hewan berlisensi. Dosis & produk wajib diverifikasi sesuai spesies, berat badan, dan kondisi pasien.",
  "created_at": "2026-06-19T13:00:57.329513Z"
}

```

---

### ML Predict

**POST /ml/predict**

**Request:**

```json

{
  "category_slug": "cat",
  "symptoms": [
    "Muntah hebat",
    "Diare berdarah"
  ],
  "top_k": 3
}

```

**Response:**

```json

{
  "category_slug": "cat",
  "predictions": [
    {
      "disease_slug": "cat-fpv-panleukopenia",
      "confidence": 0.4067,
      "name_id": "Panleukopenia (Distemper Kucing)",
      "is_emergency": true
    },
    {
      "disease_slug": "cat-hcm",
      "confidence": 0.2667,
      "name_id": "Kardiomiopati Hipertrofik (HCM)",
      "is_emergency": false
    },
    {
      "disease_slug": "cat-dermatophytosis-ringworm",
      "confidence": 0.24,
      "name_id": "Ringworm (Jamur Kulit)",
      "is_emergency": false
    }
  ]
}

```

---

### OpenAPI Schema

**GET /openapi.json**

**Response:**

```json

{
  "info": {
    "title": "Ekosistem Satwa Veterinary ML & AI API",
    "description": "Sumber data + ML + AI wrapping untuk dukungan vets, klinik & petshop. Mencakup data master, prediksi ML, konsultasi multimodal, dan learning loop.",
    "version": "0.3.0"
  },
  "paths_count": 56
}

```

---
