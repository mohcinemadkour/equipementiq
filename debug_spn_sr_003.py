#!/usr/bin/env python3
"""Debug why SPN-SR-003 query returns INSUFFICIENT_CONTEXT."""

import sys
import json
from pathlib import Path

workspace = Path(__file__).parent
sys.path.insert(0, str(workspace))

from agents.software_agent import SoftwareAgent
from ingestion.config import load_config

config = load_config()
agent = SoftwareAgent(config)

# The problematic query
query = "SPN-SR-003 is active. If I ignore it, what fires next?"

print("=" * 90)
print("DEBUG: SPN-SR-003 Escalation Query")
print("=" * 90)
print()
print(f"Query: {query}")
print()

# Run retrieval through agent
result = agent.retrieve_and_filter(
    query=query,
    top_k=5,
    severity_level=None,
    subsystem="SPN",
)

print(f"Retrieved {len(result.results)} chunks:")
print()

for i, chunk in enumerate(result.results, 1):
    print(f"  [{i}] {chunk.source_document}")
    print(f"      Chunk ID: {chunk.chunk_id}")
    print(f"      Similarity: {chunk.similarity_score:.4f}")
    # Try to read the first 200 chars of the chunk
    # In case it's metadata, try to show it
    if hasattr(chunk, 'metadata'):
        if 'escalation_path' in chunk.metadata:
            print(f"      HAS escalation_path: {chunk.metadata['escalation_path'][:100]}...")
    print()

# Now directly check the ChromaDB for SPN-SR-003
print("=" * 90)
print("Direct ChromaDB Lookup for SPN-SR-003")
print("=" * 90)

import chromadb
chroma_client = chromadb.PersistentClient(path="chroma_db")
collection = chroma_client.get_collection(name="software_collection")

# Query by ID
results = collection.get(ids=["SPN-SR-003__0000"])
print(f"Documents found: {len(results['ids'])}")
if results['ids']:
    doc = results
    print(f"Metadata: {doc.get('metadatas', [{}])[0]}")
    if 'escalation_path' in (doc.get('metadatas', [{}])[0] or {}):
        print("✓ escalation_path IS stored in ChromaDB metadata")
    else:
        print("✗ escalation_path NOT in ChromaDB metadata")
print()

# Check similarity of the query to the document
print("=" * 90)
print("Semantic Similarity Check")
print("=" * 90)
results = collection.query(
    query_texts=[query],
    n_results=10,
    include=["documents", "metadatas", "distances"]
)

print(f"Top-10 results for query:")
for i, (doc_id, distance, metadata) in enumerate(
    zip(results['ids'][0], results['distances'][0], results['metadatas'][0]), 1
):
    similarity = 1 - (distance ** 2 / 2)  # L2 to cosine
    print(f"  [{i}] {doc_id:20s} | similarity={similarity:.4f} | {metadata.get('severity_level', '?')}")

print()
