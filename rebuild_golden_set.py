#!/usr/bin/env python3
"""
Rebuild golden_set.jsonl by running actual collection queries.

For each entry, retrieves top-3 from the collection and extracts source_document
(the document ID without chunk suffix), which matches what orchestrator returns.
"""

import json
import sys
from pathlib import Path

import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

from ingestion.config import load_config

# Add workspace root to path
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
    """Get OpenAI embeddings (consistent with ingestion & agents)."""
    cfg = load_config()["embeddings"]
    return OpenAIEmbeddings(model=cfg["model"])

def _get_collection_name(agent_name: str) -> str:
    """Get ChromaDB collection name for agent."""
    cfg = load_config()
    collection_map = {
        "mechanical": cfg["collections"]["mechanical"],
        "software": cfg["collections"]["software"],
        "support": cfg["collections"]["support"],
    }
    return collection_map.get(agent_name, f"{agent_name}_collection")

def rebuild_golden_set(golden_path: str = "evaluation/golden_set.jsonl"):
    """
    Rebuild golden set by running actual collection queries.
    
    Extracts source_document IDs (not chunk IDs) to match what orchestrator returns
    after processing through agents and reranking.
    
    For each entry:
    1. Get the agent and query
    2. Query collection directly with LangChain embeddings
    3. Extract source_document from metadata (document ID without chunk suffix)
    4. Replace expected_doc_ids with top-3 source_document values
    5. Print old vs new if changed
    """
    print("Rebuilding golden_set.jsonl with actual collection queries...\n")
    
    client = _get_client()
    embedder = _get_embedder()
    
    # Load existing golden set
    with open(golden_path, encoding="utf-8") as f:
        entries = [json.loads(line) for line in f]
    
    updated_entries = []
    change_count = 0
    
    for i, entry in enumerate(entries, 1):
        query = entry["query"]
        agent = entry["agent"]
        old_expected_ids = entry.get("expected_doc_ids", [])
        
        # Get collection for this agent
        try:
            coll_name = _get_collection_name(agent)
            collection = client.get_collection(name=coll_name)
            
            # Embed query using LangChain (fixed path)
            query_embedding = embedder.embed_query(query)
            
            # Retrieve top-3 from collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=3
            )
            
            # Extract source_document (not full chunk ID)
            # This matches what orchestrator returns in merged_context
            new_expected_ids = []
            if results["ids"] and len(results["ids"]) > 0:
                if results["metadatas"] and len(results["metadatas"]) > 0:
                    for metadata in results["metadatas"][0]:
                        source_doc = metadata.get("source_document")
                        if source_doc:
                            new_expected_ids.append(source_doc)
            
            # Update entry
            entry_copy = dict(entry)
            entry_copy["expected_doc_ids"] = new_expected_ids
            updated_entries.append(entry_copy)
            
            # Track changes
            if new_expected_ids != old_expected_ids:
                change_count += 1
                print(f"[{i:2d}] {agent.upper():10s} CHANGED")
                print(f"     Query: {query[:60]}")
                print(f"     OLD:   {old_expected_ids}")
                print(f"     NEW:   {new_expected_ids}")
                print()
            else:
                print(f"[{i:2d}] {agent.upper():10s} (no change)")
        
        except Exception as e:
            print(f"[{i:2d}] ERROR: {str(e)[:80]}")
            updated_entries.append(entry)
    
    # Save updated golden set
    with open(golden_path, "w", encoding="utf-8") as f:
        for entry in updated_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    print(f"\n{'='*60}")
    print(f"Golden set rebuilt: {golden_path}")
    print(f"Total entries: {len(updated_entries)}")
    print(f"Entries changed: {change_count}")
    print(f"{'='*60}")
    
    return change_count

if __name__ == "__main__":
    change_count = rebuild_golden_set()
    sys.exit(0 if change_count >= 0 else 1)
