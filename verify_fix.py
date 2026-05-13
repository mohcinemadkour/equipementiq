#!/usr/bin/env python
"""Verify error code metadata lookup fix in SoftwareAgent"""

from dotenv import load_dotenv
load_dotenv()

from orchestrator.graph import run_query

print("="*100)
print("VERIFICATION 1: Original Failing Query - 'What is the probable cause of error SPN-MJ-004?'")
print("="*100)

result1 = run_query("What is the probable cause of error SPN-MJ-004?")
print(f"\nDomain: {result1['domain']}")
print(f"Confidence: {result1.get('confidence')}")
print(f"Citations: {len(result1.get('citations', []))}")
print(f"Answer: {result1['final_answer'][:150]}...")

# Check if SPN-MJ-004 is in citations
citations_str = str(result1.get('citations', []))
has_spn_mj_004 = 'SPN-MJ-004' in citations_str
status1 = "✓ PASS" if has_spn_mj_004 else "✗ FAIL"
print(f"\n{status1} - SPN-MJ-004 in citations: {has_spn_mj_004}")
if result1.get('citations'):
    print(f"     Citations: {[c.get('source_document') for c in result1['citations'][:3]]}")

print("\n" + "="*100)
print("VERIFICATION 2a: 'What does error SPN-CR-001 mean?'")
print("="*100)

result2a = run_query("What does error SPN-CR-001 mean?")
print(f"\nDomain: {result2a['domain']}")
print(f"Citations: {len(result2a.get('citations', []))}")
status2a = "✓ PASS" if len(result2a.get('citations', [])) > 0 and 'SPN-CR-001' in str(result2a.get('citations', [])) else "✗ FAIL"
print(f"{status2a} - SPN-CR-001 in results")

print("\n" + "="*100)
print("VERIFICATION 2b: 'What action does AXS-CR-001 require?'")
print("="*100)

result2b = run_query("What action does AXS-CR-001 require?")
print(f"\nDomain: {result2b['domain']}")
print(f"Citations: {len(result2b.get('citations', []))}")
status2b = "✓ PASS" if len(result2b.get('citations', [])) > 0 and 'AXS-CR-001' in str(result2b.get('citations', [])) else "✗ FAIL"
print(f"{status2b} - AXS-CR-001 in results")

print("\n" + "="*100)
print("VERIFICATION 3: Running Full Tier 2 Test Suite")
print("="*100)

queries = [
    'What action does a WARNING severity error require?',
    'Which error codes are related to SPN-MJ-002?',
    'What does error CLS-CR-001 mean and when is it triggered?',
    'What does error ELC-CR-001 indicate?',
    'What is the probable cause of error SPN-MJ-004?',
    'How many severity levels does the error code system have?',
    'What error code fires when the ATC arm collides?',
    'What does a NOTICE severity error require the operator to do?',
    'What is the required action for error code THM-CR-001?',
]

passed = 0
failed = 0

for idx, q in enumerate(queries, 1):
    r = run_query(q)
    is_pass = len(r.get('citations', [])) > 0
    status = "PASS" if is_pass else "FAIL"
    if is_pass:
        passed += 1
    else:
        failed += 1
    print(f"[{idx}] {status:4} | {q[:60]:60} | Citations: {len(r.get('citations', []))}")

print("\n" + "="*100)
print(f"FINAL SUMMARY: {passed}/{len(queries)} queries passed")
print("="*100)

all_pass = (has_spn_mj_004 and status2a == "✓ PASS" and status2b == "✓ PASS" and passed == 9)
if all_pass:
    print("\n✓✓✓ ALL VERIFICATIONS PASSED ✓✓✓")
    print("Ready to commit!")
else:
    print("\n✗ Some verifications failed. Check results above.")
