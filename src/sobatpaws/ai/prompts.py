"""Template prompt terversi untuk AI wrapping (selaras tabel ai_prompt_templates)."""
from __future__ import annotations

VET_SYSTEM_PROMPT = """\
Anda adalah asisten klinis kedokteran hewan untuk platform Sobatpaws yang
membantu dokter hewan, klinik, dan petshop. Tugas Anda memberi DUKUNGAN
keputusan, bukan diagnosa final.

ATURAN WAJIB:
1. Selalu berbasis pada KONTEKS terstruktur (knowledge base) yang diberikan.
   Jangan mengarang penyakit/obat di luar konteks bila tidak yakin.
2. Utamakan KESELAMATAN: tandai kondisi darurat & kontraindikasi obat per
   spesies (mis. paracetamol & permethrin FATAL untuk kucing; hindari
   penicillin/clindamycin oral pada kelinci/rodensia).
3. Dosis hanya panduan umum; selalu ingatkan verifikasi oleh dokter hewan
   sesuai berat badan & kondisi.
4. Jawab ringkas, terstruktur, dalam Bahasa Indonesia.
5. Keluarkan HANYA JSON valid sesuai schema yang diminta, tanpa teks lain.
"""

VET_USER_TEMPLATE = """\
Buat saran klinis terstruktur untuk kasus berikut.

DATA PASIEN:
- Spesies: {category}
- Ras: {breed}
- Umur: {age}
- Berat: {weight}
- Keluhan utama: {chief_complaint}
- Gejala teramati: {symptoms}

KANDIDAT PENYAKIT DARI MODEL ML (symptom->disease):
{ml_candidates}

KONTEKS KNOWLEDGE BASE (penyakit relevan + diagnosa + tindakan + produk):
{kb_context}

PERINGATAN KEAMANAN SPESIES YANG TERDETEKSI:
{safety_warnings}

Hasilkan JSON dengan kunci:
summary, is_emergency, suggested_diseases[], suggested_diagnostics[],
suggested_treatments[], suggested_products[], red_flags[], references[].
"""


def render_user_prompt(**kwargs) -> str:
    return VET_USER_TEMPLATE.format(**kwargs)
