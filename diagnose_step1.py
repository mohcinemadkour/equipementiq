import json

with open('evaluation/golden_set.jsonl') as f:
    entries = [json.loads(l) for l in f if l.strip()]

print(f'Total entries: {len(entries)}')
print(f'First entry keys: {list(entries[0].keys())}')
print(f'First entry agent: {entries[0]["agent"]}')
print(f'First entry expected_doc_ids: {entries[0]["expected_doc_ids"]}')
