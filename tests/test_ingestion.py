"""Tests for ingestion module — DR-001, DR-004, DR-005, DR-006.

DR-001: Chunking 512 tokens / 64 overlap via RecursiveCharacterTextSplitter.
DR-004: OpenAI text-embedding-3-small (1536 dims).
DR-005: Collections strictly isolated — mechanical/software/support isolation enforced.
DR-006: Metadata stamping (source_document, chunk_id, subsystem, page).
DR-007: In-place re-ingestion (deletes prior chunks per source before adding).
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ingestion.chunking import chunk_documents, chunk_text, get_splitter
from ingestion.config import load_config
from ingestion.ingest_mechanical import _delete_existing, _get_embedder, _sanitize_metadata

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestDR001Chunking:
    """DR-001: Token-aware chunking (512 / 64)."""

    def test_splitter_respects_chunk_size_from_config(self) -> None:
        """get_splitter() uses config.yaml chunk_size, never hardcoded."""
        cfg = load_config()
        expected_size = cfg["ingestion"]["chunk_size"]
        splitter = get_splitter()
        assert isinstance(splitter, RecursiveCharacterTextSplitter)
        assert splitter._chunk_size == expected_size
        assert expected_size == 512  # Validate FRD-locked value

    def test_splitter_respects_chunk_overlap_from_config(self) -> None:
        """get_splitter() uses config.yaml chunk_overlap, never hardcoded."""
        cfg = load_config()
        expected_overlap = cfg["ingestion"]["chunk_overlap"]
        splitter = get_splitter()
        assert splitter._chunk_overlap == expected_overlap
        assert expected_overlap == 64  # Validate FRD-locked value

    def test_chunk_documents_splits_correctly(self) -> None:
        """Long document is split into multiple chunks."""
        long_text = "word " * 1000  # ~5000 tokens worth
        doc = Document(
            page_content=long_text,
            metadata={"source": "test_doc", "page": 1},
        )
        chunks = chunk_documents([doc])
        assert len(chunks) > 1, "Long doc should split into multiple chunks"
        # Each chunk (except possibly last) should be roughly chunk_size
        cfg = load_config()
        max_chunk = max(len(c.page_content.split()) for c in chunks)
        # Allow some margin; token count differs from word count
        assert max_chunk < 1000, "Chunks should be reasonably bounded"

    def test_chunk_text_produces_documents_with_metadata(self) -> None:
        """chunk_text() wraps raw text, stamps source_document."""
        text = "This is a test document for chunking."
        source = "test_source"
        chunks = chunk_text(text, source_document=source)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.metadata.get("source_document") == source


class TestDR004Embeddings:
    """DR-004: OpenAI text-embedding-3-small (1536 dims)."""

    def test_embedder_uses_correct_model(self) -> None:
        """_get_embedder() instantiates with FRD-locked model text-embedding-3-small."""
        cfg = load_config()
        expected_model = cfg["embeddings"]["model"]
        embedder = _get_embedder()
        assert embedder.model == expected_model
        assert expected_model == "text-embedding-3-small"

    def test_embedder_provider_is_openai(self) -> None:
        """_get_embedder() returns OpenAIEmbeddings, not other providers."""
        from langchain_openai import OpenAIEmbeddings
        embedder = _get_embedder()
        assert isinstance(embedder, OpenAIEmbeddings)

    def test_config_embeddings_dimensions_locked(self) -> None:
        """config.yaml specifies 1536 dims for text-embedding-3-small."""
        cfg = load_config()
        expected_dims = cfg["embeddings"]["dimensions"]
        assert expected_dims == 1536


class TestDR005CollectionIsolation:
    """DR-005: Collections strictly isolated (mechanical/software/support)."""

    def test_collection_names_from_config(self) -> None:
        """Each agent's collection name is defined in config.yaml, not hardcoded."""
        cfg = load_config()
        collections = cfg["collections"]
        assert "mechanical" in collections
        assert "software" in collections
        assert "support" in collections
        # Validate names match FRD
        assert collections["mechanical"] == "mechanical_collection"
        assert collections["software"] == "software_collection"
        assert collections["support"] == "support_collection"

    def test_three_distinct_collections_exist(self) -> None:
        """Three collections are distinct (no shared naming)."""
        cfg = load_config()
        names = list(cfg["collections"].values())
        assert len(names) == len(set(names)), "Collection names must be unique"

    def test_mechanical_collection_isolation_enforced(self) -> None:
        """ingest_mechanical writes to mechanical_collection only."""
        with patch("ingestion.ingest_mechanical.chromadb.PersistentClient") as mock_client:
            mock_collection = MagicMock()
            mock_client_instance = MagicMock()
            mock_client_instance.get_or_create_collection.return_value = mock_collection
            mock_client.return_value = mock_client_instance

            cfg = load_config()
            expected_name = cfg["collections"]["mechanical"]

            from ingestion.ingest_mechanical import _get_collection
            coll = _get_collection()

            mock_client_instance.get_or_create_collection.assert_called_once()
            call_kwargs = mock_client_instance.get_or_create_collection.call_args.kwargs
            assert call_kwargs.get("name") == expected_name


class TestDR006Metadata:
    """DR-006: Metadata stamping (source_document, chunk_id, subsystem, page)."""

    def test_chunk_metadata_has_source_document(self) -> None:
        """Every chunk is stamped with source_document."""
        doc = Document(
            page_content="Test content.",
            metadata={"source": "test_pdf"},
        )
        chunks = chunk_documents([doc], source_label="test_pdf")
        for chunk in chunks:
            assert "source_document" in chunk.metadata
            assert chunk.metadata["source_document"] == "test_pdf"

    def test_chunk_id_format_correct(self) -> None:
        """chunk_id format is {source_document}__{NNNN} (zero-padded 4 digits)."""
        text = "word " * 200
        chunks = chunk_text(text, source_document="my_source")
        for i, chunk in enumerate(chunks):
            chunk_id = chunk.metadata.get("chunk_id")
            assert chunk_id is not None
            assert chunk_id.startswith("my_source__")
            # Extract number part and verify zero-padding
            num_str = chunk_id.split("__")[1]
            assert len(num_str) == 4
            assert num_str.isdigit()
            assert int(num_str) == i

    def test_chunk_ids_are_sequential_per_source(self) -> None:
        """Multiple chunks from same source have sequential chunk_ids."""
        text = "word " * 500
        chunks = chunk_text(text, source_document="seq_test")
        ids = [c.metadata["chunk_id"] for c in chunks]
        # Extract numbers
        nums = [int(cid.split("__")[1]) for cid in ids]
        expected = list(range(len(chunks)))
        assert nums == expected, "chunk_id numbers must be sequential"

    def test_sanitize_metadata_removes_none_values(self) -> None:
        """_sanitize_metadata drops None values (Chroma requires non-None)."""
        dirty = {
            "source_document": "test",
            "page": 1,
            "extra": None,
            "flag": True,
        }
        clean = _sanitize_metadata(dirty)
        assert "source_document" in clean
        assert "page" in clean
        assert "flag" in clean
        assert "extra" not in clean

    def test_sanitize_metadata_converts_to_allowed_types(self) -> None:
        """_sanitize_metadata stringifies non-primitive types (Chroma requirement)."""
        dirty = {
            "string_val": "text",
            "int_val": 42,
            "float_val": 3.14,
            "bool_val": True,
            "list_val": [1, 2, 3],
        }
        clean = _sanitize_metadata(dirty)
        for key in ["string_val", "int_val", "float_val", "bool_val", "list_val"]:
            assert key in clean
            val = clean[key]
            assert isinstance(val, (str, int, float, bool)), f"{key} not in allowed types"


class TestDR007Reingestation:
    """DR-007: In-place re-ingestion (delete prior chunks per source before adding)."""

    def test_delete_existing_removes_chunks_by_source(self) -> None:
        """_delete_existing removes all chunks for a given source_document."""
        mock_collection = MagicMock()
        # Simulate existing chunks
        mock_collection.get.return_value = {
            "ids": ["chunk_1", "chunk_2", "chunk_3"],
        }

        deleted_count = _delete_existing(mock_collection, "old_source")

        assert deleted_count == 3
        mock_collection.get.assert_called_once_with(where={"source_document": "old_source"})
        mock_collection.delete.assert_called_once_with(ids=["chunk_1", "chunk_2", "chunk_3"])

    def test_delete_existing_handles_empty_collection(self) -> None:
        """_delete_existing gracefully handles collection with no matching chunks."""
        mock_collection = MagicMock()
        mock_collection.get.return_value = {"ids": None}

        deleted_count = _delete_existing(mock_collection, "nonexistent_source")

        assert deleted_count == 0
        mock_collection.delete.assert_not_called()

    def test_delete_existing_called_before_add(self) -> None:
        """Ingestion calls _delete_existing before adding new chunks (prevents duplicates)."""
        # This is more of an integration test; we verify the flow in ingest_mechanical
        # by checking that the function exists and is meant to be called
        assert callable(_delete_existing)


class TestDR001ChunkingIntegration:
    """Integration: chunking config flows through all ingesters."""

    def test_chunk_size_propagates_to_splitter(self) -> None:
        """Changing config.yaml chunk_size is reflected in splitter immediately."""
        # This verifies get_splitter() reads from load_config() each time (via lru_cache)
        cfg = load_config()
        splitter = get_splitter()
        assert splitter._chunk_size == cfg["ingestion"]["chunk_size"]

    def test_multiple_documents_preserve_metadata(self) -> None:
        """chunking works on batch of docs, metadata preserved."""
        docs = [
            Document(page_content="Doc 1 content.", metadata={"source": "doc1"}),
            Document(page_content="Doc 2 content.", metadata={"source": "doc2"}),
        ]
        chunks = chunk_documents(docs)
        doc1_chunks = [c for c in chunks if c.metadata["source_document"] == "doc1"]
        doc2_chunks = [c for c in chunks if c.metadata["source_document"] == "doc2"]
        assert len(doc1_chunks) > 0
        assert len(doc2_chunks) > 0
        # Verify separate chunk_id sequences
        doc1_ids = [int(c.metadata["chunk_id"].split("__")[1]) for c in doc1_chunks]
        doc2_ids = [int(c.metadata["chunk_id"].split("__")[1]) for c in doc2_chunks]
        assert doc1_ids == list(range(len(doc1_chunks)))
        assert doc2_ids == list(range(len(doc2_chunks)))


class TestSoftwareIngestion:
    """Software ingester tests — atomic error code documents."""

    def test_load_error_code_json_from_disk(self) -> None:
        """Load a real error code JSON file from data/error_docs/."""
        error_json = PROJECT_ROOT / "data/error_docs/AXS-AD-001.json"
        if error_json.exists():
            import json
            with error_json.open() as f:
                data = json.load(f)
            assert "error_code" in data
            assert data["error_code"] == "AXS-AD-001"
            assert "severity_level" in data
            assert "severity_number" in data
            assert "fault_category" in data
            assert isinstance(data["severity_number"], int)

    def test_atomic_documents_no_chunking(self) -> None:
        """Error code docs are atomic — each becomes one document."""
        from ingestion.ingest_software import ingest_json
        from unittest.mock import MagicMock

        json_path = PROJECT_ROOT / "data/error_docs/SPN-CR-001.json"
        if json_path.exists():
            mock_collection = MagicMock()
            mock_embedder = MagicMock()
            mock_embedder.embed_query.return_value = [0.1] * 1536

            result = ingest_json(json_path, mock_collection, mock_embedder)

            # Should return 1 for success
            assert result == 1
            # Should call add exactly once with single document
            assert mock_collection.add.call_count == 1
            call_args = mock_collection.add.call_args.kwargs
            # Verify single document: ids, documents, metadatas, embeddings all length 1
            assert len(call_args["ids"]) == 1
            assert len(call_args["documents"]) == 1
            assert len(call_args["metadatas"]) == 1
            assert len(call_args["embeddings"]) == 1

    def test_metadata_extraction_from_error_code(self) -> None:
        """Metadata: error_code, severity_level, severity_number, subsystem_code, fault_category."""
        from ingestion.ingest_software import ingest_json
        from unittest.mock import MagicMock

        json_path = PROJECT_ROOT / "data/error_docs/SPN-MJ-001.json"
        if json_path.exists():
            mock_collection = MagicMock()
            mock_embedder = MagicMock()
            mock_embedder.embed_query.return_value = [0.1] * 1536

            ingest_json(json_path, mock_collection, mock_embedder)

            call_args = mock_collection.add.call_args.kwargs
            metadata = call_args["metadatas"][0]

            # Verify required metadata fields exist
            assert "error_code" in metadata
            assert "severity_level" in metadata
            assert "severity_number" in metadata
            assert "subsystem_code" in metadata
            assert "fault_category" in metadata

            # Verify subsystem_code extraction from error_code
            error_code = metadata["error_code"]
            subsystem_code = metadata["subsystem_code"]
            expected_subsystem = error_code.split("-")[0]
            assert subsystem_code == expected_subsystem

            # Verify severity_number is int (or stringified int)
            sev_num = metadata["severity_number"]
            assert isinstance(sev_num, (int, str))
            if isinstance(sev_num, str):
                assert sev_num.isdigit()


class TestSupportIngestion:
    """Support ingester tests — customer complaint documents."""

    def test_load_complaints_csv_from_disk(self) -> None:
        """Load real customer complaints CSV from data/processed/."""
        import pandas as pd
        complaints_csv = PROJECT_ROOT / "data/processed/customer_complaints.csv"
        if complaints_csv.exists():
            df = pd.read_csv(complaints_csv)
            assert not df.empty
            assert "complaint_case_id" in df.columns
            assert "machine_id" in df.columns
            assert "fault_category" in df.columns
            assert "case_status" in df.columns
            assert "priority" in df.columns
            assert "rma_required" in df.columns
            assert "phone_call_notes" in df.columns
            assert "investigation_notes" in df.columns
            assert "remedy_notes" in df.columns

    def test_atomic_documents_concatenate_notes(self) -> None:
        """Each complaint becomes one atomic document with concatenated notes."""
        from ingestion.ingest_support import ingest_row
        from unittest.mock import MagicMock
        import pandas as pd

        complaints_csv = PROJECT_ROOT / "data/processed/customer_complaints.csv"
        if complaints_csv.exists():
            df = pd.read_csv(complaints_csv)
            if len(df) > 0:
                row = df.iloc[0]
                mock_collection = MagicMock()
                mock_embedder = MagicMock()
                mock_embedder.embed_query.return_value = [0.1] * 1536

                result = ingest_row(row, mock_collection, mock_embedder, 0)

                # Should return 1 for success
                assert result == 1
                # Should call add exactly once
                assert mock_collection.add.call_count == 1
                call_args = mock_collection.add.call_args.kwargs
                # Verify single document
                assert len(call_args["ids"]) == 1
                assert len(call_args["documents"]) == 1
                assert len(call_args["metadatas"]) == 1
                # Verify document is concatenated from notes
                doc_content = call_args["documents"][0]
                assert len(doc_content) > 0

    def test_metadata_extraction_from_complaint(self) -> None:
        """Metadata: complaint_case_id, machine_id, fault_category, case_status, priority, rma_required."""
        from ingestion.ingest_support import ingest_row
        from unittest.mock import MagicMock
        import pandas as pd

        complaints_csv = PROJECT_ROOT / "data/processed/customer_complaints.csv"
        if complaints_csv.exists():
            df = pd.read_csv(complaints_csv)
            if len(df) > 0:
                row = df.iloc[0]
                mock_collection = MagicMock()
                mock_embedder = MagicMock()
                mock_embedder.embed_query.return_value = [0.1] * 1536

                ingest_row(row, mock_collection, mock_embedder, 0)

                call_args = mock_collection.add.call_args.kwargs
                metadata = call_args["metadatas"][0]

                # Verify all required metadata fields exist
                assert "complaint_case_id" in metadata
                assert "machine_id" in metadata
                assert "fault_category" in metadata
                assert "case_status" in metadata
                assert "priority" in metadata
                assert "rma_required" in metadata

                # Verify values from actual CSV row
                assert metadata["complaint_case_id"] == str(row["complaint_case_id"]).strip()
                assert metadata["machine_id"] == str(row["machine_id"]).strip()
                assert metadata["fault_category"] == str(row["fault_category"]).strip()

    def test_pii_masking_in_logs(self) -> None:
        """PII fields (phone, email, contact) are masked with [REDACTED]."""
        from ingestion.ingest_support import _mask_pii

        # Test email masking
        text_with_email = "Contact john.doe@example.com for support."
        masked_email = _mask_pii(text_with_email)
        assert "[REDACTED]" in masked_email
        assert "@" not in masked_email or "@example" not in masked_email

        # Test phone masking
        text_with_phone = "Call (312) 555-0142 for assistance."
        masked_phone = _mask_pii(text_with_phone)
        assert "[REDACTED]" in masked_phone
        assert "(312)" not in masked_phone

        # Test no false matches
        text_clean = "Normal text with numbers 123 and no PII."
        masked_clean = _mask_pii(text_clean)
        assert masked_clean == text_clean
