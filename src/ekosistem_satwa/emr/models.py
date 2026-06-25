"""EMR Service SQLAlchemy models.

Database schema untuk rekam medis elektronik hewan dan platform AI.
Tabel sesuai PRD Part 7 (API Specification & Database Design).

Python 3.9 compatible: menggunakan Optional[...] bukan X | None
karena SQLAlchemy 2.0 Mapped tidak kompatibel dengan sintaks PEP604
di Python 3.9.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class untuk semua model EMR."""

    type_annotation_map = {
        Dict[str, Any]: JSON,
        List[str]: JSON,
        List[Dict[str, Any]]: JSON,
        uuid.UUID: UUID(as_uuid=True),
    }


# =============================================================================
#  TABEL UTAMA EMR
# =============================================================================


class User(Base):
    """Pengguna sistem (pemilik hewan, dokter, admin)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[Optional[str]] = mapped_column(
        String(80), unique=True, nullable=True,
        comment="ID dari sistem eksternal / auth provider",
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(60))
    role: Mapped[str] = mapped_column(
        String(60), nullable=False, default="pet_owner",
        comment="pet_owner | vet | clinic_staff | admin",
    )
    preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    pets: Mapped[List[Pet]] = relationship("Pet", back_populates="owner", lazy="select")
    consultations: Mapped[List[Consultation]] = relationship(
        "Consultation", back_populates="user", lazy="select",
    )
    conversation_threads: Mapped[List[ConversationThread]] = relationship(
        "ConversationThread", back_populates="user", lazy="select",
    )
    ai_memories: Mapped[List[AIMemory]] = relationship(
        "AIMemory", back_populates="user", lazy="select",
    )
    notifications: Mapped[List[Notification]] = relationship(
        "Notification", back_populates="user", lazy="select",
    )
    audit_logs: Mapped[List[AuditLog]] = relationship(
        "AuditLog", back_populates="user", lazy="select",
    )

    __table_args__ = (
        Index("ix_users_email", "email"),
        Index("ix_users_role", "role"),
        Index("ix_users_external_id", "external_id"),
    )


class Pet(Base):
    """Data dasar hewan peliharaan."""

    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    external_id: Mapped[Optional[str]] = mapped_column(
        String(80), unique=True, nullable=True,
        comment="ID dari sistem eksternal",
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    species: Mapped[str] = mapped_column(
        String(60), nullable=False,
        comment="dog | cat | rabbit | hamster | poultry | fish | reptile | amphibian | ferret | guinea_pig",
    )
    breed: Mapped[Optional[str]] = mapped_column(String(120))
    dob: Mapped[Optional[date]] = mapped_column(Date, comment="tanggal lahir")
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, comment="berat dalam kg")
    neutered: Mapped[Optional[bool]] = mapped_column(Boolean, comment="sudah disteril")
    sex: Mapped[Optional[str]] = mapped_column(String(10), comment="male | female | unknown")
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), comment="URL foto profil")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    owner: Mapped[User] = relationship("User", back_populates="pets", lazy="joined")
    profile: Mapped[Optional[PetProfile]] = relationship(
        "PetProfile", back_populates="pet", uselist=False, lazy="select",
    )
    emr_records: Mapped[List[EMRRecord]] = relationship(
        "EMRRecord", back_populates="pet", lazy="select",
    )
    vaccinations: Mapped[List[Vaccination]] = relationship(
        "Vaccination", back_populates="pet", lazy="select",
    )
    medications: Mapped[List[Medication]] = relationship(
        "Medication", back_populates="pet", lazy="select",
    )
    consultations: Mapped[List[Consultation]] = relationship(
        "Consultation", back_populates="pet", lazy="select",
    )
    conversation_threads: Mapped[List[ConversationThread]] = relationship(
        "ConversationThread", back_populates="pet", lazy="select",
    )
    ai_memories: Mapped[List[AIMemory]] = relationship(
        "AIMemory", back_populates="pet", lazy="select",
    )
    recommendations: Mapped[List[Recommendation]] = relationship(
        "Recommendation", back_populates="pet", lazy="select",
    )
    notifications: Mapped[List[Notification]] = relationship(
        "Notification", back_populates="pet", lazy="select",
    )
    audit_logs: Mapped[List[AuditLog]] = relationship(
        "AuditLog", back_populates="pet", lazy="select",
    )

    __table_args__ = (
        Index("ix_pets_user_id", "user_id"),
        Index("ix_pets_species", "species"),
        Index("ix_pets_external_id", "external_id"),
    )


class PetProfile(Base):
    """Profil medis lengkap hewan (alergi, kondisi kronis, microchip)."""

    __tablename__ = "pet_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pets.id", ondelete="CASCADE"), nullable=False, unique=True,
    )
    microchip: Mapped[Optional[str]] = mapped_column(
        String(80), comment="nomor microchip",
    )
    allergies: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, comment="daftar alergi",
    )
    chronic_conditions: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, comment="daftar kondisi medis kronis",
    )
    blood_type: Mapped[Optional[str]] = mapped_column(String(40))
    insurance_policy: Mapped[Optional[str]] = mapped_column(String(120))
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(200))
    additional_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
    )

    # Relationships
    pet: Mapped[Pet] = relationship("Pet", back_populates="profile", lazy="joined")


class EMRRecord(Base):
    """Rekam medis elektronik — satu baris per kunjungan/episode medis."""

    __tablename__ = "emr_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pets.id", ondelete="CASCADE"), nullable=False,
    )
    visit_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
    )
    visit_type: Mapped[Optional[str]] = mapped_column(
        String(60), comment="checkup | emergency | vaccination | followup | surgery",
    )
    chief_complaint: Mapped[Optional[str]] = mapped_column(Text)
    diagnosis: Mapped[Optional[str]] = mapped_column(
        Text, comment="diagnosa utama (free text)",
    )
    diagnosis_codes: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, comment="kode ICD/penyakit terstruktur",
    )
    symptoms: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, comment="gejala yang diamati",
    )
    physical_exam: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True,
        comment="pemeriksaan fisik: temperature, heart_rate, resp_rate, weight, dll",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, comment="catatan medis lengkap",
    )
    vet_name: Mapped[Optional[str]] = mapped_column(String(120), comment="nama dokter")
    vet_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True,
    )
    clinic_id: Mapped[Optional[str]] = mapped_column(String(80), comment="ID klinik")
    clinic_name: Mapped[Optional[str]] = mapped_column(String(200))
    procedures: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, comment="tindakan yang dilakukan",
    )
    attachments: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB, nullable=True, comment="lampiran: foto, lab result, dokumen",
    )
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(
        String(40), nullable=False, default="completed",
        comment="draft | in_progress | completed | referred",
    )
    follow_up_date: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    pet: Mapped[Pet] = relationship("Pet", back_populates="emr_records", lazy="joined")

    __table_args__ = (
        Index("ix_emr_records_pet_id", "pet_id"),
        Index("ix_emr_records_visit_date", "visit_date"),
        Index("ix_emr_records_status", "status"),
    )


class Vaccination(Base):
    """Riwayat vaksinasi hewan."""

    __tablename__ = "vaccinations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pets.id", ondelete="CASCADE"), nullable=False,
    )
    vaccine_type: Mapped[str] = mapped_column(
        String(160), nullable=False,
        comment="jenis vaksin: rabies, distemper, parvovirus, fvrcp, dll",
    )
    vaccine_brand: Mapped[Optional[str]] = mapped_column(String(120))
    vaccine_code: Mapped[Optional[str]] = mapped_column(String(60))
    date_administered: Mapped[date] = mapped_column(Date, nullable=False)
    next_due: Mapped[Optional[date]] = mapped_column(Date, comment="tanggal booster berikutnya")
    batch_number: Mapped[Optional[str]] = mapped_column(String(80))
    serial_number: Mapped[Optional[str]] = mapped_column(String(80))
    dosage_ml: Mapped[Optional[float]] = mapped_column(Float, comment="dosis dalam ml")
    administration_site: Mapped[Optional[str]] = mapped_column(
        String(80), comment="tempat suntik: scruff, hind leg, dll",
    )
    vet_name: Mapped[Optional[str]] = mapped_column(String(120))
    clinic_name: Mapped[Optional[str]] = mapped_column(String(200))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    adverse_reaction: Mapped[Optional[str]] = mapped_column(
        Text, comment="reaksi alergi/efek samping",
    )
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    certificate_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
    )

    # Relationships
    pet: Mapped[Pet] = relationship("Pet", back_populates="vaccinations", lazy="joined")

    __table_args__ = (
        Index("ix_vaccinations_pet_id", "pet_id"),
        Index("ix_vaccinations_date_administered", "date_administered"),
        Index("ix_vaccinations_next_due", "next_due"),
        Index("ix_vaccinations_vaccine_type", "vaccine_type"),
    )


class Medication(Base):
    """Obat yang sedang/resep untuk hewan."""

    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pets.id", ondelete="CASCADE"), nullable=False,
    )
    emr_record_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("emr_records.id"), nullable=True,
    )
    medication_name: Mapped[str] = mapped_column(String(200), nullable=False)
    generic_name: Mapped[Optional[str]] = mapped_column(String(200))
    drug_code: Mapped[Optional[str]] = mapped_column(String(80))
    category: Mapped[Optional[str]] = mapped_column(
        String(80), comment="antibiotic | antiparasitic | analgesic | anti-inflammatory | dll",
    )
    dosage: Mapped[str] = mapped_column(
        String(120), nullable=False,
        comment="dosis per pemberian: 5mg, 1 tablet, 0.5ml",
    )
    dosage_kg: Mapped[Optional[float]] = mapped_column(
        Float, comment="dosis per kg berat badan (untuk kalkulasi)",
    )
    frequency: Mapped[str] = mapped_column(
        String(80), nullable=False,
        comment="frekuensi: sid (sekali sehari), bid (dua kali sehari), tid, q8h, prn",
    )
    frequency_hours: Mapped[Optional[int]] = mapped_column(
        Integer, comment="interval dalam jam: 24, 12, 8, dll",
    )
    route: Mapped[Optional[str]] = mapped_column(
        String(60), comment="oral | topical | injectable_sc | injectable_im | injectable_iv",
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(
        Date, comment="tanggal selesai (untuk obat jangka pendek)",
    )
    duration_days: Mapped[Optional[int]] = mapped_column(
        Integer, comment="durasi pengobatan dalam hari",
    )
    quantity: Mapped[Optional[str]] = mapped_column(String(80), comment="jumlah yang diberikan")
    refills: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    prescribing_vet: Mapped[Optional[str]] = mapped_column(String(120))
    instructions: Mapped[Optional[str]] = mapped_column(
        Text, comment="instruksi khusus: berikan bersama makanan, dll",
    )
    side_effects: Mapped[Optional[str]] = mapped_column(Text)
    contraindications: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True,
        comment="True = masih dalam penggunaan",
    )
    is_chronic: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="True = obat jangka panjang/kronis",
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
    )

    # Relationships
    pet: Mapped[Pet] = relationship("Pet", back_populates="medications", lazy="joined")

    __table_args__ = (
        Index("ix_medications_pet_id", "pet_id"),
        Index("ix_medications_is_active", "is_active"),
        Index("ix_medications_start_date", "start_date"),
        Index("ix_medications_category", "category"),
    )


# =============================================================================
#  TABEL KONSULTASI AI & CONVERSATION
# =============================================================================


class Consultation(Base):
    """Riwayat konsultasi AI Gateway."""

    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    consultation_uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4,
    )
    pet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pets.id", ondelete="CASCADE"), nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False,
    )
    thread_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("conversation_threads.id"), nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(40), nullable=False, default="active",
        comment="active | completed | escalated | closed",
    )
    agent_used: Mapped[Optional[str]] = mapped_column(
        String(80), comment="nama/tipe agent: ml_only | llm_augmented | hybrid",
    )
    model_used: Mapped[Optional[str]] = mapped_column(
        String(120), comment="model LLM yang dipakai: gpt-4o, claude-sonnet, dll",
    )
    confidence: Mapped[Optional[float]] = mapped_column(
        Float, comment="skor keyakinan AI 0.0 - 1.0",
    )
    risk_score: Mapped[Optional[float]] = mapped_column(
        Float, comment="skor risiko 0.0 - 1.0 (semakin tinggi semakin berbahaya)",
    )
    risk_level: Mapped[Optional[str]] = mapped_column(
        String(20), comment="very_low | low | moderate | high | very_high",
    )
    chief_complaint: Mapped[Optional[str]] = mapped_column(Text)
    symptoms_reported: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, comment="daftar gejala yang dilaporkan",
    )
    vitals: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, comment="tanda-tanda vital: temperature, heart_rate, dll",
    )
    suggested_diseases: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB, nullable=True,
        comment="daftar penyakit yang disarankan AI dengan confidence dan rationale",
    )
    suggested_diagnostics: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, comment="pemeriksaan yang disarankan",
    )
    suggested_treatments: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB, nullable=True, comment="tindakan pengobatan yang disarankan",
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text, comment="ringkasan konsultasi dari AI",
    )
    red_flags: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, comment="tanda bahaya yang terdeteksi",
    )
    safety_warnings: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, comment="peringatan keamanan",
    )
    disclaimer: Mapped[str] = mapped_column(
        String(500),
        default="Saran AI bersifat pendukung keputusan klinis dan TIDAK menggantikan pemeriksaan langsung oleh dokter hewan berlisensi.",
    )
    escalated_to_vet: Mapped[bool] = mapped_column(Boolean, default=False)
    escalation_reason: Mapped[Optional[str]] = mapped_column(Text)
    doctor_feedback: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, comment="feedback dari dokter jika ada",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
    )

    # Relationships
    pet: Mapped[Pet] = relationship("Pet", back_populates="consultations", lazy="joined")
    user: Mapped[User] = relationship("User", back_populates="consultations", lazy="joined")

    __table_args__ = (
        Index("ix_consultations_pet_id", "pet_id"),
        Index("ix_consultations_user_id", "user_id"),
        Index("ix_consultations_consultation_uuid", "consultation_uuid"),
        Index("ix_consultations_status", "status"),
        Index("ix_consultations_risk_level", "risk_level"),
        Index("ix_consultations_started_at", "started_at"),
    )


class ConversationThread(Base):
    """Sesi percakapan/pesan dengan AI Agent."""

    __tablename__ = "conversation_threads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4,
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False,
    )
    pet_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("pets.id"), nullable=True,
    )
    consultation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("consultations.id"), nullable=True,
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(200), comment="judul/ringkasan percakapan",
    )
    channel: Mapped[str] = mapped_column(
        String(40), nullable=False, default="chat",
        comment="chat | voice | video | in_person",
    )
    status: Mapped[str] = mapped_column(
        String(40), nullable=False, default="active",
        comment="active | archived | closed",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
    )

    # Relationships
    user: Mapped[User] = relationship(
        "User", back_populates="conversation_threads", lazy="joined",
    )
    pet: Mapped[Optional[Pet]] = relationship(
        "Pet", back_populates="conversation_threads", lazy="joined",
    )
    messages: Mapped[List[ConversationMessage]] = relationship(
        "ConversationMessage", back_populates="thread",
        order_by="ConversationMessage.created_at", lazy="select",
    )

    __table_args__ = (
        Index("ix_conversation_threads_user_id", "user_id"),
        Index("ix_conversation_threads_pet_id", "pet_id"),
        Index("ix_conversation_threads_thread_uuid", "thread_uuid"),
        Index("ix_conversation_threads_status", "status"),
        Index("ix_conversation_threads_started_at", "started_at"),
    )


class ConversationMessage(Base):
    """Pesan individual dalam conversation thread."""

    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4,
    )
    thread_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversation_threads.id", ondelete="CASCADE"), nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(40), nullable=False,
        comment="user | assistant | system | tool",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    agent: Mapped[Optional[str]] = mapped_column(
        String(80), comment="nama agent/provider untuk pesan assistant: gpt-4o, claude, rule_based",
    )
    parent_message_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("conversation_messages.id"), nullable=True,
    )
    turn_number: Mapped[Optional[int]] = mapped_column(
        Integer, comment="urutan giliran dalam percakapan",
    )
    intent: Mapped[Optional[str]] = mapped_column(
        String(80), comment="intent yang terdeteksi: symptom_report | question | follow_up",
    )
    entities: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, comment="entitas yang diekstrak: gejala, durasi, dll",
    )
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True,
        comment="metadata tambahan: token usage, latency, provider info, tool calls",
    )
    tokens_used: Mapped[Optional[int]] = mapped_column(
        Integer, comment="jumlah token yang dipakai (untuk LLM)",
    )
    latency_ms: Mapped[Optional[int]] = mapped_column(
        Integer, comment="waktu respons dalam milidetik",
    )
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
    )

    # Relationships
    thread: Mapped[ConversationThread] = relationship(
        "ConversationThread", back_populates="messages", lazy="joined",
    )

    __table_args__ = (
        Index("ix_conversation_messages_thread_id", "thread_id"),
        Index("ix_conversation_messages_message_uuid", "message_uuid"),
        Index("ix_conversation_messages_role", "role"),
        Index("ix_conversation_messages_created_at", "created_at"),
    )


# =============================================================================
#  TABEL AI MEMORY, RECOMMENDATIONS, NOTIFICATIONS
# =============================================================================


class AIMemory(Base):
    """Memori jangka panjang AI tentang user dan pet."""

    __tablename__ = "ai_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True,
    )
    pet_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("pets.id"), nullable=True,
    )
    memory_type: Mapped[str] = mapped_column(
        String(60), nullable=False,
        comment="jenis memori: preference | fact | observation | reminder | behavior",
    )
    key: Mapped[str] = mapped_column(
        String(120), nullable=False,
        comment="kunci unik untuk lookup cepat",
    )
    value: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="nilai/isi memori",
    )
    value_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True,
        comment="nilai terstruktur jika memori berupa data kompleks",
    )
    source: Mapped[Optional[str]] = mapped_column(
        String(120), comment="sumber memori: explicit_feedback | conversation_inference | observation",
    )
    source_consultation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("consultations.id"), nullable=True,
    )
    confidence: Mapped[float] = mapped_column(
        Float, default=1.0,
        comment="keyakinan AI akan kebenaran memori ini 0.0 - 1.0",
    )
    importance: Mapped[float] = mapped_column(
        Float, default=0.5,
        comment="skor pentingnya memori ini 0.0 - 1.0 (untuk prioritasi retrieval)",
    )
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    ttl: Mapped[Optional[int]] = mapped_column(
        Integer, comment="time-to-live dalam detik; NULL = permanent",
    )
    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="waktu kedaluwarsa; dihitung dari created_at + ttl",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
    )

    # Relationships
    user: Mapped[Optional[User]] = relationship(
        "User", back_populates="ai_memories", lazy="joined",
    )
    pet: Mapped[Optional[Pet]] = relationship(
        "Pet", back_populates="ai_memories", lazy="joined",
    )

    __table_args__ = (
        Index("ix_ai_memory_user_id", "user_id"),
        Index("ix_ai_memory_pet_id", "pet_id"),
        Index("ix_ai_memory_memory_type", "memory_type"),
        Index("ix_ai_memory_key", "key"),
        Index("ix_ai_memory_is_active", "is_active"),
        UniqueConstraint("user_id", "pet_id", "memory_type", "key", name="uq_ai_memory_key"),
    )


class Recommendation(Base):
    """Rekomendasi personalisasi untuk pet/owner."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pets.id"), nullable=False,
    )
    type: Mapped[str] = mapped_column(
        String(60), nullable=False,
        comment="jenis rekomendasi: vaccine_reminder | checkup_reminder | product | treatment | diet | article",
    )
    item_id: Mapped[Optional[str]] = mapped_column(
        String(80), comment="ID item yang direkomendasikan (product_id, article_id, dll)",
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    reason: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="alasan rekomendasi ini diberikan",
    )
    reason_code: Mapped[Optional[str]] = mapped_column(
        String(80), comment="kode alasan untuk filtering: breed_risk | age_related | season",
    )
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True,
        comment="detail tambahan rekomendasi",
    )
    score: Mapped[float] = mapped_column(
        Float, default=0.5,
        comment="skor relevansi 0.0 - 1.0",
    )
    scheduled_for: Mapped[Optional[date]] = mapped_column(
        Date, comment="tanggal rekomendasi seharusnya ditampilkan",
    )
    valid_until: Mapped[Optional[date]] = mapped_column(
        Date, comment="tanggal kedaluwarsa rekomendasi",
    )
    clicked: Mapped[bool] = mapped_column(Boolean, default=False)
    clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    action_taken: Mapped[Optional[str]] = mapped_column(
        String(80), comment="aksi yang diambil user: booked | purchased | ignored",
    )
    consultation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("consultations.id"), nullable=True,
    )
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
    )

    # Relationships
    pet: Mapped[Pet] = relationship(
        "Pet", back_populates="recommendations", lazy="joined",
    )

    __table_args__ = (
        Index("ix_recommendations_pet_id", "pet_id"),
        Index("ix_recommendations_type", "type"),
        Index("ix_recommendations_is_active", "is_active"),
        Index("ix_recommendations_scheduled_for", "scheduled_for"),
    )


class Notification(Base):
    """Notifikasi untuk user (email, push, in-app)."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False,
    )
    pet_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("pets.id"), nullable=True,
    )
    type: Mapped[str] = mapped_column(
        String(60), nullable=False,
        comment="jenis notifikasi: vaccine_reminder | appointment | consultation_result | system | marketing",
    )
    channel: Mapped[str] = mapped_column(
        String(40), nullable=False, default="in_app",
        comment="in_app | email | push | sms | whatsapp",
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    template_id: Mapped[Optional[str]] = mapped_column(
        String(80), comment="ID template notifikasi",
    )
    data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True,
        comment="data untuk deep linking / action buttons",
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(40), nullable=False, default="pending",
        comment="pending | scheduled | sent | delivered | read | clicked | failed",
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    consultation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("consultations.id"), nullable=True,
    )
    recommendation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("recommendations.id"), nullable=True,
    )
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
    )

    # Relationships
    user: Mapped[User] = relationship(
        "User", back_populates="notifications", lazy="joined",
    )
    pet: Mapped[Optional[Pet]] = relationship(
        "Pet", back_populates="notifications", lazy="joined",
    )

    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_pet_id", "pet_id"),
        Index("ix_notifications_type", "type"),
        Index("ix_notifications_status", "status"),
        Index("ix_notifications_scheduled_at", "scheduled_at"),
    )


class AuditLog(Base):
    """Log audit untuk semua aksi penting di sistem."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4,
    )
    event_type: Mapped[str] = mapped_column(
        String(80), nullable=False,
        comment="jenis event: user_created | pet_updated | emr_viewed | consultation_started | data_exported | login",
    )
    event_category: Mapped[Optional[str]] = mapped_column(
        String(60), comment="kategori: auth | data | emr | consultation | admin | system",
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True,
    )
    pet_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("pets.id"), nullable=True,
    )
    consultation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("consultations.id"), nullable=True,
    )
    actor_role: Mapped[Optional[str]] = mapped_column(
        String(60), comment="role actor yang melakukan aksi",
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(60))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    action: Mapped[str] = mapped_column(
        String(80), nullable=False,
        comment="aksi: create | read | update | delete | login | logout | export",
    )
    resource_type: Mapped[Optional[str]] = mapped_column(
        String(80), comment="tipe resource: user | pet | emr | consultation | settings",
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(80), comment="ID resource yang diakses",
    )
    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True,
        comment="nilai sebelum perubahan (untuk update/delete)",
    )
    new_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True,
        comment="nilai setelah perubahan (untuk create/update)",
    )
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True,
        comment="metadata tambahan: query params, request body (yang sensitif di-hash)",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, comment="deskripsi human-readable event",
    )
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="info",
        comment="debug | info | warning | error | critical",
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
    )

    # Relationships
    user: Mapped[Optional[User]] = relationship(
        "User", back_populates="audit_logs", lazy="joined",
    )
    pet: Mapped[Optional[Pet]] = relationship(
        "Pet", back_populates="audit_logs", lazy="joined",
    )

    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_pet_id", "pet_id"),
        Index("ix_audit_logs_consultation_id", "consultation_id"),
        Index("ix_audit_logs_event_type", "event_type"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_severity", "severity"),
    )
