"""Vector store for RAG using numpy for cosine similarity.

Lightweight in-memory vector store that works without external dependencies.
Can be extended to ChromaDB, FAISS, or pgvector in production.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator


@dataclass
class VectorDocument:
    """A document with embedding and metadata for RAG retrieval."""

    id: str
    text: str
    embedding: list[float]
    score: float = 0.0  # Relevance score after search

    # Metadata for filtering
    source: str | None = None  # disease, breed, drug, nutrition, faq
    species: str | None = None  # dog, cat, rabbit, etc.
    topic: str | None = None  # digestive, skin, respiratory, etc.
    confidence: float = 1.0

    # Clinical metadata
    disease_slug: str | None = None
    breed_slug: str | None = None
    is_emergency: bool = False
    is_red_flag: bool = False

    # Raw source data for reference
    raw_data: dict[str, Any] | None = field(default=None, repr=False)

    created_at: datetime = field(default_factory=datetime.now)


class VectorStore:
    """In-memory vector store with cosine similarity search.

    Features:
    - Add/update/delete documents
    - Semantic search by embedding similarity
    - Filter by metadata (species, topic, source)
    - Save/load to JSON for persistence
    """

    def __init__(self, dimensions: int = 1536):
        self.dimensions = dimensions
        self._docs: dict[str, VectorDocument] = {}
        self._embeddings_matrix: list[list[float]] = []
        self._doc_ids: list[str] = []
        self._dirty = False

    def add(self, doc: VectorDocument) -> None:
        """Add or update a document in the store."""
        if len(doc.embedding) != self.dimensions:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dimensions}, "
                f"got {len(doc.embedding)}"
            )

        self._docs[doc.id] = doc
        self._dirty = True

    def add_batch(self, docs: list[VectorDocument]) -> int:
        """Add multiple documents. Returns count added."""
        count = 0
        for doc in docs:
            self.add(doc)
            count += 1
        return count

    def get(self, doc_id: str) -> VectorDocument | None:
        """Get a document by ID."""
        return self._docs.get(doc_id)

    def delete(self, doc_id: str) -> bool:
        """Delete a document by ID. Returns True if existed."""
        if doc_id in self._docs:
            del self._docs[doc_id]
            self._dirty = True
            return True
        return False

    def _rebuild_index(self) -> None:
        """Rebuild the internal index for fast search."""
        if not self._dirty:
            return

        self._embeddings_matrix = []
        self._doc_ids = []

        for doc_id, doc in self._docs.items():
            self._embeddings_matrix.append(doc.embedding)
            self._doc_ids.append(doc_id)

        self._dirty = False

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        *,
        species: str | None = None,
        topic: str | None = None,
        source: str | None = None,
        is_emergency: bool | None = None,
        min_score: float = 0.0,
    ) -> list[VectorDocument]:
        """Search for similar documents using cosine similarity.

        Args:
            query_embedding: Embedding of the search query
            top_k: Maximum number of results to return
            species: Filter by species (dog, cat, etc.)
            topic: Filter by topic (digestive, skin, etc.)
            source: Filter by source type (disease, breed, drug, etc.)
            is_emergency: Filter by emergency flag
            min_score: Minimum similarity score (0.0 to 1.0)

        Returns:
            List of VectorDocument sorted by relevance (descending)
        """
        if len(query_embedding) != self.dimensions:
            raise ValueError(
                f"Query embedding dimension mismatch: expected {self.dimensions}, "
                f"got {len(query_embedding)}"
            )

        self._rebuild_index()

        if not self._embeddings_matrix:
            return []

        # Calculate cosine similarities
        scores = self._cosine_similarities(query_embedding, self._embeddings_matrix)

        # Build results with filtering
        results: list[VectorDocument] = []

        for i, (doc_id, score) in enumerate(zip(self._doc_ids, scores)):
            if score < min_score:
                continue

            doc = self._docs[doc_id]

            # Apply filters
            if species is not None and doc.species != species:
                continue
            if topic is not None and doc.topic != topic:
                continue
            if source is not None and doc.source != source:
                continue
            if is_emergency is not None and doc.is_emergency != is_emergency:
                continue

            # Create result with score
            result_doc = VectorDocument(
                id=doc.id,
                text=doc.text,
                embedding=doc.embedding,
                score=score,
                source=doc.source,
                species=doc.species,
                topic=doc.topic,
                confidence=doc.confidence,
                disease_slug=doc.disease_slug,
                breed_slug=doc.breed_slug,
                is_emergency=doc.is_emergency,
                is_red_flag=doc.is_red_flag,
                raw_data=doc.raw_data,
                created_at=doc.created_at,
            )
            results.append(result_doc)

        # Sort by score descending
        results.sort(key=lambda d: d.score, reverse=True)

        return results[:top_k]

    def _cosine_similarities(
        self, query: list[float], matrix: list[list[float]]
    ) -> list[float]:
        """Calculate cosine similarity between query and all vectors in matrix.

        Using pure Python for portability - no numpy required.
        """
        # Normalize query vector first
        query_norm = math.sqrt(sum(x * x for x in query))
        if query_norm == 0:
            return [0.0] * len(matrix)

        normalized_query = [x / query_norm for x in query]

        similarities: list[float] = []
        for vec in matrix:
            # Dot product with normalized vectors = cosine similarity
            vec_norm = math.sqrt(sum(x * x for x in vec))
            if vec_norm == 0:
                similarities.append(0.0)
                continue

            dot = sum(a * b for a, b in zip(normalized_query, (x / vec_norm for x in vec)))
            # Clamp to [0, 1] range
            similarities.append(max(0.0, min(1.0, dot)))

        return similarities

    def count(self) -> int:
        """Return total number of documents."""
        return len(self._docs)

    def stats(self) -> dict[str, Any]:
        """Return statistics about the vector store."""
        sources: dict[str, int] = {}
        species_counts: dict[str, int] = {}
        topics: dict[str, int] = {}
        emergency_count = 0

        for doc in self._docs.values():
            if doc.source:
                sources[doc.source] = sources.get(doc.source, 0) + 1
            if doc.species:
                species_counts[doc.species] = species_counts.get(doc.species, 0) + 1
            if doc.topic:
                topics[doc.topic] = topics.get(doc.topic, 0) + 1
            if doc.is_emergency:
                emergency_count += 1

        return {
            "total_documents": len(self._docs),
            "dimensions": self.dimensions,
            "by_source": sources,
            "by_species": species_counts,
            "by_topic": topics,
            "emergency_documents": emergency_count,
        }

    def iter_docs(self) -> Iterator[VectorDocument]:
        """Iterate over all documents."""
        yield from self._docs.values()

    def save(self, path: Path | str) -> None:
        """Save vector store to JSON file.

        Note: Embeddings are stored, so file can be large.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data: dict[str, Any] = {
            "dimensions": self.dimensions,
            "documents": [],
        }

        for doc in self._docs.values():
            doc_dict = {
                "id": doc.id,
                "text": doc.text,
                "embedding": doc.embedding,
                "source": doc.source,
                "species": doc.species,
                "topic": doc.topic,
                "confidence": doc.confidence,
                "disease_slug": doc.disease_slug,
                "breed_slug": doc.breed_slug,
                "is_emergency": doc.is_emergency,
                "is_red_flag": doc.is_red_flag,
                "raw_data": doc.raw_data,
                "created_at": doc.created_at.isoformat(),
            }
            data["documents"].append(doc_dict)

        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: Path | str) -> VectorStore:
        """Load vector store from JSON file."""
        path = Path(path)

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        store = cls(dimensions=data["dimensions"])

        for doc_dict in data["documents"]:
            doc = VectorDocument(
                id=doc_dict["id"],
                text=doc_dict["text"],
                embedding=doc_dict["embedding"],
                source=doc_dict.get("source"),
                species=doc_dict.get("species"),
                topic=doc_dict.get("topic"),
                confidence=doc_dict.get("confidence", 1.0),
                disease_slug=doc_dict.get("disease_slug"),
                breed_slug=doc_dict.get("breed_slug"),
                is_emergency=doc_dict.get("is_emergency", False),
                is_red_flag=doc_dict.get("is_red_flag", False),
                raw_data=doc_dict.get("raw_data"),
                created_at=(
                    datetime.fromisoformat(doc_dict["created_at"])
                    if doc_dict.get("created_at")
                    else datetime.now()
                ),
            )
            store.add(doc)

        return store

    def clear(self) -> None:
        """Remove all documents."""
        self._docs.clear()
        self._embeddings_matrix.clear()
        self._doc_ids.clear()
        self._dirty = True
