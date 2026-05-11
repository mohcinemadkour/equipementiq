#!/usr/bin/env python3
"""Test if orchestrator can make a single query."""

import os
from dotenv import load_dotenv

load_dotenv()

# Check environment
print(f"ANTHROPIC_API_KEY set: {'ANTHROPIC_API_KEY' in os.environ}")
print(f"OPENAI_API_KEY set: {'OPENAI_API_KEY' in os.environ}")

from orchestrator.graph import run_query

query = "What does error SPN-CR-001 mean?"

try:
    result = run_query(query)
    print(f"✅ Query successful")
    print(f"   Domain: {result.get('domain')}")
    print(f"   Confidence: {result.get('confidence')}")
except Exception as e:
    print(f"❌ Query failed: {str(e)[:200]}")
