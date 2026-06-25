# HANDOFF.md - Multi-Agent Orchestrator API Contract

**Status**: Proposed | ADR-003  
**Owner**: Naincode AI Dept  
**Last Updated**: 2026

---

## Overview

This document specifies the API contract for implementing the Multi-Agent Orchestrator
and Structured Vision Output as defined in [ADR-003](../docs/adr/ADR-003-multi-agent-vision.md).

---

## 1. New Data Structures (schemas.py)

### 1.1 Structured Vision Output

```python
from dataclasses import dataclass, field
from typing import Any
from pydantic import BaseModel, Field


class AgeEstimate(BaseModel):
    """Age estimation with confidence range."""
    min: float = Field(..., description="Minimum estimated age in years")
    max: float = Field(..., description="Maximum estimated age in years")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")


class LesionObservation(BaseModel):
    """Structured observation of a single lesion or abnormality."""
    location: str = Field(..., description="Anatomical location, e.g., 'left ear pinna'")
    type: str = Field(..., description="Lesion type from clinical vocabulary, e.g., 'erythema'")
    severity: str = Field(..., description="mild | moderate | severe")
    description: str = Field(default="", description="Detailed clinical description")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class StructuredVisionOutput(BaseModel):
    """
    Structured output from vision analysis.
    
    This is the new return type for vision analysis, replacing the unstructured str.
    The raw_description field is preserved for audit and fallback purposes.
    """
    species_detected: str | None = Field(
        default=None,
        description="Primary species: dog | cat | rabbit | ferret | bird | etc"
    )
    breed_hints: list[str] = Field(
        default_factory=list,
        description="Top matching breed slugs from knowledge base, e.g., ['dog-golden-retriever']"
    )
    age_estimate: AgeEstimate | None = Field(default=None)
    lesions: list[LesionObservation] = Field(default_factory=list)
    red_flags: list[str] = Field(
        default_factory=list,
        description="Emergency signs requiring immediate attention"
    )
    raw_description: str = Field(
        default="",
        description="Original LLM text output for audit trail"
    )
    extracted_symptoms: list[str] = Field(
        default_factory=list,
        description="Symptom name_ids matched to KB vocabulary"
    )
    model_used: str | None = Field(default=None)
    processing_time_ms: int | None = Field(default=None)
```

### 1.2 Agent Input/Output Types

```python
class ClarificationNeed(BaseModel):
    """Identified information gap requiring owner clarification."""
    field: str = Field(..., description="What needs clarification: symptom | timeline | history | etc")
    reason: str = Field(..., description="Why clarification is needed")
    ambiguity_score: float = Field(..., ge=0.0, le=1.0)
    suggested_questions: list[str] = Field(
        default_factory=list,
        description="Pre-composed questions to ask owner"
    )


class ClarificationTurn(BaseModel):
    """Record of one clarification exchange."""
    question: str
    answer: str
    extracted_symptoms: list[str] = Field(default_factory=list)
    resolved_fields: list[str] = Field(default_factory=list)


class VetSummary(BaseModel):
    """
    Structured summary optimized for veterinary clinical workflow.
    
    Designed for quick scanning by busy veterinarians.
    The 'structured' field can be used directly for UI population.
    """
    patient_overview: str = Field(
        default="",
        description="1-2 sentence executive summary"
    )
    timeline_summary: str = Field(
        default="",
        description="Chronological progression of signs"
    )
    key_clinical_findings: list[str] = Field(
        default_factory=list,
        description="Bullet points for quick scan"
    )
    visual_findings_summary: str = Field(
        default="",
        description="Synthesis of all vision outputs"
    )
    owner_concerns: list[str] = Field(
        default_factory=list,
        description="Owner-reported concerns in their own words"
    )
    red_flags: list[str] = Field(
        default_factory=list,
        description="Consolidated emergency signs from all inputs"
    )
    suggested_focus_areas: list[str] = Field(
        default_factory=list,
        description="What the vet should prioritize in examination"
    )
    structured: dict[str, Any] = Field(
        default_factory=dict,
        description="Machine-readable data for UI population: species, breed_guess, age_range, etc."
    )


class OrchestratorResult(BaseModel):
    """Combined output from orchestrator for a consultation turn."""
    consultation_id: str
    intake_result: IntakeResult
    vet_summary: VetSummary
    ai_suggestion: AISuggestion
    vision_outputs: list[StructuredVisionOutput]
    
    # Clarification state
    clarification_needed: bool = False
    next_question: str | None = None
    clarification_history: list[ClarificationTurn] = Field(default_factory=list)
    
    # Metadata
    processing_time_ms: int = 0
    agents_used: list[str] = Field(default_factory=list)  # ["vision", "clarifier", "summarizer"]
```

### 1.3 Updated Existing Types

```python
# Update to MediaObservation in schemas.py
class MediaObservation(BaseModel):
    """Hasil pemrosesan satu media (transkrip audio / deskripsi gambar)."""
    modality: IntakeModality
    text: str = Field(description="transkrip atau deskripsi temuan")
    source: str = Field(description="provider/metode, mis. speech_to_text, vision, client")
    confidence: float | None = None
    
    # NEW: optional structured data for vision modality
    structured: StructuredVisionOutput | None = Field(
        default=None,
        description="Structured vision output (if modality is image/video_frame)"
    )
```

---

## 2. LLMClient Interface Updates (llm.py)

### New Method: describe_image_structured

```python
class LLMClient:
    # ... existing methods ...
    
    def describe_image_structured(
        self,
        image_bytes: bytes,
        mime_type: str | None = None,
        *,
        context: ConsultationContext | None = None,
        **kwargs,
    ) -> StructuredVisionOutput | None:
        """
        Analyze an image and return STRUCTURED clinical observations.
        
        This is the new preferred method over describe_image() for vision tasks.
        Uses JSON mode + Pydantic parsing for guaranteed schema compliance.
        
        Args:
            image_bytes: Raw image binary data
            mime_type: MIME type (image/jpeg, image/png, etc.)
            context: Optional consultation context for species/breed hints
        
        Returns:
            StructuredVisionOutput if successful, None if analysis fails
        
        Example:
            >>> output = llm.describe_image_structured(img_bytes, "image/jpeg")
            >>> output.species_detected
            'dog'
            >>> output.lesions[0].location
            'right ear canal'
        """
        pass
```

### Backward Compatibility Guarantee

- `describe_image()` remains unchanged (returns `str | None`)
- `describe_image_structured()` is a NEW method
- Both methods share the same caching and telemetry infrastructure

---

## 3. Agent Class Interfaces

### 3.1 VisionAnalyzerAgent

```python
# src/ekosistem_satwa/ai/agents/vision_analyzer.py

from ..llm import LLMClient
from ..schemas import ConsultationContext, StructuredVisionOutput
from ...data_loader import KnowledgeBase


class VisionAnalyzerAgent:
    """
    Agent specialized in extracting structured clinical data from images.
    
    Responsibilities:
    - Species/breed identification against Knowledge Base
    - Age estimation with confidence bounds
    - Lesion detection and characterization
    - Red flag identification for emergency conditions
    - Symptom extraction from visual findings
    
    Configuration:
        enable_breed_lookup: bool - match against KB breeds (default: True)
        lesion_confidence_threshold: float - minimum confidence to report (default: 0.3)
    """
    
    def __init__(
        self,
        llm: LLMClient,
        kb: KnowledgeBase,
        enable_breed_lookup: bool = True,
        lesion_confidence_threshold: float = 0.3,
    ):
        self.llm = llm
        self.kb = kb
        self.enable_breed_lookup = enable_breed_lookup
        self.lesion_confidence_threshold = lesion_confidence_threshold
    
    def analyze(
        self,
        image_bytes: bytes,
        mime_type: str,
        context: ConsultationContext | None = None,
    ) -> StructuredVisionOutput:
        """
        Analyze a single image and return structured output.
        
        Flow:
        1. Call LLM with structured output prompt
        2. Parse JSON response into StructuredVisionOutput
        3. If context provides species/breed, use to refine/verify
        4. Match detected lesions against KB clinical vocabulary
        5. Extract symptoms from visual findings
        """
        pass
    
    def analyze_batch(
        self,
        images: list[tuple[bytes, str]],  # (bytes, mime_type)
        context: ConsultationContext | None = None,
    ) -> list[StructuredVisionOutput]:
        """
        Analyze multiple images and return per-image structured outputs.
        
        Note: This does NOT aggregate findings across images - it returns
        one StructuredVisionOutput per input image. Use aggregate_findings()
        to combine multiple outputs.
        """
        pass
    
    def aggregate_findings(
        self,
        outputs: list[StructuredVisionOutput],
    ) -> StructuredVisionOutput:
        """
        Aggregate findings from multiple images of the same patient.
        
        Logic:
        - species_detected: majority vote, or highest confidence
        - breed_hints: union, deduplicated, ordered by frequency
        - age_estimate: combine ranges, weighted by confidence
        - lesions: union, with confidence averaging
        - red_flags: union, deduplicated
        - extracted_symptoms: union, deduplicated
        """
        pass
```

### 3.2 OwnerClarifierAgent

```python
# src/ekosistem_satwa/ai/agents/owner_clarifier.py

from dataclasses import dataclass
from ..llm import LLMClient
from ..schemas import (
    ConsultationContext,
    ConsultationState,
    ExtractedSymptom,
    IntakeResult,
    StructuredVisionOutput,
)
from ...data_loader import KnowledgeBase


@dataclass
class ClarificationThresholds:
    """Configuration for when to trigger clarification."""
    min_ambiguity_score: float = 0.6      # Above this = ask
    max_questions_per_session: int = 3     # Safety limit
    min_confidence_for_symptom: float = 0.4  # Below this = clarify


class OwnerClarifierAgent:
    """
    Agent for managing interactive clarification with pet owners.
    
    Responsibilities:
    - Identify ambiguous or missing information in intake
    - Generate natural, targeted follow-up questions
    - Process owner responses and extract structured data
    - Track clarification state across turns
    - Know when to stop (sufficient information gathered)
    
    Use Cases:
    - Vision analysis shows "possible ear infection" but location is unclear
    - Owner mentions "loss of appetite" but timeline is missing
    - Symptom extractor has low confidence on a key finding
    """
    
    def __init__(
        self,
        llm: LLMClient,
        kb: KnowledgeBase,
        thresholds: ClarificationThresholds | None = None,
    ):
        self.llm = llm
        self.kb = kb
        self.thresholds = thresholds or ClarificationThresholds()
    
    def identify_needs(
        self,
        vision_outputs: list[StructuredVisionOutput],
        intake: IntakeResult,
        context: ConsultationContext,
        previous_answers: dict[str, str] | None = None,
    ) -> list[ClarificationNeed]:
        """
        Identify what information needs clarification from the owner.
        
        Returns list of ClarificationNeed objects, ordered by priority.
        An empty list means no clarification is needed.
        
        Priority order (highest first):
        1. Red flags with ambiguous details
        2. High-impact symptoms with low confidence
        3. Missing timeline/onset information
        4. Breed/species ambiguity
        5. General history questions
        """
        pass
    
    def generate_question(
        self,
        need: ClarificationNeed,
        conversation_history: list[dict] | None = None,
        context: ConsultationContext | None = None,
    ) -> str:
        """
        Generate a natural language question for the pet owner.
        
        The question should be:
        - Specific (not "Tell me more")
        - In natural Bahasa Indonesia
        - Context-aware (refers to what owner already said)
        - Not leading
        
        Example good: "Kapan pertama kali Anda melihat kemerahan di telinga kanan?"
        Example bad:  "Apakah ini sudah lama?"
        """
        pass
    
    def process_answer(
        self,
        question_asked: str,
        owner_answer: str,
        context: ConsultationContext,
    ) -> tuple[list[ExtractedSymptom], list[str]]:
        """
        Process owner's answer and extract structured data.
        
        Returns:
            (list[ExtractedSymptom], list[str] of resolved field names)
        
        Use case:
            - Owner answers "It started 3 days ago and he's been scratching a lot"
            - Extract: ["Gatal-gatal", "Onset akut (< 7 hari)"]
            - Resolved: ["timeline", "itch_description"]
        """
        pass
    
    def should_continue(
        self,
        needs_identified: list[ClarificationNeed],
        answers_collected: int,
        remaining_ambiguity: float,
    ) -> tuple[bool, str | None]:
        """
        Determine if clarification should continue.
        
        Returns:
            (should_continue: bool, reason_if_no: str | None)
        
        Stop conditions:
        1. No more high-priority needs (ambiguity < threshold)
        2. Max questions reached
        3. Owner answers are not providing new information
        
        Continue conditions:
        1. High-urgency ambiguities remain
        2. Under max questions and useful information expected
        """
        pass
```

### 3.3 VetSummarizerAgent

```python
# src/ekosistem_satwa/ai/agents/vet_summarizer.py

from ..llm import LLMClient
from ..schemas import (
    ConsultationState,
    StructuredVisionOutput,
    VetSummary,
)


class VetSummarizerAgent:
    """
    Agent for compiling consultation inputs into vet-optimized summaries.
    
    Design Principles:
    1. **Scanner-friendly**: Use bullet points, bold key items
    2. **Chronologically organized**: Timeline is critical in vet med
    3. **Highlight red flags**: Emergency signs should be impossible to miss
    4. **Separate concerns**: Owner-reported vs. AI-detected findings
    5. **Actionable**: Suggest what the vet should focus on
    
    Output Structure:
    - Patient overview (1-2 sentences)
    - Timeline summary (chronological)
    - Key findings (bulleted)
    - Visual findings (from images)
    - Owner concerns (verbatim or near-verbatim)
    - Red flags (highlighted)
    - Suggested focus areas
    """
    
    PROMPT_TEMPLATE = """
    Anda adalah asisten dokter hewan yang ahli merangkum informasi klinis.
    Buat ringkasan yang SINGKAT, PADAT, dan BERTAHAP untuk dokter hewan yang sibuk.
    
    Aturan:
    1. Gunakan poin-poin untuk temuan kunci
    2. TANDAI MERAH tanda darurat dengan [DARURAT]
    3. Urutkan gejala kronologis (kapan muncul)
    4. Bedakan: temuan AI (dari gambar) vs keluhan owner
    5. Akhiri dengan area fokus yang disarankan untuk dokter
    
    Data konsultasi:
    {consultation_data}
    
    Output dalam format JSON sesuai schema VetSummary.
    """
    
    def __init__(self, llm: LLMClient):
        self.llm = llm
    
    def summarize(
        self,
        consultation_state: ConsultationState,
        vision_outputs: list[StructuredVisionOutput],
        clarification_history: list[dict] | None = None,
    ) -> VetSummary:
        """
        Generate comprehensive vet-optimized summary.
        
        Flow:
        1. Compile all data sources:
           - Consultation state (text turns, accumulated symptoms)
           - Vision outputs (structured image analysis)
           - Clarification history (Q&A with owner)
        
        2. Build prompt with all context
        
        3. Call LLM in JSON mode with VetSummary schema
        
        4. Return structured VetSummary
        
        The structured field in VetSummary should contain:
        {
            "species": "dog" | "cat" | None,
            "breed_guess": "golden retriever" | None,
            "age_range": {"min": 2.0, "max": 4.0} | None,
            "body_systems_affected": ["integumentary", "auditory"],
            "urgency_level": "emergency" | "urgent" | "routine",
        }
        """
        pass
    
    def summarize_for_turn(
        self,
        intake_text: str,
        vision_outputs: list[StructuredVisionOutput],
        previous_summary: VetSummary | None = None,
    ) -> VetSummary:
        """
        Incremental summary for a single turn (not full consultation).
        
        Useful when vet wants to see what's new after each owner message,
        without regenerating the entire consultation summary.
        """
        pass
```

### 3.4 ClinicalReasoningOrchestrator

```python
# src/ekosistem_satwa/ai/agents/orchestrator.py

from typing import Literal

from ..llm import LLMClient
from ..schemas import (
    AISuggestion,
    ConsultationContext,
    ConsultationState,
    IntakePayload,
    IntakeResult,
    OrchestratorResult,
)
from ...data_loader import KnowledgeBase
from .vision_analyzer import VisionAnalyzerAgent
from .owner_clarifier import OwnerClarifierAgent
from .vet_summarizer import VetSummarizerAgent
from ..suggestion_engine import SuggestionEngine


OrchestratorMode = Literal["auto", "vision_only", "full", "legacy"]


class ClinicalReasoningOrchestrator:
    """
    Central orchestrator for multi-agent consultation workflow.
    
    This is the MAIN ENTRY POINT for the new architecture.
    ConsultationService can optionally delegate to this orchestrator.
    
    Modes:
    - "legacy": Use old flow (IntakeProcessor + SuggestionEngine directly)
    - "vision_only": Use structured vision but no clarification/summarization
    - "full": Complete multi-agent flow
    - "auto": Decide based on consultation complexity
    
    Flow Diagram:
    ┌─────────────────────────────────────────────────────────────┐
    │                    IntakePayload received                    │
    └─────────────────────────┬───────────────────────────────────┘
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  1. Process Media through VisionAnalyzerAgent               │
    │     - For each image: get StructuredVisionOutput           │
    │     - Aggregate findings across images                      │
    └─────────────────────────┬───────────────────────────────────┘
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  2. Process Text + extract symptoms                         │
    │     - Use existing SymptomExtractor                         │
    │     - Merge vision-extracted symptoms                       │
    └─────────────────────────┬───────────────────────────────────┘
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  3. Check: Clarification needed?                            │
    │     - OwnerClarifierAgent.identify_needs()                  │
    │     - If YES and under threshold:                            │
    │         - Generate next question                             │
    │         - Return early with clarification_needed=True       │
    │     - If NO: continue                                        │
    └─────────────────────────┬───────────────────────────────────┘
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  4. VetSummarizerAgent creates VetSummary                   │
    │     - Compile: text turns + vision + clarification history │
    │     - Output: structured summary for vet UI                 │
    └─────────────────────────┬───────────────────────────────────┘
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  5. SuggestionEngine generates AISuggestion                 │
    │     - Existing logic: symptoms → diseases + diagnostics     │
    │     - Enhanced: structured vision data as additional context│
    └─────────────────────────┬───────────────────────────────────┘
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  6. Return OrchestratorResult                                │
    │     - vet_summary + ai_suggestion + vision_outputs         │
    │     - Ready for Vet UI consumption                          │
    └─────────────────────────────────────────────────────────────┘
    """
    
    def __init__(
        self,
        kb: KnowledgeBase,
        llm: LLMClient | None = None,
        mode: OrchestratorMode = "auto",
        vision_agent: VisionAnalyzerAgent | None = None,
        clarifier_agent: OwnerClarifierAgent | None = None,
        summarizer_agent: VetSummarizerAgent | None = None,
        suggestion_engine: SuggestionEngine | None = None,
    ):
        self.kb = kb
        self.llm = llm or LLMClient()
        self.mode = mode
        
        # Agents - injectable for testing
        self.vision_agent = vision_agent or VisionAnalyzerAgent(self.llm, self.kb)
        self.clarifier_agent = clarifier_agent or OwnerClarifierAgent(self.llm, self.kb)
        self.summarizer_agent = summarizer_agent or VetSummarizerAgent(self.llm)
        self.suggestion_engine = suggestion_engine or SuggestionEngine(self.kb, self.llm)
    
    def process_intake(
        self,
        state: ConsultationState,
        payload: IntakePayload,
    ) -> OrchestratorResult:
        """
        Process a consultation intake turn using multi-agent workflow.
        
        This is the main method that ConsultationService._run_turn()
        should call when in orchestrator mode.
        
        Returns OrchestratorResult which contains:
        - intake_result: Processed intake (for backward compat)
        - vet_summary: Vet-optimized summary (NEW)
        - ai_suggestion: Disease/diagnostic/treatment suggestions
        - vision_outputs: All structured vision outputs
        - clarification_needed: True if owner should be asked a question
        - next_question: The question to ask (if clarification_needed)
        """
        # Implementation follows the flow diagram above
        pass
    
    def process_clarification_answer(
        self,
        consultation_id: str,
        question_asked: str,
        owner_answer: str,
        state: ConsultationState,
    ) -> OrchestratorResult:
        """
        Process owner's answer to a clarification question.
        
        Flow:
        1. Parse answer and extract symptoms
        2. Update consultation state
        3. Check if more clarification is needed
        4. If not: run summarizer + suggestion engine
        5. Return result
        """
        pass
    
    # --- Legacy compatibility wrapper ---
    def run_legacy(
        self,
        state: ConsultationState,
        payload: IntakePayload,
    ) -> OrchestratorResult:
        """
        Run the OLD (pre-orchestrator) flow for backward compatibility.
        
        Uses:
        - IntakeProcessor (unstructured vision)
        - SymptomExtractor
        - SuggestionEngine (direct)
        
        No:
        - StructuredVisionOutput
        - OwnerClarifierAgent
        - VetSummarizerAgent
        
        This allows gradual rollout with feature flag.
        """
        pass
```

---

## 4. Integration with ConsultationService

### 4.1 Feature Flag Configuration

```python
# src/ekosistem_satwa/config.py (or appropriate config location)

@dataclass
class OrchestratorSettings:
    """Settings for multi-agent orchestrator."""
    enabled: bool = False  # Set via EKOSISTEM_SATWA_ORCHESTRATOR_ENABLED
    mode: OrchestratorMode = "auto"
    enable_clarification: bool = True
    enable_structured_vision: bool = True
    max_clarification_questions: int = 3
    min_ambiguity_for_clarification: float = 0.6
    
    # Cost controls
    max_llm_calls_per_consultation: int = 10
    vision_cache_ttl_hours: int = 24 * 7  # 1 week
```

### 4.2 ConsultationService Modifications

```python
# In ConsultationService.__init__:
class ConsultationService:
    def __init__(
        self,
        kb: KnowledgeBase | None = None,
        store: LearningStore | None = None,
        llm: LLMClient | None = None,
        session_store: SessionStore | None = None,
        use_orchestrator: bool = False,  # NEW
    ):
        # ... existing init ...
        self.use_orchestrator = use_orchestrator
        self.orchestrator: ClinicalReasoningOrchestrator | None = None
        if use_orchestrator:
            self.orchestrator = ClinicalReasoningOrchestrator(
                kb=self.kb, llm=self.llm,
            )

    def _run_turn(
        self, state: ConsultationState, payload: IntakePayload
    ) -> ConsultationResult:
        """Modified to optionally use orchestrator."""
        
        if self.use_orchestrator and self.orchestrator:
            # NEW: use orchestrator flow
            orchestrator_result = self.orchestrator.process_intake(state, payload)
            
            # Package result into ConsultationResult (backward compatible)
            # Plus expose new fields via state
            result = ConsultationResult(
                consultation_id=state.consultation_id,
                intake=orchestrator_result.intake_result,
                suggestion=orchestrator_result.ai_suggestion,
            )
            # Store orchestrator-specific outputs in state for UI
            state.orchestrator_output = orchestrator_result.model_dump()
            return result
        
        # LEGACY: original flow
        processor = IntakeProcessor(
            self.kb, category_slug=state.context.category_slug, llm=self.llm
        )
        intake = processor.process(payload)
        # ... rest of existing _run_turn ...
```

---

## 5. Test Requirements

### 5.1 Unit Tests

```python
# Test files to create:
tests/ai/agents/
├── test_vision_analyzer.py
├── test_owner_clarifier.py
├── test_vet_summarizer.py
└── test_orchestrator.py
```

#### VisionAnalyzerAgent Tests
```python
def test_describe_image_structured_returns_valid_schema():
    """JSON output should parse into StructuredVisionOutput without errors."""
    pass

def test_species_detection_matches_kb():
    """Detected species should be in KB categories."""
    pass

def test_lesion_confidence_filtering():
    """Low confidence lesions should be filtered when below threshold."""
    pass

def test_aggregate_findings_combines_multiple_images():
    """Multiple images of same patient should have merged findings."""
    pass
```

#### OwnerClarifierAgent Tests
```python
def test_identify_needs_returns_empty_for_clear_input():
    """High-confidence intake should need no clarification."""
    pass

def test_identify_needs_prioritizes_red_flags():
    """Ambiguous emergency signs should be highest priority."""
    pass

def test_generate_question_is_specific():
    """Questions should be specific, not generic."""
    pass

def test_should_continue_stops_at_max_questions():
    """Should not exceed max_questions_per_session."""
    pass
```

#### VetSummarizerAgent Tests
```python
def test_summary_contains_all_red_flags():
    """All red flags from all sources should appear in summary."""
    pass

def test_structured_field_is_populated():
    """The machine-readable field should have species/age/breed data."""
    pass

def test_timeline_is_chronological():
    """Timeline should order events by when they occurred."""
    pass
```

#### Orchestrator Tests
```python
def test_orchestrator_runs_full_flow():
    """End-to-end flow should produce OrchestratorResult."""
    pass

def test_orchestrator_early_return_on_clarification():
    """If clarification needed, should return early before summarization."""
    pass

def test_legacy_mode_uses_old_flow():
    """When mode='legacy', should not use agents."""
    pass
```

### 5.2 Integration Tests

```python
tests/integration/
└── test_consultation_orchestrated.py
```

Test scenarios:
1. Simple text-only consultation (no images)
2. Consultation with single clear image
3. Consultation with multiple images needing aggregation
4. Consultation triggering clarification loop
5. Consultation with red flag emergency signs
6. Full multi-turn consultation with clarifications

---

## 6. Migration Plan

### Phase 1: Foundation (Week 1)
- [ ] Add `StructuredVisionOutput` and related types to `schemas.py`
- [ ] Add `describe_image_structured()` to `LLMClient`
- [ ] Update `MediaObservation` with optional `structured` field
- [ ] Write unit tests for structured vision

### Phase 2: Agents (Week 2)
- [ ] Implement `VisionAnalyzerAgent`
- [ ] Implement `OwnerClarifierAgent`
- [ ] Implement `VetSummarizerAgent`
- [ ] Write unit tests for each agent

### Phase 3: Orchestrator (Week 3)
- [ ] Implement `ClinicalReasoningOrchestrator`
- [ ] Add feature flag config `OrchestratorSettings`
- [ ] Modify `ConsultationService` to optionally use orchestrator
- [ ] Write orchestrator tests

### Phase 4: Integration (Week 4)
- [ ] Modify `IntakeProcessor._process_media()` to use structured vision
- [ ] Write integration tests
- [ ] Add API endpoints for clarification handling
- [ ] Update OpenAPI schema

### Phase 5: Deployment
- [ ] Deploy to staging with `ORCHESTRATOR_ENABLED=false`
- [ ] Enable for internal dogfooding
- [ ] A/B test with small vet cohort
- [ ] Monitor cost, latency, satisfaction
- [ ] Gradual rollout with kill switch

---

## 7. Rollback Strategy

If orchestrator causes issues:
1. **Immediate**: Set `EKOSISTEM_SATWA_ORCHESTRATOR_ENABLED=false`
2. **ConsultationService** falls back to legacy `_run_turn()`
3. **All existing data and behavior preserved**
4. **Structured vision still available** via `describe_image_structured()` even if orchestrator disabled

---

## Appendix: Prompt Templates Reference

### A.1 Structured Vision Prompt

```
Anda adalah dokter hewan ahli yang menganalisa gambar hewan untuk keperluan klinis.

Analisa gambar ini dengan SANGAT OBJEKTIF. Hanya laporkan apa yang ANDA LIHAT,
bukan apa yang Anda simpulkan tanpa bukti visual.

Output dalam format JSON dengan field berikut:
{
  "species_detected": "dog" | "cat" | "rabbit" | "ferret" | "bird" | null,
  "breed_hints": ["string"],  // breed slugs yang mirip dari KB, kosong jika tidak yakin
  "age_estimate": {
    "min": float,  // perkiraan umur minimum dalam tahun
    "max": float,  // perkiraan umur maksimum dalam tahun
    "confidence": float  // 0.0 - 1.0 keyakinan
  } | null,
  "lesions": [
    {
      "location": "string",  // lokasi anatomis spesifik
      "type": "string",      // jenis lesi: erythema, alopecia, papule, pustule, ulcer, crust, scale, mass, discharge, swelling, other
      "severity": "mild" | "moderate" | "severe",
      "description": "string",  // deskripsi detail
      "confidence": float
    }
  ],
  "red_flags": ["string"],  // tanda darurat: pucat, sesak nafas, perdarahan hebat, dll
  "raw_description": "string",  // deskripsi teks lengkap untuk audit
  "extracted_symptoms": ["string"]  // name_id gejala dari KB
}

PENTING:
- Jika tidak yakin tentang spesies/ras, isi null atau array kosong
- Jangan mendiagnosa penyakit — hanya deskripsikan temuan visual
- Lesi hanya yang TERLIHAT, bukan yang mungkin ada
```

### A.2 Clarification Question Generation Prompt

```
Anda adalah asisten dokter hewan yang bertanya ke pemilik hewan untuk klarifikasi.

Informasi yang sudah ada:
{existing_info}

Yang perlu diklarifikasi:
{clarification_need}

Riwayat percakapan sejauh ini:
{conversation_history}

Buat PERTANYAAN TUNGGAL yang:
1. SPESIFIK (bukan "ada yang lain?")
2. Alami dalam Bahasa Indonesia
3. Tidak menggiring jawaban
4. Menghormati pemilik (tidak seperti interogasi)

Contoh bagus: "Kapan pertama kali Anda melihat benjolan di kaki belakang kiri?"
Contoh buruk:  "Sudah berapa lama?"

Output hanya teks pertanyaan, tidak ada tambahan.
```

### A.3 Vet Summary Prompt

```
Anda adalah dokter hewan senior yang merangkum data konsultasi untuk rekan sejawat.

Data konsultasi:
- Pasien: {species}, {age_estimate} tahun (perkiraan)
- Keluhan utama: {chief_complaint}
- Temuan gambar: {vision_findings}
- Riwayat klarifikasi: {clarification_history}
- Gejala terakumulasi: {symptoms}
- Tanda darurat: {red_flags}

Buat ringkasan untuk dokter hewan yang akan memeriksa pasien ini.

Ringkasan harus:
1. SINGKAT namun LENGKAP (maks 150 kata untuk overview)
2. Menyoroti temuan PENTING di awal
3. Memisahkan: keluhan owner vs temuan AI
4. MENANDAI tanda darurat dengan jelas
5. Memberikan saran area fokus untuk pemeriksaan

Output dalam JSON:
{
  "patient_overview": "string",
  "timeline_summary": "string",
  "key_clinical_findings": ["string"],
  "visual_findings_summary": "string",
  "owner_concerns": ["string"],
  "red_flags": ["string"],
  "suggested_focus_areas": ["string"],
  "structured": {
    "species": "string",
    "breed_guess": "string" | null,
    "age_range": {"min": float, "max": float} | null,
    "body_systems_affected": ["string"],
    "urgency_level": "emergency" | "urgent" | "routine"
  }
}
```

---

## Appendix B: RAG Knowledge Service (NEW)

### B.1 Overview

The RAG (Retrieval-Augmented Generation) Knowledge Service provides semantic search
over the veterinary knowledge base. It complements the existing keyword-based
`KnowledgeGrounder` with embedding-based similarity search.

**Key Components:**
- `EmbeddingService` - Generates text embeddings (OpenAI or local/Ollama fallback)
- `VectorStore` - In-memory vector store with cosine similarity search
- `KnowledgeRAGService` - Main service: ingestion + retrieval
- `knowledge_router` - FastAPI endpoints at `/api/v1/knowledge/`

### B.2 Module Location

```
src/ekosistem_satwa/knowledge/
├── __init__.py          # Exports: KnowledgeRAGService, get_rag_service, EmbeddingService, VectorStore, VectorDocument
├── embeddings.py        # Embedding service (OpenAI + hash-based fallback)
├── vector_store.py      # In-memory vector store with persistence
└── rag.py               # Main RAG service + ingestion pipeline
```

### B.3 API Endpoints

#### POST `/api/v1/knowledge/query`

Semantic search over the knowledge base.

**Request:**
```json
{
  "query_text": "Anjing muntah dan diare berdarah, apa yang harus dilakukan?",
  "species": "dog",
  "topic": "digestive",
  "source": "disease",
  "top_k": 5,
  "min_score": 0.3,
  "format_for_prompt": true
}
```

**Parameters:**
- `query_text`: Natural language query (required)
- `species`: Filter by species (dog, cat, rabbit, etc.) - optional
- `topic`: Filter by body system (digestive, skin, respiratory, etc.) - optional
- `source`: Filter by source type (disease, breed, drug, nutrition, faq) - optional
- `top_k`: Max results to return (1-20, default 5)
- `min_score`: Minimum similarity threshold (0.0-1.0, default 0.3)
- `format_for_prompt`: If true, returns formatted context string for LLM prompts
- `include_embeddings`: Include raw embedding vectors (large)

**Response:**
```json
{
  "query_text": "Anjing muntah dan diare berdarah...",
  "top_k": 5,
  "total_found": 3,
  "results": [
    {
      "id": "disease_dog-parvovirus_0",
      "text": "DISEASE: Parvovirus (Parvo)\nOVERVIEW: Infeksi virus sangat menular...",
      "score": 0.92,
      "source": "disease",
      "species": "dog",
      "topic": "digestive",
      "is_emergency": true,
      "disease_slug": "dog-parvovirus"
    }
  ],
  "species_filter": "dog",
  "topic_filter": "digestive",
  "prompt_context": "[1] | Species: dog | Type: disease | ...\n\n---\n\n[2] | ..."
}
```

#### GET `/api/v1/knowledge/stats`

Get RAG service statistics.

**Response:**
```json
{
  "total_documents": 1542,
  "dimensions": 1536,
  "by_source": {"disease": 1200, "breed": 342},
  "by_species": {"dog": 400, "cat": 350, ...},
  "by_topic": {"digestive": 200, "skin": 180, ...},
  "emergency_documents": 45,
  "embedding_model": "text-embedding-3-small",
  "embedding_available": true,
  "total_embedding_tokens_used": 45000,
  "persist_path": "data/generated/rag_vector_store.json",
  "is_ingested": true
}
```

#### POST `/api/v1/knowledge/reindex`

Force rebuild of the vector store from source JSON data.

**Request:**
```json
{
  "force_rebuild": true,
  "chunk_size": 800,
  "chunk_overlap": 100
}
```

### B.4 Programmatic Usage

```python
from ekosistem_satwa.knowledge import KnowledgeRAGService, get_rag_service

# Get singleton service (auto-ingests on first call)
rag = get_rag_service()

# Or create manually
rag = KnowledgeRAGService()
rag.ingest_knowledge_base(force_rebuild=False)

# Search
result = rag.search(
    query_text="Anjing muntah dan diare berdarah",
    species="dog",
    top_k=5,
    min_score=0.3
)

# Get formatted context for LLM prompt
context = result.to_prompt_context(max_chars_per_doc=1500)

# Use in AI gateway before LLM call
# context = rag.search(owner_query, species=patient_species).to_prompt_context()
# full_prompt = f"Context: {context}\n\nQuery: {owner_query}"
```

### B.5 Data Indexed

The RAG service automatically indexes:

| Source Type | Description | Metadata |
|-------------|-------------|----------|
| `disease` | Disease clinical data (symptoms, diagnostics, treatments, medications) | species=dog/cat/..., topic=body_system, is_emergency=True/False |
| `breed` | Breed information (traits, predispositions, care level) | species=dog/cat/..., topic="breed_info" |
| `drug` | Medication database (from disease treatments) | Coming soon |
| `nutrition` | Nutrition guidelines | Coming soon |
| `faq` | Frequently asked questions | Coming soon |

**Document Fields per Disease:**
- Disease name (ID + English)
- Overview/etiology/severity
- Symptoms (with red flag markers)
- Causes/prevention/prognosis
- Diagnostic procedures (gold standard marked)
- Treatments + medications + dosages + cautions
- Breed susceptibility information

### B.6 Persistence

The vector store is automatically persisted to:
```
data/generated/rag_vector_store.json
```

On first load, if this file exists, it's loaded instead of re-ingesting.
To force re-ingestion:
- Call `POST /api/v1/knowledge/reindex` with `force_rebuild=true`
- Or call `rag.ingest_knowledge_base(force_rebuild=True)`

### B.7 Integration with AI Gateway (Future Work)

For AI Gateway integration:

1. **Before routing to LLM**, call `KnowledgeRAGService.search()`
2. **Format results** with `to_prompt_context()`
3. **Inject context** into the system prompt
4. **Include metadata** (emergency flags, disease slugs) in the structured output

```python
# Example ContextLoader pattern
class ContextLoader:
    def load_for_query(
        self,
        query: str,
        species: str | None,
        topic: str | None
    ) -> tuple[str, dict]:
        """Load RAG context for a query.
        
        Returns: (formatted_context_string, metadata_dict)
        """
        rag = get_rag_service()
        result = rag.search(
            query_text=query,
            species=species,
            topic=topic,
            top_k=5
        )
        
        context = result.to_prompt_context()
        
        # Extract metadata for safety guards
        has_emergency = any(r.is_emergency for r in result.results)
        matched_diseases = [r.disease_slug for r in result.results if r.disease_slug]
        
        return context, {
            "has_emergency": has_emergency,
            "matched_diseases": matched_diseases,
            "total_chunks": result.total_found,
        }
```

### B.8 Test Coverage

Test file: `tests/test_knowledge_rag.py`

Covers:
- `EmbeddingService`: fallback embeddings, determinism, caching
- `VectorStore`: add/get/delete, similarity search, metadata filtering, stats, persistence
- `VectorDocument`: dataclass creation, defaults

Run tests with:
```bash
cd projects/sobatpaws-ai
PYTHONPATH=src pytest tests/test_knowledge_rag.py -v
```

