#!/usr/bin/env python
"""
Comprehensive 80-query domain validation test.
Tests all 4 domains (mechanical, software, support, cross_domain) with 20 queries each.
Generates Section B domain breakdown table with scores.
"""

from dotenv import load_dotenv
load_dotenv()

from orchestrator.graph import run_query
import json
from datetime import datetime

# ============================================================================
# DOMAIN QUERIES: 20 per domain (80 total)
# ============================================================================

MECHANICAL_QUERIES = [
    "What vibration frequencies indicate spindle bearing wear?",
    "How do I diagnose a spindle bearing fault?",
    "What are typical tool wear patterns in milling?",
    "How do I check the spindle runout on a VMC?",
    "What causes intermittent vibration during roughing?",
    "How do I adjust the spindle speed for chatter reduction?",
    "What preventive maintenance is required for linear guides?",
    "How do I detect backlash in the X-axis?",
    "What cooling fluid pressure is optimal for the spindle?",
    "How do I balance a worn tool in the spindle?",
    "What thermal expansion considerations apply to precision setups?",
    "How do I align the spindle to the table surface?",
    "What lubrication schedule applies to ball screws?",
    "How do I measure spindle taper concentricity?",
    "What drive belt tension is correct for the spindle?",
    "How do I diagnose poor surface finish in finishing passes?",
    "What are signs of imminent spindle bearing failure?",
    "How do I perform spindle runout compensation?",
    "What feed rate limits apply for hardened steel?",
    "How do I calibrate tool length offset on a VMC?",
]

SOFTWARE_QUERIES = [
    "What does error SPN-CR-001 mean?",
    "What is the probable cause of error SPN-MJ-004?",
    "How many severity levels does the error code system have?",
    "What action does a WARNING severity error require?",
    "What does error AXS-CR-001 indicate?",
    "What is the required action for error code THM-CR-001?",
    "Which error codes are related to SPN-MJ-002?",
    "What does error CLS-CR-001 mean and when is it triggered?",
    "What does error ELC-CR-001 indicate?",
    "What does a NOTICE severity error require the operator to do?",
    "What error code fires when the ATC arm collides?",
    "What does CRITICAL severity mean in error codes?",
    "How do I resolve error VIB-SR-001?",
    "What is the relationship between SPN error codes and spindle speed?",
    "When should I contact support for a MAJOR error?",
    "What does TCS-CR-001 indicate about the tool changer?",
    "How do I clear a SERIOUS severity error?",
    "What HYD error codes indicate hydraulic system problems?",
    "How do I distinguish between MAJOR and SERIOUS errors?",
    "What CNC errors are reportable to Bosch maintenance?",
]

SUPPORT_QUERIES = [
    "What should I do if my spindle is vibrating excessively?",
    "How do I submit a maintenance request for the VMC-3000?",
    "What is the response time for critical equipment failures?",
    "How do I report a surface finish problem to support?",
    "What documentation do I need for a warranty claim?",
    "How do I schedule preventive maintenance with Bosch?",
    "What is the typical turnaround time for parts replacement?",
    "Can you help me troubleshoot poor tool life?",
    "How do I get training on the new spindle firmware?",
    "What spare parts should I stock for the VMC-3000?",
    "How do I access the remote diagnostics portal?",
    "What is included in the extended warranty?",
    "Can I upgrade the coolant system myself?",
    "How do I report a safety concern with the machine?",
    "What is the process for emergency service calls?",
    "How do I get replacement chips and coolant from Bosch?",
    "What is the typical maintenance cost per year?",
    "Can you recommend a local service partner?",
    "How do I extend the bed life of my VMC?",
    "What is the SLA for critical issues?",
]

CROSS_DOMAIN_QUERIES = [
    "My spindle is vibrating and I'm seeing SPN-CR-001 errors. What should I do?",
    "The tool changer is slow. Is this related to TCS errors or a mechanical issue?",
    "I need to know both the error code meaning and the maintenance procedure for bearing problems.",
    "What preventive maintenance steps will help avoid SPN-MJ-004 errors?",
    "The machine shows CRITICAL errors and I need both error details and emergency support contact.",
    "Is the thermal drift I'm seeing a vibration issue or an electrical error?",
    "I want to understand spindle bearing faults from both error code and mechanical perspectives.",
    "The ATC arm collision triggered TCS-CR-001. What's the mechanical cause and error recovery?",
    "Can coolant issues cause both HYD errors and mechanical spindle problems?",
    "I need mechanical specifications plus error code definitions for the hydraulic system.",
    "What's the relationship between tool wear patterns and error codes?",
    "The machine displays both vibration warnings and CNC errors. How are they related?",
    "I need both the technical specification and the support contact for alignment issues.",
    "Are feed rate limitations related to error thresholds?",
    "How do spindle speed errors map to mechanical spindle bearing wear?",
    "I need calibration procedures plus relevant error codes for this setup.",
    "What's the connection between surface finish errors and mechanical causes?",
    "The diagnostics show multiple domain failures. Where should I start?",
    "I need error remediation steps plus mechanical inspection procedures.",
    "Can you explain both the code meaning and how to verify the mechanical fix?",
]

# ============================================================================
# TEST EXECUTION
# ============================================================================

def run_domain_validation():
    """Run all 80 queries and collect metrics by domain."""
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "mechanical": {"queries": [], "stats": {}},
        "software": {"queries": [], "stats": {}},
        "support": {"queries": [], "stats": {}},
        "cross_domain": {"queries": [], "stats": {}},
    }
    
    all_queries = [
        ("mechanical", MECHANICAL_QUERIES),
        ("software", SOFTWARE_QUERIES),
        ("support", SUPPORT_QUERIES),
        ("cross_domain", CROSS_DOMAIN_QUERIES),
    ]
    
    total = sum(len(queries) for _, queries in all_queries)
    count = 0
    
    print("=" * 120)
    print(f"COMPREHENSIVE 80-QUERY DOMAIN VALIDATION TEST — POST-FIX BASELINE")
    print("=" * 120)
    print()
    
    for domain, queries in all_queries:
        print(f"\n{'='*120}")
        print(f"DOMAIN: {domain.upper()} ({len(queries)} queries)")
        print(f"{'='*120}\n")
        
        domain_results = results[domain]
        
        for idx, query in enumerate(queries, 1):
            count += 1
            print(f"[{count:2d}/{total}] {domain.ljust(15)} | Q{idx:2d} | ", end="", flush=True)
            
            try:
                result = run_query(query)
                
                routed_domain = result.get("domain", "unknown")
                confidence = result.get("confidence", 0)
                citations = len(result.get("citations", []))
                has_answer = bool(result.get("final_answer", "").strip())
                
                # Determine if routed correctly
                correct_routing = routed_domain == domain or (
                    domain == "cross_domain" and routed_domain in ["mechanical", "software", "support"]
                )
                
                query_result = {
                    "query": query,
                    "routed_domain": routed_domain,
                    "confidence": confidence,
                    "citations": citations,
                    "has_answer": has_answer,
                    "routing_correct": correct_routing,
                }
                
                domain_results["queries"].append(query_result)
                
                status = "✓" if correct_routing and citations > 0 else "✗"
                print(f"{status} routed={routed_domain} conf={confidence:.2f} cites={citations}")
                
            except Exception as e:
                print(f"✗ ERROR: {str(e)[:60]}")
                domain_results["queries"].append({
                    "query": query,
                    "error": str(e),
                    "routing_correct": False,
                })
    
    # ========================================================================
    # CALCULATE STATISTICS
    # ========================================================================
    
    print("\n" + "="*120)
    print("SECTION B: DOMAIN BREAKDOWN TABLE WITH SCORES")
    print("="*120 + "\n")
    
    for domain in ["mechanical", "software", "support", "cross_domain"]:
        queries = results[domain]["queries"]
        
        if queries:
            total_q = len(queries)
            routed_correctly = sum(1 for q in queries if q.get("routing_correct"))
            avg_confidence = sum(q.get("confidence", 0) for q in queries if "confidence" in q) / total_q if total_q else 0
            avg_citations = sum(q.get("citations", 0) for q in queries if "citations" in q) / total_q if total_q else 0
            has_answer_count = sum(1 for q in queries if q.get("has_answer"))
            
            routing_accuracy = (routed_correctly / total_q * 100) if total_q else 0
            answer_rate = (has_answer_count / total_q * 100) if total_q else 0
            avg_citations_rounded = round(avg_citations, 2)
            
            results[domain]["stats"] = {
                "total_queries": total_q,
                "routed_correctly": routed_correctly,
                "routing_accuracy_pct": routing_accuracy,
                "avg_confidence": round(avg_confidence, 3),
                "avg_citations": avg_citations_rounded,
                "answer_rate_pct": answer_rate,
            }
    
    # Build and display table
    table_data = []
    for domain in ["mechanical", "software", "support", "cross_domain"]:
        stats = results[domain]["stats"]
        table_data.append({
            "domain": domain.upper(),
            "queries": stats.get("total_queries", 0),
            "routed_ok": stats.get("routed_correctly", 0),
            "routing_acc": f"{stats.get('routing_accuracy_pct', 0):.1f}%",
            "confidence": f"{stats.get('avg_confidence', 0):.3f}",
            "citations": f"{stats.get('avg_citations', 0):.2f}",
            "answer_rate": f"{stats.get('answer_rate_pct', 0):.1f}%",
        })
    
    # Print formatted table
    print(f"{'DOMAIN':<20} {'QUERIES':<10} {'ROUTED OK':<12} {'ROUTING ACC':<15} {'AVG CONF':<12} {'AVG CITES':<12} {'ANSWER RATE':<15}")
    print("-" * 120)
    
    for row in table_data:
        print(f"{row['domain']:<20} {row['queries']:<10} {row['routed_ok']:<12} {row['routing_acc']:<15} {row['confidence']:<12} {row['citations']:<12} {row['answer_rate']:<15}")
    
    # Summary statistics
    print("\n" + "-" * 120)
    total_all = sum(stats.get("total_queries", 0) for stats in [results[d]["stats"] for d in results])
    total_routed = sum(stats.get("routed_correctly", 0) for stats in [results[d]["stats"] for d in results])
    overall_routing = (total_routed / total_all * 100) if total_all else 0
    
    print(f"{'TOTAL':<20} {total_all:<10} {total_routed:<12} {overall_routing:.1f}%")
    print("-" * 120)
    
    # ========================================================================
    # SAVE RESULTS
    # ========================================================================
    
    results_file = "evaluation/results/domain_validation_80_baseline.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to {results_file}")
    
    # Print summary
    print("\n" + "="*120)
    print("SUMMARY")
    print("="*120)
    print(f"Total queries tested: {total_all}")
    print(f"Correctly routed: {total_routed}/{total_all} ({overall_routing:.1f}%)")
    print(f"Overall average confidence: {sum(stats.get('avg_confidence', 0) for stats in [results[d]['stats'] for d in results]) / 4:.3f}")
    print(f"Overall average citations: {sum(stats.get('avg_citations', 0) for stats in [results[d]['stats'] for d in results]) / 4:.2f}")
    
    return results

if __name__ == "__main__":
    run_domain_validation()
