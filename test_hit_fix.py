#!/usr/bin/env python
"""Quick test of the Hit@5 fix for retrieval metrics."""

import sys
import json
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from evaluation.retrieval_metrics import evaluate_collection

# Load golden set
golden_pairs = []
with open("evaluation/golden_set.jsonl", 'r') as f:
    for line in f:
        if line.strip():
            golden_pairs.append(json.loads(line.strip()))

# Group by agent
by_agent = {}
for pair in golden_pairs:
    agent = pair['agent']
    if agent not in by_agent:
        by_agent[agent] = []
    by_agent[agent].append(pair)

# Evaluate each agent
print("\n" + "="*70)
print("RETRIEVAL METRICS EVALUATION (WITH Hit@5 FIX)")
print("="*70)

for agent_name in ['software', 'mechanical', 'support']:
    if agent_name in by_agent:
        result = evaluate_collection(agent_name, by_agent[agent_name])
        print(f"\n[{agent_name.upper()}]")
        print(f"  NDCG@5:   {result['ndcg']:.4f} (target: ≥0.70)")
        print(f"  Hit@5:    {result['hit_rate']:.4f} (target: ≥0.85)")
        print(f"  MRR:      {result['mrr']:.4f}")
        print(f"  Queries:  {result['n_queries']}")
        
        status = "✅ PASS" if result['ndcg'] >= 0.70 else "❌ FAIL"
        print(f"  Status:   {status}")

print("\n" + "="*70)
print("Expected Hit@5 values:")
print("  Software:  ~0.90+ (actual error codes found)")
print("  Mechanical: ~0.60-0.90 (mixed; some Zone C queries may lack perfect matches)")
print("  Support:   1.00 (simple customer case matching)")
print("="*70)
