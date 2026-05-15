"""
Test single evaluation query to debug faithfulness context passing.
"""

import sys
sys.path.insert(0, ".")

import json
from evaluation.generation_metrics import sample_and_evaluate

# Run evaluation on just 1 sample
print("\n" + "="*120)
print("RUNNING SINGLE QUERY EVALUATION (debugging faithfulness context passing)")
print("="*120 + "\n")

result = sample_and_evaluate(golden_path="evaluation/golden_set.jsonl", sample_rate=0.03)  # ~1 query

print("\n" + "="*120)
print("RESULT:")
print("="*120)
if result:
    for r in result:
        print(json.dumps(r, indent=2))
