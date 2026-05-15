"""
Test actual routing of support queries through Claude classifier.
Print domain and confidence for each query.
"""

import json
import sys
sys.path.insert(0, ".")

from orchestrator.intent_classifier import classify

# Load support queries from golden set
with open("evaluation/golden_set.jsonl", "r") as f:
    lines = [line.strip() for line in f if line.strip()]
    golden_set = [json.loads(line) for line in lines]

support_queries = [item for item in golden_set if item["agent"] == "support"]

print("\n" + "="*120)
print(f"SUPPORT QUERY ROUTING TEST ({len(support_queries)} queries)")
print("="*120 + "\n")

failing_queries = []

for i, item in enumerate(support_queries, 1):
    query = item["query"]
    classification = classify(query)
    
    status = "✅" if classification.domain == "support" else "❌"
    
    print(f"{status} Query {i}: {query[:80]}...")
    print(f"   Domain: {classification.domain:15s} | Confidence: {classification.confidence:.2f}")
    print(f"   Reasoning: {classification.reasoning}")
    
    if classification.domain != "support":
        failing_queries.append({
            "num": i,
            "query": query,
            "routed_to": classification.domain,
            "confidence": classification.confidence,
            "reasoning": classification.reasoning
        })
    print()

print(f"\n{'='*120}")
print(f"SUMMARY: {len(support_queries) - len(failing_queries)}/{len(support_queries)} routing to support")
print(f"         {len(failing_queries)}/{len(support_queries)} routing incorrectly")
print(f"{'='*120}\n")

if failing_queries:
    print("FAILING QUERIES:\n")
    for item in failing_queries:
        print(f"Query {item['num']}: {item['query']}")
        print(f"  ❌ Routed to: {item['routed_to']} (confidence {item['confidence']:.2f})")
        print(f"  Reasoning: {item['reasoning']}\n")
