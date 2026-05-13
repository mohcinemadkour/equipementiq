"""
Test the three optimizations with 4 queries.
Measures: total latency and classify_intent latency for each query.
"""

import time
from orchestrator.graph import run_query

def test_optimizations():
    queries = [
        "Show me complaint case CMP-2019-1000",
        "Show me complaint case CMP-2019-1000",  # Same query again (cached agents + results)
        "What does error SPN-CR-001 mean?",
        "What bearing type does the VMC-3000 spindle use?"
    ]
    
    print("=" * 100)
    print("TESTING THREE OPTIMIZATIONS")
    print("=" * 100)
    print()
    
    results = []
    
    for i, query in enumerate(queries, 1):
        print(f"Query {i}: {query!r}")
        print("-" * 100)
        
        start_total = time.time()
        result = run_query(query)
        total_time = time.time() - start_total
        
        # Extract metrics
        domain = result.get("domain", "unknown")
        confidence = result.get("confidence", 0.0)
        node_latencies = result.get("node_latency", {})
        classify_intent_time = node_latencies.get("classify_intent", 0.0)
        
        results.append({
            "query": query,
            "total_time": total_time,
            "classify_intent_time": classify_intent_time,
            "domain": domain,
            "confidence": confidence
        })
        
        print(f"Total time:        {total_time:.3f}s")
        print(f"classify_intent:   {classify_intent_time:.3f}s {'✅ FAST (rule-based)' if classify_intent_time < 0.1 else '⚠️  SLOW (Claude API)'}")
        print(f"Domain:            {domain}")
        print(f"Confidence:        {confidence:.1%}")
        print()
    
    # Summary table
    print("=" * 100)
    print("SUMMARY TABLE")
    print("=" * 100)
    print()
    print(f"{'Query #':<8} {'Total (s)':<12} {'Classify (s)':<14} {'Rule-Based?':<15} {'Domain':<12} {'Status':<15}")
    print("-" * 100)
    
    for i, r in enumerate(results, 1):
        is_rule_based = "✅ YES" if r["classify_intent_time"] < 0.1 else "❌ NO (API)"
        
        # Status check
        if i <= 3:  # Queries 1-3 should be < 8s
            status = "✅ PASS" if r["total_time"] < 8.0 else f"❌ FAIL ({r['total_time']:.1f}s > 8s)"
        else:  # Query 4 should be < 12s
            status = "✅ PASS" if r["total_time"] < 12.0 else f"❌ FAIL ({r['total_time']:.1f}s > 12s)"
        
        print(f"{i:<8} {r['total_time']:<12.3f} {r['classify_intent_time']:<14.3f} {is_rule_based:<15} {r['domain']:<12} {status:<15}")
    
    print()
    
    # Performance targets
    print("=" * 100)
    print("PERFORMANCE TARGETS")
    print("=" * 100)
    print()
    
    targets = [
        ("Query 1 (CMP case)", 8.0),
        ("Query 2 (cached repeat)", 8.0),
        ("Query 3 (error code)", 8.0),
        ("Query 4 (general)", 12.0),
    ]
    
    all_pass = True
    for (name, target), result in zip(targets, results):
        actual = result["total_time"]
        passed = actual < target
        status = "✅ PASS" if passed else "❌ FAIL"
        all_pass = all_pass and passed
        print(f"{status} {name:<30} Target: {target:.1f}s  Actual: {actual:.3f}s")
    
    print()
    
    if all_pass:
        print("🎉 ALL PERFORMANCE TARGETS MET!")
    else:
        print("⚠️  SOME QUERIES DID NOT MEET PERFORMANCE TARGETS")
    
    print()
    
    # Rule-based fast-path validation
    print("=" * 100)
    print("RULE-BASED FAST-PATH VALIDATION")
    print("=" * 100)
    print()
    
    # Query 1: Should hit CMP rule
    if results[0]["classify_intent_time"] < 0.1:
        print("✅ Query 1 (CMP-2019-1000): Rule-based classification PASSED")
    else:
        print(f"❌ Query 1 (CMP-2019-1000): Expected < 0.1s, got {results[0]['classify_intent_time']:.3f}s")
    
    # Query 3: Should hit error code rule
    if results[2]["classify_intent_time"] < 0.1:
        print("✅ Query 3 (SPN-CR-001): Rule-based classification PASSED")
    else:
        print(f"❌ Query 3 (SPN-CR-001): Expected < 0.1s, got {results[2]['classify_intent_time']:.3f}s")
    
    print()
    
    return all_pass

if __name__ == "__main__":
    success = test_optimizations()
    exit(0 if success else 1)
