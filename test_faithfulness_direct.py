#!/usr/bin/env python3
"""Test faithfulness_score directly without orchestrator."""

from dotenv import load_dotenv
load_dotenv()

from evaluation.generation_metrics import faithfulness_score

context = [
    'Spindle bearing catastrophic failure. Vibration P004 exceeds 11.2 mm/s. Machine must stop immediately.'
]

answer = 'SPN-CR-001 indicates spindle bearing failure where vibration exceeds the critical threshold.'

query = 'What does SPN-CR-001 mean?'

print('Testing faithfulness_score() with mock context...')
print(f'Query: {query}')
print(f'Context: {context}')
print(f'Answer: {answer}')
print()

score = faithfulness_score(query, context, answer)
print(f'Faithfulness Score: {score}')
print(f'Result: {"PASS" if score > 0.50 else "FAIL"} (score {score:.2f} vs threshold 0.50)')
