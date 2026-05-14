"""
Streamlit reload diagnostic - tracks what gets reinitialized on page reload.
"""

import sys
from pathlib import Path

# Fix sys.path for module imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import time
from datetime import datetime

# Track initialization events
if "init_events" not in st.session_state:
    st.session_state.init_events = []

def log_event(event_name: str, details: str = ""):
    """Log initialization events with timestamps."""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    event = f"[{ts}] {event_name} {details}"
    print(event)
    st.session_state.init_events.append(event)

# Track orchestrator initialization
@st.cache_resource
def get_orchestrator_cached():
    """This should only initialize ONCE per session."""
    log_event("🔵 INIT", "Orchestrator (cached)")
    start = time.time()
    from orchestrator.graph import run_query
    elapsed = time.time() - start
    log_event("✅ DONE", f"Orchestrator initialized in {elapsed:.2f}s")
    return run_query

# Track chromadb initialization  
@st.cache_resource
def get_chromadb_cached():
    """This should only initialize ONCE per session."""
    log_event("🔵 INIT", "ChromaDB (cached)")
    start = time.time()
    from chromadb import HttpClient
    client = HttpClient(host="localhost", port=8000) if False else None  # Use persistent
    import chromadb
    client = chromadb.PersistentClient(path="./chroma_db")
    elapsed = time.time() - start
    log_event("✅ DONE", f"ChromaDB initialized in {elapsed:.2f}s")
    return client

# Page starts
log_event("📄 PAGE", "Load started")

st.title("Streamlit Reload Diagnostic")
st.write("This page tracks what gets reinitialized when you reload the browser.")

# Initialize cached resources
log_event("📞 CALL", "Getting orchestrator...")
run_query = get_orchestrator_cached()

log_event("📞 CALL", "Getting chromadb...")
client = get_chromadb_cached()

log_event("📄 PAGE", "Load completed")

# Display events
st.subheader("📋 Initialization Events This Session")
st.write("👇 If you refresh the page, new events should appear ONLY for items not cached")

for event in st.session_state.init_events:
    if "INIT" in event:
        st.code(event, language=None)
    elif "DONE" in event:
        st.caption(f"  {event}")
    elif "CALL" in event:
        st.caption(f"  {event}")
    else:
        st.write(event)

# Test query
st.subheader("Test Query")
st.write("Run a query to see end-to-end latency:")

query = st.text_input("Query:", value="What does error SPN-CR-001 mean?")
if st.button("Run"):
    with st.spinner("Querying..."):
        start = time.time()
        result = run_query(query)
        elapsed = time.time() - start
    
    st.success(f"✅ Query completed in {elapsed:.2f}s")
    
    # Show latency breakdown
    node_latency = result.get("node_latency", {})
    if node_latency:
        total = node_latency.get("total_query", 0)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", f"{total:.2f}s")
        with col2:
            st.metric("Domain", result.get("domain"))
        with col3:
            st.metric("Confidence", f"{result.get('confidence'):.1%}")

# Instructions
st.info("""
**How to test:**
1. Run a query to establish baseline
2. Press **F5** to reload the page
3. Check if new "INIT" events appear above
4. If only "CALL" and no new "INIT" = caching works ✅
5. If new "INIT" = modules are being reloaded (slow) ❌

**What should happen:**
- First load: `INIT Orchestrator` + `INIT ChromaDB`
- After reload: No new `INIT` events (both cached)
""")
