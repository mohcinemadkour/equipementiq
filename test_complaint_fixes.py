#!/usr/bin/env python
"""Test script to verify complaint query routing and formatting fixes."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import run_query

def test_query(num: int, query: str, expected_format: str):
    """Test a single query and print results."""
    print(f"\n{'='*80}")
    print(f"TEST {num}: {query}")
    print(f"Expected format: {expected_format}")
    print(f"{'='*80}\n")
    
    result = run_query(query)
    
    print(f"Domain: {result.get('domain', 'unknown')}")
    print(f"Confidence: {result.get('confidence', 'unknown')}")
    print(f"Agents used: {', '.join(result.get('agents_used', []))}")
    print(f"\nFull Answer:\n{result.get('final_answer', 'NO ANSWER')}")
    print(f"\nCitations: {result.get('citations', [])}")
    
    return result

if __name__ == "__main__":
    # Test 1: Complaint listing query for error code
    result1 = test_query(
        1,
        "what are all complaints related to AXS-SR-001?",
        "COMPLAINT LIST FORMAT (case ID, machine, finding, remedy, RMA)"
    )
    
    # Test 2: Error code definition query
    result2 = test_query(
        2,
        "what does AXS-SR-001 mean?",
        "ERROR CODE DEFINITION FORMAT (Definition/Meaning, Root Cause, Diagnostic Steps, Remediation)"
    )
    
    # Test 3: Complaint query with machine filter
    result3 = test_query(
        3,
        "have customers reported AXS-SR-001 on M02?",
        "COMPLAINT LIST FORMAT (case ID, machine, finding, remedy, RMA)"
    )
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Query 1 - Domain: {result1.get('domain')} (should be cross_domain)")
    print(f"Query 2 - Domain: {result2.get('domain')} (should be software)")
    print(f"Query 3 - Domain: {result3.get('domain')} (should be cross_domain)")
