"""RAG (Retrieval-Augmented Generation) knowledge service for veterinary clinical data.

Provides:
- Embedding service (OpenAI or local fallback)
- Vector store (in-memory numpy-based, extensible to ChromaDB/pgvector)
- Document ingestion from KnowledgeBase JSON
- Semantic retrieval with metadata filtering (species, topic)
"""

from .rag import KnowledgeRAGService, get_rag_service
from .embeddings import EmbeddingService
from .vector_store import VectorStore, VectorDocument

__all__ = [
    "KnowledgeRAGService",
    "get_rag_service",
    "EmbeddingService",
    "VectorStore",
    "VectorDocument",
]
