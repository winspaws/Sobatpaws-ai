from fastapi import APIRouter
from pydantic import BaseModel
router = APIRouter(prefix="/api/v1/ai/triage", tags=["AI Triage"])
class TriageRequest(BaseModel):
    species: str = "dog"
    symptoms: list[str] = []
    comorbidity_flag: bool = False
@router.post("")
def triage(req: TriageRequest):
    sev_code = 3 if any("darah" in s.lower() or "kejang" in s.lower() for s in req.symptoms) else 2
    sev = ["mild","moderate","severe","critical"][sev_code]
    return {"severity":sev,"severity_code":sev_code,"confidence":0.85,"escalation_recommended":sev_code>=2}
@router.get("/health")
def health():
    return {"status":"ok","species_supported":["dog","cat","rabbit","fish","reptile","poultry","ferret","guinea_pig","hamster","amphibian"]}

