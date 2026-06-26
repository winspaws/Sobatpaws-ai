"""Specialized agents for clinical consultation workflow: VisionAnalyzer, OwnerClarifier, VetSummarizer, ClinicalOrchestrator."""
from __future__ import annotations

import base64
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from ..data_loader import KnowledgeBase, load_knowledge_base
from ..vision.analyzer import VisionService, get_vision_service
from ..vision.schemas import VisionFocus
from .llm import LLMClient
from .schemas import IntakeModality

logger = logging.getLogger("ekosistem_satwa.ai.specialized_agents")


# =============================================================================
#  SCHEMA MODELS FOR SPECIALIZED AGENTS
# =============================================================================


class AgentType(str, Enum):
    """Type of specialized agent."""

    VISION_ANALYZER = "vision_analyzer"
    OWNER_CLARIFIER = "owner_clarifier"
    VET_SUMMARIZER = "vet_summarizer"
    ORCHESTRATOR = "orchestrator"


class ClarifierQuestionType(str, Enum):
    """Category of clarification question for the owner."""

    SYMPTOM_DETAILS = "symptom_details"
    TIMELINE = "timeline"
    HISTORY = "history"
    ENVIRONMENT = "environment"
    DIET = "diet"
    VACCINATION = "vaccination"


class ClarifierQuestion(BaseModel):
    """A single clarification question to ask the pet owner."""

    question_id: str
    text: str
    question_type: ClarifierQuestionType
    options: Optional[list[str]] = None
    priority: int = 1  # 1 = highest


class ClarifierResponse(BaseModel):
    """Result from OwnerClarifierAgent determining next steps."""

    should_ask_more: bool
    questions: list[ClarifierQuestion] = []
    summary_so_far: str = ""
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    red_flags: list[str] = []
    suggested_next: Optional[str] = None  # "ask_more" | "send_to_vet" | "emergency_alert"


class LesionSeverity(str, Enum):
    """Severity level of a detected lesion."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class VisionLesion(BaseModel):
    """Structured description of a lesion detected in an image."""

    location: str  # e.g., "left_ear_pinna", "dorsal_trunk", "right_cornea"
    type: str  # e.g., "erythema", "alopecia", "papule", "pustule", "crust", "ulcer", "laceration", "abscess", "discharge"
    severity: LesionSeverity
    description: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    image_region: Optional[dict[str, int]] = None  # x, y, width, height if detectable


class StructuredVisionResult(BaseModel):
    """Structured output from VisionAnalyzerAgent."""

    species_detected: Optional[str] = None  # dog, cat, rabbit, etc.
    breed_hints: list[str] = []
    age_estimate_min_years: Optional[float] = None
    age_estimate_max_years: Optional[float] = None
    age_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    lesions: list[VisionLesion] = []
    red_flags: list[str] = []
    extracted_symptoms: list[str] = []  # symptom name_ids matching KB
    raw_description: str = ""
    structured_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    processing_time_ms: Optional[float] = None
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VetSummarySectionType(str, Enum):
    """Type of section in the vet consultation summary."""

    PATIENT_PROFILE = "patient_profile"
    CHIEF_COMPLAINT = "chief_complaint"
    TIMELINE = "timeline"
    CLINICAL_FINDINGS = "clinical_findings"
    VISION_FINDINGS = "vision_findings"
    DIFFERENTIAL_DIAGNOSIS = "differential_diagnosis"
    RED_FLAGS = "red_flags"
    AI_CONFIDENCE_NOTE = "ai_confidence_note"


class VetSummarySection(BaseModel):
    """A single section in the structured vet summary."""

    section_type: VetSummarySectionType
    title: str
    content: str
    priority: int = Field(default=3, ge=1, le=5)  # 1 = most important (red flag)
    structured_data: Optional[dict[str, Any]] = None
    ai_generated: bool = True
    confidence: Optional[float] = None


class VetConsultationSummary(BaseModel):
    """Complete structured summary for presentation to a veterinarian."""

    consultation_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    patient_profile: dict[str, Any]  # species, breed_estimate, age_estimate, sex, weight_estimate (if any)
    chief_complaint: str
    timeline_summary: str
    clinical_findings: list[VetSummarySection]
    vision_findings: list[VetSummarySection] = []
    differential_diagnosis: list[dict[str, Any]]  # from SuggestionEngine: disease_slug, name_id, confidence, rationale
    red_flags: list[str] = []
    overall_ai_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    owner_chat_summary: Optional[str] = None  # ringkasan percakapan dengan owner
    has_owner_clarification: bool = False
    clarification_questions_asked: int = 0
    disclaimer: str = (
        "Saran AI bersifat pendukung keputusan klinis. "
        "Diagnosa akhir dan terapi adalah tanggung jawab dokter hewan berlisensi."
    )

    model_config = {"protected_namespaces": ()}


# =============================================================================
#  VISION PROMPTS
# =============================================================================


VISION_PROMPT_STRUCTURED = """
Anda adalah dokter hewan ahli dermatologi dan radiologi. Analisa gambar ini secara klinis.

Output JSON VALID SAJA (tanpa markdown, tanpa penjelasan tambahan).

Field yang harus ada:
1. species_detected: string atau null — salah satu dari: dog, cat, rabbit, hamster, guinea_pig, ferret, poultry, fish, reptile, amphibian
2. breed_hints: list string — maksimal 3 kemiripan ras, boleh kosong
3. age_estimate_min_years: number atau null — estimasi umur minimum
4. age_estimate_max_years: number atau null — estimasi umur maksimum
5. age_confidence: number 0.0-1.0 — seberapa yakin dengan estimasi umur
6. lesions: list object — setiap lesi dengan:
   - location: lokasi anatomis (misal: "left_ear_pinna", "dorsal_trunk", "right_cornea", "perineal_region")
   - type: jenis lesi (erythema, alopecia, papule, pustule, crust, scale, ulcer, laceration, abscess, discharge, swelling, mass)
   - severity: "mild" atau "moderate" atau "severe"
   - description: deskripsi detail lesi
   - confidence: 0.0-1.0
7. red_flags: list string — tanda darurat: pale_mucosa, respiratory_distress, active_bleeding, seizures, severe_trauma, unconscious, cyanosis
8. extracted_symptoms: list string — gejala yang teridentifikasi (gunakan istilah yang umum)
9. raw_description: string — deskripsi natural lengkap dalam Bahasa Indonesia

Pastikan JSON valid dan komplit. JANGAN ada teks di luar JSON.
"""


# =============================================================================
#  VISION ANALYZER AGENT
# =============================================================================


class VisionAnalyzerAgent:
    """Specialized agent for clinical analysis of animal images/video frames.

    Analyzes visual media to detect species, breed hints, age estimates,
    lesions, red flags, and clinical symptoms from images.
    """

    def __init__(
        self,
        llm: Optional[LLMClient] = None,
        kb: Optional[KnowledgeBase] = None,
        vision: Optional[VisionService] = None,
    ):
        self.llm = llm or LLMClient()
        self.kb = kb or load_knowledge_base()
        self.vision = vision or get_vision_service()
        logger.info("VisionAnalyzerAgent initialized")

    def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: Optional[str] = None,
        context_species: Optional[str] = None,
    ) -> Optional[StructuredVisionResult]:
        """
        Analyze an image and return structured clinical findings.

        Args:
            image_bytes: Raw image bytes
            mime_type: Image MIME type (image/jpeg, image/png, etc.)
            context_species: Species if already known (improves prompt context)

        Returns:
            StructuredVisionResult or None if analysis fails
        """
        start_time = time.time()
        mime = mime_type or "image/jpeg"

        try:
            result = self.vision.analyze_image(
                image_bytes,
                mime_type=mime,
                category_slug=context_species,
                focus=VisionFocus.general,
            )
            processing_time = (time.time() - start_time) * 1000

            lesions: list[VisionLesion] = []
            for l in result.lesions:
                try:
                    sev = LesionSeverity(l.severity.lower())
                except ValueError:
                    sev = LesionSeverity.MODERATE
                lesions.append(
                    VisionLesion(
                        location=l.location,
                        type=l.type,
                        severity=sev,
                        description=l.description,
                        confidence=l.confidence,
                    )
                )

            structured = StructuredVisionResult(
                species_detected=result.species_detected,
                breed_hints=result.breed_hints,
                age_estimate_min_years=result.age_estimate_min_years,
                age_estimate_max_years=result.age_estimate_max_years,
                age_confidence=result.age_confidence,
                lesions=lesions,
                red_flags=result.red_flags,
                extracted_symptoms=result.extracted_symptoms,
                raw_description=result.raw_description,
                processing_time_ms=processing_time,
                structured_confidence=0.8 if result.analysis_source == "llm_structured" else 0.5,
            )
            logger.info("Vision analysis complete in %.1fms", processing_time)
            return structured

        except Exception as exc:
            logger.warning("Vision analysis failed: %s", exc)
            return None


# =============================================================================
#  OWNER CLARIFIER AGENT
# =============================================================================


OWNER_CLARIFIER_SYSTEM_PROMPT = """
Anda adalah asisten dokter hewan yang berbicara dengan pemilik hewan (pet owner).
Tugas Anda adalah mengumpulkan informasi SELENGKAP MUNGKIN sebelum kasus diteruskan ke dokter.

Gunakan Bahasa Indonesia yang ramah tapi profesional.

INFORMASI YANG PERLU DIKUMPULKAN (jika belum ada):
1. TIMELINE: Kapan gejala mulai? Semakin parah? Ada pencetus (makan baru, jalan-jalan, dll)?
2. DETAIL GEJALA: Frekuensi? Durasi? Apakah ada yang memperbaiki atau memperburuk?
3. RIWAYAT: Vaksin terakhir? Penyakit sebelumnya? Obat yang sedang dikonsumsi? Operasi pernah?
4. LINGKUNGAN: Kontak dengan hewan lain? Perubahan lingkungan (rumah baru, hewan baru)?
5. MAKANAN: Perubahan makanan? Nafsu makan? Muntah atau diare?
6. BERAT BADAN: Apakah ada penurunan atau kenaikan berat badan yang signifikan?

PRIORITASKAN RED FLAG (segera kirim ke dokter jika ada):
- Pendarahan aktif
- Selaput lendir pucat
- Sesak napas / respiratory distress
- Kejang
- Trauma parah
- Tidak sadarkan diri
- Tidak makan/minum > 24 jam
- Muntah/diare parah > 12 jam

Jika informasi sudah CUKUP (confidence > 0.85) atau owner bosan, beritahu:
"Informasi sudah cukup, saya sampaikan ke dokter ya. Mohon tunggu sebentar..."

Selalu tanya 1-2 pertanyaan SEKALI saja, jangan menumpuk.
Jika owner menjawab pertanyaan, analisa jawaban dan tentukan perlu tanya lagi atau tidak.
"""


class OwnerClarifierAgent:
    """Agent for interacting with pet owners and gathering complete clinical information.

    Determines what clarification questions to ask, identifies red flags,
    and decides when sufficient information has been collected.
    """

    def __init__(
        self,
        llm: Optional[LLMClient] = None,
        kb: Optional[KnowledgeBase] = None,
    ):
        self.llm = llm or LLMClient()
        self.kb = kb or load_knowledge_base()
        logger.info("OwnerClarifierAgent initialized")

    def should_ask_more(
        self,
        context: dict,  # ConsultationContext-like
        current_symptoms: list[str],
        messages_exchanged: int,
        has_red_flags: bool = False,
    ) -> ClarifierResponse:
        """
        Determine if additional clarification questions should be asked.

        This is currently a rule-based skeleton. LLM-powered contextual
        question generation will be added in a future iteration.

        Args:
            context: Consultation context with patient details
            current_symptoms: List of identified symptoms so far
            messages_exchanged: Number of messages in the conversation
            has_red_flags: Whether any emergency red flags were detected

        Returns:
            ClarifierResponse with decision and questions if needed
        """
        # Immediate emergency: no more questions, escalate
        if has_red_flags:
            return ClarifierResponse(
                should_ask_more=False,
                red_flags=["RED_FLAG_DETECTED"],
                suggested_next="emergency_alert",
                summary_so_far="Red flag terdeteksi, segera hubungi dokter.",
                confidence_score=1.0,
            )

        # Early in conversation with few symptoms: ask about timeline
        if len(current_symptoms) < 2 and messages_exchanged < 3:
            return ClarifierResponse(
                should_ask_more=True,
                questions=[
                    ClarifierQuestion(
                        question_id="q_timeline",
                        text="Gejala ini sudah berapa lama? Dan apakah semakin parah atau sama saja?",
                        question_type=ClarifierQuestionType.TIMELINE,
                        priority=1,
                    )
                ],
                confidence_score=0.4,
                summary_so_far=f"Baru mengumpulkan {len(current_symptoms)} gejala.",
            )

        # Still early conversation: ask about medical history
        if messages_exchanged < 4 and len(current_symptoms) < 3:
            return ClarifierResponse(
                should_ask_more=True,
                questions=[
                    ClarifierQuestion(
                        question_id="q_history",
                        text="Apakah hewan ini pernah sakit dengan gejala serupa sebelumnya? Dan vaksin terakhir kapan?",
                        question_type=ClarifierQuestionType.HISTORY,
                        priority=2,
                    )
                ],
                confidence_score=0.6,
                summary_so_far="Perlu konfirmasi riwayat medis.",
            )

        # Sufficient information collected
        return ClarifierResponse(
            should_ask_more=False,
            suggested_next="send_to_vet",
            confidence_score=0.85,
            summary_so_far="Informasi klinis sudah cukup untuk diteruskan ke dokter.",
        )

    def generate_owner_response(
        self,
        owner_message: str,
        context: dict,
        clarification_state: ClarifierResponse,
    ) -> str:
        """
        Generate a natural response for the pet owner.

        Formats questions in a friendly, conversational way in Indonesian.

        Args:
            owner_message: The last message from the owner
            context: Consultation context
            clarification_state: Output from should_ask_more()

        Returns:
            Natural language response to send to the owner
        """
        if not clarification_state.should_ask_more:
            if clarification_state.suggested_next == "emergency_alert":
                return (
                    "⚠️ Mohon maaf, kondisi ini memerlukan penanganan segera. "
                    "Saya akan menghubungkan Anda dengan dokter SEKARANG. Mohon tunggu..."
                )
            else:
                return (
                    "✅ Terima kasih informasinya! Saya sudah rangkum untuk dokter. "
                    "Mohon tunggu sebentar ya, dokter akan segera merespons. 🙏"
                )

        # Format questions naturally
        questions_text = "\n".join([
            f"{i+1}. {q.text}"
            for i, q in enumerate(clarification_state.questions)
        ])

        return (
            "Terima kasih! Untuk membantu dokter menganalisa lebih baik, "
            f"boleh saya tanya beberapa hal ya?\n{questions_text}"
        )


# =============================================================================
#  VET SUMMARIZER AGENT
# =============================================================================


VET_SUMMARIZER_SYSTEM_PROMPT = """
Anda adalah asisten dokter hewan yang merangkum informasi dari pet owner untuk ditampilkan ke DOKTER HEWAN.

PRINSIP PENTING:
1. RINGKAS TAPI LENGKAP — dokter tidak punya banyak waktu
2. HIGHLIGHT RED FLAG dengan jelas (gunakan ⚠️)
3. SELALU sertakan tingkat keyakinan AI (confidence)
4. JANGAN pernah mendiagnosa — itu hak dokter
5. Gunakan istilah medis yang tepat tapi jangan berlebihan

STRUKTUR YANG DISUKAI DOKTER:
- Patient Profile: Spesies, estimasi umur, jenis kelamin (jika ada)
- Chief Complaint: 1 kalimat inti keluhan
- Timeline: urutan kejadian yang jelas
- Clinical Findings: gejala yang terstruktur
- Vision Findings (jika ada gambar): apa yang terlihat di gambar dengan lokasi
- Differential Diagnosis: dari AI dengan confidence score
- Red Flags: tanda darurat yang perlu perhatian segera

OUTPUT GUNAKAN BAHASA INDONESIA YANG JELAS.
"""


class VetSummarizerAgent:
    """Agent for synthesizing all consultation data into a vet-optimized summary.

    Combines intake data, vision analysis, AI suggestions, and conversation
    history into a structured, prioritized summary for veterinarian review.
    """

    def __init__(
        self,
        llm: Optional[LLMClient] = None,
        kb: Optional[KnowledgeBase] = None,
    ):
        self.llm = llm or LLMClient()
        self.kb = kb or load_knowledge_base()
        logger.info("VetSummarizerAgent initialized")

    def generate_summary(
        self,
        consultation_id: str,
        context: dict,  # ConsultationContext
        intake_history: list[dict],  # list of IntakeResult-like dicts
        vision_results: list[StructuredVisionResult],
        ai_suggestion: Optional[dict] = None,  # AISuggestion-like dict
        owner_chat_messages: Optional[list[dict]] = None,
    ) -> VetConsultationSummary:
        """
        Generate a structured consultation summary for the veterinarian.

        This is a skeleton implementation that will be enhanced with
        LLM-powered summarization in a future iteration.

        Args:
            consultation_id: Unique consultation identifier
            context: Patient and consultation context
            intake_history: List of intake results from each turn
            vision_results: Results from image analysis
            ai_suggestion: AI disease/therapy suggestions
            owner_chat_messages: Full chat history for summarization

        Returns:
            Structured VetConsultationSummary ready for vet UI
        """
        # Build patient profile from context
        patient_profile = {
            "species": context.get("category_slug"),
            "breed_estimate": context.get("breed_slug"),
            "age_estimate_years": context.get("age_years"),
            "sex": context.get("sex"),
            "weight_estimate_kg": context.get("weight_kg"),
        }

        # Extract symptoms from intake history
        all_symptoms: list[str] = []
        for intake in intake_history:
            symptoms = intake.get("symptoms", [])
            for s in symptoms:
                if isinstance(s, dict):
                    symptom_id = s.get("name_id") or s.get("name", "")
                    if symptom_id:
                        all_symptoms.append(symptom_id)
                else:
                    all_symptoms.append(str(s))

        # Chief complaint from first intake
        chief_complaint = "Keluhan tidak tersedia"
        if intake_history:
            first_intake = intake_history[0]
            chief_complaint = first_intake.get("complaint_text", "Keluhan tidak tersedia")

        # Build clinical findings sections
        sections: list[VetSummarySection] = []

        if all_symptoms:
            symptom_text = ", ".join(all_symptoms[:10])
            if len(all_symptoms) > 10:
                symptom_text += f" dan {len(all_symptoms) - 10} lainnya."
            else:
                symptom_text += "."

            sections.append(VetSummarySection(
                section_type=VetSummarySectionType.CLINICAL_FINDINGS,
                title="Temuan Klinis",
                content="Gejala yang dilaporkan: " + symptom_text,
                priority=2,
                structured_data={"symptoms": all_symptoms},
            ))

        # Build vision findings sections
        vision_sections: list[VetSummarySection] = []
        for vr in vision_results:
            if vr.lesions:
                lesions_desc = "; ".join([
                    f"{l.type} ({l.severity}) di {l.location}"
                    for l in vr.lesions
                ])
                vision_sections.append(VetSummarySection(
                    section_type=VetSummarySectionType.VISION_FINDINGS,
                    title="Temuan di Gambar",
                    content=lesions_desc,
                    priority=2,
                    structured_data={"lesions": [l.model_dump() for l in vr.lesions]},
                ))
            if vr.raw_description:
                vision_sections.append(VetSummarySection(
                    section_type=VetSummarySectionType.VISION_FINDINGS,
                    title="Deskripsi Gambar",
                    content=vr.raw_description,
                    priority=3,
                    confidence=vr.structured_confidence,
                ))

        # Extract differential diagnosis from AI suggestion
        differential: list[dict] = []
        if ai_suggestion:
            diseases = ai_suggestion.get("suggested_diseases", [])
            for d in diseases:
                differential.append({
                    "disease_slug": d.get("disease_slug"),
                    "name_id": d.get("name_id"),
                    "confidence": d.get("confidence", 0.0),
                    "rationale": d.get("rationale"),
                    "is_emergency": d.get("is_emergency", False),
                })

        # Aggregate red flags from all sources
        red_flags: list[str] = []
        if ai_suggestion:
            red_flags.extend(ai_suggestion.get("red_flags", []))
        for vr in vision_results:
            red_flags.extend(vr.red_flags)

        # Calculate overall confidence from component confidences
        conf_components: list[float] = [0.7]  # baseline default
        if differential:
            max_disease_conf = max(
                [d.get("confidence", 0.0) for d in differential],
                default=0.7,
            )
            conf_components.append(max_disease_conf)
        if vision_results:
            avg_vision_conf = sum(
                [v.structured_confidence for v in vision_results]
            ) / len(vision_results)
            conf_components.append(avg_vision_conf)

        overall_confidence = sum(conf_components) / len(conf_components)

        return VetConsultationSummary(
            consultation_id=consultation_id,
            patient_profile=patient_profile,
            chief_complaint=chief_complaint,
            timeline_summary="Timeline akan di-generate dari chat history nanti.",
            clinical_findings=sections,
            vision_findings=vision_sections,
            differential_diagnosis=differential,
            red_flags=list(set(red_flags)),  # deduplicate
            overall_ai_confidence=min(overall_confidence, 0.95),  # safety cap at 0.95
            has_owner_clarification=len(intake_history) > 1,
            clarification_questions_asked=max(0, len(intake_history) - 1),
        )


# =============================================================================
#  CLINICAL ORCHESTRATOR
# =============================================================================


class ClinicalOrchestrator:
    """
    Main coordinator for the multi-agent clinical consultation workflow.

    Orchestrates the pipeline:
    Owner Input → VisionAnalyzer (if images) → OwnerClarifier → VetSummarizer → Vet UI

    This is the single entry point for processing consultation turns from
    pet owners and determining the appropriate response.
    """

    def __init__(
        self,
        llm: Optional[LLMClient] = None,
        kb: Optional[KnowledgeBase] = None,
    ):
        self.llm = llm or LLMClient()
        self.kb = kb or load_knowledge_base()

        # Initialize specialized agents
        self.vision_agent = VisionAnalyzerAgent(self.llm, self.kb)
        self.clarifier_agent = OwnerClarifierAgent(self.llm, self.kb)
        self.summarizer_agent = VetSummarizerAgent(self.llm, self.kb)

        logger.info("ClinicalOrchestrator initialized with all specialized agents")

    def process_owner_turn(
        self,
        consultation_id: str,
        context: dict,  # ConsultationContext-like
        text: Optional[str] = None,
        media: Optional[list[dict]] = None,  # list of MediaPayload-like dicts
        intake_history: Optional[list[dict]] = None,
    ) -> dict:
        """
        Process a single turn of owner input in the consultation.

        Handles:
        1. Image analysis via VisionAnalyzer
        2. Symptom extraction and red flag detection
        3. Clarification question generation via OwnerClarifier
        4. Response generation for the owner

        Args:
            consultation_id: Unique consultation identifier
            context: Patient/consultation context
            text: Text message from owner (if any)
            media: List of media items (images, etc.)
            intake_history: Previous intake results from earlier turns

        Returns:
            Dictionary with response_to_owner, should_ask_more,
            has_red_flags, vision_results, and current_state.
        """
        media = media or []
        intake_history = intake_history or []

        vision_results: list[StructuredVisionResult] = []
        red_flags: list[str] = []

        # Step 1: Process media (images) with VisionAnalyzer
        for item in media:
            modality = item.get("modality")
            if modality in (IntakeModality.image, IntakeModality.video_frame):
                b64_data = item.get("base64_data")
                if b64_data:
                    try:
                        img_bytes = base64.b64decode(b64_data)
                        vr = self.vision_agent.analyze_image(
                            img_bytes,
                            mime_type=item.get("mime_type"),
                            context_species=context.get("category_slug"),
                        )
                        if vr:
                            vision_results.append(vr)
                            red_flags.extend(vr.red_flags)
                    except Exception as exc:
                        logger.warning(f"Failed to process media item: {exc}")

        # Step 2: Extract symptoms (placeholder - will use IntakeProcessor later)
        current_symptoms: list[str] = []
        if text:
            # TODO: Replace with proper IntakeProcessor.symptom extraction
            current_symptoms.append(text[:50])

        has_red_flags = len(red_flags) > 0

        # Step 3: Let OwnerClarifier decide next steps
        clarification = self.clarifier_agent.should_ask_more(
            context=context,
            current_symptoms=current_symptoms,
            messages_exchanged=len(intake_history) + 1,
            has_red_flags=has_red_flags,
        )

        # Step 4: Generate natural response for the owner
        response_to_owner = self.clarifier_agent.generate_owner_response(
            owner_message=text or "[gambar]",
            context=context,
            clarification_state=clarification,
        )

        # Prepare vision results for JSON serialization
        serializable_vision = []
        for vr in vision_results:
            serializable_vision.append({
                "raw_description": vr.raw_description,
                "species_detected": vr.species_detected,
                "lesions": [l.model_dump() for l in vr.lesions],
                "red_flags": vr.red_flags,
                "confidence": vr.structured_confidence,
            })

        return {
            "consultation_id": consultation_id,
            "response_to_owner": response_to_owner,
            "should_ask_more": clarification.should_ask_more,
            "suggested_next": clarification.suggested_next,
            "has_red_flags": has_red_flags,
            "red_flags": list(set(red_flags)),
            "vision_results": serializable_vision,
            "clarification_confidence": clarification.confidence_score,
        }


# =============================================================================
#  EXPORTS
# =============================================================================


__all__ = [
    "VisionAnalyzerAgent",
    "OwnerClarifierAgent",
    "VetSummarizerAgent",
    "ClinicalOrchestrator",
    "StructuredVisionResult",
    "VisionLesion",
    "ClarifierResponse",
    "ClarifierQuestion",
    "VetConsultationSummary",
    "VetSummarySection",
    "AgentType",
    "ClarifierQuestionType",
    "LesionSeverity",
    "VetSummarySectionType",
]
