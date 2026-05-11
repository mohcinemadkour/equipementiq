#!/usr/bin/env python3
"""Debug support document ID retrieval."""

import json
from orchestrator.graph import run_query

# Load golden set
with open('evaluation/golden_set.jsonl', encoding='utf-8') as f:
    pairs = [json.loads(line) for line in f]

# Get support pairs
support_pairs = [p for p in pairs if p['agent'] == 'support']

print("Support Golden Set - Expected vs Retrieved IDs")
print("=" * 80)

for i, pair in enumerate(support_pairs[:3], 1):
    query = pair['query']
    expected_ids = pair['expected_doc_ids']
    
    print(f"\n{i}. Query: {query[:70]}...")
    print(f"   Expected: {expected_ids}")
    
    # Run through orchestrator
    try:
        result = run_query(query)
        
        retrieved_ids = []
        if 'merged_context' in result and result['merged_context']:
            for chunk in result['merged_context'][:5]:
                doc_id = chunk.get('source_document') or chunk.get('chunk_id')
                if doc_id:
                    retrieved_ids.append(doc_id)
        
        print(f"   Retrieved: {retrieved_ids[:5]}")
        
        # Check for matches
        matches = [e for e in expected_ids if e in retrieved_ids]
        if matches:
            print(f"   [OK] MATCH: {matches}")
        else:
            print(f"   [FAIL] NO MATCH")
    except Exception as e:
        print(f"   [ERROR] {str(e)[:100]}")
