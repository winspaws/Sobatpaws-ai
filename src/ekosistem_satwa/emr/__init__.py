"""EMR Service module untuk rekam medis elektronik hewan."""
from .models import (
    AIMemory,
    AuditLog,
    Base,
    Consultation,
    ConversationMessage,
    ConversationThread,
    EMRRecord,
    Medication,
    Notification,
    Pet,
    PetProfile,
    Recommendation,
    User,
    Vaccination,
)
from .service import EMRService, get_emr_service

__all__ = [
    "Base",
    "User",
    "Pet",
    "PetProfile",
    "EMRRecord",
    "Vaccination",
    "Medication",
    "Consultation",
    "ConversationThread",
    "ConversationMessage",
    "AIMemory",
    "Recommendation",
    "Notification",
    "AuditLog",
    "EMRService",
    "get_emr_service",
]
