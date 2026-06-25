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
