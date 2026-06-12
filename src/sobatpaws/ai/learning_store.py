"""Learning store — menyimpan jejak konsultasi & input dokter ke backend.

Tujuan strategis: setiap interaksi (keluhan, observasi media, saran AI, dan
TERUTAMA input/koreksi dokter) menjadi "bahan pembelajaran tambahan" untuk
retraining model — menutup loop human-in-the-loop sesuai skema DBML
(clinical_cases, case_symptoms, case_diagnoses, ml_feedback, ai_suggestions).

Backend penyimpanan:
- Default: JSONL append-only di `artifacts/learning/*.jsonl` (tanpa setup DB).
- Opsional: PostgreSQL via DATABASE_URL (di-hook, tidak wajib).

Setiap baris event punya: id, consultation_id, kind, timestamp, payload.
Fungsi `export_clinical_rows()` mengubah input dokter terkonfirmasi menjadi
baris siap-latih yang kompatibel dengan `ml.dataset_builder.merge_clinical_cases`.
"""
from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from ..config import ARTIFACTS_DIR, LEARNING_BACKEND
from .learning_store_pg import PostgresLearningBackend
from .schemas import (
    AISuggestion,
    ConsultationContext,
    DoctorInput,
    IntakeResult,
    SuggestionFeedback,
)

logger = logging.getLogger("sobatpaws.ai.store")

LEARNING_DIR = ARTIFACTS_DIR / "learning"

# nama file per jenis event
FILES = {
    "consultation": "consultations.jsonl",
    "intake": "intake_events.jsonl",
    "suggestion": "suggestions.jsonl",
    "doctor_input": "doctor_inputs.jsonl",
    "feedback": "feedback.jsonl",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LearningStore:
    """Penyimpanan append-only thread-safe untuk bahan pembelajaran.

    Backend: jsonl (default) | postgres | both (dual-write).
    """

    def __init__(self, base_dir: Path | None = None, backend: str | None = None):
        self.base_dir = base_dir or LEARNING_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.backend = (backend or LEARNING_BACKEND).lower()
        self._pg: PostgresLearningBackend | None = None
        if self.backend in ("postgres", "both", "pg"):
            self._pg = PostgresLearningBackend()

    @property
    def pg_available(self) -> bool:
        return self._pg is not None and self._pg.available

    def _use_jsonl(self) -> bool:
        return self.backend in ("jsonl", "both", "file", "")

    def _use_pg(self) -> bool:
        return self.backend in ("postgres", "both", "pg") and self.pg_available

    def _append(self, kind: str, record: dict[str, Any]) -> dict[str, Any]:
        record.setdefault("id", uuid.uuid4().hex)
        record.setdefault("kind", kind)
        record.setdefault("recorded_at", _now_iso())
        with self._lock:
            if self._use_jsonl():
                path = self.base_dir / FILES.get(kind, f"{kind}.jsonl")
                line = json.dumps(record, ensure_ascii=False, default=str)
                with path.open("a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
            if self._use_pg() and self._pg:
                try:
                    self._pg.append(kind, record)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("PG append gagal (%s): %s", kind, exc)
        return record

    # ---- pencatatan event -------------------------------------------------
    def record_consultation_start(
        self, consultation_id: str, context: ConsultationContext
    ) -> dict:
        return self._append("consultation", {
            "consultation_id": consultation_id,
            "event": "start",
            "context": context.model_dump(),
        })

    def record_intake(self, consultation_id: str, intake: IntakeResult) -> dict:
        return self._append("intake", {
            "consultation_id": consultation_id,
            "complaint_text": intake.complaint_text,
            "channel": intake.channel.value,
            "symptoms": [s.model_dump() for s in intake.symptoms],
            "observations": [o.model_dump() for o in intake.observations],
        })

    def record_suggestion(
        self, consultation_id: str, suggestion: AISuggestion
    ) -> dict:
        return self._append("suggestion", {
            "consultation_id": consultation_id,
            "suggestion": suggestion.model_dump(),
        })

    def record_doctor_input(self, doctor_input: DoctorInput) -> dict:
        """Input dokter = label emas. Inilah inti bahan pembelajaran."""
        return self._append("doctor_input", doctor_input.model_dump())

    def record_feedback(self, feedback: SuggestionFeedback) -> dict:
        return self._append("feedback", feedback.model_dump())

    # ---- pembacaan / ekspor untuk retraining ------------------------------
    def _read(self, kind: str) -> list[dict]:
        rows: list[dict] = []
        if self._use_pg() and self._pg:
            try:
                rows = self._pg.read(kind)
            except Exception as exc:  # noqa: BLE001
                logger.warning("PG read gagal (%s): %s", kind, exc)
        if rows:
            return rows
        if not self._use_jsonl():
            return []
        path = self.base_dir / FILES.get(kind, f"{kind}.jsonl")
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return rows

    def sync_jsonl_to_postgres(self) -> dict[str, int]:
        """Migrasi semua event JSONL ke PostgreSQL (idempotent via ON CONFLICT DO NOTHING)."""
        if not self._pg or not self._pg.available:
            raise RuntimeError("PostgreSQL learning backend tidak tersedia.")
        counts: dict[str, int] = {}
        for kind in FILES:
            n = 0
            for rec in self._read_jsonl_only(kind):
                self._pg.append(kind, rec)
                n += 1
            counts[kind] = n
        return counts

    def _read_jsonl_only(self, kind: str) -> list[dict]:
        path = self.base_dir / FILES.get(kind, f"{kind}.jsonl")
        if not path.exists():
            return []
        rows = []
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return rows

    def export_clinical_rows(self) -> list[dict]:
        """Ubah input dokter terkonfirmasi -> baris siap-latih (gold labels).

        Format kompatibel dengan ml.dataset_builder.merge_clinical_cases:
        {symptoms: [name_id], disease_slug, category_slug, ...}
        """
        # peta consultation_id -> category & gejala dari event intake/konteks
        consult_ctx = {
            r["consultation_id"]: r.get("context", {})
            for r in self._read("consultation")
        }
        consult_intake: dict[str, list[str]] = {}
        for r in self._read("intake"):
            cid = r["consultation_id"]
            consult_intake.setdefault(cid, [])
            consult_intake[cid].extend(
                s.get("name_id") for s in r.get("symptoms", []) if s.get("name_id")
            )

        rows: list[dict] = []
        for di in self._read("doctor_input"):
            disease = di.get("confirmed_disease_slug")
            if not disease:
                continue  # hanya diagnosa terkonfirmasi yang jadi label emas
            cid = di.get("consultation_id")
            ctx = consult_ctx.get(cid, {})
            category = ctx.get("category_slug")
            # gejala: utamakan yang dikonfirmasi dokter, fallback hasil intake
            symptoms = di.get("confirmed_symptoms") or consult_intake.get(cid, [])
            symptoms = sorted(set(s for s in symptoms if s))
            if not symptoms:
                continue
            rows.append({
                "symptoms": symptoms,
                "disease_slug": disease,
                "category_slug": category,
                "source": "doctor_confirmed",
                "consultation_id": cid,
                "vet_id": di.get("vet_id") or ctx.get("vet_id") or ctx.get("user_id"),
                "owner_id": di.get("owner_id") or ctx.get("owner_id") or ctx.get("customer_id"),
                "customer_id": di.get("customer_id") or ctx.get("customer_id") or ctx.get("owner_id"),
                "pet_id": di.get("pet_id") or ctx.get("pet_id"),
                "org_id": di.get("org_id") or ctx.get("org_id"),
                "case_id": di.get("case_id") or ctx.get("case_id"),
                "external_consultation_id": (
                    di.get("external_consultation_id") or ctx.get("external_consultation_id")
                ),
            })
        return rows

    def stats(self) -> dict[str, int]:
        if self._use_pg() and self._pg:
            try:
                pg_stats = self._pg.stats()
                if pg_stats:
                    return pg_stats
            except Exception:  # noqa: BLE001
                pass
        return {kind: len(self._read_jsonl_only(kind)) for kind in FILES}

    def backend_info(self) -> dict[str, Any]:
        return {
            "mode": self.backend,
            "jsonl_dir": str(self.base_dir),
            "postgres_available": self.pg_available,
        }


# singleton praktis
_default_store: LearningStore | None = None


def get_store() -> LearningStore:
    global _default_store
    if _default_store is None:
        _default_store = LearningStore()
    return _default_store


def export_for_retraining(store: LearningStore | None = None) -> list[dict]:
    """Helper agar bisa dirangkai ke pipeline retraining ML."""
    return (store or get_store()).export_clinical_rows()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Learning store utilities")
    parser.add_argument("--sync-db", action="store_true",
                        help="Migrasi JSONL -> PostgreSQL")
    args = parser.parse_args()

    s = get_store()
    if args.sync_db:
        counts = s.sync_jsonl_to_postgres()
        print("Sync ke PostgreSQL:", counts)
    else:
        print("Backend:", s.backend_info())
        print("Stats:", s.stats())
        rows = export_for_retraining(s)
        print(f"Baris siap-latih (gold) dari input dokter: {len(rows)}")
