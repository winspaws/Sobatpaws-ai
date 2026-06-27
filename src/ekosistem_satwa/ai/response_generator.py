"""
Dynamic Response Generator — LLM-powered contextual responses untuk Pawnia agents.
Menggantikan template statis dengan respons dinamis yang tetap sesuai safety rules.
"""
import json, logging
from typing import Any, Optional
from .llm import LLMClient

logger = logging.getLogger("ekosistem_satwa.ai.response_generator")

# =============================================================================
# AGENT SYSTEM PROMPTS — Persona + Rules + Output Format
# =============================================================================

AGENT_PROMPTS = {
    "pet_companion": {
        "role": "Asisten kesehatan hewan peliharaan yang ramah, hangat, dan informatif",
        "rules": [
            "Sapa dengan hangat, gunakan nama hewan jika diketahui",
            "Respons harus kontekstual dengan pertanyaan pengguna",
            "Jika ada gejala serius, arahkan ke dokter hewan",
            "Gunakan Bahasa Indonesia yang alami, hindari template kaku",
        ],
    },
    "triage_emergency": {
        "role": "Dokter hewan darurat yang tenang, jelas, dan tegas",
        "rules": [
            "RESPON CEPAT DAN TEGAS — ini kondisi darurat",
            "Beri 3-5 langkah pertolongan pertama yang jelas dan actionable",
            "Jangan menenangkan berlebihan — urgency harus tersampaikan",
            "Sertakan red flags spesifik berdasarkan gejala yang disebutkan",
            "WAJIB: suruh segera ke klinik hewan terdekat",
        ],
    },
    "vet_escalation": {
        "role": "Asisten yang mendorong pengguna untuk konsultasi dengan dokter hewan",
        "rules": [
            "Jelaskan dengan empati MENGAPA perlu ke dokter berdasarkan gejala spesifik mereka",
            "Beri ringkasan informasi yang bisa dibawa ke dokter",
            "Jangan diagnosis — hanya jelaskan bahwa butuh pemeriksaan langsung",
            "Respons harus natural, jangan seperti template 'demi keamanan' terus",
        ],
    },
    "behavior_insight": {
        "role": "Spesialis perilaku hewan yang analitis dan solutif",
        "rules": [
            "Analisis perilaku berdasarkan gejala yang disebutkan secara SPESIFIK",
            "Gunakan pengetahuan dari behavioral_medicine.py untuk referensi",
            "Beri rekomendasi bertahap yang actionable",
            "Jika ada red flags, sampaikan dengan jelas tapi tidak menakut-nakuti",
            "Bahasa alami seperti konsultan perilaku, bukan template copy-paste",
        ],
    },
    "nutrition_advisor": {
        "role": "Ahli nutrisi hewan yang praktis dan berbasis evidence",
        "rules": [
            "Analisis kebiasaan makan berdasarkan info pengguna",
            "Rekomendasi harus konkret (bukan 'makanan sehat' tapi 'coba tambah pumpkin')",
            "Tanyakan detail yang relevan jika info kurang",
            "Peringatkan makanan berbahaya jika relevan",
        ],
    },
    "meal_planner": {
        "role": "Perencana diet hewan yang detail dan personal",
        "rules": [
            "Buat jadwal makan berdasarkan berat badan, usia, dan aktivitas",
            "Kalkulasi kalori jika informasi memadai",
            "Tawarkan variasi menu yang realistis",
            "Sertakan jadwal minum air",
        ],
    },
    "medication_adherence": {
        "role": "Asisten kepatuhan pengobatan yang suportif",
        "rules": [
            "Ingatkan jadwal obat dengan cara yang membantu",
            "Tanya kendala yang dihadapi (lupa, efek samping, susah kasih obat)",
            "Beri tips praktis berdasarkan jenis obat dan spesies",
            "Jangan pernah menyarankan perubahan dosis tanpa dokter",
        ],
    },
}

# =============================================================================
# FALLBACK TEMPLATES — When LLM is unavailable
# =============================================================================

FALLBACK = {
    "pet_companion": "Halo! Ada yang bisa Pawnia bantu untuk {pet_name} hari ini? 🐾",
    "triage_emergency": "🚨 {pet_name} memerlukan penanganan medis segera. Tetap tenang. Segera bawa ke klinik hewan terdekat.",
    "vet_escalation": "Berdasarkan info yang Anda sampaikan, {pet_name} sebaiknya diperiksa langsung oleh dokter hewan untuk penanganan yang tepat.",
    "behavior_insight": "Terima kasih sudah memperhatikan perubahan perilaku {pet_name}. Bisa cerita lebih detail tentang apa yang terjadi?",
    "behavior_fun": "Haha, {pet_name} pasti lucu sekali! 🐾",
    "nutrition_advisor": "Mari lihat kebutuhan nutrisi {pet_name}! Apa yang biasanya {pet_name} makan?",
    "meal_planner": "Ayo buat jadwal makan untuk {pet_name}! Berapa berat badan {pet_name} saat ini?",
    "medication_adherence": "Halo! Ada yang bisa dibantu soal jadwal pengobatan {pet_name}?",
    "vision_screening": "👁️ Foto {pet_name} sudah diterima. Mari saya analisis...",
}


def generate_response(
    agent_type: str,
    pet_name: str,
    user_text: str,
    context: Optional[dict] = None,
    llm_client: Optional[LLMClient] = None,
    required_structure: Optional[dict] = None,
) -> dict:
    """
    Generate response dinamis menggunakan LLM, dengan fallback template.
    
    Returns dict dengan keys: text, suggestions, cta, disclaimer, (opsional: red_flags)
    """
    context = context or {}
    
    # Try LLM first
    if llm_client and llm_client.available:
        try:
            return _generate_with_llm(agent_type, pet_name, user_text, context, llm_client)
        except Exception as e:
            logger.warning(f"LLM response failed for {agent_type}: {e}, using fallback")
    
    # Fallback ke template
    return _generate_fallback(agent_type, pet_name, user_text, context)


def _generate_with_llm(
    agent_type: str,
    pet_name: str,
    user_text: str,
    context: dict,
    llm: LLMClient,
) -> dict:
    """Generate response menggunakan LLM dengan structured output."""
    
    agent_info = AGENT_PROMPTS.get(agent_type, AGENT_PROMPTS["pet_companion"])
    rules_text = "\n".join(f"- {r}" for r in agent_info["rules"])
    
    # Context info
    species = context.get("proprietary", {}).get("species", "")
    breed = context.get("proprietary", {}).get("breed", "")
    age = context.get("proprietary", {}).get("age", "")
    pet_context = f"Spesies: {species}, Ras: {breed}, Usia: {age}" if any([species, breed, age]) else "Informasi hewan terbatas"
    
    system_prompt = f"""Kamu adalah {agent_info["role"]} dalam platform Pawnia AI — asisten kesehatan hewan peliharaan Indonesia.

ATURAN:
{rules_text}

PENTING:
- RESPON DALAM BAHASA INDONESIA yang alami, hangat, dan kontekstual
- Jangan gunakan template atau kalimat yang diulang-ulang
- Sesuaikan gaya bicara dengan situasi (tenang untuk darurat, hangat untuk umum)
- Gunakan emoji secukupnya, jangan berlebihan
- Jangan menyebut dirimu "Pawnia" atau "AI" — kamu adalah asisten
- Panjang respon: 50-200 kata, sesuai kebutuhan

OUTPUT FORMAT (JSON):
{{
    "text": "Respon utama dalam Bahasa Indonesia yang natural dan kontekstual",
    "suggestions": ["Saran 1", "Saran 2", "Saran 3"],
    "cta_label": "Label tombol (jika perlu tindakan)",
    "cta_endpoint": "Endpoint API (jika perlu)",
    "has_disclaimer": true/false,
    "custom_disclaimer": "Jika ada disclaimer khusus, atau kosongkan"
}}"""

    user_prompt = f"""Konteks hewan: {pet_context}
Nama hewan: {pet_name}
Pertanyaan pengguna: {user_text}"""

    result = llm.chat_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        operation=f"response_{agent_type}",
    )
    
    if result and isinstance(result, dict) and "text" in result:
        # Build standard response structure
        response = {
            "text": result.get("text", ""),
            "suggestions": result.get("suggestions", []),
            "cta": [],
            "disclaimer": "",
        }
        
        # Add CTA if present
        if result.get("cta_label") and result.get("cta_endpoint"):
            response["cta"].append({
                "type": "action",
                "label": result["cta_label"],
                "endpoint": result["cta_endpoint"],
            })
        
        # Add disclaimer if flagged
        if result.get("has_disclaimer", True):
            response["disclaimer"] = result.get(
                "custom_disclaimer",
                "Informasi ini bersifat informatif dan bukan pengganti konsultasi dokter hewan."
            )
        
        return response
    
    raise ValueError("LLM returned invalid response structure")


def _generate_fallback(
    agent_type: str,
    pet_name: str,
    user_text: str,
    context: dict,
) -> dict:
    """Fallback response menggunakan template sederhana."""
    template = FALLBACK.get(agent_type, FALLBACK["pet_companion"])
    text = template.format(pet_name=pet_name)
    
    # Default structure yang aman
    base = {
        "text": text,
        "suggestions": ["Ceritakan lebih detail", "Konsultasi dengan dokter hewan"],
        "cta": [],
        "disclaimer": "Informasi ini bersifat informatif dan bukan pengganti konsultasi dokter hewan.",
    }
    
    # Agent-specific CTAs
    if agent_type in ("triage_emergency",):
        base["cta"].append({"type": "emergency", "label": "Cari Klinik Terdekat", "endpoint": "/api/v1/clinics/nearby"})
        base["cta"].append({"type": "teleconsult", "label": "Hubungi Dokter Darurat", "endpoint": "/api/v1/teleconsult/emergency"})
    elif agent_type in ("vet_escalation", "behavior_insight"):
        base["cta"].append({"type": "teleconsult", "label": "💬 Konsultasi dengan Dokter", "endpoint": "/api/v1/teleconsult"})
    
    return base
