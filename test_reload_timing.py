#!/usr/bin/env python3
"""
Test script to measure Streamlit reload performance.
This shows how long browser reloads take with and without caching.
"""

import subprocess
import time
import os

def test_reload_timing():
    """Run Streamlit with debug timing enabled."""
    
    print("\n" + "="*70)
    print("STREAMLIT RELOAD TIMING TEST")
    print("="*70)
    
    print("""
📝 Testing reload performance with @st.cache_resource
    
INSTRUCTIONS:
1. When Streamlit starts, it will show a "Debug" section at the bottom
2. Refresh the page multiple times (Press F5)
3. Check the "⏱️ Debug: Page Load Timing" section
4. Compare times:
   - First reload: Should include module loading time (~1-3s depending on system)
   - Subsequent reloads: Should be faster because @st.cache_resource cached the orchestrator

EXPECTED BEHAVIOR:
✅ First reload: ~1-3 seconds (includes imports)
✅ Second+ reloads: ~0.5-1 second (cached, much faster)
❌ If all reloads are slow: Caching might not be working

KEY METRICS TO WATCH:
- "Page Reload Time" in the debug section
- Whether time improves on subsequent F5 presses
- If latency breakdown shows "total_query" time (from orchestrator)

QUICK TEST:
1. Press F5 three times
2. Check the debug timing each time
3. Third reload should be fastest
""")
    
    print("\n🚀 Starting Streamlit app with debug mode enabled...")
    print("   Command: DEBUG_RELOAD_TIMING=1 streamlit run ui/app.py --server.port 8501")
    print("\n📍 Open http://localhost:8501 in your browser")
    print("   Then press F5 multiple times and watch the reload times\n")
    
    # Set debug mode
    env = os.environ.copy()
    env["DEBUG_RELOAD_TIMING"] = "1"
    
    # Start Streamlit
    try:
        subprocess.run(
            [".venv/Scripts/streamlit", "run", "ui/app.py", "--server.port", "8501"],
            env=env,
            cwd="."
        )
    except KeyboardInterrupt:
        print("\n\n✅ Test stopped by user")
        print("Summary: Check the browser debug section for reload times")

if __name__ == "__main__":
    test_reload_timing()
