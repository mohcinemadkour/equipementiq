"""Tests for feedback store, signal extraction, and correlation monitoring."""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Temporarily change DB path for testing
TEST_DB_PATH = None


@pytest.fixture(autouse=True)
def use_test_db():
    """Use temporary database for tests."""
    global TEST_DB_PATH
    with tempfile.TemporaryDirectory() as tmpdir:
        TEST_DB_PATH = Path(tmpdir) / "test_feedback.db"
        
        # Mock the DB_PATH in feedback_store
        import feedback.feedback_store as fs
        original_db_path = fs.DB_PATH
        fs.DB_PATH = TEST_DB_PATH
        
        yield
        
        fs.DB_PATH = original_db_path
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()


class TestFeedbackStore:
    """Tests for feedback.feedback_store module."""
    
    def test_init_db_creates_table(self):
        """Test that init_db() creates feedback table without error."""
        from feedback.feedback_store import init_db, DB_PATH
        import sqlite3
        
        # Should not raise
        init_db()
        
        # Verify table exists
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='feedback'"
        )
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None, "feedback table not created"
    
    def test_save_feedback_returns_uuid(self):
        """Test that save_feedback() returns non-empty string ID."""
        from feedback.feedback_store import save_feedback, init_db, DB_PATH
        import uuid as uuid_lib
        
        init_db()
        
        record = {
            'query': 'Test query',
            'agent_routed': 'mechanical',
            'rating': 'positive'
        }
        
        feedback_id = save_feedback(record)
        
        # Should be non-empty string
        assert isinstance(feedback_id, str)
        assert len(feedback_id) > 0
        
        # Should be valid UUID format
        try:
            uuid_lib.UUID(feedback_id)
            is_valid_uuid = True
        except ValueError:
            is_valid_uuid = False
        assert is_valid_uuid
    
    def test_get_feedback_returns_correct_schema(self):
        """Test that get_feedback() returns list with correct keys."""
        from feedback.feedback_store import save_feedback, get_feedback, init_db
        
        init_db()
        
        # Save sample records
        save_feedback({
            'query': 'Test query 1',
            'agent_routed': 'mechanical',
            'rating': 'positive'
        })
        save_feedback({
            'query': 'Test query 2',
            'agent_routed': 'software',
            'rating': 'negative'
        })
        
        records = get_feedback(limit=10)
        
        assert isinstance(records, list)
        assert len(records) == 2
        
        # Check keys in returned records
        required_keys = [
            'feedback_id', 'timestamp', 'query', 'agent_routed', 'domain',
            'confidence', 'retrieved_chunk_ids', 'generated_answer', 'rating',
            'free_text', 'session_id', 'faithfulness_score', 'llm_judge_score',
            'failure_mode', 'created_at'
        ]
        
        for record in records:
            for key in required_keys:
                assert key in record, f"Missing key: {key}"
    
    def test_get_stats_returns_required_keys(self):
        """Test that get_stats() returns dict with all 8 required keys."""
        from feedback.feedback_store import save_feedback, get_stats, init_db
        
        init_db()
        
        # Save sample records with different ratings
        save_feedback({
            'query': 'Query 1',
            'agent_routed': 'mechanical',
            'rating': 'positive',
            'faithfulness_score': 0.85,
            'llm_judge_score': 4
        })
        save_feedback({
            'query': 'Query 2',
            'agent_routed': 'software',
            'rating': 'negative',
            'faithfulness_score': 0.65,
            'llm_judge_score': 2
        })
        save_feedback({
            'query': 'Query 3',
            'agent_routed': 'support',
            'rating': 'neutral',
            'faithfulness_score': 0.75,
            'llm_judge_score': 3
        })
        
        stats = get_stats()
        
        # Check all required keys
        required_keys = [
            'total', 'positive', 'negative', 'neutral',
            'avg_faithfulness', 'avg_llm_judge', 'by_agent', 'by_failure_mode'
        ]
        
        for key in required_keys:
            assert key in stats, f"Missing key in stats: {key}"
        
        # Verify values make sense
        assert stats['total'] == 3
        assert stats['positive'] == 1
        assert stats['negative'] == 1
        assert stats['neutral'] == 1
        assert isinstance(stats['avg_faithfulness'], float)
        assert isinstance(stats['avg_llm_judge'], float)
        assert isinstance(stats['by_agent'], dict)
        assert isinstance(stats['by_failure_mode'], dict)


class TestSignalExtractor:
    """Tests for feedback.signal_extractor module."""
    
    def test_extract_signal_positive_rating_no_api(self):
        """Test extract_signal() returns correct schema for positive rating."""
        from feedback.signal_extractor import extract_signal
        
        result = extract_signal(
            query='Test query',
            answer='Test answer',
            free_text='Good answer',
            rating='positive'
        )
        
        # Should have required keys
        assert 'failure_mode' in result
        assert 'affected_agent' in result
        assert 'chunk_blamed' in result
        assert 'confidence' in result
        
        # For positive rating, should return correct
        assert result['failure_mode'] == 'correct'
        assert result['confidence'] == 1.0
    
    def test_extract_signal_negative_rating_with_mock(self):
        """Test extract_signal() with negative rating (mocked Claude call)."""
        from feedback.signal_extractor import extract_signal
        
        mock_response = {
            "failure_mode": "incomplete",
            "affected_agent": "mechanical",
            "chunk_blamed": True,
            "confidence": 0.85
        }
        
        with patch('feedback.signal_extractor.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            
            # Setup mock response
            mock_message = MagicMock()
            mock_message.content = [MagicMock(text=json.dumps(mock_response))]
            mock_client.messages.create.return_value = mock_message
            
            result = extract_signal(
                query='Why is this wrong?',
                answer='Incorrect answer',
                free_text='This is missing steps',
                rating='negative'
            )
            
            # Should have required keys
            assert result['failure_mode'] == 'incomplete'
            assert result['affected_agent'] == 'mechanical'
            assert result['chunk_blamed'] is True
            assert result['confidence'] == 0.85


class TestCorrelationMonitor:
    """Tests for feedback.correlation_monitor module."""
    
    def test_correlate_returns_correct_schema(self):
        """Test that correlate() returns dict with required keys."""
        from feedback.feedback_store import save_feedback, init_db
        from feedback.correlation_monitor import correlate
        
        init_db()
        
        # Save a sample record
        save_feedback({
            'query': 'Test',
            'agent_routed': 'mechanical',
            'rating': 'negative',
            'faithfulness_score': 0.85
        })
        
        result = correlate(limit=10)
        
        # Check required keys
        required_keys = [
            'n_records', 'n_with_scores', 'discordant_cases',
            'metric_calibration_flag', 'summary'
        ]
        
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
        
        # Verify types
        assert isinstance(result['n_records'], int)
        assert isinstance(result['n_with_scores'], int)
        assert isinstance(result['discordant_cases'], list)
        assert isinstance(result['metric_calibration_flag'], bool)
        assert isinstance(result['summary'], str)
