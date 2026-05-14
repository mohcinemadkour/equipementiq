"""EquipmentIQ Evaluation Dashboard."""

import streamlit as st
import pandas as pd
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

# Ensure parent directory is in path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="EquipmentIQ Evaluation Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main container styling */
    .main {
        padding-top: 0.5rem;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 600;
    }
    
    /* Better spacing for sections */
    .css-1r6slur {
        margin-bottom: 0.5rem;
    }
    
    /* Improve expander styling */
    .streamlit-expanderHeader {
        background-color: rgba(0, 100, 255, 0.05);
        border-radius: 4px;
    }
    
    /* Better table styling */
    .streamlit-dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Deferred imports
def get_feedback_functions():
    """Load feedback functions lazily."""
    try:
        from feedback.feedback_store import get_stats, get_feedback
        from feedback.correlation_monitor import correlate
        return get_stats, get_feedback, correlate
    except Exception as e:
        st.error(f"Cannot load feedback functions: {e}")
        return None, None, None

def get_retrieval_eval():
    """Load retrieval evaluation lazily."""
    try:
        from evaluation.retrieval_metrics import evaluate_collection
        return evaluate_collection
    except Exception as e:
        st.error(f"Cannot load evaluation functions: {e}")
        return None

def compute_routing_accuracy() -> Dict[str, Any]:
    """
    Compute routing accuracy from golden set.
    Returns: {accuracy (0-1), correct, total, by_agent breakdown, errors list}
    """
    try:
        from orchestrator import run_query
        
        golden_path = Path("evaluation/golden_set.jsonl")
        if not golden_path.exists():
            return {"error": "Golden set not found"}
        
        correct = 0
        total = 0
        errors = []
        by_agent = {"mechanical": {"correct": 0, "total": 0},
                    "software": {"correct": 0, "total": 0},
                    "support": {"correct": 0, "total": 0}}
        
        with open(golden_path) as f:
            queries = [json.loads(line) for line in f if line.strip()]
        
        for q in queries:
            expected_agent = q.get("agent")
            if not expected_agent:
                continue
            
            total += 1
            by_agent[expected_agent]["total"] += 1
            
            # Run through orchestrator (lightweight classification only)
            try:
                result = run_query(q["query"])
                routed_domain = result.get("domain", "unknown")
                
                if routed_domain == expected_agent:
                    correct += 1
                    by_agent[expected_agent]["correct"] += 1
            except Exception as e:
                errors.append(f"Query '{q['query'][:30]}...': {str(e)[:60]}")
        
        accuracy = correct / total if total > 0 else 0.0
        
        return {
            "accuracy": accuracy,
            "correct": correct,
            "total": total,
            "by_agent": by_agent,
            "errors": errors
        }
    except Exception as e:
        return {"error": f"Fatal: {str(e)}"}

def load_latest_batch_eval() -> Dict[str, Any]:
    """Load latest batch evaluation results."""
    try:
        results_dir = Path("evaluation/results")
        if not results_dir.exists():
            return {}
        
        # Find latest batch_*.jsonl file
        batch_files = sorted(results_dir.glob("batch_*.jsonl"), reverse=True)
        if not batch_files:
            return {}
        
        with open(batch_files[0]) as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"Could not load batch eval: {e}")
        return {}

st.title("📊 EquipmentIQ — Continuous Evaluation Dashboard")
st.markdown("""
<div style="text-align: center; margin-bottom: 1.5rem; padding: 0.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; color: white;">
    <p style="font-size: 1.1rem; margin: 0; font-weight: 500;">🔬 Real-time monitoring of system performance, retrieval metrics, and feedback signals</p>
    <p style="font-size: 0.9rem; margin: 0.25rem 0 0 0; opacity: 0.9;">Last updated: {}</p>
</div>
""".format(pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
st.divider()

# --- Dashboard Controls ---
st.subheader("⚙️ Dashboard Controls")

control_cols = st.columns([2, 2, 1, 1])

with control_cols[0]:
    refresh_interval = st.selectbox(
        "Auto-refresh interval",
        ["Off", "30s", "1m", "5m"],
        index=0,
        help="Automatically reload metrics at selected interval"
    )

with control_cols[1]:
    if st.button("🔄 Run Full Evaluation", use_container_width=True, help="Run complete evaluation pipeline (retrieval + generation + drift)"):
        st.info("📊 Starting full evaluation... This will take 2-5 minutes.")
        try:
            from evaluation.batch_eval import run_batch_eval, save_results
            result = run_batch_eval()
            save_results(result)
            st.success("✅ Evaluation complete! Reloading metrics...")
            st.rerun()
        except Exception as e:
            import traceback
            error_msg = f"**Evaluation Error:**\n\n{str(e)}\n\n**Full Traceback:**\n```\n{traceback.format_exc()}\n```"
            st.error(error_msg)

with control_cols[2]:
    if st.button("🔄 Refresh", use_container_width=True, help="Reload current metrics"):
        st.rerun()

with control_cols[3]:
    if st.button("💾 Export", use_container_width=True, help="Export evaluation results"):
        st.info("📥 Export feature coming soon")

st.divider()

# --- Summary Metrics ---
st.subheader("📈 Core Metrics")

try:
    # Load latest batch eval results
    batch_eval = load_latest_batch_eval()
    get_stats, get_feedback, correlate = get_feedback_functions()
    
    if get_stats:
        stats = get_stats()
    
    # Create four-column layout for core metrics
    metric_cols = st.columns(4, gap="medium")
    
    # Column 1: Routing Accuracy
    with metric_cols[0]:
        with st.container(border=True):
            st.markdown("### 🎯 Routing")
            if st.button("Compute", key="route_accuracy_btn", use_container_width=True):
                with st.spinner("Computing..."):
                    route_result = compute_routing_accuracy()
                    if "error" not in route_result:
                        accuracy_pct = route_result["accuracy"] * 100
                        emoji = "🟢" if accuracy_pct >= 95 else ("🟡" if accuracy_pct >= 80 else "🔴")
                        st.metric(
                            f"{emoji} Accuracy",
                            f"{accuracy_pct:.1f}%",
                            f"{route_result['correct']}/{route_result['total']}"
                        )
                        
                        # Breakdown by agent
                        st.markdown("**Breakdown:**")
                        for agent, data in route_result["by_agent"].items():
                            if data["total"] > 0:
                                acc = data['correct']/data['total']*100
                                st.caption(f"  {agent.title()}: {acc:.0f}% ({data['correct']}/{data['total']})")
                        
                        # Show errors if any
                        if route_result.get("errors"):
                            with st.expander(f"⚠️ {len(route_result['errors'])} errors"):
                                for err in route_result["errors"][:5]:
                                    st.caption(f"• {err}")
                    else:
                        st.error(route_result["error"])
            else:
                st.metric("Accuracy", "—")
    
    # Column 2: Retrieval Metrics (NDCG@5)
    with metric_cols[1]:
        with st.container(border=True):
            st.markdown("### 📊 Retrieval")
            if batch_eval and "retrieval" in batch_eval:
                retrieval = batch_eval["retrieval"]
                ndcg_scores = [v.get("ndcg", 0) for v in retrieval.values()]
                avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0
                
                emoji = "🟢" if avg_ndcg >= 0.70 else ("🟡" if avg_ndcg >= 0.60 else "🔴")
                st.metric(f"{emoji} NDCG@5", f"{avg_ndcg:.3f}")
                
                hit_scores = [v.get("hit_at_5", 0) for v in retrieval.values()]
                avg_hit = sum(hit_scores) / len(hit_scores) if hit_scores else 0.0
                st.metric("Hit@5", f"{avg_hit:.3f}")
            else:
                st.metric("NDCG@5", "—")
                st.metric("Hit@5", "—")
    
    # Column 3: Faithfulness
    with metric_cols[2]:
        with st.container(border=True):
            st.markdown("### 🧠 Faithfulness")
            if batch_eval and "generation" in batch_eval:
                gen = batch_eval["generation"]
                faithfulness = gen.get("faithfulness", 0.0)
                emoji = "🟢" if faithfulness >= 0.80 else ("🟡" if faithfulness >= 0.70 else "🔴")
                st.metric(f"{emoji} Score", f"{faithfulness:.3f}")
                st.caption(f"Target: ≥0.80")
            else:
                st.metric("Score", "—")
    
    # Column 4: Judge Score
    with metric_cols[3]:
        with st.container(border=True):
            st.markdown("### ⭐ Judge Rating")
            if batch_eval and "generation" in batch_eval:
                gen = batch_eval["generation"]
                judge = gen.get("llm_judge_avg", 0.0)
                emoji = "🟢" if judge >= 4.0 else ("🟡" if judge >= 3.5 else "🔴")
                st.metric(f"{emoji} Avg", f"{judge:.2f}/5")
            else:
                st.metric("Avg", "—")

except Exception as e:
    st.error(f"Failed to load metrics: {e}")

st.divider()

# --- Detailed Retrieval Metrics Table ---
st.subheader("� Retrieval Metrics by Agent")

try:
    batch_eval = load_latest_batch_eval()
    
    if batch_eval and "retrieval" in batch_eval:
        retrieval_data = batch_eval["retrieval"]
        
        # Prepare per-agent metrics table
        metrics_rows = []
        for agent, metrics in retrieval_data.items():
            ndcg = metrics.get('ndcg', 0.0)
            emoji = "🟢" if ndcg >= 0.70 else ("🟡" if ndcg >= 0.60 else "🔴")
            
            metrics_rows.append({
                "Agent": f"{emoji} {agent.title()}",
                "NDCG@5": f"{ndcg:.3f}",
                "Hit@5": f"{metrics.get('hit_at_5', 0.0):.3f}",
                "MRR": f"{metrics.get('mrr', 0.0):.3f}",
                "Queries": metrics.get('queries_evaluated', 0),
                "Status": "✅ PASS" if ndcg >= 0.70 else "⚠️ CHECK"
            })
        
        df_retrieval = pd.DataFrame(metrics_rows)
        st.dataframe(df_retrieval, use_container_width=True, hide_index=True)
        
        # Show batch eval metadata
        st.caption(f"Last evaluation: {batch_eval.get('timestamp', 'unknown')}")
    else:
        st.info("📋 No batch evaluation results yet. Run full evaluation to populate metrics.")
        
        # Quick retrieval eval button
        if st.button("🚀 Run Quick Retrieval Eval", use_container_width=True):
            with st.spinner("Computing NDCG@5, Hit@5, MRR..."):
                try:
                    from evaluation.batch_eval import run_batch_eval
                    result = run_batch_eval()
                    
                    if result:
                        st.rerun()
                except Exception as e:
                    st.error(f"Evaluation failed: {e}")

except Exception as e:
    st.error(f"Failed to display retrieval metrics: {e}")

st.divider()

# --- Generation Quality Metrics ---
st.subheader("🧠 Generation Quality")

try:
    batch_eval = load_latest_batch_eval()
    
    if batch_eval and "generation" in batch_eval:
        gen = batch_eval["generation"]
        
        gen_cols = st.columns(3, gap="medium")
        
        with gen_cols[0]:
            with st.container(border=True):
                faith = gen.get("faithfulness", 0.0)
                emoji = "🟢" if faith >= 0.80 else ("🟡" if faith >= 0.70 else "🔴")
                st.markdown(f"### {emoji} Faithfulness")
                st.metric("Score", f"{faith:.3f}", delta="Target: 0.80" if faith >= 0.80 else None)
                st.progress(min(faith, 1.0))
        
        with gen_cols[1]:
            with st.container(border=True):
                rel = gen.get("answer_relevance", 0.0)
                emoji = "🟢" if rel >= 0.75 else ("🟡" if rel >= 0.65 else "🔴")
                st.markdown(f"### {emoji} Relevance")
                st.metric("Score", f"{rel:.3f}")
                st.progress(min(rel, 1.0))
        
        with gen_cols[2]:
            with st.container(border=True):
                judge = gen.get("llm_judge_avg", 0.0)
                emoji = "🟢" if judge >= 4.0 else ("🟡" if judge >= 3.5 else "🔴")
                st.markdown(f"### {emoji} Judge Rating")
                st.metric("Avg", f"{judge:.2f}/5")
                st.progress(judge / 5.0)
        
        st.caption(f"📊 Evaluated {gen.get('n_sampled', 0)} queries")
    else:
        st.info("💡 Run full evaluation to see generation metrics")

except Exception as e:
    st.error(f"Failed to display generation metrics: {e}")

st.divider()

# --- Feedback Statistics ---
st.subheader("📝 User Feedback & Signals")

try:
    get_stats, get_feedback, correlate = get_feedback_functions()
    if get_stats:
        stats = get_stats()
    
    # Feedback summary metrics in a nice grid
    fb_cols = st.columns(4, gap="medium")
    
    with fb_cols[0]:
        with st.container(border=True):
            st.markdown("### 📊")
            total = stats.get("total", 0)
            st.metric("Total Feedback", total)
    
    with fb_cols[1]:
        with st.container(border=True):
            st.markdown("### 😊")
            total = stats.get("total", 1)
            positive = stats.get("positive", 0)
            pos_rate = (positive / total * 100) if total > 0 else 0
            emoji = "🟢" if pos_rate >= 80 else ("🟡" if pos_rate >= 60 else "🔴")
            st.metric(f"{emoji} Positive Rate", f"{pos_rate:.1f}%")
    
    with fb_cols[2]:
        with st.container(border=True):
            st.markdown("### 🎯")
            avg_faith = stats.get("avg_faithfulness", 0.0)
            emoji = "🟢" if avg_faith >= 0.80 else ("🟡" if avg_faith >= 0.70 else "🔴")
            st.metric(f"{emoji} Avg Faithfulness", f"{avg_faith:.2f}")
    
    with fb_cols[3]:
        with st.container(border=True):
            st.markdown("### ⭐")
            avg_judge = stats.get("avg_llm_judge", 0.0)
            emoji = "🟢" if avg_judge >= 4.0 else ("🟡" if avg_judge >= 3.5 else "🔴")
            st.metric(f"{emoji} Avg Judge", f"{avg_judge:.1f}/5")
    
    # Feedback charts
    fb_row = st.columns(2, gap="medium")
    
    with fb_row[0]:
        st.markdown("#### By Agent")
        by_agent = stats.get("by_agent", {})
        if by_agent:
            df_agents = pd.DataFrame(
                sorted(by_agent.items(), key=lambda x: x[1], reverse=True),
                columns=["Agent", "Count"]
            )
            st.bar_chart(df_agents.set_index("Agent"), height=250)
        else:
            st.info("💡 No feedback data yet")
    
    with fb_row[1]:
        st.markdown("#### By Failure Mode")
        by_failure = stats.get("by_failure_mode", {})
        if by_failure:
            df_failures = pd.DataFrame(
                sorted(by_failure.items(), key=lambda x: x[1], reverse=True),
                columns=["Failure Mode", "Count"]
            )
            st.bar_chart(df_failures.set_index("Failure Mode"), height=250)
        else:
            st.info("💡 No failure mode data yet")

except Exception as e:
    st.error(f"Failed to load feedback data: {e}")

st.divider()

# --- Discordant Cases & Calibration ---
st.subheader("⚠️ Quality Assurance & Calibration")

try:
    get_stats, get_feedback, correlate = get_feedback_functions()
    if correlate:
        corr_result = correlate(limit=50)
    
    metric_flag = corr_result.get("metric_calibration_flag", False)
    summary = corr_result.get("summary", "")
    
    # Status indicator
    if metric_flag:
        st.warning(
            f"""
        ⚠️ **Metric Calibration Issue Detected**
        
        {summary}
        """,
            icon="⚠️"
        )
    else:
        st.success(
            f"""
        ✅ **Metrics Look Good**
        
        {summary}
        """,
            icon="✅"
        )
    
    # Show discordant cases if any
    discordant = corr_result.get("discordant_cases", [])
    if discordant:
        with st.expander("🔴 View Discordant Cases (Cases needing attention)"):
            df_discordant = pd.DataFrame(discordant)
            
            # Format display
            if not df_discordant.empty:
                df_display = df_discordant[["feedback_id", "query", "rating", "faithfulness_score", "failure_mode"]].copy()
                df_display.columns = ["Feedback ID", "Query", "Rating", "Faithfulness", "Failure Mode"]
                df_display["Faithfulness"] = df_display["Faithfulness"].apply(lambda x: f"{x:.2f}")
                df_display["Query"] = df_display["Query"].apply(lambda x: x[:50] + "..." if len(str(x)) > 50 else x)
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                st.caption(f"Found {len(discordant)} discordant case(s) - investigate for metric calibration")

except Exception as e:
    st.error(f"Failed to load calibration analysis: {e}")

st.divider()

# --- Recent Feedback ---
st.subheader("🎯 Recent Feedback")

try:
    get_stats, get_feedback, correlate = get_feedback_functions()
    if get_feedback:
        recent = get_feedback(limit=20)
    
    if recent and len(recent) > 0:
        df_recent = pd.DataFrame(recent)
        
        # Select columns for display
        display_cols = ["feedback_id", "timestamp", "query", "rating", "agent_routed", "failure_mode"]
        existing_cols = [col for col in display_cols if col in df_recent.columns]
        
        if existing_cols:
            df_display = df_recent[existing_cols].copy()
            
            # Truncate long queries
            if "query" in df_display.columns:
                df_display["query"] = df_display["query"].apply(lambda x: x[:40] + "..." if len(str(x)) > 40 else x)
            
            # Rename for display
            df_display.columns = [col.replace("_", " ").title() for col in df_display.columns]
            
            # Add emoji for rating if available
            if "Rating" in df_display.columns:
                df_display["Rating"] = df_display["Rating"].apply(
                    lambda x: "👍 Positive" if x > 0 else ("👎 Negative" if x < 0 else "➖ Neutral")
                )
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("No feedback records found yet")
    else:
        st.info("💡 No feedback yet. User ratings (👍👎) will appear here.")

except Exception as e:
    st.error(f"Failed to load recent feedback: {e}")

st.divider()

# --- Continuous Evaluation Setup ---
st.subheader("⚙️ System Configuration & Help")

with st.expander("📖 Metrics Guide"):
    st.markdown("""
    ### Key Metrics Explained

    **Routing Accuracy**: Percentage of queries routed to the correct domain (mechanical, software, or support)
    - Target: ≥95%
    - Computed from golden set classifications
    
    **NDCG@5** (Normalized Discounted Cumulative Gain at rank 5):
    - Measures ranking quality of retrieved documents
    - Perfect score: 1.0 (all relevant docs at top)
    - Target: ≥0.70 per agent
    
    **Hit@5**: Fraction of queries with at least one relevant doc in top-5 results
    - Target: ≥0.85
    
    **MRR** (Mean Reciprocal Rank): Average position of first relevant document
    - Higher is better; 1.0 = always first
    
    **Faithfulness**: RAGAS metric measuring factual grounding in source documents
    - Target: ≥0.80
    - Lower = more hallucination risk
    
    **LLM Judge Score**: 1-5 scale human-like evaluation
    - Evaluates factual accuracy, completeness, uncertainty handling, citation quality
    
    **Metric Calibration**: Detects discordant cases (negative feedback despite high faithfulness)
    - May indicate eval metric drift or user expectation mismatch
    """)

with st.expander("🚀 Running Continuous Evaluation"):
    st.markdown("""
    ### How to Set Up Continuous Evaluation
    
    1. **Full Batch Evaluation**:
       - Click "🔄 Run Full Evaluation" above
       - Runs retrieval + generation + drift detection on all 3 agents
       - Takes ~2-5 minutes
       - Saves results to `evaluation/results/batch_*.jsonl`
    
    2. **Routing Accuracy**:
       - Click "Compute Routing Accuracy" in the KPI section
       - Tests intent classification on golden set
       - Shows breakdown by agent
    
    3. **Automated Monitoring**:
       - Set refresh interval (30s, 1m, 5m) at top
       - Dashboard auto-reloads metrics
       - Watches for metric drift and failure spikes
    
    4. **Feedback-Driven Signals**:
       - User ratings (👍👎) feed into failure mode analysis
       - Discordant cases highlight potential eval issues
       - Calibration status shows if metrics need tuning
    """)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    ✅ Dashboard last updated: {} | 
    <a href="#how-to-set-up-continuous-evaluation" style="text-decoration: none;">📖 Help & Configuration</a>
</div>
""".format(pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
