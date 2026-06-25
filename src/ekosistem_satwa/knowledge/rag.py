"""Main RAG service for veterinary knowledge retrieval.

Integrates:
- EmbeddingService for generating embeddings
- VectorStore for similarity search
- KnowledgeBase for document ingestion

Provides semantic search over:
- Disease clinical data (symptoms, diagnostics, treatments)
- Breed information (traits, predispositions)
- Medication/drug database
- Nutrition guidelines
- FAQ
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..config import AISettings, GENERATED_DIR
from ..data_loader import KnowledgeBase, load_knowledge_base
from .embeddings import EmbeddingService, EmbeddingResult
from .vector_store import VectorDocument, VectorStore

logger = logging.getLogger("ekosistem_satwa.knowledge.rag")


@dataclass
class RAGSearchResult:
    """Result from a RAG semantic search query."""

    query_text: str
    top_k: int
    results: list[VectorDocument]
    total_found: int

    # Metadata about the query
    species_filter: str | None = None
    topic_filter: str | None = None
    source_filter: str | None = None

    def to_prompt_context(self, max_chars_per_doc: int = 1500) -> str:
        """Format results as context string for LLM prompt."""
        if not self.results:
            return "No relevant knowledge found."

        sections: list[str] = []

        for i, doc in enumerate(self.results[:self.top_k]):
            # Build header with metadata
            header_parts = [f"[{i+1}]"]
            if doc.species:
                header_parts.append(f"Species: {doc.species}")
            if doc.source:
                header_parts.append(f"Type: {doc.source}")
            if doc.topic:
                header_parts.append(f"Topic: {doc.topic}")
            if doc.is_emergency:
                header_parts.append("⚠️ EMERGENCY")
            header_parts.append(f"(relevance: {doc.score:.2f})")

            header = " | ".join(header_parts)

            # Truncate text if too long
            text = doc.text
            if len(text) > max_chars_per_doc:
                text = text[:max_chars_per_doc] + "..."

            sections.append(f"{header}\n{text}")

        return "\n\n---\n\n".join(sections)


class KnowledgeRAGService:
    """RAG service for veterinary clinical knowledge.

    Usage:
        rag = KnowledgeRAGService()
        rag.ingest_knowledge_base()  # Load all KB data into vector store

        # Search
        result = rag.search(
            query_text="Anjing muntah dan diare berdarah",
            species="dog",
            top_k=5
        )

        # Use in prompt
        context = result.to_prompt_context()
    """

    def __init__(
        self,
        kb: KnowledgeBase | None = None,
        embedding_service: EmbeddingService | None = None,
        settings: AISettings | None = None,
        persist_path: Path | str | None = None,
    ):
        self.settings = settings or AISettings()
        self.kb = kb or load_knowledge_base()
        self.embedding = embedding_service or EmbeddingService(self.settings)

        # Determine vector store dimensions based on embedding service
        self._dimensions = self.embedding.dimensions
        self.vector_store = VectorStore(dimensions=self._dimensions)

        # Persistence path
        if persist_path is None:
            persist_path = GENERATED_DIR / "rag_vector_store.json"
        self.persist_path = Path(persist_path)

        self._ingested = False
        self._total_embedding_tokens = 0

    @property
    def is_ingested(self) -> bool:
        return self._ingested

    @property
    def stats(self) -> dict[str, Any]:
        vs_stats = self.vector_store.stats()
        return {
            **vs_stats,
            "embedding_model": self.embedding._model,
            "embedding_available": self.embedding.available,
            "total_embedding_tokens_used": self._total_embedding_tokens,
            "persist_path": str(self.persist_path),
        }

    def ingest_knowledge_base(
        self,
        force_rebuild: bool = False,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
    ) -> int:
        """Ingest all documents from KnowledgeBase into vector store.

        Args:
            force_rebuild: If True, rebuild even if persisted store exists
            chunk_size: Target size for text chunks
            chunk_overlap: Overlap between consecutive chunks

        Returns:
            Number of documents ingested
        """
        # Try to load persisted store first
        if not force_rebuild and self.persist_path.exists():
            try:
                logger.info("Loading persisted vector store from %s", self.persist_path)
                loaded = VectorStore.load(self.persist_path)
                if loaded.count() > 0:
                    self.vector_store = loaded
                    self._ingested = True
                    logger.info("Loaded %d documents from persisted store", loaded.count())
                    return loaded.count()
            except Exception as exc:
                logger.warning("Failed to load persisted store: %s", exc)

        # Clear and rebuild
        self.vector_store.clear()

        total = 0

        # Ingest diseases
        total += self._ingest_diseases(chunk_size, chunk_overlap)

        # Ingest breeds
        total += self._ingest_breeds(chunk_size, chunk_overlap)

        # Ingest medication database
        total += self._ingest_medications(chunk_size, chunk_overlap)

        # Save to disk
        try:
            self.vector_store.save(self.persist_path)
            logger.info("Persisted vector store to %s", self.persist_path)
        except Exception as exc:
            logger.warning("Failed to persist vector store: %s", exc)

        self._ingested = True
        logger.info("Ingested total %d documents into RAG store", total)
        return total

    def _ingest_diseases(self, chunk_size: int, chunk_overlap: int) -> int:
        """Ingest disease clinical data."""
        count = 0

        for disease in self.kb.diseases:
            species = disease.get("category_slug")
            disease_slug = disease.get("slug")

            # Build document text from disease data
            name_id = disease.get("name_id") or disease.get("name") or disease_slug
            name_en = disease.get("name")

            sections: list[str] = []

            # Header
            header = f"DISEASE: {name_id}"
            if name_en and name_en != name_id:
                header += f" ({name_en})"
            sections.append(header)

            # Overview and clinical info
            if disease.get("overview"):
                sections.append(f"OVERVIEW: {disease['overview']}")
            if disease.get("default_severity"):
                sections.append(f"SEVERITY: {disease['default_severity']}")
            if disease.get("is_emergency"):
                sections.append("⚠️ THIS IS AN EMERGENCY CONDITION")
            if disease.get("etiology"):
                sections.append(f"ETIOLOGY: {disease['etiology']}")
            if disease.get("body_system"):
                sections.append(f"BODY SYSTEM: {disease['body_system']}")

            # Symptoms
            symptoms = disease.get("symptoms", [])
            if symptoms:
                symptom_texts = []
                for s in symptoms:
                    parts = []
                    if s.get("name_id"):
                        parts.append(s["name_id"])
                    if s.get("is_red_flag"):
                        parts.append("[RED FLAG]")
                    if s.get("frequency"):
                        parts.append(f"(frequency: {s.get('frequency')})")
                    symptom_texts.append(" ".join(parts))
                sections.append("SYMPTOMS: " + "; ".join(symptom_texts))

            # Causes and prevention
            if disease.get("causes"):
                sections.append(f"CAUSES: {disease['causes']}")
            if disease.get("prevention"):
                sections.append(f"PREVENTION: {disease['prevention']}")
            if disease.get("prognosis"):
                sections.append(f"PROGNOSIS: {disease['prognosis']}")

            # Diagnostics
            diagnostics = disease.get("diagnostics", [])
            if diagnostics:
                diag_texts = []
                for d in diagnostics:
                    parts = []
                    if d.get("name"):
                        parts.append(d["name"])
                    if d.get("is_gold_standard"):
                        parts.append("[GOLD STANDARD]")
                    if d.get("expected_finding"):
                        parts.append(f"- {d['expected_finding']}")
                    diag_texts.append(" ".join(parts))
                sections.append("DIAGNOSTICS: " + "; ".join(diag_texts))

            # Treatments
            treatments = disease.get("treatments", [])
            for tx in treatments:
                tx_parts = [f"TREATMENT (line {tx.get('line_of_therapy', 1)}):"]
                if tx.get("name"):
                    tx_parts.append(tx["name"])
                if tx.get("recommendation"):
                    tx_parts.append(f"Recommendation: {tx['recommendation']}")
                if tx.get("procedure_steps"):
                    tx_parts.append(f"Procedure: {tx['procedure_steps']}")

                # Products/medications
                products = tx.get("products", [])
                if products:
                    prod_texts = []
                    for p in products:
                        p_parts = []
                        if p.get("name"):
                            p_parts.append(p["name"])
                        if p.get("active_ingredient"):
                            p_parts.append(f"({p['active_ingredient']})")
                        if p.get("dosage_guide"):
                            p_parts.append(f"Dosage: {p['dosage_guide']}")
                        if p.get("route"):
                            p_parts.append(f"Route: {p['route']}")
                        if p.get("cautions"):
                            p_parts.append(f"CAUTION: {p['cautions']}")
                        prod_texts.append(" ".join(p_parts))
                    tx_parts.append("Medications: " + "; ".join(prod_texts))

                sections.append(" ".join(tx_parts))

            # Breed susceptibility
            suscept = disease.get("breed_susceptibility", [])
            if suscept:
                sus_texts = []
                for s in suscept:
                    parts = []
                    if s.get("breed_slug"):
                        parts.append(s["breed_slug"])
                    if s.get("risk"):
                        parts.append(f"risk: {s['risk']}")
                    if s.get("prevalence_pct"):
                        parts.append(f"prevalence: {s['prevalence_pct']}%")
                    sus_texts.append(" ".join(parts))
                sections.append("BREED SUSCEPTIBILITY: " + "; ".join(sus_texts))

            # Combine and chunk
            full_text = "\n".join(sections)

            # Determine topic from body_system
            topic = disease.get("body_system")

            chunks = self._chunk_text(full_text, chunk_size, chunk_overlap)

            for i, chunk in enumerate(chunks):
                doc_id = f"disease_{disease_slug}_{i}"

                # Generate embedding
                emb_result = self.embedding.embed(chunk)
                self._total_embedding_tokens += emb_result.tokens_used

                doc = VectorDocument(
                    id=doc_id,
                    text=chunk,
                    embedding=emb_result.embedding,
                    source="disease",
                    species=species,
                    topic=topic,
                    confidence=1.0,
                    disease_slug=disease_slug,
                    is_emergency=bool(disease.get("is_emergency", False)),
                    raw_data={
                        "name_id": name_id,
                        "name_en": name_en,
                        "severity": disease.get("default_severity"),
                    },
                )
                self.vector_store.add(doc)
                count += 1

        logger.info("Ingested %d disease document chunks", count)
        return count

    def _ingest_breeds(self, chunk_size: int, chunk_overlap: int) -> int:
        """Ingest breed information."""
        count = 0

        for breed in self.kb.breeds:
            species = breed.get("category_slug")
            breed_slug = breed.get("slug")

            name_id = breed.get("name_id") or breed.get("name") or breed_slug

            sections: list[str] = [f"BREED: {name_id} ({breed_slug})"]

            if breed.get("origin_country"):
                sections.append(f"ORIGIN: {breed['origin_country']}")
            if breed.get("size_class"):
                sections.append(f"SIZE CLASS: {breed['size_class']}")
            if breed.get("care_level"):
                sections.append(f"CARE LEVEL: {breed['care_level']}")
            if breed.get("lifespan_years"):
                sections.append(f"LIFESPAN: {breed['lifespan_years']} years")

            # Traits
            traits = breed.get("traits", [])
            if traits:
                trait_texts = []
                for t in traits:
                    if isinstance(t, dict):
                        name = t.get("name_id") or t.get("name")
                        if name:
                            level = t.get("level") or t.get("value")
                            if level:
                                trait_texts.append(f"{name}: {level}")
                            else:
                                trait_texts.append(name)
                    elif isinstance(t, str):
                        trait_texts.append(t)
                if trait_texts:
                    sections.append("TRAITS: " + "; ".join(trait_texts))

            # Common diseases for this breed
            common_diseases = self.kb.diseases_for_breed(breed_slug or "")
            if common_diseases:
                disease_texts = []
                for d in common_diseases:
                    parts = [str(d.get("name_id") or d.get("name") or d.get("slug", ""))]
                    risk = d.get("_risk")
                    if risk:
                        parts.append(f"(risk: {risk})")
                    prev = d.get("_prevalence_pct")
                    if prev:
                        parts.append(f"({prev}% prevalence)")
                    disease_texts.append(" ".join(parts))
                sections.append("PREDISPOSED DISEASES: " + "; ".join(disease_texts))

            full_text = "\n".join(sections)
            chunks = self._chunk_text(full_text, chunk_size, chunk_overlap)

            for i, chunk in enumerate(chunks):
                doc_id = f"breed_{breed_slug}_{i}"

                emb_result = self.embedding.embed(chunk)
                self._total_embedding_tokens += emb_result.tokens_used

                doc = VectorDocument(
                    id=doc_id,
                    text=chunk,
                    embedding=emb_result.embedding,
                    source="breed",
                    species=species,
                    topic="breed_info",
                    confidence=1.0,
                    breed_slug=breed_slug,
                    raw_data={
                        "name_id": name_id,
                        "size_class": breed.get("size_class"),
                        "care_level": breed.get("care_level"),
                    },
                )
                self.vector_store.add(doc)
                count += 1

        logger.info("Ingested %d breed document chunks", count)
        return count

    def _ingest_medications(self, chunk_size: int, chunk_overlap: int) -> int:
        """Ingest medication/drug database."""
        # TODO: Load from medication_kb.json and ingest
        # For now, medication info is already embedded in disease treatments
        count = 0
        return count

    def _chunk_text(
        self, text: str, chunk_size: int, chunk_overlap: int
    ) -> list[str]:
        """Split text into overlapping chunks.

        Simple paragraph-aware chunking.
        """
        if len(text) <= chunk_size:
            return [text]

        chunks: list[str] = []
        paragraphs = text.split("\n\n")

        current_chunk = ""
        current_length = 0

        for para in paragraphs:
            para_len = len(para)

            if current_length + para_len <= chunk_size:
                # Add to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                    current_length += 2 + para_len
                else:
                    current_chunk = para
                    current_length = para_len
            else:
                # Save current chunk and start new one with overlap
                if current_chunk:
                    chunks.append(current_chunk)

                    # Get last portion for overlap
                    # Take last chunk_overlap chars or last paragraph
                    if len(current_chunk) > chunk_overlap:
                        overlap_start = len(current_chunk) - chunk_overlap
                        # Try to find a paragraph boundary
                        last_newline = current_chunk.rfind("\n\n", overlap_start)
                        if last_newline != -1:
                            current_chunk = current_chunk[last_newline + 2:]
                            current_length = len(current_chunk)
                        else:
                            current_chunk = current_chunk[overlap_start:]
                            current_length = len(current_chunk)
                    else:
                        current_length = len(current_chunk)
                else:
                    # Single long paragraph - split by sentences
                    # Fallback: just take what fits
                    chunks.append(para[:chunk_size])
                    current_chunk = para[chunk_size - chunk_overlap:] if chunk_size > chunk_overlap else ""
                    current_length = len(current_chunk)

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def search(
        self,
        query_text: str,
        species: str | None = None,
        topic: str | None = None,
        source: str | None = None,
        top_k: int = 5,
        min_score: float = 0.3,
    ) -> RAGSearchResult:
        """Semantic search over the knowledge base.

        Args:
            query_text: Natural language query
            species: Filter by species (dog, cat, rabbit, etc.)
            topic: Filter by topic (digestive, skin, etc.)
            source: Filter by source type (disease, breed, drug)
            top_k: Maximum results to return
            min_score: Minimum similarity threshold (0.0 to 1.0)

        Returns:
            RAGSearchResult with ranked documents
        """
        if not self._ingested:
            logger.warning("RAG store not ingested. Run ingest_knowledge_base() first.")
            return RAGSearchResult(
                query_text=query_text,
                top_k=top_k,
                results=[],
                total_found=0,
                species_filter=species,
                topic_filter=topic,
                source_filter=source,
            )

        # Embed the query
        emb_result = self.embedding.embed(query_text)

        # Search
        results = self.vector_store.search(
            emb_result.embedding,
            top_k=top_k * 2,  # Get extra for filtering
            species=species,
            topic=topic,
            source=source,
            min_score=min_score,
        )

        return RAGSearchResult(
            query_text=query_text,
            top_k=top_k,
            results=results[:top_k],
            total_found=len(results),
            species_filter=species,
            topic_filter=topic,
            source_filter=source,
        )


# Singleton instance for API
_rag_service: KnowledgeRAGService | None = None


def get_rag_service(
    kb: KnowledgeBase | None = None,
    auto_ingest: bool = True,
    force_rebuild: bool = False,
) -> KnowledgeRAGService:
    """Get or create the singleton RAG service.

    Args:
        kb: Optional KnowledgeBase instance
        auto_ingest: If True, automatically ingest on first call
        force_rebuild: If True, rebuild vector store even if persisted
    """
    global _rag_service

    if _rag_service is None:
        _rag_service = KnowledgeRAGService(kb=kb)

        if auto_ingest and not _rag_service.is_ingested:
            _rag_service.ingest_knowledge_base(force_rebuild=force_rebuild)

    return _rag_service
