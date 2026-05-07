#!/usr/bin/env python3
"""Pre-merge E2E test for orchestrator"""

import os
import sys

# Check if we have valid API keys
anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()

if not anthropic_key or anthropic_key.upper() in ["REPLACE_ME", "YOUR_API_KEY", ""]:
    print("⚠️  ANTHROPIC_API_KEY not configured - E2E test skipped")
    print("This is expected for CI/CD - set ANTHROPIC_API_KEY in .env to run live test")
    sys.exit(0)

try:
    from orchestrator.graph import run_query
    print("🔍 Running live E2E query...")
    result = run_query('What causes error SPN-CR-001 and what is the remedy?')
    print(f"✅ Domain: {result.get('domain', 'N/A')}")
    print(f"✅ Confidence: {result.get('confidence', 'N/A')}")
    print(f"✅ Citations: {len(result.get('citations', []))}")
    answer = result.get('final_answer', '')
    print(f"✅ Answer preview: {answer[:300] if answer else 'No answer'}")
    print("\n✅ E2E test passed!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
