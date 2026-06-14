#!/usr/bin/env python3
import sys
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from orchestrator import run_query

queries = {
    "COMPLAINT_QUERIES": [
        "what are all complaints related to AXS-SR-001?",
        "what complaints have been reported for SPN-MJ-004?",
        "show me all cases involving error code VIB-WN-002",
        "have customers reported CLS-MD-005?",
        "were there any incidents with TCS-CR-001?",
        "what is the history of error code HYD-SR-003?",
    ],
    "ERROR_DEFINITION_QUERIES": [
        "what does SPN-CR-001 mean?",
        "explain error code AXS-SR-001",
        "define the error VIB-MJ-001",
        "what is HYD-MD-002?",
        "tell me about error ELC-WN-004",
    ],
    "FILTERED_COMPLAINT_QUERIES": [
        "have customers reported issues with AXS-SR-001 on M02?",
        "what complaints involved spindle bearing faults on M01?",
        "show me tool wear issues reported on M03",
        "were there any critical severity errors on machine M02?",
        "list all complaints about vibration on M01",
    ],
    "MIXED_INTENT_QUERIES": [
        "I'm getting error SPN-CR-001, what should I do?",
        "has anyone else experienced error AXS-SR-001?",
        "CLS-MD-005 keeps appearing—what does it mean and have others seen it?",
        "are there any known issues with actuators?",
    ],
    "EDGE_CASE_QUERIES": [
        "what are all complaints?",
        "anything related to tool wear?",
        "which errors are critical?",
        "what's been happening on our machines?"
    ],
}

all_queries = [(cat, q) for cat, qs in queries.items() for q in qs]
results = []

print(f"Running {len(all_queries)} queries...\n")

for idx, (category, question) in enumerate(all_queries, 1):
    print(f"[{idx:2d}/{len(all_queries)}] {question[:60]:<60s}", end=" ", flush=True)
    try:
        result = run_query(question)
        domain = result.get("domain", "unknown")
        confidence = result.get("confidence", 0.0)
        answer = result.get("final_answer", "")[:200]
        
        results.append({
            "question": question,
            "domain": domain,
            "confidence": f"{confidence:.2f}",
            "answer_preview": answer.replace("\n", " ")[:100]
        })
        print(f"v {domain:12s} ({confidence:.2f})")
    except Exception as e:
        print(f"x ERROR")

# Write CSV
with open("test_results.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["question", "domain", "confidence", "answer_preview"])
    writer.writeheader()
    writer.writerows(results)

print(f"\nv Results written to test_results.csv")

# Print summary
domain_counts = {}
for r in results:
    d = r['domain']
    domain_counts[d] = domain_counts.get(d, 0) + 1

print(f"\nDomain Summary:")
for d, count in sorted(domain_counts.items()):
    print(f"  {d:<20} {count:3d} queries")
