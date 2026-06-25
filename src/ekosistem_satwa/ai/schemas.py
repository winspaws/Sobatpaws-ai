"""Skema input/output terstruktur untuk AI suggestion (selaras tabel ai_suggestions)."""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

DEFAULT_DISCLAIMER = (
    "Saran AI bersifat pendukung keputusan klinis dan TIDAK menggantikan "
    "pemeriksaan langsung serta penilaian dokter hewan berlisensi. Dosis & "
    "produk wajib diverifikasi sesuai spesies, berat badan, dan kondisi pasien."
)


class SuggestionRequest(BaseModel):
    """Permintaan saran untuk satu kasus."""

    category_slug: str = Field(..., description="slug spesies, mis. 'dog'")
    breed_slug: str | None = Field(None, description="slug ras bila diketahui")
    symptoms: list[str] = Field(default_factory=list,
                                description="daftar gejala (name_id), mis. ['Muntah hebat']")
    age_years: float | None = None
    weight_kg: float | None = None
    sex: str | None = None
    is_neutered: bool | None = None
    chief_complaint: str | None = None
    vitals: dict | None = None
    top_k: int = 5


class DiseaseHypothesis(BaseModel):
    disease_slug: str
    name_id: str | None = None
    confidence: float = Field(..., ge=0, le=1)
    rationale: str | None = None
    source: str = "ml"  # ml | knowledge_base | breed_risk | llm
    is_emergency: bool = False


class DiagnosticStep(BaseModel):
    name: str
    type: str | None = None
    is_gold_standard: bool = False
    expected_finding: str | None = None


class TreatmentSuggestion(BaseModel):
    name: str
    type: str | None = None
    line_of_therapy: int | None = None
    recommendation: str | None = None
    procedure_steps: str | None = None


class ProductSuggestion(BaseModel):
    name: str
    kind: str | None = None
    active_ingredient: str | None = None
    dosage_guide: str | None = None
    route: str | None = None
    cautions: str | None = None
    safety_flag: str | None = Field(
        None, description="peringatan keamanan spesies bila terdeteksi kontraindikasi")


class SuggestionResponse(BaseModel):
    """Output terstruktur untuk vet (disimpan ke ai_suggestions)."""

    category_slug: str
    breed_slug: str | None = None
    summary: str
    is_emergency: bool = False
    suggested_diseases: list[DiseaseHypothesis] = Field(default_factory=list)
    suggested_diagnostics: list[DiagnosticStep] = Field(default_factory=list)
    suggested_treatments: list[TreatmentSuggestion] = Field(default_factory=list)
    suggested_products: list[ProductSuggestion] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    model_used: str = Field(default="rule_based")
    disclaimer: str = DEFAULT_DISCLAIMER

    model_config = {"protected_namespaces": ()}


# =============================================================================
#  SKEMA KONSULTASI MULTIMODAL (intake mic/kamera/teks -> saran -> learning)
#  Melengkapi skema single-shot di atas untuk alur aplikasi dokter real-time.
# =============================================================================

from datetime import datetime, timezone  # noqa: E402
from enum import Enum  # noqa: E402
from typing import Any  # noqa: E402


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ConsultationChannel(str, Enum):
    """Kanal konsultasi pada aplikasi dokter."""

    chat = "chat"
    video = "video"
    voice = "voice"
    in_person = "in_person"


class IntakeModality(str, Enum):
    """Sumber tangkapan input dari tools aplikasi."""

    text = "text"                # ketikan keluhan user
    audio = "audio"              # tangkapan mikrofon (di-transkripsi)
    image = "image"              # tangkapan kamera / foto (dianalisa vision)
    video_frame = "video_frame"  # frame dari sesi video


class ConsultationContext(BaseModel):
    """Konteks pasien & sesi (selaras pets / clinical_cases / users / org)."""

    org_id: int | None = Field(None, description="organizations.id — klinik/cabang")
    user_id: int | None = Field(default=None, description="users.id — dokter (alias vet_id)")
    vet_id: int | None = Field(default=None, description="users.id — dokter hewan")
    doctor_id: int | None = Field(default=None, description="alias vet_id")
    owner_id: int | None = Field(default=None, description="pet_owners.id — pemilik/pelanggan")
    customer_id: int | None = Field(default=None, description="alias owner_id — pelanggan")
    pet_id: int | None = Field(None, description="pets.id")
    case_id: int | None = Field(None, description="clinical_cases.id")

    external_consultation_id: str | None = Field(
        default=None,
        description="ID konsultasi/kasus dari app Ekosistem Satwa utama (untuk lookup & sync)",
    )
    external_refs: dict[str, str] = Field(
        default_factory=dict,
        description="ID tambahan dari CRM/ERP, mis. appointment_id, invoice_id",
    )

    category_slug: str | None = Field(
        default=None, description="spesies: dog, cat, rabbit, ... (untuk pilih model)"
    )
    breed_slug: str | None = None
    age_years: float | None = None
    weight_kg: float | None = None
    sex: str | None = Field(default=None, description="male | female | unknown")
    is_neutered: bool | None = None

    temperature_c: float | None = None
    heart_rate: int | None = None
    resp_rate: int | None = None

    @model_validator(mode="after")
    def _sync_entity_aliases(self) -> ConsultationContext:
        vet = self.vet_id or self.doctor_id or self.user_id
        if vet is not None:
            self.vet_id = self.doctor_id = self.user_id = vet
        owner = self.owner_id or self.customer_id
        if owner is not None:
            self.owner_id = self.customer_id = owner
        return self


class MediaPayload(BaseModel):
    """Muatan media mentah dari mikrofon/kamera (base64) atau referensi URI."""

    modality: IntakeModality
    mime_type: str | None = None
    base64_data: str | None = Field(default=None, description="data biner ter-encode base64")
    uri: str | None = Field(default=None, description="alternatif: lokasi file/objek")
    pretranscribed_text: str | None = None


class IntakePayload(BaseModel):
    """Satu paket input dari user/dokter pada satu giliran percakapan."""

    channel: ConsultationChannel = ConsultationChannel.chat
    text: str | None = Field(default=None, description="keluhan / pesan teks")
    media: list[MediaPayload] = Field(default_factory=list)
    is_first_contact: bool = Field(
        default=False, description="True bila keluhan pertama saat mulai konsultasi"
    )
    author_role: str = Field(default="owner", description="owner | vet")


class MediaObservation(BaseModel):
    """Hasil pemrosesan satu media (transkrip audio / deskripsi gambar)."""

    modality: IntakeModality
    text: str = Field(description="transkrip atau deskripsi temuan")
    source: str = Field(description="provider/metode, mis. speech_to_text, vision, client")
    confidence: float | None = None
    structured: dict[str, Any] | None = None
    structured_model: str | None = None


class VisionLesion(BaseModel):
    """Lesion or abnormality detected in a veterinary image."""

    location: str = Field(description="anatomical location, e.g. 'left_ear', 'dorsal_trunk', 'right_eye'")
    type: str = Field(description="lesion type, e.g. 'laceration', 'abscess', 'erythema', 'discharge'")
    severity: str = Field(description="'mild' | 'moderate' | 'severe'")
    description: str = Field(description="detailed description of the lesion")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class StructuredVisionOutput(BaseModel):
    """Structured output from veterinary vision analysis for clinical use."""

    species_detected: str | None = Field(
        None, description="detected species: dog, cat, rabbit, hamster, poultry, fish, reptile, amphibian, ferret, guinea_pig"
    )
    breed_hints: list[str] = Field(
        default_factory=list, description="list of breed matches from knowledge base (max 3)"
    )
    age_estimate_min_years: float | None = Field(
        None, description="minimum estimated age in years"
    )
    age_estimate_max_years: float | None = Field(
        None, description="maximum estimated age in years"
    )
    age_confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="confidence in age estimate"
    )
    lesions: list[VisionLesion] = Field(
        default_factory=list, description="detected lesions and abnormalities"
    )
    red_flags: list[str] = Field(
        default_factory=list, description="emergency signs: pale_mucosa, respiratory_distress, active_bleeding, etc."
    )
    extracted_symptoms: list[str] = Field(
        default_factory=list, description="detected symptoms matching KB name_id terms"
    )
    raw_description: str = Field(description="natural language description in Indonesian")
    processing_time_ms: float | None = Field(
        None, description="time taken to process in milliseconds"
    )


class ExtractedSymptom(BaseModel):
    """Gejala yang dikenali & dipetakan ke kosakata knowledge base."""

    name_id: str
    name: str | None = None
    body_system: str | None = None
    is_red_flag: bool = False
    score: float = Field(default=1.0, description="keyakinan pencocokan 0..1")
    matched_text: str | None = None


class IntakeResult(BaseModel):
    """Hasil normalisasi seluruh modalitas input menjadi sinyal klinis."""

    complaint_text: str = Field(default="", description="gabungan keluhan ter-normalisasi")
    observations: list[MediaObservation] = Field(default_factory=list)
    symptoms: list[ExtractedSymptom] = Field(default_factory=list)
    channel: ConsultationChannel = ConsultationChannel.chat
    created_at: datetime = Field(default_factory=_now)

    def symptom_name_ids(self) -> list[str]:
        return [s.name_id for s in self.symptoms]

    def has_red_flag(self) -> bool:
        return any(s.is_red_flag for s in self.symptoms)


class SuggestedDisease(BaseModel):
    disease_slug: str
    name_id: str | None = None
    confidence: float = Field(description="0..1")
    rationale: str | None = None
    is_emergency: bool = False
    source: str = Field(default="ml", description="ml | knowledge_base | llm")


class SuggestedDiagnostic(BaseModel):
    name: str
    type: str | None = None
    step_order: int | None = None
    is_gold_standard: bool = False
    expected_finding: str | None = None
    for_disease: str | None = None


class SuggestedTreatment(BaseModel):
    name: str
    type: str | None = None
    line_of_therapy: int | None = None
    procedure_steps: str | None = None
    recommendation: str | None = None
    for_disease: str | None = None


class SuggestedProduct(BaseModel):
    name: str
    kind: str | None = None
    active_ingredient: str | None = None
    route: str | None = None
    dosage_guide: str | None = None
    cautions: str | None = None
    safety_flag: str | None = Field(
        default=None, description="peringatan kontraindikasi spesies bila terdeteksi"
    )


class AISuggestion(BaseModel):
    """Output terstruktur untuk ditampilkan ke dokter (mendukung, bukan final)."""

    suggestion_type: str = Field(default="symptom_to_disease")
    summary: str = Field(default="")
    follow_up_questions: list[str] = Field(default_factory=list)
    suggested_diseases: list[SuggestedDisease] = Field(default_factory=list)
    suggested_diagnostics: list[SuggestedDiagnostic] = Field(default_factory=list)
    suggested_treatments: list[SuggestedTreatment] = Field(default_factory=list)
    suggested_products: list[SuggestedProduct] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    safety_warnings: list[str] = Field(default_factory=list)
    references: list[dict[str, Any]] = Field(default_factory=list)
    is_emergency: bool = False
    generated_by: str = Field(default="rule_based", description="rule_based | llm_augmented")
    disclaimer: str = DEFAULT_DISCLAIMER
    created_at: datetime = Field(default_factory=_now)


class DoctorInput(BaseModel):
    """Apa pun yang diinput dokter — disimpan sebagai bahan pembelajaran.

    Dipetakan ke case_diagnoses / case_treatments / clinical_cases.
    """

    consultation_id: str | None = None
    case_id: int | None = None
    vet_id: int | None = None
    org_id: int | None = None
    owner_id: int | None = None
    customer_id: int | None = None
    pet_id: int | None = None
    external_consultation_id: str | None = None

    confirmed_disease_slug: str | None = None
    differential_disease_slugs: list[str] = Field(default_factory=list)
    confirmed_symptoms: list[str] = Field(
        default_factory=list, description="name_id gejala yang dikonfirmasi dokter"
    )
    diagnostics_ordered: list[str] = Field(default_factory=list)
    treatments_given: list[str] = Field(default_factory=list)
    products_prescribed: list[str] = Field(default_factory=list)
    clinical_notes: str | None = None
    outcome: str | None = None
    confidence: float | None = Field(default=None, description="0..100 keyakinan dokter")


class SuggestionFeedback(BaseModel):
    """Penilaian dokter atas saran AI (human-in-the-loop)."""

    consultation_id: str | None = None
    suggestion_ref: str | None = None
    verdict: str = Field(description="correct | partially_correct | incorrect | not_applicable")
    corrected_disease_slug: str | None = None
    comment: str | None = None
    reviewer_id: int | None = None


class AgentChatRequest(BaseModel):
    """Pesan interaktif ke agent AI dalam sesi konsultasi."""

    message: str = Field(..., min_length=1, max_length=4000)
    provider_id: str | None = Field(
        None, description="opsional: paksa provider (openai|anthropic|local|custom id)"
    )


class AgentChatResponse(BaseModel):
    consultation_id: str
    reply: str
    follow_up_questions: list[str] = Field(default_factory=list)
    action_hint: str | None = None
    request_id: str | None = None
    provider_used: str | None = None


class ProviderUpsertRequest(BaseModel):
    id: str
    name: str
    kind: str = "custom"
    base_url: str | None = None
    default_model: str = ""
    api_key: str | None = None
    is_active: bool = True


class SuggestionReviewRequest(BaseModel):
    note: str | None = None
    reviewed: bool = True


# =============================================================================
#  SKEMA CONSULTATION ENHANCEMENT — Multi-turn, History, Session Management
# =============================================================================

from enum import Enum  # noqa: E402


class SessionStatus(str, Enum):
    """Status sesi konsultasi untuk manajemen."""

    active = "active"
    archived = "archived"
    closed = "closed"


class ConsultChatRequest(BaseModel):
    """Request untuk multi-turn chat dengan session_id.

    Jika session_id null/empty, session baru dibuat otomatis.
    """

    session_id: str | None = Field(
        default=None,
        description="ID sesi (opsional; buat baru jika kosong)",
    )
    message: str = Field(
        ..., min_length=1, max_length=4000,
        description="Pesan teks dari user/dokter",
    )
    context: ConsultationContext | None = Field(
        default=None,
        description="Konteks pasien (wajib untuk session baru)",
    )
    provider_id: str | None = Field(
        default=None,
        description="Paksa provider LLM tertentu (opsional)",
    )
    include_suggestion: bool = Field(
        default=True,
        description="True = jalankan intake + AI suggestion; False = chat biasa saja",
    )


class ConsultChatResponse(BaseModel):
    """Response untuk chat endpoint."""

    session_id: str
    message_id: str | None = None
    reply: str
    follow_up_questions: list[str] = Field(default_factory=list)
    is_new_session: bool = False
    suggestion: AISuggestion | None = None
    intake: IntakeResult | None = None
    suggestion_id: str | None = None
    request_id: str | None = None
    provider_used: str | None = None


class ConsultSessionCreate(BaseModel):
    """Request untuk membuat session baru tanpa chat."""

    context: ConsultationContext = Field(
        ...,
        description="Konteks pasien untuk sesi ini",
    )
    title: str | None = Field(
        default=None,
        description="Judul/ringkasan sesi (opsional)",
    )


class ConsultSessionResponse(BaseModel):
    """Response untuk session management."""

    session_id: str
    title: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime | None = None
    context: dict[str, Any] | None = None
    message_count: int = 0
    suggestion_count: int = 0


class MessageItem(BaseModel):
    """Satu pesan dalam riwayat."""

    id: str
    role: str  # user | assistant | vet | system
    content: str
    created_at: datetime
    meta: dict[str, Any] = Field(default_factory=dict)


class ConsultHistoryResponse(BaseModel):
    """Response untuk riwayat percakapan dengan pagination."""

    session_id: str
    messages: list[MessageItem]
    total: int
    limit: int
    offset: int
    has_more: bool


class ConsultSessionListResponse(BaseModel):
    """Response untuk list sessions."""

    sessions: list[ConsultSessionResponse]
    total: int
    limit: int
    offset: int
    status_filter: SessionStatus | None = None
