"""FastAPI service Sobatpaws — endpoint AI untuk aplikasi dokter hewan.

Alur integrasi aplikasi:
- Aplikasi menangkap input user dari tools: mikrofon (audio), kamera (gambar),
  atau ketikan (text). Kirim ke endpoint di bawah (base64 untuk media).
- Backend memproses (transkrip/vision + ekstraksi gejala), menjalankan AI,
  mengembalikan saran terstruktur untuk ditampilkan ke dokter.
- Setiap input dokter & feedback disimpan sebagai bahan pembelajaran.

Jalankan:
    uvicorn sobatpaws.api.main:app --reload
Dokumentasi interaktif: http://localhost:8000/docs
"""
from __future__ import annotations

import base64
import re
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .admin_router import router as admin_router
from .agent_router import router as agent_router
from .auth import require_admin, require_vet
from .deps import ai_status, db_status, get_agent, get_service, ml_status
from .integration_router import router as integration_router
from .platform_router import router as platform_router
from ..ai.llm import LLMClient
from ..ai.schemas import (
    AISuggestion,
    ConsultationChannel,
    ConsultationContext,
    DoctorInput,
    IntakeModality,
    IntakePayload,
    IntakeResult,
    MediaPayload,
    SuggestionFeedback,
)
from ..ai.symptom_extractor import SymptomExtractor
from ..ai.telemetry import get_telemetry
from ..integration.identity import resolve_consultation_id

app = FastAPI(
    title="Sobatpaws Veterinary ML & AI API",
    version="0.3.0",
    description=(
        "Sumber data + ML + AI wrapping untuk dukungan vets, klinik & petshop. "
        "Mencakup data master, prediksi ML, konsultasi multimodal, dan learning loop."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_WEB_DIR = Path(__file__).resolve().parents[3] / "web"

app.include_router(integration_router)
app.include_router(platform_router)
app.include_router(admin_router)
app.include_router(agent_router)


# =============================================================================
#  MODEL REQUEST/RESPONSE
# =============================================================================

class StartConsultationRequest(BaseModel):
    context: ConsultationContext
    intake: IntakePayload
    consultation_id: str | None = Field(
        default=None,
        description=(
            "ID sesi dari app Sobatpaws utama (opsional). "
            "Bila kosong, server generate UUID atau pakai external_consultation_id."
        ),
    )


class TurnRequest(BaseModel):
    intake: IntakePayload


class ConsultationResponse(BaseModel):
    consultation_id: str
    intake: IntakeResult
    suggestion: AISuggestion
    suggestion_id: str | None = None
    suggestion_ref: str | None = None
    entities: dict | None = Field(
        default=None,
        description="Bundle ID entitas Sobatpaws (vet, pelanggan, pet, case, ...)",
    )


class AckResponse(BaseModel):
    status: str
    record_id: str | None = None


# =============================================================================
#  HEALTH & INFO
# =============================================================================

@app.get("/health")
def health() -> dict:
    svc = get_service()
    return {
        "status": "ok",
        "llm_available": LLMClient().available,
        "knowledge_base": svc.kb.stats(),
        "learning_store": svc.store.stats(),
    }


# =============================================================================
#  KONSULTASI — CHAT / VIDEO / TEXT
# =============================================================================

@app.post("/consultations", response_model=ConsultationResponse, dependencies=[Depends(require_vet)])
def start_consultation(req: StartConsultationRequest) -> ConsultationResponse:
    """Mulai konsultasi: proses keluhan pertama (text/audio/image) -> saran AI."""
    out = get_agent().start(req.context, req.intake, consultation_id=req.consultation_id)
    return ConsultationResponse(
        consultation_id=out["consultation_id"],
        intake=out["intake"],
        suggestion=out["suggestion"],
        suggestion_id=out.get("suggestion_id"),
        suggestion_ref=out.get("suggestion_ref"),
        entities=out.get("entities"),
    )


@app.get("/consultations/{consultation_id}", dependencies=[Depends(require_vet)])
def get_consultation(consultation_id: str) -> dict:
    """Detail sesi: gejala kumulatif, riwayat saran & pesan agent."""
    cid = resolve_consultation_id(consultation_id) or consultation_id
    detail = get_agent().get_session_detail(cid)
    if not detail:
        raise HTTPException(404, "Konsultasi tidak ditemukan.")
    return detail


def _resolve_cid(consultation_id: str) -> str:
    return resolve_consultation_id(consultation_id) or consultation_id


@app.post("/consultations/{consultation_id}/turns", response_model=ConsultationResponse,
          dependencies=[Depends(require_vet)])
def add_turn(consultation_id: str, req: TurnRequest) -> ConsultationResponse:
    """Giliran lanjutan dalam sesi (chat/video) -> saran diperbarui kumulatif."""
    cid = _resolve_cid(consultation_id)
    try:
        out = get_agent().add_turn(cid, req.intake)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ConsultationResponse(
        consultation_id=out["consultation_id"],
        intake=out["intake"],
        suggestion=out["suggestion"],
        suggestion_id=out.get("suggestion_id"),
        suggestion_ref=out.get("suggestion_ref"),
        entities=out.get("entities"),
    )


@app.post("/consultations/{consultation_id}/media", response_model=ConsultationResponse,
          dependencies=[Depends(require_vet)])
async def upload_media(
    consultation_id: str,
    file: UploadFile = File(...),
    modality: IntakeModality = Form(IntakeModality.image),
    channel: ConsultationChannel = Form(ConsultationChannel.video),
) -> ConsultationResponse:
    """Unggah media mentah (mic/kamera) sebagai multipart -> proses & saran.

    Alternatif praktis dari mengirim base64 di JSON; cocok untuk frame kamera
    atau rekaman suara langsung dari aplikasi.
    """
    raw = await file.read()
    b64 = base64.b64encode(raw).decode("ascii")
    payload = IntakePayload(
        channel=channel,
        media=[MediaPayload(
            modality=modality,
            mime_type=file.content_type,
            base64_data=b64,
        )],
    )
    try:
        out = get_agent().add_turn(_resolve_cid(consultation_id), payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ConsultationResponse(
        consultation_id=out["consultation_id"],
        intake=out["intake"],
        suggestion=out["suggestion"],
        suggestion_id=out.get("suggestion_id"),
        suggestion_ref=out.get("suggestion_ref"),
        entities=out.get("entities"),
    )


# =============================================================================
#  INPUT DOKTER & FEEDBACK — BAHAN PEMBELAJARAN
# =============================================================================

@app.post("/consultations/{consultation_id}/doctor-input", response_model=AckResponse,
          dependencies=[Depends(require_vet)])
def record_doctor_input(consultation_id: str, payload: DoctorInput) -> AckResponse:
    """Simpan keputusan dokter (diagnosa/tindakan/resep) sebagai label emas."""
    payload.consultation_id = consultation_id
    rec = get_agent().record_doctor_input(payload)
    return AckResponse(status="stored", record_id=rec.get("agent_id") or rec.get("learning_id"))


@app.post("/consultations/{consultation_id}/feedback", response_model=AckResponse,
          dependencies=[Depends(require_vet)])
def record_feedback(consultation_id: str, payload: SuggestionFeedback) -> AckResponse:
    """Penilaian dokter atas saran AI (human-in-the-loop)."""
    payload.consultation_id = consultation_id
    rec = get_agent().record_feedback(payload)
    return AckResponse(status="stored", record_id=rec.get("agent_id") or rec.get("learning_id"))


@app.get("/learning/export")
def export_learning() -> dict:
    """Ekspor baris siap-latih (gold) dari input dokter untuk retraining ML."""
    svc = get_service()
    rows = svc.store.export_clinical_rows()
    return {
        "count": len(rows),
        "rows": rows,
        "backend": svc.store.backend_info(),
    }


@app.get("/learning/stats")
def learning_stats() -> dict:
    """Statistik event pembelajaran + info backend."""
    svc = get_service()
    return {"stats": svc.store.stats(), "backend": svc.store.backend_info()}


class RetrainRequest(BaseModel):
    category: str | None = Field(
        default=None, description="slug kategori; kosong = semua kategori berdata dokter"
    )
    samples_per_disease: int = 80


@app.post("/learning/retrain", dependencies=[Depends(require_admin)])
def retrain(req: RetrainRequest) -> dict:
    """Eksekusi pembelajaran: latih ulang model dari input dokter (gold rows).

    Menutup loop human-in-the-loop. Mengembalikan ringkasan metrik & jumlah
    kasus dokter yang digabungkan ke dataset latih.
    """
    svc = get_service()
    try:
        from ..ml.retrain import retrain_from_learning_store

        summary = retrain_from_learning_store(
            store=svc.store, category=req.category,
            samples_per_disease=req.samples_per_disease,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Retraining gagal: {exc}") from exc
    return summary


@app.post("/learning/sync-db", dependencies=[Depends(require_admin)])
def sync_learning_to_db() -> dict:
    """Migrasi event JSONL lokal ke PostgreSQL (learning_events). Idempotent."""
    svc = get_service()
    try:
        counts = svc.store.sync_jsonl_to_postgres()
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Sync gagal: {exc}") from exc
    return {"status": "synced", "counts": counts, "backend": svc.store.backend_info()}


@app.post("/learning/sync-models-db", dependencies=[Depends(require_admin)])
def sync_models_db() -> dict:
    """Sinkronkan artefak ML lokal ke tabel PostgreSQL ml_models."""
    try:
        from ..platform.model_registry_pg import sync_models_to_postgres
        result = sync_models_to_postgres()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Sync model gagal: {exc}") from exc
    return result


# =============================================================================
#  STATUS TERPADU (untuk dashboard / monitoring)
# =============================================================================

@app.get("/api/status")
def system_status() -> dict:
    """Status terpadu seluruh komponen (data, AI, ML, DB, token usage)."""
    svc = get_service()
    components = {
        "backend": {"ok": True, "version": app.version, "name": app.title},
        "data": {"ok": True, **svc.kb.stats()},
        "ai": ai_status(),
        "ml": ml_status(),
        "database": db_status(),
        "ai_usage": get_telemetry().summary(limit_recent=5),
    }
    components["all_ok"] = all(
        c.get("ok", False) for k, c in components.items()
        if k not in ("database", "ai_usage")
    )
    return components


# =============================================================================
#  DATA MASTER (knowledge base)
# =============================================================================

@app.get("/categories")
def categories() -> list:
    return get_service().kb.categories


@app.get("/categories/{slug}/breeds")
def breeds(slug: str) -> list:
    items = get_service().kb.breeds_for_category(slug)
    if not items:
        raise HTTPException(404, f"Kategori '{slug}' tidak ditemukan / tanpa ras")
    return items


@app.get("/breeds/{slug}")
def breed_detail(slug: str) -> dict:
    kb = get_service().kb
    b = kb.breed_by_slug(slug)
    if not b:
        raise HTTPException(404, "Ras tidak ditemukan")
    return {"breed": b, "common_diseases": kb.diseases_for_breed(slug)}


@app.get("/diseases/{slug}")
def disease_detail(slug: str) -> dict:
    d = get_service().kb.disease_by_slug(slug)
    if not d:
        raise HTTPException(404, "Penyakit tidak ditemukan")
    return d


@app.get("/api/stats/breakdown")
def stats_breakdown() -> dict:
    """Rincian jumlah data: ras, varian, traits, penyakit + analitik varian."""
    kb = get_service().kb
    rows: list[dict] = []
    total_variants = 0
    total_traits = 0
    breeds_without_variants = 0
    variant_type_counts: dict[str, int] = {}
    all_breed_summaries: list[dict] = []

    for c in kb.categories:
        slug = c["slug"]
        cat_name = c.get("name_id") or c.get("name") or slug
        bs = kb.breeds_for_category(slug)
        cat_variant_types: dict[str, int] = {}
        cat_no_variant = 0
        variant_count = 0
        trait_count = 0

        for b in bs:
            variants = b.get("variants") or []
            traits = b.get("traits") or []
            vcount = len(variants)
            tcount = len(traits)
            variant_count += vcount
            trait_count += tcount
            if vcount == 0:
                cat_no_variant += 1
                breeds_without_variants += 1
            for v in variants:
                vtype = v.get("variant_type") or "other"
                variant_type_counts[vtype] = variant_type_counts.get(vtype, 0) + 1
                cat_variant_types[vtype] = cat_variant_types.get(vtype, 0) + 1
            all_breed_summaries.append({
                "slug": b["slug"],
                "name_id": b.get("name_id") or b.get("name") or b["slug"],
                "category_slug": slug,
                "category_name_id": cat_name,
                "size_class": b.get("size_class"),
                "origin_country": b.get("origin_country"),
                "care_level": b.get("care_level"),
                "variants": vcount,
                "traits": tcount,
                "variant_types": sorted({v.get("variant_type") or "other" for v in variants}),
            })

        total_variants += variant_count
        total_traits += trait_count
        breed_n = len(bs)
        rows.append({
            "slug": slug,
            "name_id": cat_name,
            "name": c.get("name"),
            "species_class": c.get("species_class"),
            "scientific_name": c.get("scientific_name"),
            "breeds": breed_n,
            "variants": variant_count,
            "traits": trait_count,
            "diseases": len(kb.diseases_for_category(slug)),
            "symptoms": len({
                (s.get("name_id") or s.get("name"))
                for d in kb.diseases_for_category(slug)
                for s in d.get("symptoms", [])
                if s.get("name_id") or s.get("name")
            }),
            "breeds_without_variants": cat_no_variant,
            "avg_variants_per_breed": round(variant_count / breed_n, 2) if breed_n else 0,
            "variant_types": cat_variant_types,
        })

    rows.sort(key=lambda r: (r["breeds"], r["variants"]), reverse=True)
    all_breed_summaries.sort(key=lambda b: (b["variants"], b["traits"]), reverse=True)
    total_breeds = len(kb.breeds)

    return {
        "totals": {
            "categories": len(kb.categories),
            "breeds": total_breeds,
            "variants": total_variants,
            "traits": total_traits,
            "diseases": len(kb.diseases),
            "symptoms": len(kb.all_symptoms()),
            "breeds_without_variants": breeds_without_variants,
            "avg_variants_per_breed": round(total_variants / total_breeds, 2) if total_breeds else 0,
        },
        "variant_types": dict(sorted(variant_type_counts.items(), key=lambda x: -x[1])),
        "by_category": rows,
        "top_breeds": all_breed_summaries[:15],
    }


@app.get("/api/stats/breeds")
def stats_breeds(
    category: str | None = None,
    q: str | None = None,
    sort: str = "variants",
    limit: int = 200,
) -> dict:
    """Daftar ras dengan ringkasan varian/traits — untuk pencarian & tabel explorer."""
    kb = get_service().kb
    qnorm = (q or "").strip().lower()
    items: list[dict] = []

    categories = kb.categories
    if category:
        categories = [c for c in categories if c["slug"] == category]

    for c in categories:
        slug = c["slug"]
        cat_name = c.get("name_id") or c.get("name") or slug
        for b in kb.breeds_for_category(slug):
            name_id = b.get("name_id") or b.get("name") or b["slug"]
            haystack = f"{name_id} {b.get('name', '')} {b.get('slug', '')} {cat_name}".lower()
            if qnorm and qnorm not in haystack:
                continue
            variants = b.get("variants") or []
            traits = b.get("traits") or []
            items.append({
                "slug": b["slug"],
                "name_id": name_id,
                "name": b.get("name"),
                "category_slug": slug,
                "category_name_id": cat_name,
                "size_class": b.get("size_class"),
                "origin_country": b.get("origin_country"),
                "care_level": b.get("care_level"),
                "coat_type": b.get("coat_type"),
                "variants": len(variants),
                "traits": len(traits),
                "variant_list": [
                    {
                        "name": v.get("name"),
                        "variant_type": v.get("variant_type") or "other",
                        "hex_color": v.get("hex_color"),
                    }
                    for v in variants
                ],
                "trait_keys": [t.get("trait_key") for t in traits if t.get("trait_key")],
            })

    sort_key = {
        "variants": lambda x: (x["variants"], x["traits"], x["name_id"]),
        "traits": lambda x: (x["traits"], x["variants"], x["name_id"]),
        "name": lambda x: x["name_id"].lower(),
        "category": lambda x: (x["category_name_id"], x["name_id"]),
    }.get(sort, lambda x: (x["variants"], x["name_id"]))

    reverse = sort != "name"
    items.sort(key=sort_key, reverse=reverse)
    if limit > 0:
        items = items[:limit]

    return {"count": len(items), "breeds": items}


@app.get("/api/symptoms")
def symptoms(category: str | None = None) -> list:
    """Daftar gejala unik (opsional difilter per kategori) untuk pilihan UI."""
    extractor = SymptomExtractor(get_service().kb, category_slug=category)
    return [
        {"name_id": e.name_id, "name": e.name, "body_system": e.body_system,
         "is_red_flag": e.is_red_flag}
        for e in extractor._entries  # noqa: SLF001 - akses index internal disengaja
    ]


# =============================================================================
#  CONSULT SINGLE-SHOT & ML PREDICT (tanpa sesi)
# =============================================================================

class ConsultRequest(BaseModel):
    category_slug: str = Field(..., description="slug spesies, mis. 'dog'")
    breed_slug: str | None = None
    age_years: float | None = None
    weight_kg: float | None = None
    sex: str | None = None
    complaint_text: str | None = Field(None, description="keluhan teks bebas owner")
    symptoms: list[str] = Field(default_factory=list,
                                description="name_id gejala terpilih (opsional)")
    top_k: int = 5


@app.post("/api/consult", response_model=AISuggestion, dependencies=[Depends(require_vet)])
def consult(req: ConsultRequest) -> AISuggestion:
    """Saran klinis terstruktur single-shot (RAG: ML + KB + LLM opsional)."""
    svc = get_service()
    extractor = SymptomExtractor(svc.kb, category_slug=req.category_slug)
    extracted: dict = {}
    if req.complaint_text:
        for s in extractor.extract(req.complaint_text):
            extracted[s.name_id] = s
    for s in extractor.merge_known(req.symptoms):
        extracted.setdefault(s.name_id, s)
    intake = IntakeResult(
        complaint_text=req.complaint_text or ", ".join(req.symptoms),
        symptoms=list(extracted.values()),
    )
    context = ConsultationContext(
        category_slug=req.category_slug, breed_slug=req.breed_slug,
        age_years=req.age_years, weight_kg=req.weight_kg, sex=req.sex,
    )
    return svc.engine.suggest(context, intake, top_k=req.top_k)


class PredictRequest(BaseModel):
    category_slug: str
    symptoms: list[str]
    top_k: int = 5


@app.post("/ml/predict")
def ml_predict(req: PredictRequest) -> dict:
    """Prediksi symptom -> disease langsung dari model ML."""
    try:
        from ..ml.predict import predict_diseases

        results = predict_diseases(req.category_slug, req.symptoms, top_k=req.top_k)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Prediksi gagal: {exc}") from exc
    kb = get_service().kb
    for r in results:
        d = kb.disease_by_slug(r["disease_slug"]) or {}
        r["name_id"] = d.get("name_id")
        r["is_emergency"] = bool(d.get("is_emergency", False))
    return {"category_slug": req.category_slug, "predictions": results}


# =============================================================================
#  EXPORT EXCEL (data/generated + learning)
# =============================================================================

_EXCEL_NAME = re.compile(r"^Sobatpaws_\d{2}_[\w]+\.xlsx$")


@app.get("/exports/excel")
def list_excel_exports() -> dict:
    """Daftar file Excel yang tersedia di data/excel/."""
    EXCEL_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    for path in sorted(EXCEL_DIR.glob("Sobatpaws_*.xlsx")):
        files.append({
            "filename": path.name,
            "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
            "url": f"/exports/excel/{path.name}",
        })
    return {"count": len(files), "files": files, "directory": str(EXCEL_DIR)}


@app.get("/exports/excel/{filename}")
def download_excel(filename: str) -> FileResponse:
    """Unduh workbook Excel (hanya Sobatpaws_XX_*.xlsx)."""
    if not _EXCEL_NAME.match(filename):
        raise HTTPException(400, "Nama file tidak valid.")
    path = EXCEL_DIR / filename
    if not path.is_file():
        raise HTTPException(404, f"File '{filename}' tidak ditemukan.")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )


# =============================================================================
#  Frontend statis (opsional) — dipasang terakhir agar tak menutupi route API
# =============================================================================
if _WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_WEB_DIR), html=True), name="web")
