#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Expand knowledge base for remaining species: rabbit, hamster, poultry, fish,
reptile, amphibian, ferret, guinea_pig, exotic_others
"""

import json
import os

CLINICAL_DIR = '/app/data/clinical'

EXPANSIONS = {
    "diseases_rabbits.json": [
        {"slug": "rabbit-gi-stasis", "name": "Gastrointestinal Stasis (GI Stasis)", "name_id": "GI Stasis (Macet Pencernaan)",
         "etiology": "digestive_disorder", "body_system": "digestive", "is_contagious": False, "is_zoonotic": False,
         "default_severity": "critical", "is_emergency": True,
         "overview": "Kondisi darurat dimana motilitas gastrointestinal berhenti total. Penyebab kematian nomor satu pada kelinci.",
         "causes": "Diet rendah serat, stres, nyeri, dehidrasi, penyakit gigi, perubahan diet mendadak, hairball.",
         "prevention": "Diet tinggi serat (timothy hay 80%), air minum cukup, exercise teratur, hindari stres, perawatan gigi rutin.",
         "prognosis": "Baik dengan penanganan cepat; mortalitas tinggi jika terlambat (>48 jam).",
         "symptoms": [
             {"name": "Anorexia", "name_id": "Tidak mau makan", "body_system": "digestive", "frequency": "very_high"},
             {"name": "Reduced fecal output", "name_id": "Kotoran sedikit/kecil", "body_system": "digestive", "frequency": "very_high"},
             {"name": "Lethargy", "name_id": "Lemas", "body_system": "systemic", "frequency": "very_high"},
             {"name": "Bruxism (teeth grinding)", "name_id": "Gertakan gigi (nyeri)", "body_system": "digestive", "frequency": "high"},
             {"name": "Abdominal distension", "name_id": "Perut kembung", "body_system": "digestive", "frequency": "high"},
             {"name": "Dehydration", "name_id": "Dehidrasi", "body_system": "systemic", "frequency": "high"},
             {"name": "Hypothermia", "name_id": "Hipotermia", "body_system": "systemic", "frequency": "moderate", "is_red_flag": True},
             {"name": "Diarrhea or no feces", "name_id": "Diare atau tidak ada feses", "body_system": "digestive", "frequency": "moderate"},
         ],
         "diagnostics": [
             {"name": "Abdominal radiography", "name_id": "Radiografi abdomen", "category": "imaging", "sensitivity": "high"},
             {"name": "Abdominal ultrasound", "name_id": "USG abdomen", "category": "imaging", "sensitivity": "high"},
             {"name": "Auscultation borborygmi", "name_id": "Auskultasi borborygmi", "category": "physical", "sensitivity": "moderate"},
         ],
         "treatments": [
             {"type": "supportive_care", "name": "Rehidrasi", "protocol": "Lactated Ringer's 100-150 mL/kg SC/IV q24h"},
             {"type": "pharmacological", "name": "Prokinetik", "protocol": "Metoclopramide 0.5 mg/kg SC q8h atau cisapride 0.5 mg/kg PO q8-12h"},
             {"type": "pharmacological", "name": "Analgesik", "protocol": "Meloxicam 0.3-0.6 mg/kg SC q24h, buprenorphine 0.01-0.05 mg/kg IV q8h"},
             {"type": "supportive_care", "name": "Syringe feeding", "protocol": "Critical Care (Oxbow) 15-30 mL/kg q6-8h via syringe"},
             {"type": "supportive_care", "name": "Massage abdomen", "protocol": "Pijat perut lembut, exercise ringan untuk stimulasi motilitas"},
         ],
         "medications": [
             {"name": "Metoclopramide", "category": "prokinetic", "dosage": "0.5 mg/kg SC q8h", "route": "SC", "contraindications": ["GI obstruction"]},
             {"name": "Meloxicam", "category": "NSAID", "dosage": "0.3-0.6 mg/kg SC q24h", "route": "SC", "contraindications": ["Renal disease", "Dehydration"]},
             {"name": "Buprenorphine", "category": "analgesic", "dosage": "0.01-0.05 mg/kg IV q8h", "route": "IV", "contraindications": []},
             {"name": "Simethicone", "category": "antigas", "dosage": "20-40 mg/kg PO q8h", "route": "PO", "contraindications": []},
         ]},
        {"slug": "rabbit-dental-disease", "name": "Rabbit Dental Disease (Malocclusion)", "name_id": "Penyakit Gigi Kelinci (Maloklusi)",
         "etiology": "genetic_acquired", "body_system": "digestive", "is_contagious": False, "is_zoonotic": False,
         "default_severity": "moderate", "is_emergency": False,
         "overview": "Pertumbuhan gigi berlebihan akibat maloklusi. Sangat umum pada kelinci peliharaan karena diet kurang serat.",
         "causes": "Diet rendah serat (kurang hay), predisposisi genetik (ras lop, dwarf), trauma, abses gigi.",
         "prevention": "Diet 80% timothy hay, mainan kunyah, periksa gigi rutin, hindari diet pelet berlebihan.",
         "prognosis": "Baik dengan koreksi gigi rutin (4-8 minggu) dan perubahan diet.",
         "symptoms": [
             {"name": "Anorexia", "name_id": "Tidak mau makan", "body_system": "digestive", "frequency": "very_high"},
             {"name": "Weight loss", "name_id": "Penurunan berat badan", "body_system": "systemic", "frequency": "high"},
             {"name": "Drooling/slobbers", "name_id": "Ngeces", "body_system": "digestive", "frequency": "high"},
             {"name": "Bruxism", "name_id": "Gertakan gigi", "body_system": "digestive", "frequency": "high"},
             {"name": "Facial swelling", "name_id": "Pembengkakan wajah", "body_system": "digestive", "frequency": "moderate"},
             {"name": "Epiphora (excessive tearing)", "name_id": "Mata berair", "body_system": "ophthalmic", "frequency": "moderate"},
             {"name": "Nasal discharge", "name_id": "Leleran hidung", "body_system": "respiratory", "frequency": "moderate"},
             {"name": "Preference for soft food", "name_id": "Hanya mau makanan lunak", "body_system": "digestive", "frequency": "high"},
         ],
         "diagnostics": [
             {"name": "Oral exam under sedation", "name_id": "Pemeriksaan oral sedasi", "category": "physical", "sensitivity": "high"},
             {"name": "Skull radiography", "name_id": "Radiografi kepala", "category": "imaging", "sensitivity": "high"},
             {"name": "CT scan head", "name_id": "CT scan kepala", "category": "imaging", "sensitivity": "very_high"},
         ],
         "treatments": [
             {"type": "surgical", "name": "Burring/correction maloklusi", "protocol": "Bur gigi dengan dental bur under sedation, koreksi spur/taji"},
             {"type": "surgical", "name": "Ekstraksi gigi", "protocol": "Ekstraksi gigi yang bermasalah parah (insisor/premolar)"},
             {"type": "dietary", "name": "Diet korektif", "protocol": "Timothy hay unlimited, kurangi pelet, sayuran hijau, mainan kunyah"},
             {"type": "pharmacological", "name": "Analgesik", "protocol": "Meloxicam 0.3-0.6 mg/kg PO q24h x 3-5 hari post-burring"},
         ],
         "medications": [
             {"name": "Meloxicam", "category": "NSAID", "dosage": "0.3-0.6 mg/kg PO q24h", "route": "PO", "contraindications": []},
             {"name": "Enrofloxacin", "category": "antibiotic", "dosage": "10 mg/kg PO q12h", "route": "PO", "contraindications": []},
         ]},
        {"slug": "rabbit-pasteurellosis", "name": "Pasteurellosis (Snuffles)", "name_id": "Pasteurellosis (Snuffles)",
         "etiology": "infectious_bacterial", "body_system": "respiratory", "is_contagious": True, "is_zoonotic": False,
         "default_severity": "moderate", "is_emergency": False,
         "overview": "Infeksi bakteri Pasteurella multocida, penyebab utama respiratory disease pada kelinci. Dapat menjadi kronis.",
         "causes": "Pasteurella multocida, bakteri gram negatif. Transmisi kontak langsung, aerosol, fomites.",
         "prevention": "Hindari stres, ventilasi baik, karantina kelinci baru, hindari overcrowding.",
         "prognosis": "Baik untuk kasus akut; kasus kronis memerlukan manajemen jangka panjang.",
         "symptoms": [
             {"name": "Nasal discharge", "name_id": "Leleran hidung", "body_system": "respiratory", "frequency": "very_high"},
             {"name": "Sneezing", "name_id": "Bersin", "body_system": "respiratory", "frequency": "very_high"},
             {"name": "Ocular discharge", "name_id": "Leleran mata", "body_system": "ophthalmic", "frequency": "high"},
             {"name": "Dyspnea", "name_id": "Sesak napas", "body_system": "respiratory", "frequency": "moderate"},
             {"name": "Head tilt/torticollis", "name_id": "Kepala miring", "body_system": "neurologic", "frequency": "moderate"},
             {"name": "Abscess subcutaneous", "name_id": "Abses subkutan", "body_system": "integumentary", "frequency": "moderate"},
             {"name": "Anorexia", "name_id": "Tidak mau makan", "body_system": "digestive", "frequency": "moderate"},
         ],
         "diagnostics": [
             {"name": "Culture nasal swab", "name_id": "Kultur swab hidung", "category": "laboratory", "sensitivity": "high"},
             {"name": "PCR Pasteurella", "name_id": "PCR Pasteurella", "category": "molecular", "sensitivity": "very_high"},
             {"name": "Radiography thorax/skull", "name_id": "Radiografi toraks/kepala", "category": "imaging", "sensitivity": "moderate"},
         ],
         "treatments": [
             {"type": "pharmacological", "name": "Antibiotik", "protocol": "Enrofloxacin 10 mg/kg PO q12h x 14-30 hari atau doxycycline 5 mg/kg PO q12h"},
             {"type": "supportive_care", "name": "Nebulisasi", "protocol": "Saline + gentamicin nebulization q12h"},
             {"type": "surgical", "name": "Drainase abses", "protocol": "Incision and drainage, flush dengan chlorhexidine"},
         ],
         "medications": [
             {"name": "Enrofloxacin", "category": "antibiotic", "dosage": "10 mg/kg PO q12h", "route": "PO", "contraindications": []},
             {"name": "Doxycycline", "category": "antibiotic", "dosage": "5 mg/kg PO q12h", "route": "PO", "contraindications": []},
         ]},
        {"slug": "rabbit-uterine-adenocarcinoma", "name": "Uterine Adenocarcinoma", "name_id": "Adenokarsinoma Uterus",
         "etiology": "neoplastic", "body_system": "reproductive", "is_contagious": False, "is_zoonotic": False,
         "default_severity": "moderate", "is_emergency": False,
         "overview": "Tumor uterus paling umum pada kelinci betina tidak steril. Insidensi 50-80% pada betina >3 tahun.",
         "causes": "Paparan hormon estrogen berulang, predisposisi genetik, tidak steril.",
         "prevention": "Sterilisasi (OVH) sebelum 2 tahun, idealnya 4-6 bulan.",
         "prognosis": "Sangat baik jika OVH dini; metastasis lanjut prognosis buruk.",
         "symptoms": [
             {"name": "Hematuria", "name_id": "Kencing darah", "body_system": "reproductive", "frequency": "very_high"},
             {"name": "Abdominal mass", "name_id": "Benjolan perut", "body_system": "reproductive", "frequency": "high"},
             {"name": "Weight loss", "name_id": "Penurunan berat badan", "body_system": "systemic", "frequency": "moderate"},
             {"name": "Lethargy", "name_id": "Lemas", "body_system": "systemic", "frequency": "moderate"},
             {"name": "Dyspnea (if metastatic)", "name_id": "Sesak napas (metastasis)", "body_system": "respiratory", "frequency": "low"},
         ],
         "diagnostics": [
             {"name": "Abdominal ultrasound", "name_id": "USG abdomen", "category": "imaging", "sensitivity": "high"},
             {"name": "Radiography thorax", "name_id": "Radiografi toraks", "category": "imaging", "sensitivity": "moderate"},
             {"name": "Biopsy histopathology", "name_id": "Biopsi histopatologi", "category": "pathology", "sensitivity": "very_high"},
         ],
         "treatments": [
             {"type": "surgical", "name": "OVH (Ovariohisterektomi)", "protocol": "OVH total, termasuk ovarium dan uterus"},
             {"type": "supportive_care", "name": "Manajemen metastasis", "protocol": "Jika sudah metastasis, palliative care"},
         ]},
        {"slug": "rabbit-ec-cuniculi", "name": "Encephalitozoon cuniculi", "name_id": "E. cuniculi (Penyakit Saraf Kelinci)",
         "etiology": "parasitic_protozoal", "body_system": "neurologic", "is_contagious": True, "is_zoonotic": True,
         "default_severity": "moderate", "is_emergency": False,
         "overview": "Infeksi protozoa intraseluler yang menyebabkan penyakit neurologis dan ginjal pada kelinci. Zoonotik pada imunokompromis.",
         "causes": "Encephalitozoon cuniculi, microsporidia. Transmisi oral-fecal, urin, vertikal.",
         "prevention": "Hindari kontak dengan urin terinfeksi, screening serologis, fenbendazole profilaksis.",
         "prognosis": "Baik dengan terapi; beberapa kasus meninggalkan defisit neurologis permanen.",
         "symptoms": [
             {"name": "Head tilt", "name_id": "Kepala miring", "body_system": "neurologic", "frequency": "very_high"},
             {"name": "Ataxia", "name_id": "Inkoordinasi", "body_system": "neurologic", "frequency": "high"},
             {"name": "Nystagmus", "name_id": "Nistagmus", "body_system": "neurologic", "frequency": "high"},
             {"name": "Rolling/tumbling", "name_id": "Berguling-guling", "body_system": "neurologic", "frequency": "moderate"},
             {"name": "Urinary incontinence", "name_id": "Tidak bisa nahan kencing", "body_system": "urinary", "frequency": "moderate"},
             {"name": "Cataracts (phacoclastic uveitis)", "name_id": "Katarak (uveitis)", "body_system": "ophthalmic", "frequency": "moderate"},
             {"name": "Weight loss", "name_id": "Penurunan berat badan", "body_system": "systemic", "frequency": "moderate"},
         ],
         "diagnostics": [
             {"name": "Serology (antibody titer)", "name_id": "Serologi titer antibodi", "category": "serology", "sensitivity": "high"},
             {"name": "PCR urine/CSF", "name_id": "PCR urin/CSF", "category": "molecular", "sensitivity": "very_high"},
             {"name": "Ophthalmic exam", "name_id": "Pemeriksaan mata", "category": "ophthalmic", "sensitivity": "moderate"},
         ],
         "treatments": [
             {"type": "pharmacological", "name": "Fenbendazole", "protocol": "20 mg/kg PO q24h x 28 hari"},
             {"type": "pharmacological", "name": "Anti-inflamasi", "protocol": "Meloxicam 0.3-0.6 mg/kg PO q24h x 7-14 hari"},
             {"type": "supportive_care", "name": "Supportive care", "protocol": "Hand feeding, physiotherapy untuk head tilt"},
         ],
         "medications": [
             {"name": "Fenbendazole", "category": "antiparasitic", "dosage": "20 mg/kg PO q24h x 28 hari", "route": "PO", "contraindications": []},
             {"name": "Meloxicam", "category": "NSAID", "dosage": "0.3-0.6 mg/kg PO q24h", "route": "PO", "contraindications": []},
         ]},
    ],
    "diseases_hamsters.json": [
        {"slug": "hamster-wet-tail", "name": "Proliferative Ileitis (Wet Tail)", "name_id": "Wet Tail (Diare Basah)",
         "etiology": "infectious_bacterial", "body_system": "digestive", "is_contagious": True, "is_zoonotic": False,
         "default_severity": "critical", "is_emergency": True,
         "overview": "Penyakit diare akut berat pada hamster muda. Sangat menular dan sering fatal dalam 24-48 jam.",
         "causes": "Lawsonia intracellularis, diperparah oleh stres, overcrowding, perubahan diet, sanitasi buruk.",
         "prevention": "Hindari stres, karantina hewan baru, sanitasi kandang rutin, diet konsisten.",
         "prognosis": "Guarded; mortalitas tinggi tanpa terapi agresif.",
         "symptoms": [
             {"name": "Watery diarrhea", "name_id": "Diare cair", "body_system": "digestive", "frequency": "very_high"},
             {"name": "Wet perineal area", "name_id": "Area anus basah", "body_system": "digestive", "frequency": "very_high"},
             {"name": "Lethargy", "name_id": "Lemas", "body_system": "systemic", "frequency": "very_high"},
             {"name": "Anorexia", "name_id": "Tidak mau makan", "body_system": "digestive", "frequency": "very_high"},
             {"name": "Hunched posture", "name_id": "Posisi membungkuk", "body_system": "digestive", "frequency": "high"},
             {"name": "Dehydration", "name_id": "Dehidrasi", "body_system": "systemic", "frequency": "very_high"},
             {"name": "Weight loss", "name_id": "Penurunan berat badan", "body_system": "systemic", "frequency": "high"},
         ],
         "diagnostics": [
             {"name": "Fecal PCR Lawsonia", "name_id": "PCR feses Lawsonia", "category": "molecular", "sensitivity": "very_high"},
             {"name": "Fecal floatation", "name_id": "Flotasi feses", "category": "laboratory", "sensitivity": "moderate"},
         ],
         "treatments": [
             {"type": "pharmacological", "name": "Antibiotik", "protocol": "Enrofloxacin 10 mg/kg PO q12h x 7-10 hari"},
             {"type": "supportive_care", "name": "Rehidrasi", "protocol": "SC fluids Lactated Ringer's 10-20 mL/kg q12h"},
             {"type": "supportive_care", "name": "Nutrisi", "protocol": "Syringe feeding Critical Care, probiotik"},
         ],
         "medications": [
             {"name": "Enrofloxacin", "category": "antibiotic", "dosage": "10 mg/kg PO q12h", "route": "PO", "contraindications": []},
             {"name": "Metronidazole", "category": "antibiotic", "dosage": "20 mg/kg PO q12h", "route": "PO", "contraindications": []},
         ]},
        {"slug": "hamster-lymphoma", "name": "Hamster Lymphoma", "name_id": "Limfoma Hamster",
         "etiology": "neoplastic", "body_system": "lymphatic", "is_contagious": False, "is_zoonotic": False,
         "default_severity": "moderate", "is_emergency": False,
         "overview": "Neoplasma limforetikuler umum pada hamster, terutama Syrian hamster. Sering mengenai usus dan kelenjar getah bening.",
         "causes": "Idiopatik, mungkin terkait virus (hamster polyomavirus pada hamster Syrian).",
         "prevention": "Tidak dapat dicegah; breeding selektif.",
         "prognosis": "Guarded; kemoterapi jarang dilakukan pada hamster.",
         "symptoms": [
             {"name": "Abdominal mass", "name_id": "Benjolan perut", "body_system": "lymphatic", "frequency": "very_high"},
             {"name": "Weight loss", "name_id": "Penurunan berat badan", "body_system": "systemic", "frequency": "very_high"},
             {"name": "Lethargy", "name_id": "Lemas", "body_system": "systemic", "frequency": "high"},
             {"name": "Lymphadenopathy", "name_id": "Pembesaran kelenjar getah bening", "body_system": "lymphatic", "frequency": "high"},
             {"name": "Anorexia", "name_id": "Tidak mau makan", "body_system": "digestive", "frequency": "high"},
         ],
         "diagnostics": [
             {"name": "FNA cytology", "name_id": "FNA sitologi", "category": "pathology", "sensitivity": "high"},
             {"name": "Biopsy histopathology", "name_id": "Biopsi histopatologi", "category": "pathology", "sensitivity": "very_high"},
         ],
         "treatments": [
             {"type": "supportive_care", "name": "Palliative care", "protocol": "Analgesik, nutrisi supportif, kualitas hidup"},
         ]},
        {"slug": "hamster-diabetes", "name": "Hamster Diabetes Mellitus", "name_id": "Diabetes Hamster",
         "etiology": "genetic", "body_system": "endocrine", "is_contagious": False, "is_zoonotic": False,
         "default_severity": "moderate", "is_emergency": False,
         "overview": "Umum pada Chinese hamster dan Campbell's dwarf hamster. Predisposisi genetik kuat.",
         "causes": "Mutasi genetik, diet tinggi gula/karbohidrat, obesitas.",
         "prevention": "Diet rendah gula, hindari buah manis, kontrol berat badan.",
         "prognosis": "Baik dengan manajemen diet.",
         "symptoms": [
             {"name": "Polyuria", "name_id": "Sering kencing", "body_system": "urinary", "frequency": "very_high"},
             {"name": "Polydipsia", "name_id": "Sering minum", "body_system": "systemic", "frequency": "very_high"},
             {"name": "Weight loss", "name_id": "Penurunan berat badan", "body_system": "systemic", "frequency": "high"},
             {"name": "Lethargy", "name_id": "Lemas", "body_system": "systemic", "frequency": "high"},
         ],
         "diagnostics": [
             {"name": "Blood glucose", "name_id": "Gula darah", "category": "laboratory", "sensitivity": "high"},
             {"name": "Urinalysis glucose", "name_id": "Urinalisis glukosa", "category": "laboratory", "sensitivity": "high"},
         ],
         "treatments": [
             {"type": "dietary", "name": "Diet rendah gula", "protocol": "Hindari buah manis, seed mix rendah gula, sayuran segar"},
         ]},
    ],
    "diseases_poultry.json": [
        {"slug": "poultry-avian-influenza", "name": "Avian Influenza (Bird Flu)", "name_id": "Flu Burung (Avian Influenza)",
         "etiology": "infectious_viral", "body_system": "respiratory", "is_contagious": True, "is_zoonotic": True,
         "default_severity": "critical", "is_emergency": True,
         "overview": "Penyakit virus sangat menular pada unggas. Strain H5N1 dan H7N9 bersifat zoonotik dengan mortalitas tinggi pada manusia.",
         "causes": "Influenza A virus (H5N1, H7N9, H9N2). Transmisi kontak langsung, fomites, aerosol, feces.",
         "prevention": "Biosekuriti ketat, vaksinasi (strain tertentu), surveilans aktif, pelaporan wajib ke otoritas.",
         "prognosis": "Mortalitas tinggi pada strain patogen; depopulasi sering diperlukan.",
         "symptoms": [
             {"name": "Sudden death", "name_id": "Kematian mendadak", "body_system": "systemic", "frequency": "very_high"},
             {"name": "Respiratory distress", "name_id": "Sesak napas", "body_system": "respiratory", "frequency": "very_high"},
             {"name": "Cyanosis comb/wattles", "name_id": "Sianosis jengger", "body_system": "integumentary", "frequency": "high"},
             {"name": "Swollen head/face", "name_id": "Kepala bengkak", "body_system": "integumentary", "frequency": "high"},
             {"name": "Diarrhea", "name_id": "Diare", "body_system": "digestive", "frequency": "high"},
             {"name": "Egg drop", "name_id": "Produksi telur turun", "body_system": "reproductive", "frequency": "very_high"},
             {"name": "Neurologic signs", "name_id": "Tanda neurologis", "body_system": "neurologic", "frequency": "moderate"},
         ],
         "diagnostics": [
             {"name": "RT-PCR avian influenza", "name_id": "RT-PCR AI", "category": "molecular", "sensitivity": "very_high"},
             {"name": "Virus isolation (egg culture)", "name_id": "Isolasi virus", "category": "laboratory", "sensitivity": "very_high"},
         ],
         "treatments": [
             {"type": "supportive_care", "name": "Tidak ada terapi spesifik", "protocol": "Supportive care; pelaporan wajib; depopulasi pada wabah"},
         ]},
        {"slug": "poultry-marek-disease", "name": "Marek's Disease", "name_id": "Penyakit Marek",
         "etiology": "infectious_viral", "body_system": "neurologic", "is_contagious": True, "is_zoonotic": False,
         "default_severity": "moderate", "is_emergency": False,
         "overview": "Penyakit herpesvirus pada ayam yang menyebabkan limfoma, kelumpuhan, dan kematian. Sangat menular.",
         "causes": "Marek's disease virus (MDV), herpesvirus. Transmisi aerosol dari feather follicle.",
         "prevention": "Vaksinasi (HVT, Rispens, SB-1) pada DOC (day-old chick).",
         "prognosis": "Vaksinasi efektif; tanpa vaksin mortalitas tinggi.",
         "symptoms": [
             {"name": "Paralysis legs/wings", "name_id": "Lumpuh kaki/sayap", "body_system": "neurologic", "frequency": "very_high"},
             {"name": "Weight loss", "name_id": "Penurunan berat badan", "body_system": "systemic", "frequency": "high"},
             {"name": "Visceral tumors", "name_id": "Tumor organ dalam", "body_system": "lymphatic", "frequency": "high"},
             {"name": "Eye color change (gray eye)", "name_id": "Perubahan warna mata", "body_system": "ophthalmic", "frequency": "moderate"},
             {"name": "Death", "name_id": "Kematian", "body_system": "systemic", "frequency": "high"},
         ],
         "diagnostics": [
             {"name": "Necropsy histopathology", "name_id": "Nekropsi histopatologi", "category": "pathology", "sensitivity": "very_high"},
             {"name": "PCR MDV", "name_id": "PCR MDV", "category": "molecular", "sensitivity": "very_high"},
         ],
         "treatments": [
             {"type": "biological", "name": "Vaksinasi", "protocol": "Vaksin HVT/Rispens pada DOC"},
         ]},
        {"slug": "poultry-coccidiosis", "name": "Avian Coccidiosis", "name_id": "Koksidiosis Unggas",
         "etiology": "parasitic_protozoal", "body_system": "digestive", "is_contagious": True, "is_zoonotic": False,
         "default_severity": "moderate", "is_emergency": False,
         "overview": "Penyakit protozoa usus sangat umum pada unggas muda. Menyebabkan diare berdarah, penurunan produksi, dan mortalitas.",
         "causes": "Eimeria spp. (E. tenella, E. necatrix, E. acervulina). Transmisi fecal-oral, oocyst tahan lingkungan.",
         "prevention": "Manajemen litter kering, vaksinasi (koksidiosis vaccine), anticoccidial feed additive.",
         "prognosis": "Baik dengan terapi dan manajemen; wabah berat dapat menyebabkan mortalitas tinggi.",
         "symptoms": [
             {"name": "Bloody diarrhea", "name_id": "Diare berdarah", "body_system": "digestive", "frequency": "very_high"},
             {"name": "Weight loss", "name_id": "Penurunan berat badan", "body_system": "systemic", "frequency": "high"},
             {"name": "Lethargy", "name_id": "Lemas", "body_system": "systemic", "frequency": "high"},
             {"name": "Ruffled feathers", "name_id": "Bulu kusam mengembang", "body_system": "integumentary", "frequency": "high"},
             {"name": "Decreased egg production", "name_id": "Produksi telur turun", "body_system": "reproductive", "frequency": "high"},
             {"name": "Death", "name_id": "Kematian", "body_system": "systemic", "frequency": "moderate"},
         ],
         "diagnostics": [
             {"name": "Fecal floatation oocyst", "name_id": "Flotasi feses oocyst", "category": "laboratory", "sensitivity": "high"},
             {"name": "Necropsy intestinal lesions", "name_id": "Nekropsi lesi usus", "category": "pathology", "sensitivity": "high"},
         ],
         "treatments": [
             {"type": "pharmacological", "name": "Anticoccidial", "protocol": "Amprolium 0.012% in water x 5-7 hari atau toltrazuril 7 mg/kg PO"},
             {"type": "supportive_care", "name": "Manajemen", "protocol": "Litter kering, vitamin A & K, probiotik"},
         ],
         "medications": [
             {"name": "Amprolium", "category": "anticoccidial", "dosage": "0.012% in drinking water x 5-7 hari", "route": "oral_water", "contraindications": []},
             {"name": "Toltrazuril", "category": "anticoccidial", "dosage": "7 mg/kg PO", "route": "PO", "contraindications": []},
         ]},
    ],
    "diseases_fish.json": [
        {"slug": "fish-ichthyophthirius", "name": "Ichthyophthirius multifiliis (Ich)", "name_id": "Ich (Bintik Putih)",
         "etiology": "parasitic_protozoal", "body_system": "integumentary", "is_contagious": True, "is_zoonotic": False,
         "default_severity": "moderate", "is_emergency": False,
         "overview": "Penyakit parasit paling umum pada ikan air tawar. Protozoa menembus kulit dan insang, menyebabkan bintik putih khas.",
         "causes": "Ichthyophthirius multifiliis, protozoa ciliate. Siklus hidup: trofont (pada ikan) → tomont (di lingkungan) → theront (infektif).",
         "prevention": "Karantina ikan baru, karantina 2-4 minggu, hindari stres, kualitas air optimal.",
         "prognosis": "Baik dengan deteksi dini dan terapi; wabah berat dapat menyebabkan mortalitas tinggi.",
         "symptoms": [
             {"name": "White spots on skin/fins", "name_id": "Bintik putih di kulit/sirip", "body_system": "integumentary", "frequency": "very_high"},
             {"name": "Flashing/rubbing", "name_id": "Menggosok badan", "body_system": "behavioral", "frequency": "very_high"},
             {"name": "Respiratory distress", "name_id": "Sesak napas", "body_system": "respiratory", "frequency": "high"},
             {"name": "Lethargy", "name_id": "Lemas", "body_system": "systemic", "frequency": "high"},
             {"name": "Anorexia", "name_id": "Tidak mau makan", "body_system": "digestive", "frequency": "high"},
             {"name": "Clamped fins", "name_id": "Sirip menguncup", "body_system": "integumentary", "frequency": "high"},
         ],
         "diagnostics": [
             {"name": "Skin scrape microscopy", "name_id": "Kerokan kulit mikroskopi", "category": "laboratory", "sensitivity": "very_high"},
             {"name": "Gill biopsy microscopy", "name_id": "Biopsi insang mikroskopi", "category": "laboratory", "sensitivity": "very_high"},
         ],
         "treatments": [
             {"type": "pharmacological", "name": "Malachite green + formalin", "protocol": "0.05 mg/L malachite green + 15 mg/L formalin, q48h x 3 treatments"},
             {"type": "pharmacological", "name": "Salt bath", "protocol": "NaCl 0.3-0.5% prolonged bath atau 3% short bath 30-60 detik"},
             {"type": "supportive_care", "name": "Raise temperature", "protocol": "Naikkan suhu ke 30°C selama 3-5 hari untuk mempercepat siklus"},
         ],
         "medications": [
             {"name": "Malachite green", "category": "antiparasitic", "dosage": "0.05 mg/L q48h", "route": "bath", "contraindications": ["Tetras"]},
             {"name": "Formalin", "category": "antiparasitic", "dosage": "15-25 mg/L bath", "route": "bath", "contraindications": []},
         ]},
        {"slug": "fish-fin-rot", "name": "Fin Rot (Bacterial)", "name_id": "Busuk Sirip (Bakterial)",
         "etiology": "infectious_bacterial", "body_system": "integumentary", "is_contagious": True, "is_zoonotic": False,
         "default_severity": "mild", "is_emergency": False,
         "overview": "Infeksi bakteri pada sirip dan ekor ikan. Sering sekunder dari kualitas air buruk atau stres.",
         "causes": "Aeromonas, Pseudomonas, Flexibacter columnaris. Faktor predisposisi: kualitas air buruk, stres, cedera.",
         "prevention": "Kualitas air optimal, karantina, hindari overcrowding, diet seimbang.",
         "prognosis": "Sangat baik dengan koreksi kualitas air dan terapi.",
         "symptoms": [
             {"name": "Ragged/disintegrating fins", "name_id": "Sirip robek/hancur", "body_system": "integumentary", "frequency": "very_high"},
             {"name": "White/red edge on fins", "name_id": "Tepi sirip putih/merah", "body_system": "integumentary", "frequency": "high"},
             {"name": "Lethargy", "name_id": "Lemas", "body_system": "systemic", "frequency": "moderate"},
             {"name": "Anorexia", "name_id": "Tidak mau makan", "body_system": "digestive", "frequency": "moderate"},
         ],
         "diagnostics": [
             {"name": "Skin scrape microscopy", "name_id": "Kerokan kulit mikroskopi", "category": "laboratory", "sensitivity": "moderate"},
             {"name": "Bacterial culture", "name_id": "Kultur bakteri", "category": "laboratory", "sensitivity": "high"},
         ],
         "treatments": [
             {"type": "pharmacological", "name": "Antibiotik", "protocol": "Oxytetracycline 50-100 mg/L bath x 5 hari atau melafix 5 mL/40L"},
             {"type": "supportive_care", "name": "Koreksi kualitas air", "protocol": "Water change 25-50%, filter maintenance, parameter optimal"},
         ],
         "medications": [
             {"name": "Oxytetracycline", "category": "antibiotic", "dosage": "50-100 mg/L bath x 5 hari", "route": "bath", "contraindications": []},
             {"name": "Melafix (tea tree oil)", "category": "antiseptic", "dosage": "5 mL/40L q24h", "route": "bath", "contraindications": []},
         ]},
        {"slug": "fish-dropsy", "name": "Dropsy (Ascites)", "name_id": "Dropsy (Perut Bengkak)",
         "etiology": "infectious_bacterial", "body_system": "systemic", "is_contagious": True, "is_zoonotic": False,
         "default_severity": "critical", "is_emergency": True,
         "overview": "Akumulasi cairan dalam rongga tubuh akibat infeksi bakteri sistemik. Prognosis buruk.",
         "causes": "Aeromonas hydrophila, Pseudomonas, Mycobacterium. Gagal ginjal atau hati.",
         "prevention": "Kualitas air optimal, karantina, hindari stres.",
         "prognosis": "Guarded; sulit diobati, sering fatal.",
         "symptoms": [
             {"name": "Abdominal distension", "name_id": "Perut bengkak", "body_system": "systemic", "frequency": "very_high"},
             {"name": "Pinecone scales", "name_id": "Sisik mengembang (pinecone)", "body_system": "integumentary", "frequency": "very_high"},
             {"name": "Exophthalmos (pop-eye)", "name_id": "Mata menonjol", "body_system": "ophthalmic", "frequency": "moderate"},
             {"name": "Lethargy", "name_id": "Lemas", "body_system": "systemic", "frequency": "very_high"},
             {"name": "Anorexia", "name_id": "Tidak mau makan", "body_system": "digestive", "frequency": "very_high"},
         ],
         "diagnostics": [
             {"name": "Abdominal fluid analysis", "name_id": "Analisis cairan abdomen", "category": "laboratory", "sensitivity": "moderate"},
             {"name": "Bacterial culture", "name_id": "Kultur bakteri", "category": "laboratory", "sensitivity": "high"},
         ],
         "treatments": [
             {"type": "pharmacological", "name": "Antibiotik", "protocol": "Kanamycin 10-20 mg/L bath + oxytetracycline 50 mg/L bath"},
             {"type": "supportive_care", "name": "Epsom salt bath", "protocol": "MgSO4 1 tsp/20L untuk mengurangi edema"},
         ]},
    ],
    "diseases_reptiles.json": [
        {"slug": "reptile-metabolic-bone-disease", "name": "Metabolic Bone Disease (MBD)", "name_id": "Penyakit Tulang Metabolik (MBD)",
         "etiology": "nutritional", "body_system": "musculoskeletal", "is_contagious": False, "is_zoonotic": False,
         "default_severity": "moderate", "is_emergency": False,
         "overview": "Penyakit sangat umum pada reptil peliharaan akibat ketidakseimbangan kalsium-fosfor dan defisiensi UVB. Menyebabkan deformitas tulang.",
         "causes": "Defisiensi UVB, rasio Ca:P tidak seimbang, defisiensi vitamin D3, diet kurang kalsium.",
         "prevention": "UVB lamp 10-12 jam/hari, suplemen kalsium + D3, diet seimbang (Ca:P 2:1).",
         "prognosis": "Baik jika ditangani dini; deformitas permanen jika sudah lanjut.",
         "symptoms": [
             {"name": "Soft jaw/rubber jaw", "name_id": "Rahang lunak", "body_system": "musculoskeletal", "frequency": "very_high"},
             {"name": "Limb deformities", "name_id": "Deformitas kaki", "body_system": "musculoskeletal", "frequency": "high"},
             {"name": "Lethargy", "name_id": "Lemas", "body_system": "systemic", "frequency": "very_high"},
             {"name": "Anorexia", "name_id": "Tidak mau makan", "body_system": "digestive", "frequency": "high"},
             {"name": "Muscle tremors", "name_id": "Tremor otot", "body_system": "neurologic", "frequency": "high"},
             {"name": "Pathologic fractures", "name_id": "Fraktur patologis", "body_system": "musculoskeletal", "frequency": "moderate"},
             {"name": "Spinal curvature", "name_id": "Tulang belakang bengkok", "body_system": "musculoskeletal", "frequency": "moderate"},
         ],
         "diagnostics": [
             {"name": "Radiography", "name_id": "Radiografi", "category": "imaging", "sensitivity": "high"},
             {"name": "Blood Ca:P ratio", "name_id": "Rasio Ca:P darah", "category": "laboratory", "sensitivity": "high"},
         ],
         "treatments": [
             {"type": "supportive_care", "name": "Koreksi UVB", "protocol": "UVB 5.0/10.0 lamp 10-12 jam/hari, jarak 20-30 cm"},
             {"type": "pharmacological", "name": "Suplemen kalsium", "protocol": "Calcium glubionate 100 mg/kg PO q24h + vitamin D3 100 IU/kg PO q7hari"},
             {"type": "pharmacological", "name": "Kalsitonin", "protocol": "Kalsitonin 50 IU/kg IM q24h x 3-5 hari (kasus berat)"},
             {"type": "supportive_care", "name": "Diet korektif", "protocol": "Dusting feeder insects dengan Ca+D3 powder setiap feeding"},
         ],
         "medications": [
             {"name": "Calcium glubionate", "category": "calcium_supplement", "dosage": "100 mg/kg PO q24h", "route": "PO", "contraindications": []},
             {"name": "Vitamin D3", "category": "vitamin", "dosage": "100 IU/kg PO q7hari", "route": "PO", "contraindications": []},
         ]},
        {"slug": "reptile-rti", "name": "Reptile Respiratory Infection", "name_id": "Infeksi Saluran Napas Reptil",
         "etiology": "infectious_bacterial", "body_system": "respiratory", "is_contagious": True, "is_zoonotic": False,
         "default_severity": "moderate", "is_emergency": False,
         "overview": "Infeksi saluran napas umum pada reptil, sering terkait suhu lingkungan tidak adekuat.",
         "causes": "Bakteri (Aeromonas, Pseudomonas, Mycoplasma), jamur, parasit. Faktor predisposisi: suhu terlalu rendah, kelembaban salah, stres.",
         "prevention": "Gradien suhu optimal, kelembaban sesuai spesies, karantina, hindari stres.",
         "prognosis": "Baik dengan koreksi lingkungan dan terapi antibiotik.",
         "symptoms": [
             {"name": "Nasal discharge", "name_id": "Leleran hidung", "body_system": "respiratory", "frequency": "very_high"},
             {"name": "Open mouth breathing", "name_id": "Bernapas dengan mulut terbuka", "body_system": "respiratory", "frequency": "very_high"},
             {"name": "Wheezing", "name_id": "Napas berbunyi", "body_system": "respiratory", "frequency": "high"},
             {"name": "Lethargy", "name_id": "Lemas", "body_system": "systemic", "frequency": "very_high"},
             {"name": "Anorexia", "name_id": "Tidak mau makan", "body_system": "digestive", "frequency": "high"},
             {"name": "Excess saliva/mucus", "name_id": "Lendir berlebihan", "body_system": "respiratory", "frequency": "moderate"},
         ],
         "diagnostics": [
             {"name": "Tracheal wash culture", "name_id": "Kultur trakea", "category": "laboratory", "sensitivity": "high"},
             {"name": "Radiography", "name_id": "Radiografi", "category": "imaging", "sensitivity": "moderate"},
         ],
         "treatments": [
             {"type": "pharmacological", "name": "Antibiotik", "protocol": "Enrofloxacin 5-10 mg/kg IM q24h x 7-14 hari atau ceftazidime 20 mg/kg IM q72h"},
             {"type": "supportive_care", "name": "Koreksi suhu", "protocol": "Naikkan suhu hotspot 2-3°C selama terapi"},
             {"type": "supportive_care", "name": "Nebulisasi", "protocol": "Saline nebulization q12h"},
         ],
         "medications": [
             {"name": "Enrofloxacin", "category": "antibiotic", "dosage": "5-10 mg/kg IM q24h", "route": "IM", "contraindications": []},
             {"name": "Ceftazidime", "category": "antibiotic", "dosage": "20 mg/kg IM q72h", "route": "IM", "contraindications": []},
         ]},
        {"slug": "reptile-dysecdysis", "name": "Dysecdysis (Abnormal Shedding)", "name_id": "Ganti Kulit Tidak Sempurna",
         "etiology": "environmental", "body_system": "integumentary", "is_contagious": False, "is_zoonotic": False,
         "default_severity": "mild", "is_emergency": False,
         "overview": "Kegagalan reptil melepas kulit secara normal. Umum pada iguana, kadal, dan ular dengan kelembaban tidak adekuat.",
         "causes": "Kelembaban terlalu rendah, dehidrasi, nutrisi buruk, ektoparasit, trauma, penyakit sistemik.",
         "prevention": "Kelembaban sesuai spesies, humid hide box, hidrasi cukup, diet seimbang.",
         "prognosis": "Sangat baik dengan koreksi lingkungan.",
         "symptoms": [
             {"name": "Retained shed patches", "name_id": "Kulit lama tersisa", "body_system": "integumentary", "frequency": "very_high"},
             {"name": "Retained spectacles (eye caps)", "name_id": "Selaput mata tersisa", "body_system": "ophthalmic", "frequency": "high"},
             {"name": "Constriction rings on digits", "name_id": "Lingkaran konstriksi di jari", "body_system": "integumentary", "frequency": "moderate"},
             {"name": "Irritability", "name_id": "Mudah stres", "body_system": "behavioral", "frequency": "moderate"},
         ],
         "diagnostics": [
             {"name": "Physical examination", "name_id": "Pemeriksaan fisik", "category": "physical", "sensitivity": "high"},
         ],
         "treatments": [
             {"type": "supportive_care", "name": "Soak in warm water", "protocol": "Rendam air hangat 25-30°C selama 15-20 menit q12-24h"},
             {"type": "supportive_care", "name": "Humidity increase", "protocol": "Mist enclosure 2-3x/hari, humid hide dengan sphagnum moss"},
             {"type": "supportive_care", "name": "Manual removal", "protocol": "Lembabkan lalu lepas perlahan dengan cotton bud; jangan paksa"},
         ]},
    ],
    "diseases_ferret.json": [
        {"slug": "ferret-adrenal-disease", "name": "Adrenal Gland Disease (Hyperadrenocorticism)", "name_id": "Penyakit Adrenal Ferret",
         "etiology": "endocrine", "body_system": "endocrine", "is_contagious": False, "is_zoonotic": False,
         "default_severity": "moderate", "is_emergency": False,
         "overview": "Penyakit endokrin paling umum pada ferret. Produksi hormon seks berlebihan oleh kelenjar adrenal.",
         "causes": "Hiperplasia/adenoma adrenal, terkait fotoperiode tidak alami (pencahayaan buatan).",
         "prevention": "Gelapkan kandang 12-14 jam/hari, hindari cahaya buatan malam hari.",
         "prognosis": "Baik dengan terapi medis atau bedah.",
         "symptoms": [
             {"name": "Bilateral alopecia", "name_id": "Rambut rontok bilateral", "body_system": "integumentary", "frequency": "very_high"},
             {"name": "Pruritus", "name_id": "Gatal", "body_system": "integumentary", "frequency": "high"},
             {"name": "Enlarged vulva (female)", "name_id": "Vulva membesar (betina)", "body_system": "reproductive", "frequency": "very_high"},
             {"name": "Prostatomegaly (male)", "name_id": "Prostat membesar (jantan)", "body_system": "urinary", "frequency": "high"},
             {"name": "Stranguria", "name_id": "Nyeri kencing", "body_system": "urinary", "frequency": "moderate"},
             {"name": "Muscle atrophy", "name_id": "Atrofi otot", "body_system": "musculoskeletal", "frequency": "moderate"},
             {"name": "Lethargy", "name_id": "Lemas", "body_system": "systemic", "frequency": "moderate"},
         ],
         "diagnostics": [
             {"name": "Abdominal ultrasound", "name_id": "USG abdomen", "category": "imaging", "sensitivity": "high"},
             {"name": "Sex hormone panel", "name_id": "Panel hormon seks", "category": "laboratory", "sensitivity": "very_high"},
             {"name": "ACTH stim test", "name_id": "Tes stimulasi ACTH", "category": "laboratory", "sensitivity": "moderate"},
         ],
         "treatments": [
             {"type": "surgical", "name": "Adrenalectomy", "protocol": "Reseksi kelenjar adrenal yang terkena"},
             {"type": "pharmacological", "name": "Deslorelin implant (Suprelorin)", "protocol": "4.7 mg SC implant, efek 6-12 bulan"},
             {"type": "pharmacological", "name": "Melatonin", "protocol": "0.5-1 mg PO q12h, efek terbatas"},
         ],
         "medications": [
             {"name": "Deslorelin (Suprelorin)", "category": "GnRH_agonist", "dosage": "4.7 mg SC implant q6-12 bulan", "route": "SC", "contraindications": []},
             {"name": "Melatonin", "category": "hormone", "dosage": "0.5-1 mg PO q12h", "route": "PO", "contraindications": []},
         ]},
        {"slug": "ferret-insulinoma", "name": "Insulinoma (Pancreatic Beta Cell Tumor)", "name_id": "Insulinoma Ferret",
         "etiology": "neoplastic", "body_system": "endocrine", "is_contagious": False, "is_zoonotic": False,
         "default_severity": "moderate", "is_emergency": True,
         "overview": "Tumor sel beta pankreas yang menghasilkan insulin berlebihan, menyebabkan hipoglikemia. Sangat umum pada ferret >3 tahun.",
         "causes": "Adenoma atau karsinoma sel beta pankreas. Etiologi tidak diketahui.",
         "prevention": "Diet tinggi protein, rendah karbohidrat sederhana, hindari gula.",
         "prognosis": "Baik dengan manajemen medis; survival 12-24 bulan dengan terapi.",
         "symptoms": [
             {"name": "Lethargy", "name_id": "Lemas", "body_system": "systemic", "frequency": "very_high"},
             {"name": "Hypoglycemic collapse", "name_id": "Collapse hipoglikemia", "body_system": "neurologic", "frequency": "high"},
             {"name": "Pawing at mouth", "name_id": "Menggaruk mulut", "body_system": "neurologic", "frequency": "high"},
             {"name": "Staring into space", "name_id": "Menatap kosong", "body_system": "neurologic", "frequency": "high"},
             {"name": "Weight loss", "name_id": "Penurunan berat badan", "body_system": "systemic", "frequency": "high"},
             {"name": "Polyphagia", "name_id": "Lapar berlebihan", "body_system": "digestive", "frequency": "moderate"},
             {"name": "Seizures", "name_id": "Kejang", "body_system": "neurologic", "frequency": "moderate", "is_red_flag": True},
         ],
         "diagnostics": [
             {"name": "Fasting blood glucose", "name_id": "Gula darah puasa", "category": "laboratory", "sensitivity": "high"},
             {"name": "Insulin:glucose ratio", "name_id": "Rasio insulin:glukosa", "category": "laboratory", "sensitivity": "very_high"},
             {"name": "Abdominal ultrasound", "name_id": "USG abdomen", "category": "imaging", "sensitivity": "moderate"},
         ],
         "treatments": [
             {"type": "pharmacological", "name": "Prednisone/prednisolone", "protocol": "0.5-2 mg/kg PO q12h, titrasi berdasarkan glukosa"},
             {"type": "pharmacological", "name": "Diazoxide", "protocol": "5-10 mg/kg PO q12h (second line)"},
             {"type": "surgical", "name": "Partial pancreatectomy", "protocol": "Reseksi nodul pankreas; tidak kuratif jika multiple"},
             {"type": "dietary", "name": "Diet tinggi protein", "protocol": "High protein diet, frequent small meals, hindari gula sederhana"},
         ],
         "medications": [
             {"name": "Prednisone", "category": "corticosteroid", "dosage": "0.5-2 mg/kg PO q12h", "route": "PO", "contraindications": []},
             {"name": "Diazoxide", "category": "antihypoglycemic", "dosage": "5-10 mg/kg PO q12h", "route": "PO", "contraindications": []},
         ]},
        {"slug": "ferret-lymphoma", "name": "Ferret Lymphoma", "name_id": "Limfoma Ferret",
         "etiology": "neoplastic", "body_system": "lymphatic", "is_contagious": False, "is_zoonotic": False,
         "default_severity": "critical", "is_emergency": False,
         "overview": "Neoplasma limforetikuler paling umum pada ferret. Dapat mengenai berbagai organ.",
         "causes": "Idiopatik, mungkin terkait virus (retrovirus ferret).",
         "prevention": "Tidak dapat dicegah.",
         "prognosis": "Guarded; kemoterapi dapat memperpanjang survival 6-12 bulan.",
         "symptoms": [
             {"name": "Lymphadenopathy", "name_id": "Pembesaran kelenjar getah bening", "body_system": "lymphatic", "frequency": "very_high"},
             {"name": "Weight loss", "name_id": "Penurunan berat badan", "body_system": "systemic", "frequency": "very_high"},
             {"name": "Lethargy", "name_id": "Lemas", "body_system": "systemic", "frequency": "very_high"},
             {"name": "Anorexia", "name_id": "Tidak mau makan", "body_system": "digestive", "frequency": "high"},
             {"name": "Splenomegaly", "name_id": "Pembesaran limpa", "body_system": "lymphatic", "frequency": "high"},
             {"name": "Dyspnea (mediastinal mass)", "name_id": "Sesak napas (massa mediastinum)", "body_system": "respiratory", "frequency": "moderate"},
         ],
         "diagnostics": [
             {"name": "FNA cytology", "name_id": "FNA sitologi", "category": "pathology", "sensitivity": "high"},
             {"name": "Biopsy histopathology", "name_id": "Biopsi histopatologi", "category": "pathology", "sensitivity": "very_high"},
             {"name": "CBC + chemistry", "name_id": "CBC + kimia darah", "category": "laboratory", "sensitivity": "moderate"},
         ],
         "treatments": [
             {"type": "pharmacological", "name": "Kemoterapi CHOP", "protocol": "Cyclophosphamide, doxorubicin, vincristine, prednisone"},
             {"type": "pharmacological", "name": "Prednisone palliatif", "protocol": "1-2 mg/kg PO q12h"},
         ]},
    ],
    "diseases_guinea_pig.json": [
        {"slug": "guinea-pig-scurvy", "name": "Vitamin C Deficiency (Scurvy)", "name_id": "Defisiensi Vitamin C (Skorbut)",
         "etiology": "nutritional", "body_system": "systemic", "is_contagious": False, "is_zoonotic": False,
         "default_severity": "moderate", "is_emergency": False,
         "overview": "Marmut tidak dapat mensintesis vitamin C. Defisiensi menyebabkan gangguan kolagen, perdarahan, dan imunosupresi.",
         "causes": "Diet kurang vitamin C (sayuran segar). Kebutuhan: 10-30 mg/kg/hari.",
         "prevention": "Suplemen vitamin C 10-30 mg/kg/hari, sayuran kaya vitamin C (paprika, kale).",
         "prognosis": "Sangat baik dengan suplementasi vitamin C.",
         "symptoms": [
             {"name": "Lethargy", "name_id": "Lemas", "body_system": "systemic", "frequency": "very_high"},
             {"name": "Anorexia", "name_id": "Tidak mau makan", "body_system": "digestive", "frequency": "very_high"},
             {"name": "Weight loss", "name_id": "Penurunan berat badan", "body_system": "systemic", "frequency": "high"},
             {"name": "Joint swelling/pain", "name_id": "Bengkak/nyeri sendi", "body_system": "musculoskeletal", "frequency": "high"},
             {"name": "Hemorrhage (subcutaneous)", "name_id": "Perdarahan bawah kulit", "body_system": "integumentary", "frequency": "moderate"},
             {"name": "Poor coat quality", "name_id": "Bulu kusam", "body_system": "integumentary", "frequency": "high"},
             {"name": "Delayed wound healing", "name_id": "Luka sulit sembuh", "body_system": "integumentary", "frequency": "moderate"},
             {"name": "Dental problems", "name_id": "Masalah gigi", "body_system": "digestive", "frequency": "moderate"},
         ],
         "diagnostics": [
             {"name": "Response to vitamin C therapy", "name_id": "Respon terapi vitamin C", "category": "clinical", "sensitivity": "high"},
             {"name": "Plasma vitamin C level", "name_id": "Kadar vitamin C plasma", "category": "laboratory", "sensitivity": "high"},
         ],
         "treatments": [
             {"type": "pharmacological", "name": "Vitamin C suplementasi", "protocol": "Vitamin C 50 mg/kg SC/PO q24h x 7-14 hari, lalu maintenance 10-30 mg/kg/hari"},
             {"type": "dietary", "name": "Diet korektif", "protocol": "Sayuran segar kaya vitamin C (paprika merah, kale, brokoli) setiap hari"},
         ],
         "medications": [
             {"name": "Vitamin C (ascorbic acid)", "category": "vitamin", "dosage": "50 mg/kg SC/PO q24h loading", "route": "SC/PO", "contraindications": []},
         ]},
        {"slug": "guinea-pig-ovarian-cyst", "name": "Ovarian Cysts", "name_id": "Kista Ovarium Marmut",
         "etiology": "reproductive", "body_system": "reproductive", "is_contagious": False, "is_zoonotic": False,
         "default_severity": "mild", "is_emergency": False,
         "overview": "Kista ovarium sangat umum pada marmut betina dewasa tidak steril. Dapat menyebabkan alopecia dan masalah reproduksi.",
         "causes": "Ketidakseimbangan hormonal, folikel tidak berovulasi.",
         "prevention": "Sterilisasi (OVH) pada usia muda.",
         "prognosis": "Sangat baik dengan OVH.",
         "symptoms": [
             {"name": "Bilateral alopecia", "name_id": "Rambut rontok bilateral", "body_system": "integumentary", "frequency": "very_high"},
             {"name": "Abdominal distension", "name_id": "Perut buncit", "body_system": "reproductive", "frequency": "high"},
             {"name": "Lethargy", "name_id": "Lemas", "body_system": "systemic", "frequency": "moderate"},
             {"name": "Anorexia", "name_id": "Tidak mau makan", "body_system": "digestive", "frequency": "moderate"},
         ],
         "diagnostics": [
             {"name": "Abdominal ultrasound", "name_id": "USG abdomen", "category": "imaging", "sensitivity": "very_high"},
             {"name": "Abdominal radiography", "name_id": "Radiografi abdomen", "category": "imaging", "sensitivity": "moderate"},
         ],
         "treatments": [
             {"type": "surgical", "name": "OVH (Ovariohisterektomi)", "protocol": "OVH total, termasuk ovarium dan uterus"},
             {"type": "pharmacological", "name": "hCG therapy", "protocol": "hCG 1000 IU IM, efek sementara"},
         ]},
        {"slug": "guinea-pig-urinary-stones", "name": "Urinary Stones (Urolithiasis)", "name_id": "Batu Kemih Marmut",
         "etiology": "metabolic", "body_system": "urinary", "is_contagious": False, "is_zoonotic": False,
         "default_severity": "critical", "is_emergency": True,
         "overview": "Batu kalsium oksalat/karbonat pada saluran kemih. Umum pada marmut betina dan jantan. Dapat menyebabkan obstruksi fatal.",
         "causes": "Diet tinggi kalsium, rasio Ca:P tidak seimbang, kurang minum, predisposisi genetik.",
         "prevention": "Diet seimbang kalsium, hindari alfalfa hay (kalsium tinggi), air minum cukup, timothy hay sebagai basis.",
         "prognosis": "Baik dengan koreksi bedah; rekurensi tinggi tanpa perubahan diet.",
         "symptoms": [
             {"name": "Stranguria", "name_id": "Nyeri kencing", "body_system": "urinary", "frequency": "very_high"},
             {"name": "Hematuria", "name_id": "Kencing darah", "body_system": "urinary", "frequency": "very_high"},
             {"name": "Vocalizing when urinating", "name_id": "Menjerit saat kencing", "body_system": "urinary", "frequency": "high"},
             {"name": "Anorexia", "name_id": "Tidak mau makan", "body_system": "digestive", "frequency": "high"},
             {"name": "Lethargy", "name_id": "Lemas", "body_system": "systemic", "frequency": "high"},
             {"name": "Anuria (obstruction)", "name_id": "Tidak bisa kencing", "body_system": "urinary", "frequency": "moderate", "is_red_flag": True},
         ],
         "diagnostics": [
             {"name": "Abdominal radiography", "name_id": "Radiografi abdomen", "category": "imaging", "sensitivity": "high"},
             {"name": "Abdominal ultrasound", "name_id": "USG abdomen", "category": "imaging", "sensitivity": "very_high"},
             {"name": "Urinalysis + sediment", "name_id": "Urinalisis + sedimen", "category": "laboratory", "sensitivity": "moderate"},
         ],
         "treatments": [
             {"type": "surgical", "name": "Cystotomy", "protocol": "Sistotomi untuk mengeluarkan batu kandung kemih"},
             {"type": "supportive_care", "name": "Terapi cairan", "protocol": "IV/SC fluids untuk flush saluran kemih"},
             {"type": "dietary", "name": "Diet korektif", "protocol": "Timothy hay, hindari alfalfa, sayuran rendah kalsium, air banyak"},
             {"type": "pharmacological", "name": "Analgesik", "protocol": "Meloxicam 0.3-0.6 mg/kg PO q24h"},
         ],
         "medications": [
             {"name": "Meloxicam", "category": "NSAID", "dosage": "0.3-0.6 mg/kg PO q24h", "route": "PO", "contraindications": []},
             {"name": "Enrofloxacin", "category": "antibiotic", "dosage": "10 mg/kg PO q12h", "route": "PO", "contraindications": []},
         ]},
    ],
}

def main():
    print("=" * 60)
    print("EXPANDING OTHER SPECIES KNOWLEDGE BASE")
    print("=" * 60)
    
    total_new = 0
    total_updated = 0
    
    for filename, diseases in EXPANSIONS.items():
        filepath = os.path.join(CLINICAL_DIR, filename)
        
        with open(filepath) as f:
            existing = json.load(f)
        
        existing_slugs = {d['slug'] for d in existing['diseases']}
        new_count = 0
        updated_count = 0
        
        for new_disease in diseases:
            if new_disease['slug'] in existing_slugs:
                for i, d in enumerate(existing['diseases']):
                    if d['slug'] == new_disease['slug']:
                        existing['diseases'][i] = new_disease
                        updated_count += 1
                        break
            else:
                existing['diseases'].append(new_disease)
                new_count += 1
        
        with open(filepath, 'w') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        
        print(f"\n{filename}:")
        print(f"  New: {new_count}, Updated: {updated_count}, Total: {len(existing['diseases'])}")
        total_new += new_count
        total_updated += updated_count
    
    print(f"\n{'=' * 60}")
    print(f"TOTAL: {total_new} new, {total_updated} updated")
    print(f"{'=' * 60}")

if __name__ == '__main__':
    main()
