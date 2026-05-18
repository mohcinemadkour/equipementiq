"""Support agent for customer complaint case retrieval.

Sources: 150 customer complaint records (atomic, concatenated notes)
Collection: support_collection
Features: Case-based filtering, priority-aware retrieval, error code metadata lookup
Requirements: FR-SUPP-001..008
"""
from __future__ import annotations

import re
from agents.base_agent import BaseAgent, RetrievalResult, AgentResponse


class SupportAgent(BaseAgent):
    """Retrieval agent for customer support cases and solutions.

    Handles queries about:
    - Customer complaint cases
    - Case resolution approaches
    - Warranty and RMA procedures
    - Service-level agreements
    - Similar past cases for reference
    """

    def __init__(self):
        """Initialize support agent (support_collection)."""
        from ingestion.config import load_config
        cfg = load_config()
        super().__init__(
            domain="support",
            collection_name=cfg["collections"]["support"],
        )

    def _build_where_filter(
        self,
        case_status: str | None = None,
        priority: str | None = None,
        machine_id: str | None = None,
        rma_required: str | None = None,
        **kwargs,
    ) -> dict | None:
        """Build metadata filter for support cases.

        FR-SUPP-001: Support case-status filtering.
        """
        filters = []
        if case_status:
            filters.append({"case_status": case_status})
        if priority:
            filters.append({"priority": priority})
        if machine_id:
            filters.append({"machine_id": machine_id})
        if rma_required:
            filters.append({"rma_required": rma_required})

        if not filters:
            return None
        if len(filters) == 1:
            return filters[0]
        # Note: ChromaDB may not support $or; return first filter as fallback
        return filters[0]

    def _extract_error_codes(self, query: str) -> list[str]:
        """Extract error code patterns from query text.
        
        Error code format: XXX-YY-NNN (e.g., SPN-MJ-004, CLS-CR-001)
        Returns: List of error codes found in query (uppercase)
        """
        pattern = r'\b([A-Z]{3})-([A-Z]{2})-(\d{3})\b'
        matches = re.findall(pattern, query.upper())
        return [f"{subsys}-{severity}-{number}" for subsys, severity, number in matches]

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        case_status: str | None = None,
        priority: str | None = None,
        machine_id: str | None = None,
        rma_required: str | None = None,
    ) -> AgentResponse:
        """Retrieve support cases with optional filtering and error code metadata lookup.

        Args:
            query: Support query (e.g., "spindle bearing replacement warranty")
            top_k: Number of pre-rerank results
            case_status: Filter by status (CLOSED, ESCALATED, PENDING_PARTS, etc.)
            priority: Filter by priority (P1-CRITICAL, P2-HIGH, etc.)
            machine_id: Filter by machine (M01, M02, M03)
            rma_required: Filter by RMA requirement (YES/NO)

        Returns:
            AgentResponse with citation (complaint_case_id + chunk_id)
        
        Enhancement: If query contains error code patterns (e.g., AXS-SR-001),
        retrieve complaints mentioning that error code via metadata lookup
        and place at top of results.
        """
        # Extract error codes from query
        error_codes = self._extract_error_codes(query)
        
        # Perform semantic search
        response = super().retrieve(
            query=query,
            top_k=top_k,
            filters={
                "case_status": case_status,
                "priority": priority,
                "machine_id": machine_id,
                "rma_required": rma_required,
            },
        )
        
        # If error codes found in query, retrieve complaints mentioning them via metadata
        if error_codes and not response.insufficient_context:
            try:
                semantic_results = response.results[:]  # Copy semantic results
                metadata_results = []
                seen_chunk_ids = {r.chunk_id for r in semantic_results}
                
                # Query for each extracted error code via error_code_triggered metadata
                for error_code in error_codes:
                    try:
                        metadata_matches = self._collection.get(
                            where={"error_code_triggered": error_code},
                            include=["documents", "metadatas"]
                        )
                        
                        if metadata_matches["ids"] and len(metadata_matches["ids"]) > 0:
                            # Convert metadata matches to RetrievalResult objects
                            for doc_id, doc, metadata in zip(
                                metadata_matches["ids"],
                                metadata_matches["documents"],
                                metadata_matches["metadatas"]
                            ):
                                chunk_id = metadata.get("chunk_id", "unknown")
                                # Avoid duplicates
                                if chunk_id not in seen_chunk_ids:
                                    metadata_results.append(
                                        RetrievalResult(
                                            chunk_id=chunk_id,
                                            source_document=metadata.get("source_document", "unknown"),
                                            content=doc,
                                            similarity_score=0.95,  # High score for exact metadata match
                                            metadata=metadata,
                                            rerank_score=None
                                        )
                                    )
                                    seen_chunk_ids.add(chunk_id)
                    except Exception:
                        # If metadata lookup fails, continue with semantic results
                        pass
                
                # Merge: metadata chunks first (higher relevance), then semantic
                all_results = metadata_results + semantic_results
                
                # Cap at top_k_final
                top_k_final = self._config["retrieval"]["top_k_final"]
                final_results = all_results[:top_k_final]
                
                return AgentResponse(
                    query=query,
                    domain=self.domain,
                    results=final_results,
                    total_count=len(final_results),
                    insufficient_context=len(final_results) == 0,
                )
            except Exception:
                # If any error in metadata merging, return semantic results only
                return response
        
        return response
