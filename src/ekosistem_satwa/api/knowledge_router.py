"""Knowledge Service API Router — RAG query endpoint.

Endpoints:
- POST /api/v1/knowledge/query — Query RAG knowledge base
- GET  /api/v1/knowledge/status — Knowledge service status
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..config import ARTIFACTS_DIR
from ..knowledge.embeddings import EmbeddingService
from ..knowledge.vector_store import VectorDocument, VectorStore

logger = logging.getLogger("ekosistem_satwa.api.knowledge_router")

router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge Service (RAG)"])


# =============================================================================
# REQUEST / RESPONSE MODELS
# =============================================================================


class KnowledgeQueryRequest(BaseModel):
    """Query the RAG knowledge base."""

    query: str = Field(..., min_length=3, max_length=2000, description="Search query")
    species: str | None = Field(default=None, description="Filter by species (dog, cat, etc.)")
    topic: str | None = Field(default=None, description="Filter by topic (digestive, skin, etc.)")
    source: str | None = Field(default=None, description="Filter by source (disease, breed, drug, etc.)")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    min_score: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum relevance score")


class KnowledgeDocument(BaseModel):
    """A single knowledge document result."""

    id: str
    text: str
    score: float
    source: str | None = None
    species: str | None = None
    topic: str | None = None
    confidence: float = 1.0
    disease_slug: str | None = None
    breed_slug: str | None = None
    is_emergency: bool = False
    is_red_flag: bool = False


class KnowledgeQueryResponse(BaseModel):
    """Response from knowledge query."""

    query: str
    results: list[KnowledgeDocument]
    total_found: int
    processing_time_ms: float
    embedding_model: str


class KnowledgeStatusResponse(BaseModel):
    """Knowledge service status."""

    status: str
    vector_store_loaded: bool
    total_documents: int
    embedding_available: bool
    embedding_model: str
    dimensions: int


# =============================================================================
# SERVICE INSTANCES (lazy-loaded)
# =============================================================================

_vector_store: VectorStore | None = None
_embedding_service: EmbeddingService | None = None


def _get_embedding() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def _get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        store_path = ARTIFACTS_DIR / "vector_store.json"
        if store_path.exists():
            try:
                _vector_store = VectorStore.load(store_path)
                logger.info("Vector store loaded: %d docs", _vector_store.count())
            except Exception as exc:
                logger.warning("Failed to load vector store: %s", exc)
                _vector_store = VectorStore()
        else:
            _vector_store = VectorStore()
            logger.info("New vector store created (empty)")
    return _vector_store


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("/query", response_model=KnowledgeQueryResponse)
def knowledge_query(req: KnowledgeQueryRequest) -> KnowledgeQueryResponse:
    """Query the RAG knowledge base.

    Returns relevant documents ranked by semantic similarity.

    **Example request:**
    ```json
    {
        "query": "Kucing muntah dan diare",
        "species": "cat",
        "topic": "digestive",
        "top_k": 5,
        "min_score": 0.3
    }
    ```
    """
    import time

    start = time.time()

    store = _get_vector_store()
    embedding = _get_embedding()

    if store.count() == 0:
        return KnowledgeQueryResponse(
            query=req.query,
            results=[],
            total_found=0,
            processing_time_ms=0,
            embedding_model=embedding._model,
        )

    # Generate query embedding
    emb_result = embedding.embed(req.query)

    # Search
    results = store.search(
        query_embedding=emb_result.embedding,
        top_k=req.top_k,
        species=req.species,
        topic=req.topic,
        source=req.source,
        min_score=req.min_score,
    )

    elapsed = (time.time() - start) * 1000

    return KnowledgeQueryResponse(
        query=req.query,
        results=[
            KnowledgeDocument(
                id=doc.id,
                text=doc.text[:500],  # Truncate for response size
                score=doc.score,
                source=doc.source,
                species=doc.species,
                topic=doc.topic,
                confidence=doc.confidence,
                disease_slug=doc.disease_slug,
                breed_slug=doc.breed_slug,
                is_emergency=doc.is_emergency,
                is_red_flag=doc.is_red_flag,
            )
            for doc in results
        ],
        total_found=len(results),
        processing_time_ms=round(elapsed, 1),
        embedding_model=emb_result.model,
    )


@router.get("/status", response_model=KnowledgeStatusResponse)
def knowledge_status() -> KnowledgeStatusResponse:
    """Get knowledge service status."""
    store = _get_vector_store()
    embedding = _get_embedding()

    return KnowledgeStatusResponse(
        status="ok",
        vector_store_loaded=store.count() > 0,
        total_documents=store.count(),
        embedding_available=embedding.available,
        embedding_model=embedding._model,
        dimensions=embedding.dimensions,
    )


@router.post("/reindex")
def knowledge_reindex() -> dict[str, Any]:
    """Trigger reindexing of the knowledge base from clinical data.

    Reads all disease/breed data from the knowledge base and rebuilds
    the vector store with embeddings.
    """
    import json
    import time

    from ..data_loader import load_knowledge_base

    start = time.time()
    store = _get_vector_store()
    embedding = _get_embedding()
    kb = load_knowledge_base()

    # Clear existing
    store.clear()

    # Index diseases
    doc_count = 0
    for disease in kb.diseases:
        slug = disease.get("slug", "")
        name = disease.get("name_id") or disease.get("name") or slug
        species = disease.get("category_slug", "")
        body_system = disease.get("body_system", "general")
        is_emergency = disease.get("is_emergency", False)

        # Create document text
        doc_text = f"{name}. "
        doc_text += " ".join(
            s.get("name_id") or s.get("name") or ""
            for s in disease.get("symptoms", [])
        )
        doc_text += ". "
        doc_text += disease.get("description", "")
        doc_text += ". "
        doc_text += " ".join(
            t.get("name", "")
            for t in disease.get("treatments", [])
        )

        # Generate embedding
        emb = embedding.embed(doc_text)

        doc = VectorDocument(
            id=f"disease_{slug}",
            text=doc_text,
            embedding=emb.embedding,
            source="disease",
            species=species,
            topic=body_system,
            disease_slug=slug,
            is_emergency=is_emergency,
            confidence=0.9,
            raw_data=disease,
        )
        store.add(doc)
        doc_count += 1

    # Save to disk
    store_path = ARTIFACTS_DIR / "vector_store.json"
    store.save(store_path)

    elapsed = time.time() - start
    logger.info("Reindexed %d documents in %.1fs", doc_count, elapsed)

    return {
        "status": "ok",
        "documents_indexed": doc_count,
        "processing_time_seconds": round(elapsed, 1),
        "embedding_model": embedding._model,
        "vector_store_path": str(store_path),
    }
