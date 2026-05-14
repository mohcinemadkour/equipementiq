"""
Quick diagnostic for slow CMP query.
"""

import time
from orchestrator.graph import run_query

query = "complaint cmp-2019-1000?"

print(f"Query: {query!r}")
print("=" * 80)

start = time.time()
result = run_query(query)
total_time = time.time() - start

print(f"\nTotal time: {total_time:.1f}s")
print(f"Domain: {result.get('domain')}")
print(f"Confidence: {result.get('confidence'):.0%}")

node_latencies = result.get("node_latency", {})
print("\nNode latencies:")
for node, latency in sorted(node_latencies.items(), key=lambda x: x[1], reverse=True):
    print(f"  {node:<20} {latency:7.3f}s")

# Check if rule-based classifier fired
classify_time = node_latencies.get("classify_intent", 0)
if classify_time < 0.1:
    print(f"\n✅ Rule-based classifier FIRED (time: {classify_time:.3f}s)")
else:
    print(f"\n❌ Claude API CALLED (time: {classify_time:.3f}s) - rule-based didn't match!")
    print("   Check if 'cmp-2019-1000' matches the CMP-XXXX pattern")
