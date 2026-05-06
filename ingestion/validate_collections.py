"""Validate collections before merge (Phase 2 acceptance gate).

Checks:
1. All 3 collections exist
2. Mechanical has >= 50 chunks (DOC-EIQ-001..006)
3. Software has exactly 96 documents (error codes)
4. Support has exactly 150 documents (customer complaints)
5. Spot-check queries return results for each collection
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings

from ingestion.config import load_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)


def _get_client():
    """Get ChromaDB client."""
    cfg = load_config()
    persist_dir = PROJECT_ROOT / cfg["paths"]["chroma_persist_dir"]
    return chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False),
    )


def _get_embedder() -> OpenAIEmbeddings:
    """Get OpenAI embeddings."""
    cfg = load_config()["embeddings"]
    return OpenAIEmbeddings(model=cfg["model"])


def check_collections_exist() -> bool:
    """Check all 3 collections exist."""
    logging.info("✓ Checking collections exist...")
    cfg = load_config()
    client = _get_client()
    
    required = ["mechanical", "software", "support"]
    existing = {c["name"] for c in client.list_collections()}
    
    for name in required:
        coll_name = cfg["collections"][name]
        if coll_name not in existing:
            logging.error("✗ Missing collection: %s", coll_name)
            return False
        logging.info("  - %s: ✓", coll_name)
    
    return True


def check_mechanical_count() -> bool:
    """Mechanical collection should have >= 50 chunks."""
    logging.info("✓ Checking mechanical collection count...")
    cfg = load_config()
    client = _get_client()
    
    try:
        coll = client.get_collection(name=cfg["collections"]["mechanical"])
        count = coll.count()
        logging.info("  - Count: %d", count)
        if count >= 50:
            logging.info("  - Requirement (>= 50): ✓")
            return True
        else:
            logging.error("  - Requirement (>= 50): ✗ — got %d", count)
            return False
    except Exception as exc:
        logging.error("Failed to count mechanical: %s", exc)
        return False


def check_software_count() -> bool:
    """Software collection should have exactly 96 documents."""
    logging.info("✓ Checking software collection count...")
    cfg = load_config()
    client = _get_client()
    
    try:
        coll = client.get_collection(name=cfg["collections"]["software"])
        count = coll.count()
        logging.info("  - Count: %d", count)
        if count == 96:
            logging.info("  - Requirement (exactly 96): ✓")
            return True
        else:
            logging.error("  - Requirement (exactly 96): ✗ — got %d", count)
            return False
    except Exception as exc:
        logging.error("Failed to count software: %s", exc)
        return False


def check_support_count() -> bool:
    """Support collection should have exactly 150 documents."""
    logging.info("✓ Checking support collection count...")
    cfg = load_config()
    client = _get_client()
    
    try:
        coll = client.get_collection(name=cfg["collections"]["support"])
        count = coll.count()
        logging.info("  - Count: %d", count)
        if count == 150:
            logging.info("  - Requirement (exactly 150): ✓")
            return True
        else:
            logging.error("  - Requirement (exactly 150): ✗ — got %d", count)
            return False
    except Exception as exc:
        logging.error("Failed to count support: %s", exc)
        return False


def check_mechanical_query() -> bool:
    """Spot-check: spindle bearing query should return results."""
    logging.info("✓ Spot-checking mechanical collection query...")
    cfg = load_config()
    client = _get_client()
    embedder = _get_embedder()
    
    try:
        coll = client.get_collection(name=cfg["collections"]["mechanical"])
        query = "spindle bearing vibration diagnostics"
        query_embedding = embedder.embed_query(query)
        results = coll.query(query_embeddings=[query_embedding], n_results=1)
        
        if results["ids"] and len(results["ids"][0]) > 0:
            logging.info("  - Query returned: %d result(s) ✓", len(results["ids"][0]))
            return True
        else:
            logging.error("  - Query returned 0 results ✗")
            return False
    except Exception as exc:
        logging.error("Failed to query mechanical: %s", exc)
        return False


def check_software_query() -> bool:
    """Spot-check: error code query should return results."""
    logging.info("✓ Spot-checking software collection query...")
    cfg = load_config()
    client = _get_client()
    embedder = _get_embedder()
    
    try:
        coll = client.get_collection(name=cfg["collections"]["software"])
        query = "spindle alarm SPN-MJ bearing defect"
        query_embedding = embedder.embed_query(query)
        results = coll.query(query_embeddings=[query_embedding], n_results=1)
        
        if results["ids"] and len(results["ids"][0]) > 0:
            logging.info("  - Query returned: %d result(s) ✓", len(results["ids"][0]))
            return True
        else:
            logging.error("  - Query returned 0 results ✗")
            return False
    except Exception as exc:
        logging.error("Failed to query software: %s", exc)
        return False


def check_support_query() -> bool:
    """Spot-check: complaint query should return results."""
    logging.info("✓ Spot-checking support collection query...")
    cfg = load_config()
    client = _get_client()
    embedder = _get_embedder()
    
    try:
        coll = client.get_collection(name=cfg["collections"]["support"])
        query = "spindle bearing replacement warranty service"
        query_embedding = embedder.embed_query(query)
        results = coll.query(query_embeddings=[query_embedding], n_results=1)
        
        if results["ids"] and len(results["ids"][0]) > 0:
            logging.info("  - Query returned: %d result(s) ✓", len(results["ids"][0]))
            return True
        else:
            logging.error("  - Query returned 0 results ✗")
            return False
    except Exception as exc:
        logging.error("Failed to query support: %s", exc)
        return False


def run() -> int:
    """Run all validation checks. Return 0 on success, 1 on failure."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )
    
    logging.info("=" * 70)
    logging.info("Phase 2 — Ingestion Validation")
    logging.info("=" * 70)
    
    checks = [
        ("Collections exist", check_collections_exist),
        ("Mechanical count", check_mechanical_count),
        ("Software count", check_software_count),
        ("Support count", check_support_count),
        ("Mechanical query", check_mechanical_query),
        ("Software query", check_software_query),
        ("Support query", check_support_query),
    ]
    
    results = {}
    for name, check_fn in checks:
        try:
            results[name] = check_fn()
        except Exception as exc:
            logging.error("✗ %s failed: %s", name, exc)
            results[name] = False
        logging.info("")
    
    logging.info("=" * 70)
    logging.info("Summary")
    logging.info("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓" if result else "✗"
        logging.info("%s %s", status, name)
    
    logging.info("=" * 70)
    logging.info("Result: %d/%d checks passed", passed, total)
    logging.info("=" * 70)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run())
