#!/usr/bin/env python3
"""Debug: Compare support golden set expectations vs actual collection results."""

import json
import sys
from pathlib import Path

import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

from ingestion.config import load_config

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent

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

# Load golden set
with open("evaluation/golden_set.jsonl", encoding="utf-8") as f:
    entries = [json.loads(line) for line in f if json.loads(line)["agent"] == "support"]

print(f"Analyzing {len(entries)} support golden set entries:\n")

client = _get_client()
embedder = _get_embedder()
collection = client.get_collection(name="support_collection")

for i, entry in enumerate(entries, 1):
    query = entry["query"]
    expected_ids = entry["expected_doc_ids"]
    
    print(f"[{i:2d}] Query: {query}")
    print(f"     Expected: {expected_ids}")
    
    # Query collection
    try:
        query_embedding = embedder.embed_query(query)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )
        
        # Get retrieved source_documents
        retrieved_ids = []
        if results["metadatas"] and len(results["metadatas"]) > 0:
            for metadata in results["metadatas"][0]:
                source_doc = metadata.get("source_document")
                if source_doc:
                    retrieved_ids.append(source_doc)
        
        print(f"     Retrieved: {retrieved_ids}")
        
        # Check matches
        matches = [doc_id for doc_id in expected_ids if doc_id in retrieved_ids]
        if matches:
            print(f"     Matches:   {matches} ✓")
        else:
            print(f"     Matches:   NONE ✗")
    
    except Exception as e:
        print(f"     ERROR: {str(e)[:80]}")
    
    print()
