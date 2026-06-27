
import json, os
CLINICAL = '/home/ubuntu/sobatpaws/data/clinical'

BULK = {
    "diseases_dogs.json": [
        {"slug": "dog-pancreatitis", "name": "Pancreatitis", "name_id": "Pankreatitis", "etiology": "digestive_disorder", "body_system": "digestive", "is_contagious": False, "is_zoonotic": False, "default_severity": "critical", "is_emergency": True, "overview": "Radang pankreas akut.", "symptoms": [{"name": "Vomiting", "name_id": "Muntah", "body_system": "digestive", "frequency": "very_high"}]},
        {"slug": "dog-demodicosis", "name": "Demodicosis", "name_id": "Demodek", "etiology": "parasitic", "body_system": "integumentary", "is_contagious": False, "is_zoonotic": False, "default_severity": "mild", "is_emergency": False, "overview": "Tungau kulit Demodex.", "symptoms": [{"name": "Hair loss", "name_id": "Rontok bulu", "body_system": "integumentary", "frequency": "very_high"}]},
        {"slug": "dog-glaucoma", "name": "Glaucoma", "name_id": "Glaukoma", "etiology": "degenerative", "body_system": "ocular", "is_contagious": False, "is_zoonotic": False, "default_severity": "critical", "is_emergency": True, "overview": "Tekanan bola mata meningkat.", "symptoms": [{"name": "Red eye", "name_id": "Mata merah", "body_system": "ocular", "frequency": "very_high", "is_red_flag": True}]},
        {"slug": "dog-epilepsy", "name": "Idiopathic Epilepsy", "name_id": "Epilepsi", "etiology": "idiopathic", "body_system": "neurological", "is_contagious": False, "is_zoonotic": False, "default_severity": "moderate", "is_emergency": False, "overview": "Kejang berulang tanpa penyebab organik.", "symptoms": [{"name": "Seizures", "name_id": "Kejang", "body_system": "neurological", "frequency": "very_high", "is_red_flag": True}]},
        {"slug": "dog-cushings", "name": "Cushing's Syndrome", "name_id": "Cushing", "etiology": "endocrine", "body_system": "endocrine", "is_contagious": False, "is_zoonotic": False, "default_severity": "moderate", "is_emergency": False, "overview": "Produksi kortisol berlebih.", "symptoms": [{"name": "Increased thirst", "name_id": "Banyak minum", "body_system": "endocrine", "frequency": "very_high"}]},
        {"slug": "dog-addisons", "name": "Addison's Disease", "name_id": "Addison", "etiology": "endocrine", "body_system": "endocrine", "is_contagious": False, "is_zoonotic": False, "default_severity": "critical", "is_emergency": True, "overview": "Defisiensi kortisol.", "symptoms": [{"name": "Collapse", "name_id": "Kolaps", "body_system": "systemic", "frequency": "very_high", "is_red_flag": True}]},
        {"slug": "dog-hypothyroidism", "name": "Hypothyroidism", "name_id": "Hipotiroidisme", "etiology": "endocrine", "body_system": "endocrine", "is_contagious": False, "is_zoonotic": False, "default_severity": "mild", "is_emergency": False, "overview": "Produksi hormon tiroid kurang.", "symptoms": [{"name": "Weight gain", "name_id": "Gemuk", "body_system": "systemic", "frequency": "very_high"}]},
        {"slug": "dog-cataract", "name": "Cataract", "name_id": "Katarak", "etiology": "degenerative", "body_system": "ocular", "is_contagious": False, "is_zoonotic": False, "default_severity": "mild", "is_emergency": False, "overview": "Lensa mata keruh.", "symptoms": [{"name": "Cloudy eye", "name_id": "Mata keruh", "body_system": "ocular", "frequency": "very_high"}]},
        {"slug": "dog-bronchitis", "name": "Chronic Bronchitis", "name_id": "Bronkitis Kronis", "etiology": "degenerative", "body_system": "respiratory", "is_contagious": False, "is_zoonotic": False, "default_severity": "moderate", "is_emergency": False, "overview": "Batuk kronis pada anjing.", "symptoms": [{"name": "Chronic cough", "name_id": "Batuk kronis", "body_system": "respiratory", "frequency": "very_high"}]},
        {"slug": "dog-cornel-ulcer", "name": "Corneal Ulcer", "name_id": "Ulkus Kornea", "etiology": "traumatic", "body_system": "ocular", "is_contagious": False, "is_zoonotic": False, "default_severity": "moderate", "is_emergency": True, "overview": "Luka pada kornea.", "symptoms": [{"name": "Eye discharge", "name_id": "Belekan", "body_system": "ocular", "frequency": "very_high"}]},
    ],
    "diseases_cats.json": [
        {"slug": "cat-diabetes", "name": "Feline Diabetes Mellitus", "name_id": "Diabetes Kucing", "etiology": "endocrine", "body_system": "endocrine", "is_contagious": False, "is_zoonotic": False, "default_severity": "moderate", "is_emergency": False, "overview": "Gangguan metabolisme insulin.", "symptoms": [{"name": "Polyuria", "name_id": "Banyak kencing", "body_system": "urinary", "frequency": "very_high"}, {"name": "Polydipsia", "name_id": "Banyak minum", "body_system": "urinary", "frequency": "very_high"}]},
        {"slug": "cat-asthma", "name": "Feline Asthma", "name_id": "Asma Kucing", "etiology": "allergic_immune", "body_system": "respiratory", "is_contagious": False, "is_zoonotic": False, "default_severity": "moderate", "is_emergency": True, "overview": "Penyempitan saluran napas akibat alergi.", "symptoms": [{"name": "Coughing", "name_id": "Batuk", "body_system": "respiratory", "frequency": "very_high"}, {"name": "Wheezing", "name_id": "Mengi", "body_system": "respiratory", "frequency": "high"}]},
        {"slug": "cat-gingivitis", "name": "Feline Gingivitis", "name_id": "Radang Gusi", "etiology": "infectious_bacterial", "body_system": "dental", "is_contagious": False, "is_zoonotic": False, "default_severity": "mild", "is_emergency": False, "overview": "Peradangan gusi kronis.", "symptoms": [{"name": "Red gums", "name_id": "Gusi merah", "body_system": "dental", "frequency": "very_high"}]},
        {"slug": "cat-constipation", "name": "Feline Constipation", "name_id": "Konstipasi Kucing", "etiology": "digestive_disorder", "body_system": "digestive", "is_contagious": False, "is_zoonotic": False, "default_severity": "mild", "is_emergency": False, "overview": "Kesulitan buang air besar.", "symptoms": [{"name": "Straining", "name_id": "Ngeden pup", "body_system": "digestive", "frequency": "very_high"}, {"name": "Hard stool", "name_id": "Kotoran keras", "body_system": "digestive", "frequency": "very_high"}]},
        {"slug": "cat-food-allergy", "name": "Food Allergy", "name_id": "Alergi Makanan", "etiology": "allergic_immune", "body_system": "integumentary", "is_contagious": False, "is_zoonotic": False, "default_severity": "mild", "is_emergency": False, "overview": "Reaksi alergi terhadap protein dalam makanan.", "symptoms": [{"name": "Pruritus", "name_id": "Gatal", "body_system": "integumentary", "frequency": "very_high"}, {"name": "Facial itching", "name_id": "Gatal muka", "body_system": "integumentary", "frequency": "high"}]},
    ],
    "diseases_fish.json": [
        {"slug": "fish-hole-in-head", "name": "Hole in the Head (Hexamita)", "name_id": "Hexamita", "etiology": "parasitic", "body_system": "integumentary", "is_contagious": True, "is_zoonotic": False, "default_severity": "moderate", "is_emergency": False, "overview": "Infeksi protozoa yang menyebabkan lubang di kepala.", "symptoms": [{"name": "Pits on head", "name_id": "Lubang di kepala", "body_system": "integumentary", "frequency": "very_high"}]},
        {"slug": "fish-velvet", "name": "Velvet Disease", "name_id": "Beludru", "etiology": "parasitic", "body_system": "integumentary", "is_contagious": True, "is_zoonotic": False, "default_severity": "moderate", "is_emergency": False, "overview": "Parasit Oodinium yang memberi kesan debu emas.", "symptoms": [{"name": "Gold dust", "name_id": "Debu emas di kulit", "body_system": "integumentary", "frequency": "very_high"}]},
        {"slug": "fish-bacterial-hemorrhagic", "name": "Hemorrhagic Septicemia", "name_id": "Septikemia Hemoragik", "etiology": "infectious_bacterial", "body_system": "systemic", "is_contagious": True, "is_zoonotic": False, "default_severity": "critical", "is_emergency": True, "overview": "Infeksi bakteri sistemik.", "symptoms": [{"name": "Red spots", "name_id": "Bercak merah", "body_system": "integumentary", "frequency": "very_high", "is_red_flag": True}]},
    ],
    "diseases_reptiles.json": [
        {"slug": "reptile-paramyxovirus", "name": "Paramyxovirus", "name_id": "Paramyxovirus", "etiology": "infectious_viral", "body_system": "respiratory", "is_contagious": True, "is_zoonotic": False, "default_severity": "critical", "is_emergency": True, "overview": "Virus pada ular.", "symptoms": [{"name": "Regurgitation", "name_id": "Muntah", "body_system": "digestive", "frequency": "very_high", "is_red_flag": True}]},
        {"slug": "reptile-egg-binding", "name": "Egg Binding (Dystocia)", "name_id": "Telur Nyangkut", "etiology": "reproductive", "body_system": "reproductive", "is_contagious": False, "is_zoonotic": False, "default_severity": "critical", "is_emergency": True, "overview": "Telur tidak bisa dikeluarkan.", "symptoms": [{"name": "Straining", "name_id": "Ngeden", "body_system": "reproductive", "frequency": "very_high", "is_red_flag": True}]},
        {"slug": "reptile-hypovitaminosis", "name": "Hypovitaminosis A", "name_id": "Defisiensi Vitamin A", "etiology": "metabolic_nutritional", "body_system": "systemic", "is_contagious": False, "is_zoonotic": False, "default_severity": "moderate", "is_emergency": False, "overview": "Kekurangan vitamin A pada kura-kura.", "symptoms": [{"name": "Swollen eyes", "name_id": "Mata bengkak", "body_system": "ocular", "frequency": "very_high"}]},
    ],
    "diseases_poultry.json": [
        {"slug": "poultry-sour-crop", "name": "Sour Crop", "name_id": "Tembolok Asam", "etiology": "infectious_fungal", "body_system": "digestive", "is_contagious": False, "is_zoonotic": False, "default_severity": "moderate", "is_emergency": False, "overview": "Infeksi jamur pada tembolok.", "symptoms": [{"name": "Bad breath", "name_id": "Bau mulut", "body_system": "digestive", "frequency": "very_high"}]},
        {"slug": "poultry-bumblefoot", "name": "Bumblefoot", "name_id": "Kaki Bengkak", "etiology": "infectious_bacterial", "body_system": "musculoskeletal", "is_contagious": False, "is_zoonotic": False, "default_severity": "moderate", "is_emergency": False, "overview": "Infeksi telapak kaki.", "symptoms": [{"name": "Limping", "name_id": "Pincang", "body_system": "musculoskeletal", "frequency": "very_high"}]},
        {"slug": "poultry-pox", "name": "Fowl Pox", "name_id": "Cacar Unggas", "etiology": "infectious_viral", "body_system": "integumentary", "is_contagious": True, "is_zoonotic": False, "default_severity": "moderate", "is_emergency": False, "overview": "Virus cacar pada unggas.", "symptoms": [{"name": "Warts", "name_id": "Kutil", "body_system": "integumentary", "frequency": "very_high"}]},
    ],
    "diseases_ferret.json": [
        {"slug": "ferret-lymphoma", "name": "Lymphoma", "name_id": "Limfoma", "etiology": "neoplastic", "body_system": "immune", "is_contagious": False, "is_zoonotic": False, "default_severity": "critical", "is_emergency": True, "overview": "Kanker sistem limfatik.", "symptoms": [{"name": "Lymph node swelling", "name_id": "Kelenjar bengkak", "body_system": "immune", "frequency": "very_high", "is_red_flag": True}]},
        {"slug": "ferret-prostate", "name": "Prostatic Disease", "name_id": "Penyakit Prostat", "etiology": "neoplastic", "body_system": "reproductive", "is_contagious": False, "is_zoonotic": False, "default_severity": "moderate", "is_emergency": False, "overview": "Pembesaran prostat pada musang jantan.", "symptoms": [{"name": "Difficulty urinating", "name_id": "Susah kencing", "body_system": "urinary", "frequency": "very_high"}]},
    ],
}

total_added = 0
for fname, new_diseases in BULK.items():
    fpath = os.path.join(CLINICAL, fname)
    with open(fpath) as f:
        data = json.load(f)
    existing = data['diseases']
    slugs = {d['slug'] for d in existing}
    added = sum(1 for d in new_diseases if d['slug'] not in slugs)
    data['diseases'].extend(d for d in new_diseases if d['slug'] not in slugs)
    with open(fpath, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    total_added += added
    print(f"{fname}: {len(data['diseases'])} diseases (+{added})")

total = 0
for f in os.listdir(CLINICAL):
    if f.startswith('diseases_'):
        total += len(json.load(open(os.path.join(CLINICAL, f)))['diseases'])
print(f"\n=== FINAL: {total} total diseases (+{total_added} new) ===")
assert total >= 200
