#!/usr/bin/env python
"""Debug Query 5 specifically"""

import chromadb
from chromadb.config import Settings
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

persist_dir = Path(__file__).resolve().parent / "chroma_db"
client = chromadb.PersistentClient(
    path=str(persist_dir),
    settings=Settings(anonymized_telemetry=False)
)

soft_col = client.get_collection("software_collection")

from langchain_openai import OpenAIEmbeddings
embedder = OpenAIEmbeddings(model="text-embedding-3-small")

query = "What is the probable cause of error SPN-MJ-004?"
print(f"Query: {query}")
print("="*100)

embedding = embedder.embed_query(query)
results = soft_col.query(
    query_embeddings=[embedding],
    n_results=10,
    include=["documents", "metadatas", "distances"]
)

print("\nTop 10 matches:")
for i, (doc_id, metadata, distance) in enumerate(zip(
    results["ids"][0],
    results["metadatas"][0],
    results["distances"][0]
), 1):
    similarity = 1 - (distance ** 2 / 2)
    source = metadata.get('source_document', 'N/A')
    content_preview = results["documents"][0][i-1][:100] if results["documents"][0] else "N/A"
    print(f"{i:2}. {source:20} | Sim: {similarity:.4f} | {content_preview}...")

# Check if SPN-MJ-004 exists
print("\n" + "="*100)
print("Direct lookup for SPN-MJ-004:")
direct_results = soft_col.get(
    where={"source_document": "SPN-MJ-004"},
    include=["documents", "metadatas"]
)
if direct_results["ids"]:
    print(f"✓ Found {len(direct_results['ids'])} document(s)")
    doc = direct_results["documents"][0]
    print(f"First 200 chars: {doc[:200]}...")
else:
    print("✗ Not found in collection")
