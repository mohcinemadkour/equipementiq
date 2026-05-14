import json
file_path = r'evaluation\golden_set.jsonl'
errors = []
with open(file_path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if not line.strip(): continue
        try:
            json.loads(line)
        except Exception as e:
            errors.append(f"Line {i}: {e}")
if errors:
    print("\n".join(errors))
else:
    print("All lines are valid JSON.")
