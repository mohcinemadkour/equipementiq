"""
Identify which software/mechanical queries are being misrouted to support.
"""

import json
import sys
sys.path.insert(0, ".")

from orchestrator.intent_classifier import classify

# Load golden set
with open("evaluation/golden_set.jsonl", "r") as f:
    lines = [line.strip() for line in f if line.strip()]
    golden_set = [json.loads(line) for line in lines]

domain_map = {"software": "software", "mechanical": "mechanical", "support": "support"}

print(f"\n{'='*120}")
print(f"MISROUTED QUERIES (queries routing to wrong domain)")
print(f"{'='*120}\n")

misrouted = []

for item in golden_set:
    query = item["query"]
    expected_domain = domain_map[item["agent"]]
    classification = classify(query)
    
    if classification.domain != expected_domain and expected_domain != "support":
        # Only show non-support queries that are being misrouted
        misrouted.append({
            "query": query,
            "expected": expected_domain,
            "routed_to": classification.domain,
            "confidence": classification.confidence,
            "reasoning": classification.reasoning
        })

if misrouted:
    for i, item in enumerate(misrouted, 1):
        print(f"Misrouted Query {i}:")
        print(f"  Query: {item['query']}")
        print(f"  Expected: {item['expected']}")
        print(f"  ❌ Routed to: {item['routed_to']} (confidence {item['confidence']:.2f})")
        print(f"  Reasoning: {item['reasoning'][:100]}...")
        print()
else:
    print("No misrouted queries found!")
