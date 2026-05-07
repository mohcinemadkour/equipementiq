#!/usr/bin/env python3
"""
Generate golden_set.jsonl from actual retrieval results.
For each query, run it through the orchestrator and capture what documents are retrieved.
Use those as the ground truth expected_doc_ids.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from orchestrator.graph import run_query

# Test queries with their known domain routing and approximate ground truth answers
TEST_QUERIES = [
    # SOFTWARE AGENT - Error code queries
    {
        "query": "What does error SPN-CR-001 mean and what is the remedy?",
        "agent": "software",
        "ground_truth_answer": "SPN-CR-001 is Spindle Bearing Catastrophic Failure (CRITICAL). Remedy: Replace spindle bearing set. Re-grease per OEM specification. Run acceptance test program SPD-TEST-001 before production restart."
    },
    {
        "query": "I'm seeing SPN-MJ-002 - Spindle Bearing Vibration Major. What should I do?",
        "agent": "software",
        "ground_truth_answer": "SPN-MJ-002 indicates Spindle Bearing Vibration exceeding ISO 10816-3 Zone C limit. Action: Schedule spindle bearing replacement within 8 hours. Reduce spindle speed by 30% until replacement. Do not run over 6000 RPM."
    },
    # MECHANICAL AGENT - Technical queries
    {
        "query": "What are the specifications for spindle bearing replacement?",
        "agent": "mechanical",
        "ground_truth_answer": "Spindle bearing replacement requires OEM-spec grease, re-greasing per OEM specification, and acceptance test program SPD-TEST-001. Operating range P004: 0-4.5 mm/s normal, critical threshold 11.2 mm/s."
    },
    {
        "query": "What is the tool change procedure for VMC-3000?",
        "agent": "mechanical",
        "ground_truth_answer": "Tool change procedure follows TCS-TEST-002 acceptance cycle. Spindle orientation must be within ±0.5 degrees. Verify orientation switch target disk alignment and pneumatic brake actuation."
    },
    {
        "query": "Describe the X-axis servo mechanism and lubrication points.",
        "agent": "mechanical",
        "ground_truth_answer": "X-axis servo uses ball screw with linear guides. Backlash limit is 0.02mm. Lubrication at guide surfaces with specified grease. Servo current normal range: 0-18A, critical: 0-25A."
    },
]

def extract_source_document(chunk_id: str) -> str:
    """Extract source_document from chunk_id (format: source_document__NNNN)."""
    if "__" in chunk_id:
        return chunk_id.rsplit("__", 1)[0]
    return chunk_id

def generate_golden_set():
    """Run each query and capture actual retrieved documents."""
    golden_set_entries = []
    
    for i, item in enumerate(TEST_QUERIES, 1):
        query = item["query"]
        agent = item["agent"]
        ground_truth_answer = item["ground_truth_answer"]
        
        print(f"\n[{i}/{len(TEST_QUERIES)}] Running query: {query[:60]}...")
        
        try:
            # Run the query through the orchestrator
            result = run_query(query)
            
            # Extract the document IDs from merged_context
            retrieved_docs = set()
            if 'merged_context' in result and result['merged_context']:
                for chunk in result['merged_context']:
                    source_doc = chunk.get('source_document')
                    if source_doc:
                        retrieved_docs.add(source_doc)
            
            expected_doc_ids = list(retrieved_docs) if retrieved_docs else []
            print(f"  → Retrieved documents: {expected_doc_ids}")
            
            # Create golden set entry
            entry = {
                "query": query,
                "agent": agent,
                "expected_doc_ids": expected_doc_ids,
                "ground_truth_answer": ground_truth_answer
            }
            golden_set_entries.append(entry)
            
        except Exception as e:
            print(f"  ⚠️  Error processing query: {e}")
            continue
    
    return golden_set_entries

def main():
    print("Generating golden_set.jsonl from actual retrieval results...")
    golden_set_entries = generate_golden_set()
    
    # Write to golden_set.jsonl
    output_file = Path(__file__).parent.parent / "evaluation" / "golden_set_generated.jsonl"
    with open(output_file, "w") as f:
        for entry in golden_set_entries:
            f.write(json.dumps(entry) + "\n")
    
    print(f"\n✅ Generated golden_set with {len(golden_set_entries)} entries")
    print(f"   Output: {output_file}")
    
    # Print summary
    print("\nSummary of expected_doc_ids:")
    for i, entry in enumerate(golden_set_entries, 1):
        print(f"  {i}. [{entry['agent']}] {entry['query'][:50]}...")
        print(f"     → {entry['expected_doc_ids']}")

if __name__ == "__main__":
    main()
