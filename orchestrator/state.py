"""
Orchestrator state definitions for EquipmentIQ RAG.

TypedDicts define immutable state contracts across LangGraph nodes.
- AgentState: Full application state managed by StateGraph
- AgentResult: Domain-agent return type
"""

from typing import TypedDict, Literal


class AgentResult(TypedDict, total=False):
    """Return type from domain agents (mechanical, software, support).
    
    Fields:
        chunks: Retrieved documents with metadata
        answer: Agent's synthesis of retrieved chunks
        citations: List of cited sources with relevance scores
        agent_name: Domain agent name (mechanical_agent, software_agent, support_agent)
        status: Retrieval outcome (ok, out_of_scope, error)
        retrieval_scores: Cosine similarity scores for each chunk
    """
    chunks: list[dict]
    answer: str
    citations: list[dict]
    agent_name: str
    status: Literal["ok", "out_of_scope", "error"]
    retrieval_scores: list[float]


class AgentState(TypedDict, total=False):
    """Full state managed by LangGraph StateGraph.
    
    Carries query, routing decision, parallel retrieval results, and synthesis.
    Updated incrementally as queries flow through orchestrator nodes.
    
    Fields:
        query: User question (original input)
        domain: Routing decision (mechanical, software, support, cross_domain)
        confidence: Intent classifier confidence [0.0, 1.0]
        agent_results: Parallel agent outputs keyed by agent_name
            - mechanical_agent: AgentResult
            - software_agent: AgentResult
            - support_agent: AgentResult
        agents_used: List of agents that returned chunks (for UI display)
        merged_context: Unified context chunks from selected agent(s)
        final_answer: Synthesized LLM response to query
        citations: Merged citation list (source_document, chunk_id, cosine_sim)
        eval_scores: RAGAS metrics (faithfulness, answer_relevance, context_precision)
        feedback: User feedback signal (rating, comment, corrections)
        conversation_history: Last 5 (query, answer) turns for synthesis context
        node_latency: Execution times for each node in the graph
    """
    query: str
    domain: Literal["mechanical", "software", "support", "cross_domain"]
    confidence: float
    agent_results: dict[str, AgentResult]
    agents_used: list[str]
    merged_context: list[dict]
    final_answer: str
    citations: list[dict]
    eval_scores: dict[str, float]
    feedback: dict[str, str | int | None]
    conversation_history: list[dict]
    node_latency: dict[str, float]
