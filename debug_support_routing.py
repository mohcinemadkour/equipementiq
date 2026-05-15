"""
Debug support routing issues - identify why 8 support queries are routing to mechanical/cross_domain.
"""

import json
import sys

sys.path.insert(0, "/".join(__file__.split("\\")[:-1]))

from orchestrator.intent_classifier import classify


def main():
    # Load golden set
    with open("evaluation/golden_set.jsonl", "r") as f:
        lines = [line.strip() for line in f if line.strip()]
        golden_set = [json.loads(line) for line in lines]
    
    # Filter support queries
    support_queries = [item for item in golden_set if item["agent"] == "support"]
    
    print(f"\n{'='*100}")
    print(f"SUPPORT QUERY ROUTING ANALYSIS ({len(support_queries)} queries)")
    print(f"{'='*100}\n")
    
    routing_breakdown = {"support": 0, "mechanical": 0, "cross_domain": 0, "software": 0}
    
    for i, item in enumerate(support_queries, 1):
        query = item["query"]
        classification = classify(query)
        
        routing_breakdown[classification.domain] += 1
        
        status = "✅" if classification.domain == "support" else "❌"
        
        print(f"{status} Query {i}:")
        print(f"   Query: {query}")
        print(f"   Domain: {classification.domain}")
        print(f"   Confidence: {classification.confidence:.2f}")
        print(f"   Reasoning: {classification.reasoning}")
        print()
    
    print(f"\n{'='*100}")
    print(f"ROUTING SUMMARY:")
    print(f"{'='*100}")
    for domain, count in routing_breakdown.items():
        pct = (count / len(support_queries)) * 100
        print(f"  {domain:15s}: {count:2d}/{len(support_queries)} ({pct:5.1f}%)")
    
    # Identify failing queries
    failing = []
    for i, item in enumerate(support_queries, 1):
        query = item["query"]
        classification = classify(query)
        if classification.domain != "support":
            failing.append({
                "num": i,
                "query": query,
                "routed_to": classification.domain,
                "confidence": classification.confidence
            })
    
    if failing:
        print(f"\n{'='*100}")
        print(f"FAILING QUERIES ({len(failing)} routing incorrectly):")
        print(f"{'='*100}\n")
        for item in failing:
            print(f"Query {item['num']}: {item['query']}")
            print(f"  ❌ Routed to: {item['routed_to']} ({item['confidence']:.2f} confidence)")
            print()


if __name__ == "__main__":
    main()
