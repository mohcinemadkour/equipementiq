"""
Auto-generate escalation_path for all error code documents with related_codes.
Applies systematically to all 96 error code JSON files.
"""

import json
import os
from pathlib import Path

error_docs_dir = Path("data/error_docs")

updated_count = 0
skipped_count = 0
samples = {}  # Collect samples from different subsystems

for filepath in sorted(error_docs_dir.glob("*.json")):
    with open(filepath) as f:
        doc = json.load(f)
    
    related = doc.get("related_codes", [])
    if not related:
        skipped_count += 1
        continue
    
    if "escalation_path" in doc:
        skipped_count += 1
        continue  # Already has escalation_path
    
    severity = doc.get("severity_level", "")
    code = doc.get("error_code", filepath.stem)
    title = doc.get("title", code)
    action = doc.get("required_action", "address immediately")
    
    # Build natural language escalation text from related_codes
    related_text = ", then ".join(related)
    escalation = (
        f"If {code} is not addressed ({action.lower()}), "
        f"the fault will escalate in this order: {related_text}. "
        f"Each subsequent code represents a more severe fault state "
        f"requiring more urgent intervention. Query each related code "
        f"for its specific thresholds and required actions."
    )
    
    doc["escalation_path"] = escalation
    
    with open(filepath, "w") as f:
        json.dump(doc, f, indent=2)
    
    updated_count += 1
    
    # Collect sample from each subsystem
    subsystem = code.split("-")[0]  # e.g., "SPN" from "SPN-SR-003"
    if subsystem not in samples:
        samples[subsystem] = {
            "code": code,
            "related": related,
            "escalation": escalation
        }
    
    print(f"✓ {code:15s} -> {related}")

print(f"\n{'='*100}")
print(f"SUMMARY:")
print(f"{'='*100}")
print(f"Updated: {updated_count} documents")
print(f"Skipped: {skipped_count} documents (already have escalation_path or no related_codes)")
print(f"Total:   {updated_count + skipped_count} documents")

print(f"\n{'='*100}")
print(f"SAMPLE ESCALATION PATHS (one per subsystem):")
print(f"{'='*100}\n")

for subsystem in sorted(samples.keys()):
    sample = samples[subsystem]
    print(f"📌 {subsystem} Subsystem — {sample['code']}:")
    print(f"   Related codes: {sample['related']}")
    print(f"   Escalation path:")
    print(f"   {sample['escalation']}")
    print()
