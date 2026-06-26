"""EMR Service layer untuk operasi database.

Wrapper SQLAlchemy untuk CRUD operations pada tabel EMR.

Python 3.9 compatible: menggunakan Optional[...] bukan X | None.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timezone
from typing import Any, Dict, Generator, List, Optional, Sequence, Tuple, TypeVar

from sqlalchemy import create_engine, delete, desc, select, update
from sqlalchemy.orm import Session, sessionmaker

from ..config import DATABASE_URL
from .models import (
    Base,
    EMRRecord,
    Medication,
    Pet,
    PetProfile,
    User,
    Vaccination,
)

# Type var untuk generic operations
T = TypeVar("T")


class EMRService:
    """Service untuk operasi database EMR."""

    def __init__(self, database_url: Optional[str] = None):
        url = database_url or DATABASE_URL
        self.engine = create_engine(
            url, pool_pre_ping=True, connect_args={"connect_timeout": 5},
        )
        self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Dapatkan session database dengan context manager."""
        session = self._SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_tables(self) -> None:
        """Buat semua tabel (untuk development/testing)."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """Hapus semua tabel (hanya untuk testing!)."""
        Base.metadata.drop_all(bind=self.engine)

    # =========================================================================
    #  USER OPERATIONS
    # =========================================================================

    def get_user(self, session: Session, user_id: int) -> Optional[User]:
        return session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    def get_user_by_email(self, session: Session, email: str) -> Optional[User]:
        return session.execute(select(User).where(User.email == email)).scalar_one_or_none()

    def create_user(self, session: Session, **kwargs: Any) -> User:
        user = User(**kwargs)
        session.add(user)
        session.flush()
        return user

    def update_user(self, session: Session, user_id: int, **kwargs: Any) -> Optional[User]:
        user = self.get_user(session, user_id)
        if user:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(user, key, value)
            session.flush()
        return user

    # =========================================================================
    #  PET OPERATIONS
    # =========================================================================

    def get_pet(self, session: Session, pet_id: int) -> Optional[Pet]:
        """Dapatkan pet beserta profilnya."""
        return session.execute(
            select(Pet).where(Pet.id == pet_id, Pet.deleted_at.is_(None))
        ).scalar_one_or_none()

    def list_pets_by_user(
        self, session: Session, user_id: int, limit: int = 100, offset: int = 0,
    ) -> Tuple[Sequence[Pet], int]:
        """List pets milik user beserta total count."""
        query = select(Pet).where(
            Pet.user_id == user_id, Pet.deleted_at.is_(None),
        ).order_by(desc(Pet.updated_at))

        count_query = select(Pet.id).where(
            Pet.user_id == user_id, Pet.deleted_at.is_(None),
        )

        total = len(session.execute(count_query).all())
        pets = session.execute(query.offset(offset).limit(limit)).scalars().all()
        return pets, total

    def create_pet(self, session: Session, **kwargs: Any) -> Pet:
        pet = Pet(**kwargs)
        session.add(pet)
        session.flush()
        return pet

    def update_pet(self, session: Session, pet_id: int, **kwargs: Any) -> Optional[Pet]:
        pet = self.get_pet(session, pet_id)
        if pet:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(pet, key, value)
            session.flush()
        return pet

    def delete_pet(self, session: Session, pet_id: int) -> bool:
        """Soft delete pet."""
        result = session.execute(
            update(Pet)
            .where(Pet.id == pet_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )
        return result.rowcount > 0

    # =========================================================================
    #  PET PROFILE OPERATIONS
    # =========================================================================

    def get_pet_profile(self, session: Session, pet_id: int) -> Optional[PetProfile]:
        return session.execute(
            select(PetProfile).where(PetProfile.pet_id == pet_id)
        ).scalar_one_or_none()

    def create_pet_profile(self, session: Session, **kwargs: Any) -> PetProfile:
        profile = PetProfile(**kwargs)
        session.add(profile)
        session.flush()
        return profile

    def update_pet_profile(
        self, session: Session, pet_id: int, **kwargs: Any,
    ) -> Optional[PetProfile]:
        profile = self.get_pet_profile(session, pet_id)
        if profile:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(profile, key, value)
            session.flush()
        return profile

    # =========================================================================
    #  EMR RECORD OPERATIONS
    # =========================================================================

    def get_emr_record(self, session: Session, record_id: int) -> Optional[EMRRecord]:
        return session.execute(
            select(EMRRecord).where(
                EMRRecord.id == record_id, EMRRecord.deleted_at.is_(None),
            )
        ).scalar_one_or_none()

    def list_emr_by_pet(
        self, session: Session, pet_id: int, limit: int = 50, offset: int = 0,
    ) -> Tuple[Sequence[EMRRecord], int]:
        """List rekam medis untuk pet tertentu (terurut tanggal terbaru)."""
        query = select(EMRRecord).where(
            EMRRecord.pet_id == pet_id, EMRRecord.deleted_at.is_(None),
        ).order_by(desc(EMRRecord.visit_date))

        count_query = select(EMRRecord.id).where(
            EMRRecord.pet_id == pet_id, EMRRecord.deleted_at.is_(None),
        )

        total = len(session.execute(count_query).all())
        records = session.execute(query.offset(offset).limit(limit)).scalars().all()
        return records, total

    def create_emr_record(self, session: Session, **kwargs: Any) -> EMRRecord:
        record = EMRRecord(**kwargs)
        session.add(record)
        session.flush()
        return record

    def update_emr_record(
        self, session: Session, record_id: int, **kwargs: Any,
    ) -> Optional[EMRRecord]:
        record = self.get_emr_record(session, record_id)
        if record:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(record, key, value)
            session.flush()
        return record

    def delete_emr_record(self, session: Session, record_id: int) -> bool:
        """Soft delete EMR record."""
        result = session.execute(
            update(EMRRecord)
            .where(EMRRecord.id == record_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )
        return result.rowcount > 0

    # =========================================================================
    #  VACCINATION OPERATIONS
    # =========================================================================

    def get_vaccination(self, session: Session, vac_id: int) -> Optional[Vaccination]:
        return session.execute(
            select(Vaccination).where(Vaccination.id == vac_id)
        ).scalar_one_or_none()

    def list_vaccinations_by_pet(
        self, session: Session, pet_id: int, limit: int = 50, offset: int = 0,
    ) -> Tuple[Sequence[Vaccination], int]:
        """List vaksinasi untuk pet tertentu."""
        query = select(Vaccination).where(
            Vaccination.pet_id == pet_id,
        ).order_by(desc(Vaccination.date_administered))

        count_query = select(Vaccination.id).where(Vaccination.pet_id == pet_id)

        total = len(session.execute(count_query).all())
        vaccinations = session.execute(query.offset(offset).limit(limit)).scalars().all()
        return vaccinations, total

    def create_vaccination(self, session: Session, **kwargs: Any) -> Vaccination:
        vac = Vaccination(**kwargs)
        session.add(vac)
        session.flush()
        return vac

    def update_vaccination(
        self, session: Session, vac_id: int, **kwargs: Any,
    ) -> Optional[Vaccination]:
        vac = self.get_vaccination(session, vac_id)
        if vac:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(vac, key, value)
            session.flush()
        return vac

    # =========================================================================
    #  MEDICATION OPERATIONS
    # =========================================================================

    def get_medication(self, session: Session, med_id: int) -> Optional[Medication]:
        return session.execute(
            select(Medication).where(Medication.id == med_id)
        ).scalar_one_or_none()

    def list_medications_by_pet(
        self, session: Session, pet_id: int, active_only: bool = True,
        limit: int = 50, offset: int = 0,
    ) -> Tuple[Sequence[Medication], int]:
        """List obat untuk pet tertentu."""
        conditions: List[Any] = [Medication.pet_id == pet_id]
        if active_only:
            conditions.append(Medication.is_active == True)  # noqa: E712

        query = select(Medication).where(*conditions).order_by(
            desc(Medication.start_date),
        )

        count_query = select(Medication.id).where(*conditions)

        total = len(session.execute(count_query).all())
        medications = session.execute(query.offset(offset).limit(limit)).scalars().all()
        return medications, total

    def create_medication(self, session: Session, **kwargs: Any) -> Medication:
        med = Medication(**kwargs)
        session.add(med)
        session.flush()
        return med

    def update_medication(
        self, session: Session, med_id: int, **kwargs: Any,
    ) -> Optional[Medication]:
        med = self.get_medication(session, med_id)
        if med:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(med, key, value)
            session.flush()
        return med


# Singleton instance untuk penggunaan umum
_emr_service: Optional[EMRService] = None


def get_emr_service() -> EMRService:
    """Dapatkan singleton instance EMRService."""
    global _emr_service
    if _emr_service is None:
        _emr_service = EMRService()
    return _emr_service
