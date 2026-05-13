"""Ingest the 96 error code JSONs into software_collection.

DR-001: Error code docs are atomic — no chunking.
DR-004: OpenAI text-embedding-3-small.
DR-005: Strict collection isolation (writes only to software_collection).
DR-006: Metadata (error_code, severity_level, severity_number, subsystem_code, fault_category).

Run from the project root:
    python -m ingestion.ingest_software
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from ingestion.config import load_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)


def _get_collection():
    """Get or create software_collection for error codes."""
    cfg = load_config()
    persist_dir = PROJECT_ROOT / cfg["paths"]["chroma_persist_dir"]
    persist_dir.mkdir(exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(
        name=cfg["collections"]["software"],
        metadata={"description": "VMC-3000 error codes (96 atomic documents, no chunking)"},
    )


def _get_embedder() -> OpenAIEmbeddings:
    """Get OpenAI embeddings adapter."""
    cfg = load_config()["embeddings"]
    return OpenAIEmbeddings(model=cfg["model"])


def _sanitize_metadata(meta: dict) -> dict:
    """Chroma metadata values must be str/int/float/bool — drop None, stringify the rest."""
    clean: dict = {}
    for k, v in meta.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        else:
            clean[k] = str(v)
    return clean


def _delete_existing(collection, error_code: str) -> int:
    """DR-007 — re-ingestion updates in-place by dropping prior document for this error code."""
    existing = collection.get(where={"error_code": error_code})
    ids = existing.get("ids") or []
    if ids:
        collection.delete(ids=ids)
    return len(ids)


def ingest_json(json_path: Path, collection, embedder: OpenAIEmbeddings) -> int:
    """Ingest a single error code JSON as one atomic document.
    
    Returns 1 if successful, 0 if skipped.
    """
    try:
        with json_path.open(encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        logger.exception("source=%s: JSON load failed (%s) — skipping", json_path.stem, exc)
        return 0

    # Extract required fields
    error_code = data.get("error_code")
    severity_level = data.get("severity_level")
    severity_number = data.get("severity_number")
    fault_category = data.get("fault_category")
    
    if not error_code:
        logger.warning("source=%s: missing error_code — skipping", json_path.stem)
        return 0

    # Extract subsystem_code from error_code (first 3 chars, e.g., "AXS" from "AXS-AD-001")
    subsystem_code = error_code.split("-")[0] if "-" in error_code else error_code[:3]

    # Build document content from key fields
    # Include error code name prominently for better semantic matching
    title = data.get("title", "")
    description = data.get("description", "")
    probable_cause = data.get("probable_cause", "")
    remedy = data.get("remedy", "")
    required_action = data.get("required_action", "")
    
    # Embed error code + severity + title multiple times for better semantic matching on error code queries
    # Repeat error code name and key fields to boost signal for exact error code queries
    page_content = (
        f"Error Code: {error_code}\n"
        f"{error_code}: {title}\n"
        f"Severity: {severity_level}\n\n"
        f"Error Code {error_code} - {title}\n\n"
        f"{description}\n\n"
        f"Probable Cause: {probable_cause}\n\n"
        f"Remedy: {remedy}\n\n"
        f"Required Action: {required_action}"
    )

    metadata = {
        "source_document": error_code,
        "chunk_id": f"{error_code}__0000",  # Single chunk per error code
        "error_code": error_code,
        "severity_level": severity_level,
        "severity_number": severity_number,
        "subsystem_code": subsystem_code,
        "fault_category": fault_category,
    }
    
    # Delete existing to prevent duplicates (DR-007)
    deleted = _delete_existing(collection, error_code)
    if deleted:
        logger.info("source=%s: deleted %d prior document (DR-007 in-place update)", error_code, deleted)

    # Create and embed
    try:
        embedding = embedder.embed_query(page_content)
    except Exception as exc:
        logger.exception("source=%s: embedding failed (%s) — skipping", error_code, exc)
        return 0

    clean_meta = _sanitize_metadata(metadata)
    collection.add(
        ids=[metadata["chunk_id"]],
        documents=[page_content],
        metadatas=[clean_meta],
        embeddings=[embedding],
    )
    
    logger.info("source=%s: ingested (severity=%s, subsystem=%s, category=%s)",
                error_code, severity_level, subsystem_code, fault_category)
    return 1


def run() -> None:
    """Load all 96 error code JSONs and persist to software_collection."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    load_dotenv(PROJECT_ROOT / ".env")

    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "REPLACE_ME":
        sys.exit("OPENAI_API_KEY missing or placeholder — set it in .env before running.")

    cfg = load_config()
    error_docs_dir = PROJECT_ROOT / cfg["paths"]["error_docs_dir"]
    jsons = sorted(error_docs_dir.glob("*.json"))
    
    if not jsons:
        sys.exit(f"No JSON files found in {error_docs_dir}")

    collection = _get_collection()
    embedder = _get_embedder()

    total = 0
    for json_file in jsons:
        total += ingest_json(json_file, collection, embedder)

    logger.info("Done. software_collection: %d documents (no chunking, 1:1 error code).",
                collection.count())


if __name__ == "__main__":
    run()
