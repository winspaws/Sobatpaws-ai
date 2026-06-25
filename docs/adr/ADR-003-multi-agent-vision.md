# ADR-003: Multi-Agent Orchestrator + Structured Vision Output

## Status
Proposed

## Context

### Current Architecture
Ekosistem Satwa AI currently processes consultations with a monolithic flow:
1. `LLMClient.describe_image()` returns unstructured `str` (plain text description)
2. `IntakeProcessor._process_media()` wraps vision output in `MediaObservation.text`
3. `SymptomExtractor` parses free text to extract symptoms
4. `ConsultationService` + `SuggestionEngine` generates final suggestions

### Problems Identified
1. **Unstructured Vision Output**: `describe_image()` returns free text which:
   - Requires re-parsing to extract structured data (species, breed, lesions)
   - Loses semantic structure between LLM output and downstream consumption
   - Cannot directly populate structured fields in vet UI

2. **Missing Specialized Capabilities**:
   - No dedicated agent to extract clinical signs from images systematically
   - No clarifying agent to ask pet owners targeted follow-up questions
   - No summarization agent tailored for veterinary clinical documentation

3. **Hardcoded Orchestration**: `ConsultationService` handles all logic directly, making it:
   - Difficult to add new agent types
   - Hard to test individual components in isolation
   - Challenging to implement conditional flows (e.g., "only clarify if vision is ambiguous")

### Alternatives Considered
| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| Keep monolithic + regex parsing | Simple to implement | Fragile, unmaintainable, no semantic guarantees | ❌ Rejected |
| Structured vision only (no agents) | Smaller scope | Still misses clarification & summarization value | ⚠️ Partial |
| **Multi-agent + structured vision** | Clean separation, testable, extensible | More initial implementation work | ✅ **Selected** |

### Requirements for Structured Vision Output
The vision system must provide:
- `species_detected`: Primary species identification
- `breed_hints`: Top N breed matches from knowledge base
- `age_estimate_years`: Range with confidence score
- `lesions`: Structured list with location, type, severity, description
- `red_flags`: Emergency signs requiring immediate attention
- `raw_description`: Original LLM output for audit/compliance

### Requirements for Agent Architecture
Four specialized agents identified:
1. **VisionAnalyzerAgent**: Image → structured output + symptom extraction
2. **OwnerClarifierAgent**: Interactive Q&A with pet owner to resolve ambiguities
3. **VetSummarizerAgent**: Compile all inputs into vet-optimized structured summary
4. **ClinicalReasoningOrchestrator**: Coordinate agents + existing `SuggestionEngine`

## Decision

### 1. Structured Vision Output Schema
Modify `LLMClient.describe_image()` to return a structured dictionary instead of `str`. A new method `describe_image_structured()` will be added alongside the legacy method for backward compatibility.

```python
@dataclass
class AgeEstimate:
    min: float
    max: float
    confidence: float  # 0.0 - 1.0

@dataclass
class LesionObservation:
    location: str           # e.g., "left ear pinna", "dorsal trunk"
    type: str               # e.g., "erythema", "alopecia", "papule", "ulcer"
    severity: str           # "mild" | "moderate" | "severe"
    description: str        # detailed clinical description

@dataclass
class StructuredVisionOutput:
    species_detected: str | None           # "dog" | "cat" | "rabbit" | ...
    breed_hints: list[str]                  # matched breed slugs from KB
    age_estimate: AgeEstimate | None
    lesions: list[LesionObservation]
    red_flags: list[str]                    # emergency signs detected
    raw_description: str                     # original LLM text output
    extracted_symptoms: list[str]            # symptom name_ids from KB vocabulary
```

**Backward Compatibility**:
- Existing `describe_image()` will remain unchanged (returns `str`)
- New `describe_image_structured()` returns `StructuredVisionOutput | None`
- `MediaObservation` will be extended with optional `structured` field

### 2. Multi-Agent Architecture

#### System Diagram (Mermaid)
```mermaid
flowchart TB
    Owner[Pet Owner Input<br/>(text + images + audio)]
    
    subgraph Orchestrator["ClinicalReasoningOrchestrator"]
        Router{Router & State}
    end
    
    subgraph SpecializedAgents["Specialized Agents"]
        Vision[VisionAnalyzerAgent]
        Clarifier[OwnerClarifierAgent]
        Summarizer[VetSummarizerAgent]
    end
    
    subgraph ExistingComponents["Existing Components"]
        SymptomExtractor[SymptomExtractor]
        SuggestionEngine[SuggestionEngine]
        KB[(Knowledge Base)]
    end
    
    VetUI[Vet Clinical UI]
    
    %% Flow
    Owner -->|IntakePayload| Router
    Router -->|images + prompt| Vision
    Vision -->|StructuredVisionOutput| Router
    Router -->|ambiguities detected?| Clarifier
    Clarifier -->|targeted questions| Owner
    Owner -->|answers| Clarifier
    Clarifier -->|resolved context| Router
    Router -->|all inputs + history| Summarizer
    Router -->|symptoms + context| SymptomExtractor
    SymptomExtractor -->|structured symptoms| SuggestionEngine
    KB --> SuggestionEngine
    KB --> Vision
    Summarizer -->|VetSummary| Router
    SuggestionEngine -->|AISuggestion| Router
    Router -->|combined output| VetUI
```

#### Agent Interfaces
```python
# --- VisionAnalyzerAgent ---
class VisionAnalyzerAgent:
    """
    Processes images to extract structured clinical observations.
    
    Responsibilities:
    - Species/breed identification
    - Age estimation
    - Lesion detection and characterization
    - Red flag identification
    - Symptom extraction from visual findings
    """
    
    def __init__(self, llm: LLMClient, kb: KnowledgeBase):
        ...
    
    def analyze(
        self,
        image_bytes: bytes,
        mime_type: str,
        context: ConsultationContext,
    ) -> StructuredVisionOutput:
        """Analyze single image and return structured output."""
        ...
    
    def analyze_batch(
        self,
        images: list[tuple[bytes, str]],  # (bytes, mime_type)
        context: ConsultationContext,
    ) -> list[StructuredVisionOutput]:
        """Analyze multiple images and aggregate findings."""
        ...


# --- OwnerClarifierAgent ---
class ClarificationNeed(BaseModel):
    field: str                    # what needs clarification
    reason: str                   # why clarification is needed
    suggested_questions: list[str]  # targeted questions to ask

class OwnerClarifierAgent:
    """
    Generates and manages clarification dialog with pet owners.
    
    Responsibilities:
    - Identify ambiguities in vision/intake data
    - Generate context-aware follow-up questions
    - Track clarification state across turns
    - Determine when sufficient information is gathered
    """
    
    def __init__(self, llm: LLMClient, kb: KnowledgeBase):
        ...
    
    def identify_needs(
        self,
        vision_outputs: list[StructuredVisionOutput],
        intake: IntakeResult,
        context: ConsultationContext,
    ) -> list[ClarificationNeed]:
        """Identify what needs clarification from owner."""
        ...
    
    def generate_question(
        self,
        need: ClarificationNeed,
        conversation_history: list[dict],
    ) -> str:
        """Generate natural language question for owner."""
        ...
    
    def process_answer(
        self,
        question: str,
        answer: str,
        context: ConsultationContext,
    ) -> ExtractedSymptom | None:
        """Process owner's answer and extract structured data."""
        ...
    
    def is_satisfied(
        self,
        needs: list[ClarificationNeed],
        answers_collected: dict[str, str],
    ) -> bool:
        """Check if clarification threshold is met."""
        ...


# --- VetSummarizerAgent ---
class VetSummary(BaseModel):
    """Structured summary optimized for veterinary clinical workflow."""
    
    patient_overview: str           # 1-2 sentence summary of patient
    timeline_summary: str           # chronological progression of signs
    key_clinical_findings: list[str]  # bullet points for quick scan
    visual_findings_summary: str    # synthesis of all vision outputs
    owner_concerns: list[str]       # owner-reported concerns
    red_flags: list[str]            # consolidated emergency signs
    suggested_focus_areas: list[str]  # what vet should prioritize
    
    # Structured data for UI population
    structured: dict[str, Any]      # species, breed_guess, age_range, etc.


class VetSummarizerAgent:
    """
    Compiles all consultation inputs into a vet-optimized summary.
    
    Responsibilities:
    - Synthesize multi-turn conversation
    - Extract and highlight clinically relevant information
    - Structure output for quick scanning
    - Preserve audit trail of all inputs
    """
    
    def __init__(self, llm: LLMClient):
        ...
    
    def summarize(
        self,
        consultation_state: ConsultationState,
        vision_outputs: list[StructuredVisionOutput],
        clarification_history: list[dict],
    ) -> VetSummary:
        """Generate comprehensive summary for vet."""
        ...


# --- ClinicalReasoningOrchestrator ---
class OrchestratorResult(BaseModel):
    consultation_id: str
    vet_summary: VetSummary
    ai_suggestion: AISuggestion
    vision_outputs: list[StructuredVisionOutput]
    clarification_needed: bool
    next_question: str | None  # if clarification needed


class ClinicalReasoningOrchestrator:
    """
    Orchestrates the multi-agent consultation workflow.
    
    Responsibilities:
    - Manage agent execution order
    - Track consultation state
    - Handle conditional flows (clarification loop)
    - Combine outputs from all agents
    - Interface with existing SuggestionEngine
    """
    
    def __init__(
        self,
        kb: KnowledgeBase,
        llm: LLMClient | None = None,
        vision_agent: VisionAnalyzerAgent | None = None,
        clarifier_agent: OwnerClarifierAgent | None = None,
        summarizer_agent: VetSummarizerAgent | None = None,
        suggestion_engine: SuggestionEngine | None = None,
    ):
        ...
    
    def process_intake(
        self,
        state: ConsultationState,
        payload: IntakePayload,
    ) -> OrchestratorResult:
        """
        Main entry point for processing a consultation turn.
        
        Flow:
        1. Process all media through VisionAnalyzerAgent
        2. Extract symptoms from text + vision
        3. Check if clarification is needed via OwnerClarifierAgent
        4. If needed: generate question and return early
        5. If satisfied: generate VetSummary
        6. Get AISuggestion from SuggestionEngine
        7. Return combined result
        """
        ...
    
    def process_clarification_answer(
        self,
        consultation_id: str,
        question_asked: str,
        owner_answer: str,
    ) -> OrchestratorResult:
        """Process owner's answer to clarification question."""
        ...
```

### 3. Integration with Existing Architecture

#### Modified Files
| File | Change Type | Description |
|------|-------------|-------------|
| `src/ekosistem_satwa/ai/llm.py` | Add | New `describe_image_structured()` method |
| `src/ekosistem_satwa/ai/schemas.py` | Add | New dataclasses: `StructuredVisionOutput`, `LesionObservation`, `AgeEstimate` |
| `src/ekosistem_satwa/ai/intake.py` | Modify | Use structured vision when available |
| `src/ekosistem_satwa/ai/consultation.py` | Modify | Optionally use Orchestrator instead of direct flow |

#### New Files
```
src/ekosistem_satwa/ai/agents/
├── __init__.py
├── base.py              # BaseAgent interface
├── vision_analyzer.py   # VisionAnalyzerAgent
├── owner_clarifier.py   # OwnerClarifierAgent
├── vet_summarizer.py    # VetSummarizerAgent
└── orchestrator.py      # ClinicalReasoningOrchestrator
```

## Consequences

### Positive
1. **Structured Data from Source**: Vision output is immediately usable without text parsing
2. **Separation of Concerns**: Each agent has single responsibility, easier to test and maintain
3. **Testability**: Agents can be unit tested independently with mock inputs
4. **Extensibility**: New agents (e.g., `ResearchAgent`, `SafetyAuditAgent`) can be added without disrupting existing flow
5. **Interactive Capability**: Clarification agent enables multi-turn intelligent dialog
6. **Vet UX Improvement**: Structured summaries reduce cognitive load on veterinarians
7. **Backward Compatible**: Legacy `describe_image()` remains unchanged; opt-in to new features

### Negative
1. **Increased Complexity**: More components to understand and maintain
2. **More Code to Write**: 4 new agent classes plus orchestrator
3. **State Management**: Orchestrator needs to track clarification state across turns
4. **API Surface Expansion**: More methods and classes to document and version
5. **Testing Overhead**: More components = more test cases needed

### Risks
1. **Orchestrator Logic Bloat**: The orchestrator could become a new monolith if not carefully designed
   - Mitigation: Keep orchestrator thin; delegate all actual work to agents
   
2. **Clarification Loop Overhead**: Too many questions could annoy pet owners
   - Mitigation: Implement "sufficiently confident" threshold; max questions per session
   
3. **Schema Evolution**: `StructuredVisionOutput` schema may need to evolve
   - Mitigation: Use Pydantic models with optional fields; versioned schemas if needed
   
4. **Performance**: Multiple LLM calls per consultation increases latency and cost
   - Mitigation:
     - Parallel execution of independent agent calls
     - Aggressive caching of vision outputs
     - Configurable agent enablement (disable clarifier for simple cases)
     - Token optimization via structured output (fewer parsing tokens)

### Cost Impact Analysis
| Component | Current | With Agents | Mitigation |
|-----------|---------|-------------|------------|
| Vision per image | 1 call | 1 call | Same (structured output uses similar tokens) |
| Clarification | 0 calls | 0-3 calls | Threshold-based, optional |
| Summarization | 0 calls | 1 call | Only at end of consultation |
| Symptom extraction | 1 call | 1 call | Same (existing flow) |

**Net Estimate**: +20-50% LLM cost per consultation, with significant UX and clinical value gains.

## Next Steps

### Phase 1: Foundation (Week 1)
1. ✅ Create this ADR for alignment
2. Add `StructuredVisionOutput`, `LesionObservation`, `AgeEstimate` to `schemas.py`
3. Implement `LLMClient.describe_image_structured()` with Pydantic parsing
4. Update `MediaObservation` with optional `structured: StructuredVisionOutput` field
5. Write unit tests for structured vision parsing

### Phase 2: Agents (Week 2)
6. Implement `VisionAnalyzerAgent` wrapper around structured vision
7. Implement `OwnerClarifierAgent` with threshold logic
8. Implement `VetSummarizerAgent` with prompt engineering for vet audience
9. Write agent unit tests with mock LLM responses

### Phase 3: Orchestrator (Week 3)
10. Implement `ClinicalReasoningOrchestrator` with basic flow
11. Add clarification loop state management
12. Integrate with existing `ConsultationService` (opt-in flag)
13. Add feature flag `EKOSISTEM_SATWA_USE_ORCHESTRATOR=true|false`

### Phase 4: Integration & Testing (Week 4)
14. Update `IntakeProcessor._process_media()` to use structured output
15. Write integration tests for full orchestration flow
16. Performance profiling and optimization
17. Update Vet UI API contracts to consume `VetSummary`

### Phase 5: Deployment
18. Deploy to staging with feature flag disabled by default
19. A/B testing with small vet cohort
20. Monitor cost, latency, and vet satisfaction metrics
21. Gradual rollout with kill switch

## Decision Criteria for Go/No-Go
Before full production rollout, verify:
- [ ] Structured vision accuracy > 90% on labeled test set
- [ ] Clarification agent reduces "unknown" symptom rate by > 30%
- [ ] Vet summary receives > 4/5 satisfaction rating in beta
- [ ] p99 latency < 3s for standard consultation
- [ ] Cost increase within projected budget (+50% max)
