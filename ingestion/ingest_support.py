"""Ingest customer complaints CSV into support_collection.

DR-004: OpenAI text-embedding-3-small.
DR-005: Strict collection isolation (writes only to support_collection).
DR-006: Metadata (complaint_case_id, machine_id, fault_category, case_status, priority, rma_required).
NFR-SEC-002: Mask PII fields (customer_phone, customer_email, customer_contact) before logging.

Run from the project root:
    python -m ingestion.ingest_support
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import chromadb
import pandas as pd
from chromadb.config import Settings
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

from ingestion.config import load_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)


def _get_collection():
    """Get or create support_collection for customer complaints."""
    cfg = load_config()
    persist_dir = PROJECT_ROOT / cfg["paths"]["chroma_persist_dir"]
    persist_dir.mkdir(exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(
        name=cfg["collections"]["support"],
        metadata={"description": "VMC-3000 customer support cases (150 complaints)"},
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


def _mask_pii(text: str | None) -> str:
    """Replace PII patterns with [REDACTED]."""
    if not text:
        return ""
    # Email pattern
    text = __import__("re").sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED]", text)
    # Phone pattern (US format)
    text = __import__("re").sub(r"\(\d{3}\)\s*\d{3}-\d{4}", "[REDACTED]", text)
    return text


def _delete_existing(collection, complaint_case_id: str) -> int:
    """DR-007 — re-ingestion updates in-place by dropping prior document for this case."""
    existing = collection.get(where={"complaint_case_id": complaint_case_id})
    ids = existing.get("ids") or []
    if ids:
        collection.delete(ids=ids)
    return len(ids)


def ingest_row(
    row: pd.Series,
    collection,
    embedder: OpenAIEmbeddings,
    row_index: int,
) -> int:
    """Ingest a single complaint row as one atomic document.
    
    Returns 1 if successful, 0 if skipped.
    """
    complaint_case_id = row.get("complaint_case_id")
    if pd.isna(complaint_case_id) or not str(complaint_case_id).strip():
        logger.warning("row %d: missing complaint_case_id — skipping", row_index)
        return 0

    complaint_case_id = str(complaint_case_id).strip()

    # Extract fields
    machine_id = str(row.get("machine_id", "unknown")).strip()
    fault_category = str(row.get("fault_category", "unknown")).strip()
    case_status = str(row.get("case_status", "unknown")).strip()
    priority = str(row.get("priority", "unknown")).strip()
    rma_required = str(row.get("rma_required", "NO")).strip()

    # Concatenate notes into searchable text
    phone_notes = str(row.get("phone_call_notes") or "").strip()
    invest_notes = str(row.get("investigation_notes") or "").strip()
    remedy_notes = str(row.get("remedy_notes") or "").strip()
    
    page_content = f"{phone_notes}\n\n{invest_notes}\n\n{remedy_notes}"
    
    if not page_content.strip():
        logger.warning(
            "row %d: case=%s all notes empty — skipping",
            row_index,
            complaint_case_id,
        )
        return 0

    # Extract PII for masking in log message only
    customer_phone = str(row.get("customer_phone", "")).strip()
    customer_email = str(row.get("customer_email", "")).strip()
    customer_contact = str(row.get("customer_contact", "")).strip()
    
    # Build log message with masked PII
    log_msg = f"case={complaint_case_id}, machine={machine_id}, status={case_status}, priority={priority}"
    if customer_phone and customer_phone != "":
        log_msg += f", phone={_mask_pii(customer_phone)}"
    if customer_email and customer_email != "":
        log_msg += f", email={_mask_pii(customer_email)}"

    metadata = {
        "source_document": complaint_case_id,
        "chunk_id": f"{complaint_case_id}__0000",
        "complaint_case_id": complaint_case_id,
        "machine_id": machine_id,
        "fault_category": fault_category,
        "case_status": case_status,
        "priority": priority,
        "rma_required": rma_required,
    }

    # Delete existing to prevent duplicates (DR-007)
    deleted = _delete_existing(collection, complaint_case_id)
    if deleted:
        logger.info("%s: deleted %d prior document (DR-007 in-place update)", log_msg, deleted)

    # Create and embed
    try:
        embedding = embedder.embed_query(page_content)
    except Exception as exc:
        logger.exception("%s: embedding failed (%s) — skipping", log_msg, exc)
        return 0

    clean_meta = _sanitize_metadata(metadata)
    collection.add(
        ids=[metadata["chunk_id"]],
        documents=[page_content],
        metadatas=[clean_meta],
        embeddings=[embedding],
    )

    logger.info("%s: ingested (fault=%s, rma=%s)", log_msg, fault_category, rma_required)
    return 1


def run() -> None:
    """Load customer complaints CSV and persist to support_collection."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    load_dotenv(PROJECT_ROOT / ".env")

    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "REPLACE_ME":
        sys.exit("OPENAI_API_KEY missing or placeholder — set it in .env before running.")

    cfg = load_config()
    complaints_csv = PROJECT_ROOT / cfg["paths"]["complaints_csv"]
    
    if not complaints_csv.exists():
        sys.exit(f"Complaints CSV not found: {complaints_csv}")

    try:
        df = pd.read_csv(complaints_csv)
    except Exception as exc:
        sys.exit(f"Failed to load CSV: {exc}")

    if df.empty:
        sys.exit("Complaints CSV is empty")

    collection = _get_collection()
    embedder = _get_embedder()

    total = 0
    for idx, row in df.iterrows():
        total += ingest_row(row, collection, embedder, idx)

    logger.info("Done. support_collection: %d documents.", collection.count())


if __name__ == "__main__":
    run()
