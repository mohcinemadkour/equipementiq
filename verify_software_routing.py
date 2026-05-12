#!/usr/bin/env python3
"""Verify software domain routing after prompt enhancement."""

from dotenv import load_dotenv
load_dotenv()

from orchestrator.graph import run_query

test_queries = [
    'What is the remedy for error TCS-MJ-001?',
    'What parameter P004 monitors and what is its critical limit?',
    'What is the normal range for parameter P002 spindle load?',
    'What is the MID number for the spindle drive subsystem?',
    'What parameter monitors hydraulic system pressure?',
    'How many severity levels does the EquipmentIQ error code system have?',
]

print("=" * 90)
print("VERIFYING SOFTWARE DOMAIN ROUTING")
print("=" * 90)

passed = 0
failed = 0

for q in test_queries:
    r = run_query(q)
    is_software = r['domain'] == 'software'
    status = '[PASS]' if is_software else '[FAIL]'
    if is_software:
        passed += 1
    else:
        failed += 1
    print(f'{status}  {r["domain"]:15} {r["confidence"]:.2f}  {q[:55]}')

print("=" * 90)
print(f'RESULT: {passed}/6 passed, {failed}/6 failed')
if passed == 6:
    print('[SUCCESS] All software routing tests PASSED!')
else:
    print(f'[WARNING] {failed} tests still failing')
print("=" * 90)
