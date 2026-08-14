"""Pawnia Orchestrator — Intent Detection, Risk Classification & Agent Routing.

Pawnia adalah AI Orchestrator dan pusat kecerdasan utama dari ekosistem Ekosistem Satwa.
Dirancang sebagai asisten kesehatan hewan peliharaan yang aman, proaktif, personal, dan protektif.

Flow:
1. User Input → Intent Detection → Risk Classification → Context Loading → Agent Routing → Response
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger("ekosistem_satwa.ai.pawnia_orchestrator")


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================


class AgentType(str, Enum):
    """9 agent spesialis dalam arsitektur Pawnia."""

    COMPANION = "pet_companion"           # Default — greeting, obrolan umum
    EMERGENCY = "triage_emergency"         # 🚨 Kata kunci emergency, Risk Score >80
    VET_ESCALATION = "vet_escalation"      # 🩺 Confidence <60%, user minta dokter
    VISION = "vision_screening"            # 👁️ User upload foto/gambar
    BEHAVIOR_INSIGHT = "behavior_insight"  # 🧠 Gangguan perilaku/fisik klinis
    BEHAVIOR_FUN = "behavior_fun"          # 🎭 AI Pet Translator, mood hiburan
    NUTRITION = "nutrition_advisor"        # 🥗 Diet, alergi, nutrisi, suplemen
    MEAL_PLANNER = "meal_planner"          # 📋 Jadwal makan, porsi, kalkulasi kalori
    MEDICATION = "medication_adherence"    # 💊 Vaksin, obat, reminder, konfirmasi


class RiskLevel(str, Enum):
    CRITICAL = "critical"   # 81-100
    HIGH = "high"           # 61-80
    MEDIUM = "medium"       # 31-60
    LOW = "low"             # 0-30


class IntentCategory(str, Enum):
    EMERGENCY = "emergency"
    SYMPTOM_DISCUSSION = "symptom_discussion"
    VISION_REQUEST = "vision_request"
    VET_BOOKING = "vet_booking"
    BEHAVIOR_CLINICAL = "behavior_clinical"
    BEHAVIOR_FUN = "behavior_fun"
    NUTRITION_QUERY = "nutrition_query"
    MEAL_PLANNING = "meal_planning"
    MEDICATION_QUERY = "medication_query"
    GENERAL_CHAT = "general_chat"
    PRODUCT_RECOMMENDATION = "product_recommendation"


@dataclass
class IntentResult:
    """Hasil intent detection."""
    intent: IntentCategory
    confidence: float  # 0.0 - 1.0
    sub_intent: str | None = None
    detected_keywords: list[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class RiskAssessment:
    """Hasil risk classification."""
    score: int  # 0-100
    level: RiskLevel
    factors: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)


@dataclass
class AgentRoutingDecision:
    """Keputusan routing ke agent spesialis."""
    primary_agent: AgentType
    secondary_agent: AgentType | None = None
    confidence: float = 0.0
    risk_assessment: RiskAssessment | None = None
    intent: IntentResult | None = None
    context: dict[str, Any] = field(default_factory=dict)
    should_escalate: bool = False
    escalation_reason: str | None = None


@dataclass
class PawniaResponse:
    """Output terstruktur dari Pawnia Orchestrator."""
    agent: AgentType
    confidence: float
    risk_score: int
    risk_level: str
    response: dict[str, Any]
    context_used: dict[str, Any]
    escalated: bool = False
    conversation_id: str = ""


# =============================================================================
# EMERGENCY KEYWORDS
# =============================================================================

EMERGENCY_KEYWORDS = [
    "darah", "pendarahan", "berdarah", "kejang", "kejang-kejang",
    "pingsan", "tidak sadar", "tidak sadarkan diri", "sulit bernapas",
    "sesak napas", "megap-megap", "kecelakaan", "tertabrak", "jatuh",
    "keracunan", "racun", "luka terbuka", "luka parah", "tulang patah",
    "fraktur", "muntah darah", "diare berdarah", "bab darah",
    "biru", "sianosis", "lemas total", "collapse", "seizure",
    "bleeding", "unconscious", "poison", "fracture", "trauma",
    "gums pale", "pale gums", "distress", "choking", "tersedak",
]

VITAL_SYSTEM_KEYWORDS = [
    "napas", "pernapasan", "jantung", "denyut", "nadi", "sianosis",
    "biru", "mukosa", "respiratory", "cardiac", "pulse",
]

HIGH_RISK_FACTORS = [
    "anak", "anakan", "puppy", "kitten", "geriatrik", "tua", "senior",
    "hamil", "bunting", "menyusui", "post-op", "pasca operasi",
]

SEVERITY_KEYWORDS = [
    "parah", "berat", "akut", "kronis", "semakin parah", "memburuk",
    "tidak membaik", "3 hari", "seminggu", "berhari-hari",
]

# =============================================================================
# INTENT KEYWORDS
# =============================================================================

INTENT_PATTERNS: dict[IntentCategory, list[str]] = {
    IntentCategory.SYMPTOM_DISCUSSION: [
        "muntah", "diare", "batuk", "pilek", "demam", "gatal", "luka",
        "lemah", "nafsu makan", "tidak mau makan", "gejala", "sakit",
        "vomiting", "diarrhea", "cough", "fever", "itch", "wound",
    ],
    IntentCategory.EMERGENCY: EMERGENCY_KEYWORDS,
    IntentCategory.VISION_REQUEST: [
        "foto", "gambar", "upload", "kamera", "fotokan", "potoin",
        "photo", "picture", "image", "camera", "lihat",
    ],
    IntentCategory.VET_BOOKING: [
        "dokter", "konsultasi", "booking", "klinik", "vet", "periksa",
        "doctor", "clinic", "appointment", "janji", "berobat",
    ],
    IntentCategory.BEHAVIOR_CLINICAL: [
        "agresif", "galak", "takut", "cemas", "stress", "stres",
        "pincang", "lemas", "lesu", "gelisah", "merusak", "ngegong",
        "aggressive", "anxious", "limping", "restless", "destructive",
        "pikun", "bingung", "linglung", "lupa", "tersesat", "tua",
        "kompulsif", "obsesif", "berputar", "ngejar ekor", "jilat",
        "phobia", "fobia", "petir", "kembang api", "takut suara",
        "separasi", "ditinggal", "sendirian", "merusak",
        "pica", "makan batu", "makan plastik", "makan tanah",
        "kencing", "buang air", "spraying", "nyemprot",
        "vokalisasi", "gonggong", "meong", "melolong",
        "stereotip", "berputar kandang", "cabut bulu",
        "play agresi", "gigit main", "bite inhibition",
    ],
    IntentCategory.BEHAVIOR_FUN: [
        "mood", "suasana hati", "translater", "translator", "terjemah",
        "suara", "ngomong", "bicara", "arti", "lagu", "nyanyi",
        "mood", "translate", "sound", "speak", "singing",
    ],
    IntentCategory.NUTRITION_QUERY: [
        "makanan", "diet", "nutrisi", "berat badan", "gemuk", "kurus",
        "alergi", "suplemen", "vitamin", "pakan", "food", "nutrition",
        "diet", "allergy", "supplement", "obesitas", "obese",
    ],
    IntentCategory.MEAL_PLANNING: [
        "jadwal makan", "porsi", "kalori", "jadwal diet", "meal plan",
        "berapa kali makan", "takaran", "porsi makan", "feeding schedule",
    ],
    IntentCategory.MEDICATION_QUERY: [
        "obat", "vaksin", "vaksinasi", "reminder", "pengingat",
        "jadwal obat", "kapan vaksin", "obat cacing", "kutu",
        "medicine", "vaccine", "vaccination", "medication",
    ],
    IntentCategory.PRODUCT_RECOMMENDATION: [
        "rekomendasi", "beli", "produk", "recommend", "recommendation",
        "grooming", "toko", "shop", "marketplace", "brand",
    ],
}


# =============================================================================
# PAWNIA ORCHESTRATOR
# =============================================================================


class PawniaOrchestrator:
    """Pawnia — AI Orchestrator untuk ekosistem Ekosistem Satwa.

    Bertanggung jawab atas:
    - Intent Detection: memahami maksud user dari input teks/gambar
    - Risk Classification: menilai tingkat kegawatan
    - Context Loading: memuat proprietary context + memory + RAG
    - Agent Routing: mengirim ke agent spesialis yang tepat
    - Safety Validation: memastikan output aman
    """

    def __init__(
        self,
        memory_service=None,
        knowledge_service=None,
        emr_service=None,
        llm_client=None,
    ):
        self.memory = memory_service
        self.knowledge = knowledge_service
        self.emr = emr_service
        if llm_client is None:
            from .llm import LLMClient
            llm_client = LLMClient()
        self.llm = llm_client
        logger.info("🧠 Pawnia Orchestrator initialized")

    # -------------------------------------------------------------------------
    # INTENT DETECTION
    # -------------------------------------------------------------------------

    def detect_intent(self, text: str, has_image: bool = False) -> IntentResult:
        """Detect user intent from text input.

        Uses keyword-based detection with confidence scoring.
        Falls back to LLM-based detection for ambiguous inputs.
        """
        text_lower = text.lower().strip()
        detected_keywords: list[str] = []
        best_intent = IntentCategory.GENERAL_CHAT
        best_score = 0.0

        # Check for image first — overrides text intent
        if has_image:
            return IntentResult(
                intent=IntentCategory.VISION_REQUEST,
                confidence=0.9,
                detected_keywords=["image_uploaded"],
                raw_text=text,
            )

        # Score each intent category
        for intent, keywords in INTENT_PATTERNS.items():
            score = 0.0
            matched: list[str] = []
            for kw in keywords:
                if kw.lower() in text_lower:
                    score += 0.15
                    matched.append(kw)

            # Emergency gets priority boost
            if intent == IntentCategory.EMERGENCY and matched:
                score *= 1.5

            if score > best_score:
                best_score = score
                best_intent = intent
                detected_keywords = matched

        # Clamp confidence
        confidence = min(best_score, 1.0)

        # LLM intent hanya jika keyword sangat ambigu (hemat token)
        if confidence < 0.3 and self.llm and getattr(self.llm, "available", False):
            from .token_policy import should_detect_intent_llm

            intent_decision = should_detect_intent_llm(text, confidence)
            if intent_decision.use_llm:
                llm_intent = self._detect_intent_llm(text_lower)
                if llm_intent:
                    return llm_intent

        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            detected_keywords=detected_keywords,
            raw_text=text,
        )

    def _detect_intent_llm(self, text: str) -> IntentResult | None:
        """Fallback LLM-based intent detection for ambiguous inputs."""
        try:
            prompt = f"""Classify the intent of this pet owner message into ONE category:
- emergency: life-threatening symptoms (bleeding, seizures, unconscious)
- symptom_discussion: describing symptoms, asking about health
- vision_request: asking to upload/analyze photos
- vet_booking: asking for doctor consultation or clinic booking
- behavior_clinical: behavioral issues (aggression, anxiety, limping)
- behavior_fun: fun pet translator, mood check
- nutrition_query: food, diet, allergies, supplements
- meal_planning: meal schedule, portions, calories
- medication_query: vaccines, medications, reminders
- general_chat: greetings, general pet care questions
- product_recommendation: asking for product recommendations

Message: "{text}"

Respond with ONLY the category name, nothing else."""
            response = self.llm.generate(prompt, max_tokens=20, temperature=0.1)
            intent_str = response.strip().lower()
            for intent in IntentCategory:
                if intent.value == intent_str:
                    return IntentResult(
                        intent=intent,
                        confidence=0.6,
                        raw_text=text,
                    )
        except Exception as exc:
            logger.debug("LLM intent detection failed: %s", exc)
        return None

    # -------------------------------------------------------------------------
    # RISK CLASSIFICATION
    # -------------------------------------------------------------------------

    def classify_risk(
        self,
        text: str,
        intent: IntentResult,
        pet_context: dict[str, Any] | None = None,
    ) -> RiskAssessment:
        """Classify risk level based on text content and context.

        Scoring:
        - Emergency keywords: +40
        - Vital system keywords: +30
        - High-risk factors (age, pregnancy): +20
        - Prolonged symptoms: +15
        - Multiple systemic symptoms: +20
        - Fever: +15
        - Not eating/drinking >24h: +20
        """
        text_lower = text.lower()
        score = 0
        factors: list[str] = []
        red_flags: list[str] = []

        # Emergency keywords — more aggressive scoring
        emergency_matches = [
            kw for kw in EMERGENCY_KEYWORDS if kw.lower() in text_lower
        ]
        if emergency_matches:
            # Each emergency keyword adds significant score
            score += 40 + (len(emergency_matches) * 15)
            factors.append(f"Emergency keywords: {', '.join(emergency_matches[:3])}")
            red_flags.extend(emergency_matches[:3])
            # Single strong emergency keyword is enough for critical
            if len(emergency_matches) >= 1:
                score = max(score, 85)

        # Vital system keywords
        vital_matches = [
            kw for kw in VITAL_SYSTEM_KEYWORDS if kw.lower() in text_lower
        ]
        if vital_matches:
            score += 30
            factors.append("Vital system involvement detected")

        # High-risk factors
        risk_matches = [
            kw for kw in HIGH_RISK_FACTORS if kw.lower() in text_lower
        ]
        if risk_matches:
            score += 20
            factors.append(f"High-risk factor: {risk_matches[0]}")

        # Severity/prolonged symptoms
        severity_matches = [
            kw for kw in SEVERITY_KEYWORDS if kw.lower() in text_lower
        ]
        if severity_matches:
            score += 15
            factors.append("Prolonged or worsening symptoms")

        # Pet context factors (dari DB atau client)
        if pet_context:
            age = pet_context.get("age_years")
            if age is not None and (age < 0.5 or age > 12):
                score += 20
                factors.append(f"Extreme age ({age} years)")
            if pet_context.get("chronic_conditions"):
                conditions = pet_context["chronic_conditions"]
                score += 10
                if isinstance(conditions, list):
                    factors.append(f"Chronic conditions: {', '.join(conditions[:3])}")
                else:
                    factors.append("Has chronic conditions")
            if pet_context.get("has_allergies"):
                score += 5
                factors.append("Has known allergies — check drug safety")
            if pet_context.get("has_active_medications"):
                score += 5
                factors.append("Currently on medication — check interactions")
            if pet_context.get("overdue_vaccines"):
                score += 5
                factors.append(f"Overdue vaccines: {', '.join(pet_context['overdue_vaccines'][:3])}")

        # Determine level
        if score >= 81:
            level = RiskLevel.CRITICAL
        elif score >= 61:
            level = RiskLevel.HIGH
        elif score >= 31:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        return RiskAssessment(
            score=min(score, 100),
            level=level,
            factors=factors,
            red_flags=red_flags,
        )

    # -------------------------------------------------------------------------
    # AGENT ROUTING
    # -------------------------------------------------------------------------

    def route_to_agent(
        self,
        intent: IntentResult,
        risk: RiskAssessment,
        has_image: bool = False,
        confidence_override: float | None = None,
    ) -> AgentRoutingDecision:
        """Route to the appropriate specialist agent based on intent and risk.

        Priority rules:
        1. Emergency > All — Risk Score >80 → Emergency Agent
        2. Image + Emergency → Vision first, then Emergency
        3. Confidence <60% → Vet Escalation
        4. Multi-intent → Most critical first
        """
        # Rule 1: Emergency override
        if risk.level == RiskLevel.CRITICAL or intent.intent == IntentCategory.EMERGENCY:
            return AgentRoutingDecision(
                primary_agent=AgentType.EMERGENCY,
                confidence=0.95,
                risk_assessment=risk,
                intent=intent,
                should_escalate=True,
                escalation_reason="Critical risk detected — immediate escalation",
            )

        # Rule 2: Image → Vision Agent
        if has_image or intent.intent == IntentCategory.VISION_REQUEST:
            return AgentRoutingDecision(
                primary_agent=AgentType.VISION,
                confidence=0.85,
                risk_assessment=risk,
                intent=intent,
            )

        # Rule 3: Confidence <60% → Vet Escalation
        actual_confidence = confidence_override or intent.confidence
        if actual_confidence < 0.6 and risk.level in (RiskLevel.HIGH, RiskLevel.MEDIUM):
            return AgentRoutingDecision(
                primary_agent=AgentType.VET_ESCALATION,
                confidence=actual_confidence,
                risk_assessment=risk,
                intent=intent,
                should_escalate=True,
                escalation_reason=f"Low confidence ({actual_confidence:.0%}) with non-trivial risk",
            )

        # Normal routing by intent
        routing_map: dict[IntentCategory, AgentType] = {
            IntentCategory.VET_BOOKING: AgentType.VET_ESCALATION,
            IntentCategory.BEHAVIOR_CLINICAL: AgentType.BEHAVIOR_INSIGHT,
            IntentCategory.BEHAVIOR_FUN: AgentType.BEHAVIOR_FUN,
            IntentCategory.NUTRITION_QUERY: AgentType.NUTRITION,
            IntentCategory.MEAL_PLANNING: AgentType.MEAL_PLANNER,
            IntentCategory.MEDICATION_QUERY: AgentType.MEDICATION,
            IntentCategory.PRODUCT_RECOMMENDATION: AgentType.COMPANION,
            IntentCategory.SYMPTOM_DISCUSSION: AgentType.COMPANION,
            IntentCategory.GENERAL_CHAT: AgentType.COMPANION,
            IntentCategory.EMERGENCY: AgentType.EMERGENCY,
            IntentCategory.VISION_REQUEST: AgentType.VISION,
        }

        primary = routing_map.get(intent.intent, AgentType.COMPANION)

        # Secondary agent for cross-sell opportunities
        secondary = None
        if primary == AgentType.NUTRITION:
            secondary = AgentType.MEAL_PLANNER
        elif primary == AgentType.COMPANION and risk.level == RiskLevel.MEDIUM:
            secondary = AgentType.VET_ESCALATION

        return AgentRoutingDecision(
            primary_agent=primary,
            secondary_agent=secondary,
            confidence=intent.confidence,
            risk_assessment=risk,
            intent=intent,
        )

    # -------------------------------------------------------------------------
    # CONTEXT LOADING
    # -------------------------------------------------------------------------

    def load_context(
        self,
        user_id: int | None = None,
        pet_id: int | None = None,
        session_id: str | None = None,
        pet_context_override: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Load consolidated context for AI Gateway Context Loader.

        Combines:
        1. Proprietary Context (pet profile, EMR dari database)
        2. Client-provided pet_context (merge/override)
        3. User Context (data pemilik hewan)
        4. Memory Context (short-term + long-term)
        5. Knowledge Base (RAG) — loaded on demand
        """
        context: dict[str, Any] = {
            "proprietary": {},
            "user": {},
            "memory": {},
            "knowledge": [],
            "loaded_at": datetime.now(timezone.utc).isoformat(),
        }

        # Load memory context
        if self.memory and session_id:
            try:
                memory_context = self.memory.load_context(
                    user_id=user_id,
                    pet_id=pet_id,
                    session_id=session_id,
                )
                if memory_context:
                    context["memory"] = memory_context
            except Exception as exc:
                logger.debug("Memory load failed: %s", exc)

        # Load EMR/proprietary context dari database
        if self.emr and pet_id:
            try:
                pet_data = self.emr.get_pet_context(pet_id)
                if pet_data:
                    context["proprietary"] = pet_data
            except Exception as exc:
                logger.warning("EMR pet context load failed for pet %s: %s", pet_id, exc)

        # Merge client-provided pet_context (override DB data jika ada)
        if pet_context_override:
            if context["proprietary"]:
                context["proprietary"].update(pet_context_override)
            else:
                context["proprietary"] = pet_context_override

        # Load user context
        if self.emr and user_id:
            try:
                user_data = self.emr.get_user_context(user_id)
                if user_data:
                    context["user"] = user_data
            except Exception as exc:
                logger.debug("User context load failed for user %s: %s", user_id, exc)

        return context

    # -------------------------------------------------------------------------
    # MAIN PROCESSING PIPELINE
    # -------------------------------------------------------------------------

    def process(
        self,
        text: str,
        has_image: bool = False,
        user_id: int | None = None,
        pet_id: int | None = None,
        session_id: str | None = None,
        pet_context: dict[str, Any] | None = None,
    ) -> PawniaResponse:
        """Main processing pipeline for Pawnia.

        Flow:
        1. Intent Detection
        2. Risk Classification
        3. Context Loading
        4. Agent Routing
        5. Response Generation
        6. Safety Validation
        """
        start_time = time.time()
        conv_id = session_id or f"pawnia_{uuid.uuid4().hex[:12]}"

        # Step 1: Intent Detection
        intent = self.detect_intent(text, has_image=has_image)
        logger.info("Intent: %s (%.0f%%)", intent.intent.value, intent.confidence * 100)

        # Step 2+3: Context Loading (sebelum risk, agar risk bisa pakai data DB)
        context = self.load_context(
            user_id=user_id,
            pet_id=pet_id,
            session_id=conv_id,
            pet_context_override=pet_context,
        )
        if pet_context:
            context["pet_context"] = pet_context
            if not context.get("proprietary"):
                context["proprietary"] = {
                    k: v for k, v in pet_context.items() if v is not None
                }

        # Step 2b: Risk Classification — pakai context yang sudah terisi dari DB
        merged_pet_context = context.get("proprietary") or pet_context
        risk = self.classify_risk(text, intent, pet_context=merged_pet_context)
        logger.info("Risk: %s (%d)", risk.level.value, risk.score)

        # Step 4: Agent Routing
        routing = self.route_to_agent(
            intent=intent,
            risk=risk,
            has_image=has_image,
        )
        logger.info("Routing → %s", routing.primary_agent.value)

        # Step 5: Generate response based on agent
        response = self._generate_response(
            routing=routing,
            text=text,
            context=context,
        )

        # Step 6: Save conversation to memory
        if self.memory and conv_id:
            try:
                self.memory.save_conversation(
                    session_id=conv_id,
                    message={
                        "role": "user",
                        "content": text,
                        "intent": intent.intent.value,
                        "risk_score": risk.score,
                    },
                    user_id=user_id,
                    pet_id=pet_id,
                )
                self.memory.set_short_term(
                    session_id=conv_id,
                    key="last_intent",
                    value={"intent": intent.intent.value, "agent": routing.primary_agent.value},
                    user_id=user_id,
                    pet_id=pet_id,
                )
            except Exception as exc:
                logger.debug("Memory save failed: %s", exc)

        processing_time = (time.time() - start_time) * 1000
        logger.info("Pawnia processed in %.0fms", processing_time)

        # Step 6b: Collect safety warnings dari data nyata
        from .safety import check_contraindications_from_context
        safety_warnings = check_contraindications_from_context(
            context.get("proprietary", {}),
        )
        if safety_warnings:
            response.setdefault("safety_warnings", safety_warnings)
            logger.warning(
                "Safety warnings for pet %s: %s",
                pet_id, "; ".join(safety_warnings[:3]),
            )

        return PawniaResponse(
            agent=routing.primary_agent,
            confidence=routing.confidence,
            risk_score=risk.score,
            risk_level=risk.level.value,
            response=response,
            context_used={
                "intent_detection": True,
                "risk_classification": True,
                "memory": bool(context["memory"]),
                "proprietary": bool(context["proprietary"]),
<<<<<<< HEAD
                "user": bool(context.get("user")),
=======
                "token_mode": response.get("token_mode", "template"),
                "token_reason": response.get("token_reason", ""),
>>>>>>> 82ac43a20f6f5d87cf3ec8e2b8035cfee3d52dc6
            },
            escalated=routing.should_escalate,
            conversation_id=conv_id,
        )

    # -------------------------------------------------------------------------
    # RESPONSE GENERATION
    # -------------------------------------------------------------------------

    def _generate_response(
        self,
        routing: AgentRoutingDecision,
        text: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate response based on the routed agent.

        Each agent has its own response template following:
        1. Empathy Greeting
        2. Core Insight
        3. Actionable CTA
        """
        agent = routing.primary_agent
        risk = routing.risk_assessment

        # Get pet name from context (EMR proprietary or pet_context from chat)
        pet_name = "Si Kecil"
        if context.get("proprietary"):
            pet_name = context["proprietary"].get("name", pet_name)
        elif context.get("pet_context"):
            pet_name = context["pet_context"].get("name", pet_name)

        conf = float(routing.confidence or 0.0)
        context["risk_score"] = int(getattr(risk, "score", 0) or 0) if risk else 0

        if agent == AgentType.EMERGENCY:
            return self._response_emergency(pet_name, risk, text, context)

        elif agent == AgentType.VET_ESCALATION:
            return self._response_vet_escalation(pet_name, risk, routing.confidence, context)

        elif agent == AgentType.VISION:
            return self._response_vision(pet_name)

        elif agent == AgentType.BEHAVIOR_INSIGHT:
<<<<<<< HEAD
            return self._response_behavior_insight(pet_name, text, context)
=======
            return self._response_behavior_insight(pet_name, text, context, conf)
>>>>>>> 82ac43a20f6f5d87cf3ec8e2b8035cfee3d52dc6

        elif agent == AgentType.BEHAVIOR_FUN:
            return self._response_behavior_fun(pet_name)

        elif agent == AgentType.NUTRITION:
            return self._response_nutrition(pet_name, text, context, conf)

        elif agent == AgentType.MEAL_PLANNER:
            return self._response_meal_planner(pet_name, context)

        elif agent == AgentType.MEDICATION:
            return self._response_medication(pet_name, context)

        else:  # COMPANION (default)
            return self._response_companion(pet_name, text, context, conf)


    def _get_llm(self):
        """Lazy init LLM client."""
        if self.llm is None:
            from .llm import LLMClient
            self.llm = LLMClient()
        return self.llm

    def _dynamic_response(self, agent_type: str, pet_name: str,
                          user_text: str = "", context: Optional[dict] = None,
                          risk: Optional["RiskAssessment"] = None,
                          intent_confidence: float = 0.0) -> dict:
        """Template-first; LLM hanya jika token_policy mengizinkan."""
        context = context or {}
        llm = self._get_llm()
        risk_score = int(getattr(risk, "score", 0) or 0) if risk else int(
            (context.get("risk_score") or 0)
        )

        from .response_generator import generate_response
        response = generate_response(
            agent_type=agent_type,
            pet_name=pet_name,
            user_text=user_text or "",
            context=context,
            llm_client=llm if getattr(llm, "available", False) else None,
            intent_confidence=intent_confidence,
            risk_score=risk_score,
        )
        response.setdefault("text", "")
        response.setdefault("suggestions", [])
        response.setdefault("cta", [])
        response.setdefault("disclaimer", "")
        return response

    def _response_emergency(
        self, pet_name: str, risk: "RiskAssessment", text: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """🚨 Emergency — dynamic + structured first aid."""
<<<<<<< HEAD
        resp = self._dynamic_response("triage_emergency", pet_name, text, context)
=======
        resp = self._dynamic_response(
            "triage_emergency", pet_name, text, risk=risk, intent_confidence=0.95,
        )
>>>>>>> 82ac43a20f6f5d87cf3ec8e2b8035cfee3d52dc6
        
        if not resp["text"]:
            tips = [
                "1. Jaga agar tetap tenang dan hangat",
                "2. Jangan berikan makanan atau minuman",
                "3. Catat durasi dan gejala untuk dilaporkan",
                "4. Segera bawa ke klinik hewan terdekat",
            ]
            resp["text"] = f"🚨 {pet_name} memerlukan penanganan medis segera.\n\nTetap tenang. Langkah pertolongan pertama:\n" + "\n".join(tips)
            resp["suggestions"] = tips
        
        resp["cta"] = [
            {"type": "emergency", "label": "Cari Klinik Terdekat", "endpoint": "/api/v1/clinics/nearby"},
            {"type": "teleconsult", "label": "Hubungi Dokter Darurat", "endpoint": "/api/v1/teleconsult/emergency"},
        ]
        resp["red_flags"] = risk.red_flags if risk else []
        resp["disclaimer"] = "⚠️ INI KONDISI DARURAT. Segera cari pertolongan dokter hewan profesional."
        return resp

    def _response_vet_escalation(
        self, pet_name: str, risk: "RiskAssessment", confidence: float,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """🩺 Vet escalation — suggest consultation with context."""
<<<<<<< HEAD
        resp = self._dynamic_response("vet_escalation", pet_name, "", context)
=======
        resp = self._dynamic_response(
            "vet_escalation", pet_name, "", intent_confidence=confidence, risk=risk,
        )
>>>>>>> 82ac43a20f6f5d87cf3ec8e2b8035cfee3d52dc6
        
        if not resp["text"]:
            reason = "gejala yang Anda sampaikan memerlukan pemeriksaan langsung oleh dokter" if risk.level in ("high","medium") else "informasi yang tersedia belum cukup untuk analisis yang akurat"
            resp["text"] = f"Demi keamanan {pet_name}, saya sarankan konsultasi dengan dokter hewan karena {reason}."
        
        resp.setdefault("cta", []).extend([
            {"type": "teleconsult", "label": "💬 Konsultasi Dokter", "endpoint": "/api/v1/teleconsult"},
            {"type": "booking", "label": "🏥 Booking Klinik", "endpoint": "/api/v1/clinics/book"},
        ])
        resp["disclaimer"] = "Saran AI bersifat pendukung keputusan klinis. Diagnosa akhir oleh dokter hewan berlisensi."
        return resp

    def _response_vision(self, pet_name: str) -> dict[str, Any]:
        """👁️ Vision — request image upload."""
        return {
            "text": f"Baik, saya siap menganalisis kondisi {pet_name} melalui gambar! 📸\n\nUntuk hasil terbaik:\n1. Pencahayaan cukup\n2. Fokus area yang dikeluhkan\n3. Ambil dari beberapa sudut\n\nSilakan upload gambar.",
            "suggestions": ["Buka AI Camera", "Upload dari galeri"],
            "cta": [{"type": "camera", "label": "📸 Buka AI Camera", "endpoint": "/api/v1/vision/analyze/upload"}],
            "disclaimer": "Analisis AI bersifat screening awal, bukan diagnosis medis.",
        }

    def _response_behavior_insight(
<<<<<<< HEAD
        self, pet_name: str, text: str,
        context: dict[str, Any] | None = None,
=======
        self, pet_name: str, text: str, context: dict[str, Any] | None = None, confidence: float = 0.0,
>>>>>>> 82ac43a20f6f5d87cf3ec8e2b8035cfee3d52dc6
    ) -> dict[str, Any]:
        """🧠 Behavior insight — dynamic analysis + behavioral_medicine reference."""
        # Gunakan behavioral_medicine untuk analisis berbasis pengetahuan
        from .behavioral_medicine import analyze_behavior

        species = (context or {}).get("proprietary", {}).get("species", "dog")
        common = ["merusak","gonggong","takut","gelisah","agresif","pincang","jilat","berputar","kencing","vokalisasi","makan","stress","cemas"]
        mentioned = [s for s in common if s in text.lower()]
        analysis = analyze_behavior(species, mentioned, text)
        primary = analysis.get("primary_condition")
<<<<<<< HEAD

        # Merge analisis ke context yang sudah ada
        ctx = dict(context) if context else {}
        ctx.setdefault("proprietary", {})["behavior_analysis"] = analysis
        resp = self._dynamic_response("behavior_insight", pet_name, text, ctx)
=======
        
        ctx = dict(context or {})
        ctx.setdefault("proprietary", {})
        if isinstance(ctx["proprietary"], dict):
            ctx["proprietary"]["behavior_analysis"] = analysis
        else:
            ctx["proprietary"] = {"behavior_analysis": analysis}
        resp = self._dynamic_response(
            "behavior_insight", pet_name, text, ctx, intent_confidence=confidence,
        )
>>>>>>> 82ac43a20f6f5d87cf3ec8e2b8035cfee3d52dc6
        
        if primary and not resp["text"]:
            name = primary["name"]
            treatments_text = "\n".join([f"{i+1}. {t['label']}" for i, t in enumerate(primary.get("treatment",[])[:3])])
            resp["text"] = f"🧠 Analisis: {pet_name} mungkin mengalami **{name}**.\n\n{primary['description']}\n\nRekomendasi:\n{treatments_text}"
        
        resp.setdefault("cta", []).extend([
            {"type": "teleconsult", "label": "💬 Konsultasi Dokter", "endpoint": "/api/v1/teleconsult"},
        ])
        resp.setdefault("disclaimer", "Analisis perilaku bersifat informatif. Diagnosis oleh dokter hewan.")
        resp["behavioral_analysis"] = analysis
        return resp

    def _response_behavior_fun(self, pet_name: str) -> dict[str, Any]:
        """🎭 Behavior fun — entertainment."""
        return {
            "text": f"Haha, {pet_name} pasti lucu sekali! 🐾\n\nFitur Pet Translator akan segera hadir! Nanti kamu bisa:\n• Merekam suara hewan\n• Upload video ekspresi\n• Tahu mood mereka\n\nPantau terus ya! 🎉",
            "suggestions": ["Coba fitur lainnya", "Kembali ke menu utama"],
            "cta": [], "disclaimer": "",
        }

    def _response_nutrition(
        self, pet_name: str, text: str, context: dict[str, Any], confidence: float = 0.0,
    ) -> dict[str, Any]:
        """🥗 Nutrition — dynamic advice."""
        resp = self._dynamic_response(
            "nutrition_advisor", pet_name, text, context, intent_confidence=confidence,
        )
        if not resp["text"]:
            resp["text"] = f"Tentu! Bantu cari nutrisi terbaik untuk {pet_name}. 🥗\n\nBeberapa hal yang perlu diperhatikan:\n• Pilih makanan sesuai spesies, usia, dan kondisi\n• Perhatikan protein, lemak, dan serat\n• Hindari alergen jika ada riwayat alergi"
        resp.setdefault("cta", []).extend([
            {"type": "teleconsult", "label": "💬 Konsultasi Dokter", "endpoint": "/api/v1/teleconsult"},
        ])
        resp.setdefault("disclaimer", "Rekomendasi nutrisi bersifat informatif. Konsultasi dengan dokter hewan untuk diet spesifik.")
        return resp

    def _response_meal_planner(
        self, pet_name: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """📋 Meal planner — interactive."""
        return {
            "text": f"Saya bantu buatkan jadwal makan untuk {pet_name}! 📋\n\nUntuk kalkulasi akurat, perlu info:\n1. Berat badan (kg)\n2. Jenis makanan (kering/basah/campuran)\n3. Frekuensi makan saat ini\n4. Kondisi medis tertentu?",
            "suggestions": ["Isi profil berat badan", "Lihat rekomendasi produk"],
            "cta": [{"type": "action", "label": "🛒 Beli Makanan", "endpoint": "/api/v1/recommendations"}],
            "disclaimer": "",
        }

    def _response_medication(
        self, pet_name: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """💊 Medication — reminders with real data."""
        prop = context.get("proprietary", {})
        meds = prop.get("active_medications") or []
        overdue = prop.get("overdue_vaccines") or []
        vaccinations = prop.get("vaccinations") or []

        parts: list[str] = [f"Saya bantu cek jadwal pengobatan {pet_name}! 💊"]

        # Tampilkan obat aktif jika ada
        if meds:
            parts.append("\n**Obat Aktif Saat Ini:**")
            for m in meds[:5]:
                line = f"• {m.get('name', '?')} — {m.get('dosage', '?')}, {m.get('frequency', '?')}"
                if m.get("instructions"):
                    line += f" ({m['instructions']})"
                parts.append(line)

        # Peringatan vaksin overdue
        if overdue:
            parts.append(f"\n⚠️ **Vaksin Overdue:** {', '.join(overdue)}")
            parts.append("Segera jadwalkan vaksinasi ulang!")

        # Safety warnings
        from .safety import check_contraindications_from_context
        warnings = check_contraindications_from_context(prop)
        if warnings:
            parts.append("\n🚨 **Peringatan Keselamatan:**")
            for w in warnings[:3]:
                parts.append(f"• {w}")

        if not meds and not overdue:
            parts.append("\nSmart Reminder membantu:\n• Pengingat vaksinasi (H-7 dan H-1)\n• Pengingat obat harian\n• Riwayat pengobatan\nMau saya cek jadwal?")

        return {
            "text": "\n".join(parts),
            "suggestions": ["Cek jadwal vaksin", "Cek jadwal obat", "Buat pengingat baru"],
            "cta": [{"type": "reminder", "label": "⏰ Cek Jadwal", "endpoint": "/api/v1/reminders"}],
            "disclaimer": "Pengingat bersifat informatif. Ikuti petunjuk dokter hewan.",
            "safety_warnings": warnings if warnings else [],
        }

    def _response_companion(
        self, pet_name: str, text: str, context: dict[str, Any], confidence: float = 0.0,
    ) -> dict[str, Any]:
        """🐾 Companion — template dulu, LLM hanya jika perlu."""
        resp = self._dynamic_response(
            "pet_companion", pet_name, text, context, intent_confidence=confidence,
        )
        if not resp["text"]:
            resp["text"] = f"Halo! Ada yang bisa Pawnia bantu untuk {pet_name} hari ini? 🐾\n\nSaya bisa:\n• Analisis gejala kesehatan\n• Screening via foto\n• Rekomendasi nutrisi\n• Pengingat obat & vaksin\n• Analisis perilaku\n• Booking dokter"
        resp.setdefault("suggestions", [
            "Cek kesehatan " + pet_name,
            "Rekomendasi makanan",
            "Jadwal vaksin",
            "Konsultasi dokter",
        ])
        resp.setdefault("cta", [{"type": "chat", "label": "💬 Mulai Konsultasi", "endpoint": "/api/v1/ai/chat"}])
        resp.setdefault("disclaimer", "")
        return resp



# =============================================================================
# SINGLETON
# =============================================================================

_pawnia_instance: PawniaOrchestrator | None = None


def get_pawnia(
    memory_service=None,
    knowledge_service=None,
    emr_service=None,
    llm_client=None,
) -> PawniaOrchestrator:
    """Get or create the Pawnia Orchestrator singleton."""
    global _pawnia_instance
    if _pawnia_instance is None:
        if memory_service is None:
            from .memory_store import get_memory_service
            memory_service = get_memory_service()
        if knowledge_service is None:
            try:
                from ..knowledge.rag import get_rag_service
                knowledge_service = get_rag_service(auto_ingest=False)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Knowledge RAG unavailable: %s", exc)
                knowledge_service = None
        _pawnia_instance = PawniaOrchestrator(
            memory_service=memory_service,
            knowledge_service=knowledge_service,
            emr_service=emr_service,
            llm_client=llm_client,
        )
    return _pawnia_instance