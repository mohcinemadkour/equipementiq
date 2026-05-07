"""Check what run_query returns."""

from orchestrator.graph import run_query
import json

# Simple test query
result = run_query("What is SPN-CR-001?")

print("Keys in result:")
print(json.dumps(list(result.keys()), indent=2))

print("\nResult structure:")
print(json.dumps({k: type(v).__name__ for k, v in result.items()}, indent=2))

# Check merged_context
if 'merged_context' in result:
    print(f"\nmerged_context type: {type(result['merged_context'])}")
    print(f"merged_context length: {len(result['merged_context'])}")
    if result['merged_context']:
        print(f"First chunk: {result['merged_context'][0]}")
else:
    print("\nmerged_context NOT in result")
    
# Check citations
if 'citations' in result:
    print(f"\ncitations: {result['citations']}")
