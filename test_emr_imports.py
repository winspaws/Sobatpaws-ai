"""Test imports for EMR module."""
import sys
sys.path.insert(0, 'src')

from ekosistem_satwa.emr import Base, User, Pet, EMRRecord, Vaccination, Medication, Consultation
from ekosistem_satwa.emr import PetProfile, ConversationThread, ConversationMessage
from ekosistem_satwa.emr import AIMemory, Recommendation, Notification, AuditLog
from ekosistem_satwa.emr import EMRService, get_emr_service
from ekosistem_satwa.emr.schemas import (
    PetResponse, EMRRecordResponse, VaccinationResponse, 
    MedicationResponse, ConsultationResponse
)

print('All EMR module imports OK')
print(f'Tables in metadata: {list(Base.metadata.tables.keys())}')
print(f'Total tables: {len(Base.metadata.tables)}')
