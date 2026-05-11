#!/usr/bin/env python3
"""Test support retrieval with fixed golden set."""

import json
from orchestrator.graph import create_agent_graph

# Load orchestrator
graph = create_agent_graph()

# Load golden set
with open('evaluation/golden_set.jsonl', encoding='utf-8') as f:
    pairs = [json.loads(line) for line in f]

# Get support pairs
support_pairs = [p for p in pairs if p['agent'] == 'support']

print(f"Testing {len(support_pairs)} support queries...\n")

for i, pair in enumerate(support_pairs[:3], 1):  # Test first 3
    query = pair['query']
    expected_ids = pair['expected_doc_ids']
    
    print(f"{i}. Query: {query[:60]}...")
    print(f"   Expected IDs: {expected_ids}")
    
    # Run query through orchestrator
    try:
        result = graph.run_query(query, agent="support_agent", debug=False)
        
        # Check if any expected IDs are in the retrieved chunks
        retrieved_ids = result.get('chunk_ids', [])
        print(f"   Retrieved IDs (first 5): {retrieved_ids[:5]}")
        
        # Check for matches
        matches = [eid for eid in expected_ids if eid in retrieved_ids]
        if matches:
            print(f"   ✓ MATCH: {matches}")
        else:
            print(f"   ✗ NO MATCH - expected IDs not in top-5 retrieved")
    except Exception as e:
        print(f"   ERROR: {str(e)[:100]}")
    
    print()
