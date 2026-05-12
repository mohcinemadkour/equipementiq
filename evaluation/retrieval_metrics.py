"""
Retrieval evaluation metrics for EquipmentIQ RAG system.
Computes NDCG@5, Hit Rate@5, and Mean Reciprocal Rank for each agent.

Uses LangChain's OpenAIEmbeddings (consistent with ingestion & agents).
Direct collection queries - no orchestrator/API required.
"""

import sys
from pathlib import Path

# Add workspace root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import argparse
import math
import os
from datetime import datetime
from typing import Any
from dotenv import load_dotenv
import chromadb
from langchain_openai import OpenAIEmbeddings

from ingestion.config import load_config

load_dotenv()


def _compute_ndcg_direct(expected_doc_ids: list[str], retrieved_ids: list[str], k: int = 5) -> float:
    """Compute NDCG directly from retrieved_ids list."""
    # IDCG - sum of log2 discounts for expected docs
    ideal_dcg = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(expected_doc_ids), k) + 1))
    
    if ideal_dcg == 0:
        return 0.0
    
    # Actual DCG
    actual_dcg = 0.0
    for rank, doc_id in enumerate(retrieved_ids[:k], start=1):
        if doc_id in expected_doc_ids:
            actual_dcg += 1.0 / math.log2(rank + 1)
    
    ndcg = actual_dcg / ideal_dcg
    return min(1.0, max(0.0, ndcg))


def _compute_hit_rate_direct(expected_doc_ids: list[str], retrieved_ids: list[str], k: int = 5) -> float:
    """Compute Hit Rate directly from retrieved_ids list."""
    for doc_id in expected_doc_ids:
        if doc_id in retrieved_ids[:k]:
            return 1.0
    return 0.0


def _compute_mrr_direct(expected_doc_ids: list[str], retrieved_ids: list[str]) -> float:
    """Compute MRR directly from retrieved_ids list."""
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in expected_doc_ids:
            return 1.0 / rank
    return 0.0


def _extract_source_doc_id(chunk_id: str) -> str:
    """Extract source document ID from full chunk ID (strip __XXXX suffix)."""
    if '__' in chunk_id:
        return chunk_id.split('__')[0]
    return chunk_id


def ndcg_at_k(query: str, expected_doc_ids: list[str], agent: str, k: int = 5) -> float:
    """
    Compute NDCG@k (Normalized Discounted Cumulative Gain).
    Relevance binary: doc in expected_doc_ids = 1, else = 0.
    Uses log2 discount: DCG = Σ(relevance / log2(rank + 1)) where rank is 1-indexed.
    Queries collections directly (no orchestrator/API required).
    """
    try:
        # Initialize ChromaDB client
        chroma_persist_dir = os.getenv('CHROMA_PERSIST_DIR', './chroma_db')
        client = chromadb.PersistentClient(path=chroma_persist_dir)
        
        # Get the appropriate collection based on agent
        agent_to_collection = {
            'mechanical': 'mechanical_collection',
            'software': 'software_collection',
            'support': 'support_collection'
        }
        collection_name = agent_to_collection.get(agent, 'mechanical_collection')
        collection = client.get_collection(name=collection_name)
        
        # Embed query using LangChain (same as ingestion)
        cfg = load_config()
        embedder = OpenAIEmbeddings(model=cfg['embeddings']['model'])
        query_embedding = embedder.embed_query(query)
        
        # Query the collection
        result = collection.query(query_embeddings=[query_embedding], n_results=k)
        
        # Extract source_document IDs (strip __XXXX suffix from chunk_ids)
        retrieved_ids = []
        if result['ids'] and len(result['ids']) > 0:
            for chunk_id in result['ids'][0][:k]:
                source_id = _extract_source_doc_id(chunk_id)
                retrieved_ids.append(source_id)
        
    except Exception as e:
        print(f"  [ERROR] Query failed: {str(e)[:80]}")
        return 0.0
    
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
    Queries collections directly (no orchestrator/API required).
    """
    try:
        # Initialize ChromaDB client
        chroma_persist_dir = os.getenv('CHROMA_PERSIST_DIR', './chroma_db')
        client = chromadb.PersistentClient(path=chroma_persist_dir)
        
        # Get the appropriate collection based on agent
        agent_to_collection = {
            'mechanical': 'mechanical_collection',
            'software': 'software_collection',
            'support': 'support_collection'
        }
        collection_name = agent_to_collection.get(agent, 'mechanical_collection')
        collection = client.get_collection(name=collection_name)
        
        # Embed query using LangChain (same as ingestion)
        cfg = load_config()
        embedder = OpenAIEmbeddings(model=cfg['embeddings']['model'])
        query_embedding = embedder.embed_query(query)
        
        # Query the collection
        result = collection.query(query_embeddings=[query_embedding], n_results=k)
        
        # Extract source_document IDs (strip __XXXX suffix from chunk_ids)
        retrieved_ids = []
        if result['ids'] and len(result['ids']) > 0:
            for chunk_id in result['ids'][0][:k]:
                source_id = _extract_source_doc_id(chunk_id)
                retrieved_ids.append(source_id)
        
    except Exception as e:
        print(f"  [ERROR] Query failed: {str(e)[:80]}")
        return 0.0
    
    # Check if any expected doc in top-k
    for doc_id in expected_doc_ids:
        if doc_id in retrieved_ids:
            return 1.0
    
    return 0.0


def mean_reciprocal_rank(query: str, expected_doc_ids: list[str], agent: str) -> float:
    """
    Compute MRR (Mean Reciprocal Rank): 1/rank of first relevant doc.
    If no relevant doc found, return 0.0.
    Queries collections directly (no orchestrator/API required).
    """
    try:
        # Initialize ChromaDB client
        chroma_persist_dir = os.getenv('CHROMA_PERSIST_DIR', './chroma_db')
        client = chromadb.PersistentClient(path=chroma_persist_dir)
        
        # Get the appropriate collection based on agent
        agent_to_collection = {
            'mechanical': 'mechanical_collection',
            'software': 'software_collection',
            'support': 'support_collection'
        }
        collection_name = agent_to_collection.get(agent, 'mechanical_collection')
        collection = client.get_collection(name=collection_name)
        
        # Embed query using LangChain (same as ingestion)
        cfg = load_config()
        embedder = OpenAIEmbeddings(model=cfg['embeddings']['model'])
        query_embedding = embedder.embed_query(query)
        
        # Query the collection (get more results to find MRR rank)
        result = collection.query(query_embeddings=[query_embedding], n_results=20)
        
        # Extract source_document IDs (strip __XXXX suffix from chunk_ids)
        retrieved_ids = []
        if result['ids'] and len(result['ids']) > 0:
            for chunk_id in result['ids'][0]:
                source_id = _extract_source_doc_id(chunk_id)
                retrieved_ids.append(source_id)
        
    except Exception as e:
        print(f"  [ERROR] Query failed: {str(e)[:80]}")
        return 0.0
    
    # Find rank of first relevant doc (1-indexed)
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in expected_doc_ids:
            return 1.0 / rank
    
    return 0.0


def evaluate_collection(agent_name: str, golden_pairs: list[dict]) -> dict:
    """
    Evaluate a single agent on its golden query set using the full orchestrator.
    This tests end-to-end retrieval through the routing system.
    
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
        
        # Query collections directly (no orchestrator API required)
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
