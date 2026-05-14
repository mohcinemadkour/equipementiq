from dotenv import load_dotenv
load_dotenv()

import json
from orchestrator.graph import run_query

with open('evaluation/golden_set.jsonl') as f:
    entries = [json.loads(l) for l in f if l.strip()][:3]

for entry in entries:
    try:
        result = run_query(entry['query'])
        expected = entry['agent']
        actual = result.get('domain', 'MISSING')
        match = '✅' if actual == expected else '❌'
        print(f'{match} Expected: {expected:12} Got: {actual:12} Query: {entry["query"][:45]}')
        print(f'   Full result keys: {list(result.keys())}')
    except Exception as e:
        print(f'❌ ERROR: {str(e)[:80]}')
        print(f'   Query: {entry["query"][:45]}')
