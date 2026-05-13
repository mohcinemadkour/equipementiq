#!/usr/bin/env python
"""Test Tier 2: 9 failing software queries after routing fix"""

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

print("=" * 80)
print("TIER 2 QUERY TEST: 9 Software Queries After Routing Fix")
print("=" * 80)

for idx, q in enumerate(queries, 1):
    print(f"\n[Query {idx}] {q}")
    print("-" * 80)
    
    r = run_query(q)
    answer = r['final_answer'][:100]
    insufficient = 'INSUFFICIENT' in answer
    status = '❌ EMPTY' if insufficient else '✅ OK'
    
    print(f"Status:    {status}")
    print(f"Domain:    {r['domain']}")
    print(f"Confidence: {r.get('confidence', 'N/A')}")
    print(f"Citations: {len(r.get('citations', []))}")
    print(f"Answer:    {answer}...")
    
    if insufficient:
        print(f"\n⚠️  INSUFFICIENT_CONTEXT DETECTED")
        if 'agent_results' in r and r['agent_results']:
            print(f"   Retrieved chunks: {len(r['agent_results'].get('results', []))}")
            if r['agent_results'].get('results'):
                for chunk in r['agent_results']['results'][:3]:
                    print(f"     - Chunk {chunk.get('chunk_id', 'N/A')}: {chunk.get('similarity_score', 'N/A'):.3f}")

print("\n" + "=" * 80)
print("END OF TIER 2 TEST")
print("=" * 80)
