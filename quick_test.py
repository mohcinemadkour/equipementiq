#!/usr/bin/env python3
"""Quick test of orchestrator."""

from dotenv import load_dotenv
load_dotenv()

from orchestrator.graph import run_query

query = "What does SPN-CR-001 mean?"

try:
    result = run_query(query)
    print(f"✅ Query successful")
    print(f"   Domain: {result['domain']}")
    print(f"   Confidence: {result['confidence']}")
except Exception as e:
    err_str = str(e)
    print(f"❌ Query failed")
    print(f"   Error: {err_str[:300]}")
