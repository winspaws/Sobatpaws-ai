"""Integration Router — Endpoints khusus untuk integrasi dengan sobatpaws-admin panel.

Endpoint ini menyediakan jembatan antara admin panel PetPro dengan
Ekosistem Satwa AI Services + EMR.

Semua endpoint menggunakan JWT auth (compatible dengan admin panel cookie-based auth).
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from .auth import require_jwt_or_apikey
from ..ai.pawnia_orchestrator import PawniaOrchestrator, get_pawnia
from ..emr.service import EMRService, get_emr_service

logger = logging.getLogger("ekosistem_satwa.api.integration")

router = APIRouter(
    prefix="/api/v1/integration",
    tags=["Integration - Admin Panel"],
)


# =============================================================================
# 1. AI PRE-SCREENING — untuk appointment booking
# =============================================================================


@router.post("/appointment/screening")
def appointment_ai_screening(
    species: str = Query(..., description="Species: dog, cat, rabbit, etc."),
    breed: str | None = Query(None, description="Breed slug"),
    age_years: float | None = Query(None, ge=0, le=50, description="Age in years"),
    symptoms: str = Query(..., description="Comma-separated symptoms"),
    duration_days: int | None = Query(None, ge=0, le=365, description="Duration of symptoms"),
    auth: dict = Depends(require_jwt_or_apikey),
    pawnia: PawniaOrchestrator = Depends(lambda: get_pawnia()),
) -> dict:
    """AI Pre-Screening untuk appointment booking.

    Sebelum customer booking appointment, admin panel bisa panggil endpoint ini
    untuk mendapatkan risk assessment dari Pawnia.

    **Example:**
    ```
    POST /api/v1/integration/appointment/screening
        ?species=cat&breed=cat-persian&age_years=3
        &symptoms=muntah,lemas,tidak mau makan&duration_days=2
    ```

    **Response:**
    ```json
    {
        "success": true,
        "data": {
            "risk_level": "high",
            "risk_score": 65,
            "suggested_specialist": "dokter_hewan_umum",
            "urgency": "within_24h",
            "ai_summary": "...",
            "disclaimer": "..."
        }
    }
    ```
    """
    if not symptoms.strip():
        raise HTTPException(400, "Symptoms cannot be empty")

    # Build message for Pawnia
    message = f"Gejala pada {species}"
    if breed:
        message += f" ({breed})"
    if age_years:
        message += f", usia {age_years} tahun"
    message += f": {symptoms}"
    if duration_days:
        message += f" (sudah {duration_days} hari)"

    try:
        result = pawnia.process(text=message)

        # Map risk level to urgency
        urgency_map = {
            "critical": "immediate",
            "high": "within_24h",
            "medium": "within_week",
            "low": "routine",
        }

        return {
            "success": True,
            "data": {
                "risk_level": result.risk_level,
                "risk_score": result.risk_score,
                "agent": str(result.agent),
                "confidence": result.confidence,
                "suggested_specialist": _map_agent_to_specialist(str(result.agent)),
                "urgency": urgency_map.get(result.risk_level, "routine"),
                "ai_summary": result.response.get("text", ""),
                "escalated": result.escalated,
                "suggestions": result.response.get("suggestions", []),
                "cta": result.response.get("cta", []),
                "disclaimer": result.response.get("disclaimer", ""),
            },
        }
    except Exception as exc:
        logger.error("AI screening error: %s", exc, exc_info=True)
        return {
            "success": False,
            "error": "AI screening temporarily unavailable",
            "data": {
                "risk_level": "unknown",
                "risk_score": 0,
                "urgency": "routine",
                "ai_summary": None,
            },
        }


def _map_agent_to_specialist(agent: str) -> str:
    """Map Pawnia agent type to specialist recommendation."""
    mapping = {
        "triage_emergency": "dokter_gawat_darurat",
        "vet_escalation": "dokter_hewan_umum",
        "vision_screening": "dokter_kulit_hewan",
        "behavior_insight": "dokter_perilaku_hewan",
        "nutrition_advisor": "dokter_gizi_hewan",
        "medication_adherence": "dokter_hewan_umum",
        "pet_companion": "dokter_hewan_umum",
    }
    return mapping.get(agent, "dokter_hewan_umum")


# =============================================================================
# 2. PET MEDICAL HISTORY — untuk customer detail
# =============================================================================


@router.get("/customer/{external_id}/medical-history")
def customer_medical_history(
    external_id: str,
    pet_id: str | None = Query(None, description="Filter by pet external ID"),
    auth: dict = Depends(require_jwt_or_apikey),
    emr: EMRService = Depends(lambda: get_emr_service()),
) -> dict:
    """Get medical history for all pets of a customer.

    **Example:**
    ```
    GET /api/v1/integration/customer/ext-123/medical-history
    ```

    **Response:**
    ```json
    {
        "success": true,
        "data": {
            "pets": [{
                "external_id": "...",
                "name": "Milo",
                "species": "cat",
                "breed": "Persian",
                "vaccinations": [...],
                "active_medications": [...],
                "recent_consultations": [...],
                "chronic_conditions": []
            }]
        }
    }
    ```
    """
    try:
        with emr.session() as session:
            user = emr.get_user(session, int(external_id)) if external_id.isdigit() else None
            if not user:
                return {"success": True, "data": {"pets": []}}

            pets = emr.list_pets_by_user(session, user_id=user.id)

            result = []
            for pet in pets:
                if pet_id and pet.external_id != pet_id:
                    continue

                pet_data = {
                    "external_id": pet.external_id or str(pet.id),
                    "name": pet.name,
                    "species": pet.species,
                    "breed": pet.breed or "",
                    "photo_url": pet.photo_url,
                    "age_years": _calc_age(pet.dob) if pet.dob else None,
                    "weight_kg": pet.weight_kg,
                    "neutered": pet.neutered,
                    "sex": pet.sex or "",
                    "color": "",  # TODO: add color field to Pet model
                }

                # Get vaccinations
                try:
                    vax, _ = emr.list_vaccinations_by_pet(session, pet_id=pet.id)
                    pet_data["vaccinations"] = [
                        {
                            "type": v.vaccine_type,
                            "date": str(v.date_administered),
                            "next_due": str(v.next_due) if v.next_due else None,
                            "clinic": v.clinic_name or "",
                        }
                        for v in vax
                    ]
                except Exception:
                    pet_data["vaccinations"] = []

                # Get active medications
                try:
                    meds, _ = emr.list_medications_by_pet(session, pet_id=pet.id)
                    pet_data["active_medications"] = [
                        {
                            "name": m.medication_name,
                            "dosage": m.dosage,
                            "frequency": m.frequency,
                            "start_date": str(m.start_date),
                            "end_date": str(m.end_date) if m.end_date else None,
                            "prescribing_vet": m.prescribing_vet or "",
                        }
                        for m in meds
                    ]
                except Exception:
                    pet_data["active_medications"] = []

                # Recent consultations - via Consultation model if available
                pet_data["recent_consultations"] = []

                # Get chronic conditions from profile
                try:
                    profile = emr.get_pet_profile(session, pet_id=pet.id)
                    pet_data["chronic_conditions"] = (
                        profile.chronic_conditions if profile and profile.chronic_conditions else []
                    )
                    pet_data["allergies"] = (
                        profile.allergies if profile and profile.allergies else []
                    )
                except Exception:
                    pet_data["chronic_conditions"] = []
                    pet_data["allergies"] = []

                result.append(pet_data)

            return {"success": True, "data": {"pets": result}}

    except Exception as exc:
        logger.error("Medical history error: %s", exc, exc_info=True)
        return {"success": False, "error": str(exc)}


def _calc_age(dob) -> float | None:
    """Calculate age in years from date of birth."""
    from datetime import date
    today = date.today()
    if hasattr(dob, 'year'):
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return None


# =============================================================================
# 3. PRODUCT RECOMMENDATION — AI-powered product suggestions
# =============================================================================


@router.post("/product/recommend")
def product_recommendation(
    species: str = Query(..., description="Species"),
    breed: str | None = Query(None, description="Breed"),
    age_years: float | None = Query(None, description="Age"),
    condition: str = Query(..., description="Health condition or symptoms"),
    auth: dict = Depends(require_jwt_or_apikey),
    pawnia: PawniaOrchestrator = Depends(lambda: get_pawnia()),
) -> dict:
    """Get AI-powered product recommendations based on pet condition.

    **Example:**
    ```
    POST /api/v1/integration/product/recommend
        ?species=dog&breed=dog-golden&age_years=5
        &condition=obesitas,susah bergerak
    ```
    """
    message = f"Rekomendasi produk untuk {species}"
    if breed:
        message += f" ({breed})"
    if age_years:
        message += f", {age_years} tahun"
    message += f" dengan kondisi: {condition}"

    try:
        result = pawnia.process(text=message)
        return {
            "success": True,
            "data": {
                "recommendations": result.response.get("suggestions", []),
                "summary": result.response.get("text", ""),
                "disclaimer": result.response.get("disclaimer", ""),
            },
        }
    except Exception as exc:
        logger.error("Product recommendation error: %s", exc, exc_info=True)
        return {"success": False, "error": str(exc)}


# =============================================================================
# 4. HEALTH CHECK — untuk admin panel monitoring
# =============================================================================


@router.get("/health")
def integration_health() -> dict:
    """Health check endpoint khusus untuk admin panel."""
    return {
        "success": True,
        "data": {
            "service": "Ekosistem Satwa Integration API",
            "version": "1.0.0",
            "status": "ok",
            "endpoints": [
                "POST /api/v1/integration/appointment/screening",
                "GET /api/v1/integration/customer/{external_id}/medical-history",
                "POST /api/v1/integration/product/recommend",
                "GET /api/v1/integration/health",
            ],
        },
    }
