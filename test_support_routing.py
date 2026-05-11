#!/usr/bin/env python3
"""Test one support query through the orchestrator to verify routing fix."""

import os
import json
from dotenv import load_dotenv
from orchestrator.graph import run_query

load_dotenv()

# Test query from our golden set that was being misclassified
test_query = "Tool changing takes longer than normal"

print("Testing support query routing through orchestrator:")
print("=" * 80)
print(f"Query: {test_query}\n")

# Run through the orchestrator
result = run_query(test_query)

print(f"Domain: {result['domain']}")
print(f"Confidence: {result['confidence']:.2f}")
print(f"Reasoning: {result['reasoning']}")
print(f"\nAgents used: {result['agents_used']}")
print(f"\nRetrieved documents:")

merged_context = result.get('merged_context', '')
if merged_context:
    # Extract chunk_ids from merged context
    lines = merged_context.split('\n')
    for line in lines:
        if 'SOURCE:' in line or 'chunk_id' in line.lower():
            print(f"  {line.strip()}")
else:
    print("  (no merged context)")

print(f"\nFinal answer (first 200 chars):")
print(f"{result['final_answer'][:200]}")

# Verify routing
expected_domain = "support"
if result['domain'] == expected_domain and result['confidence'] >= 0.80:
    print(f"\n✅ SUCCESS: Query correctly routed to {expected_domain} domain with confidence {result['confidence']:.2f}")
else:
    print(f"\n❌ FAIL: Query routed to {result['domain']} with confidence {result['confidence']:.2f}")
    print(f"   Expected: {expected_domain} with confidence >= 0.80")
