#!/usr/bin/env python3
"""Verify support domain routing issues from Tier 2."""

from dotenv import load_dotenv
load_dotenv()

from orchestrator.graph import run_query

# P10-P13: Connection errors, P06: cross_domain when should be support, P17: mechanical when should be support
test_queries = [
    ('P06', 'What investigation notes were recorded for chatter vibration cases?'),
    ('P10', 'Show me all open warranty claims on machines M01 and M02.'),
    ('P17', 'What sensor readings were recorded for spindle bearing fault cases in 2021?'),
]

print("=" * 100)
print("TIER 2 — SUPPORT DOMAIN ROUTING VERIFICATION")
print("=" * 100)

for qid, q in test_queries:
    print(f'\n[{qid}] {q}')
    
    try:
        r = run_query(q)
        print(f'    Domain: {r.get("domain", "unknown"):15} Confidence: {r.get("confidence", 0):.2f}')
        answer = r.get('final_answer', '')[:100]
        print(f'    Answer: {answer}...')
    except Exception as e:
        print(f'    ERROR: {str(e)[:100]}')

print("\n" + "=" * 100)
