"""Tests for config.yaml loading (NFR-MAINT-003 — single source of truth)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from ingestion import config as config_module
from ingestion.config import load_config


def _clear_cache() -> None:
    load_config.cache_clear()


def test_loads_successfully() -> None:
    """config.yaml exists, parses, and has every top-level section CLAUDE.md promises."""
    _clear_cache()
    cfg = load_config()
    assert isinstance(cfg, dict)
    expected = {
        "paths", "collections", "ingestion", "embeddings",
        "retrieval", "llm", "orchestrator", "evaluation",
        "feedback", "ui", "pii_fields",
    }
    missing = expected - cfg.keys()
    assert not missing, f"missing top-level sections: {missing}"


def test_raises_on_missing_file(tmp_path: Path) -> None:
    """If config.yaml isn't on disk, load_config() must fail loudly — never silently default."""
    _clear_cache()
    fake = tmp_path / "no_such_config.yaml"
    with patch.object(config_module, "CONFIG_PATH", fake):
        with pytest.raises(FileNotFoundError):
            load_config()
    _clear_cache()


def test_correct_types() -> None:
    """FRD-locked values must be the right shape — DR-001, FR-MECH-002/007, FR-ORCH-002/007."""
    _clear_cache()
    cfg = load_config()

    # Integers (token counts, top-K).
    assert isinstance(cfg["ingestion"]["chunk_size"], int)
    assert isinstance(cfg["ingestion"]["chunk_overlap"], int)
    assert isinstance(cfg["retrieval"]["top_k_retrieval"], int)
    assert isinstance(cfg["retrieval"]["top_k_final"], int)
    assert isinstance(cfg["embeddings"]["dimensions"], int)

    # Floats (similarity / probability thresholds).
    assert isinstance(cfg["retrieval"]["mmr_lambda"], float)
    assert isinstance(cfg["retrieval"]["oos_similarity_floor"], float)
    assert isinstance(cfg["orchestrator"]["intent_confidence_threshold"], float)

    # Strings (model + collection identifiers).
    assert isinstance(cfg["embeddings"]["model"], str)
    assert isinstance(cfg["llm"]["generation_model"], str)
    assert isinstance(cfg["collections"]["mechanical"], str)
    assert isinstance(cfg["collections"]["software"], str)
    assert isinstance(cfg["collections"]["support"], str)

    # Lists.
    assert isinstance(cfg["pii_fields"], list)
    assert all(isinstance(f, str) for f in cfg["pii_fields"])

    # Concrete FRD lock-in values.
    assert cfg["ingestion"]["chunk_size"] == 512                      # DR-001
    assert cfg["ingestion"]["chunk_overlap"] == 64                    # DR-001
    assert cfg["embeddings"]["model"] == "text-embedding-3-small"     # DR-004
    assert cfg["embeddings"]["dimensions"] == 1536                    # DR-004
    assert cfg["orchestrator"]["intent_confidence_threshold"] == 0.80  # FR-ORCH-002
