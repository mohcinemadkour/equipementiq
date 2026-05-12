#!/usr/bin/env python3
"""Verify 9 software queries after routing fix."""

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

print("=" * 100)
print("VERIFYING 9 SOFTWARE QUERIES (INSUFFICIENT_CONTEXT CHECK)")
print("=" * 100)

passed = 0
failed = 0

for q in queries:
    r = run_query(q)
    answer = r.get('final_answer', '')[:80]
    insufficient = 'INSUFFICIENT' in answer
    status = '[EMPTY]' if insufficient else '[OK]'
    if not insufficient:
        passed += 1
    else:
        failed += 1
    
    print(f'\n{status} [{r.get("domain","unknown"):10}] {q}')
    print(f'    Confidence: {r.get("confidence", 0):.2f}')
    print(f'    Answer preview: {answer}...')
    
    # Show chunk IDs and similarity if available
    chunk_ids = r.get('chunk_ids', [])
    if chunk_ids:
        print(f'    Retrieved chunks: {len(chunk_ids)} chunks')
        for cid in chunk_ids[:3]:
            print(f'      - {cid}')
    else:
        print(f'    Retrieved chunks: NONE')
    
    citations = r.get('citations', [])
    print(f'    Citations: {len(citations)}')

print("\n" + "=" * 100)
print(f'RESULT: {passed}/9 OK, {failed}/9 INSUFFICIENT_CONTEXT')
print("=" * 100)
