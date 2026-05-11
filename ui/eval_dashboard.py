"""EquipmentIQ Evaluation Dashboard."""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="EquipmentIQ Evaluation Dashboard",
    page_icon="📊",
    layout="wide"
)

from feedback.feedback_store import get_stats, get_feedback
from feedback.correlation_monitor import correlate
from evaluation.retrieval_metrics import evaluate_collection

st.title("📊 EquipmentIQ — Evaluation Dashboard")
st.markdown("Monitor system performance, feedback metrics, and data quality.")
st.divider()

# --- Summary Metrics ---
st.subheader("📈 Key Metrics")

try:
    stats = get_stats()
    
    metric_cols = st.columns(4)
    
    with metric_cols[0]:
        st.metric(
            "Total Feedback",
            stats.get("total", 0),
            help="Total feedback records collected"
        )
    
    with metric_cols[1]:
        avg_faith = stats.get("avg_faithfulness", 0.0)
        st.metric(
            "Avg Faithfulness",
            f"{avg_faith:.2f}",
            help="Average RAGAS Faithfulness score (target: ≥0.80)"
        )
    
    with metric_cols[2]:
        avg_judge = stats.get("avg_llm_judge", 0.0)
        st.metric(
            "Avg LLM Judge",
            f"{avg_judge:.1f} / 5",
            help="Average LLM Judge score (1-5 scale)"
        )
    
    with metric_cols[3]:
        total = stats.get("total", 1)
        positive = stats.get("positive", 0)
        positive_rate = (positive / total * 100) if total > 0 else 0
        st.metric(
            "Positive Feedback Rate",
            f"{positive_rate:.1f}%",
            help="Percentage of positive feedback"
        )

except Exception as e:
    st.error(f"Failed to load stats: {e}")

st.divider()

# --- Retrieval Evaluation ---
st.subheader("🔍 Retrieval Evaluation")

col_eval = st.columns([1, 4])
with col_eval[0]:
    if st.button("▶️ Run Evaluation", use_container_width=True):
        st.session_state.run_eval = True

if st.session_state.get("run_eval", False):
    with st.spinner("Evaluating retrieval metrics..."):
        try:
            # Load golden set
            golden_path = Path("evaluation/golden_set.jsonl")
            if golden_path.exists():
                results = []
                with open(golden_path) as f:
                    for line in f:
                        results.append(json.loads(line))
                
                # Display results as table
                df_results = pd.DataFrame(results)
                st.dataframe(df_results, use_container_width=True)
                
                st.success("✅ Retrieval evaluation complete!")
            else:
                st.warning("Golden set not found at evaluation/golden_set.jsonl")
        
        except Exception as e:
            st.error(f"Evaluation failed: {e}")

st.divider()

# --- Feedback Breakdown ---
st.subheader("📊 Feedback Breakdown by Agent")

try:
    stats = get_stats()
    by_agent = stats.get("by_agent", {})
    
    if by_agent:
        df_agents = pd.DataFrame(
            list(by_agent.items()),
            columns=["Agent", "Count"]
        )
        st.bar_chart(df_agents.set_index("Agent"))
    else:
        st.info("No feedback data yet.")

except Exception as e:
    st.error(f"Failed to load agent breakdown: {e}")

st.divider()

# --- Failure Modes ---
st.subheader("❌ Failure Mode Distribution")

try:
    stats = get_stats()
    by_failure = stats.get("by_failure_mode", {})
    
    if by_failure:
        df_failures = pd.DataFrame(
            list(by_failure.items()),
            columns=["Failure Mode", "Count"]
        )
        st.bar_chart(df_failures.set_index("Failure Mode"))
    else:
        st.info("No failure mode data yet.")

except Exception as e:
    st.error(f"Failed to load failure modes: {e}")

st.divider()

# --- Discordant Cases ---
st.subheader("⚠️ Metric Calibration Status")

try:
    corr_result = correlate(limit=50)
    
    metric_flag = corr_result.get("metric_calibration_flag", False)
    summary = corr_result.get("summary", "")
    
    if metric_flag:
        st.warning(f"⚠️ Metric Calibration Issue Detected\n\n{summary}")
    else:
        st.success(f"✅ Metrics Look Good\n\n{summary}")
    
    # Show discordant cases
    discordant = corr_result.get("discordant_cases", [])
    if discordant:
        st.subheader("🔴 Discordant Cases (negative rating ∧ high faithfulness)")
        
        df_discordant = pd.DataFrame(discordant)
        
        # Format display
        df_display = df_discordant[["feedback_id", "query", "rating", "faithfulness_score", "failure_mode"]].copy()
        df_display.columns = ["Feedback ID", "Query", "Rating", "Faithfulness", "Failure Mode"]
        df_display["Faithfulness"] = df_display["Faithfulness"].apply(lambda x: f"{x:.2f}")
        
        st.dataframe(df_display, use_container_width=True)

except Exception as e:
    st.error(f"Failed to load correlation analysis: {e}")

st.divider()

# --- Recent Feedback ---
st.subheader("📝 Recent Feedback")

try:
    recent = get_feedback(limit=20)
    
    if recent:
        df_recent = pd.DataFrame(recent)
        
        # Select columns for display
        display_cols = ["feedback_id", "timestamp", "query", "rating", "agent_routed", "failure_mode"]
        df_display = df_recent[[col for col in display_cols if col in df_recent.columns]]
        
        # Rename for display
        df_display.columns = [col.replace("_", " ").title() for col in df_display.columns]
        
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No feedback yet.")

except Exception as e:
    st.error(f"Failed to load recent feedback: {e}")
