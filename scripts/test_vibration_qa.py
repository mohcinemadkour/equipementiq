#!/usr/bin/env python3
"""
Test 20 vibration Q&A pairs against mechanical agent.
Validates DOC-EIQ-005 (vibration monitoring) indexing and retrieval.
"""

import sys
from pathlib import Path

# Add workspace root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from orchestrator.graph import run_query
import json

QA_PAIRS = [
    # Section 2 — ISO 10816-3
    {
        "query": "What standard is used to classify vibration severity in the VMC-3000?",
        "expected_domain": "mechanical",
        "expected_terms": ["ISO 10816-3", "10816"]
    },
    {
        "query": "Which ISO 10816-3 group does the VMC-3000 spindle belong to?",
        "expected_domain": "mechanical",
        "expected_terms": ["Group 2", "flexible"]
    },
    {
        "query": "What RMS range defines Zone D and what action is required?",
        "expected_domain": "mechanical",
        "expected_terms": ["11.2", "emergency", "stop"]
    },
    {
        "query": "What error codes are triggered in Zone C?",
        "expected_domain": "mechanical",
        "expected_terms": ["VIB-MJ-001", "SPN-MJ-002"]
    },
    {
        "query": "What distinguishes Zone B from Zone B Upper?",
        "expected_domain": "mechanical",
        "expected_terms": ["2.3", "4.5", "7.1"]
    },
    
    # Section 3 — Statistical Features
    {
        "query": "How many statistical features are extracted per axis per operation cycle?",
        "expected_domain": "mechanical",
        "expected_terms": ["eight", "8"]
    },
    {
        "query": "Which feature is described as the best early-fault indicator?",
        "expected_domain": "mechanical",
        "expected_terms": ["kurtosis", "Kurtosis"]
    },
    {
        "query": "At what Kurtosis value does the system escalate from Warning to Alarm?",
        "expected_domain": "mechanical",
        "expected_terms": ["5.0", "8.0"]
    },
    {
        "query": "What formula is used to calculate Crest Factor?",
        "expected_domain": "mechanical",
        "expected_terms": ["peak", "rms", "x_peak", "x_rms"]
    },
    {
        "query": "What is the purpose of the Mean feature in vibration analysis?",
        "expected_domain": "mechanical",
        "expected_terms": ["DC offset", "static load", "cross-check"]
    },
    
    # Section 4 — Fault Category Signatures
    {
        "query": "Which fault category is associated with periodic peaks at tooth-pass frequency?",
        "expected_domain": "mechanical",
        "expected_terms": ["chatter", "chatter_vibration", "tooth"]
    },
    {
        "query": "What parameter values characterize a spindle bearing fault?",
        "expected_domain": "mechanical",
        "expected_terms": ["crest", "kurtosis", "Kurtosis"]
    },
    {
        "query": "Which operations are most affected by tool wear faults?",
        "expected_domain": "mechanical",
        "expected_terms": ["OP01", "OP02", "OP07"]
    },
    {
        "query": "What indicates an actuator fault in the VMC-3000?",
        "expected_domain": "mechanical",
        "expected_terms": ["following error", "0.5 mm", "servo"]
    },
    {
        "query": "What parameter deviation signals a process anomaly?",
        "expected_domain": "mechanical",
        "expected_terms": ["50 RPM", "override", "speed deviation"]
    },
    
    # Section 5 & 6 — Parameters and Error Codes
    {
        "query": "What is the normal range for Kurtosis Index P064?",
        "expected_domain": "mechanical",
        "expected_terms": ["2.5", "5.0"]
    },
    {
        "query": "What action does error code VIB-SR-001 require?",
        "expected_domain": "software",
        "expected_terms": ["cycle", "stop", "Zone B", "maintenance"]
    },
    {
        "query": "What is the critical range for Spindle Bearing Vibration P004?",
        "expected_domain": "mechanical",
        "expected_terms": ["11.2", "mm/s"]
    },
    
    # Section 7 — Dataset Reference
    {
        "query": "How many total HDF5 recordings are in the Bosch CNC Machining Dataset?",
        "expected_domain": "mechanical",
        "expected_terms": ["1,702", "1702"]
    },
    {
        "query": "What is the breakdown of normal vs fault samples in the Bosch dataset?",
        "expected_domain": "mechanical",
        "expected_terms": ["1,632", "70", "95.9", "4.1"]
    },
]

def check_terms(answer_text, expected_terms):
    """Check if any expected term appears in answer (case-insensitive)."""
    answer_lower = answer_text.lower()
    found_terms = []
    for term in expected_terms:
        if term.lower() in answer_lower:
            found_terms.append(term)
    return found_terms

def run_tests():
    """Run all 20 Q&A pair tests."""
    print("=" * 140)
    print("VIBRATION Q&A TEST SUITE — 20 queries against DOC-EIQ-005")
    print("=" * 140)
    print()
    
    results = []
    
    for idx, qa in enumerate(QA_PAIRS, start=1):
        query = qa["query"]
        expected_domain = qa["expected_domain"]
        expected_terms = qa["expected_terms"]
        
        print(f"[Query {idx}] {query[:70]}...")
        
        try:
            # Run through orchestrator
            response = run_query(query)
            
            actual_domain = response.get("domain", "unknown")
            confidence = response.get("confidence", 0)
            answer = response.get("final_answer", "")
            citations = response.get("citations", [])
            
            # Check domain routing
            domain_match = actual_domain == expected_domain
            
            # Check expected terms in answer
            found_terms = check_terms(answer, expected_terms)
            terms_match = len(found_terms) > 0
            
            # Determine pass/fail
            overall_pass = domain_match and terms_match
            
            result = {
                "idx": idx,
                "query": query,
                "expected_domain": expected_domain,
                "actual_domain": actual_domain,
                "domain_match": domain_match,
                "confidence": confidence,
                "expected_terms": expected_terms,
                "found_terms": found_terms,
                "terms_match": terms_match,
                "answer": answer[:300],  # First 300 chars
                "full_answer": answer,
                "citations": citations,
                "overall_pass": overall_pass,
            }
            results.append(result)
            
            # Print quick status
            domain_status = "✓" if domain_match else "✗"
            terms_status = "✓" if terms_match else "✗"
            overall_status = "PASS" if overall_pass else "FAIL"
            print(f"  Domain: {domain_status} {actual_domain} ({confidence:.0%})")
            print(f"  Terms:  {terms_status} Found: {found_terms if found_terms else '(none)'}")
            print(f"  Status: {overall_status}")
            print()
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            result = {
                "idx": idx,
                "query": query,
                "expected_domain": expected_domain,
                "actual_domain": "ERROR",
                "domain_match": False,
                "confidence": 0,
                "expected_terms": expected_terms,
                "found_terms": [],
                "terms_match": False,
                "answer": f"ERROR: {str(e)[:300]}",
                "full_answer": f"ERROR: {str(e)}",
                "citations": [],
                "overall_pass": False,
            }
            results.append(result)
            print()
    
    # ========== STEP 2: SUMMARY TABLE ==========
    print("\n" + "=" * 140)
    print("STEP 2: SUMMARY TABLE")
    print("=" * 140)
    print()
    print(f"{'#':<3} {'Query':<50} {'Domain':<15} {'Terms':<15} {'Overall':<10}")
    print("-" * 140)
    
    for r in results:
        domain_indicator = "✓ PASS" if r["domain_match"] else "✗ FAIL"
        terms_indicator = "✓ PASS" if r["terms_match"] else "✗ FAIL"
        overall_indicator = "PASS" if r["overall_pass"] else "FAIL"
        
        query_short = r["query"][:45] + "..." if len(r["query"]) > 45 else r["query"]
        print(f"{r['idx']:<3} {query_short:<50} {domain_indicator:<15} {terms_indicator:<15} {overall_indicator:<10}")
    
    # ========== STEP 3: FAILURE ANALYSIS ==========
    failures = [r for r in results if not r["overall_pass"]]
    
    if failures:
        print("\n" + "=" * 140)
        print(f"STEP 3: FAILURE ANALYSIS ({len(failures)} failing queries)")
        print("=" * 140)
        print()
        
        for r in failures:
            print(f"\n[Query {r['idx']}] {r['query']}")
            print("-" * 140)
            
            # Failure type analysis
            if not r["domain_match"]:
                print(f"❌ ROUTING ISSUE: Expected '{r['expected_domain']}' but got '{r['actual_domain']}'")
            
            if not r["terms_match"]:
                print(f"❌ TERMS ISSUE: Expected any of {r['expected_terms']} but found {r['found_terms']}")
            
            print(f"\nConfidence: {r['confidence']:.0%}")
            print(f"\nAnswer (first 300 chars):\n{r['answer']}\n...")
            print(f"\nFull Answer:\n{r['full_answer']}")
            print(f"\nCitations: {r['citations']}")
            
            # Determine issue type
            if not r["domain_match"]:
                issue_type = "ROUTING ISSUE"
            elif len(r["citations"]) == 0:
                issue_type = "RETRIEVAL ISSUE (no chunks retrieved)"
            else:
                # Check if citations include vibration docs
                has_vib_doc = any("DOC-EIQ-005" in str(c) or "Vibration" in str(c) for c in r["citations"])
                if not has_vib_doc:
                    issue_type = "RETRIEVAL ISSUE (wrong source docs)"
                else:
                    issue_type = "SYNTHESIS ISSUE (retrieved but not synthesized correctly)"
            
            print(f"\nIssue Type: {issue_type}")
            print()
    
    # ========== STEP 4: FINAL SUMMARY ==========
    print("\n" + "=" * 140)
    print("STEP 4: FINAL SUMMARY")
    print("=" * 140)
    print()
    
    total = len(results)
    passes = len([r for r in results if r["overall_pass"]])
    fails = total - passes
    
    print(f"Total Queries: {total}")
    print(f"PASS: {passes} ({passes/total*100:.1f}%)")
    print(f"FAIL: {fails} ({fails/total*100:.1f}%)")
    print()
    
    if fails > 0:
        print("Failing Queries:")
        print("-" * 140)
        for r in failures:
            # Categorize failure type
            if not r["domain_match"]:
                category = "ROUTING"
            elif len(r["citations"]) == 0:
                category = "RETRIEVAL (empty)"
            elif not r["terms_match"] and r["actual_domain"] == r["expected_domain"]:
                has_vib_doc = any("DOC-EIQ-005" in str(c) for c in r["citations"])
                category = "SYNTHESIS" if has_vib_doc else "RETRIEVAL (wrong sources)"
            else:
                category = "UNKNOWN"
            
            print(f"  [{r['idx']}] {r['query'][:60]}... → {category}")
            
            # Recommendation
            if category == "ROUTING":
                print(f"        FIX: Update intent_classification.txt prompt to route '{r['query'][:30]}...' to {r['expected_domain']}")
            elif category == "RETRIEVAL (empty)":
                print(f"        FIX: Check if DOC-EIQ-005 was ingested; re-run ingest_mechanical.py if needed")
            elif category == "RETRIEVAL (wrong sources)":
                print(f"        FIX: Add golden set entry to enforce retrieval from DOC-EIQ-005")
            elif category == "SYNTHESIS":
                print(f"        FIX: Update synthesis.txt prompt to extract '{r['expected_terms'][0]}' from retrieved chunks")
    
    print()
    print("=" * 140)


if __name__ == "__main__":
    run_tests()
