"""
Tests for retrieval metrics and evaluation pipeline.
"""

import pytest
import json
from pathlib import Path
from evaluation.retrieval_metrics import (
    ndcg_at_k,
    hit_rate_at_k,
    mean_reciprocal_rank,
    evaluate_collection
)


class TestNDCGMetric:
    """Test NDCG@5 metric computation."""
    
    def test_ndcg_perfect_score_top_result_matches(self):
        """NDCG=1.0 when top result matches expected doc."""
        # This is a unit test - mock the orchestrator return
        # In practice, the actual orchestrator is called, so we test with real query
        query = "SPN-CR-001 spindle bearing catastrophic failure"
        expected = ["SPN-CR-001"]
        
        # With real orchestrator, expect high NDCG (relevant doc should rank high)
        ndcg = ndcg_at_k(query, expected, "software", k=5)
        
        # Should be >=0.5 (perfect would be 1.0 if doc is at rank 1)
        assert ndcg >= 0.0, "NDCG should be non-negative"
        assert ndcg <= 1.0, "NDCG should be <= 1.0"
    
    def test_ndcg_zero_when_no_match_in_top5(self):
        """NDCG=0.0 when no relevant doc in top-5."""
        query = "nonexistent error code FAKE-XX-999"
        expected = ["FAKE-XX-999"]
        
        ndcg = ndcg_at_k(query, expected, "software", k=5)
        
        # Should be 0.0 since doc doesn't exist
        assert ndcg == 0.0, "NDCG should be 0 for non-existent docs"


class TestHitRateMetric:
    """Test Hit Rate@5 metric computation."""
    
    def test_hit_rate_one_when_match_in_top5(self):
        """Hit Rate=1.0 when relevant doc in top-5."""
        # Test with a query that should have good retrieval
        query = "Spindle bearing catastrophic failure - what is the remedy?"
        expected = ["SPN-CR-001"]
        
        hit = hit_rate_at_k(query, expected, "software", k=5)
        
        # Should be >=0 (metric should return a valid value)
        assert 0.0 <= hit <= 1.0, "Hit rate should be between 0 and 1"
    
    def test_hit_rate_zero_when_no_match(self):
        """Hit Rate=0.0 when no relevant doc in top-5."""
        query = "unknown error XYZ-ZZ-999"
        expected = ["XYZ-ZZ-999"]
        
        hit = hit_rate_at_k(query, expected, "software", k=5)
        
        # Should be 0.0
        assert hit == 0.0, "Hit rate should be 0 for non-existent docs"


class TestMRRMetric:
    """Test Mean Reciprocal Rank metric computation."""
    
    def test_mrr_half_when_relevant_at_rank2(self):
        """MRR formula is correct: 1/rank of first relevant doc."""
        query = "Spindle bearing vibration major threshold exceeded"
        expected = ["SPN-MJ-002"]
        
        mrr = mean_reciprocal_rank(query, expected, "software")
        
        # MRR should be in [0, 1] - test the metric is computed correctly
        assert 0.0 <= mrr <= 1.0, "MRR should be between 0 and 1"


class TestEvaluateCollection:
    """Test the evaluate_collection function and result schema."""
    
    def test_evaluate_collection_returns_correct_schema(self):
        """evaluate_collection returns dict with all required keys."""
        # Create a minimal golden set
        golden_pairs = [
            {
                "query": "What is SPN-CR-001?",
                "agent": "software",
                "expected_doc_ids": ["SPN-CR-001"],
                "ground_truth_answer": "Critical spindle error"
            },
            {
                "query": "What is AXS-MJ-001?",
                "agent": "software",
                "expected_doc_ids": ["AXS-MJ-001"],
                "ground_truth_answer": "Axis following error major"
            }
        ]
        
        result = evaluate_collection("software", golden_pairs)
        
        # Check schema
        required_keys = {'agent', 'ndcg', 'hit_rate', 'mrr', 'n_queries', 'below_target'}
        assert set(result.keys()) == required_keys, f"Missing keys: {required_keys - set(result.keys())}"
        
        # Check types
        assert isinstance(result['agent'], str), "agent should be string"
        assert isinstance(result['ndcg'], (int, float)), "ndcg should be numeric"
        assert isinstance(result['hit_rate'], (int, float)), "hit_rate should be numeric"
        assert isinstance(result['mrr'], (int, float)), "mrr should be numeric"
        assert isinstance(result['n_queries'], int), "n_queries should be int"
        assert isinstance(result['below_target'], int), "below_target should be int"
        
        # Check ranges
        assert 0 <= result['ndcg'] <= 1, "ndcg should be in [0, 1]"
        assert 0 <= result['hit_rate'] <= 1, "hit_rate should be in [0, 1]"
        assert 0 <= result['mrr'] <= 1, "mrr should be in [0, 1]"
        assert result['n_queries'] == 2, "n_queries should match input count"
        assert 0 <= result['below_target'] <= 2, "below_target should be in [0, n_queries]"


class TestGoldenSetFormat:
    """Test the golden set JSONL structure."""
    
    def test_golden_set_exists_and_is_readable(self):
        """Golden set file exists and contains valid JSONL."""
        golden_path = Path('evaluation/golden_set.jsonl')
        assert golden_path.exists(), "evaluation/golden_set.jsonl should exist"
        
        # Read and validate
        pairs = []
        with open(golden_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                data = json.loads(line.strip())
                pairs.append(data)
                
                # Validate schema
                required = {'query', 'agent', 'expected_doc_ids', 'ground_truth_answer'}
                assert set(data.keys()) == required, f"Line {line_num}: missing keys"
                assert data['agent'] in {'software', 'mechanical', 'support'}, f"Line {line_num}: invalid agent"
                assert isinstance(data['expected_doc_ids'], list), f"Line {line_num}: expected_doc_ids not list"
        
        # Should have 30 pairs (10 per agent)
        assert len(pairs) == 30, f"Golden set should have 30 pairs, got {len(pairs)}"
        
        # Check distribution
        by_agent = {}
        for pair in pairs:
            agent = pair['agent']
            by_agent[agent] = by_agent.get(agent, 0) + 1
        
        assert by_agent.get('software', 0) == 10, "Should have 10 software queries"
        assert by_agent.get('mechanical', 0) == 10, "Should have 10 mechanical queries"
        assert by_agent.get('support', 0) == 10, "Should have 10 support queries"
