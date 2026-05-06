"""Support agent for customer complaint case retrieval.

Sources: 150 customer complaint records (atomic, concatenated notes)
Collection: support_collection
Features: Case-based filtering, priority-aware retrieval
Requirements: FR-SUPP-001..008
"""
from __future__ import annotations

from agents.base_agent import BaseAgent


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

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        case_status: str | None = None,
        priority: str | None = None,
        machine_id: str | None = None,
        rma_required: str | None = None,
    ) -> dict:
        """Retrieve support cases with optional filtering.

        Args:
            query: Support query (e.g., "spindle bearing replacement warranty")
            top_k: Number of pre-rerank results
            case_status: Filter by status (CLOSED, ESCALATED, PENDING_PARTS, etc.)
            priority: Filter by priority (P1-CRITICAL, P2-HIGH, etc.)
            machine_id: Filter by machine (M01, M02, M03)
            rma_required: Filter by RMA requirement (YES/NO)

        Returns:
            AgentResponse with citation (complaint_case_id + chunk_id)
        """
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
        return response
