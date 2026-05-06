"""Software agent for error code and diagnostic retrieval.

Sources: 96 error code JSON documents (atomic, no chunking)
Collection: software_collection
Features: Error code lookup, severity filtering
Requirements: FR-SOFT-001..007
"""
from __future__ import annotations

from agents.base_agent import BaseAgent


class SoftwareAgent(BaseAgent):
    """Retrieval agent for error codes and diagnostic procedures.

    Handles queries about:
    - Error codes (SPN, AXS, TCS, CLS, LUB, HYD, CNC, ELC, VIB, THM subsystems)
    - Severity levels (CRITICAL to ADVISORY)
    - Fault categories (tool_wear, spindle_bearing_fault, etc.)
    - Diagnostic steps and remedies
    """

    def __init__(self):
        """Initialize software agent (software_collection)."""
        from ingestion.config import load_config
        cfg = load_config()
        super().__init__(
            domain="software",
            collection_name=cfg["collections"]["software"],
        )

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
    ) -> dict:
        """Retrieve error codes with optional filtering.

        Args:
            query: Error code query (e.g., "spindle bearing fault")
            top_k: Number of pre-rerank results
            severity_level: Filter by severity (CRITICAL, MAJOR, SERIOUS, etc.)
            subsystem_code: Filter by subsystem (SPN, AXS, TCS, etc.)
            fault_category: Filter by category (tool_wear, spindle_bearing_fault, etc.)

        Returns:
            AgentResponse with citation (error_code + chunk_id)
        """
        response = super().retrieve(
            query=query,
            top_k=top_k,
            filters={
                "severity_level": severity_level,
                "subsystem_code": subsystem_code,
                "fault_category": fault_category,
            },
        )
        return response
