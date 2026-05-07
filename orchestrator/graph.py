"""
LangGraph orchestrator for EquipmentIQ RAG.

8-node StateGraph with conditional routing, parallel retrieval, and synthesis.
- classify_intent: Route based on domain
- agent nodes: Retrieve from domain collections
- parallel_node: Cross-domain retrieval
- merge_context: Deduplicate and score
- synthesise: LLM synthesis with citations
- log_trace: LangSmith logging
"""

import json
import re
import time
from functools import lru_cache
from typing import Literal

from langgraph.graph import StateGraph, END
from langsmith import traceable

from ingestion.config import load_config
from orchestrator.state import AgentState, AgentResult
from orchestrator.intent_classifier import classify
from agents import MechanicalAgent, SoftwareAgent, SupportAgent


# ============================================================================
# Singletons (cached initialization)
# ============================================================================

@lru_cache(maxsize=1)
def _mechanical_agent() -> MechanicalAgent:
    return MechanicalAgent()


@lru_cache(maxsize=1)
def _software_agent() -> SoftwareAgent:
    return SoftwareAgent()


@lru_cache(maxsize=1)
def _support_agent() -> SupportAgent:
    return SupportAgent()


@lru_cache(maxsize=1)
def _get_synthesis_prompt() -> str:
    """Load synthesis prompt from disk."""
    cfg = load_config()
    prompt_path = cfg["paths"]["prompts_dir"] + "/synthesis.txt"
    with open(prompt_path, "r") as f:
        return f.read()


@lru_cache(maxsize=1)
def _get_anthropic_client():
    """Get cached Anthropic client."""
    from anthropic import Anthropic
    return Anthropic()


# ============================================================================
# Node 1: Classify Intent
# ============================================================================

def classify_intent(state: AgentState) -> AgentState:
    """Route query to appropriate domain(s) using intent classifier.
    
    Updates:
        domain: mechanical | software | support | cross_domain
        confidence: 0.0 - 1.0
    """
    start_time = time.time()
    
    # Classify query
    classification = classify(state["query"], history=state.get("conversation_history", []))
    
    # Update state
    state["domain"] = classification.domain
    state["confidence"] = classification.confidence
    
    # Store latency
    if "node_latency" not in state:
        state["node_latency"] = {}
    state["node_latency"]["classify_intent"] = time.time() - start_time
    
    return state


# ============================================================================
# Nodes 2-4: Single-Domain Agent Nodes
# ============================================================================

def mechanical_node(state: AgentState) -> AgentState:
    """Retrieve from mechanical_collection using MechanicalAgent."""
    start_time = time.time()
    
    agent = _mechanical_agent()
    
    # Extract filters from intent if available
    filters = state.get("suggested_filters", {})
    subsystem = filters.get("subsystem")
    
    # Retrieve
    chunks = agent.retrieve(state["query"], where_filter={"subsystem": subsystem} if subsystem else None)
    
    # Format result
    agent_result: AgentResult = {
        "chunks": chunks,
        "answer": "",
        "citations": [{"source_document": c["metadata"].get("source_document"), 
                       "chunk_id": c["metadata"].get("chunk_id"),
                       "score": c["cosine_similarity"]} for c in chunks],
        "agent_name": "mechanical_agent",
        "status": "ok" if chunks else "out_of_scope",
        "retrieval_scores": [c["cosine_similarity"] for c in chunks]
    }
    
    state["agent_results"]["mechanical_agent"] = agent_result
    
    if "node_latency" not in state:
        state["node_latency"] = {}
    state["node_latency"]["mechanical_node"] = time.time() - start_time
    
    return state


def software_node(state: AgentState) -> AgentState:
    """Retrieve from software_collection using SoftwareAgent."""
    start_time = time.time()
    
    agent = _software_agent()
    
    # Extract filters
    filters = state.get("suggested_filters", {})
    severity = filters.get("severity_level")
    error_prefix = filters.get("error_code_prefix")
    
    where_filter = {}
    if severity:
        where_filter["severity_level"] = severity
    if error_prefix:
        where_filter["error_code"] = {"$regex": f"^{error_prefix}"}
    
    # Retrieve
    chunks = agent.retrieve(state["query"], where_filter=where_filter if where_filter else None)
    
    # Format result
    agent_result: AgentResult = {
        "chunks": chunks,
        "answer": "",
        "citations": [{"source_document": c["metadata"].get("source_document"), 
                       "chunk_id": c["metadata"].get("chunk_id"),
                       "score": c["cosine_similarity"]} for c in chunks],
        "agent_name": "software_agent",
        "status": "ok" if chunks else "out_of_scope",
        "retrieval_scores": [c["cosine_similarity"] for c in chunks]
    }
    
    state["agent_results"]["software_agent"] = agent_result
    
    if "node_latency" not in state:
        state["node_latency"] = {}
    state["node_latency"]["software_node"] = time.time() - start_time
    
    return state


def support_node(state: AgentState) -> AgentState:
    """Retrieve from support_collection using SupportAgent."""
    start_time = time.time()
    
    agent = _support_agent()
    
    # Extract filters
    filters = state.get("suggested_filters", {})
    case_status = filters.get("case_status")
    priority = filters.get("priority")
    machine_id = filters.get("machine_id")
    
    where_filter = {}
    if case_status:
        where_filter["case_status"] = case_status
    if priority:
        where_filter["priority"] = priority
    if machine_id:
        where_filter["machine_id"] = machine_id
    
    # Retrieve
    chunks = agent.retrieve(state["query"], where_filter=where_filter if where_filter else None)
    
    # Format result
    agent_result: AgentResult = {
        "chunks": chunks,
        "answer": "",
        "citations": [{"source_document": c["metadata"].get("source_document"), 
                       "chunk_id": c["metadata"].get("chunk_id"),
                       "score": c["cosine_similarity"]} for c in chunks],
        "agent_name": "support_agent",
        "status": "ok" if chunks else "out_of_scope",
        "retrieval_scores": [c["cosine_similarity"] for c in chunks]
    }
    
    state["agent_results"]["support_agent"] = agent_result
    
    if "node_latency" not in state:
        state["node_latency"] = {}
    state["node_latency"]["support_node"] = time.time() - start_time
    
    return state


# ============================================================================
# Node 5: Parallel Node (Cross-Domain)
# ============================================================================

def parallel_node(state: AgentState) -> AgentState:
    """Call all 3 agents in parallel for cross-domain queries.
    
    Note: In practice, these run sequentially but are conceptually parallel.
    For true async parallelism, agents would need async retrieve() methods.
    """
    start_time = time.time()
    
    # Call all 3 agents (conceptually parallel, practically sequential)
    mech_agent = _mechanical_agent()
    soft_agent = _software_agent()
    supp_agent = _support_agent()
    
    mech_chunks = mech_agent.retrieve(state["query"])
    soft_chunks = soft_agent.retrieve(state["query"])
    support_chunks = supp_agent.retrieve(state["query"])
    
    # Format results
    state["agent_results"]["mechanical_agent"] = {
        "chunks": mech_chunks,
        "answer": "",
        "citations": [{"source_document": c["metadata"].get("source_document"), 
                       "chunk_id": c["metadata"].get("chunk_id"),
                       "score": c["cosine_similarity"]} for c in mech_chunks],
        "agent_name": "mechanical_agent",
        "status": "ok" if mech_chunks else "out_of_scope",
        "retrieval_scores": [c["cosine_similarity"] for c in mech_chunks]
    }
    
    state["agent_results"]["software_agent"] = {
        "chunks": soft_chunks,
        "answer": "",
        "citations": [{"source_document": c["metadata"].get("source_document"), 
                       "chunk_id": c["metadata"].get("chunk_id"),
                       "score": c["cosine_similarity"]} for c in soft_chunks],
        "agent_name": "software_agent",
        "status": "ok" if soft_chunks else "out_of_scope",
        "retrieval_scores": [c["cosine_similarity"] for c in soft_chunks]
    }
    
    state["agent_results"]["support_agent"] = {
        "chunks": support_chunks,
        "answer": "",
        "citations": [{"source_document": c["metadata"].get("source_document"), 
                       "chunk_id": c["metadata"].get("chunk_id"),
                       "score": c["cosine_similarity"]} for c in support_chunks],
        "agent_name": "support_agent",
        "status": "ok" if support_chunks else "out_of_scope",
        "retrieval_scores": [c["cosine_similarity"] for c in support_chunks]
    }
    
    state["node_latency"]["parallel_node"] = time.time() - start_time
    
    return state


# ============================================================================
# Node 6: Merge Context
# ============================================================================

def merge_context(state: AgentState) -> AgentState:
    """Deduplicate chunks by chunk_id, sort by retrieval score descending."""
    start_time = time.time()
    
    # Collect all chunks from all agents
    all_chunks = []
    seen_chunk_ids = set()
    
    for agent_result in state["agent_results"].values():
        for chunk in agent_result.get("chunks", []):
            chunk_id = chunk["metadata"].get("chunk_id")
            if chunk_id not in seen_chunk_ids:
                all_chunks.append(chunk)
                seen_chunk_ids.add(chunk_id)
    
    # Sort by cosine_similarity descending
    all_chunks.sort(key=lambda c: c.get("cosine_similarity", 0.0), reverse=True)
    
    # Format as merged_context (limit to top_k_final)
    cfg = load_config()
    top_k = cfg["retrieval"]["top_k_final"]
    
    state["merged_context"] = [
        {
            "text": c.get("text", ""),
            "source_document": c["metadata"].get("source_document"),
            "chunk_id": c["metadata"].get("chunk_id"),
            "cosine_similarity": c.get("cosine_similarity", 0.0)
        }
        for c in all_chunks[:top_k]
    ]
    
    state["node_latency"]["merge_context"] = time.time() - start_time
    
    return state


# ============================================================================
# Node 7: Synthesise
# ============================================================================

def synthesise(state: AgentState) -> AgentState:
    """LLM synthesis of merged context with citations."""
    start_time = time.time()
    
    cfg = load_config()
    client = _get_anthropic_client()
    
    # Format merged context for prompt
    context_str = "\n\n".join(
        f"[SOURCE: {c['source_document']} chunk {c['chunk_id']}]\n{c['text']}"
        for c in state["merged_context"]
    )
    
    # Format conversation history for prompt
    history_str = "\n\n".join(
        f"Q: {turn['query']}\nA: {turn['answer'][:100]}..."
        for turn in state.get("conversation_history", [])[-5:]
    )
    
    # Load synthesis prompt
    prompt_template = _get_synthesis_prompt()
    
    # Inject into prompt
    full_prompt = prompt_template.format(
        merged_context=context_str,
        conversation_history=history_str,
        query=state["query"]
    )
    
    # Call Claude
    response = client.messages.create(
        model=cfg["llm"]["generation_model"],
        max_tokens=cfg["llm"]["max_tokens"],
        temperature=cfg["llm"]["temperature"],
        messages=[
            {
                "role": "user",
                "content": full_prompt
            }
        ]
    )
    
    final_answer = response.content[0].text.strip()
    
    # Extract citations from response
    import re
    citation_pattern = r"\[SOURCE: ([^\]]+) chunk ([^\]]+)\]"
    matches = re.findall(citation_pattern, final_answer)
    
    state["final_answer"] = final_answer
    state["citations"] = [
        {
            "source_document": source.strip(),
            "chunk_id": chunk_id.strip()
        }
        for source, chunk_id in matches
    ]
    
    state["node_latency"]["synthesise"] = time.time() - start_time
    
    return state


# ============================================================================
# Node 8: Log Trace
# ============================================================================

def log_trace(state: AgentState) -> AgentState:
    """Log query execution to LangSmith."""
    start_time = time.time()
    
    # Build trace data
    trace_data = {
        "query": state["query"],
        "domain": state["domain"],
        "confidence": state["confidence"],
        "agents_used": [k for k, v in state["agent_results"].items() if v.get("chunks")],
        "chunk_ids": [c["chunk_id"] for c in state["merged_context"]],
        "citation_count": len(state["citations"]),
        "node_latencies": state.get("node_latency", {})
    }
    
    # Log via LangSmith (traceable decorator will capture this)
    print(f"[TRACE] {json.dumps(trace_data, indent=2)}")
    
    state["node_latency"]["log_trace"] = time.time() - start_time
    
    return state


# ============================================================================
# Conditional Routing
# ============================================================================

def route_by_domain(state: AgentState) -> Literal["mechanical", "software", "support", "parallel"]:
    """Route to appropriate node based on classified domain."""
    domain = state["domain"]
    
    if domain == "mechanical":
        return "mechanical"
    elif domain == "software":
        return "software"
    elif domain == "support":
        return "support"
    elif domain == "cross_domain":
        return "parallel"
    else:
        # Default to parallel (safe fallback)
        return "parallel"


# ============================================================================
# StateGraph Construction
# ============================================================================

def _build_graph():
    """Build and compile LangGraph StateGraph."""
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("mechanical", mechanical_node)
    graph.add_node("software", software_node)
    graph.add_node("support", support_node)
    graph.add_node("parallel", parallel_node)
    graph.add_node("merge_context", merge_context)
    graph.add_node("synthesise", synthesise)
    graph.add_node("log_trace", log_trace)
    
    # Set entry point
    graph.set_entry_point("classify_intent")
    
    # Add conditional edge from classify_intent based on domain
    graph.add_conditional_edges(
        "classify_intent",
        route_by_domain,
        {
            "mechanical": "mechanical",
            "software": "software",
            "support": "support",
            "parallel": "parallel"
        }
    )
    
    # Agent nodes → merge_context
    graph.add_edge("mechanical", "merge_context")
    graph.add_edge("software", "merge_context")
    graph.add_edge("support", "merge_context")
    graph.add_edge("parallel", "merge_context")
    
    # merge_context → synthesise → log_trace → END
    graph.add_edge("merge_context", "synthesise")
    graph.add_edge("synthesise", "log_trace")
    graph.add_edge("log_trace", END)
    
    return graph.compile()


@lru_cache(maxsize=1)
def _get_graph():
    """Get cached compiled StateGraph."""
    return _build_graph()


# ============================================================================
# Public API
# ============================================================================

@traceable
def run_query(query: str, history: list[dict] | None = None) -> AgentState:
    """Execute a query through the full orchestrator graph.
    
    Args:
        query: User question
        history: Last 5 (query, answer) turns for context
    
    Returns:
        AgentState with domain, confidence, agent_results, final_answer, citations
    
    Process:
        1. classify_intent: Route query to domain(s)
        2. agent nodes: Retrieve from appropriate collection(s)
        3. merge_context: Deduplicate and score chunks
        4. synthesise: LLM synthesis with citations
        5. log_trace: LangSmith logging
    """
    # Initialize state
    initial_state: AgentState = {
        "query": query,
        "domain": "cross_domain",  # Will be overridden by classify_intent
        "confidence": 0.0,
        "agent_results": {},
        "merged_context": [],
        "final_answer": "",
        "citations": [],
        "eval_scores": {},
        "feedback": {},
        "conversation_history": history or []
    }
    
    # Run graph
    graph = _get_graph()
    final_state = graph.invoke(initial_state)
    
    return final_state
