"""Respons Pawnia — template dulu, LLM hanya jika token_policy mengizinkan.

Prompt disingkat sengaja agar hemat token SumoPod.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from .llm import LLMClient
from .telemetry import get_telemetry
from .token_policy import compact_pet_context, should_use_llm_pawnia, token_budget_for

logger = logging.getLogger("ekosistem_satwa.ai.response_generator")

# Prompt super pendek per agent (hemat input token)
_ROLE = {
    "pet_companion": "Asisten vet ramah ID. Jangan diagnosis pasti.",
    "triage_emergency": "Triage darurat. Tenang, langkah singkat, suruh ke klinik.",
    "vet_escalation": "Dorong telekonsultasi. Empati, tanpa diagnosis pasti.",
    "behavior_insight": "Spesialis perilaku hewan. Saran bertahap, red flag jika ada.",
    "nutrition_advisor": "Ahli nutrisi hewan. Saran konkret, sebut alergen jika relevan.",
    "meal_planner": "Perencana porsi makan hewan.",
    "medication_adherence": "Pengingat obat/vaksin. Jangan ubah dosis.",
    "behavior_fun": "Asisten fun pet translator, ringan.",
    "vision_screening": "Screening foto. Disclaimer medis wajib.",
}


def generate_response(
    agent_type: str,
    pet_name: str,
    user_text: str,
    context: Optional[dict] = None,
    llm_client: Optional[LLMClient] = None,
    required_structure: Optional[dict] = None,
    *,
    intent_confidence: float = 0.0,
    risk_score: int = 0,
) -> dict:
    context = context or {}
    decision = should_use_llm_pawnia(
        agent_type=agent_type,
        user_text=user_text,
        intent_confidence=intent_confidence,
        risk_score=risk_score,
    )
    telemetry = get_telemetry()

    if not decision.use_llm or not llm_client or not llm_client.available:
        if not decision.use_llm:
            telemetry.record_skip(
                "pawnia_chat",
                decision.reason,
                provider=getattr(llm_client, "provider", "") if llm_client else "",
                model=getattr(llm_client, "model", "") if llm_client else "",
            )
        kb_resp = _try_kb_brief(agent_type, pet_name, user_text, context)
        if kb_resp:
            kb_resp.setdefault("token_reason", "kb_ml")
            return kb_resp
        fallback = _generate_fallback(agent_type, pet_name, user_text, context)
        fallback["token_reason"] = decision.reason
        return fallback

    try:
        result = _generate_with_llm(
            agent_type, pet_name, user_text, context, llm_client, decision.max_tokens,
        )
        if result:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM Pawnia gagal (%s): %s — fallback template", agent_type, exc)

    fallback = _generate_fallback(agent_type, pet_name, user_text, context)
    fallback["token_reason"] = "llm_failed"
    return fallback


def _format_pet_context_for_prompt(context: dict) -> str:
    """Format data pet dari DB menjadi section prompt yang informatif untuk LLM."""
    prop = context.get("proprietary", {})
    if not prop:
        return "Informasi hewan terbatas — data medis belum tersedia."

    parts: list[str] = []

    # Identitas dasar
    name = prop.get("name", "")
    species = prop.get("species", "")
    breed = prop.get("breed", "")
    age = prop.get("age_years")
    weight = prop.get("weight_kg")
    sex = prop.get("sex", "")
    neutered = prop.get("neutered")

    identity = f"Nama: {name}" if name else ""
    if species:
        identity += f" | Spesies: {species}"
    if breed:
        identity += f" | Ras: {breed}"
    if age is not None:
        identity += f" | Umur: {age} tahun"
    if weight:
        identity += f" | Berat: {weight} kg"
    if sex:
        identity += f" | Kelamin: {sex}"
    if neutered is not None:
        identity += f" | Steril: {'Ya' if neutered else 'Tidak'}"
    if identity:
        parts.append(f"## Data Pasien\n{identity}")

    # Alergi
    allergies = prop.get("allergies") or []
    if allergies:
        parts.append(f"## Alergi (PENTING)\n⚠️ {', '.join(allergies)}")

    # Kondisi kronis
    chronic = prop.get("chronic_conditions") or []
    if chronic:
        parts.append(f"## Kondisi Kronis\n{', '.join(chronic)}")

    # Obat aktif
    meds = prop.get("active_medications") or []
    if meds:
        med_lines = []
        for m in meds[:5]:
            line = f"- {m.get('name', '?')}"
            if m.get("dosage"):
                line += f" ({m['dosage']}"
                if m.get("frequency"):
                    line += f", {m['frequency']}"
                line += ")"
            if m.get("route"):
                line += f" via {m['route']}"
            med_lines.append(line)
        parts.append("## Obat Aktif Saat Ini\n" + "\n".join(med_lines))

    # Riwayat kunjungan terakhir
    visits = prop.get("recent_visits") or []
    if visits:
        visit_lines = []
        for v in visits[:3]:
            vdate = v.get("date", "?")
            complaint = v.get("complaint", "-")
            diagnosis = v.get("diagnosis", "-")
            visit_lines.append(f"- [{vdate}] Keluhan: {complaint} → Diagnosis: {diagnosis}")
        parts.append("## Riwayat Medis Terakhir\n" + "\n".join(visit_lines))

    # Vaksinasi overdue
    overdue = prop.get("overdue_vaccines") or []
    if overdue:
        parts.append(f"## Vaksin Overdue\n⚠️ {', '.join(overdue)}")

    # Owner
    user_ctx = context.get("user", {})
    if user_ctx.get("name"):
        parts.append(f"## Pemilik\nNama: {user_ctx['name']}")

    if not parts:
        return "Informasi hewan terbatas — data medis belum tersedia."

    return "\n\n".join(parts)


def _generate_with_llm(
    agent_type: str,
    pet_name: str,
    user_text: str,
    context: dict,
    llm: LLMClient,
<<<<<<< HEAD
) -> dict:
    """Generate response menggunakan LLM dengan structured output."""

    agent_info = AGENT_PROMPTS.get(agent_type, AGENT_PROMPTS["pet_companion"])
    rules_text = "\n".join(f"- {r}" for r in agent_info["rules"])

    # Build rich pet context dari data DB
    pet_context_section = _format_pet_context_for_prompt(context)

    # Safety warnings berdasarkan spesies
    species = context.get("proprietary", {}).get("species", "")
    safety_section = ""
    if species:
        from .safety import collect_safety_warnings, check_contraindications_from_context
        warnings = collect_safety_warnings(species)
        context_warnings = check_contraindications_from_context(context.get("proprietary", {}))
        all_warnings = warnings + context_warnings
        if all_warnings:
            safety_section = "\n\nPERINGATAN KESELAMATAN (WAJIB dipatuhi):\n" + "\n".join(
                f"- {w}" for w in all_warnings
            )

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
- GUNAKAN data medis pasien di bawah untuk memberikan saran yang PERSONAL dan KONTEKSTUAL
- Jika pasien punya alergi, JANGAN sarankan apapun yang mengandung alergen tersebut
- Jika ada obat aktif, pertimbangkan potensi interaksi obat
- Jika ada kondisi kronis, sesuaikan saran dengan kondisi tersebut{safety_section}

OUTPUT FORMAT (JSON):
{{
    "text": "Respon utama dalam Bahasa Indonesia yang natural dan kontekstual",
    "suggestions": ["Saran 1", "Saran 2", "Saran 3"],
    "cta_label": "Label tombol (jika perlu tindakan)",
    "cta_endpoint": "Endpoint API (jika perlu)",
    "has_disclaimer": true/false,
    "custom_disclaimer": "Jika ada disclaimer khusus, atau kosongkan"
}}"""

    user_prompt = f"""{pet_context_section}

Nama hewan: {pet_name}
Pertanyaan pengguna: {user_text}"""

    result = llm.chat_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        operation=f"response_{agent_type}",
=======
    max_tokens: int,
) -> dict | None:
    role = _ROLE.get(agent_type, _ROLE["pet_companion"])
    pet_line = compact_pet_context(context)
    system = (
        f"{role} Bahasa Indonesia. JSON saja. "
        f'{{"text":"max 90 kata","suggestions":["..",".."],'
        f'"cta_label":"","cta_endpoint":"","disclaimer":""}} '
        "Tidak diagnosis pasti. Tidak dosis obat resep."
>>>>>>> 82ac43a20f6f5d87cf3ec8e2b8035cfee3d52dc6
    )
    user = f"hewan:{pet_name}|{pet_line}\nuser:{(user_text or '')[:400]}"
    result = llm.chat_json(
        system,
        user,
        max_tokens=max_tokens or token_budget_for("pawnia_chat"),
        operation=f"pawnia_{agent_type}",
    )
    if not isinstance(result, dict) or not result.get("text"):
        return None
    response = {
        "text": str(result.get("text", "")).strip(),
        "suggestions": list(result.get("suggestions") or [])[:3],
        "cta": [],
        "disclaimer": str(result.get("disclaimer") or ""),
        "token_mode": "llm",
    }
    if result.get("cta_label") and result.get("cta_endpoint"):
        response["cta"].append({
            "type": "action",
            "label": result["cta_label"],
            "endpoint": result["cta_endpoint"],
        })
    if not response["disclaimer"] and agent_type not in ("behavior_fun",):
        response["disclaimer"] = (
            "Informasi bersifat pendukung, bukan pengganti dokter hewan."
        )
    return response


def _try_kb_brief(agent_type: str, pet_name: str, user_text: str, context: dict) -> dict | None:
    if agent_type not in ("pet_companion", "vet_escalation", "behavior_insight"):
        return None
    text = (user_text or "").strip()
    if len(text) < 12:
        return None
    from .kb_brief import build_symptom_brief

    pet_ctx = context.get("pet_context") or context.get("proprietary") or {}
    return build_symptom_brief(text, pet_name=pet_name, pet_context=pet_ctx)


def _generate_fallback(
    agent_type: str,
    pet_name: str,
    user_text: str,
    context: dict,
) -> dict:
    text_lower = (user_text or "").lower()

    if agent_type == "behavior_insight":
        if any(k in text_lower for k in ("muntah", "diare")):
            intro = f"Saya prihatin {pet_name} ada keluhan pencernaan."
        elif any(k in text_lower for k in ("agresif", "galak")):
            intro = f"Perubahan agresivitas {pet_name} perlu dicermati."
        elif any(k in text_lower for k in ("takut", "cemas", "stres", "stress")):
            intro = f"{pet_name} tampak cemas — kita cari pemicunya."
        else:
            intro = f"Perubahan perilaku {pet_name} sudah tercatat."
        return {
            "text": f"{intro}\n\nSejak kapan, seberapa sering, dan apa pemicunya?",
            "suggestions": ["Ceritakan lebih detail", "Konsultasi dokter hewan"],
            "cta": [{"type": "teleconsult", "label": "💬 Konsultasi Dokter", "endpoint": "/api/v1/teleconsult"}],
            "disclaimer": "Analisis perilaku bersifat informatif.",
            "token_mode": "template",
        }

    if agent_type == "pet_companion":
        if any(k in text_lower for k in ("halo", "hai", "hi ", "selamat")):
            text = (
                f"Halo! Senang bertemu denganmu dan {pet_name}! 🐾\n\n"
                "Saya bisa bantu: gejala, nutrisi, vaksin, atau arahkan ke dokter."
            )
        elif any(k in text_lower for k in ("terima kasih", "makasih", "thanks")):
            text = f"Sama-sama! Senang bisa membantu {pet_name}. Ada lagi?"
        else:
            text = f"Halo! Ada yang bisa saya bantu untuk {pet_name} hari ini?"
        return {
            "text": text,
            "suggestions": [f"Cek kesehatan {pet_name}", "Rekomendasi makanan", "Konsultasi dokter"],
            "cta": [{"type": "chat", "label": "💬 Mulai Konsultasi", "endpoint": "/api/v1/ai/chat"}],
            "disclaimer": "",
            "token_mode": "template",
        }

    if agent_type == "triage_emergency":
        return {
            "text": (
                f"🚨 Kondisi darurat terdeteksi pada {pet_name}. Tetap tenang.\n"
                "1. Jauhkan dari benda berbahaya\n"
                "2. Jangan masukkan apa pun ke mulut\n"
                "3. Catat waktu gejala\n"
                "4. Segera ke klinik hewan terdekat"
            ),
            "suggestions": ["Cari klinik terdekat", "Hubungi dokter darurat"],
            "cta": [
                {"type": "emergency", "label": "🏥 Cari Klinik", "endpoint": "/api/v1/clinics/nearby"},
                {"type": "teleconsult", "label": "Hubungi Dokter", "endpoint": "/api/v1/teleconsult/emergency"},
            ],
            "disclaimer": "⚠️ Darurat. Segera cari pertolongan medis profesional.",
            "token_mode": "template",
        }

    if agent_type == "nutrition_advisor":
        allergy = ""
        if "alergi" in text_lower or "allergy" in text_lower:
            allergy = " Hindari alergen yang sudah diketahui (mis. ayam) sampai dikonfirmasi dokter."
        return {
            "text": (
                f"Untuk nutrisi {pet_name}: sesuaikan spesies, usia, dan kondisi."
                f"{allergy}\nApa yang biasanya dimakan sekarang?"
            ),
            "suggestions": ["Rekomendasi produk", "Diet khusus", "Konsultasi dokter"],
            "cta": [{"type": "teleconsult", "label": "💬 Konsultasi Dokter", "endpoint": "/api/v1/teleconsult"}],
            "disclaimer": "Rekomendasi nutrisi bersifat informatif.",
            "token_mode": "template",
        }

    if agent_type == "vet_escalation":
        return {
            "text": (
                f"Berdasarkan keluhan {pet_name}, sebaiknya diperiksa dokter hewan "
                "agar penanganan tepat. Saya bisa bantu siapkan ringkasan gejala."
            ),
            "suggestions": ["Booking telekonsultasi", "Cari klinik"],
            "cta": [{"type": "teleconsult", "label": "💬 Konsultasi Dokter", "endpoint": "/api/v1/teleconsult"}],
            "disclaimer": "Bukan diagnosis. Keputusan klinis oleh dokter hewan.",
            "token_mode": "template",
        }

    if agent_type == "meal_planner":
        return {
            "text": (
                f"Untuk jadwal makan {pet_name} saya butuh: berat badan (kg), "
                "jenis pakan, frekuensi makan, dan kondisi medis."
            ),
            "suggestions": ["Isi berat badan", "Lihat produk pakan"],
            "cta": [{"type": "action", "label": "🛒 Beli Makanan", "endpoint": "/api/v1/recommendations"}],
            "disclaimer": "",
            "token_mode": "template",
        }

    if agent_type == "medication_adherence":
        return {
            "text": (
                f"Pengingat pengobatan {pet_name}: vaksin H-7/H-1, obat harian, "
                "dan riwayat. Dosis hanya mengikuti instruksi dokter."
            ),
            "suggestions": ["Cek jadwal vaksin", "Buat pengingat"],
            "cta": [{"type": "reminder", "label": "⏰ Cek Jadwal", "endpoint": "/api/v1/reminders"}],
            "disclaimer": "Ikuti petunjuk dokter hewan.",
            "token_mode": "template",
        }

    if agent_type == "vision_screening":
        return {
            "text": f"Foto {pet_name} bisa dianalisis. Unggah gambar yang jelas (cahaya cukup).",
            "suggestions": ["Unggah foto", "Deskripsikan gejala"],
            "cta": [{"type": "camera", "label": "📸 Buka AI Camera", "endpoint": "/api/v1/vision/analyze/upload"}],
            "disclaimer": "Screening AI bukan diagnosis.",
            "token_mode": "template",
        }

    return {
        "text": f"Ada yang bisa Pawnia bantu untuk {pet_name} hari ini?",
        "suggestions": ["Ceritakan lebih detail", "Konsultasi dokter"],
        "cta": [],
        "disclaimer": "Informasi bersifat informatif.",
        "token_mode": "template",
    }
