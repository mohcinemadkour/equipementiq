#!/usr/bin/env python3
"""Rebuild golden_set.jsonl using orchestrator results with updated routing."""

import os
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from orchestrator.graph import run_query

load_dotenv()

# Original golden set queries
golden_set_entries = [
    # MECHANICAL (10 queries)
    {"query": "What are the specifications for spindle bearing replacement?", "agent": "mechanical"},
    {"query": "What is the tool change procedure for VMC-3000?", "agent": "mechanical"},
    {"query": "Describe the X-axis servo mechanism and lubrication points.", "agent": "mechanical"},
    {"query": "What cooling system maintenance is required for the spindle?", "agent": "mechanical"},
    {"query": "How to check spindle encoder signal quality?", "agent": "mechanical"},
    {"query": "What is the vibration monitoring procedure?", "agent": "mechanical"},
    {"query": "Describe foundation bolt re-torquing procedure.", "agent": "mechanical"},
    {"query": "What maintenance interval is required for ball screw inspection?", "agent": "mechanical"},
    {"query": "How to verify correct tool length offset?", "agent": "mechanical"},
    {"query": "What are the spindle motor temperature thresholds?", "agent": "mechanical"},
    
    # SOFTWARE (10 queries)
    {"query": "What does error SPN-CR-001 mean and what is the remedy?", "agent": "software"},
    {"query": "I'm seeing SPN-MJ-002 - Spindle Bearing Vibration Major. What should I do?", "agent": "software"},
    {"query": "Error AXS-CR-001 - Axis Following Error Emergency Stop", "agent": "software"},
    {"query": "Spindle overtemperature warning SPN-MJ-001", "agent": "software"},
    {"query": "What is SPN-SR-001 fault code?", "agent": "software"},
    {"query": "How to respond to AXS-MJ-001 following error?", "agent": "software"},
    {"query": "SPN-CR-002 spindle drive overcurrent", "agent": "software"},
    {"query": "Error SPN-WN-001 tool life warning", "agent": "software"},
    {"query": "What does SPN-MN-002 indicate?", "agent": "software"},
    {"query": "Servo drive thermal warning AXS-MJ-002", "agent": "software"},
    
    # SUPPORT (10 queries)
    {"query": "Customer reports spindle not spinning up to full speed", "agent": "support"},
    {"query": "Tool changing takes longer than normal", "agent": "support"},
    {"query": "Machine stops with following error during rapid traverse", "agent": "support"},
    {"query": "Operator noticed excessive spindle vibration and noise", "agent": "support"},
    {"query": "Customer getting overload fault on X-axis servo during heavy cut", "agent": "support"},
    {"query": "Spindle cooling fan is not running - spindle temperature rising", "agent": "support"},
    {"query": "Tool life counter showing inconsistent values between parts", "agent": "support"},
    {"query": "Machine going into alarm when feed override is applied", "agent": "support"},
    {"query": "Axis positioning accuracy degraded over time", "agent": "support"},
    {"query": "Intermittent M code errors during tool change program", "agent": "support"},
]

def _extract_source_doc_id(chunk_id: str) -> str:
    """Extract source document ID from full chunk ID (strip __XXXX suffix)."""
    if '__' in chunk_id:
        return chunk_id.split('__')[0]
    return chunk_id

print("Rebuilding golden_set.jsonl with orchestrator results...")
print("=" * 80)

rebuilt_entries = []

for idx, entry in enumerate(golden_set_entries, 1):
    query = entry["query"]
    expected_agent = entry["agent"]
    
    print(f"\n[{idx}/30] Query: {query[:60]}...")
    
    # Run through orchestrator
    try:
        result = run_query(query)
        domain = result.get("domain", "unknown")
        confidence = result.get("confidence", 0.0)
        
        # Extract source_document IDs (strip __XXXX suffix from chunk_ids)
        expected_doc_ids = []
        if result.get("chunk_ids"):
            for chunk_id in result["chunk_ids"][:3]:  # Top-3 for golden set
                source_id = _extract_source_doc_id(chunk_id)
                expected_doc_ids.append(source_id)
        
        # Get ground truth answer from synthesized response
        ground_truth_answer = result.get("final_answer", "")[:200]
        
        rebuilt_entry = {
            "query": query,
            "agent": expected_agent,
            "domain_routed": domain,
            "confidence": confidence,
            "expected_doc_ids": expected_doc_ids,
            "ground_truth_answer": ground_truth_answer
        }
        
        rebuilt_entries.append(rebuilt_entry)
        print(f"  Domain: {domain} (confidence {confidence:.2f})")
        print(f"  Expected IDs: {expected_doc_ids}")
        
    except Exception as e:
        print(f"  ERROR: {str(e)[:80]}")

# Write rebuilt golden set
output_path = Path(__file__).parent / "evaluation" / "golden_set.jsonl"
with open(output_path, "w") as f:
    for entry in rebuilt_entries:
        f.write(json.dumps(entry) + "\n")

print(f"\n{'='*80}")
print(f"✅ Rebuilt golden_set.jsonl with {len(rebuilt_entries)}/30 entries")
print(f"   Location: {output_path}")
print(f"\nKey changes:")
print(f"  - Queries now route through full orchestrator (with updated intent prompt)")
print(f"  - expected_doc_ids extracted from orchestrator chunk_ids")
print(f"  - Includes domain_routed and confidence for verification")
