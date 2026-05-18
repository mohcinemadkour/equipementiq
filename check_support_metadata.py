#!/usr/bin/env python
"""Check support_collection metadata schema."""

import chromadb
from pathlib import Path
from ingestion.config import load_config

cfg = load_config()
persist_dir = Path(__file__).resolve().parent / cfg["paths"]["chroma_persist_dir"]
client = chromadb.PersistentClient(path=str(persist_dir))
collection = client.get_collection(name=cfg["collections"]["support"])

# Get first few documents with metadata
results = collection.get(limit=5, include=["metadatas"])

print("Support Collection Metadata Schema")
print("=" * 80)
if results["metadatas"]:
    first_metadata = results["metadatas"][0]
    print("Sample metadata (first document):")
    for key, value in first_metadata.items():
        print(f"  {key}: {value} (type: {type(value).__name__})")
    
    print("\nAll available keys:")
    all_keys = set()
    for metadata in results["metadatas"]:
        all_keys.update(metadata.keys())
    for key in sorted(all_keys):
        print(f"  - {key}")
    
    # Check if error_code_triggered exists
    if "error_code_triggered" in all_keys:
        print("\n✓ error_code_triggered field FOUND")
        # Show sample values
        sample_values = set()
        for metadata in results["metadatas"]:
            val = metadata.get("error_code_triggered")
            if val:
                sample_values.add(str(val))
        print(f"  Sample values: {sample_values}")
    else:
        print("\n✗ error_code_triggered field NOT FOUND")
        # Check for similar fields
        error_fields = [k for k in all_keys if "error" in k.lower() or "code" in k.lower()]
        if error_fields:
            print(f"  Similar fields found: {error_fields}")
else:
    print("No documents found in collection!")
