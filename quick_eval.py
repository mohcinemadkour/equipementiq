"""Quick evaluation of single agent to test."""

import json
from evaluation.retrieval_metrics import ndcg_at_k, hit_rate_at_k, mean_reciprocal_rank

# Load golden set
with open('evaluation/golden_set.jsonl', 'r') as f:
    golden_pairs = [json.loads(line) for line in f]

# Test just software queries
software_queries = [p for p in golden_pairs if p['agent'] == 'software'][:3]

print(f"Testing {len(software_queries)} software queries...")

for i, pair in enumerate(software_queries, 1):
    ndcg = ndcg_at_k(pair['query'], pair['expected_doc_ids'], pair['agent'])
    hit = hit_rate_at_k(pair['query'], pair['expected_doc_ids'], pair['agent'])
    mrr = mean_reciprocal_rank(pair['query'], pair['expected_doc_ids'], pair['agent'])
    
    status = "[PASS]" if ndcg >= 0.70 else "[FAIL]"
    print(f"{i}. {pair['query'][:50]}... NDCG={ndcg:.2f} Hit={hit:.1f} MRR={mrr:.2f} {status}")

print("\nDone")
