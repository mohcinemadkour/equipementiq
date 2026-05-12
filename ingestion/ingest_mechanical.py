"""Ingest the 6 DOC-EIQ technical PDFs into mechanical_collection.

DR-001 chunking (512/64 tokens) + DR-004 OpenAI text-embedding-3-small +
DR-005 strict collection isolation (writes only to mechanical_collection) +
DR-006 metadata (source_document, chunk_id, subsystem, page) +
DR-007 in-place re-ingest (deletes existing chunks per source before adding).

Run from the project root:
    python -m ingestion.ingest_mechanical
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings

from ingestion.chunking import chunk_documents, load_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)

# Per FRD §3.1.1 — primary subsystem tag enables filtered retrieval (DR-006).
# Multi-subsystem PDFs tagged with their dominant subsystem.
PDF_SUBSYSTEM: dict[str, str] = {
    "DOC-EIQ-001_Machine_Overview":            "overview",
    "DOC-EIQ-002_Spindle_Drive_System":        "SPN",
    "DOC-EIQ-003_Axis_Servo_Motion_Control":   "AXS",
    "DOC-EIQ-004_Coolant_Lubrication_Systems": "CLS",   # also LUB, HYD
    "DOC-EIQ-005_Vibration_Condition_Monitoring": "VIB",
    "DOC-EIQ-006_Electrical_CNC_Wiring":       "ELC",   # also THM, CNC
}


def _get_collection():
    cfg = load_config()
    persist_dir = PROJECT_ROOT / cfg["paths"]["chroma_persist_dir"]
    persist_dir.mkdir(exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(
        name=cfg["collections"]["mechanical"],
        metadata={"description": "VMC-3000 technical documentation (DOC-EIQ-001..006)"},
    )


def _get_embedder() -> OpenAIEmbeddings:
    cfg = load_config()["embeddings"]
    return OpenAIEmbeddings(model=cfg["model"])


def _sanitize_metadata(meta: dict) -> dict:
    """Chroma metadata values must be str/int/float/bool — drop None, stringify the rest."""
    clean: dict = {}
    for k, v in meta.items():
        if v is None:
            continue
        clean[k] = v if isinstance(v, (str, int, float, bool)) else str(v)
    return clean


def _delete_existing(collection, source_document: str) -> int:
    """DR-007 — re-ingestion updates in-place by dropping prior chunks for this source."""
    existing = collection.get(where={"source_document": source_document})
    ids = existing.get("ids") or []
    if ids:
        collection.delete(ids=ids)
    return len(ids)


def ingest_pdf(pdf_path: Path, collection, embedder: OpenAIEmbeddings) -> int:
    stem = pdf_path.stem
    subsystem = PDF_SUBSYSTEM.get(stem, "unknown")

    try:
        pages = PyPDFLoader(str(pdf_path)).load()
    except Exception as exc:  # DR-008 — log rejected documents, do not crash the run
        logger.exception("source=%s: PDF load failed (%s) — skipping", stem, exc)
        return 0

    if not pages:
        logger.warning("source=%s: 0 pages extracted — skipping", stem)
        return 0

    for p in pages:
        p.metadata = {
            **p.metadata,
            "source_document": stem,
            "subsystem": subsystem,
        }

    chunks = chunk_documents(pages, source_label=stem)
    if not chunks:
        logger.warning("source=%s: produced 0 chunks — skipping", stem)
        return 0

    deleted = _delete_existing(collection, stem)
    if deleted:
        logger.info("source=%s: deleted %d prior chunks (DR-007 in-place update)", stem, deleted)

    texts = [c.page_content for c in chunks]
    metadatas = [_sanitize_metadata(c.metadata) for c in chunks]
    ids = [c.metadata["chunk_id"] for c in chunks]
    embeddings = embedder.embed_documents(texts)

    collection.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)
    logger.info("source=%s: ingested %d chunks (subsystem=%s, pages=%d)",
                stem, len(chunks), subsystem, len(pages))
    return len(chunks)


def ingest_text_file(txt_path: Path, collection, embedder: OpenAIEmbeddings, subsystem: str = "VIB") -> int:
    """Ingest supplementary text files (e.g., vib_zone_detail.txt) into mechanical_collection.
    
    Args:
        txt_path: Path to .txt file
        collection: ChromaDB collection
        embedder: OpenAI embeddings instance
        subsystem: Subsystem tag for metadata
        
    Returns:
        Number of chunks ingested
    """
    stem = txt_path.stem
    stem = f"VMC3000_{stem}" if not stem.startswith("VMC3000") else stem

    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as exc:
        logger.exception("source=%s: Text file load failed (%s) — skipping", stem, exc)
        return 0

    if not content.strip():
        logger.warning("source=%s: file is empty — skipping", stem)
        return 0

    # Create a document-like object from the text file
    from langchain_core.documents import Document
    doc = Document(
        page_content=content,
        metadata={
            "source_document": stem,
            "subsystem": subsystem,
            "chunk_type": "supplementary",
            "source": str(txt_path),
        }
    )

    chunks = chunk_documents([doc], source_label=stem)
    if not chunks:
        logger.warning("source=%s: produced 0 chunks — skipping", stem)
        return 0

    deleted = _delete_existing(collection, stem)
    if deleted:
        logger.info("source=%s: deleted %d prior chunks (DR-007 in-place update)", stem, deleted)

    texts = [c.page_content for c in chunks]
    metadatas = [_sanitize_metadata(c.metadata) for c in chunks]
    ids = [c.metadata["chunk_id"] for c in chunks]
    embeddings = embedder.embed_documents(texts)

    collection.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)
    logger.info("source=%s: ingested %d chunks (subsystem=%s, type=supplementary)",
                stem, len(chunks), subsystem)
    return len(chunks)


def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    load_dotenv(PROJECT_ROOT / ".env")

    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "REPLACE_ME":
        sys.exit("OPENAI_API_KEY missing or placeholder — set it in .env before running.")

    cfg = load_config()
    pdfs_dir = PROJECT_ROOT / cfg["paths"]["pdfs_dir"]
    pdfs = sorted(pdfs_dir.glob("DOC-EIQ-*.pdf"))
    if not pdfs:
        sys.exit(f"No PDFs found in {pdfs_dir}")

    collection = _get_collection()
    embedder = _get_embedder()

    total = 0
    for pdf in pdfs:
        total += ingest_pdf(pdf, collection, embedder)

    # Also ingest supplementary text files if they exist
    supp_dir = PROJECT_ROOT / "data" / "supplementary"
    txt_count = 0
    if supp_dir.exists():
        txt_files = sorted(supp_dir.glob("*.txt"))
        txt_count = len(txt_files)
        for txt in txt_files:
            total += ingest_text_file(txt, collection, embedder, subsystem="VIB")

    logger.info("Done. mechanical_collection: %d chunks across %d PDFs and %d supplementary files.",
                collection.count(), len(pdfs), txt_count)


if __name__ == "__main__":
    run()
