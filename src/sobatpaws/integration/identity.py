"""Registry identitas entitas Sobatpaws — penghubung ID app utama ↔ sesi ML/AI.

Selaras skema DBML:
  organizations.id  → org_id
  users.id (vet)    → vet_id / user_id / doctor_id
  pet_owners.id     → owner_id / customer_id
  pets.id           → pet_id
  clinical_cases.id → case_id
  (app utama)       → external_consultation_id
  (sesi AI)         → consultation_id
"""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator

from ..config import ARTIFACTS_DIR

REGISTRY_FILE = ARTIFACTS_DIR / "integration" / "entity_registry.jsonl"


class SobatpawsEntityIds(BaseModel):
    """Bundle ID entitas untuk traceability lintas sistem."""

    consultation_id: str | None = Field(
        None, description="ID sesi AI (internal API path param)",
    )
    external_consultation_id: str | None = Field(
        None, description="ID konsultasi/kasus dari app Sobatpaws utama",
    )

    org_id: int | None = Field(None, description="organizations.id — klinik/cabang")
    vet_id: int | None = Field(None, description="users.id — dokter hewan (role vet)")
    doctor_id: int | None = Field(None, description="alias vet_id")
    user_id: int | None = Field(None, description="alias vet_id (legacy field)")

    owner_id: int | None = Field(None, description="pet_owners.id — pemilik hewan")
    customer_id: int | None = Field(None, description="alias owner_id — pelanggan")

    pet_id: int | None = Field(None, description="pets.id")
    case_id: int | None = Field(None, description="clinical_cases.id")

    external_refs: dict[str, str] = Field(
        default_factory=dict,
        description="ID tambahan dari sistem eksternal, mis. {'crm_lead': 'L-99'}",
    )

    @model_validator(mode="after")
    def _sync_aliases(self) -> SobatpawsEntityIds:
        if self.vet_id is None and self.doctor_id is not None:
            self.vet_id = self.doctor_id
        if self.vet_id is None and self.user_id is not None:
            self.vet_id = self.user_id
        if self.doctor_id is None and self.vet_id is not None:
            self.doctor_id = self.vet_id
        if self.user_id is None and self.vet_id is not None:
            self.user_id = self.vet_id

        if self.owner_id is None and self.customer_id is not None:
            self.owner_id = self.customer_id
        if self.customer_id is None and self.owner_id is not None:
            self.customer_id = self.owner_id
        return self

    def to_public_dict(self) -> dict[str, Any]:
        """Dict stabil untuk response API (tanpa duplikasi alias)."""
        return {
            "consultation_id": self.consultation_id,
            "external_consultation_id": self.external_consultation_id,
            "org_id": self.org_id,
            "vet_id": self.vet_id,
            "owner_id": self.owner_id,
            "customer_id": self.customer_id,
            "pet_id": self.pet_id,
            "case_id": self.case_id,
            "external_refs": self.external_refs or {},
        }


def normalize_context(context: Any) -> Any:
    """Sinkronkan alias ID pada ConsultationContext (in-place safe via model_copy)."""
    from ..ai.schemas import ConsultationContext

    if not isinstance(context, ConsultationContext):
        return context
    data = context.model_dump()
    vet = data.get("vet_id") or data.get("doctor_id") or data.get("user_id")
    owner = data.get("owner_id") or data.get("customer_id")
    if vet:
        data["vet_id"] = data["doctor_id"] = data["user_id"] = vet
    if owner:
        data["owner_id"] = data["customer_id"] = owner
    return ConsultationContext(**data)


def entities_from_context(
    context: Any,
    *,
    consultation_id: str | None = None,
) -> SobatpawsEntityIds:
    """Ekstrak bundle entitas dari ConsultationContext."""
    ctx = normalize_context(context)
    ext = ctx.external_consultation_id
    if not ext and ctx.external_refs:
        ext = ctx.external_refs.get("consultation_id") or ctx.external_refs.get(
            "sobatpaws_consultation_id"
        )
    return SobatpawsEntityIds(
        consultation_id=consultation_id,
        external_consultation_id=ext,
        org_id=ctx.org_id,
        vet_id=ctx.vet_id or ctx.user_id,
        doctor_id=ctx.doctor_id or ctx.vet_id or ctx.user_id,
        user_id=ctx.user_id or ctx.vet_id,
        owner_id=ctx.owner_id or ctx.customer_id,
        customer_id=ctx.customer_id or ctx.owner_id,
        pet_id=ctx.pet_id,
        case_id=ctx.case_id,
        external_refs=dict(ctx.external_refs or {}),
    )


class IdentityRegistry:
    """Persist mapping consultation_id ↔ entitas Sobatpaws (JSONL)."""

    def __init__(self, path: Path | None = None):
        self.path = path or REGISTRY_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._by_consultation: dict[str, dict] = {}
        self._by_external: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cid = rec.get("consultation_id")
                if cid:
                    self._by_consultation[cid] = rec
                    ext = rec.get("external_consultation_id")
                    if ext:
                        self._by_external[str(ext)] = cid

    def register(
        self,
        consultation_id: str,
        entities: SobatpawsEntityIds | dict,
        *,
        context_snapshot: dict | None = None,
    ) -> dict[str, Any]:
        if isinstance(entities, SobatpawsEntityIds):
            payload = entities.to_public_dict()
        else:
            payload = dict(entities)
        payload["consultation_id"] = consultation_id
        payload.setdefault("id", uuid.uuid4().hex)
        payload.setdefault("registered_at", datetime.now(timezone.utc).isoformat())
        if context_snapshot:
            payload["context_snapshot"] = context_snapshot

        with self._lock:
            self._by_consultation[consultation_id] = payload
            ext = payload.get("external_consultation_id")
            if ext:
                self._by_external[str(ext)] = consultation_id
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
        return payload

    def get(self, consultation_id: str) -> dict | None:
        return self._by_consultation.get(consultation_id)

    def get_entities(self, consultation_id: str) -> SobatpawsEntityIds | None:
        rec = self.get(consultation_id)
        if not rec:
            return None
        return SobatpawsEntityIds(**{
            k: rec[k] for k in SobatpawsEntityIds.model_fields if k in rec
        })

    def resolve_external(self, external_id: str) -> str | None:
        return self._by_external.get(str(external_id))

    def list_by_filter(
        self,
        *,
        vet_id: int | None = None,
        owner_id: int | None = None,
        customer_id: int | None = None,
        pet_id: int | None = None,
        org_id: int | None = None,
        limit: int = 50,
    ) -> list[dict]:
        owner_id = owner_id or customer_id
        rows = list(self._by_consultation.values())
        rows.sort(key=lambda r: r.get("registered_at", ""), reverse=True)
        out: list[dict] = []
        for r in rows:
            if vet_id is not None and r.get("vet_id") != vet_id:
                continue
            if owner_id is not None and r.get("owner_id") != owner_id:
                continue
            if pet_id is not None and r.get("pet_id") != pet_id:
                continue
            if org_id is not None and r.get("org_id") != org_id:
                continue
            out.append(r)
            if len(out) >= limit:
                break
        return out


_registry: IdentityRegistry | None = None


def get_identity_registry() -> IdentityRegistry:
    global _registry
    if _registry is None:
        _registry = IdentityRegistry()
    return _registry


def resolve_consultation_id(
    consultation_id: str | None = None,
    external_consultation_id: str | None = None,
) -> str | None:
    """Resolve path param: terima internal ID atau external ID app utama."""
    reg = get_identity_registry()
    if consultation_id:
        if reg.get(consultation_id):
            return consultation_id
        mapped = reg.resolve_external(consultation_id)
        if mapped:
            return mapped
        return consultation_id
    if external_consultation_id:
        return reg.resolve_external(external_consultation_id)
    return None


def new_consultation_id(
    preferred_id: str | None = None,
    external_id: str | None = None,
) -> str:
    """Tentukan ID sesi: pakai ID app utama bila diberikan, else UUID."""
    if preferred_id:
        return str(preferred_id)
    if external_id:
        return str(external_id)
    return uuid.uuid4().hex
