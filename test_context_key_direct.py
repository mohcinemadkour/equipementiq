"""
Direct test of the context key fix - minimal example.
"""

import sys
sys.path.insert(0, ".")

from orchestrator.graph import run_query

# Test one query
query = "What are the specifications for spindle bearing replacement?"

print("\n" + "="*100)
print("Testing context key fix")
print("="*100)

result = run_query(query)

print(f"\nMerged context type: {type(result.get('merged_context'))}")
print(f"Merged context length: {len(result.get('merged_context', []))}")

if result.get('merged_context'):
    first_chunk = result['merged_context'][0]
    print(f"\nFirst chunk keys: {list(first_chunk.keys())}")
    
    # Test OLD way (using 'content')
    context_chunks_old = [chunk.get('content', '') for chunk in result['merged_context']]
    print(f"OLD way (chunk.get('content', '')): {len(context_chunks_old)} chunks, {sum(len(c) for c in context_chunks_old)} total chars")
    
    # Test NEW way (using 'text')
    context_chunks_new = [chunk.get('text', '') for chunk in result['merged_context']]
    print(f"NEW way (chunk.get('text', '')): {len(context_chunks_new)} chunks, {sum(len(c) for c in context_chunks_new)} total chars")
    
    print(f"\nFirst chunk 'text' preview: {str(context_chunks_new[0])[:100]}...")
