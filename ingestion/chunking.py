"""Shared chunking for all ingesters (DR-001).

config.yaml is the single source of truth for chunk_size / chunk_overlap.
All three ingesters (mechanical / software / support) import from here.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ingestion.config import load_config

# Re-export for backwards-compat with callers that imported from chunking.
__all__ = ["chunk_documents", "chunk_text", "get_splitter", "load_config"]


@lru_cache(maxsize=1)
def get_splitter() -> RecursiveCharacterTextSplitter:
    """Token-aware splitter via tiktoken — DR-001 specifies 512 *tokens* / 64 overlap, not characters."""
    cfg = load_config()["ingestion"]
    return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=cfg["chunk_size"],
        chunk_overlap=cfg["chunk_overlap"],
    )


def chunk_documents(
    docs: list[Document],
    *,
    source_label: str | None = None,
) -> list[Document]:
    """Split docs and stamp source_document + chunk_id on every chunk.

    chunk_id format: ``{source_document}__{NNNN}`` — sequential per source.
    If source_label is supplied it overrides any pre-existing source metadata
    (useful when LangChain loaders set ``metadata['source']`` to a file path).
    """
    splitter = get_splitter()
    sub_chunks = splitter.split_documents(docs)
    counters: dict[str, int] = {}
    for chunk in sub_chunks:
        if source_label:
            src = Path(source_label).stem
        else:
            raw = (
                chunk.metadata.get("source_document")
                or chunk.metadata.get("source")
                or "unknown"
            )
            src = Path(str(raw)).stem
        idx = counters.get(src, 0)
        chunk.metadata = {
            **chunk.metadata,
            "source_document": src,
            "chunk_id": f"{src}__{idx:04d}",
        }
        counters[src] = idx + 1
    return sub_chunks


def chunk_text(
    text: str,
    *,
    source_document: str,
    extra_metadata: dict | None = None,
) -> list[Document]:
    """Raw text + identifier -> chunked Documents with metadata stamped."""
    metadata = {"source_document": source_document, **(extra_metadata or {})}
    return chunk_documents(
        [Document(page_content=text, metadata=metadata)],
        source_label=source_document,
    )
