#!/usr/bin/env python3
"""Verify escalation_path field is retrievable in synthesised answers."""

import sys
from pathlib import Path

# Add workspace to path
workspace = Path(__file__).parent
sys.path.insert(0, str(workspace))

from orchestrator.graph import run_query

# Test queries covering different error codes with escalation paths
test_queries = [
    {
        "query": "SPN-SR-003 is active. If I ignore it, what fires next?",
        "expected_codes": ["SPN-MJ-002", "SPN-CR-001", "VIB-WN-060"],
        "label": "SPN-SR-003 escalation"
    },
    {
        "query": "AXS-SR-001 is showing. What happens if I do not fix it?",
        "expected_codes": ["SPN-MJ-004", "AXS-MJ-001", "VIB-WN-060"],
        "label": "AXS-SR-001 escalation"
    },
    {
        "query": "VIB-MJ-001 triggered. What is the escalation path?",
        "expected_codes": ["VIB-CR-001", "SPN-MJ-002", "VIB-SR-001"],
        "label": "VIB-MJ-001 escalation"
    },
]

print("=" * 90)
print("VERIFICATION: Escalation Path Queries")
print("=" * 90)
print()

for i, test_case in enumerate(test_queries, 1):
    print(f"TEST {i}: {test_case['label']}")
    print(f"Query: {test_case['query']}")
    print()

    try:
        # Run query through orchestrator
        result = run_query(test_case["query"])

        # Check result structure
        answer = result.get("final_answer", "")
        domain = result.get("domain", "unknown")
        confidence = result.get("confidence", 0.0)
        citations = result.get("citations", [])

        print(f"  Domain: {domain} (confidence: {confidence:.1%})")
        print(f"  Answer: {answer[:200]}...")
        print(f"  Found {len(citations)} citation(s)")

        # Check if escalation is mentioned
        if "escalat" in answer.lower():
            print("  ✓ ESCALATION CONTEXT RETRIEVED")
        else:
            print("  ⚠ WARNING: Escalation context not found in answer")

        # Check for INSUFFICIENT_CONTEXT
        if "INSUFFICIENT_CONTEXT" in answer:
            print("  ✗ FAIL: INSUFFICIENT_CONTEXT returned")
        else:
            print("  ✓ PASS: Answer provided without INSUFFICIENT_CONTEXT")

    except Exception as e:
        print(f"  ✗ ERROR: {e}")

    print()
    print("-" * 90)
    print()

print("=" * 90)
print("VERIFICATION COMPLETE")
print("=" * 90)
