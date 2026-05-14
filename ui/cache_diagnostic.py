"""
Test if Streamlit @st.cache_resource is working properly.
This validates that agents/orchestrator are being cached across reruns.
"""

import streamlit as st
import time
from functools import lru_cache

# Test 1: Check if cached function gets called only once
call_count = 0

@st.cache_resource
def get_test_resource():
    """Should only initialize once per session."""
    global call_count
    call_count += 1
    print(f"[INIT] get_test_resource called (call #{call_count})")
    time.sleep(0.1)  # Simulate initialization
    return {"value": f"initialized on call {call_count}"}

# Test 2: Check if orchestrator is cached
@st.cache_resource
def get_orchestrator():
    """Should initialize once per session."""
    print("[INIT] Initializing orchestrator...")
    start = time.time()
    from orchestrator.graph import run_query
    elapsed = time.time() - start
    print(f"[INIT] Orchestrator initialized in {elapsed:.2f}s")
    return {"run_query": run_query, "init_time": elapsed}

# Main page
st.title("Streamlit Cache Diagnostic")

st.write("This page tests if @st.cache_resource is working properly.")

# Test resource caching
st.subheader("Test 1: Basic Resource Caching")
resource = get_test_resource()
st.metric("Resource value", resource["value"])
st.write(f"Call count on this run: {call_count}")

# Test orchestrator caching
st.subheader("Test 2: Orchestrator Caching")
orchestrator = get_orchestrator()
st.metric("Orchestrator init time", f"{orchestrator['init_time']:.2f}s")

# Test query
st.subheader("Test 3: Query Latency")
query_text = st.text_input("Enter query:", value="What does error SPN-CR-001 mean?")

if st.button("Run Query"):
    with st.spinner("Running query..."):
        start = time.time()
        result = orchestrator["run_query"](query_text)
        elapsed = time.time() - start
    
    st.success(f"Query completed in {elapsed:.2f}s")
    
    # Show latency breakdown
    node_latency = result.get("node_latency", {})
    if node_latency:
        total = node_latency.get("total_query", 0)
        st.metric("Total latency", f"{total:.2f}s")
        
        st.write("**Latency breakdown:**")
        for node_name, latency in sorted(node_latency.items(), key=lambda x: x[1], reverse=True):
            if node_name != "total_query":
                pct = (latency / total * 100) if total > 0 else 0
                st.write(f"- {node_name}: {latency:.2f}s ({pct:.0f}%)")

st.info("💡 If you refresh this page multiple times, you should see 'call #1' consistently, proving caching is working.")
