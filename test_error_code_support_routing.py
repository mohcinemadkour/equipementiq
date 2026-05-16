#!/usr/bin/env python3
"""
Test script: Verify new error code + support keyword routing rule.

Tests the updated _rule_based_classify function with three test queries:
1. "what are all complaints related to AXS-SR-001?" → Expected: cross_domain
2. "what does AXS-SR-001 mean?" → Expected: software
3. "have customers reported AXS-SR-001 on M01?" → Expected: cross_domain
"""

import sys
sys.path.insert(0, ".")

from orchestrator.intent_classifier import _rule_based_classify

# Test queries
test_queries = [
    {
        "query": "what are all complaints related to AXS-SR-001?",
        "expected_domain": "cross_domain",
        "reason": "Error code + support keyword (complaints)"
    },
    {
        "query": "what does AXS-SR-001 mean?",
        "expected_domain": "software",
        "reason": "Error code only, no support keyword"
    },
    {
        "query": "have customers reported AXS-SR-001 on M01?",
        "expected_domain": "cross_domain",
        "reason": "Error code + support keyword (customers reported)"
    }
]

print("=" * 120)
print("TESTING ERROR CODE + SUPPORT KEYWORD ROUTING")
print("=" * 120)
print()

all_passed = True

for i, test in enumerate(test_queries, 1):
    query = test["query"]
    expected = test["expected_domain"]
    reason = test["reason"]
    
    # Run classification
    result = _rule_based_classify(query)
    
    if result is None:
        actual = "None (deferred to Claude)"
        status = "[FAIL]" if expected != "None" else "[PASS]"
    else:
        actual = result.domain
        status = "[PASS]" if actual == expected else "[FAIL]"
        if actual != expected:
            all_passed = False
    
    print(f"Test {i}: {status}")
    print(f"  Query: {query}")
    print(f"  Expected: {expected} | Actual: {actual}")
    print(f"  Reason: {reason}")
    if result:
        print(f"  Confidence: {result.confidence}")
        print(f"  Routing Reasoning: {result.reasoning}")
    print()

print("=" * 120)
if all_passed:
    print("[SUCCESS] ALL TESTS PASSED")
else:
    print("[FAILURE] SOME TESTS FAILED")
print("=" * 120)
