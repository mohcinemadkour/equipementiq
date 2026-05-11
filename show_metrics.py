#!/usr/bin/env python3
"""Extract metrics from batch results."""

import json

# Load old batch results (before support fix)
with open('evaluation/results/batch_20260507_181049.jsonl') as f:
    old_results = json.load(f)

print('BEFORE Support Golden Set Fix:')
print('=' * 60)
print('Retrieval Metrics:')
for agent, metrics in old_results.get('retrieval', {}).items():
    print(f"  {agent}: NDCG={metrics.get('ndcg'):.3f}, Hit={metrics.get('hit_rate'):.3f}, MRR={metrics.get('mrr'):.3f}")

gen = old_results.get('generation', {})
print(f'\nGeneration Metrics:')
print(f"  Faithfulness: {gen.get('faithfulness'):.3f}")
print(f"  Answer Relevance: {gen.get('answer_relevance'):.3f}")
print(f"  LLM Judge: {gen.get('llm_judge_avg'):.1f} / 5")

print(f"\nGate Result: {old_results.get('gate_result')}")
print(f"Failures: {len(old_results.get('failures', []))}")
