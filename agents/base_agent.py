"""Base agent class with shared retrieval logic.

All domain agents (Mechanical, Software, Support) inherit from BaseAgent.
Implements:
- Collection initialization and connection
- Top-K retrieval with reranking
- Cosine similarity filtering (FR-ORCH-007: < 0.4 → insufficient context)
- Citation tracking (FR-ORCH-006: source_document + chunk_id)
- Structured result formatting
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from sentence_transformers import CrossEncoder

from ingestion.config import load_config


@dataclass
class RetrievalResult:
    """Single retrieved result with metadata and citation."""

    chunk_id: str
    source_document: str
    content: str
    similarity_score: float
    metadata: dict[str, Any]
    rerank_score: float | None = None


@dataclass
class AgentResponse:
    """Structured response from an agent."""

    query: str
    domain: str
    results: list[RetrievalResult]
    total_count: int
    insufficient_context: bool = False
    error: str | None = None


class BaseAgent(ABC):
    """Abstract base for domain-specific retrieval agents.

    Enforces collection isolation (DR-005) and implements shared retrieval logic
    (DR-004: embeddings, reranking, similarity filtering, citation tracking).
    """

    def __init__(self, domain: str, collection_name: str):
        """Initialize agent with domain and collection name.

        Args:
            domain: Agent domain (mechanical, software, support)
            collection_name: ChromaDB collection name
        """
        self.domain = domain
        self.collection_name = collection_name
        self._config = load_config()
        self._client = self._get_client()
        self._collection = self._get_collection()
        self._embedder = self._get_embedder()
        self._reranker = self._get_reranker()

    def _get_client(self) -> chromadb.PersistentClient:
        """Get ChromaDB client."""
        from pathlib import Path
        persist_dir = Path(
            __file__
        ).resolve().parent.parent / self._config["paths"]["chroma_persist_dir"]
        return chromadb.PersistentClient(
            path=str(persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )

    def _get_collection(self):
        """Get or retrieve collection. Raises if not found."""
        try:
            return self._client.get_collection(name=self.collection_name)
        except Exception as exc:
            raise ValueError(
                f"Collection '{self.collection_name}' not found. "
                f"Run ingestion pipeline first."
            ) from exc

    def _get_embedder(self) -> OpenAIEmbeddings:
        """Get OpenAI embeddings (DR-004: text-embedding-3-small)."""
        cfg = self._config["embeddings"]
        return OpenAIEmbeddings(model=cfg["model"])

    def _get_reranker(self) -> CrossEncoder:
        """Get cross-encoder reranker (FR-MECH-007)."""
        return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    @abstractmethod
    def _build_where_filter(self, **kwargs) -> dict | None:
        """Build metadata where filter for domain-specific constraints.

        Subclasses override to add subsystem, severity, status filters, etc.
        Return None if no filtering.
        """
        pass

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict | None = None,
    ) -> AgentResponse:
        """Retrieve results from collection with reranking and filtering.

        DR-005: Collection isolation enforced (reads only own collection).
        DR-004: Uses OpenAI embeddings.
        FR-ORCH-006: Tracks citations (source_document + chunk_id).
        FR-ORCH-007: Filters similarity < 0.4.

        Args:
            query: User query string
            top_k: Number of results (default from config pre-rerank)
            filters: Domain-specific metadata filters

        Returns:
            AgentResponse with results and metadata
        """
        if top_k is None:
            top_k = self._config["retrieval"]["top_k_retrieval"]

        try:
            # Embed query
            query_embedding = self._embedder.embed_query(query)

            # Build where filter from domain-specific constraints
            where = self._build_where_filter(**(filters or {}))

            # Retrieve from collection
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances", "embeddings"],
            )

            if not results["ids"] or len(results["ids"]) == 0 or len(results["ids"][0]) == 0:
                return AgentResponse(
                    query=query,
                    domain=self.domain,
                    results=[],
                    total_count=0,
                    insufficient_context=True,
                )

            # Convert Chroma distance to cosine similarity
            # For unit vectors: cosine_similarity = 1 - (distance^2 / 2)
            retrieval_results = []
            for doc_id, doc, metadata, distance in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                similarity = 1 - (distance ** 2 / 2)

                # Skip low-similarity results (FR-ORCH-007)
                if similarity < self._config["retrieval"]["oos_similarity_floor"]:
                    continue

                retrieval_results.append(
                    RetrievalResult(
                        chunk_id=metadata.get("chunk_id", "unknown"),
                        source_document=metadata.get("source_document", "unknown"),
                        content=doc,
                        similarity_score=similarity,
                        metadata=metadata,
                    )
                )

            if not retrieval_results:
                return AgentResponse(
                    query=query,
                    domain=self.domain,
                    results=[],
                    total_count=0,
                    insufficient_context=True,
                )

            # Rerank results
            reranked = self._rerank_results(query, retrieval_results)

            # Take top_k_final after reranking
            top_k_final = self._config["retrieval"]["top_k_final"]
            final_results = reranked[:top_k_final]

            return AgentResponse(
                query=query,
                domain=self.domain,
                results=final_results,
                total_count=len(final_results),
                insufficient_context=len(final_results) == 0,
            )

        except Exception as exc:
            return AgentResponse(
                query=query,
                domain=self.domain,
                results=[],
                total_count=0,
                insufficient_context=True,
                error=str(exc),
            )

    def _rerank_results(
        self,
        query: str,
        results: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """Rerank results using cross-encoder (FR-MECH-007)."""
        if not results:
            return results

        # Build pairs for reranking
        pairs = [(query, result.content) for result in results]
        rerank_scores = self._reranker.predict(pairs)

        # Attach rerank scores
        for result, score in zip(results, rerank_scores):
            result.rerank_score = float(score)

        # Sort by rerank score descending
        results.sort(key=lambda r: r.rerank_score or 0, reverse=True)
        return results

    def format_results(self, response: AgentResponse) -> str:
        """Format results for display (subclasses can override)."""
        if response.insufficient_context:
            return f"[{self.domain.upper()}] Insufficient context to answer query."

        lines = [f"[{self.domain.upper()}] Found {response.total_count} result(s):"]
        for i, result in enumerate(response.results, 1):
            lines.append(f"\n{i}. [{result.source_document}] {result.chunk_id}")
            lines.append(f"   Similarity: {result.similarity_score:.3f}")
            if result.rerank_score is not None:
                lines.append(f"   Rerank Score: {result.rerank_score:.3f}")
            lines.append(f"   Content: {result.content[:200]}...")

        return "\n".join(lines)
