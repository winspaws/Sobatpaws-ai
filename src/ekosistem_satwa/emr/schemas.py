"""Pydantic schemas untuk EMR Service API endpoints.

Schemas untuk request/response sesuai PRD Part 7 API Specification.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
#  BASE SCHEMAS
# =============================================================================


class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
#  USER SCHEMAS
# =============================================================================


class UserBase(BaseModel):
    name: str = Field(..., max_length=160)
    email: str = Field(..., max_length=160)
    phone: str | None = Field(None, max_length=60)
    role: str = Field("pet_owner", max_length=60)
    preferences: dict[str, Any] | None = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: str | None = Field(None, max_length=160)
    email: str | None = Field(None, max_length=160)
    phone: str | None = Field(None, max_length=60)
    preferences: dict[str, Any] | None = None


class UserResponse(UserBase, TimestampMixin):
    id: int
    external_id: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
#  PET SCHEMAS
# =============================================================================


class PetBase(BaseModel):
    name: str = Field(..., max_length=120)
    species: str = Field(..., max_length=60)
    breed: str | None = Field(None, max_length=120)
    dob: date | None = None
    weight_kg: float | None = None
    neutered: bool | None = None
    sex: str | None = Field(None, max_length=10)
    photo_url: str | None = Field(None, max_length=500)
    notes: str | None = None


class PetCreate(PetBase):
    user_id: int


class PetUpdate(BaseModel):
    name: str | None = Field(None, max_length=120)
    breed: str | None = Field(None, max_length=120)
    dob: date | None = None
    weight_kg: float | None = None
    neutered: bool | None = None
    sex: str | None = Field(None, max_length=10)
    photo_url: str | None = Field(None, max_length=500)
    notes: str | None = None


class PetProfileResponse(BaseModel):
    id: int
    pet_id: int
    microchip: str | None = None
    allergies: list[str] | None = None
    chronic_conditions: list[str] | None = None
    blood_type: str | None = None
    insurance_policy: str | None = None
    emergency_contact: str | None = None
    additional_info: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PetResponse(PetBase, TimestampMixin):
    id: int
    user_id: int
    external_id: str | None = None
    is_active: bool
    profile: PetProfileResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class PetListResponse(BaseModel):
    pets: list[PetResponse]
    total: int


# =============================================================================
#  PET PROFILE SCHEMAS
# =============================================================================


class PetProfileCreate(BaseModel):
    pet_id: int
    microchip: str | None = Field(None, max_length=80)
    allergies: list[str] | None = None
    chronic_conditions: list[str] | None = None
    blood_type: str | None = Field(None, max_length=40)
    insurance_policy: str | None = Field(None, max_length=120)
    emergency_contact: str | None = Field(None, max_length=200)
    additional_info: dict[str, Any] | None = None


class PetProfileUpdate(BaseModel):
    microchip: str | None = Field(None, max_length=80)
    allergies: list[str] | None = None
    chronic_conditions: list[str] | None = None
    blood_type: str | None = Field(None, max_length=40)
    insurance_policy: str | None = Field(None, max_length=120)
    emergency_contact: str | None = Field(None, max_length=200)
    additional_info: dict[str, Any] | None = None


# =============================================================================
#  EMR RECORD SCHEMAS
# =============================================================================


class EMRRecordBase(BaseModel):
    visit_date: datetime = Field(default_factory=datetime.now)
    visit_type: str | None = Field(None, max_length=60)
    chief_complaint: str | None = None
    diagnosis: str | None = None
    diagnosis_codes: list[str] | None = None
    symptoms: list[str] | None = None
    physical_exam: dict[str, Any] | None = None
    notes: str | None = None
    vet_name: str | None = Field(None, max_length=120)
    vet_id: int | None = None
    clinic_id: str | None = Field(None, max_length=80)
    clinic_name: str | None = Field(None, max_length=200)
    procedures: list[str] | None = None
    attachments: list[dict[str, Any]] | None = None
    is_urgent: bool = False
    status: str = Field("completed", max_length=40)
    follow_up_date: date | None = None


class EMRRecordCreate(EMRRecordBase):
    pet_id: int


class EMRRecordUpdate(BaseModel):
    visit_date: datetime | None = None
    visit_type: str | None = Field(None, max_length=60)
    chief_complaint: str | None = None
    diagnosis: str | None = None
    diagnosis_codes: list[str] | None = None
    symptoms: list[str] | None = None
    physical_exam: dict[str, Any] | None = None
    notes: str | None = None
    vet_name: str | None = Field(None, max_length=120)
    clinic_name: str | None = Field(None, max_length=200)
    procedures: list[str] | None = None
    attachments: list[dict[str, Any]] | None = None
    is_urgent: bool | None = None
    status: str | None = Field(None, max_length=40)
    follow_up_date: date | None = None


class EMRRecordResponse(EMRRecordBase, TimestampMixin):
    id: int
    pet_id: int
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class EMRListResponse(BaseModel):
    records: list[EMRRecordResponse]
    total: int
    pet_name: str | None = None


# =============================================================================
#  VACCINATION SCHEMAS
# =============================================================================


class VaccinationBase(BaseModel):
    vaccine_type: str = Field(..., max_length=160)
    vaccine_brand: str | None = Field(None, max_length=120)
    vaccine_code: str | None = Field(None, max_length=60)
    date_administered: date
    next_due: date | None = None
    batch_number: str | None = Field(None, max_length=80)
    serial_number: str | None = Field(None, max_length=80)
    dosage_ml: float | None = None
    administration_site: str | None = Field(None, max_length=80)
    vet_name: str | None = Field(None, max_length=120)
    clinic_name: str | None = Field(None, max_length=200)
    notes: str | None = None
    adverse_reaction: str | None = None
    certificate_url: str | None = Field(None, max_length=500)


class VaccinationCreate(VaccinationBase):
    pet_id: int


class VaccinationUpdate(BaseModel):
    vaccine_type: str | None = Field(None, max_length=160)
    vaccine_brand: str | None = Field(None, max_length=120)
    next_due: date | None = None
    notes: str | None = None
    adverse_reaction: str | None = None
    is_valid: bool | None = None


class VaccinationResponse(VaccinationBase, TimestampMixin):
    id: int
    pet_id: int
    is_valid: bool

    model_config = ConfigDict(from_attributes=True)


class VaccinationListResponse(BaseModel):
    vaccinations: list[VaccinationResponse]
    total: int
    upcoming_count: int = 0
    overdue_count: int = 0


# =============================================================================
#  MEDICATION SCHEMAS
# =============================================================================


class MedicationBase(BaseModel):
    medication_name: str = Field(..., max_length=200)
    generic_name: str | None = Field(None, max_length=200)
    drug_code: str | None = Field(None, max_length=80)
    category: str | None = Field(None, max_length=80)
    dosage: str = Field(..., max_length=120)
    dosage_kg: float | None = None
    frequency: str = Field(..., max_length=80)
    frequency_hours: int | None = None
    route: str | None = Field(None, max_length=60)
    start_date: date
    end_date: date | None = None
    duration_days: int | None = None
    quantity: str | None = Field(None, max_length=80)
    refills: int | None = 0
    prescribing_vet: str | None = Field(None, max_length=120)
    instructions: str | None = None
    side_effects: str | None = None
    contraindications: str | None = None
    is_chronic: bool = False
    notes: str | None = None


class MedicationCreate(MedicationBase):
    pet_id: int
    emr_record_id: int | None = None


class MedicationUpdate(BaseModel):
    dosage: str | None = Field(None, max_length=120)
    frequency: str | None = Field(None, max_length=80)
    end_date: date | None = None
    instructions: str | None = None
    is_active: bool | None = None
    notes: str | None = None


class MedicationResponse(MedicationBase, TimestampMixin):
    id: int
    pet_id: int
    emr_record_id: int | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class MedicationListResponse(BaseModel):
    medications: list[MedicationResponse]
    total: int
    active_count: int = 0


# =============================================================================
#  CONSULTATION SCHEMAS
# =============================================================================


class ConsultationBase(BaseModel):
    status: str = Field("active", max_length=40)
    chief_complaint: str | None = None
    symptoms_reported: list[str] | None = None
    vitals: dict[str, Any] | None = None


class ConsultationCreate(ConsultationBase):
    pet_id: int
    user_id: int


class ConsultationResponse(ConsultationBase, TimestampMixin):
    id: int
    consultation_uuid: UUID
    pet_id: int
    user_id: int
    thread_id: int | None = None
    agent_used: str | None = None
    model_used: str | None = None
    confidence: float | None = None
    risk_score: float | None = None
    risk_level: str | None = None
    suggested_diseases: list[dict[str, Any]] | None = None
    suggested_diagnostics: list[str] | None = None
    suggested_treatments: list[dict[str, Any]] | None = None
    summary: str | None = None
    red_flags: list[str] | None = None
    safety_warnings: list[str] | None = None
    disclaimer: str
    escalated_to_vet: bool
    escalation_reason: str | None = None
    doctor_feedback: dict[str, Any] | None = None
    started_at: datetime
    ended_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
#  NOTIFICATION SCHEMAS
# =============================================================================


class NotificationBase(BaseModel):
    type: str = Field(..., max_length=60, description="jenis notifikasi: vaccine_reminder | medication_reminder | appointment | emergency | weekly_digest | re_engagement")
    channel: str = Field("in_app", max_length=40, description="in_app | email | push | sms | whatsapp")
    title: str = Field(..., max_length=200)
    body: str
    template_id: str | None = Field(None, max_length=80)
    data: dict[str, Any] | None = None
    scheduled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    consultation_id: int | None = None
    recommendation_id: int | None = None
    extra_metadata: dict[str, Any] | None = None


class NotificationCreate(NotificationBase):
    user_id: int
    pet_id: int | None = None


class NotificationUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    body: str | None = None
    data: dict[str, Any] | None = None
    scheduled_at: datetime | None = None
    status: str | None = Field(None, max_length=40)


class NotificationConfirmRequest(BaseModel):
    action: str = Field("read", description="Action performed: read | clicked | dismissed | snoozed")
    snooze_minutes: int | None = Field(None, description="Minutes to snooze (if action=snoozed)")


class NotificationResponse(NotificationBase, TimestampMixin):
    id: int
    user_id: int
    pet_id: int | None = None
    sent_at: datetime | None = None
    read_at: datetime | None = None
    clicked_at: datetime | None = None
    status: str = Field("pending", max_length=40)
    failure_reason: str | None = None
    retry_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total: int
    pending_count: int = 0
    unread_count: int = 0


# =============================================================================
#  API RESPONSE WRAPPERS
# =============================================================================


class ApiResponse(BaseModel):
    success: bool = True
    message: str | None = None
    data: dict[str, Any] | list[Any] | None = None


class ApiError(BaseModel):
    success: bool = False
    error: str
    detail: str | None = None
