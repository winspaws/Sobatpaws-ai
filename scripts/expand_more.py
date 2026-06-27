
import json, os, copy

CLINICAL = '/home/ubuntu/sobatpaws/data/clinical'

# Additional disease templates per species based on real veterinary knowledge
ADDITIONAL = {
    "diseases_dogs.json": [
        {"slug": "dog-canine-distemper", "name": "Canine Distemper", "name_id": "Distemper", "etiology": "infectious_viral", "body_system": "respiratory", "is_contagious": True, "is_zoonotic": False, "default_severity": "critical", "is_emergency": True, "overview": "Penyakit virus sistemik yang menyerang saluran pernapasan, pencernaan, dan saraf.", "causes": "Canine distemper virus (CDV), penularan aerosol.", "symptoms": [{"name": "Fever", "name_id": "Demam", "body_system": "systemic", "frequency": "very_high"}, {"name": "Nasal discharge", "name_id": "Ingus", "body_system": "respiratory", "frequency": "very_high"}, {"name": "Cough", "name_id": "Batuk", "body_system": "respiratory", "frequency": "high"}, {"name": "Seizures", "name_id": "Kejang", "body_system": "neurological", "frequency": "moderate", "is_red_flag": True}]},
        {"slug": "dog-hip-dysplasia", "name": "Hip Dysplasia", "name_id": "Hip Displasia", "etiology": "genetic_congenital", "body_system": "musculoskeletal", "is_contagious": False, "is_zoonotic": False, "default_severity": "moderate", "is_emergency": False, "overview": "Malformasi sendi panggul yang menyebabkan nyeri dan ketimpangan.", "causes": "Genetik, pertumbuhan cepat, obesitas.", "symptoms": [{"name": "Lameness", "name_id": "Pincang", "body_system": "musculoskeletal", "frequency": "very_high"}, {"name": "Difficulty standing", "name_id": "Susah berdiri", "body_system": "musculoskeletal", "frequency": "high"}]},
        {"slug": "dog-ear-infection", "name": "Otitis Externa", "name_id": "Infeksi Telinga", "etiology": "infectious_bacterial", "body_system": "auditory", "is_contagious": False, "is_zoonotic": False, "default_severity": "mild", "is_emergency": False, "overview": "Peradangan saluran telinga luar akibat bakteri atau jamur.", "causes": "Kelembaban, alergi, bentuk telinga.", "symptoms": [{"name": "Ear scratching", "name_id": "Garu telinga", "body_system": "auditory", "frequency": "very_high"}, {"name": "Head shaking", "name_id": "Geleng kepala", "body_system": "auditory", "frequency": "very_high"}]},
        {"slug": "dog-bloat-gdv", "name": "Gastric Dilatation-Volvulus", "name_id": "Bloat (Kembung Akut)", "etiology": "digestive_disorder", "body_system": "digestive", "is_contagious": False, "is_zoonotic": False, "default_severity": "critical", "is_emergency": True, "overview": "Kondisi darurat dimana lambung terpuntir dan mengembang.", "causes": "Makan terlalu cepat, exercise setelah makan.", "symptoms": [{"name": "Unproductive retching", "name_id": "Muntah kering", "body_system": "digestive", "frequency": "very_high", "is_red_flag": True}]},
        {"slug": "dog-heartworm", "name": "Heartworm Disease", "name_id": "Heartworm (Cacing Jantung)", "etiology": "parasitic", "body_system": "cardiovascular", "is_contagious": False, "is_zoonotic": False, "default_severity": "critical", "is_emergency": True, "overview": "Infeksi cacing Dirofilaria immitis di jantung dan pembuluh darah paru.", "causes": "Gigitan nyamuk terinfeksi.", "symptoms": [{"name": "Cough", "name_id": "Batuk", "body_system": "respiratory", "frequency": "very_high"}, {"name": "Exercise intolerance", "name_id": "Cepat lelah", "body_system": "systemic", "frequency": "high"}]},
    ],
    "diseases_cats.json": [
        {"slug": "cat-fiv", "name": "Feline Immunodeficiency Virus", "name_id": "FIV (AIDS Kucing)", "etiology": "infectious_viral", "body_system": "immune", "is_contagious": True, "is_zoonotic": False, "default_severity": "chronic", "is_emergency": False, "overview": "Virus imunodefisiensi kucing mirip HIV pada manusia.", "causes": "Gigitandan luka dalam, penularan vertikal.", "symptoms": [{"name": "Weight loss", "name_id": "Berat turun", "body_system": "systemic", "frequency": "very_high"}, {"name": "Chronic infections", "name_id": "Infeksi kronis", "body_system": "immune", "frequency": "high"}]},
        {"slug": "cat-fip", "name": "Feline Infectious Peritonitis", "name_id": "FIP", "etiology": "infectious_viral", "body_system": "systemic", "is_contagious": True, "is_zoonotic": False, "default_severity": "critical", "is_emergency": True, "overview": "Penyakit fatal akibat mutasi virus corona kucing.", "causes": "Mutasi FCoV, stres, usia muda.", "symptoms": [{"name": "Abdominal effusion", "name_id": "Perut buncit", "body_system": "digestive", "frequency": "very_high", "is_red_flag": True}]},
        {"slug": "cat-hyperthyroidism", "name": "Feline Hyperthyroidism", "name_id": "Hipertiroidisme", "etiology": "neoplastic", "body_system": "endocrine", "is_contagious": False, "is_zoonotic": False, "default_severity": "moderate", "is_emergency": False, "overview": "Produksi berlebih hormon tiroid pada kucing senior.", "causes": "Adenoma tiroid jinak.", "symptoms": [{"name": "Weight loss", "name_id": "BB turun", "body_system": "systemic", "frequency": "very_high"}, {"name": "Increased appetite", "name_id": "Nafsu makan naik", "body_system": "endocrine", "frequency": "very_high"}]},
        {"slug": "cat-ckd", "name": "Chronic Kidney Disease", "name_id": "Penyakit Ginjal Kronis", "etiology": "degenerative", "body_system": "urinary", "is_contagious": False, "is_zoonotic": False, "default_severity": "chronic", "is_emergency": False, "overview": "Penurunan fungsi ginjal progresif pada kucing senior.", "causes": "Usia, hipertensi, genetik.", "symptoms": [{"name": "Polyuria", "name_id": "Banyak kencing", "body_system": "urinary", "frequency": "very_high"}, {"name": "Polydipsia", "name_id": "Banyak minum", "body_system": "urinary", "frequency": "very_high"}]},
    ],
    "diseases_rabbits.json": [
        {"slug": "rabbit-snuffles", "name": "Snuffles (Pasteurellosis)", "name_id": "Snuffles", "etiology": "infectious_bacterial", "body_system": "respiratory", "is_contagious": True, "is_zoonotic": False, "default_severity": "moderate", "is_emergency": False, "overview": "Infeksi saluran pernapasan atas oleh Pasteurella multocida.", "causes": "Bakteri Pasteurella, stres, ventilasi buruk.", "symptoms": [{"name": "Sneezing", "name_id": "Bersin", "body_system": "respiratory", "frequency": "very_high"}, {"name": "Nasal discharge", "name_id": "Ingus", "body_system": "respiratory", "frequency": "very_high"}]},
        {"slug": "rabbit-malocclusion", "name": "Malocclusion", "name_id": "Maloklusi Gigi", "etiology": "genetic_congenital", "body_system": "dental", "is_contagious": False, "is_zoonotic": False, "default_severity": "moderate", "is_emergency": False, "overview": "Pertumbuhan gigi tidak normal yang mengganggu makan.", "causes": "Genetik, diet rendah serat.", "symptoms": [{"name": "Drooling", "name_id": "Ngeces", "body_system": "dental", "frequency": "very_high"}, {"name": "Weight loss", "name_id": "BB turun", "body_system": "systemic", "frequency": "high"}]},
    ],
}

total_added = 0
for fname, new_diseases in ADDITIONAL.items():
    fpath = os.path.join(CLINICAL, fname)
    with open(fpath) as f:
        data = json.load(f)
    
    existing = data.get('diseases', [])
    existing_slugs = {d['slug'] for d in existing}
    
    added = 0
    for d in new_diseases:
        if d['slug'] not in existing_slugs:
            existing.append(d)
            added += 1
            existing_slugs.add(d['slug'])
    
    data['diseases'] = existing
    with open(fpath, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    total_added += added
    print(f"{fname}: {len(existing)} diseases (+{added})")

total = sum(len(json.load(open(os.path.join(CLINICAL, f)))['diseases']) for f in os.listdir(CLINICAL) if f.startswith('diseases_'))
print(f"\n=== FINAL: {total} total diseases (+{total_added} new) ===")
