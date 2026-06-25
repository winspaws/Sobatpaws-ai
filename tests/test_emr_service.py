"""Unit tests untuk EMR Service module.

Menggunakan SQLite in-memory database untuk testing.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from ekosistem_satwa.emr import Base
from ekosistem_satwa.emr.models import (
    AIMemory,
    AuditLog,
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
from ekosistem_satwa.emr.service import EMRService


@pytest.fixture
def emr_service() -> Generator[EMRService, None, None]:
    """Fixture untuk EMRService dengan SQLite in-memory."""
    service = EMRService(database_url="sqlite:///:memory:")
    service.create_tables()
    yield service
    service.drop_tables()


class TestEMRModels:
    """Test untuk model SQLAlchemy."""

    def test_create_user(self, emr_service: EMRService) -> None:
        """Test membuat user."""
        with emr_service.session() as session:
            user = User(
                name="Test User",
                email="test@example.com",
                phone="08123456789",
                role="pet_owner",
            )
            session.add(user)
            session.flush()

            assert user.id is not None
            assert user.name == "Test User"
            assert user.email == "test@example.com"
            assert user.is_active == True

    def test_create_pet_with_profile(self, emr_service: EMRService) -> None:
        """Test membuat pet dengan profile."""
        with emr_service.session() as session:
            user = User(name="Owner", email="owner@example.com")
            session.add(user)
            session.flush()

            pet = Pet(
                user_id=user.id,
                name="Buddy",
                species="dog",
                breed="Golden Retriever",
                sex="male",
                neutered=True,
            )
            session.add(pet)
            session.flush()

            profile = PetProfile(
                pet_id=pet.id,
                microchip="982000123456789",
                allergies=["chicken", "beef"],
                chronic_conditions=["hip dysplasia"],
            )
            session.add(profile)
            session.flush()

            assert pet.id is not None
            assert pet.name == "Buddy"
            assert pet.owner == user
            assert pet.profile == profile
            assert profile.microchip == "982000123456789"

    def test_create_emr_record(self, emr_service: EMRService) -> None:
        """Test membuat EMR record."""
        with emr_service.session() as session:
            user = User(name="Owner", email="owner@example.com")
            session.add(user)
            session.flush()

            pet = Pet(user_id=user.id, name="Buddy", species="dog")
            session.add(pet)
            session.flush()

            emr = EMRRecord(
                pet_id=pet.id,
                visit_type="checkup",
                chief_complaint="Coughing for 3 days",
                diagnosis="Kennel cough",
                symptoms=["Cough", "Lethargy"],
                vet_name="Dr. Smith",
                clinic_name="Happy Paws Clinic",
            )
            session.add(emr)
            session.flush()

            assert emr.id is not None
            assert emr.pet == pet
            assert emr.diagnosis == "Kennel cough"

    def test_create_vaccination(self, emr_service: EMRService) -> None:
        """Test membuat vaccination record."""
        with emr_service.session() as session:
            user = User(name="Owner", email="owner@example.com")
            session.add(user)
            session.flush()

            pet = Pet(user_id=user.id, name="Buddy", species="dog")
            session.add(pet)
            session.flush()

            vac = Vaccination(
                pet_id=pet.id,
                vaccine_type="Rabies",
                vaccine_brand="Nobivac",
                date_administered=date(2024, 1, 15),
                next_due=date(2025, 1, 15),
                batch_number="RAB-2024-001",
                vet_name="Dr. Smith",
            )
            session.add(vac)
            session.flush()

            assert vac.id is not None
            assert vac.pet == pet
            assert vac.vaccine_type == "Rabies"
            assert vac.date_administered == date(2024, 1, 15)

    def test_create_medication(self, emr_service: EMRService) -> None:
        """Test membuat medication record."""
        with emr_service.session() as session:
            user = User(name="Owner", email="owner@example.com")
            session.add(user)
            session.flush()

            pet = Pet(user_id=user.id, name="Buddy", species="dog")
            session.add(pet)
            session.flush()

            med = Medication(
                pet_id=pet.id,
                medication_name="Amoxicillin",
                generic_name="Amoxicillin trihydrate",
                category="antibiotic",
                dosage="250mg",
                frequency="BID (twice daily)",
                frequency_hours=12,
                route="oral",
                start_date=date(2024, 1, 20),
                end_date=date(2024, 1, 30),
                duration_days=10,
                instructions="Give with food",
                is_active=True,
            )
            session.add(med)
            session.flush()

            assert med.id is not None
            assert med.pet == pet
            assert med.medication_name == "Amoxicillin"
            assert med.is_active == True

    def test_create_consultation(self, emr_service: EMRService) -> None:
        """Test membuat consultation record."""
        with emr_service.session() as session:
            user = User(name="Owner", email="owner@example.com")
            session.add(user)
            session.flush()

            pet = Pet(user_id=user.id, name="Buddy", species="dog")
            session.add(pet)
            session.flush()

            consult = Consultation(
                pet_id=pet.id,
                user_id=user.id,
                status="completed",
                agent_used="llm_augmented",
                model_used="gpt-4o",
                confidence=0.85,
                risk_score=0.3,
                risk_level="low",
                chief_complaint="Dog is scratching ears",
                symptoms_reported=["Scratching", "Redness in ears"],
                summary="Suggesting ear infection, recommend vet visit for confirmation.",
                red_flags=[],
                safety_warnings=["Do not use human ear drops without vet guidance"],
            )
            session.add(consult)
            session.flush()

            assert consult.id is not None
            assert consult.consultation_uuid is not None
            assert consult.pet == pet
            assert consult.user == user
            assert consult.risk_level == "low"

    def test_create_conversation_thread_with_messages(
        self, emr_service: EMRService,
    ) -> None:
        """Test membuat conversation thread dan messages."""
        with emr_service.session() as session:
            user = User(name="Owner", email="owner@example.com")
            session.add(user)
            session.flush()

            pet = Pet(user_id=user.id, name="Buddy", species="dog")
            session.add(pet)
            session.flush()

            thread = ConversationThread(
                user_id=user.id,
                pet_id=pet.id,
                title="Ear infection concern",
                channel="chat",
                status="closed",
                message_count=2,
            )
            session.add(thread)
            session.flush()

            msg1 = ConversationMessage(
                thread_id=thread.id,
                role="user",
                content="My dog is scratching his ears a lot. What should I do?",
                turn_number=1,
            )
            msg2 = ConversationMessage(
                thread_id=thread.id,
                role="assistant",
                content="I understand your concern. Ear scratching can indicate ear mites, infection, or allergies. I recommend having a vet examine the ears for proper diagnosis.",
                agent="gpt-4o",
                turn_number=1,
                tokens_used=150,
                latency_ms=2300,
            )
            session.add_all([msg1, msg2])
            session.flush()

            assert thread.id is not None
            assert len(thread.messages) == 2
            assert msg1.role == "user"
            assert msg2.role == "assistant"

    def test_create_ai_memory(self, emr_service: EMRService) -> None:
        """Test membuat AI memory record."""
        with emr_service.session() as session:
            user = User(name="Owner", email="owner@example.com")
            session.add(user)
            session.flush()

            pet = Pet(user_id=user.id, name="Buddy", species="dog")
            session.add(pet)
            session.flush()

            memory = AIMemory(
                user_id=user.id,
                pet_id=pet.id,
                memory_type="fact",
                key="allergic_to_chicken",
                value="Buddy shows skin reactions when eating chicken-based food",
                source="conversation_inference",
                confidence=0.9,
                importance=0.8,
                is_active=True,
            )
            session.add(memory)
            session.flush()

            assert memory.id is not None
            assert memory.key == "allergic_to_chicken"
            assert memory.memory_type == "fact"

    def test_create_recommendation(self, emr_service: EMRService) -> None:
        """Test membuat recommendation record."""
        with emr_service.session() as session:
            user = User(name="Owner", email="owner@example.com")
            session.add(user)
            session.flush()

            pet = Pet(user_id=user.id, name="Buddy", species="dog")
            session.add(pet)
            session.flush()

            rec = Recommendation(
                pet_id=pet.id,
                type="vaccine_reminder",
                title="Rabies booster due soon",
                reason="Rabies vaccination is due in 2 weeks",
                reason_code="upcoming_vaccine",
                score=0.9,
                scheduled_for=date(2024, 2, 1),
                is_active=True,
            )
            session.add(rec)
            session.flush()

            assert rec.id is not None
            assert rec.type == "vaccine_reminder"
            assert rec.score == 0.9

    def test_create_notification(self, emr_service: EMRService) -> None:
        """Test membuat notification record."""
        with emr_service.session() as session:
            user = User(name="Owner", email="owner@example.com")
            session.add(user)
            session.flush()

            pet = Pet(user_id=user.id, name="Buddy", species="dog")
            session.add(pet)
            session.flush()

            notif = Notification(
                user_id=user.id,
                pet_id=pet.id,
                type="vaccine_reminder",
                channel="push",
                title="Rabies Vaccine Due Soon",
                body="Buddy's rabies vaccine is due in 2 weeks. Please schedule an appointment.",
                status="pending",
            )
            session.add(notif)
            session.flush()

            assert notif.id is not None
            assert notif.type == "vaccine_reminder"
            assert notif.status == "pending"

    def test_create_audit_log(self, emr_service: EMRService) -> None:
        """Test membuat audit log record."""
        with emr_service.session() as session:
            user = User(name="Owner", email="owner@example.com")
            session.add(user)
            session.flush()

            pet = Pet(user_id=user.id, name="Buddy", species="dog")
            session.add(pet)
            session.flush()

            audit = AuditLog(
                event_type="emr_viewed",
                event_category="emr",
                user_id=user.id,
                pet_id=pet.id,
                actor_role="pet_owner",
                ip_address="192.168.1.1",
                action="read",
                resource_type="emr",
                resource_id=str(pet.id),
                description="User viewed EMR records for pet",
                severity="info",
                success=True,
            )
            session.add(audit)
            session.flush()

            assert audit.id is not None
            assert audit.event_uuid is not None
            assert audit.event_type == "emr_viewed"
            assert audit.severity == "info"


class TestEMRService:
    """Test untuk EMRService layer."""

    def test_get_user(self, emr_service: EMRService) -> None:
        """Test get_user service method."""
        with emr_service.session() as session:
            created = emr_service.create_user(
                session, name="Test User", email="test@test.com",
            )
            session.flush()

            retrieved = emr_service.get_user(session, created.id)
            assert retrieved is not None
            assert retrieved.id == created.id
            assert retrieved.email == "test@test.com"

            not_found = emr_service.get_user(session, 999999)
            assert not_found is None

    def test_get_user_by_email(self, emr_service: EMRService) -> None:
        """Test get_user_by_email service method."""
        with emr_service.session() as session:
            emr_service.create_user(
                session, name="Test User", email="unique@test.com",
            )
            session.flush()

            retrieved = emr_service.get_user_by_email(session, "unique@test.com")
            assert retrieved is not None
            assert retrieved.name == "Test User"

    def test_list_pets_by_user(self, emr_service: EMRService) -> None:
        """Test list_pets_by_user service method."""
        with emr_service.session() as session:
            user = emr_service.create_user(session, name="Owner", email="owner@test.com")
            session.flush()

            # Create 3 pets for this user
            for i in range(3):
                emr_service.create_pet(
                    session,
                    user_id=user.id,
                    name=f"Pet {i}",
                    species="dog",
                )
            session.flush()

            # Create a pet for different user
            other_user = emr_service.create_user(session, name="Other", email="other@test.com")
            session.flush()
            emr_service.create_pet(
                session,
                user_id=other_user.id,
                name="Other Pet",
                species="cat",
            )
            session.flush()

            pets, total = emr_service.list_pets_by_user(session, user_id=user.id)
            assert total == 3
            assert len(pets) == 3
            assert all(p.user_id == user.id for p in pets)

    def test_pet_crud_operations(self, emr_service: EMRService) -> None:
        """Test CRUD operations for Pet."""
        with emr_service.session() as session:
            user = emr_service.create_user(session, name="Owner", email="owner@test.com")
            session.flush()

            # Create
            pet = emr_service.create_pet(
                session,
                user_id=user.id,
                name="Buddy",
                species="dog",
                breed="Labrador",
            )
            session.flush()
            pet_id = pet.id

            # Read
            retrieved = emr_service.get_pet(session, pet_id)
            assert retrieved is not None
            assert retrieved.name == "Buddy"

            # Update
            updated = emr_service.update_pet(session, pet_id, name="Buddy Updated")
            assert updated is not None
            assert updated.name == "Buddy Updated"

            # Soft delete
            result = emr_service.delete_pet(session, pet_id)
            assert result == True

            # Should not find after delete
            deleted = emr_service.get_pet(session, pet_id)
            assert deleted is None

    def test_emr_record_crud(self, emr_service: EMRService) -> None:
        """Test CRUD for EMRRecord."""
        from datetime import date, datetime, timezone

        with emr_service.session() as session:
            user = emr_service.create_user(session, name="Owner", email="owner@test.com")
            session.flush()
            pet = emr_service.create_pet(
                session, user_id=user.id, name="Buddy", species="dog",
            )
            session.flush()

            # Create
            record = emr_service.create_emr_record(
                session,
                pet_id=pet.id,
                visit_date=datetime.now(timezone.utc),
                chief_complaint="Test complaint",
                diagnosis="Test diagnosis",
                status="completed",
            )
            session.flush()
            record_id = record.id

            # List
            records, total = emr_service.list_emr_by_pet(session, pet_id=pet.id)
            assert total == 1
            assert len(records) == 1

            # Read
            retrieved = emr_service.get_emr_record(session, record_id)
            assert retrieved is not None
            assert retrieved.chief_complaint == "Test complaint"

            # Update
            updated = emr_service.update_emr_record(
                session, record_id, notes="Updated notes",
            )
            assert updated is not None
            assert updated.notes == "Updated notes"

            # Delete
            result = emr_service.delete_emr_record(session, record_id)
            assert result == True

            deleted = emr_service.get_emr_record(session, record_id)
            assert deleted is None

    def test_vaccination_crud(self, emr_service: EMRService) -> None:
        """Test CRUD for Vaccination."""
        from datetime import date

        with emr_service.session() as session:
            user = emr_service.create_user(session, name="Owner", email="owner@test.com")
            session.flush()
            pet = emr_service.create_pet(
                session, user_id=user.id, name="Buddy", species="dog",
            )
            session.flush()

            # Create
            vac = emr_service.create_vaccination(
                session,
                pet_id=pet.id,
                vaccine_type="Rabies",
                date_administered=date(2024, 1, 15),
                next_due=date(2025, 1, 15),
            )
            session.flush()
            vac_id = vac.id

            # List
            vaccinations, total = emr_service.list_vaccinations_by_pet(
                session, pet_id=pet.id,
            )
            assert total == 1
            assert len(vaccinations) == 1

            # Read
            retrieved = emr_service.get_vaccination(session, vac_id)
            assert retrieved is not None
            assert retrieved.vaccine_type == "Rabies"

            # Update
            updated = emr_service.update_vaccination(
                session, vac_id, notes="Booster shot",
            )
            assert updated is not None
            assert updated.notes == "Booster shot"

    def test_medication_list(self, emr_service: EMRService) -> None:
        """Test medication listing with active_only filter."""
        from datetime import date

        with emr_service.session() as session:
            user = emr_service.create_user(session, name="Owner", email="owner@test.com")
            session.flush()
            pet = emr_service.create_pet(
                session, user_id=user.id, name="Buddy", species="dog",
            )
            session.flush()

            # Create active medication
            emr_service.create_medication(
                session,
                pet_id=pet.id,
                medication_name="Active Med",
                dosage="10mg",
                frequency="daily",
                start_date=date(2024, 1, 1),
                is_active=True,
            )
            session.flush()

            # Create inactive medication
            emr_service.create_medication(
                session,
                pet_id=pet.id,
                medication_name="Inactive Med",
                dosage="5mg",
                frequency="daily",
                start_date=date(2023, 1, 1),
                is_active=False,
            )
            session.flush()

            # List active only (default)
            active, total = emr_service.list_medications_by_pet(session, pet_id=pet.id)
            assert total == 1
            assert len(active) == 1
            assert active[0].medication_name == "Active Med"

            # List all
            all_meds, total_all = emr_service.list_medications_by_pet(
                session, pet_id=pet.id, active_only=False,
            )
            assert total_all == 2
            assert len(all_meds) == 2
