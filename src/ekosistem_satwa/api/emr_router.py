"""EMR API Router untuk endpoint rekam medis elektronik.

Endpoint sesuai PRD Part 7 (API Specification & Database Design):
- GET  /api/v1/pets          — List pets
- GET  /api/v1/pets/{id}     — Pet detail
- GET  /api/v1/emr/{petId}   — Medical history
- POST /api/v1/emr/{petId}   — Add EMR record
- GET  /api/v1/vaccinations/{petId} — Vaccination status
- POST /api/v1/vaccinations/{petId} — Add vaccination
"""
from __future__ import annotations

from datetime import date
from typing import Annotated, Dict, Generator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..emr import EMRService, get_emr_service
from ..emr.schemas import (
    EMRListResponse,
    EMRRecordCreate,
    EMRRecordResponse,
    PetResponse,
    VaccinationCreate,
    VaccinationListResponse,
    VaccinationResponse,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["emr"],
    responses={404: {"description": "Not found"}},
)


def get_db_session() -> Generator[Session, None, None]:
    """Dependency untuk mendapatkan database session."""
    svc = get_emr_service()
    with svc.session() as session:
        yield session


DBSession = Annotated[Session, Depends(get_db_session)]
EMRDeps = Annotated[EMRService, Depends(get_emr_service)]


# =============================================================================
#  PETS ENDPOINTS
# =============================================================================


@router.get("/pets", response_model=Dict)
def list_pets(
    db: DBSession,
    svc: EMRDeps,
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> Dict:
    """List semua pets (hewan peliharaan).

    - `user_id`: filter pets milik user tertentu
    - `limit`: jumlah maksimal hasil (default 100)
    - `offset`: pagination offset
    """
    if user_id is None:
        # TODO: Implementasi auth untuk mendapatkan user_id dari token
        raise HTTPException(
            status_code=400,
            detail="user_id parameter is required for now (auth pending)",
        )

    pets, total = svc.list_pets_by_user(db, user_id=user_id, limit=limit, offset=offset)

    pet_responses = [
        PetResponse.model_validate(pet, from_attributes=True)
        for pet in pets
    ]

    return {
        "pets": pet_responses,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/pets/{pet_id}", response_model=PetResponse)
def get_pet_detail(
    pet_id: int,
    db: DBSession,
    svc: EMRDeps,
) -> PetResponse:
    """Dapatkan detail pet beserta profil medisnya."""
    pet = svc.get_pet(db, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail=f"Pet with id {pet_id} not found")

    return PetResponse.model_validate(pet, from_attributes=True)


# =============================================================================
#  EMR (Medical History) ENDPOINTS
# =============================================================================


@router.get("/emr/{pet_id}", response_model=EMRListResponse)
def get_medical_history(
    pet_id: int,
    db: DBSession,
    svc: EMRDeps,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> EMRListResponse:
    """Dapatkan riwayat medis lengkap untuk pet tertentu.

    Mengembalikan semua EMR records terurut dari yang terbaru.
    """
    # Validasi pet exists
    pet = svc.get_pet(db, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail=f"Pet with id {pet_id} not found")

    records, total = svc.list_emr_by_pet(db, pet_id=pet_id, limit=limit, offset=offset)

    record_responses = [
        EMRRecordResponse.model_validate(rec, from_attributes=True)
        for rec in records
    ]

    return EMRListResponse(
        records=record_responses,
        total=total,
        pet_name=pet.name,
    )


@router.post("/emr/{pet_id}", response_model=EMRRecordResponse, status_code=201)
def add_emr_record(
    pet_id: int,
    record: EMRRecordCreate,
    db: DBSession,
    svc: EMRDeps,
) -> EMRRecordResponse:
    """Tambahkan record EMR baru untuk pet.

    Ini mencatat satu kunjungan medis atau episode kesehatan.
    """
    # Validasi pet exists
    pet = svc.get_pet(db, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail=f"Pet with id {pet_id} not found")

    # Pastikan pet_id di body sama dengan path
    data = record.model_dump()
    data["pet_id"] = pet_id

    new_record = svc.create_emr_record(db, **data)
    db.commit()

    return EMRRecordResponse.model_validate(new_record, from_attributes=True)


# =============================================================================
#  VACCINATION ENDPOINTS
# =============================================================================


@router.get("/vaccinations/{pet_id}", response_model=VaccinationListResponse)
def get_vaccination_status(
    pet_id: int,
    db: DBSession,
    svc: EMRDeps,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> VaccinationListResponse:
    """Dapatkan status vaksinasi untuk pet tertentu.

    Mengembalikan riwayat vaksinasi beserta yang akan datang.
    """
    # Validasi pet exists
    pet = svc.get_pet(db, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail=f"Pet with id {pet_id} not found")

    vaccinations, total = svc.list_vaccinations_by_pet(
        db, pet_id=pet_id, limit=limit, offset=offset,
    )

    today = date.today()
    upcoming_count = 0
    overdue_count = 0

    vac_responses: List[VaccinationResponse] = []
    for vac in vaccinations:
        if vac.next_due:
            if vac.next_due < today:
                overdue_count += 1
            elif vac.next_due >= today:
                upcoming_count += 1
        vac_responses.append(
            VaccinationResponse.model_validate(vac, from_attributes=True)
        )

    return VaccinationListResponse(
        vaccinations=vac_responses,
        total=total,
        upcoming_count=upcoming_count,
        overdue_count=overdue_count,
    )


@router.post("/vaccinations/{pet_id}", response_model=VaccinationResponse, status_code=201)
def add_vaccination(
    pet_id: int,
    vaccination: VaccinationCreate,
    db: DBSession,
    svc: EMRDeps,
) -> VaccinationResponse:
    """Catatkan vaksinasi baru untuk pet.

    Digunakan untuk mencatat vaksinasi yang telah diberikan.
    """
    # Validasi pet exists
    pet = svc.get_pet(db, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail=f"Pet with id {pet_id} not found")

    # Pastikan pet_id di body sama dengan path
    data = vaccination.model_dump()
    data["pet_id"] = pet_id

    new_vac = svc.create_vaccination(db, **data)
    db.commit()

    return VaccinationResponse.model_validate(new_vac, from_attributes=True)


# =============================================================================
#  UTILITY: Health check EMR module
# =============================================================================


@router.get("/emr/health", response_model=Dict)
def emr_health_check(
    svc: EMRDeps,
) -> Dict:
    """Health check untuk EMR Service dan koneksi database."""
    try:
        with svc.session() as session:
            from sqlalchemy import text
            session.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "service": "emr",
            "database": "connected",
            "endpoints": [
                "GET  /api/v1/pets",
                "GET  /api/v1/pets/{id}",
                "GET  /api/v1/emr/{petId}",
                "POST /api/v1/emr/{petId}",
                "GET  /api/v1/vaccinations/{petId}",
                "POST /api/v1/vaccinations/{petId}",
            ],
        }
    except Exception as exc:
        return {
            "status": "degraded",
            "service": "emr",
            "database": "disconnected",
            "error": str(exc),
        }
