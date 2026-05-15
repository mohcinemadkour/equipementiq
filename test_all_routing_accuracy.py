"""
Verify routing accuracy across all three domains after support routing fix.
"""

import json
import sys
sys.path.insert(0, ".")

from orchestrator.intent_classifier import classify

# Load golden set
with open("evaluation/golden_set.jsonl", "r") as f:
    lines = [line.strip() for line in f if line.strip()]
    golden_set = [json.loads(line) for line in lines]

# Group by agent
by_agent = {}
for item in golden_set:
    agent = item["agent"]
    if agent not in by_agent:
        by_agent[agent] = []
    by_agent[agent].append(item)

print(f"\n{'='*120}")
print(f"ROUTING ACCURACY TEST (All 37 golden set queries)")
print(f"{'='*120}\n")

domain_map = {
    "software": "software",
    "mechanical": "mechanical",
    "support": "support"
}

results = {}
for agent, queries in by_agent.items():
    correct = 0
    incorrect = 0
    
    for item in queries:
        query = item["query"]
        classification = classify(query)
        expected_domain = domain_map[agent]
        
        if classification.domain == expected_domain:
            correct += 1
        else:
            incorrect += 1
    
    pct = (correct / len(queries)) * 100
    results[agent] = {
        "correct": correct,
        "incorrect": incorrect,
        "total": len(queries),
        "pct": pct
    }
    
    status = "✅ PASS" if pct == 100 else "⚠️ PARTIAL" if pct >= 80 else "❌ FAIL"
    print(f"{status} {agent.upper():15s}: {correct:2d}/{len(queries):2d} correct ({pct:5.1f}%)")

print(f"\n{'='*120}")
total_correct = sum(r["correct"] for r in results.values())
total_queries = sum(r["total"] for r in results.values())
overall_pct = (total_correct / total_queries) * 100
print(f"OVERALL: {total_correct}/{total_queries} correct ({overall_pct:.1f}%)")
print(f"{'='*120}\n")
