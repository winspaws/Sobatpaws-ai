"""Unit tests for RAG knowledge service.

Tests for vector store, embeddings, and document chunking.
Uses fallback embeddings (hash-based) so tests work offline.
"""
from __future__ import annotations

import math
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ekosistem_satwa.knowledge.embeddings import (
    DEFAULT_EMBEDDING_DIM,
    EmbeddingResult,
    EmbeddingService,
    FALLBACK_EMBEDDING_DIM,
)
from ekosistem_satwa.knowledge.vector_store import VectorDocument, VectorStore


class TestEmbeddingService:
    """Tests for embedding service."""

    def test_embedding_service_initialization(self):
        """Test service initializes correctly."""
        service = EmbeddingService()
        assert service is not None
        assert service.dimensions in [DEFAULT_EMBEDDING_DIM, FALLBACK_EMBEDDING_DIM]

    def test_fallback_embedding_generation(self):
        """Test hash-based fallback embeddings work offline."""
        service = EmbeddingService()

        # Test with simple text
        result = service.embed("test veterinary query")

        assert result is not None
        assert len(result.embedding) == FALLBACK_EMBEDDING_DIM
        assert result.model == "hash-fallback"

        # Embedding should be normalized (unit length)
        norm = math.sqrt(sum(x * x for x in result.embedding))
        assert abs(norm - 1.0) < 0.001

    def test_embedding_deterministic(self):
        """Test same text gives same embedding."""
        service = EmbeddingService()

        text = "Anjing dengan gejala muntah dan diare"
        result1 = service.embed(text)
        result2 = service.embed(text)

        # Should be identical
        assert result1.embedding == result2.embedding

    def test_embedding_caching(self):
        """Test caching works for repeated embeddings."""
        service = EmbeddingService()

        text = "test caching"
        result1 = service.embed(text)
        assert not result1.from_cache

        result2 = service.embed(text)
        assert result2.from_cache
        assert result2.tokens_used == 0

    def test_different_texts_different_embeddings(self):
        """Test different texts produce different embeddings."""
        service = EmbeddingService()

        text1 = "dog vomiting diarrhea"
        text2 = "cat skin infection scratching"

        result1 = service.embed(text1)
        result2 = service.embed(text2)

        # Cosine similarity should be less for different texts
        def cos_sim(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            return dot

        same_text_sim = cos_sim(result1.embedding, service.embed(text1).embedding)
        diff_text_sim = cos_sim(result1.embedding, result2.embedding)

        # Same text should have perfect similarity
        assert abs(same_text_sim - 1.0) < 0.001
        # Different texts should have lower similarity
        assert diff_text_sim < 0.95


class TestVectorStore:
    """Tests for in-memory vector store."""

    def test_vector_store_initialization(self):
        """Test store initializes correctly."""
        store = VectorStore(dimensions=64)
        assert store is not None
        assert store.dimensions == 64
        assert store.count() == 0

    def test_add_and_get_document(self):
        """Test adding and retrieving documents."""
        store = VectorStore(dimensions=32)

        doc = VectorDocument(
            id="test-001",
            text="Canine parvovirus causes vomiting and bloody diarrhea",
            embedding=[0.1] * 32,
            species="dog",
            topic="digestive",
            source="disease",
            is_emergency=True,
        )

        store.add(doc)
        assert store.count() == 1

        retrieved = store.get("test-001")
        assert retrieved is not None
        assert retrieved.id == "test-001"
        assert retrieved.text == doc.text
        assert retrieved.species == "dog"
        assert retrieved.is_emergency is True

    def test_delete_document(self):
        """Test deleting documents."""
        store = VectorStore(dimensions=16)

        store.add(VectorDocument(
            id="del-001",
            text="to delete",
            embedding=[0.5] * 16,
        ))

        assert store.count() == 1
        assert store.delete("del-001") is True
        assert store.count() == 0
        assert store.delete("del-001") is False

    def test_basic_similarity_search(self):
        """Test cosine similarity search works."""
        store = VectorStore(dimensions=4)

        # Add test documents with simple vectors
        # Doc A: [1, 0, 0, 0] - pointing along X
        # Doc B: [0, 1, 0, 0] - pointing along Y
        # Doc C: [0.707, 0.707, 0, 0] - pointing midway

        def normalize(v: list[float]) -> list[float]:
            norm = math.sqrt(sum(x * x for x in v))
            return [x / norm for x in v] if norm > 0 else v

        store.add(VectorDocument(
            id="doc-x",
            text="Document X axis",
            embedding=normalize([1.0, 0.0, 0.0, 0.0]),
            source="test",
        ))
        store.add(VectorDocument(
            id="doc-y",
            text="Document Y axis",
            embedding=normalize([0.0, 1.0, 0.0, 0.0]),
            source="test",
        ))
        store.add(VectorDocument(
            id="doc-xy",
            text="Document mid axis",
            embedding=normalize([1.0, 1.0, 0.0, 0.0]),
            source="test",
        ))

        # Search with X axis query
        results = store.search(
            query_embedding=normalize([1.0, 0.0, 0.0, 0.0]),
            top_k=3,
        )

        assert len(results) == 3
        # doc-x should be most similar (score ~1.0)
        assert results[0].id == "doc-x"
        assert results[0].score > 0.99
        # doc-xy should be next (~0.707)
        assert results[1].id == "doc-xy"
        # doc-y should be last (~0.0)
        assert results[2].id == "doc-y"

    def test_search_with_species_filter(self):
        """Test search filtering by species."""
        store = VectorStore(dimensions=8)

        docs = [
            VectorDocument(
                id="dog-1",
                text="Dog disease A",
                embedding=[0.1] * 8,
                species="dog",
                topic="digestive",
            ),
            VectorDocument(
                id="cat-1",
                text="Cat disease A",
                embedding=[0.1] * 8,
                species="cat",
                topic="skin",
            ),
            VectorDocument(
                id="dog-2",
                text="Dog disease B",
                embedding=[0.2] * 8,
                species="dog",
                topic="respiratory",
            ),
        ]

        for doc in docs:
            store.add(doc)

        # Search with dog filter
        results = store.search(
            query_embedding=[0.15] * 8,
            top_k=10,
            species="dog",
        )

        assert len(results) == 2
        result_ids = {r.id for r in results}
        assert "dog-1" in result_ids
        assert "dog-2" in result_ids
        assert "cat-1" not in result_ids

    def test_search_with_source_filter(self):
        """Test search filtering by source type."""
        store = VectorStore(dimensions=8)

        store.add(VectorDocument(
            id="disease-001",
            text="Parvovirus info",
            embedding=[0.1] * 8,
            source="disease",
        ))
        store.add(VectorDocument(
            id="breed-001",
            text="Golden retriever info",
            embedding=[0.1] * 8,
            source="breed",
        ))

        results = store.search(
            query_embedding=[0.1] * 8,
            top_k=10,
            source="disease",
        )

        assert len(results) == 1
        assert results[0].id == "disease-001"

    def test_search_with_emergency_filter(self):
        """Test search filtering by emergency flag."""
        store = VectorStore(dimensions=8)

        store.add(VectorDocument(
            id="emergency-001",
            text="Parvovirus - emergency",
            embedding=[0.1] * 8,
            is_emergency=True,
        ))
        store.add(VectorDocument(
            id="routine-001",
            text="Ear mites - routine",
            embedding=[0.1] * 8,
            is_emergency=False,
        ))

        results = store.search(
            query_embedding=[0.1] * 8,
            top_k=10,
            is_emergency=True,
        )

        assert len(results) == 1
        assert results[0].id == "emergency-001"

    def test_stats(self):
        """Test store statistics."""
        store = VectorStore(dimensions=16)

        store.add(VectorDocument(
            id="s1",
            text="Dog digestive disease",
            embedding=[0.1] * 16,
            species="dog",
            topic="digestive",
            source="disease",
            is_emergency=True,
        ))
        store.add(VectorDocument(
            id="s2",
            text="Cat skin disease",
            embedding=[0.2] * 16,
            species="cat",
            topic="skin",
            source="disease",
            is_emergency=False,
        ))

        stats = store.stats()

        assert stats["total_documents"] == 2
        assert stats["dimensions"] == 16
        assert stats["by_source"]["disease"] == 2
        assert stats["by_species"]["dog"] == 1
        assert stats["by_species"]["cat"] == 1
        assert stats["by_topic"]["digestive"] == 1
        assert stats["by_topic"]["skin"] == 1
        assert stats["emergency_documents"] == 1

    def test_clear(self):
        """Test clearing the store."""
        store = VectorStore(dimensions=8)

        store.add(VectorDocument(
            id="test",
            text="test",
            embedding=[0.1] * 8,
        ))

        assert store.count() == 1
        store.clear()
        assert store.count() == 0

    def test_save_and_load(self):
        """Test persisting and loading vector store."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_store.json"

            # Create and save
            store1 = VectorStore(dimensions=8)
            store1.add(VectorDocument(
                id="saved-doc",
                text="Saved document",
                embedding=[0.5, 0.3, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0],
                species="dog",
                source="disease",
                is_emergency=True,
            ))
            store1.save(path)

            # Load in new instance
            store2 = VectorStore.load(path)

            assert store2.count() == 1
            doc = store2.get("saved-doc")
            assert doc is not None
            assert doc.text == "Saved document"
            assert doc.species == "dog"
            assert doc.is_emergency is True

    def test_iter_docs(self):
        """Test iterating over documents."""
        store = VectorStore(dimensions=4)

        ids = {"a", "b", "c"}
        for doc_id in ids:
            store.add(VectorDocument(
                id=doc_id,
                text=f"Document {doc_id}",
                embedding=[0.1] * 4,
            ))

        retrieved_ids = {doc.id for doc in store.iter_docs()}
        assert retrieved_ids == ids


class TestVectorDocument:
    """Tests for VectorDocument dataclass."""

    def test_document_creation(self):
        """Test document creation with all fields."""
        doc = VectorDocument(
            id="test-doc-123",
            text="Clinical information about a disease",
            embedding=[0.1, 0.2, 0.3, 0.4],
            score=0.95,
            source="disease",
            species="dog",
            topic="digestive",
            confidence=1.0,
            disease_slug="dog-parvovirus",
            breed_slug=None,
            is_emergency=True,
            is_red_flag=False,
            raw_data={"name": "Parvovirus", "severity": "critical"},
        )

        assert doc.id == "test-doc-123"
        assert doc.text == "Clinical information about a disease"
        assert len(doc.embedding) == 4
        assert doc.score == 0.95
        assert doc.source == "disease"
        assert doc.species == "dog"
        assert doc.is_emergency is True

    def test_document_defaults(self):
        """Test document default values."""
        doc = VectorDocument(
            id="minimal",
            text="Minimal doc",
            embedding=[0.5],
        )

        assert doc.score == 0.0
        assert doc.source is None
        assert doc.species is None
        assert doc.confidence == 1.0
        assert doc.is_emergency is False
        assert doc.is_red_flag is False
