#!/usr/bin/env python3
"""Debug: Inspect actual merged_context structure from orchestrator."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.graph import run_query

query = "What are the specifications for spindle bearing replacement?"
print(f"Query: {query}\n")

try:
    result = run_query(query)
    
    if "merged_context" in result and result["merged_context"]:
        print(f"merged_context has {len(result['merged_context'])} items:\n")
        
        for i, chunk in enumerate(result["merged_context"][:3]):
            print(f"Item {i}:")
            print(f"  Keys: {list(chunk.keys())}")
            print(f"  source_document: {chunk.get('source_document')}")
            print(f"  chunk_id: {chunk.get('chunk_id')}")
            print(f"  Full item: {chunk}")
            print()
    else:
        print("No merged_context in result")
        print(f"Result keys: {list(result.keys())}")
        
except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
