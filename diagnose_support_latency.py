"""
Diagnose support agent latency for query: "Show me complaint case CMP-2019-1000"
Captures node-by-node execution times and identifies bottleneck.
"""

import time
from orchestrator.graph import run_query

def diagnose_latency():
    query = "Show me complaint case CMP-2019-1000"
    
    print(f"Running query: {query!r}")
    print(f"Started at: {time.strftime('%H:%M:%S')}")
    print("-" * 80)
    
    start_total = time.time()
    result = run_query(query)
    total_time = time.time() - start_total
    
    print(f"Total execution time: {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
    print()
    
    # Extract node latencies
    node_latencies = result.get("node_latency", {})
    
    if not node_latencies:
        print("❌ No node latency data captured")
        return
    
    print("=" * 80)
    print("NODE-BY-NODE LATENCY BREAKDOWN")
    print("=" * 80)
    
    # Sort by latency descending to show bottlenecks first
    sorted_nodes = sorted(node_latencies.items(), key=lambda x: x[1], reverse=True)
    
    cumulative = 0
    for node_name, latency_seconds in sorted_nodes:
        cumulative += latency_seconds
        percent = (latency_seconds / total_time) * 100 if total_time > 0 else 0
        
        # Visual bar chart
        bar_width = int(percent / 2)  # Scale to ~50 chars max
        bar = "█" * bar_width
        
        print(f"{node_name:20s} | {latency_seconds:7.3f}s | {percent:5.1f}% | {bar}")
    
    print("-" * 80)
    print(f"{'TOTAL':20s} | {total_time:7.3f}s | 100.0%")
    print()
    
    # Identify the worst offender
    if sorted_nodes:
        worst_node, worst_time = sorted_nodes[0]
        worst_pct = (worst_time / total_time) * 100
        print(f"⚠️  BOTTLENECK: '{worst_node}' consuming {worst_time:.2f}s ({worst_pct:.1f}% of total)")
        print()
    
    # Show routing info
    print("=" * 80)
    print("ROUTING INFORMATION")
    print("=" * 80)
    print(f"Domain:       {result.get('domain', 'unknown')}")
    print(f"Confidence:   {result.get('confidence', 0):.2%}")
    print(f"Answer length: {len(result.get('final_answer', ''))} chars")
    print(f"Citation count: {len(result.get('citations', []))}")
    print()
    
    # Show which agents were used
    print("=" * 80)
    print("AGENTS USED")
    print("=" * 80)
    agent_results = result.get("agent_results", {})
    for agent_name, agent_result in agent_results.items():
        status = agent_result.get("status", "unknown")
        chunks_count = len(agent_result.get("chunks", []))
        print(f"{agent_name:20s} | Status: {status:12s} | Chunks: {chunks_count}")
    print()
    
    # Provide recommendations
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    if worst_node == "synthesise":
        print("❌ LLM synthesis is the bottleneck (likely Claude API latency)")
        print("   → Check Claude API response times")
        print("   → Consider caching synthesized answers")
        print("   → Use faster model or adjust max_tokens")
    elif worst_node == "support_node":
        print("❌ Support agent retrieval is the bottleneck")
        print("   → Check support_collection size and indexing")
        print("   → Profile ChromaDB query performance")
        print("   → Consider adding caching layer")
    elif worst_node == "mechanical_node" or worst_node == "software_node":
        print("❌ Agent retrieval is the bottleneck")
        print("   → Check collection size and ChromaDB indexing")
        print("   → Profile embedding generation time")
    elif worst_node == "parallel_node":
        print("❌ Cross-domain parallel retrieval is slow")
        print("   → Implement true async retrieval")
        print("   → Cache frequently used queries")
    elif worst_node == "classify_intent":
        print("❌ Intent classification is slow")
        print("   → Check Claude API performance")
        print("   → Optimize intent classifier prompt")
    elif worst_node == "merge_context":
        print("❌ Context merging is slow")
        print("   → Too many chunks being processed")
        print("   → Optimize deduplication logic")

if __name__ == "__main__":
    diagnose_latency()
