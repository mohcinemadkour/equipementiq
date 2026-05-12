"""Software agent for error code and diagnostic retrieval.

Sources: 96 error code JSON documents (atomic, no chunking)
Collection: software_collection
Features: Error code lookup, severity filtering, exact error code matching
Requirements: FR-SOFT-001..007
"""
from __future__ import annotations

import re
from agents.base_agent import BaseAgent, AgentResponse


class SoftwareAgent(BaseAgent):
    """Retrieval agent for error codes and diagnostic procedures.

    Handles queries about:
    - Error codes (SPN, AXS, TCS, CLS, LUB, HYD, CNC, ELC, VIB, THM subsystems)
    - Severity levels (CRITICAL to ADVISORY)
    - Fault categories (tool_wear, spindle_bearing_fault, etc.)
    - Diagnostic steps and remedies
    
    Enhanced: Extracts error codes from queries and prioritizes exact metadata matches.
    """

    def __init__(self):
        """Initialize software agent (software_collection)."""
        from ingestion.config import load_config
        cfg = load_config()
        super().__init__(
            domain="software",
            collection_name=cfg["collections"]["software"],
        )

    def _extract_error_codes(self, query: str) -> list[str]:
        """Extract error code patterns from query text.
        
        Error code format: XXX-YY-NNN (e.g., SPN-MJ-004, CLS-CR-001)
        Returns: List of error codes found in query (uppercase)
        """
        pattern = r'\b([A-Z]{3})-([A-Z]{2})-(\d{3})\b'
        matches = re.findall(pattern, query.upper())
        return [f"{subsys}-{severity}-{number}" for subsys, severity, number in matches]

    def _build_where_filter(
        self,
        severity_level: str | None = None,
        subsystem_code: str | None = None,
        fault_category: str | None = None,
        **kwargs,
    ) -> dict | None:
        """Build metadata filter for error codes.

        FR-SOFT-001: Support severity-based filtering.
        """
        filters = []
        if severity_level:
            filters.append({"severity_level": severity_level})
        if subsystem_code:
            filters.append({"subsystem_code": subsystem_code})
        if fault_category:
            filters.append({"fault_category": fault_category})

        if not filters:
            return None
        if len(filters) == 1:
            return filters[0]
        # Note: ChromaDB may not support $or; return first filter as fallback
        return filters[0]

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        severity_level: str | None = None,
        subsystem_code: str | None = None,
        fault_category: str | None = None,
    ) -> AgentResponse:
        """Retrieve error codes with optional filtering and exact error code matching.

        Args:
            query: Error code query (e.g., "spindle bearing fault")
            top_k: Number of pre-rerank results
            severity_level: Filter by severity (CRITICAL, MAJOR, SERIOUS, etc.)
            subsystem_code: Filter by subsystem (SPN, AXS, TCS, etc.)
            fault_category: Filter by category (tool_wear, spindle_bearing_fault, etc.)

        Returns:
            AgentResponse with citation (error_code + chunk_id)
        
        Enhancement: If query contains error code patterns (e.g., SPN-MJ-004),
        retrieve by exact metadata match and place at top of results.
        """
        # Extract error codes from query
        error_codes = self._extract_error_codes(query)
        
        # Perform semantic search first
        response = super().retrieve(
            query=query,
            top_k=top_k,
            filters={
                "severity_level": severity_level,
                "subsystem_code": subsystem_code,
                "fault_category": fault_category,
            },
        )
        
        # If error codes found in query, retrieve exact matches and prepend
        if error_codes and not response.insufficient_context:
            try:
                semantic_results = response.results[:]  # Copy semantic results
                exact_match_results = []
                seen_chunk_ids = {r.chunk_id for r in semantic_results}
                
                # Query for each extracted error code
                for error_code in error_codes:
                    try:
                        exact_results = self._collection.get(
                            where={"error_code": error_code},
                            include=["documents", "metadatas"]
                        )
                        
                        if exact_results["ids"]:
                            for i, doc_id in enumerate(exact_results["ids"]):
                                if doc_id not in seen_chunk_ids:
                                    # Create RetrievalResult for exact match
                                    from agents.base_agent import RetrievalResult
                                    exact_match_results.append(
                                        RetrievalResult(
                                            chunk_id=doc_id,
                                            source_document=exact_results["metadatas"][i].get("source_document", error_code),
                                            content=exact_results["documents"][i],
                                            similarity_score=0.99,  # Boost exact match score
                                            metadata=exact_results["metadatas"][i],
                                            rerank_score=None
                                        )
                                    )
                                    seen_chunk_ids.add(doc_id)
                    except Exception:
                        # If metadata lookup fails, continue with semantic results
                        pass
                
                # Prepend exact matches to semantic results
                if exact_match_results:
                    response.results = exact_match_results + semantic_results
                    response.total_count = len(response.results)
            except Exception:
                # If enhancement fails, return original semantic results
                pass
        
        return response
