#!/usr/bin/env python
"""Quick verification of SPN-MJ-004 fix"""

from dotenv import load_dotenv
load_dotenv()

from orchestrator.graph import run_query

print("Testing: 'What is the probable cause of error SPN-MJ-004?'")
result = run_query("What is the probable cause of error SPN-MJ-004?")

print(f"\nDomain: {result['domain']}")
print(f"Citations: {len(result.get('citations', []))}")

if result.get('citations'):
    print("\nCitations found:")
    for c in result['citations']:
        print(f"  - {c.get('source_document')}")
    
    has_spn = any('SPN-MJ-004' in str(c.get('source_document', '')) for c in result['citations'])
    print(f"\n✓ SPN-MJ-004 found: {has_spn}")
else:
    print("\n✗ No citations found")

print(f"\nAnswer (first 200 chars): {result['final_answer'][:200]}")
