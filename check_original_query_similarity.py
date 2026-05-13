#!/usr/bin/env python
"""Check semantic similarity for original Query 5"""

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

# Original failing query
original_query = "What is the probable cause of error SPN-MJ-004?"
print(f"Original Query: '{original_query}'")
print("="*100)

embedding = embedder.embed_query(original_query)
results = soft_col.query(
    query_embeddings=[embedding],
    n_results=15,
    include=["metadatas", "distances"]
)

print(f"\nTop 15 semantic matches:")
print(f"{'Rank':<5} {'Error Code':<15} {'Similarity':<12} {'Is SPN-MJ-004?':<15}")
print("-" * 50)

for rank, (metadata, distance) in enumerate(zip(
    results["metadatas"][0],
    results["distances"][0]
), 1):
    similarity = 1 - (distance ** 2 / 2)
    error_code = metadata.get('error_code', 'N/A')
    is_target = "← TARGET" if error_code == "SPN-MJ-004" else ""
    print(f"{rank:<5} {error_code:<15} {similarity:.4f}        {is_target:<15}")

# Find where SPN-MJ-004 ranks
error_codes = [m.get('error_code') for m in results["metadatas"][0]]
if "SPN-MJ-004" in error_codes:
    rank = error_codes.index("SPN-MJ-004") + 1
    similarity = 1 - (results["distances"][0][rank-1] ** 2 / 2)
    print(f"\n✓ SPN-MJ-004 found at rank {rank} with similarity {similarity:.4f}")
    print(f"  The software agent's top_k_retrieval is {8}, so SPN-MJ-004 IS retrieved")
    print(f"  But it's ranked below other documents, so it may not make it past similarity floor")
else:
    print(f"\n✗ SPN-MJ-004 NOT in top 15 semantic matches for original query")

print("\n" + "="*100)
