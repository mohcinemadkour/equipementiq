import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from orchestrator import run_query

queries = [
    "what are all complaints related to AXS-SR-001?",
    "what does AXS-SR-001 mean?",
    "have customers reported issues with AXS-SR-001 on M02?"
]

for i, query in enumerate(queries, 1):
    print(f"\n{'='*80}")
    print(f"QUERY {i}: {query}")
    print(f"{'='*80}\n")
    
    result = run_query(query)
    
    answer = result.get('final_answer', 'NO ANSWER')
    # Show just first 500 chars of answer
    if len(answer) > 500:
        print(answer[:500] + "\n[... truncated ...]")
    else:
        print(answer)
