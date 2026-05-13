#!/usr/bin/env python
"""Test Tier 2: 9 failing software queries - detailed analysis"""

from dotenv import load_dotenv
load_dotenv()

from orchestrator.graph import run_query

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

results = []
for idx, q in enumerate(queries, 1):
    r = run_query(q)
    insufficient = 'INSUFFICIENT' in r['final_answer']
    status = 'FAIL' if insufficient else 'PASS'
    results.append({
        'query': q,
        'status': status,
        'domain': r['domain'],
        'confidence': r.get('confidence'),
        'chunks': r.get('chunk_ids', []),
        'citations': len(r.get('citations', []))
    })
    print(f"[{idx}] {status:4} | {q[:50]:50} | Citations: {len(r.get('citations', []))}")

print("\n" + "="*80)
print(f"SUMMARY: {sum(1 for r in results if r['status']=='PASS')}/{len(results)} queries passed")
print("="*80)
