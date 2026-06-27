"""
Admin Dashboard API Router — AI monitoring, KB stats, testing playground
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import json, os, glob, random, datetime

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Dashboard"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get('DATA_DIR', '/app/data')

# =============================================================================
# 1. OVERALL STATS
# =============================================================================
@router.get("/stats")
def get_overall_stats():
    """Ringkasan statistik sistem."""
    # KB stats
    kb_stats = {"total_species": 0, "total_diseases": 0, "total_breeds": 177, "total_symptoms": 207}
    clinical_dir = os.path.join(DATA_DIR, 'clinical')
    if os.path.exists(clinical_dir):
        species_list = []
        total_d = 0
        for f in glob.glob(os.path.join(clinical_dir, 'diseases_*.json')):
            try:
                data = json.load(open(f))
                species = data.get("category_slug", "?")
                count = len(data.get('diseases', []))
                species_list.append({"slug": species, "disease_count": count})
                total_d += count
            except: pass
        kb_stats["species_list"] = species_list
        kb_stats["total_diseases"] = total_d
        kb_stats["total_species"] = len(species_list)
    
    return {
        "status": "ok",
        "timestamp": datetime.datetime.now().isoformat(),
        "knowledge_base": kb_stats,
        "agents": [
            {"name": "pet_companion", "status": "active", "type": "companion"},
            {"name": "triage_emergency", "status": "active", "type": "emergency"},
            {"name": "vet_escalation", "status": "active", "type": "escalation"},
            {"name": "vision_screening", "status": "active", "type": "vision"},
            {"name": "behavior_insight", "status": "active", "type": "behavior"},
            {"name": "behavior_fun", "status": "active", "type": "entertainment"},
            {"name": "nutrition_advisor", "status": "active", "type": "nutrition"},
            {"name": "meal_planner", "status": "active", "type": "meal"},
            {"name": "medication_adherence", "status": "active", "type": "medication"},
        ]
    }

# =============================================================================
# 2. AI METRICS
# =============================================================================
@router.get("/ai/metrics")
def get_ai_metrics():
    """AI performance metrics (simulasi dari data real-time)."""
    now = datetime.datetime.now()
    hours = [ (now - datetime.timedelta(hours=i)).strftime("%H:00") for i in range(23, -1, -1) ]
    
    # Simulasi request volume (nanti bisa dari Prometheus)
    request_volume = [random.randint(5, 50) for _ in range(24)]
    token_usage = [random.randint(1000, 15000) for _ in range(24)]
    error_rate = [round(random.uniform(0, 5), 1) for _ in range(24)]
    
    return {
        "request_volume": {"labels": hours, "data": request_volume},
        "token_usage": {"labels": hours, "data": token_usage},
        "error_rate": {"labels": hours, "data": error_rate},
        "current_rpm": sum(request_volume[-5:]) // 5,
        "total_tokens_today": sum(token_usage),
        "avg_response_ms": round(random.uniform(200, 800), 1),
        "uptime_hours": 5,
    }

# =============================================================================
# 3. KNOWLEDGE BASE MANAGEMENT
# =============================================================================
@router.get("/kb/diseases")
def list_diseases(species: Optional[str] = None, search: Optional[str] = None, limit: int = Query(50, le=200)):
    """List diseases dengan filter species dan search."""
    clinical_dir = os.path.join(DATA_DIR, 'clinical')
    results = []
    for f in glob.glob(os.path.join(clinical_dir, 'diseases_*.json')):
        try:
            data = json.load(open(f))
            cat_slug = data.get("category_slug", "")
            if species and species != cat_slug:
                continue
            for d in data.get('diseases', []):
                if search and search.lower() not in d.get('name','').lower() and search.lower() not in d.get('name_id','').lower():
                    continue
                results.append({
                    "slug": d["slug"],
                    "name": d.get("name", ""),
                    "name_id": d.get("name_id", ""),
                    "species": cat_slug,
                    "severity": d.get("default_severity", ""),
                    "emergency": d.get("is_emergency", False),
                    "contagious": d.get("is_contagious", False),
                    "body_system": d.get("body_system", ""),
                    "etiology": d.get("etiology", ""),
                })
        except: pass
    results.sort(key=lambda x: x["name"])
    return {"total": len(results), "diseases": results[:limit]}

# =============================================================================
# 4. LEARNING LOOP
# =============================================================================
@router.get("/learning/stats")
def get_learning_stats():
    """Learning loop feedback statistics."""
    return {
        "total_feedback": 0,
        "feedback_by_verdict": {"correct": 0, "incorrect": 0, "partial": 0},
        "last_retrain": None,
        "pending_feedback": 0,
        "accuracy_trend": [],
    }

# =============================================================================
# 5. TESTING PLAYGROUND
# =============================================================================
class ChatTestRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    pet_id: Optional[int] = None
    agent: Optional[str] = None
    include_context: bool = False

@router.post("/testing/chat")
def test_chat(req: ChatTestRequest):
    """Testing endpoint — proxy ke AI Gateway untuk testing."""
    from ekosistem_satwa.api.ai_gateway_router import PawniaProcessor
    processor = PawniaProcessor()
    result = processor.process(
        text=req.message,
        session_id=req.session_id or "test-session",
        pet_id=req.pet_id,
    )
    return {
        "request": req.dict(),
        "response": {
            "agent": result.get("agent", ""),
            "risk_level": result.get("risk_level", ""),
            "risk_score": result.get("risk_score", 0),
            "text": result.get("text", ""),
            "suggestions": result.get("suggestions", []),
        },
        "processing_time_ms": 0,
    }
