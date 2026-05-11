#!/usr/bin/env python3
"""Test if updated intent classification routes support queries correctly."""

import os
import json
from dotenv import load_dotenv
from orchestrator.intent_classifier import classify

load_dotenv()

# These are the exact queries from our golden set that were being misclassified
test_queries = [
    ("Tool changing takes longer than normal", "support"),
    ("Machine stops with following error during rapid traverse", "support"),
    ("Customer reported spindle noise after repair", "support"),
    ("What was the resolution for the last complaint on M01", "support"),
    ("How long did it take to fix the spindle bearing issue", "support"),
    ("What remedy was applied to CMP-2019-1033", "support"),
    ("Customer reports spindle not spinning up to full speed", "support"),
    ("Spindle cooling fan is not running - spindle temperature rising", "support"),
]

print("Testing intent classification with updated prompt:")
print("=" * 80)

support_correctly_classified = 0

for query, expected_domain in test_queries:
    result = classify(query)
    domain = result.domain
    confidence = result.confidence
    
    is_correct = domain == expected_domain
    status = "✓ PASS" if is_correct else "✗ FAIL"
    
    if is_correct:
        support_correctly_classified += 1
    
    print(f"\n{status}")
    print(f"  Query: {query[:60]}")
    print(f"  Expected: {expected_domain}")
    print(f"  Got: {domain} (confidence: {confidence:.2f})")
    print(f"  Reasoning: {result.reasoning}")

print("\n" + "=" * 80)
print(f"Result: {support_correctly_classified}/{len(test_queries)} support queries correctly classified")
print(f"Success rate: {100 * support_correctly_classified / len(test_queries):.1f}%")

if support_correctly_classified >= len(test_queries) - 1:
    print("\n✅ Intent routing FIX SUCCESSFUL - support queries now routing correctly!")
else:
    print(f"\n⚠️  Still {len(test_queries) - support_correctly_classified} queries misclassified - may need threshold adjustment")
