#!/usr/bin/env python3
"""Debug: Compare orchestrator results vs golden set expectations."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.graph import run_query

# Load golden set
with open("evaluation/golden_set.jsonl", encoding="utf-8") as f:
    entries = [json.loads(line) for line in f]

print("Comparing orchestrator results vs golden set expectations:\n")

for i, entry in enumerate(entries[:3], 1):  # Just first 3 for debugging
    query = entry["query"]
    expected_ids = entry["expected_doc_ids"]
    agent = entry["agent"]
    
    print(f"[{i}] {agent.upper()}: {query[:60]}")
    
    # Run through orchestrator
    try:
        result = run_query(query)
        retrieved_ids = []
        if "merged_context" in result and result["merged_context"]:
            for chunk in result["merged_context"][:5]:
                doc_id = chunk.get("source_document") or chunk.get("chunk_id")
                if doc_id:
                    retrieved_ids.append(doc_id)
        
        print(f"  EXPECTED:  {expected_ids[:3]}")
        print(f"  RETRIEVED: {retrieved_ids[:3]}")
        
        # Check if first one matches
        if expected_ids and retrieved_ids:
            match = expected_ids[0] in retrieved_ids
            print(f"  Match: {match}")
        print()
    except Exception as e:
        print(f"  ERROR: {str(e)[:80]}\n")
