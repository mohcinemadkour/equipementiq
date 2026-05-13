#!/usr/bin/env python
"""Diagnostic checks for SPN-MJ-004 indexing and retrieval"""

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

print("="*100)
print("CHECK 1: Metadata Filter Query for SPN-MJ-004")
print("="*100)

try:
    results = soft_col.get(
        where={"error_code": "SPN-MJ-004"},
        include=["documents", "metadatas"]
    )
    
    if results["ids"]:
        print(f"\n✓ Found {len(results['ids'])} document(s) with error_code=SPN-MJ-004")
        for i, doc_id in enumerate(results["ids"], 1):
            print(f"  {i}. Document ID: {doc_id}")
            metadata = results["metadatas"][i-1]
            print(f"     source_document: {metadata.get('source_document', 'N/A')}")
            print(f"     error_code: {metadata.get('error_code', 'N/A')}")
            print(f"     severity_level: {metadata.get('severity_level', 'N/A')}")
    else:
        print("\n✗ No documents found with error_code=SPN-MJ-004")
        print("  This means the document was NOT properly indexed.")
        
except Exception as e:
    print(f"\n✗ Error during metadata query: {e}")

print("\n" + "="*100)
print("CHECK 2: Semantic Query for 'SPN-MJ-004 probable cause chatter regenerative stability'")
print("="*100)

try:
    from langchain_openai import OpenAIEmbeddings
    embedder = OpenAIEmbeddings(model="text-embedding-3-small")
    
    query_text = "SPN-MJ-004 probable cause chatter regenerative stability"
    embedding = embedder.embed_query(query_text)
    
    results = soft_col.query(
        query_embeddings=[embedding],
        n_results=8,
        include=["documents", "metadatas", "distances"]
    )
    
    print(f"\nQuery: '{query_text}'")
    print(f"\nTop 8 semantic matches:")
    print(f"{'Rank':<5} {'Document ID':<25} {'Error Code':<15} {'Similarity':<12}")
    print("-" * 60)
    
    for rank, (doc_id, metadata, distance) in enumerate(zip(
        results["ids"][0],
        results["metadatas"][0],
        results["distances"][0]
    ), 1):
        similarity = 1 - (distance ** 2 / 2)
        error_code = metadata.get('error_code', 'N/A')
        print(f"{rank:<5} {doc_id:<25} {error_code:<15} {similarity:.4f}")
    
    # Highlight if SPN-MJ-004 is in results
    error_codes = [m.get('error_code') for m in results["metadatas"][0]]
    if "SPN-MJ-004" in error_codes:
        rank = error_codes.index("SPN-MJ-004") + 1
        print(f"\n✓ SPN-MJ-004 found at rank {rank}")
    else:
        print(f"\n✗ SPN-MJ-004 NOT in top 8 semantic matches")
        print("  This indicates the semantic embedding is not matching the query well.")
    
except Exception as e:
    print(f"\n✗ Error during semantic query: {e}")

print("\n" + "="*100)
