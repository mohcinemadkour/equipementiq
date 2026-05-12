#!/usr/bin/env python3
"""Examine orchestrator trace to understand why chunks are filtered during synthesis."""

from dotenv import load_dotenv
load_dotenv()

from orchestrator.graph import run_query
import json

queries = [
    'What action does a WARNING severity error require?',
    'Which error codes are related to SPN-MJ-002?',
    'What does error CLS-CR-001 mean and when is it triggered?',
]

print("=" * 100)
print("EXAMINING ORCHESTRATOR TRACE - MERGED_CONTEXT ANALYSIS")
print("=" * 100)

for q in queries:
    print(f'\n\nQuery: {q}')
    print("-" * 100)
    
    r = run_query(q)
    
    # Print full trace
    print(f"Domain: {r['domain']}")
    print(f"Confidence: {r['confidence']}")
    print(f"Chunks retrieved: {len(r.get('chunk_ids', []))}")
    
    if r.get('chunk_ids'):
        print(f"Chunk IDs: {r.get('chunk_ids', [])}")
    
    print(f"Citation count in answer: {r.get('citation_count', 0)}")
    print(f"Merged context length: {len(r.get('merged_context', ''))}")
    
    # Show merged context to see if chunks made it through
    merged = r.get('merged_context', '')
    if merged:
        print(f"\nMerged context (first 500 chars):\n{merged[:500]}")
    else:
        print(f"\nMerged context: EMPTY")
    
    print(f"\nFinal answer (first 200 chars):\n{r.get('final_answer', 'N/A')[:200]}")

print("\n" + "=" * 100)
