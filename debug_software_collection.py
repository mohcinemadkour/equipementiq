#!/usr/bin/env python
"""Debug software_collection contents and statistics"""

import chromadb
from chromadb.config import Settings
from pathlib import Path

# Get ChromaDB client
persist_dir = Path(__file__).resolve().parent / "chroma_db"
client = chromadb.PersistentClient(
    path=str(persist_dir),
    settings=Settings(anonymized_telemetry=False)
)

# Try to get collections
try:
    collections = client.list_collections()
    print(f"Available collections: {len(collections)}")
    for col in collections:
        print(f"  - {col.name}")
except Exception as e:
    print(f"Error listing collections: {e}")

# Try to get software_collection
try:
    soft_col = client.get_collection("software_collection")
    print(f"\n✓ software_collection exists")
    print(f"  Count: {soft_col.count()}")
    
    # Get some sample documents
    results = soft_col.get(limit=5, include=["documents", "metadatas"])
    print(f"\n  Sample documents:")
    for i, (doc_id, metadata) in enumerate(zip(results["ids"], results["metadatas"]), 1):
        print(f"    {i}. {doc_id}")
        print(f"       Error Code: {metadata.get('source_document', 'N/A')}")
        print(f"       Subsystem: {metadata.get('subsystem_code', 'N/A')}")
        print(f"       Severity: {metadata.get('severity_level', 'N/A')}")
except Exception as e:
    print(f"\n✗ Error accessing software_collection: {e}")

# Test a retrieval query
print("\n" + "="*80)
print("Testing retrieval with semantic similarity:")
print("="*80)

try:
    from langchain_openai import OpenAIEmbeddings
    from dotenv import load_dotenv
    
    load_dotenv()
    
    embedder = OpenAIEmbeddings(model="text-embedding-3-small")
    soft_col = client.get_collection("software_collection")
    
    test_queries = [
        "What does error CLS-CR-001 mean?",
        "SPN-MJ-002 error code",
        "WARNING severity error action",
        "error code fires when ATC arm collides",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        embedding = embedder.embed_query(query)
        results = soft_col.query(
            query_embeddings=[embedding],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        
        if results["ids"][0]:
            for doc_id, metadata, distance in zip(
                results["ids"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                similarity = 1 - (distance ** 2 / 2)
                print(f"  • {metadata.get('source_document', 'N/A'):15} | Sim: {similarity:.3f}")
        else:
            print("  (No results)")
            
except Exception as e:
    print(f"Error during retrieval test: {e}")
