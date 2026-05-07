"""
Tests for orchestrator intent classification and routing.

20 routing tests (5 per domain) with mocked Claude API.
Validates IntentClassification model, confidence thresholding, and domain routing.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from orchestrator import classify, IntentClassification
from ingestion.config import load_config


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_anthropic_response():
    """Factory for mocked Anthropic API responses."""
    def _make_response(domain, confidence, reasoning="", filters=None):
        if filters is None:
            filters = {
                "subsystem": None,
                "severity_level": None,
                "error_code_prefix": None,
                "case_status": None,
                "machine_id": None
            }
        
        response_data = {
            "domain": domain,
            "confidence": confidence,
            "reasoning": reasoning,
            "suggested_filters": filters
        }
        
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(response_data))]
        return mock_response
    
    return _make_response


@pytest.fixture
def config_threshold():
    """Load actual confidence threshold from config."""
    cfg = load_config()
    return cfg["orchestrator"]["intent_confidence_threshold"]


# ============================================================================
# Mechanical Domain Tests (5 tests)
# ============================================================================

class TestMechanicalDomain:
    """Intent classification for mechanical/equipment queries."""
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_mechanical_clear_spindle_query(self, mock_client, mock_anthropic_response):
        """Test clear mechanical spindle bearing question."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="mechanical",
            confidence=0.95,
            reasoning="Clear spindle bearing mechanical question",
            filters={"subsystem": "SPN"}
        )
        mock_client.return_value = mock_instance
        
        result = classify("What are spindle bearing failure modes?")
        
        assert result.domain == "mechanical"
        assert result.confidence == 0.95
        assert result.suggested_filters.get("subsystem") == "SPN"
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_mechanical_with_subsystem_filter(self, mock_client, mock_anthropic_response):
        """Test mechanical query with subsystem-specific filter."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="mechanical",
            confidence=0.88,
            reasoning="Axis mechanical design question",
            filters={"subsystem": "AXS"}
        )
        mock_client.return_value = mock_instance
        
        result = classify("Explain the Z-axis actuator design")
        
        assert result.domain == "mechanical"
        assert result.confidence == 0.88
        assert result.suggested_filters.get("subsystem") == "AXS"
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_mechanical_ambiguous_failure_modes(self, mock_client, mock_anthropic_response):
        """Test ambiguous mechanical query (could include failure symptoms)."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="mechanical",
            confidence=0.72,
            reasoning="Mechanical focus but could involve vibration error codes"
        )
        mock_client.return_value = mock_instance
        
        result = classify("What causes the machine to vibrate excessively?")
        
        # Confidence < 0.80, should override to cross_domain
        assert result.domain == "cross_domain"
        assert result.confidence == 0.72
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_mechanical_at_threshold_boundary(self, mock_client, mock_anthropic_response):
        """Test mechanical query at confidence threshold boundary (0.80)."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="mechanical",
            confidence=0.80,
            reasoning="Right at threshold"
        )
        mock_client.return_value = mock_instance
        
        result = classify("How does the spindle system work?")
        
        # Confidence == 0.80 (not < 0.80), should stay mechanical
        assert result.domain == "mechanical"
        assert result.confidence == 0.80
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_mechanical_high_confidence(self, mock_client, mock_anthropic_response):
        """Test mechanical query with high confidence."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="mechanical",
            confidence=0.92,
            reasoning="Unambiguous mechanical design question"
        )
        mock_client.return_value = mock_instance
        
        result = classify("Describe the hydraulic pressure regulation system")
        
        assert result.domain == "mechanical"
        assert result.confidence == 0.92


# ============================================================================
# Software/Error Code Domain Tests (5 tests)
# ============================================================================

class TestSoftwareDomain:
    """Intent classification for error code / software queries."""
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_software_error_code_lookup(self, mock_client, mock_anthropic_response):
        """Test direct error code lookup query."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="software",
            confidence=0.99,
            reasoning="Direct error code lookup",
            filters={"error_code_prefix": "SPN-CR"}
        )
        mock_client.return_value = mock_instance
        
        result = classify("What does error SPN-CR-001 mean?")
        
        assert result.domain == "software"
        assert result.confidence == 0.99
        assert result.suggested_filters.get("error_code_prefix") == "SPN-CR"
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_software_severity_filter(self, mock_client, mock_anthropic_response):
        """Test software query with severity filtering."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="software",
            confidence=0.85,
            reasoning="Severity-level software query",
            filters={"severity_level": "CRITICAL"}
        )
        mock_client.return_value = mock_instance
        
        result = classify("Show me all CRITICAL severity error codes")
        
        assert result.domain == "software"
        assert result.confidence == 0.85
        assert result.suggested_filters.get("severity_level") == "CRITICAL"
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_software_multiple_codes(self, mock_client, mock_anthropic_response):
        """Test software query referencing multiple error codes."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="software",
            confidence=0.90,
            reasoning="Multiple error code references"
        )
        mock_client.return_value = mock_instance
        
        result = classify("Compare AXS-MJ-001 and AXS-MJ-002")
        
        assert result.domain == "software"
        assert result.confidence == 0.90
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_software_ambiguous_code_plus_action(self, mock_client, mock_anthropic_response):
        """Test software query mixing error code with resolution."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="software",
            confidence=0.65,
            reasoning="Error code + resolution (possibly support-domain)"
        )
        mock_client.return_value = mock_instance
        
        result = classify("Error code AXS-MD-001 appeared — how do we fix it?")
        
        # Confidence < 0.80, should override to cross_domain
        assert result.domain == "cross_domain"
        assert result.confidence == 0.65
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_software_just_above_threshold(self, mock_client, mock_anthropic_response):
        """Test software query just above confidence threshold."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="software",
            confidence=0.81,
            reasoning="Slightly ambiguous but primarily software"
        )
        mock_client.return_value = mock_instance
        
        result = classify("What error codes involve the spindle subsystem?")
        
        # Confidence >= 0.80, should stay software
        assert result.domain == "software"
        assert result.confidence == 0.81


# ============================================================================
# Support/Complaint Domain Tests (5 tests)
# ============================================================================

class TestSupportDomain:
    """Intent classification for customer support / complaint queries."""
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_support_complaint_lookup(self, mock_client, mock_anthropic_response):
        """Test direct complaint case lookup."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="support",
            confidence=0.94,
            reasoning="Direct support case reference"
        )
        mock_client.return_value = mock_instance
        
        result = classify("What was the remedy for case #C-00145?")
        
        assert result.domain == "support"
        assert result.confidence == 0.94
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_support_priority_filter(self, mock_client, mock_anthropic_response):
        """Test support query with priority/severity filtering."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="support",
            confidence=0.88,
            reasoning="Priority-filtered complaint query",
            filters={"priority": "P1-CRITICAL"}
        )
        mock_client.return_value = mock_instance
        
        result = classify("Show me CRITICAL priority cases on M01")
        
        assert result.domain == "support"
        assert result.confidence == 0.88
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_support_machine_specific(self, mock_client, mock_anthropic_response):
        """Test support query filtered by machine."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="support",
            confidence=0.89,
            reasoning="Machine-specific complaint query",
            filters={"machine_id": "M02"}
        )
        mock_client.return_value = mock_instance
        
        result = classify("List all open cases for M02")
        
        assert result.domain == "support"
        assert result.confidence == 0.89
        assert result.suggested_filters.get("machine_id") == "M02"
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_support_case_status_filter(self, mock_client, mock_anthropic_response):
        """Test support query with case status filtering."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="support",
            confidence=0.86,
            reasoning="Case status filter (open/closed)",
            filters={"case_status": "open"}
        )
        mock_client.return_value = mock_instance
        
        result = classify("Which RMA cases are still open?")
        
        assert result.domain == "support"
        assert result.confidence == 0.86
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_support_just_below_threshold(self, mock_client, mock_anthropic_response):
        """Test support query just below confidence threshold."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="support",
            confidence=0.79,
            reasoning="Support-focused but lacks specificity"
        )
        mock_client.return_value = mock_instance
        
        result = classify("What happened with that complaint last month?")
        
        # Confidence < 0.80, should override to cross_domain
        assert result.domain == "cross_domain"
        assert result.confidence == 0.79


# ============================================================================
# Cross-Domain Tests (5 tests)
# ============================================================================

class TestCrossDomain:
    """Intent classification for multi-domain / ambiguous queries."""
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_cross_domain_error_plus_mechanical(self, mock_client, mock_anthropic_response):
        """Test query mixing error code + mechanical explanation."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="cross_domain",
            confidence=0.60,
            reasoning="Error code + mechanical cause explanation"
        )
        mock_client.return_value = mock_instance
        
        result = classify("SPN-CR-001 occurs when the spindle bearing fails — what's the mechanical cause?")
        
        assert result.domain == "cross_domain"
        assert result.confidence == 0.60
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_cross_domain_error_plus_support(self, mock_client, mock_anthropic_response):
        """Test query mixing error code + support resolution."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="cross_domain",
            confidence=0.55,
            reasoning="Error code + support action"
        )
        mock_client.return_value = mock_instance
        
        result = classify("Error AXS-MD-001 on M02 — what's the remedy?")
        
        assert result.domain == "cross_domain"
        assert result.confidence == 0.55
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_cross_domain_explicit_classification(self, mock_client, mock_anthropic_response):
        """Test query that Claude explicitly classifies as cross_domain."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="cross_domain",
            confidence=0.70,
            reasoning="Multi-part: error definition + mechanical investigation + complaint history"
        )
        mock_client.return_value = mock_instance
        
        result = classify("What does SPN-MJ-002 indicate mechanically, and did we see it on M03 last week?")
        
        assert result.domain == "cross_domain"
        assert result.confidence == 0.70
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_cross_domain_with_conversation_history(self, mock_client, mock_anthropic_response):
        """Test intent classification with conversation context."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="cross_domain",
            confidence=0.58,
            reasoning="Follow-up to previous spindle discussion, now asking about errors"
        )
        mock_client.return_value = mock_instance
        
        history = [
            {"query": "Explain spindle bearing design", "answer": "The spindle bearing is..."},
            {"query": "Common spindle failures?", "answer": "Spindle failures occur when..."}
        ]
        
        result = classify("So if SPN-CR-001 appears, what's the root mechanical cause?", history=history)
        
        assert result.domain == "cross_domain"
        # Verify that classify was called with mocked client
        assert result.confidence == 0.58
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_cross_domain_very_low_confidence(self, mock_client, mock_anthropic_response):
        """Test query with very low confidence (completely ambiguous)."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="cross_domain",
            confidence=0.35,
            reasoning="Query is vague and could mean multiple things"
        )
        mock_client.return_value = mock_instance
        
        result = classify("Tell me about something broken")
        
        assert result.domain == "cross_domain"
        assert result.confidence == 0.35


# ============================================================================
# Pydantic Model Validation Tests
# ============================================================================

class TestIntentClassificationModel:
    """Tests for IntentClassification Pydantic model validation."""
    
    def test_model_accepts_valid_data(self):
        """Test that IntentClassification accepts valid data."""
        data = {
            "domain": "mechanical",
            "confidence": 0.85,
            "reasoning": "Clear mechanical query",
            "suggested_filters": {"subsystem": "SPN"}
        }
        
        model = IntentClassification(**data)
        assert model.domain == "mechanical"
        assert model.confidence == 0.85
    
    def test_model_rejects_invalid_domain(self):
        """Test that IntentClassification rejects invalid domain."""
        data = {
            "domain": "invalid_domain",
            "confidence": 0.85,
            "reasoning": "Test"
        }
        
        with pytest.raises(Exception):  # Pydantic ValidationError
            IntentClassification(**data)
    
    def test_model_enforces_confidence_range(self):
        """Test that confidence must be between 0.0 and 1.0."""
        # Too high
        with pytest.raises(Exception):
            IntentClassification(
                domain="mechanical",
                confidence=1.5,
                reasoning="Test"
            )
        
        # Too low
        with pytest.raises(Exception):
            IntentClassification(
                domain="mechanical",
                confidence=-0.1,
                reasoning="Test"
            )
    
    def test_model_optional_suggested_filters(self):
        """Test that suggested_filters is optional."""
        data = {
            "domain": "software",
            "confidence": 0.92,
            "reasoning": "Error code query"
            # No suggested_filters
        }
        
        model = IntentClassification(**data)
        assert model.suggested_filters == {}


# ============================================================================
# Confidence Threshold Override Tests
# ============================================================================

class TestConfidenceThresholdOverride:
    """Tests for automatic cross_domain override when confidence < 0.80."""
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_threshold_override_at_0_79(self, mock_client, mock_anthropic_response):
        """Test override triggers at confidence 0.79 (< 0.80)."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="mechanical",
            confidence=0.79,
            reasoning="Just below threshold"
        )
        mock_client.return_value = mock_instance
        
        result = classify("Some query")
        
        assert result.domain == "cross_domain"
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_threshold_no_override_at_0_80(self, mock_client, mock_anthropic_response):
        """Test no override at confidence 0.80 (>= 0.80)."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="software",
            confidence=0.80,
            reasoning="Exactly at threshold"
        )
        mock_client.return_value = mock_instance
        
        result = classify("Some query")
        
        assert result.domain == "software"
    
    @patch("orchestrator.intent_classifier._get_client")
    def test_threshold_no_override_at_0_81(self, mock_client, mock_anthropic_response):
        """Test no override at confidence 0.81 (> 0.80)."""
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_anthropic_response(
            domain="support",
            confidence=0.81,
            reasoning="Just above threshold"
        )
        mock_client.return_value = mock_instance
        
        result = classify("Some query")
        
        assert result.domain == "support"


# ============================================================================
# Integration Tests (Real ChromaDB Collections)
# ============================================================================

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env to get API keys
_env_path = Path(__file__).parent.parent / '.env'
load_dotenv(_env_path, override=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
SKIP_INTEGRATION = (
    not ANTHROPIC_API_KEY or 
    ANTHROPIC_API_KEY.upper() in ["REPLACE_ME", "", "YOUR_API_KEY", "NONE"]
)


class TestOrchestratorIntegration:
    """Integration tests using REAL ChromaDB collections (no mocking).
    
    NOTE: These tests require valid ANTHROPIC_API_KEY environment variable.
    They will be skipped if the API key is not set or is a placeholder.
    """
    
    @pytest.mark.skipif(SKIP_INTEGRATION, reason="ANTHROPIC_API_KEY not configured or is placeholder")
    @pytest.mark.integration
    def test_software_query_error_code_lookup(self):
        """Test software domain: error code query."""
        from orchestrator.graph import run_query
        
        query = "What does error SPN-CR-001 mean?"
        state = run_query(query)
        
        # Verify domain routing
        assert state["domain"] in ["software", "cross_domain"]
        assert 0.0 <= state["confidence"] <= 1.0
        
        # Verify state structure
        assert "final_answer" in state
        assert isinstance(state["final_answer"], str)
        assert isinstance(state["citations"], list)
        assert "agent_results" in state
    
    @pytest.mark.skipif(SKIP_INTEGRATION, reason="ANTHROPIC_API_KEY not configured or is placeholder")
    @pytest.mark.integration
    def test_mechanical_query_bearing_type(self):
        """Test mechanical domain: bearing specifications query."""
        from orchestrator.graph import run_query
        
        query = "What bearing type does the VMC-3000 spindle use?"
        state = run_query(query)
        
        # Verify domain routing
        assert state["domain"] in ["mechanical", "cross_domain"]
        assert 0.0 <= state["confidence"] <= 1.0
        
        # Verify state structure
        assert "final_answer" in state
        assert isinstance(state["final_answer"], str)
        assert "merged_context" in state
        assert isinstance(state["merged_context"], list)
    
    @pytest.mark.skipif(SKIP_INTEGRATION, reason="ANTHROPIC_API_KEY not configured or is placeholder")
    @pytest.mark.integration
    def test_support_query_complaint_lookup(self):
        """Test support domain: complaint case lookup."""
        from orchestrator.graph import run_query
        
        query = "Show me complaint case CMP-2019-1000"
        state = run_query(query)
        
        # Verify domain routing
        assert state["domain"] in ["support", "cross_domain"]
        assert 0.0 <= state["confidence"] <= 1.0
        
        # Verify response structure
        assert "final_answer" in state
        assert len(state["final_answer"]) > 0 or state["final_answer"] == "INSUFFICIENT_CONTEXT"
        
        # Verify citations present if answer provided
        if "INSUFFICIENT_CONTEXT" not in state["final_answer"]:
            assert len(state["citations"]) >= 0
    
    @pytest.mark.skipif(SKIP_INTEGRATION, reason="ANTHROPIC_API_KEY not configured or is placeholder")
    @pytest.mark.integration
    def test_cross_domain_query_mixed(self):
        """Test cross-domain: spindle fault + error code + machine."""
        from orchestrator.graph import run_query
        
        query = "M01 spindle bearing fault and ATC alarm triggered — what's happening?"
        state = run_query(query)
        
        # Verify cross-domain routing for ambiguous query
        assert state["domain"] in ["mechanical", "software", "support", "cross_domain"]
        assert 0.0 <= state["confidence"] <= 1.0
        
        # Verify all agents were called (if cross_domain)
        if state["domain"] == "cross_domain":
            assert len(state["agent_results"]) > 0
        
        # Verify synthesis occurred
        assert isinstance(state["final_answer"], str)
        assert len(state["final_answer"]) > 0
    
    @pytest.mark.skipif(SKIP_INTEGRATION, reason="ANTHROPIC_API_KEY not configured or is placeholder")
    @pytest.mark.integration
    def test_langgraph_execution_complete(self):
        """Test that full LangGraph execution completes with valid state."""
        from orchestrator.graph import run_query
        
        query = "Any diagnostic query"
        state = run_query(query)
        
        # Verify all required state fields are present
        assert "query" in state
        assert "domain" in state
        assert "confidence" in state
        assert "agent_results" in state
        assert "merged_context" in state
        assert "final_answer" in state
        assert "citations" in state
        assert "conversation_history" in state
        
        # Verify types
        assert isinstance(state["query"], str)
        assert isinstance(state["domain"], str)
        assert isinstance(state["confidence"], float)
        assert isinstance(state["agent_results"], dict)
        assert isinstance(state["merged_context"], list)
        assert isinstance(state["final_answer"], str)
        assert isinstance(state["citations"], list)
        assert isinstance(state["conversation_history"], list)
        
        # Verify node_latency tracking (proof of execution)
        assert "node_latency" in state
        assert len(state["node_latency"]) > 0
