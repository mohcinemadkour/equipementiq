#!/usr/bin/env python3
"""Quick test of support retrieval metrics."""

import json
from evaluation.retrieval_metrics import evaluate_collection

# Load golden set
with open('evaluation/golden_set.jsonl', encoding='utf-8') as f:
    pairs = [json.loads(line) for line in f]

# Get support pairs
support_pairs = [p for p in pairs if p['agent'] == 'support']

print(f"Testing {len(support_pairs)} support queries for NDCG...")
print("=" * 60)

# Evaluate support collection
metrics = evaluate_collection("support", support_pairs)

print(f"\nSupport Collection Retrieval Metrics:")
print(f"  NDCG@5: {metrics['ndcg']:.3f}")
print(f"  Hit@5:  {metrics['hit_rate']:.3f}")
print(f"  MRR:    {metrics['mrr']:.3f}")

if metrics['ndcg'] > 0.0:
    print(f"\n[OK] SUCCESS: Support NDCG > 0.0 (was 0.0 before fix)")
else:
    print(f"\n[FAIL] Support NDCG still 0.0 - document IDs may still be wrong")
