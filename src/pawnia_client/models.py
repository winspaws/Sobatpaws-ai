from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    pet_id: Optional[int] = None

class ChatSuggestion(BaseModel):
    text: str
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None

class ChatResponse(BaseModel):
    suggestion: Optional[ChatSuggestion] = None
    agent: Optional[str] = None
    conversation_id: Optional[str] = None

class PetResponse(BaseModel):
    id: int
    name: str
    species: str
    breed: Optional[str] = None

class EMRRecordResponse(BaseModel):
    id: int
    pet_id: int
    record_type: str
    description: str
