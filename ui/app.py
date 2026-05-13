"""EquipmentIQ Streamlit Demo Interface."""

import streamlit as st
import os
import sys
import json
import time
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Track page load time
_PAGE_LOAD_START = time.time()

# Ensure parent directory is in path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="EquipmentIQ",
    page_icon="🔧",
    layout="wide"
)

# ============================================================================
# OPTIMIZATION 1: Cache expensive resources with st.cache_resource
# ============================================================================

@st.cache_resource
def get_orchestrator_run_query():
    """Get the orchestrator's run_query function (cached)."""
    from orchestrator.graph import run_query
    return run_query


@st.cache_resource
def get_chromadb_client():
    """Get ChromaDB client (cached)."""
    import chromadb
    cfg = get_config()
    persist_dir = cfg.get("paths", {}).get("chroma_persist_dir", "./chroma_db")
    return chromadb.PersistentClient(path=persist_dir)


# Deferred imports - loaded only when needed
def get_config():
    """Load configuration lazily."""
    try:
        from ingestion.config import load_config
        return load_config()
    except Exception as e:
        st.warning(f"Cannot load config: {e}")
        return {}

def get_feedback_functions():
    """Load feedback functions lazily."""
    try:
        from feedback.feedback_store import init_db, save_feedback, get_stats
        return init_db, save_feedback, get_stats
    except Exception as e:
        st.error(f"Cannot load feedback functions: {e}")
        return None, None, None

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ EquipmentIQ Demo")
    st.divider()
    
    # System status
    st.subheader("System Status")
    try:
        config = get_config()
        client = get_chromadb_client()
        collections = ["mechanical_collection", "software_collection", "support_collection"]
        for coll_name in collections:
            try:
                coll = client.get_collection(coll_name)
                count = coll.count()
                col_display = coll_name.replace("_", " ").title()
                st.metric(col_display, count)
            except Exception:
                st.metric(coll_name, "N/A")
    except Exception as e:
        st.warning(f"Cannot connect to ChromaDB: {e}")
    
    st.divider()
    
    # Demo mode
    st.subheader("Demo Queries")
    demo_mode = st.checkbox("📋 Use Curated Queries", value=False)
    
    demo_queries = [
        "What does error SPN-CR-001 mean and what is the remedy?",
        "What bearing type does the VMC-3000 spindle use?",
        "What is the part number for spindle bearings?",
        "What wiring connects the X-axis encoder to the CNC?",
        "Show me complaint case CMP-2019-1000",
        "What are the most common failure modes on M01?",
        "What does error AXS-CR-001 mean?",
        "What maintenance is required every 4000 hours?",
        "What caused the spindle bearing fault in February 2019?",
        "M01 spindle vibration and ATC alarm at the same time"
    ]
    
    if demo_mode:
        selected_query = st.selectbox(
            "Select a query:",
            demo_queries,
            key="demo_selector"
        )
    
    st.divider()
    
    # Model info
    st.subheader("Configuration")
    config = get_config()
    model_name = config.get("generation_model", "claude-haiku-4-5-20251001")
    st.text(f"🤖 Model: {model_name}")
    
    # Feedback stats
    try:
        init_db, save_feedback, get_stats = get_feedback_functions()
        if init_db:
            init_db()
            stats = get_stats()
            if stats['total'] > 0:
                st.metric("Total Feedback", stats['total'])
                st.metric("Positive", stats['positive'])
                st.metric("Negative", stats['negative'])
    except Exception:
        pass


# --- MAIN AREA ---
st.title("🏭 EquipmentIQ — Industrial Predictive Maintenance")
st.markdown("**Query the VMC-3000 knowledge base:** mechanical specs, error codes, and customer complaints.")
st.divider()

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

if "current_result" not in st.session_state:
    st.session_state.current_result = None

# --- Query Input ---
st.subheader("📝 Your Query")

# Example buttons in a row
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("❌ Error SPN-CR-001?", use_container_width=True, key="btn_error"):
        st.session_state.query_input = "What does error SPN-CR-001 mean?"
        st.rerun()
with col2:
    if st.button("⚙️ Spindle bearing?", use_container_width=True, key="btn_bearing"):
        st.session_state.query_input = "What bearing type does the VMC-3000 spindle use?"
        st.rerun()
with col3:
    if st.button("📋 Complaint CMP-2019-1000?", use_container_width=True, key="btn_complaint"):
        st.session_state.query_input = "Show me complaint case CMP-2019-1000"
        st.rerun()

# Query text area
try:
    selected_query
    demo_default = selected_query if demo_mode else ""
except NameError:
    demo_default = ""

query_input = st.text_area(
    "Enter your query:",
    value=st.session_state.get("query_input", demo_default),
    height=100
)
)
st.session_state.query_input = query_input

# Submit button
col_submit = st.columns([1, 4])
with col_submit[0]:
    submit_button = st.button("🚀 Submit", use_container_width=True)

# --- Process Query ---
if submit_button and query_input.strip():
    st.session_state.query_input = ""  # Clear after submit
    
    with st.spinner("🔍 Routing and retrieving..."):
        try:
            # Get cached orchestrator run_query function
            run_query = get_orchestrator_run_query()
            
            # Run orchestrator
            result = run_query(query_input)
            st.session_state.current_result = result
            
            # Add to history
            st.session_state.history.append({
                "query": query_input,
                "timestamp": datetime.now().isoformat(),
                "result": result
            })
            
        except Exception as e:
            st.error(f"❌ Error processing query: {e}")
            st.session_state.current_result = None

# --- Display Latest Result ---
if st.session_state.current_result:
    result = st.session_state.current_result
    
    st.divider()
    st.subheader("✅ Result")
    
    # --- SECTION A: Routing Display ---
    st.markdown("### 🧭 Routing Information")
    
    domain = result.get("domain", "unknown")
    confidence = result.get("confidence", 0.0)
    agents_used = result.get("agents_used", [])
    node_latency = result.get("node_latency", {})
    
    # Domain badge with color
    domain_colors = {
        "mechanical": "🔵",
        "software": "🟠",
        "support": "🟢",
        "cross_domain": "🟣"
    }
    domain_emoji = domain_colors.get(domain, "⚪")
    
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("Domain", f"{domain_emoji} {domain.title()}")
    
    with metric_cols[1]:
        st.metric("Confidence", f"{confidence:.1%}")
    
    with metric_cols[2]:
        st.metric("Agents Used", ", ".join(agents_used) if agents_used else "N/A")
    
    with metric_cols[3]:
        total_latency = node_latency.get("total_query", 0) if node_latency else 0
        st.metric("Latency", f"{total_latency:.2f}s")
    
    # Confidence progress bar
    st.progress(min(confidence, 1.0))
    
    # --- SECTION B: Answer ---
    st.markdown("### 💬 Answer")
    answer = result.get("final_answer", "No answer generated.")
    st.markdown(answer)
    
    # Sources expander
    with st.expander("📚 Sources Used", expanded=False):
        citations = result.get("citations", [])
        if citations:
            for i, citation in enumerate(citations, 1):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.text(f"**Source {i}**")
                    st.text(citation.get("source_document", "Unknown"))
                with col2:
                    st.text("Chunk ID")
                    st.code(citation.get("chunk_id", "N/A"))
                with col3:
                    st.text("Similarity")
                    sim = citation.get("similarity_score", 0.0)
                    st.metric("", f"{sim:.3f}")
                st.divider()
        else:
            st.info("No citations available.")
    
    # --- SECTION C: Metrics Expander ---
    with st.expander("📊 Evaluation Metrics", expanded=False):
        eval_scores = result.get("eval_scores", {})
        
        # Faithfulness with color coding
        faithfulness = eval_scores.get("faithfulness_score", 0.0)
        if faithfulness >= 0.80:
            color = "🟢"  # Green
        elif faithfulness >= 0.60:
            color = "🟡"  # Amber
        else:
            color = "🔴"  # Red
        
        metrics_cols = st.columns(3)
        with metrics_cols[0]:
            st.metric(f"{color} Faithfulness", f"{faithfulness:.2f}")
        
        with metrics_cols[1]:
            judge_score = eval_scores.get("llm_judge_score", 0.0)
            st.metric("LLM Judge", f"{judge_score:.1f} / 5")
        
        with metrics_cols[2]:
            st.metric("Confidence", f"{confidence:.1%}")
        
        # Latency breakdown
        st.markdown("**⏱️ Latency Breakdown:**")
        node_latency = result.get("node_latency", {})
        if node_latency:
            # Show total
            total = node_latency.get("total_query", 0)
            st.caption(f"**Total: {total:.2f}s**")
            
            # Show individual nodes in columns
            latency_cols = st.columns(2)
            sorted_latencies = sorted(
                [(k, v) for k, v in node_latency.items() if k != "total_query"],
                key=lambda x: x[1],
                reverse=True
            )
            
            for idx, (node_name, latency_ms) in enumerate(sorted_latencies):
                col = latency_cols[idx % 2]
                with col:
                    pct = (latency_ms / total * 100) if total > 0 else 0
                    st.caption(f"{node_name}: {latency_ms:.2f}s ({pct:.0f}%)")
        else:
            st.caption("No latency data available")
    
    # --- SECTION D: Feedback Widget ---
    st.divider()
    st.markdown("### 👍 Was this answer helpful?")
    
    # Initialize session state for feedback
    if "last_feedback_query" not in st.session_state:
        st.session_state.last_feedback_query = None
    if "feedback_rating" not in st.session_state:
        st.session_state.feedback_rating = None
    
    feedback_cols = st.columns(2)
    
    with feedback_cols[0]:
        if st.button("👍 Yes, helpful!", use_container_width=True, key="feedback_yes"):
            st.session_state.feedback_rating = "positive"
            st.session_state.last_feedback_query = query_input
    
    with feedback_cols[1]:
        if st.button("👎 No, needs work", use_container_width=True, key="feedback_no"):
            st.session_state.feedback_rating = "negative"
            st.session_state.last_feedback_query = query_input
    
    # Show comment field if feedback was given
    if st.session_state.feedback_rating and st.session_state.last_feedback_query == query_input:
        feedback_comment = st.text_area(
            "Optional: What could be improved?",
            height=80,
            key=f"feedback_comment_{query_input[:20]}"
        )
        
        if st.button("📤 Submit Feedback", use_container_width=True, key="submit_feedback"):
            try:
                # Import feedback functions
                init_db, save_feedback, get_stats = get_feedback_functions()
                if save_feedback:
                    init_db()
                    # Save feedback
                    record = {
                        "query": query_input,
                        "agent_routed": domain,
                        "domain": domain,
                        "confidence": confidence,
                        "retrieved_chunk_ids": [c.get("chunk_id", "") for c in citations],
                        "generated_answer": answer,
                        "rating": st.session_state.feedback_rating,
                        "free_text": feedback_comment if feedback_comment.strip() else None,
                        "faithfulness_score": eval_scores.get("faithfulness_score"),
                        "llm_judge_score": eval_scores.get("llm_judge_score")
                    }
                    
                    feedback_id = save_feedback(record)
                    st.success(f"✅ Thank you for your feedback! (ID: {feedback_id[:8]}...)")
                    
                    # Reset feedback state
                    st.session_state.feedback_rating = None
                    st.session_state.last_feedback_query = None
            
            except Exception as e:
                st.error(f"Failed to save feedback: {e}")


# --- Conversation History (Last 5 turns) ---
if st.session_state.history:
    st.divider()
    st.subheader("📜 Conversation History (Last 5 turns)")
    
    for turn in st.session_state.history[-5:]:
        with st.expander(f"Q: {turn['query'][:60]}..."):
            st.text(f"Timestamp: {turn['timestamp']}")
            st.markdown(turn['result'].get('final_answer', 'N/A'))

# --- Debug Footer: Page Load Time ---
if "DEBUG_RELOAD_TIMING" in os.environ:
    page_load_time = time.time() - _PAGE_LOAD_START
    st.divider()
    with st.expander("⏱️ Debug: Page Load Timing"):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Page Reload Time", f"{page_load_time:.3f}s")
        with col2:
            st.caption("First reload: slower (imports loaded)\nSecond reload: faster (cached)")
        st.info("💡 To enable: `export DEBUG_RELOAD_TIMING=1` then restart Streamlit")

