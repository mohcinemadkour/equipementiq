"""
Test script to measure query latencies with detailed breakdown.
Runs 3 queries and displays latency breakdown for each.
"""

import time
from orchestrator.graph import run_query

def test_query(query_text: str, description: str):
    """Test a single query and print latency breakdown."""
    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"Query: {query_text}")
    print(f"{'='*70}")
    
    start = time.time()
    result = run_query(query_text)
    total_time = time.time() - start
    
    print(f"\n✅ Query completed in {total_time:.2f}s")
    print(f"Domain: {result.get('domain')} ({result.get('confidence'):.1%} confidence)")
    
    # Show node latency breakdown
    node_latency = result.get("node_latency", {})
    if node_latency:
        print(f"\n📊 Latency Breakdown:")
        total_query = node_latency.get("total_query", 0)
        print(f"   Total (end-to-end): {total_query:.2f}s")
        
        # Sort by duration (longest first)
        sorted_latencies = sorted(
            [(k, v) for k, v in node_latency.items() if k != "total_query"],
            key=lambda x: x[1],
            reverse=True
        )
        
        for node_name, latency in sorted_latencies:
            pct = (latency / total_query * 100) if total_query > 0 else 0
            print(f"   • {node_name:20s}: {latency:.2f}s ({pct:5.1f}%)")
    
    # Show retrieved chunks
    print(f"\n📚 Retrieved chunks:")
    merged_context = result.get("merged_context", [])
    print(f"   Total chunks: {len(merged_context)}")
    for i, chunk in enumerate(merged_context[:3], 1):
        print(f"   [{i}] {chunk.get('source_document')} - {chunk.get('chunk_id')}")
    if len(merged_context) > 3:
        print(f"   ... and {len(merged_context)-3} more")
    
    return total_time

if __name__ == "__main__":
    print("\n🚀 Testing latency breakdown with detailed timing...\n")
    
    # Test 1: Support query (fast path with rule-based classifier)
    t1 = test_query(
        "Show me complaint case CMP-2019-1010",
        "Support Query (rule-based fast path)"
    )
    
    # Test 2: Same query again (should be slightly faster due to caching)
    t2 = test_query(
        "Show me complaint case CMP-2019-1010",
        "Support Query Again (cached)"
    )
    
    # Test 3: Error code query (rule-based)
    t3 = test_query(
        "What does error SPN-CR-001 mean?",
        "Software Error Code Query (rule-based fast path)"
    )
    
    # Summary
    print(f"\n{'='*70}")
    print(f"📋 SUMMARY")
    print(f"{'='*70}")
    print(f"Query 1 (support): {t1:.2f}s")
    print(f"Query 2 (support, cached): {t2:.2f}s (improvement: {(1-t2/t1)*100:.1f}%)")
    print(f"Query 3 (software): {t3:.2f}s")
    print(f"Average: {(t1+t2+t3)/3:.2f}s")
    print(f"\n✅ Test complete")
