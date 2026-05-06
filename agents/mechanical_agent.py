"""Mechanical agent for VMC-3000 technical documentation retrieval.

Sources: 6 technical PDFs (DOC-EIQ-001..006)
Collection: mechanical_collection
Chunking: 512/64 tokens (DR-001)
Features: Subsystem-aware filtering, maintenance procedures
Requirements: FR-MECH-001..007
"""
from __future__ import annotations

from agents.base_agent import BaseAgent


class MechanicalAgent(BaseAgent):
    """Retrieval agent for mechanical/technical documentation.

    Handles queries about:
    - Spindle system (SPN)
    - Axis servo system (AXS)
    - Thermal control system (TCS)
    - Coolant/lubrication (CLS, LUB)
    - Hydraulic system (HYD)
    - CNC control (CNC)
    - Electrical/wiring (ELC)
    - Vibration monitoring (VIB)
    - Thermal management (THM)
    """

    def __init__(self):
        """Initialize mechanical agent (mechanical_collection)."""
        from ingestion.config import load_config
        cfg = load_config()
        super().__init__(
            domain="mechanical",
            collection_name=cfg["collections"]["mechanical"],
        )

    def _build_where_filter(self, subsystem: str | None = None, **kwargs) -> dict | None:
        """Build metadata filter for subsystem (SPN, AXS, TCS, etc.).

        FR-MECH-001: Support subsystem-specific queries.
        """
        if subsystem:
            return {"subsystem": subsystem}
        return None

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        subsystem: str | None = None,
    ) -> dict:
        """Retrieve mechanical documentation with optional subsystem filter.

        Args:
            query: Technical query (e.g., "spindle bearing replacement")
            top_k: Number of pre-rerank results
            subsystem: Optional subsystem code (SPN, AXS, TCS, CLS, LUB, HYD, CNC, ELC, VIB, THM)

        Returns:
            AgentResponse with citation (DOC-EIQ-XXX + chunk_id)
        """
        response = super().retrieve(
            query=query,
            top_k=top_k,
            filters={"subsystem": subsystem} if subsystem else None,
        )
        return response
