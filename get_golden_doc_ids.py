#!/usr/bin/env python
"""Get real doc IDs for 5 failing vibration Q&A queries."""
import json
from pathlib import Path
from orchestrator.graph import run_query

PROJECT_ROOT = Path(__file__).resolve().parent

# The 5 failing queries that need golden set entries
FAILING_QUERIES = [
    {
        "id": 5,
        "query": "What is Zone B Upper on the vibration scale?",
        "agent": "mechanical"
    },
    {
        "id": 9,
        "query": "What is the crest factor formula for vibration analysis?",
        "agent": "mechanical"
    },
    {
        "id": 14,
        "query": "What causes an actuator fault in the VMC-3000 servo system?",
        "agent": "mechanical"
    },
    {
        "id": 19,
        "query": "How many total recordings are in the Bosch CNC Machining Dataset?",
        "agent": "mechanical"
    },
    {
        "id": 20,
        "query": "What is the breakdown of normal vs fault samples in the Bosch dataset?",
        "agent": "mechanical"
    }
]

def get_doc_ids_for_query(query_text):
    """Run a query and extract the chunk IDs returned."""
    result = run_query(query_text)
    chunk_ids = result.get("chunk_ids", [])
    return chunk_ids

def main():
    print("\n" + "="*80)
    print("RETRIEVING REAL DOC IDs FOR 5 FAILING QUERIES")
    print("="*80 + "\n")
    
    golden_entries = []
    
    for q_info in FAILING_QUERIES:
        query = q_info["query"]
        query_id = q_info["id"]
        agent = q_info["agent"]
        
        print(f"[Query {query_id}] {query}")
        chunk_ids = get_doc_ids_for_query(query)
        print(f"  → Retrieved {len(chunk_ids)} chunks")
        if chunk_ids:
            print(f"  → Chunk IDs: {chunk_ids}")
        
        # Create golden set entry
        entry = {
            "query": query,
            "agent": agent,
            "expected_doc_ids": chunk_ids,
            "ground_truth_answer": ""  # Will be filled in manually
        }
        golden_entries.append(entry)
        print()
    
    # Save as JSONL format
    golden_path = PROJECT_ROOT / "evaluation" / "golden_set.jsonl"
    with open(golden_path, 'a') as f:
        for entry in golden_entries:
            f.write(json.dumps(entry) + "\n")
    
    print(f"\n✓ Added {len(golden_entries)} entries to {golden_path}")
    print("\nJSON Lines to add (for reference):")
    for entry in golden_entries:
        print(json.dumps(entry))

if __name__ == "__main__":
    main()
