#!/usr/bin/env python3
"""Quick test of routing accuracy computation after max_depth fix."""
import sys
sys.path.insert(0, '.')

from orchestrator.graph import run_query
import json

# Load golden set
golden = []
with open('evaluation/golden_set.jsonl') as f:
    for line in f:
        line = line.strip()
        if line:  # Skip empty lines
            golden.append(json.loads(line))

print(f"Loaded {len(golden)} golden set queries\n")

# Test first 5 queries
correct = 0
total = 0
errors = []

for i, q in enumerate(golden[:5]):
    try:
        result = run_query(q["query"])
        routed_domain = result.get("domain", "unknown")
        expected_agent = q.get("agent", "unknown")
        
        match = routed_domain == expected_agent
        status = "✓" if match else "✗"
        
        print(f"{status} Query {i+1}: '{q['query'][:40]}...'")
        print(f"   Expected: {expected_agent}, Got: {routed_domain}")
        
        if match:
            correct += 1
        total += 1
    except Exception as e:
        error_msg = str(e)[:60]
        print(f"✗ Query {i+1}: ERROR - {error_msg}")
        errors.append(f"Query '{q['query'][:30]}...': {error_msg}")
        total += 1

print(f"\n{'='*60}")
print(f"Routing Accuracy (first 5 queries): {correct}/{total} = {100*correct/total:.1f}%")
if errors:
    print(f"\nErrors encountered:")
    for err in errors:
        print(f"  - {err}")
