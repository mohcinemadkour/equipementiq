"""
Full trace diagnostic for slow support query.
Shows: All node latencies, routing decision, token count for synthesis.
"""

import time
import json
from orchestrator.graph import run_query
from ingestion.config import load_config
from anthropic import Anthropic

def count_tokens(text: str, model: str = "claude-haiku-4-5-20251001") -> int:
    """Approximate token count using Anthropic's token counter."""
    try:
        client = Anthropic()
        # Use the token counter via the API
        response = client.messages.count_tokens(
            model=model,
            messages=[{"role": "user", "content": text}]
        )
        return response.input_tokens
    except Exception as e:
        # Fallback: rough estimate (1 token ≈ 4 chars)
        return len(text) // 4

def diagnose_full_trace():
    query = "Show me complaint case CMP-2019-1000"
    
    print("=" * 100)
    print("FULL QUERY TRACE DIAGNOSTIC")
    print("=" * 100)
    print(f"\nQuery: {query!r}")
    print(f"Started at: {time.strftime('%H:%M:%S')}")
    print()
    
    # Run the query
    start_total = time.time()
    result = run_query(query)
    total_time = time.time() - start_total
    
    print("=" * 100)
    print("1. ROUTING DECISION")
    print("=" * 100)
    domain = result.get("domain", "unknown")
    confidence = result.get("confidence", 0)
    print(f"Domain:              {domain}")
    print(f"Confidence:          {confidence:.1%}")
    
    if domain == "cross_domain":
        print("⚠️  ROUTED TO CROSS_DOMAIN - All 3 agents ran in parallel node!")
    elif domain == "support":
        print("✅ Routed to support (single agent)")
    else:
        print(f"✅ Routed to {domain}")
    print()
    
    # Extract node latencies
    node_latencies = result.get("node_latency", {})
    
    print("=" * 100)
    print("2. NODE-BY-NODE LATENCY BREAKDOWN")
    print("=" * 100)
    
    if not node_latencies:
        print("❌ No node latency data captured!")
        return
    
    # Sort by latency descending
    sorted_nodes = sorted(node_latencies.items(), key=lambda x: x[1], reverse=True)
    
    print(f"{'Node':<25} | {'Time (s)':>8} | {'% of Total':>10} | {'Visualization':<40}")
    print("-" * 100)
    
    cumulative = 0
    for node_name, latency_seconds in sorted_nodes:
        cumulative += latency_seconds
        percent = (latency_seconds / total_time) * 100 if total_time > 0 else 0
        bar_width = int(percent / 2)
        bar = "█" * bar_width
        
        print(f"{node_name:<25} | {latency_seconds:8.3f} | {percent:9.1f}% | {bar:<40}")
    
    print("-" * 100)
    print(f"{'TOTAL':<25} | {total_time:8.3f} | 100.0%")
    print()
    
    # Identify bottleneck
    if sorted_nodes:
        worst_node, worst_time = sorted_nodes[0]
        worst_pct = (worst_time / total_time) * 100
        print(f"⚠️  PRIMARY BOTTLENECK: '{worst_node}'")
        print(f"    Consuming {worst_time:.3f}s ({worst_pct:.1f}% of total {total_time:.1f}s)")
        print()
    
    # Analyze synthesis token count
    print("=" * 100)
    print("3. SYNTHESIS PROMPT TOKEN ANALYSIS")
    print("=" * 100)
    
    merged_context = result.get("merged_context", [])
    print(f"Merged context chunks: {len(merged_context)}")
    print()
    
    # Reconstruct the synthesis prompt
    context_str = "\n\n".join(
        f"[SOURCE: {c.get('source_document', 'UNKNOWN')} chunk {c.get('chunk_id', 'UNKNOWN')}]\n{c.get('text', '')}"
        for c in merged_context
    )
    
    history_str = "\n\n".join(
        f"Q: {turn.get('query', '')}\nA: {turn.get('answer', '')[:100]}..."
        for turn in result.get("conversation_history", [])[- 5:]
    )
    
    cfg = load_config()
    prompt_path = cfg["paths"]["prompts_dir"] + "/synthesis.txt"
    with open(prompt_path, "r") as f:
        prompt_template = f.read()
    
    try:
        full_prompt = prompt_template.format(
            merged_context=context_str,
            conversation_history=history_str,
            query=query
        )
    except Exception as e:
        print(f"⚠️  Error formatting prompt: {e}")
        full_prompt = f"Query: {query}\nContext: {context_str}"
    
    # Count tokens
    print(f"Query text:         {len(query)} chars")
    print(f"Context text:       {len(context_str)} chars")
    print(f"History text:       {len(history_str)} chars")
    print(f"Full prompt:        {len(full_prompt)} chars")
    print()
    
    # Use Anthropic's token counter
    token_count = count_tokens(full_prompt)
    print(f"🔢 Token count for synthesis prompt: {token_count} tokens")
    print()
    
    # Estimate synthesis time based on token count
    avg_tokens_per_second = 100  # Typical API throughput
    estimated_synthesis = token_count / avg_tokens_per_second
    actual_synthesis = node_latencies.get("synthesise", 0)
    
    print(f"Estimated synthesis time (100 tok/s): {estimated_synthesis:.1f}s")
    print(f"Actual synthesis time:                {actual_synthesis:.3f}s")
    print(f"Difference:                           {actual_synthesis - estimated_synthesis:.3f}s")
    print()
    
    # Show first 500 chars of full prompt
    print("=" * 100)
    print("4. SYNTHESIS PROMPT PREVIEW (first 500 chars)")
    print("=" * 100)
    print(full_prompt[:500])
    if len(full_prompt) > 500:
        print(f"\n... ({len(full_prompt) - 500} more characters)")
    print()
    
    # Final summary
    print("=" * 100)
    print("5. SUMMARY")
    print("=" * 100)
    print(f"Total query time:      {total_time:.1f}s")
    print(f"Domain routed:         {domain} (confidence {confidence:.0%})")
    print(f"Agents used:           {domain}")
    print(f"Synthesis tokens:      {token_count}")
    print(f"Merged chunks:         {len(merged_context)}")
    print(f"Context size:          {len(context_str)} chars")
    
    if total_time > 180:  # 3 minutes
        print(f"\n⚠️  QUERY TOOK {total_time/60:.1f} MINUTES - UNACCEPTABLE")
    elif total_time > 30:
        print(f"\n⚠️  Query took {total_time:.1f}s - slow but may be acceptable")
    else:
        print(f"\n✅ Query completed in {total_time:.1f}s")

if __name__ == "__main__":
    diagnose_full_trace()
