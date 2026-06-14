import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from orchestrator import run_query

query = "what are all complaints related to AXS-SR-001?"
print(f"Query: {query}\n")

result = run_query(query)

print(f"Domain: {result.get('domain')}")
print(f"Confidence: {result.get('confidence')}")
print(f"Agents used: {', '.join(result.get('agents_used', []))}")
print(f"\n{'='*80}")
print("ANSWER:")
print(f"{'='*80}\n")
print(result.get('final_answer', 'NO ANSWER'))
print(f"\n{'='*80}")
print(f"Total results: {len(result.get('citations', []))}")
