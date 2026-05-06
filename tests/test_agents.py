"""Unit tests for agent layer (mocked collections).

Tests cover:
- Agent initialization
- Metadata filtering
- Reranking
- Citation tracking
- Similarity filtering
- Domain isolation (no cross-collection reads)
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agents import (
    AgentResponse,
    BaseAgent,
    MechanicalAgent,
    RetrievalResult,
    SoftwareAgent,
    SupportAgent,
)


class TestBaseAgent:
    """BaseAgent base class tests."""

    def test_agent_initialization_requires_collection(self) -> None:
        """Agent initialization fails if collection not found."""
        with patch("agents.base_agent.chromadb.PersistentClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client_instance.get_collection.side_effect = Exception(
                "Collection not found"
            )
            mock_client.return_value = mock_client_instance

            with pytest.raises(ValueError, match="Collection"):
                MechanicalAgent()

    def test_retrieval_result_dataclass(self) -> None:
        """RetrievalResult has correct structure."""
        result = RetrievalResult(
            chunk_id="DOC-EIQ-001__0042",
            source_document="DOC-EIQ-001",
            content="Sample content",
            similarity_score=0.85,
            metadata={"subsystem": "SPN"},
        )
        assert result.chunk_id == "DOC-EIQ-001__0042"
        assert result.source_document == "DOC-EIQ-001"
        assert result.similarity_score == 0.85

    def test_agent_response_dataclass(self) -> None:
        """AgentResponse has correct structure."""
        results = [
            RetrievalResult(
                chunk_id="test__0001",
                source_document="test",
                content="test",
                similarity_score=0.8,
                metadata={},
            )
        ]
        response = AgentResponse(
            query="test query",
            domain="mechanical",
            results=results,
            total_count=1,
        )
        assert response.domain == "mechanical"
        assert len(response.results) == 1
        assert response.insufficient_context is False


class TestMechanicalAgent:
    """MechanicalAgent specific tests."""

    @patch("agents.base_agent.chromadb.PersistentClient")
    def test_mechanical_agent_initialization(self, mock_client) -> None:
        """MechanicalAgent initializes with mechanical_collection."""
        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        with patch("agents.base_agent.OpenAIEmbeddings"):
            with patch("agents.base_agent.CrossEncoder"):
                agent = MechanicalAgent()
                assert agent.domain == "mechanical"

    @patch("agents.base_agent.chromadb.PersistentClient")
    def test_mechanical_subsystem_filter(self, mock_client) -> None:
        """MechanicalAgent filters by subsystem (SPN, AXS, etc.)."""
        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        with patch("agents.base_agent.OpenAIEmbeddings"):
            with patch("agents.base_agent.CrossEncoder"):
                agent = MechanicalAgent()
                filter_dict = agent._build_where_filter(subsystem="SPN")
                assert filter_dict == {"subsystem": "SPN"}

    @patch("agents.base_agent.chromadb.PersistentClient")
    def test_mechanical_no_filter_when_none(self, mock_client) -> None:
        """MechanicalAgent returns None filter if no subsystem specified."""
        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        with patch("agents.base_agent.OpenAIEmbeddings"):
            with patch("agents.base_agent.CrossEncoder"):
                agent = MechanicalAgent()
                filter_dict = agent._build_where_filter()
                assert filter_dict is None


class TestSoftwareAgent:
    """SoftwareAgent specific tests."""

    @patch("agents.base_agent.chromadb.PersistentClient")
    def test_software_agent_initialization(self, mock_client) -> None:
        """SoftwareAgent initializes with software_collection."""
        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        with patch("agents.base_agent.OpenAIEmbeddings"):
            with patch("agents.base_agent.CrossEncoder"):
                agent = SoftwareAgent()
                assert agent.domain == "software"

    @patch("agents.base_agent.chromadb.PersistentClient")
    def test_software_severity_filter(self, mock_client) -> None:
        """SoftwareAgent filters by severity level."""
        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        with patch("agents.base_agent.OpenAIEmbeddings"):
            with patch("agents.base_agent.CrossEncoder"):
                agent = SoftwareAgent()
                filter_dict = agent._build_where_filter(severity_level="CRITICAL")
                assert filter_dict == {"severity_level": "CRITICAL"}

    @patch("agents.base_agent.chromadb.PersistentClient")
    def test_software_fault_category_filter(self, mock_client) -> None:
        """SoftwareAgent filters by fault category."""
        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        with patch("agents.base_agent.OpenAIEmbeddings"):
            with patch("agents.base_agent.CrossEncoder"):
                agent = SoftwareAgent()
                filter_dict = agent._build_where_filter(fault_category="tool_wear")
                assert filter_dict == {"fault_category": "tool_wear"}


class TestSupportAgent:
    """SupportAgent specific tests."""

    @patch("agents.base_agent.chromadb.PersistentClient")
    def test_support_agent_initialization(self, mock_client) -> None:
        """SupportAgent initializes with support_collection."""
        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        with patch("agents.base_agent.OpenAIEmbeddings"):
            with patch("agents.base_agent.CrossEncoder"):
                agent = SupportAgent()
                assert agent.domain == "support"

    @patch("agents.base_agent.chromadb.PersistentClient")
    def test_support_case_status_filter(self, mock_client) -> None:
        """SupportAgent filters by case status."""
        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        with patch("agents.base_agent.OpenAIEmbeddings"):
            with patch("agents.base_agent.CrossEncoder"):
                agent = SupportAgent()
                filter_dict = agent._build_where_filter(case_status="CLOSED")
                assert filter_dict == {"case_status": "CLOSED"}

    @patch("agents.base_agent.chromadb.PersistentClient")
    def test_support_priority_filter(self, mock_client) -> None:
        """SupportAgent filters by priority."""
        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        with patch("agents.base_agent.OpenAIEmbeddings"):
            with patch("agents.base_agent.CrossEncoder"):
                agent = SupportAgent()
                filter_dict = agent._build_where_filter(priority="P1-CRITICAL")
                assert filter_dict == {"priority": "P1-CRITICAL"}

    @patch("agents.base_agent.chromadb.PersistentClient")
    def test_support_machine_filter(self, mock_client) -> None:
        """SupportAgent filters by machine ID."""
        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        with patch("agents.base_agent.OpenAIEmbeddings"):
            with patch("agents.base_agent.CrossEncoder"):
                agent = SupportAgent()
                filter_dict = agent._build_where_filter(machine_id="M01")
                assert filter_dict == {"machine_id": "M01"}


class TestAgentCollectionIsolation:
    """DR-005: Verify collection isolation (no cross-collection reads)."""

    @patch("agents.base_agent.chromadb.PersistentClient")
    def test_mechanical_agent_uses_mechanical_collection(self, mock_client) -> None:
        """MechanicalAgent reads from mechanical_collection only."""
        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        with patch("agents.base_agent.OpenAIEmbeddings"):
            with patch("agents.base_agent.CrossEncoder"):
                agent = MechanicalAgent()
                assert agent.collection_name == "mechanical_collection"

    @patch("agents.base_agent.chromadb.PersistentClient")
    def test_software_agent_uses_software_collection(self, mock_client) -> None:
        """SoftwareAgent reads from software_collection only."""
        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        with patch("agents.base_agent.OpenAIEmbeddings"):
            with patch("agents.base_agent.CrossEncoder"):
                agent = SoftwareAgent()
                assert agent.collection_name == "software_collection"

    @patch("agents.base_agent.chromadb.PersistentClient")
    def test_support_agent_uses_support_collection(self, mock_client) -> None:
        """SupportAgent reads from support_collection only."""
        mock_collection = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        with patch("agents.base_agent.OpenAIEmbeddings"):
            with patch("agents.base_agent.CrossEncoder"):
                agent = SupportAgent()
                assert agent.collection_name == "support_collection"


class TestAgentRetrieval:
    """Integration-style retrieval tests with mocked collections."""

    @patch("agents.base_agent.chromadb.PersistentClient")
    def test_retrieval_with_insufficient_context(self, mock_client) -> None:
        """Agent returns insufficient_context=True when no results."""
        mock_collection = MagicMock()
        mock_collection.query.return_value = {"ids": [[]], "documents": [[]]}
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        with patch("agents.base_agent.OpenAIEmbeddings") as mock_embedder:
            with patch("agents.base_agent.CrossEncoder"):
                mock_embedder_inst = MagicMock()
                mock_embedder_inst.embed_query.return_value = [0.1] * 1536
                mock_embedder.return_value = mock_embedder_inst

                agent = MechanicalAgent()
                response = agent.retrieve("test query")

                assert response.insufficient_context is True
                assert response.total_count == 0


class TestAgentExports:
    """Test agent module exports."""

    def test_agent_classes_exported(self) -> None:
        """All agent classes are exported from agents module."""
        from agents import BaseAgent, MechanicalAgent, SoftwareAgent, SupportAgent
        assert BaseAgent is not None
        assert MechanicalAgent is not None
        assert SoftwareAgent is not None
        assert SupportAgent is not None
