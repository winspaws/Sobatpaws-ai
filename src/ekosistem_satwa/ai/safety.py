"""Guardrail keselamatan: kontraindikasi obat per spesies & deteksi darurat.

Ini lapisan kritis: AI/ML TIDAK boleh menyarankan produk yang berbahaya untuk
spesies tertentu. Aturan di sini bersifat hard-rule (selalu diterapkan).
"""
from __future__ import annotations

# Bahan aktif berbahaya/kontraindikasi per spesies (lowercase match)
SPECIES_CONTRAINDICATIONS: dict[str, list[dict]] = {
    "cat": [
        {"ingredient": "paracetamol", "note": "FATAL untuk kucing (methemoglobinemia). Jangan diberikan."},
        {"ingredient": "acetaminophen", "note": "FATAL untuk kucing. Jangan diberikan."},
        {"ingredient": "permethrin", "note": "Sangat toksik untuk kucing (produk anjing). Bisa fatal."},
        {"ingredient": "ibuprofen", "note": "Toksik; margin keamanan NSAID sangat sempit pada kucing."},
        {"ingredient": "aspirin", "note": "Metabolisme lambat; hanya dosis sangat hati-hati oleh vet."},
    ],
    "dog": [
        {"ingredient": "xylitol", "note": "Toksik untuk anjing (hipoglikemia/gagal hati)."},
        {"ingredient": "permethrin", "note": "Umumnya aman anjing, tetapi JANGAN aplikasikan ke kucing serumah."},
    ],
    "rabbit": [
        {"ingredient": "amoxicillin", "note": "Antibiotik oral penicillin -> enterotoxemia fatal pada kelinci."},
        {"ingredient": "penicillin", "note": "Oral berbahaya (dysbiosis fatal). Hindari per oral."},
        {"ingredient": "clindamycin", "note": "Menyebabkan enterotoxemia fatal pada kelinci."},
        {"ingredient": "lincomycin", "note": "Berbahaya bagi flora usus kelinci."},
    ],
    "hamster": [
        {"ingredient": "amoxicillin", "note": "Berbahaya bagi rodensia (dysbiosis)."},
        {"ingredient": "penicillin", "note": "Toksik bagi rodensia."},
        {"ingredient": "clindamycin", "note": "Toksik bagi rodensia."},
    ],
    "guinea_pig": [
        {"ingredient": "penicillin", "note": "FATAL untuk marmut (enterotoxemia)."},
        {"ingredient": "amoxicillin", "note": "FATAL untuk marmut."},
        {"ingredient": "clindamycin", "note": "FATAL untuk marmut."},
    ],
}


def check_product_safety(category_slug: str, active_ingredient: str | None) -> str | None:
    """Kembalikan peringatan bila bahan aktif kontraindikasi untuk spesies."""
    if not active_ingredient:
        return None
    ing = active_ingredient.lower()
    for rule in SPECIES_CONTRAINDICATIONS.get(category_slug, []):
        if rule["ingredient"] in ing:
            return f"PERINGATAN ({rule['ingredient']}): {rule['note']}"
    return None


def collect_safety_warnings(category_slug: str) -> list[str]:
    """Daftar peringatan umum spesies untuk disuntikkan ke prompt LLM."""
    return [f"{r['ingredient']}: {r['note']}"
            for r in SPECIES_CONTRAINDICATIONS.get(category_slug, [])]


# =============================================================================
# BREED-SPECIFIC RISK PROFILES
# =============================================================================

BREED_DRUG_RISKS: dict[str, list[dict]] = {
    # MDR1 mutation — sensitif terhadap ivermectin dosis tinggi
    "collie": [
        {"drug": "ivermectin", "note": "Mutasi MDR1: dosis tinggi ivermectin bisa fatal. Gunakan alternatif (milbemycin)."},
        {"drug": "loperamide", "note": "Mutasi MDR1: loperamide bisa menyebabkan toksisitas neurologis."},
    ],
    "border collie": [
        {"drug": "ivermectin", "note": "Risiko mutasi MDR1: hindari dosis tinggi ivermectin."},
    ],
    "australian shepherd": [
        {"drug": "ivermectin", "note": "Risiko mutasi MDR1: hindari dosis tinggi ivermectin."},
    ],
    "shetland sheepdog": [
        {"drug": "ivermectin", "note": "Risiko mutasi MDR1: hindari dosis tinggi ivermectin."},
    ],
    # Brachycephalic — risiko anestesi
    "bulldog": [
        {"drug": "anesthesia", "note": "Ras brachycephalic: risiko tinggi komplikasi anestesi. Perlu monitoring ekstra."},
    ],
    "pug": [
        {"drug": "anesthesia", "note": "Ras brachycephalic: risiko tinggi komplikasi anestesi."},
    ],
    "persian": [
        {"drug": "anesthesia", "note": "Ras brachycephalic: risiko anestesi lebih tinggi."},
    ],
}


def check_breed_risks(breed: str | None) -> list[str]:
    """Peringatan risiko obat berdasarkan ras hewan."""
    if not breed:
        return []
    breed_lower = breed.lower()
    warnings: list[str] = []
    for breed_key, risks in BREED_DRUG_RISKS.items():
        if breed_key in breed_lower:
            for r in risks:
                warnings.append(f"Peringatan ras ({breed}): {r['note']}")
    return warnings


def check_allergy_conflicts(
    allergies: list[str] | None,
    active_medications: list[dict] | None,
) -> list[str]:
    """Cek apakah obat aktif mengandung zat yang pasien alergi."""
    if not allergies or not active_medications:
        return []
    warnings: list[str] = []
    allergy_lower = [a.lower() for a in allergies]
    for med in active_medications:
        med_name = (med.get("name") or "").lower()
        generic = (med.get("generic_name") or "").lower()
        for allergy in allergy_lower:
            if allergy in med_name or allergy in generic:
                warnings.append(
                    f"⚠️ ALERGI: Pasien alergi terhadap '{allergy}' tetapi sedang menggunakan obat '{med.get('name')}'. "
                    f"SEGERA konsultasi dokter hewan!"
                )
    return warnings


def check_drug_interactions(active_medications: list[dict] | None) -> list[str]:
    """Deteksi interaksi obat yang diketahui berbahaya."""
    if not active_medications or len(active_medications) < 2:
        return []

    KNOWN_INTERACTIONS = [
        ({"nsaid", "ibuprofen", "meloxicam", "carprofen", "firocoxib"},
         {"corticosteroid", "prednisone", "prednisolone", "dexamethasone"},
         "NSAID + Corticosteroid: risiko tinggi ulkus gastrointestinal dan perdarahan."),
        ({"ace inhibitor", "enalapril", "benazepril"},
         {"nsaid", "ibuprofen", "meloxicam", "carprofen"},
         "ACE Inhibitor + NSAID: dapat menurunkan efektivitas ACE inhibitor dan merusak ginjal."),
        ({"furosemide", "diuretik"},
         {"aminoglycoside", "gentamicin", "amikacin"},
         "Diuretik + Aminoglycoside: risiko ototoksisitas dan nefrotoksisitas meningkat."),
    ]

    warnings: list[str] = []
    med_names: list[str] = []
    for m in active_medications:
        med_names.append((m.get("name") or "").lower())
        med_names.append((m.get("generic_name") or "").lower())
        med_names.append((m.get("category") or "").lower())

    med_text = " ".join(med_names)
    for group_a, group_b, warning in KNOWN_INTERACTIONS:
        has_a = any(drug in med_text for drug in group_a)
        has_b = any(drug in med_text for drug in group_b)
        if has_a and has_b:
            warnings.append(f"⚠️ INTERAKSI OBAT: {warning}")

    return warnings


def check_age_risk(species: str, age_years: float | None) -> list[str]:
    """Peringatan berdasarkan usia ekstrem (neonatal/geriatrik)."""
    if age_years is None:
        return []
    warnings: list[str] = []
    # Neonatal
    if age_years < 0.25:
        warnings.append(
            "Pasien NEONATAL (<3 bulan): metabolisme obat belum matang. "
            "Dosis harus disesuaikan secara hati-hati oleh dokter hewan."
        )
    # Geriatrik
    senior_age = {"dog": 8, "cat": 10, "rabbit": 6, "hamster": 1.5, "guinea_pig": 5}
    threshold = senior_age.get(species, 8)
    if age_years >= threshold:
        warnings.append(
            f"Pasien GERIATRIK ({age_years} tahun): fungsi hati & ginjal mungkin menurun. "
            f"Dosis obat perlu penyesuaian dan monitoring lebih ketat."
        )
    return warnings


def check_contraindications_from_context(pet_context: dict) -> list[str]:
    """Kumpulkan semua peringatan keselamatan berdasarkan data pet nyata.

    Dipanggil oleh response_generator untuk disuntikkan ke prompt LLM.
    """
    if not pet_context:
        return []

    warnings: list[str] = []
    species = (pet_context.get("species") or "").lower()
    breed = pet_context.get("breed")
    age = pet_context.get("age_years")
    allergies = pet_context.get("allergies")
    meds = pet_context.get("active_medications")

    # 1. Cek kontraindikasi obat aktif vs spesies
    if meds and species:
        for med in meds:
            generic = med.get("generic_name") or med.get("name") or ""
            warning = check_product_safety(species, generic)
            if warning:
                warnings.append(warning)

    # 2. Cek breed-specific drug risks
    warnings.extend(check_breed_risks(breed))

    # 3. Cek alergi vs obat aktif
    warnings.extend(check_allergy_conflicts(allergies, meds))

    # 4. Cek interaksi obat
    warnings.extend(check_drug_interactions(meds))

    # 5. Cek risiko usia
    warnings.extend(check_age_risk(species, age))

    return warnings
