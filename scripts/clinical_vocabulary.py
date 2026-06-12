# -*- coding: utf-8 -*-
"""
Katalog klinis diperluas: penyakit, gejala, dan diagnosa per spesies.

Dipakai oleh catalogs.py untuk memperkaya CLINICAL sebelum generate_dataset.
Setiap penyakit memuat daftar gejala terstruktur (untuk disease_symptoms.csv).
"""
from __future__ import annotations

# Reuse fragments & builder dari catalogs (impor setelah catalogs dimuat — dipanggil dari expand)
import catalogs as C


def S(slug, name_id, body_system, frequency="high", is_red_flag=False, is_pathognomonic=False):
    """Definisi gejala singkat."""
    return {
        "slug": slug,
        "name": name_id,
        "name_id": name_id,
        "body_system": body_system,
        "frequency": frequency,
        "is_red_flag": is_red_flag,
        "is_pathognomonic": is_pathognomonic,
    }


# Gejala umum per sistem (dipakai ulang lintas penyakit)
_COMMON = {
    "digestive": [
        S("vomiting", "Muntah", "digestive", "high"),
        S("diarrhea", "Diare", "digestive", "high"),
        S("anorexia", "Tidak nafsu makan", "digestive", "high"),
        S("abdominal-pain", "Nyeri perut", "digestive", "moderate"),
        S("bloating", "Perut kembung", "digestive", "moderate", True),
        S("dehydration", "Dehidrasi", "systemic", "high", True),
        S("weight-loss", "Berat badan turun", "systemic", "moderate"),
        S("constipation", "Sembelit", "digestive", "moderate"),
        S("regurgitation", "Regurgitasi", "digestive", "moderate"),
        S("melena", "Feses berdarah hitam", "digestive", "high", True),
    ],
    "respiratory": [
        S("coughing", "Batuk", "respiratory", "high"),
        S("sneezing", "Bersin", "respiratory", "moderate"),
        S("nasal-discharge", "Ingus/leleran hidung", "respiratory", "high"),
        S("dyspnea", "Sesak napas", "respiratory", "high", True),
        S("open-mouth-breathing", "Bernapas mulut terbuka", "respiratory", "high", True),
        S("fever", "Demam", "systemic", "moderate"),
        S("wheezing", "Suara napas melengking", "respiratory", "moderate"),
        S("respiratory-distress", "Gangguan napas", "respiratory", "high", True),
    ],
    "urinary": [
        S("dysuria", "Mengejan saat pipis", "urinary", "high", True),
        S("polyuria", "Banyak pipis", "urinary", "high"),
        S("polydipsia", "Banyak minum", "urinary", "high"),
        S("hematuria", "Kencing berdarah", "urinary", "high", True),
        S("inappetence", "Tidak mau makan", "digestive", "moderate"),
    ],
    "integumentary": [
        S("itching", "Gatal", "integumentary", "high"),
        S("hair-loss", "Kerontokan bulu", "integumentary", "high"),
        S("skin-lesion", "Lesi kulit", "integumentary", "high"),
        S("scaly-skin", "Kulit bersisik", "integumentary", "moderate"),
        S("red-skin", "Kulit merah", "integumentary", "moderate"),
        S("odor-skin", "Bau busuk kulit", "integumentary", "moderate"),
        S("alopecia-patchy", "Bulu rontok patchy", "integumentary", "moderate"),
        S("crusty-skin", "Kulit berkerak", "integumentary", "moderate"),
    ],
    "musculoskeletal": [
        S("limping", "Pincang", "musculoskeletal", "high"),
        S("stiffness", "Kaku saat bangun", "musculoskeletal", "high"),
        S("reluctance-move", "Enggan bergerak", "musculoskeletal", "moderate"),
        S("muscle-atrophy", "Otot mengecil", "musculoskeletal", "moderate"),
        S("joint-swelling", "Sendi bengkak", "musculoskeletal", "moderate"),
    ],
    "cardiovascular": [
        S("exercise-intolerance", "Cepat lemas saat aktivitas", "cardiovascular", "high"),
        S("collapse", "Kolaps", "cardiovascular", "high", True),
        S("cough-night", "Batuk malam", "cardiovascular", "moderate"),
        S("pale-gums", "Gusi pucat", "cardiovascular", "high", True),
        S("murmur", "Bising jantung", "cardiovascular", "high"),
    ],
    "nervous": [
        S("seizure", "Kejang", "nervous", "high", True),
        S("ataxia", "Gangguan keseimbangan", "nervous", "high"),
        S("head-tilt", "Kepala miring", "nervous", "moderate"),
        S("circling", "Berputar", "nervous", "moderate"),
        S("tremor", "Gemetar", "nervous", "moderate"),
        S("lethargy", "Lemas", "systemic", "high"),
    ],
    "ophthalmic": [
        S("ocular-discharge", "Mata berair", "ophthalmic", "high"),
        S("red-eye", "Mata merah", "ophthalmic", "high"),
        S("squinting", "Mata terpejam", "ophthalmic", "moderate"),
        S("cloudy-eye", "Mata keruh", "ophthalmic", "moderate"),
        S("vision-loss", "Penglihatan menurun", "ophthalmic", "moderate"),
    ],
    "auditory": [
        S("ear-scratching", "Menggaruk telinga", "auditory", "high"),
        S("head-shaking", "Menggeleng kepala", "auditory", "high"),
        S("ear-discharge", "Leleran telinga", "auditory", "high"),
        S("ear-odor", "Bau telinga", "auditory", "moderate"),
        S("ear-redness", "Telinga merah", "auditory", "moderate"),
    ],
    "dental": [
        S("drooling", "Ngiler berlebihan", "dental", "high"),
        S("bad-breath", "Bau mulut", "dental", "high"),
        S("difficulty-eating", "Sulit makan", "dental", "high"),
        S("facial-swelling", "Bengkak wajah", "dental", "moderate", True),
        S("tooth-loss", "Gigi lepas/rapuh", "dental", "moderate"),
    ],
    "endocrine": [
        S("polyuria-polydipsia", "Banyak pipis & minum", "endocrine", "high"),
        S("weight-change", "Berat badan berubah", "systemic", "high"),
        S("coat-change", "Perubahan bulu", "integumentary", "moderate"),
        S("lethargy-endo", "Lesu", "systemic", "high"),
    ],
    "reproductive": [
        S("vulvar-discharge", "Leleran vulva", "reproductive", "high"),
        S("straining", "Mengejan", "reproductive", "high", True),
        S("infertility", "Gagal reproduksi", "reproductive", "low"),
    ],
    "hematologic": [
        S("pale-mucosa", "Mukosa pucat", "hematologic", "high", True),
        S("bleeding", "Perdarahan", "hematologic", "high", True),
        S("bruising", "Bintik merah/perdarahan kulit", "hematologic", "moderate"),
    ],
    "systemic": [
        S("lethargy-sys", "Lesu", "systemic", "very_high"),
        S("fever-sys", "Demam", "systemic", "moderate"),
        S("weight-loss-sys", "Berat badan turun", "systemic", "moderate"),
    ],
    "behavioral": [
        S("aggression", "Agresi", "behavioral", "moderate"),
        S("anxiety", "Gelisah/cemas", "behavioral", "moderate"),
        S("hiding", "Bersembunyi", "behavioral", "moderate"),
    ],
    "immune": [
        S("recurrent-infection", "Infeksi berulang", "immune", "high"),
        S("slow-healing", "Luka lambat sembuh", "immune", "moderate"),
        S("swollen-lymph", "Kelenjar getah bening besar", "immune", "moderate"),
    ],
}


def _symptoms_for(body_system, extra=None, take=8):
    pool = list(_COMMON.get(body_system, _COMMON["systemic"]))
    if extra:
        pool = extra + pool
    seen = set()
    out = []
    for s in pool:
        if s["slug"] not in seen:
            seen.add(s["slug"])
            out.append(s)
        if len(out) >= take:
            break
    return out


def _d(slug, name, name_id, etiology, body_system, severity, risk,
       diagnostics, treatment, products, symptoms=None,
       contagious=False, zoonotic=False, emergency=False, prevalence=None):
    syms = symptoms or _symptoms_for(body_system, take=8)
    d = C._disease(slug, name, name_id, etiology, body_system, severity, risk,
                   diagnostics, treatment, products,
                   contagious=contagious, zoonotic=zoonotic, emergency=emergency,
                   prevalence=prevalence)
    d["symptoms"] = syms
    return d


# ---------------------------------------------------------------------------
# PENYAKIT ANJING (~90 tambahan di luar base catalogs)
# ---------------------------------------------------------------------------
_DOG_EXTRA = [
    _d("dog-heartworm", "Heartworm Disease", "Penyakit Cacing Paru", "parasitic_internal",
       "cardiovascular", "severe", "high", [C.DX_BLOOD, C.DX_XRAY], C.TX_PARASITE,
       [C.PR_IVER, C.PR_WORMER], prevalence=18, contagious=False),
    _d("dog-lyme", "Lyme Disease", "Penyakit Lyme", "infectious_bacterial",
       "musculoskeletal", "moderate", "moderate", [C.DX_SEROLOGY, C.DX_BLOOD], C.TX_PHARMA,
       [C.PR_ENRO, C.PR_MELOX], zoonotic=True, prevalence=8),
    _d("dog-ehrlichiosis", "Ehrlichiosis", "Ehrlichiosis", "infectious_bacterial",
       "hematologic", "severe", "moderate", [C.DX_BLOOD, C.DX_SEROLOGY], C.TX_PHARMA,
       [C.PR_ENRO, C.PR_FLUID], prevalence=6),
    _d("dog-pancreatitis", "Pancreatitis", "Pankreatitis", "metabolic",
       "digestive", "severe", "high", [C.DX_BLOOD, C.DX_USG], C.TX_SUPPORT,
       [C.PR_FLUID, C.PR_MAROP], emergency=True, prevalence=15),
    _d("dog-ibd", "Inflammatory Bowel Disease", "IBD", "idiopathic",
       "digestive", "moderate", "moderate", [C.DX_FECAL, C.DX_USG], C.TX_DIET,
       [C.PR_DIET_RX, C.PR_METRO], prevalence=12),
    _d("dog-cruciate", "Cruciate Ligament Rupture", "Robek Ligamen Cruziat", "traumatic",
       "musculoskeletal", "severe", "high", [C.DX_PHYS, C.DX_XRAY], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_FLUID], prevalence=14),
    _d("dog-patellar-luxation", "Patellar Luxation", "Luxasi Patella", "genetic_congenital",
       "musculoskeletal", "moderate", "high", [C.DX_PHYS, C.DX_XRAY], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_DIET_RX], prevalence=16),
    _d("dog-ivdd", "Intervertebral Disc Disease", "IVDD (Hernia Diskus)", "degenerative",
       "musculoskeletal", "severe", "high", [C.DX_PHYS, C.DX_XRAY], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_FLUID], emergency=True, prevalence=10),
    _d("dog-hypothyroid", "Hypothyroidism", "Hipotiroidisme", "metabolic",
       "endocrine", "moderate", "high", [C.DX_BLOOD, C.DX_HISTORY], C.TX_PHARMA,
       [C.PR_DIET_RX, C.PR_MELOX], prevalence=12),
    _d("dog-cushings", "Hyperadrenocorticism (Cushing)", "Sindrom Cushing", "metabolic",
       "endocrine", "moderate", "moderate", [C.DX_BLOOD, C.DX_USG], C.TX_PHARMA,
       [C.PR_FURO, C.PR_DIET_RX], prevalence=8),
    _d("dog-addisons", "Hypoadrenocorticism (Addison)", "Penyakit Addison", "metabolic",
       "endocrine", "critical", "moderate", [C.DX_BLOOD, C.DX_HISTORY], C.TX_FLUID,
       [C.PR_FLUID, C.PR_ENRO], emergency=True, prevalence=4),
    _d("dog-diabetes", "Diabetes Mellitus", "Diabetes Melitus", "metabolic",
       "endocrine", "severe", "moderate", [C.DX_BLOOD, C.DX_URINE], C.TX_PHARMA,
       [C.PR_DIET_RX, C.PR_FLUID], prevalence=10),
    _d("dog-epilepsy", "Epilepsy", "Epilepsi", "genetic_congenital",
       "nervous", "severe", "moderate", [C.DX_BLOOD, C.DX_HISTORY], C.TX_PHARMA,
       [C.PR_MELOX, C.PR_FLUID], prevalence=9),
    _d("dog-dcm", "Dilated Cardiomyopathy", "Kardiomiopati Dilatasi (DCM)", "genetic_congenital",
       "cardiovascular", "severe", "high", [C.DX_USG, C.DX_XRAY], C.TX_PHARMA,
       [C.PR_FURO, C.PR_MELOX], prevalence=11),
    _d("dog-mvd", "Mitral Valve Disease", "Penyakit Katup Mitral", "degenerative",
       "cardiovascular", "moderate", "high", [C.DX_USG, C.DX_PHYS], C.TX_PHARMA,
       [C.PR_FURO, C.PR_MELOX], prevalence=20),
    _d("dog-kennel-cough", "Kennel Cough", "Batuk Anjing (Kennel Cough)", "infectious_bacterial",
       "respiratory", "moderate", "high", [C.DX_PHYS, C.DX_PCR], C.TX_PHARMA,
       [C.PR_ABX, C.PR_FLUID], contagious=True, prevalence=22),
    _d("dog-pneumonia", "Pneumonia", "Pneumonia", "infectious_bacterial",
       "respiratory", "severe", "high", [C.DX_XRAY, C.DX_CULTURE], C.TX_PHARMA,
       [C.PR_ENRO, C.PR_FLUID], contagious=True, emergency=True, prevalence=8),
    _d("dog-bronchitis", "Chronic Bronchitis", "Bronkitis Kronis", "degenerative",
       "respiratory", "moderate", "moderate", [C.DX_XRAY, C.DX_PHYS], C.TX_PHARMA,
       [C.PR_MELOX, C.PR_ABX], prevalence=10),
    _d("dog-brachy-airway", "Brachycephalic Airway Syndrome", "Sindrom Saluran Napas Brachycephalic",
       "genetic_congenital", "respiratory", "moderate", "high", [C.DX_PHYS, C.DX_XRAY], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_FLUID], prevalence=18),
    _d("dog-laryngeal-paralysis", "Laryngeal Paralysis", "Paralisis Laring", "degenerative",
       "respiratory", "severe", "moderate", [C.DX_PHYS, C.DX_XRAY], C.TX_SURGERY,
       [C.PR_FLUID, C.PR_MELOX], emergency=True, prevalence=6),
    _d("dog-collapsing-trachea", "Collapsing Trachea", "Trakea Kolaps", "degenerative",
       "respiratory", "moderate", "high", [C.DX_XRAY, C.DX_PHYS], C.TX_PHARMA,
       [C.PR_MELOX, C.PR_ABX], prevalence=14),
    _d("dog-pyometra", "Pyometra", "Piometra", "infectious_bacterial",
       "reproductive", "critical", "high", [C.DX_USG, C.DX_BLOOD], C.TX_SURGERY,
       [C.PR_ENRO, C.PR_FLUID], emergency=True, prevalence=7),
    _d("dog-uti", "Urinary Tract Infection", "Infeksi Saluran Kemih (UTI)", "infectious_bacterial",
       "urinary", "moderate", "high", [C.DX_URINE, C.DX_CULTURE], C.TX_PHARMA,
       [C.PR_ENRO, C.PR_FLUID], prevalence=16),
    _d("dog-urolithiasis", "Urolithiasis", "Batu Kandung Kemih", "metabolic",
       "urinary", "severe", "moderate", [C.DX_URINE, C.DX_XRAY], C.TX_SURGERY,
       [C.PR_DIET_RX, C.PR_FLUID], prevalence=9),
    _d("dog-prostatitis", "Prostatitis", "Prostatitis", "infectious_bacterial",
       "reproductive", "severe", "moderate", [C.DX_USG, C.DX_CULTURE], C.TX_PHARMA,
       [C.PR_ENRO, C.PR_MELOX], prevalence=5),
    _d("dog-atopic-dermatitis", "Atopic Dermatitis", "Dermatitis Atopik", "environmental",
       "integumentary", "moderate", "high", [C.DX_SKIN, C.DX_HISTORY], C.TX_PHARMA,
       [C.PR_MELOX, C.PR_ANTIFUNGAL_BATH], prevalence=18),
    _d("dog-pyoderma", "Pyoderma", "Pioderma", "infectious_bacterial",
       "integumentary", "moderate", "high", [C.DX_CYTO, C.DX_CULTURE], C.TX_PHARMA,
       [C.PR_ABX, C.PR_SALEP], prevalence=20),
    _d("dog-hot-spot", "Acute Moist Dermatitis", "Hot Spot", "infectious_bacterial",
       "integumentary", "mild", "high", [C.DX_PHYS, C.DX_CYTO], C.TX_PHARMA,
       [C.PR_SALEP, C.PR_ABX], prevalence=15),
    _d("dog-sarcoptic-mange", "Sarcoptic Mange", "Kudis Sarcoptik", "parasitic_external",
       "integumentary", "moderate", "high", [C.DX_SKIN, C.DX_CYTO], C.TX_PARASITE,
       [C.PR_IVER, C.PR_ANTIFUNGAL_BATH], contagious=True, zoonotic=True, prevalence=12),
    _d("dog-food-allergy", "Food Allergy", "Alergi Makanan", "nutritional",
       "integumentary", "moderate", "moderate", [C.DX_HISTORY, C.DX_CYTO], C.TX_DIET,
       [C.PR_DIET_RX, C.PR_MELOX], prevalence=11),
    _d("dog-glaucoma", "Glaucoma", "Glaukoma", "degenerative",
       "ophthalmic", "severe", "moderate", [C.DX_PHYS, C.DX_USG], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_FLUID], emergency=True, prevalence=5),
    _d("dog-corneal-ulcer", "Corneal Ulcer", "Ulser Kornea", "traumatic",
       "ophthalmic", "severe", "high", [C.DX_PHYS, C.DX_CYTO], C.TX_PHARMA,
       [C.PR_ABX, C.PR_MELOX], emergency=True, prevalence=8),
    _d("dog-kcs", "Keratoconjunctivitis Sicca", "Mata Kering (KCS)", "idiopathic",
       "ophthalmic", "moderate", "moderate", [C.DX_PHYS, C.DX_CYTO], C.TX_PHARMA,
       [C.PR_SALEP, C.PR_MELOX], prevalence=7),
    _d("dog-cherry-eye", "Cherry Eye", "Cherry Eye", "genetic_congenital",
       "ophthalmic", "mild", "moderate", [C.DX_PHYS, C.DX_HISTORY], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_FLUID], prevalence=6),
    _d("dog-periodontitis", "Periodontitis", "Periodontitis", "degenerative",
       "dental", "moderate", "very_high", [C.DX_PHYS, C.DX_XRAY], C.TX_SURGERY,
       [C.PR_ABX, C.PR_MELOX], prevalence=28),
    _d("dog-lymphoma", "Lymphoma", "Limfoma", "neoplastic",
       "hematologic", "severe", "moderate", [C.DX_CYTO, C.DX_BLOOD], C.TX_PHARMA,
       [C.PR_ABX, C.PR_FLUID], prevalence=5),
    _d("dog-mast-cell", "Mast Cell Tumor", "Tumor Sel Mast", "neoplastic",
       "integumentary", "moderate", "moderate", [C.DX_CYTO, C.DX_PHYS], C.TX_SURGERY,
       [C.PR_ABX, C.PR_MELOX], prevalence=6),
    _d("dog-osteosarcoma", "Osteosarcoma", "Osteosarcoma", "neoplastic",
       "musculoskeletal", "severe", "moderate", [C.DX_XRAY, C.DX_CYTO], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_FLUID], prevalence=4),
    _d("dog-hemangiosarcoma", "Hemangiosarcoma", "Hemangiosarcoma", "neoplastic",
       "cardiovascular", "critical", "moderate", [C.DX_USG, C.DX_CYTO], C.TX_SURGERY,
       [C.PR_FLUID, C.PR_MELOX], emergency=True, prevalence=3),
    _d("dog-imha", "Immune-Mediated Hemolytic Anemia", "IMHA (Anemia Imun)", "idiopathic",
       "hematologic", "critical", "moderate", [C.DX_BLOOD, C.DX_CYTO], C.TX_PHARMA,
       [C.PR_FLUID, C.PR_ENRO], emergency=True, prevalence=4),
    _d("dog-imtp", "Immune-Mediated Thrombocytopenia", "IMTP", "idiopathic",
       "hematologic", "critical", "moderate", [C.DX_BLOOD, C.DX_CYTO], C.TX_PHARMA,
       [C.PR_FLUID, C.PR_ENRO], emergency=True, prevalence=3),
    _d("dog-foreign-body", "GI Foreign Body", "Benda Asing Saluran Cerna", "traumatic",
       "digestive", "severe", "high", [C.DX_XRAY, C.DX_USG], C.TX_SURGERY,
       [C.PR_FLUID, C.PR_MAROP], emergency=True, prevalence=9),
    _d("dog-megaoesophagus", "Megaesophagus", "Megaesofagus", "degenerative",
       "digestive", "severe", "moderate", [C.DX_XRAY, C.DX_HISTORY], C.TX_SUPPORT,
       [C.PR_DIET_RX, C.PR_FLUID], prevalence=5),
    _d("dog-anal-gland", "Anal Gland Disease", "Penyakit Kelenjar Anal", "infectious_bacterial",
       "digestive", "moderate", "high", [C.DX_PHYS, C.DX_CYTO], C.TX_PHARMA,
       [C.PR_ABX, C.PR_MELOX], prevalence=14),
    _d("dog-heat-stroke", "Heat Stroke", "Heat Stroke", "environmental",
       "systemic", "critical", "moderate", [C.DX_PHYS, C.DX_BLOOD], C.TX_FLUID,
       [C.PR_FLUID, C.PR_MELOX], emergency=True, prevalence=6),
    _d("dog-chocolate-toxicity", "Chocolate Toxicity", "Toksik Cokelat", "toxic",
       "nervous", "severe", "moderate", [C.DX_HISTORY, C.DX_BLOOD], C.TX_SUPPORT,
       [C.PR_FLUID, C.PR_MAROP], emergency=True, prevalence=5),
    _d("dog-xylitol-toxicity", "Xylitol Toxicity", "Toksik Xylitol", "toxic",
       "endocrine", "critical", "moderate", [C.DX_BLOOD, C.DX_HISTORY], C.TX_FLUID,
       [C.PR_FLUID, C.PR_ENRO], emergency=True, prevalence=4),
    _d("dog-cognitive-dysfunction", "Cognitive Dysfunction", "Demensia Anjing", "degenerative",
       "behavioral", "mild", "moderate", [C.DX_HISTORY, C.DX_PHYS], C.TX_PHARMA,
       [C.PR_DIET_RX, C.PR_MELOX], prevalence=8),
    _d("dog-separation-anxiety", "Separation Anxiety", "Kecemasan Terpisah", "behavioral",
       "behavioral", "mild", "moderate", [C.DX_HISTORY, C.DX_PHYS], C.TX_PHARMA,
       [C.PR_MELOX, C.PR_DIET_RX], prevalence=10),
    _d("dog-hookworm", "Hookworm Infection", "Cacing Tambang", "parasitic_internal",
       "digestive", "moderate", "high", [C.DX_FECAL, C.DX_HISTORY], C.TX_PARASITE,
       [C.PR_WORMER, C.PR_IVER], zoonotic=True, prevalence=20),
    _d("dog-roundworm", "Roundworm Infection", "Cacing Ascaris", "parasitic_internal",
       "digestive", "moderate", "high", [C.DX_FECAL, C.DX_HISTORY], C.TX_PARASITE,
       [C.PR_WORMER, C.PR_IVER], zoonotic=True, prevalence=22),
    _d("dog-giardia", "Giardiasis", "Giardiasis", "parasitic_internal",
       "digestive", "moderate", "high", [C.DX_FECAL, C.DX_PCR], C.TX_PHARMA,
       [C.PR_METRO, C.PR_PROBIO], contagious=True, zoonotic=True, prevalence=14),
    _d("dog-tick-fever", "Tick Fever (Babesiosis)", "Demam Tungau (Babesiosis)", "parasitic_internal",
       "hematologic", "severe", "moderate", [C.DX_BLOOD, C.DX_SEROLOGY], C.TX_PHARMA,
       [C.PR_ENRO, C.PR_FLUID], prevalence=5),
]

# ---------------------------------------------------------------------------
# KUCING (~70 tambahan)
# ---------------------------------------------------------------------------
_CAT_EXTRA = [
    _d("cat-fip", "Feline Infectious Peritonitis", "FIP", "infectious_viral",
       "systemic", "critical", "moderate", [C.DX_PCR, C.DX_BLOOD], C.TX_SUPPORT,
       [C.PR_FLUID, C.PR_ENRO], contagious=True, emergency=True, prevalence=6),
    _d("cat-felv", "Feline Leukemia Virus", "FeLV", "infectious_viral",
       "hematologic", "severe", "moderate", [C.DX_SEROLOGY, C.DX_BLOOD], C.TX_SUPPORT,
       [C.PR_FLUID, C.PR_ABX], contagious=True, prevalence=8),
    _d("cat-fiv", "Feline Immunodeficiency Virus", "FIV", "infectious_viral",
       "immune", "severe", "moderate", [C.DX_SEROLOGY, C.DX_BLOOD], C.TX_SUPPORT,
       [C.PR_ABX, C.PR_FLUID], contagious=True, prevalence=7),
    _d("cat-calicivirus", "Feline Calicivirus", "Calicivirus", "infectious_viral",
       "respiratory", "moderate", "high", [C.DX_PCR, C.DX_PHYS], C.TX_SUPPORT,
       [C.PR_ABX, C.PR_FLUID], contagious=True, prevalence=15),
    _d("cat-herpesvirus", "Feline Herpesvirus (FHV-1)", "Herpesvirus Kucing", "infectious_viral",
       "respiratory", "moderate", "high", [C.DX_PCR, C.DX_PHYS], C.TX_SUPPORT,
       [C.PR_ABX, C.PR_FLUID], contagious=True, prevalence=18),
    _d("cat-hyperthyroid", "Hyperthyroidism", "Hipertiroidisme", "metabolic",
       "endocrine", "moderate", "high", [C.DX_BLOOD, C.DX_USG], C.TX_PHARMA,
       [C.PR_FURO, C.PR_DIET_RX], prevalence=14),
    _d("cat-diabetes", "Diabetes Mellitus", "Diabetes Melitus", "metabolic",
       "endocrine", "severe", "moderate", [C.DX_BLOOD, C.DX_URINE], C.TX_PHARMA,
       [C.PR_DIET_RX, C.PR_FLUID], prevalence=10),
    _d("cat-asthma", "Feline Asthma", "Asma Kucing", "environmental",
       "respiratory", "severe", "moderate", [C.DX_XRAY, C.DX_PHYS], C.TX_PHARMA,
       [C.PR_MELOX, C.PR_FLUID], emergency=True, prevalence=8),
    _d("cat-pkd", "Polycystic Kidney Disease", "PKD (Ginjal Polikistik)", "genetic_congenital",
       "urinary", "severe", "high", [C.DX_USG, C.DX_PCR], C.TX_DIET,
       [C.PR_DIET_RX, C.PR_FURO], prevalence=12),
    _d("cat-urethral-plug", "Urethral Plug", "Plugs Uretra", "metabolic",
       "urinary", "critical", "high", [C.DX_URINE, C.DX_PHYS], C.TX_SUPPORT,
       [C.PR_FLUID, C.PR_ENRO], emergency=True, prevalence=9),
    _d("cat-pyometra", "Pyometra", "Piometra", "infectious_bacterial",
       "reproductive", "critical", "moderate", [C.DX_USG, C.DX_BLOOD], C.TX_SURGERY,
       [C.PR_ENRO, C.PR_FLUID], emergency=True, prevalence=5),
    _d("cat-dental-resorptive", "Tooth Resorption", "Resorpsi Gigi", "degenerative",
       "dental", "moderate", "high", [C.DX_PHYS, C.DX_XRAY], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_ABX], prevalence=22),
    _d("cat-stomatitis", "Stomatitis", "Stomatitis", "idiopathic",
       "dental", "severe", "moderate", [C.DX_PHYS, C.DX_CYTO], C.TX_PHARMA,
       [C.PR_MELOX, C.PR_ABX], prevalence=8),
    _d("cat-flea-allergy", "Flea Allergy Dermatitis", "Dermatitis Alergi Kutu", "parasitic_external",
       "integumentary", "moderate", "high", [C.DX_SKIN, C.DX_PHYS], C.TX_PARASITE,
       [C.PR_IVER, C.PR_MELOX], prevalence=16),
    _d("cat-miliary-dermatitis", "Miliary Dermatitis", "Dermatitis Milier", "environmental",
       "integumentary", "moderate", "high", [C.DX_SKIN, C.DX_CYTO], C.TX_PHARMA,
       [C.PR_MELOX, C.PR_SALEP], prevalence=14),
    _d("cat-lymphoma", "Lymphoma", "Limfoma", "neoplastic",
       "hematologic", "severe", "moderate", [C.DX_CYTO, C.DX_BLOOD], C.TX_PHARMA,
       [C.PR_ABX, C.PR_FLUID], prevalence=6),
    _d("cat-squamous-cell", "Squamous Cell Carcinoma", "Karsinoma Sel Skuamosa", "neoplastic",
       "integumentary", "severe", "moderate", [C.DX_CYTO, C.DX_PHYS], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_FLUID], prevalence=4),
    _d("cat-pancreatitis", "Pancreatitis", "Pankreatitis", "metabolic",
       "digestive", "severe", "moderate", [C.DX_BLOOD, C.DX_USG], C.TX_SUPPORT,
       [C.PR_FLUID, C.PR_MAROP], prevalence=7),
    _d("cat-ibd", "Inflammatory Bowel Disease", "IBD", "idiopathic",
       "digestive", "moderate", "moderate", [C.DX_USG, C.DX_FECAL], C.TX_DIET,
       [C.PR_DIET_RX, C.PR_METRO], prevalence=10),
    _d("cat-constipation", "Constipation", "Sembelit", "metabolic",
       "digestive", "moderate", "moderate", [C.DX_PHYS, C.DX_XRAY], C.TX_SUPPORT,
       [C.PR_PROBIO, C.PR_FLUID], prevalence=9),
    _d("cat-hypercalcemia", "Hypercalcemia", "Hiperkalsemia", "metabolic",
       "endocrine", "severe", "low", [C.DX_BLOOD, C.DX_USG], C.TX_FLUID,
       [C.PR_FLUID, C.PR_FURO], prevalence=3),
    _d("cat-toxoplasmosis", "Toxoplasmosis", "Toxoplasmosis", "parasitic_internal",
       "digestive", "moderate", "moderate", [C.DX_SEROLOGY, C.DX_PCR], C.TX_PHARMA,
       [C.PR_ENRO, C.PR_ABX], zoonotic=True, prevalence=6),
    _d("cat-tri-tri", "Tri-Tri (Tritrichomonas)", "Tri-Tri", "parasitic_internal",
       "digestive", "moderate", "moderate", [C.DX_FECAL, C.DX_PCR], C.TX_PHARMA,
       [C.PR_METRO, C.PR_PROBIO], contagious=True, prevalence=5),
    _d("cat-vestibular", "Vestibular Disease", "Gangguan Vestibular", "idiopathic",
       "nervous", "moderate", "moderate", [C.DX_PHYS, C.DX_BLOOD], C.TX_SUPPORT,
       [C.PR_MELOX, C.PR_FLUID], prevalence=4),
    _d("cat-retinal-detachment", "Retinal Detachment", "Retina Lepas", "degenerative",
       "ophthalmic", "severe", "low", [C.DX_USG, C.DX_PHYS], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_FLUID], prevalence=3),
]

# Fix toxoplasmosis product reference
_CAT_EXTRA[-2]["products"] = [C.PR_ENRO, C.PR_ABX]

# Add symptoms to base CLINICAL diseases that lack them
def _ensure_symptoms_on_base(disease_dict):
    if "symptoms" not in disease_dict or not disease_dict["symptoms"]:
        disease_dict["symptoms"] = _symptoms_for(disease_dict.get("body_system", "systemic"), take=8)
    return disease_dict


# Smaller expansions for other categories (batch generated)
def _batch_diseases(cat_prefix, cat_name, items):
    """items: list of (slug_suffix, name, name_id, etiology, body_system, severity, risk, prev)"""
    out = []
    for slug_s, name, name_id, etio, bs, sev, risk, prev in items:
        slug = f"{cat_prefix}-{slug_s}"
        out.append(_d(slug, name, name_id, etio, bs, sev, risk,
                      [C.DX_PHYS, C.DX_BLOOD], C.TX_PHARMA, [C.PR_ABX, C.PR_FLUID],
                      prevalence=prev))
    return out


_RABBIT_EXTRA = _batch_diseases("rabbit", "Kelinci", [
    ("enteritis", "Enteritis", "Enteritis", "infectious_bacterial", "digestive", "severe", "high", 18),
    ("uterine-adenocarcinoma", "Uterine Adenocarcinoma", "Adenokarsinoma Uterus", "neoplastic", "reproductive", "severe", "moderate", 8),
    ("pododermatitis", "Pododermatitis", "Pododermatitis", "environmental", "integumentary", "moderate", "high", 15),
    ("heat-stress", "Heat Stress", "Stres Panas", "environmental", "systemic", "severe", "moderate", 10),
    ("pneumonia", "Pneumonia", "Pneumonia", "infectious_bacterial", "respiratory", "severe", "high", 12),
    ("coccidiosis", "Coccidiosis", "Koksidiosis", "parasitic_internal", "digestive", "moderate", "high", 20),
    ("ringworm", "Ringworm", "Ringworm", "infectious_fungal", "integumentary", "mild", "moderate", 10),
    ("dental-abscess", "Dental Abscess", "Abses Gigi", "infectious_bacterial", "dental", "moderate", "high", 14),
    ("head-tilt", "Head Tilt", "Kepala Miring", "infectious_bacterial", "nervous", "moderate", "moderate", 8),
    ("mucoid-enteropathy", "Mucoid Enteropathy", "Enteropati Mucoid", "infectious_bacterial", "digestive", "critical", "moderate", 6),
])

_HAMSTER_EXTRA = _batch_diseases("hamster", "Hamster", [
    ("pneumonia", "Pneumonia", "Pneumonia", "infectious_bacterial", "respiratory", "severe", "high", 12),
    ("skin-abscess", "Skin Abscess", "Abses Kulit", "infectious_bacterial", "integumentary", "moderate", "moderate", 10),
    ("overgrown-teeth", "Overgrown Teeth", "Gigi Panjang", "nutritional", "dental", "moderate", "high", 15),
    ("cardiomyopathy", "Cardiomyopathy", "Kardiomiopati", "degenerative", "cardiovascular", "severe", "moderate", 8),
    ("prolapse", "Rectal Prolapse", "Prolaps Rektal", "traumatic", "digestive", "severe", "moderate", 5),
    ("conjunctivitis", "Conjunctivitis", "Konjungtivitis", "infectious_bacterial", "ophthalmic", "mild", "moderate", 9),
    ("ringworm", "Ringworm", "Ringworm", "infectious_fungal", "integumentary", "mild", "moderate", 6),
    ("heat-stroke", "Heat Stroke", "Heat Stroke", "environmental", "systemic", "critical", "moderate", 7),
])

_POULTRY_EXTRA = _batch_diseases("poultry", "Unggas", [
    ("fowl-cholera", "Fowl Cholera", "Kolera Unggas", "infectious_bacterial", "respiratory", "severe", "high", 18),
    ("salmonella", "Salmonellosis", "Salmonellosis", "infectious_bacterial", "digestive", "moderate", "high", 20),
    ("avian-influenza", "Avian Influenza", "Flu Burung (AI)", "infectious_viral", "respiratory", "critical", "high", 8),
    ("mareks", "Marek Disease", "Penyakit Marek", "infectious_viral", "nervous", "severe", "high", 15),
    ("gapeworm", "Gapeworm", "Cacing Gape", "parasitic_internal", "respiratory", "severe", "high", 12),
    ("canker", "Trichomoniasis (Canker)", "Canker", "infectious_bacterial", "digestive", "moderate", "moderate", 14),
    ("air-sac-mite", "Air Sac Mite", "Tungau Kantung Udara", "parasitic_external", "respiratory", "moderate", "high", 16),
    ("aspergillosis", "Aspergillosis", "Aspergilosis", "infectious_fungal", "respiratory", "severe", "moderate", 7),
    ("botulism", "Botulism", "Botulisme", "toxic", "nervous", "critical", "moderate", 5),
    ("egg-peritonitis", "Egg Yolk Peritonitis", "Peritonitis Kuning Telur", "metabolic", "reproductive", "severe", "moderate", 9),
    ("bacterial-enteritis", "Bacterial Enteritis", "Enteritis Bakteri", "infectious_bacterial", "digestive", "moderate", "high", 22),
    ("fowl-typhoid", "Fowl Typhoid", "Tifus Unggas", "infectious_bacterial", "digestive", "severe", "high", 10),
])

_FISH_EXTRA = _batch_diseases("fish", "Ikan", [
    ("ammonia-poisoning", "Ammonia Poisoning", "Toksik Amonia", "toxic", "systemic", "critical", "very_high", 25),
    ("nitrite-poisoning", "Nitrite Poisoning", "Toksik Nitrit", "toxic", "systemic", "severe", "high", 18),
    ("anchor-worm", "Anchor Worm", "Cacing Jangkar", "parasitic_external", "integumentary", "moderate", "high", 12),
    ("flukes", "Gill Flukes", "Flukes Insang", "parasitic_external", "respiratory", "moderate", "high", 15),
    ("hole-in-head", "Hole-in-the-Head", "Hole-in-the-Head", "parasitic_internal", "integumentary", "moderate", "moderate", 8),
    ("mouth-fungus", "Mouth Fungus (Columnaris)", "Jamur Mulut", "infectious_bacterial", "integumentary", "moderate", "high", 14),
    ("pop-eye", "Pop Eye", "Mata Menonjol", "infectious_bacterial", "ophthalmic", "moderate", "moderate", 10),
    ("tail-rot", "Tail Rot", "Busuk Ekor", "infectious_bacterial", "integumentary", "moderate", "high", 16),
    ("oxygen-deprivation", "Oxygen Deprivation", "Kekurangan Oksigen", "environmental", "respiratory", "severe", "high", 12),
    ("swim-bladder-bacterial", "Bacterial Swim Bladder", "Gangguan Gelembung Renang Bakteri", "infectious_bacterial", "systemic", "moderate", "moderate", 11),
])

_REPTILE_EXTRA = _batch_diseases("reptile", "Reptil", [
    ("atadenovirus", "Atadenovirus", "Atadenovirus", "infectious_viral", "digestive", "severe", "moderate", 8),
    ("mouth-rot", "Mouth Rot", "Mulut Busuk", "infectious_bacterial", "dental", "moderate", "high", 18),
    ("parasites-intestinal", "Intestinal Parasites", "Parasit Usus", "parasitic_internal", "digestive", "moderate", "high", 26),
    ("egg-binding", "Egg Binding", "Telur Tersangkut", "metabolic", "reproductive", "severe", "moderate", 10),
    ("burns", "Thermal Burns", "Luka Bakar", "traumatic", "integumentary", "moderate", "moderate", 7),
    ("gout", "Gout", "Gout", "metabolic", "urinary", "severe", "moderate", 6),
    ("blister-disease", "Blister Disease", "Penyakit Blister", "environmental", "integumentary", "moderate", "moderate", 9),
    ("hypervitaminosis-d", "Hypervitaminosis D", "Hipervitaminosis D", "nutritional", "systemic", "severe", "moderate", 5),
    ("prolapse", "Prolapse", "Prolaps", "traumatic", "reproductive", "severe", "moderate", 6),
    ("scale-rot-advanced", "Advanced Scale Rot", "Busuk Sisik Lanjut", "infectious_bacterial", "integumentary", "severe", "moderate", 12),
])

_AMPHIBIAN_EXTRA = _batch_diseases("amphibian", "Amfibi", [
    ("ranavirus", "Ranavirus", "Ranavirus", "infectious_viral", "systemic", "critical", "moderate", 6),
    ("bacterial-septicemia", "Bacterial Septicemia", "Septikemia Bakteri", "infectious_bacterial", "systemic", "critical", "high", 10),
    ("nutritional-deficiency", "Nutritional Deficiency", "Defisiensi Nutrisi", "nutritional", "systemic", "moderate", "high", 14),
    ("skin-shedding-issue", "Dysecdysis", "Gangguan Ganti Kulit", "environmental", "integumentary", "moderate", "high", 18),
    ("bloat", "Bloat", "Kembung", "metabolic", "digestive", "severe", "moderate", 8),
])

_FERRET_EXTRA = _batch_diseases("ferret", "Ferret", [
    ("aleutian-disease", "Aleutian Disease", "Penyakit Aleutian", "infectious_viral", "systemic", "severe", "moderate", 5),
    ("cardiomyopathy", "Dilated Cardiomyopathy", "DCM Ferret", "degenerative", "cardiovascular", "severe", "high", 10),
    ("gastroenteritis", "Gastroenteritis", "Gastroenteritis", "infectious_bacterial", "digestive", "moderate", "high", 14),
    ("ear-mites", "Ear Mites", "Tungau Telinga", "parasitic_external", "auditory", "mild", "high", 16),
    ("adrenal-alopecia", "Adrenal Alopecia", "Alopecia Adrenal", "neoplastic", "integumentary", "moderate", "very_high", 28),
    ("foreign-body", "GI Foreign Body", "Benda Asing", "traumatic", "digestive", "severe", "high", 12),
])

_GP_EXTRA = _batch_diseases("guinea_pig", "Marmut", [
    ("respiratory-infection", "Respiratory Infection", "Infeksi Napas", "infectious_bacterial", "respiratory", "severe", "high", 22),
    ("dental-overgrowth", "Dental Overgrowth", "Gigi Panjang", "nutritional", "dental", "moderate", "very_high", 24),
    ("heat-stroke", "Heat Stroke", "Heat Stroke", "environmental", "systemic", "critical", "moderate", 7),
    ("pneumonia", "Pneumonia", "Pneumonia", "infectious_bacterial", "respiratory", "severe", "high", 12),
    ("ringworm", "Ringworm", "Ringworm", "infectious_fungal", "integumentary", "mild", "moderate", 14),
    ("ovarian-cyst", "Ovarian Cyst", "Kista Ovarium", "metabolic", "reproductive", "moderate", "moderate", 10),
    ("seizure", "Seizure Disorder", "Kejang", "metabolic", "nervous", "severe", "moderate", 6),
    ("foot-problems", "Foot Problems", "Masalah Kaki", "environmental", "musculoskeletal", "moderate", "high", 15),
    ("bloat", "Bloat", "Kembung", "metabolic", "digestive", "critical", "moderate", 8),
    ("scurvy", "Scurvy", "Skorbut (defisiensi C)", "nutritional", "systemic", "moderate", "moderate", 6),
])

# Batch penyakit tambahan (gelombang 2)
_DOG_EXTRA_B2 = [
    _d("dog-brucellosis", "Brucellosis", "Brucellosis", "infectious_bacterial",
       "reproductive", "severe", "moderate", [C.DX_SEROLOGY, C.DX_BLOOD], C.TX_PHARMA,
       [C.PR_ENRO, C.PR_ABX], zoonotic=True, prevalence=3),
    _d("dog-leptospirosis", "Leptospirosis", "Leptospirosis", "infectious_bacterial",
       "urinary", "severe", "moderate", [C.DX_SEROLOGY, C.DX_BLOOD], C.TX_PHARMA,
       [C.PR_ENRO, C.PR_FLUID], zoonotic=True, contagious=True, prevalence=7),
    _d("dog-babesiosis", "Babesiosis", "Babesiosis", "parasitic_internal",
       "hematologic", "severe", "moderate", [C.DX_BLOOD, C.DX_SEROLOGY], C.TX_PHARMA,
       [C.PR_ENRO, C.PR_FLUID], prevalence=4),
    _d("dog-distemper", "Canine Distemper", "Distemper Anjing", "infectious_viral",
       "nervous", "critical", "moderate", [C.DX_PCR, C.DX_BLOOD], C.TX_SUPPORT,
       [C.PR_FLUID, C.PR_ABX], contagious=True, emergency=True, prevalence=5),
    _d("dog-hepatitis", "Infectious Hepatitis", "Hepatitis Infeksius", "infectious_viral",
       "digestive", "severe", "moderate", [C.DX_BLOOD, C.DX_PCR], C.TX_SUPPORT,
       [C.PR_FLUID, C.PR_ABX], contagious=True, prevalence=4),
    _d("dog-coronavirus", "Canine Coronavirus", "Coronavirus Anjing", "infectious_viral",
       "digestive", "moderate", "high", [C.DX_FECAL, C.DX_PCR], C.TX_SUPPORT,
       [C.PR_FLUID, C.PR_PROBIO], contagious=True, prevalence=12),
    _d("dog-tracheobronchitis", "Tracheobronchitis", "Trakeobronkitis", "infectious_bacterial",
       "respiratory", "moderate", "high", [C.DX_PHYS, C.DX_XRAY], C.TX_PHARMA,
       [C.PR_ABX, C.PR_FLUID], contagious=True, prevalence=14),
    _d("dog-pyometra", "Pyometra", "Piometra", "infectious_bacterial",
       "reproductive", "critical", "moderate", [C.DX_USG, C.DX_BLOOD], C.TX_SURGERY,
       [C.PR_ENRO, C.PR_FLUID], emergency=True, prevalence=6),
    _d("dog-prostate-disease", "Prostatic Disease", "Penyakit Prostat", "degenerative",
       "reproductive", "moderate", "moderate", [C.DX_USG, C.DX_CYTO], C.TX_PHARMA,
       [C.PR_ENRO, C.PR_ABX], prevalence=8),
    _d("dog-vestibular", "Vestibular Disease", "Gangguan Vestibular", "idiopathic",
       "nervous", "moderate", "moderate", [C.DX_PHYS, C.DX_HISTORY], C.TX_SUPPORT,
       [C.PR_MELOX, C.PR_FLUID], prevalence=7),
    _d("dog-wobbler", "Wobbler Syndrome", "Sindrom Wobbler", "degenerative",
       "musculoskeletal", "severe", "moderate", [C.DX_XRAY, C.DX_PHYS], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_FLUID], prevalence=4),
    _d("dog-elbow-dysplasia", "Elbow Dysplasia", "Displasia Siku", "genetic_congenital",
       "musculoskeletal", "moderate", "high", [C.DX_XRAY, C.DX_PHYS], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_DIET_RX], prevalence=10),
    _d("dog-hip-dysplasia", "Hip Dysplasia", "Displasia Pinggul", "genetic_congenital",
       "musculoskeletal", "moderate", "high", [C.DX_XRAY, C.DX_PHYS], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_DIET_RX], prevalence=14),
    _d("dog-laryngeal-paralysis", "Laryngeal Paralysis", "Paralisis Laring", "degenerative",
       "respiratory", "severe", "moderate", [C.DX_PHYS, C.DX_XRAY], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_FLUID], prevalence=5),
    _d("dog-tracheal-collapse", "Tracheal Collapse", "Kolaps Trakea", "degenerative",
       "respiratory", "severe", "moderate", [C.DX_XRAY, C.DX_PHYS], C.TX_PHARMA,
       [C.PR_MELOX, C.PR_FLUID], prevalence=9),
    _d("dog-portosystemic-shunt", "Portosystemic Shunt", "Shunt Portosistemik", "genetic_congenital",
       "digestive", "severe", "moderate", [C.DX_BLOOD, C.DX_USG], C.TX_SURGERY,
       [C.PR_FLUID, C.PR_DIET_RX], prevalence=3),
    _d("dog-hepatitis-chronic", "Chronic Hepatitis", "Hepatitis Kronik", "degenerative",
       "digestive", "severe", "moderate", [C.DX_BLOOD, C.DX_USG], C.TX_PHARMA,
       [C.PR_FURO, C.PR_DIET_RX], prevalence=6),
    _d("dog-copper-storage", "Copper Storage Disease", "Penyakit Penyimpanan Tembaga", "metabolic",
       "digestive", "severe", "low", [C.DX_BLOOD, C.DX_CYTO], C.TX_PHARMA,
       [C.PR_FURO, C.PR_DIET_RX], prevalence=2),
    _d("dog-nephritis", "Glomerulonephritis", "Glomerulonefritis", "idiopathic",
       "urinary", "severe", "moderate", [C.DX_URINE, C.DX_BLOOD], C.TX_PHARMA,
       [C.PR_FURO, C.PR_DIET_RX], prevalence=5),
    _d("dog-urinary-stones", "Urolithiasis", "Batu Saluran Kemih", "metabolic",
       "urinary", "severe", "high", [C.DX_URINE, C.DX_XRAY], C.TX_SURGERY,
       [C.PR_FLUID, C.PR_ENRO], emergency=True, prevalence=11),
    _d("dog-splenic-tumor", "Splenic Tumor", "Tumor Splena", "neoplastic",
       "hematologic", "severe", "moderate", [C.DX_USG, C.DX_CYTO], C.TX_SURGERY,
       [C.PR_FLUID, C.PR_MELOX], emergency=True, prevalence=4),
    _d("dog-transitional-cell", "Transitional Cell Carcinoma", "Karsinoma Sel Transisi", "neoplastic",
       "urinary", "severe", "moderate", [C.DX_CYTO, C.DX_USG], C.TX_PHARMA,
       [C.PR_ABX, C.PR_FLUID], prevalence=3),
    _d("dog-melanoma", "Melanoma", "Melanoma", "neoplastic",
       "integumentary", "severe", "moderate", [C.DX_CYTO, C.DX_PHYS], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_FLUID], prevalence=4),
    _d("dog-fibrosarcoma", "Fibrosarcoma", "Fibrosarcoma", "neoplastic",
       "integumentary", "severe", "moderate", [C.DX_CYTO, C.DX_PHYS], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_ABX], prevalence=3),
    _d("dog-granulomatous-meningitis", "GME", "GME (Meningitis Granulomatosa)", "idiopathic",
       "nervous", "critical", "low", [C.DX_XRAY, C.DX_BLOOD], C.TX_PHARMA,
       [C.PR_MELOX, C.PR_FLUID], emergency=True, prevalence=2),
    _d("dog-snake-bite", "Snake Envenomation", "Gigitan Ular", "toxic",
       "systemic", "critical", "moderate", [C.DX_PHYS, C.DX_BLOOD], C.TX_SUPPORT,
       [C.PR_FLUID, C.PR_MELOX], emergency=True, prevalence=3),
    _d("dog-rodenticide", "Rodenticide Toxicity", "Toksik Rodentisida", "toxic",
       "hematologic", "critical", "moderate", [C.DX_BLOOD, C.DX_HISTORY], C.TX_SUPPORT,
       [C.PR_FLUID, C.PR_ENRO], emergency=True, prevalence=4),
    _d("dog-grape-toxicity", "Grape/Raisin Toxicity", "Toksik Anggur/Kismis", "toxic",
       "urinary", "severe", "moderate", [C.DX_BLOOD, C.DX_URINE], C.TX_FLUID,
       [C.PR_FLUID, C.PR_FURO], emergency=True, prevalence=3),
    _d("dog-onion-toxicity", "Onion Toxicity", "Toksik Bawang", "toxic",
       "hematologic", "moderate", "moderate", [C.DX_BLOOD, C.DX_HISTORY], C.TX_SUPPORT,
       [C.PR_FLUID, C.PR_ENRO], prevalence=3),
    _d("dog-compulsive-disorder", "Compulsive Disorder", "Gangguan Kompulsif", "behavioral",
       "behavioral", "mild", "moderate", [C.DX_HISTORY, C.DX_PHYS], C.TX_PHARMA,
       [C.PR_MELOX, C.PR_DIET_RX], prevalence=6),
]

_CAT_EXTRA_B2 = [
    _d("cat-chylothorax", "Chylothorax", "Chylothorax", "idiopathic",
       "respiratory", "severe", "low", [C.DX_XRAY, C.DX_CYTO], C.TX_SURGERY,
       [C.PR_FLUID, C.PR_FURO], prevalence=2),
    _d("cat-pleural-effusion", "Pleural Effusion", "Efusi Pleura", "idiopathic",
       "respiratory", "severe", "moderate", [C.DX_XRAY, C.DX_USG], C.TX_FLUID,
       [C.PR_FLUID, C.PR_FURO], emergency=True, prevalence=5),
    _d("cat-hcm", "Hypertrophic Cardiomyopathy", "HCM (Kardiomiopati Hipertrofik)", "genetic_congenital",
       "cardiovascular", "severe", "high", [C.DX_USG, C.DX_XRAY], C.TX_PHARMA,
       [C.PR_FURO, C.PR_MELOX], prevalence=12),
    _d("cat-dcm", "Dilated Cardiomyopathy", "DCM Kucing", "nutritional",
       "cardiovascular", "severe", "moderate", [C.DX_USG, C.DX_XRAY], C.TX_PHARMA,
       [C.PR_FURO, C.PR_DIET_RX], prevalence=4),
    _d("cat-thromboembolism", "Aortic Thromboembolism", "Thromboemboli Aorta", "metabolic",
       "cardiovascular", "critical", "moderate", [C.DX_PHYS, C.DX_USG], C.TX_PHARMA,
       [C.PR_FLUID, C.PR_ENRO], emergency=True, prevalence=4),
    _d("cat-portosystemic", "Portosystemic Shunt", "Shunt Portosistemik", "genetic_congenital",
       "digestive", "severe", "low", [C.DX_BLOOD, C.DX_USG], C.TX_SURGERY,
       [C.PR_FLUID, C.PR_DIET_RX], prevalence=2),
    _d("cat-hepatic-lipidosis", "Hepatic Lipidosis", "Lipidosis Hepatik", "metabolic",
       "digestive", "severe", "moderate", [C.DX_BLOOD, C.DX_USG], C.TX_SUPPORT,
       [C.PR_FLUID, C.PR_DIET_RX], emergency=True, prevalence=6),
    _d("cat-cholangitis", "Cholangitis", "Kolangitis", "infectious_bacterial",
       "digestive", "moderate", "moderate", [C.DX_BLOOD, C.DX_USG], C.TX_PHARMA,
       [C.PR_ENRO, C.PR_FLUID], prevalence=5),
    _d("cat-pancreatic-insufficiency", "EPI", "Insufisiensi Pankreas (EPI)", "genetic_congenital",
       "digestive", "moderate", "low", [C.DX_FECAL, C.DX_BLOOD], C.TX_DIET,
       [C.PR_DIET_RX, C.PR_PROBIO], prevalence=3),
    _d("cat-megacolon", "Megacolon", "Megacolon", "degenerative",
       "digestive", "severe", "moderate", [C.DX_XRAY, C.DX_PHYS], C.TX_SURGERY,
       [C.PR_PROBIO, C.PR_FLUID], prevalence=5),
    _d("cat-urinary-cystitis", "FIC", "Kistitis Interstisial (FIC)", "idiopathic",
       "urinary", "moderate", "high", [C.DX_URINE, C.DX_PHYS], C.TX_SUPPORT,
       [C.PR_FLUID, C.PR_MELOX], prevalence=14),
    _d("cat-urinary-stones", "Urolithiasis", "Batu Saluran Kemih", "metabolic",
       "urinary", "severe", "high", [C.DX_URINE, C.DX_XRAY], C.TX_SURGERY,
       [C.PR_FLUID, C.PR_ENRO], emergency=True, prevalence=10),
    _d("cat-chronic-kidney", "Chronic Kidney Disease", "Ginjal Kronik (CKD)", "degenerative",
       "urinary", "severe", "very_high", [C.DX_BLOOD, C.DX_URINE], C.TX_DIET,
       [C.PR_DIET_RX, C.PR_FURO], prevalence=22),
    _d("cat-flea-dermatitis", "Flea Bite Dermatitis", "Dermatitis Gigitan Kutu", "parasitic_external",
       "integumentary", "moderate", "high", [C.DX_SKIN, C.DX_PHYS], C.TX_PARASITE,
       [C.PR_IVER, C.PR_MELOX], prevalence=18),
    _d("cat-atopic-dermatitis", "Atopic Dermatitis", "Dermatitis Atopik", "environmental",
       "integumentary", "moderate", "moderate", [C.DX_SKIN, C.DX_HISTORY], C.TX_PHARMA,
       [C.PR_MELOX, C.PR_SALEP], prevalence=9),
    _d("cat-cutaneous-asthenia", "Cutaneous Asthenia", "Asthenia Kutaneus", "genetic_congenital",
       "integumentary", "moderate", "low", [C.DX_PHYS, C.DX_HISTORY], C.TX_SUPPORT,
       [C.PR_MELOX, C.PR_SALEP], prevalence=2),
    _d("cat-fibrosarcoma", "Injection Site Sarcoma", "Sarkoma Situs Injeksi", "neoplastic",
       "integumentary", "severe", "low", [C.DX_CYTO, C.DX_PHYS], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_FLUID], prevalence=2),
    _d("cat-mammary-tumor", "Mammary Tumor", "Tumor Mamaria", "neoplastic",
       "reproductive", "severe", "moderate", [C.DX_CYTO, C.DX_USG], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_FLUID], prevalence=5),
    _d("cat-oral-scc", "Oral Squamous Cell Carcinoma", "Karsinoma Sel Skuamosa Mulut", "neoplastic",
       "dental", "severe", "moderate", [C.DX_CYTO, C.DX_PHYS], C.TX_SURGERY,
       [C.PR_MELOX, C.PR_FLUID], prevalence=4),
    _d("cat-vestibular", "Vestibular Disease", "Gangguan Vestibular", "idiopathic",
       "nervous", "moderate", "moderate", [C.DX_PHYS, C.DX_HISTORY], C.TX_SUPPORT,
       [C.PR_MELOX, C.PR_FLUID], prevalence=6),
    _d("cat-hyperesthesia", "Feline Hyperesthesia", "Hiperestesia Kucing", "behavioral",
       "behavioral", "moderate", "moderate", [C.DX_HISTORY, C.DX_PHYS], C.TX_PHARMA,
       [C.PR_MELOX, C.PR_DIET_RX], prevalence=5),
    _d("cat-pica", "Pica", "Pica (makan benda tidak biasa)", "behavioral",
       "behavioral", "mild", "moderate", [C.DX_HISTORY, C.DX_XRAY], C.TX_SUPPORT,
       [C.PR_DIET_RX, C.PR_PROBIO], prevalence=4),
    _d("cat-lily-toxicity", "Lily Toxicity", "Toksik Lili", "toxic",
       "urinary", "critical", "moderate", [C.DX_BLOOD, C.DX_URINE], C.TX_FLUID,
       [C.PR_FLUID, C.PR_FURO], emergency=True, prevalence=4),
    _d("cat-paracetamol-toxicity", "Acetaminophen Toxicity", "Toksik Paracetamol", "toxic",
       "hematologic", "critical", "moderate", [C.DX_BLOOD, C.DX_HISTORY], C.TX_SUPPORT,
       [C.PR_FLUID, C.PR_ENRO], emergency=True, prevalence=3),
    _d("cat-bartonellosis", "Bartonellosis", "Bartonellosis", "infectious_bacterial",
       "systemic", "moderate", "moderate", [C.DX_SEROLOGY, C.DX_BLOOD], C.TX_PHARMA,
       [C.PR_ENRO, C.PR_ABX], zoonotic=True, prevalence=5),
]

_RABBIT_EXTRA_B2 = _batch_diseases("rabbit", "Kelinci", [
    ("pasteurellosis", "Pasteurellosis", "Pasteurellosis", "infectious_bacterial", "respiratory", "severe", "high", 16),
    ("encephalitozoonosis", "Encephalitozoonosis", "Encephalitozoonosis", "parasitic_internal", "nervous", "severe", "moderate", 7),
    ("fly-strike", "Fly Strike", "Myiasis (serangga)", "environmental", "integumentary", "severe", "moderate", 9),
    ("dental-malocclusion", "Dental Malocclusion", "Maloklusi Gigi", "genetic_congenital", "dental", "moderate", "high", 18),
    ("bladder-sludge", "Bladder Sludge", "Sludge Kandung Kemih", "metabolic", "urinary", "moderate", "high", 14),
    ("uterine-disorder", "Uterine Disorder", "Gangguan Uterus", "metabolic", "reproductive", "severe", "moderate", 10),
])

_POULTRY_EXTRA_B2 = _batch_diseases("poultry", "Unggas", [
    ("newcastle", "Newcastle Disease", "Penyakit Newcastle", "infectious_viral", "respiratory", "critical", "high", 12),
    ("fowl-pox", "Fowl Pox", "Cacar Unggas", "infectious_viral", "integumentary", "moderate", "high", 14),
    ("coryza", "Infectious Coryza", "Coriza Infeksius", "infectious_bacterial", "respiratory", "moderate", "high", 16),
    ("blackhead", "Blackhead Disease", "Penyakit Blackhead", "parasitic_internal", "digestive", "severe", "moderate", 8),
    ("egg-drop", "Egg Drop Syndrome", "Sindrom Penurunan Produksi Telur", "infectious_viral", "reproductive", "moderate", "high", 11),
    ("calcium-deficiency", "Calcium Deficiency", "Defisiensi Kalsium", "nutritional", "musculoskeletal", "severe", "high", 15),
    ("vent-gleet", "Vent Gleet", "Gleet (infeksi kloaka)", "infectious_bacterial", "reproductive", "moderate", "moderate", 10),
])

_FISH_EXTRA_B2 = _batch_diseases("fish", "Ikan", [
    ("velvet", "Velvet Disease", "Penyakit Velvet", "parasitic_external", "integumentary", "moderate", "high", 14),
    ("dropsy", "Dropsy", "Dropsy (ascites)", "infectious_bacterial", "systemic", "critical", "high", 12),
    ("fin-rot", "Fin Rot", "Busuk Sirip", "infectious_bacterial", "integumentary", "moderate", "high", 18),
    ("cloudy-eye", "Cloudy Eye", "Mata Keruh", "infectious_bacterial", "ophthalmic", "moderate", "moderate", 11),
    ("gas-bubble", "Gas Bubble Disease", "Penyakit Gelembung Gas", "environmental", "systemic", "severe", "moderate", 8),
    ("popeye-bacterial", "Bacterial Popeye", "Popeye Bakteri", "infectious_bacterial", "ophthalmic", "moderate", "moderate", 9),
])

_REPTILE_EXTRA_B2 = _batch_diseases("reptile", "Reptil", [
    ("cryptosporidiosis", "Cryptosporidiosis", "Kryptosporidiosis", "parasitic_internal", "digestive", "severe", "moderate", 7),
    ("metabolic-bone-advanced", "Advanced MBD", "MBD Lanjut", "nutritional", "musculoskeletal", "severe", "high", 20),
    ("dysecdysis", "Dysecdysis", "Gangguan Ganti Kulit", "environmental", "integumentary", "moderate", "high", 16),
    ("stomatitis-advanced", "Advanced Stomatitis", "Stomatitis Lanjut", "infectious_bacterial", "dental", "severe", "moderate", 10),
    ("respiratory-infection", "Respiratory Infection", "Infeksi Napas", "infectious_bacterial", "respiratory", "severe", "high", 18),
    ("parasites-external", "External Parasites", "Parasit Eksternal", "parasitic_external", "integumentary", "moderate", "high", 14),
])

EXTRA_BY_CATEGORY = {
    "dog": _DOG_EXTRA + _DOG_EXTRA_B2,
    "cat": _CAT_EXTRA + _CAT_EXTRA_B2,
    "rabbit": _RABBIT_EXTRA + _RABBIT_EXTRA_B2,
    "rabbit": _RABBIT_EXTRA,
    "hamster": _HAMSTER_EXTRA,
    "poultry": _POULTRY_EXTRA + _POULTRY_EXTRA_B2,
    "fish": _FISH_EXTRA + _FISH_EXTRA_B2,
    "reptile": _REPTILE_EXTRA + _REPTILE_EXTRA_B2,
    "amphibian": _AMPHIBIAN_EXTRA,
    "ferret": _FERRET_EXTRA,
    "guinea_pig": _GP_EXTRA,
}


def expand_clinical_catalog(base_clinical: dict) -> dict:
    """Gabungkan base CLINICAL + EXTRA; pastikan semua punya gejala."""
    merged = {}
    for cat, diseases in base_clinical.items():
        merged[cat] = [_ensure_symptoms_on_base(dict(d)) for d in diseases]
    for cat, extra in EXTRA_BY_CATEGORY.items():
        merged.setdefault(cat, [])
        existing_slugs = {d["slug"] for d in merged[cat]}
        for d in extra:
            if d["slug"] not in existing_slugs:
                merged[cat].append(d)
                existing_slugs.add(d["slug"])
    return merged
