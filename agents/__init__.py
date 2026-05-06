"""EquipmentIQ agent layer — domain-specific retrieval agents.

Three specialised agents with collection isolation (DR-005):
- MechanicalAgent: Technical documentation (mechanical_collection)
- SoftwareAgent: Error codes (software_collection)
- SupportAgent: Customer cases (support_collection)

All agents inherit from BaseAgent and implement:
- OpenAI embeddings (DR-004)
- Cross-encoder reranking (FR-MECH-007)
- Cosine similarity filtering (FR-ORCH-007: < 0.4)
- Citation tracking (FR-ORCH-006: source_document + chunk_id)
"""
from __future__ import annotations

from agents.base_agent import AgentResponse, BaseAgent, RetrievalResult
from agents.mechanical_agent import MechanicalAgent
from agents.software_agent import SoftwareAgent
from agents.support_agent import SupportAgent

__all__ = [
    "BaseAgent",
    "AgentResponse",
    "RetrievalResult",
    "MechanicalAgent",
    "SoftwareAgent",
    "SupportAgent",
]
