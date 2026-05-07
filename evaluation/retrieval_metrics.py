"""
Retrieval evaluation metrics for EquipmentIQ RAG system.
Computes NDCG@5, Hit Rate@5, and Mean Reciprocal Rank for each agent.
"""

import sys
from pathlib import Path

# Add workspace root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import argparse
import math
from datetime import datetime
from typing import Any
import chromadb
from orchestrator.graph import run_query


def ndcg_at_k(query: str, expected_doc_ids: list[str], agent: str, k: int = 5) -> float:
    """
    Compute NDCG@k (Normalized Discounted Cumulative Gain).
    Relevance binary: doc in expected_doc_ids = 1, else = 0.
    Uses log2 discount: DCG = Σ(relevance / log2(rank + 1)) where rank is 1-indexed.
    """
    # Run the orchestrator query
    try:
        result = run_query(query)
    except Exception as e:
        print(f"  ⚠️  Query failed: {e}")
        return 0.0
    
    # Extract retrieved doc IDs from merged_context
    retrieved_ids = []
    if 'merged_context' in result and result['merged_context']:
        for chunk in result['merged_context'][:k]:
            doc_id = chunk.get('source_document') or chunk.get('chunk_id')
            if doc_id:
                retrieved_ids.append(doc_id)
    
    # Compute ideal DCG (all relevant documents at top with log2 discount)
    # IDCG = Σ(1.0 / log2(i + 1)) for i in 1..min(len(expected_doc_ids), k)
    ideal_dcg = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(expected_doc_ids), k) + 1))
    
    # Guard against division by zero
    if ideal_dcg == 0:
        return 0.0
    
    # Compute actual DCG with log2 discount (1-indexed rank)
    actual_dcg = 0.0
    for rank, doc_id in enumerate(retrieved_ids[:k], start=1):
        if doc_id in expected_doc_ids:
            actual_dcg += 1.0 / math.log2(rank + 1)
    
    # Compute and clamp NDCG to [0.0, 1.0] as safety net
    ndcg = actual_dcg / ideal_dcg
    return min(1.0, max(0.0, ndcg))


def hit_rate_at_k(query: str, expected_doc_ids: list[str], agent: str, k: int = 5) -> float:
    """
    Compute Hit Rate@k: fraction of queries where at least one relevant doc appears in top-k.
    Returns 1.0 if any expected_doc_id in top-k, else 0.0.
    """
    try:
        result = run_query(query)
    except Exception as e:
        print(f"  ⚠️  Query failed: {e}")
        return 0.0
    
    retrieved_ids = []
    if 'merged_context' in result and result['merged_context']:
        for chunk in result['merged_context'][:k]:
            doc_id = chunk.get('source_document') or chunk.get('chunk_id')
            if doc_id:
                retrieved_ids.append(doc_id)
    
    # Check if any expected doc in top-k
    for doc_id in expected_doc_ids:
        if doc_id in retrieved_ids:
            return 1.0
    
    return 0.0


def mean_reciprocal_rank(query: str, expected_doc_ids: list[str], agent: str) -> float:
    """
    Compute MRR (Mean Reciprocal Rank): 1/rank of first relevant doc.
    If no relevant doc found, return 0.0.
    """
    try:
        result = run_query(query)
    except Exception as e:
        print(f"  ⚠️  Query failed: {e}")
        return 0.0
    
    retrieved_ids = []
    if 'merged_context' in result and result['merged_context']:
        for chunk in result['merged_context']:
            doc_id = chunk.get('source_document') or chunk.get('chunk_id')
            if doc_id:
                retrieved_ids.append(doc_id)
    
    # Find rank of first relevant doc (1-indexed)
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in expected_doc_ids:
            return 1.0 / rank
    
    return 0.0


def evaluate_collection(agent_name: str, golden_pairs: list[dict]) -> dict:
    """
    Evaluate a single agent on its golden query set.
    
    Returns:
        {
            'agent': agent_name,
            'ndcg': mean_ndcg,
            'hit_rate': mean_hit_rate,
            'mrr': mean_mrr,
            'n_queries': count,
            'below_target': count_below_threshold
        }
    """
    ndcg_scores = []
    hit_rates = []
    mrr_scores = []
    below_target = 0
    
    print(f"\n[{agent_name.upper()}]")
    
    for i, pair in enumerate(golden_pairs, 1):
        query = pair['query']
        expected_ids = pair['expected_doc_ids']
        
        # Compute metrics
        ndcg = ndcg_at_k(query, expected_ids, agent_name, k=5)
        hit = hit_rate_at_k(query, expected_ids, agent_name, k=5)
        mrr = mean_reciprocal_rank(query, expected_ids, agent_name)
        
        ndcg_scores.append(ndcg)
        hit_rates.append(hit)
        mrr_scores.append(mrr)
        
        # Track below-threshold
        if ndcg < 0.70:
            below_target += 1
        
        status = "[PASS]" if ndcg >= 0.70 else "[FAIL]"
        print(f"  {i:2d}. {query[:50]:<50} NDCG={ndcg:.2f} Hit={hit:.1f} MRR={mrr:.2f} {status}")
    
    mean_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0
    mean_hit = sum(hit_rates) / len(hit_rates) if hit_rates else 0.0
    mean_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0
    
    return {
        'agent': agent_name,
        'ndcg': round(mean_ndcg, 4),
        'hit_rate': round(mean_hit, 4),
        'mrr': round(mean_mrr, 4),
        'n_queries': len(golden_pairs),
        'below_target': below_target
    }


def run_retrieval_eval(golden_path: str) -> dict:
    """
    Load golden set, group by agent, evaluate each, save results.
    """
    # Load golden set
    golden_pairs = []
    with open(golden_path, 'r') as f:
        for line in f:
            golden_pairs.append(json.loads(line.strip()))
    
    print(f"[RETRIEVAL EVALUATION]")
    print(f"Loaded {len(golden_pairs)} Q&A pairs from {golden_path}")
    
    # Group by agent
    by_agent = {}
    for pair in golden_pairs:
        agent = pair['agent']
        if agent not in by_agent:
            by_agent[agent] = []
        by_agent[agent].append(pair)
    
    # Evaluate each agent
    results = {
        'timestamp': datetime.now().isoformat(),
        'golden_path': golden_path,
        'agents': {}
    }
    
    for agent_name in ['software', 'mechanical', 'support']:
        if agent_name in by_agent:
            result = evaluate_collection(agent_name, by_agent[agent_name])
            results['agents'][agent_name] = result
    
    # Print summary table
    print(f"\n[SUMMARY TABLE]")
    print(f"{'Agent':<15} {'NDCG@5':<10} {'Hit@5':<10} {'MRR':<10} {'Below Target':<15}")
    print("=" * 60)
    
    for agent_name in ['software', 'mechanical', 'support']:
        if agent_name in results['agents']:
            r = results['agents'][agent_name]
            print(f"{agent_name:<15} {r['ndcg']:<10.4f} {r['hit_rate']:<10.4f} {r['mrr']:<10.4f} {r['below_target']:<15}/{r['n_queries']}")
    
    # Compute aggregate
    all_ndcg = []
    all_hit = []
    all_mrr = []
    for r in results['agents'].values():
        all_ndcg.append(r['ndcg'] * r['n_queries'])  # Weight by n_queries
        all_hit.append(r['hit_rate'] * r['n_queries'])
        all_mrr.append(r['mrr'] * r['n_queries'])
    
    total_queries = sum(r['n_queries'] for r in results['agents'].values())
    agg_ndcg = sum(all_ndcg) / total_queries if total_queries > 0 else 0.0
    agg_hit = sum(all_hit) / total_queries if total_queries > 0 else 0.0
    agg_mrr = sum(all_mrr) / total_queries if total_queries > 0 else 0.0
    
    print("=" * 60)
    print(f"{'AGGREGATE':<15} {agg_ndcg:<10.4f} {agg_hit:<10.4f} {agg_mrr:<10.4f}")
    
    results['aggregate'] = {
        'ndcg': round(agg_ndcg, 4),
        'hit_rate': round(agg_hit, 4),
        'mrr': round(agg_mrr, 4)
    }
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_path = Path('evaluation/results') / f'retrieval_{timestamp}.jsonl'
    with open(results_path, 'w') as f:
        f.write(json.dumps(results) + '\n')
    
    print(f"\n[OK] Results saved to {results_path}")
    
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate retrieval metrics')
    parser.add_argument('--golden', default='evaluation/golden_set.jsonl', help='Path to golden set JSONL')
    args = parser.parse_args()
    
    run_retrieval_eval(args.golden)
