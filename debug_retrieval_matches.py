#!/usr/bin/env python
"""Debug which documents are being matched for each failing query"""

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

# The 9 failing queries
queries = [
    ('What action does a WARNING severity error require?', 'WARNING'),
    ('Which error codes are related to SPN-MJ-002?', 'SPN-MJ-002'),
    ('What does error CLS-CR-001 mean and when is it triggered?', 'CLS-CR-001'),
    ('What does error ELC-CR-001 indicate?', 'ELC-CR-001'),
    ('What is the probable cause of error SPN-MJ-004?', 'SPN-MJ-004'),
    ('How many severity levels does the error code system have?', 'SEVERITY_SYSTEM'),
    ('What error code fires when the ATC arm collides?', 'ATC_COLLISION'),
    ('What does a NOTICE severity error require the operator to do?', 'NOTICE'),
    ('What is the required action for error code THM-CR-001?', 'THM-CR-001'),
]

print("="*100)
print("RETRIEVAL DEBUG: Which documents match for each failing query")
print("="*100)

for query_text, expected in queries:
    print(f"\nQuery: {query_text}")
    print(f"Expected match: {expected}")
    print("-" * 100)
    
    embedding = embedder.embed_query(query_text)
    results = soft_col.query(
        query_embeddings=[embedding],
        n_results=5,
        include=["documents", "metadatas", "distances"]
    )
    
    if results["ids"][0]:
        for i, (doc_id, metadata, distance) in enumerate(zip(
            results["ids"][0],
            results["metadatas"][0],
            results["distances"][0]
        ), 1):
            similarity = 1 - (distance ** 2 / 2)
            source = metadata.get('source_document', 'N/A')
            is_match = "✓ MATCH" if expected in source or source in expected else ""
            print(f"  {i}. {source:15} | Sim: {similarity:.3f} {is_match}")
    else:
        print("  (No results)")

print("\n" + "="*100)
print("Analysis: Check if expected error codes are matching with high similarity.")
print("="*100)
