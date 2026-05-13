#!/usr/bin/env python
"""Standalone test for conflict detection guard in intent classifier."""

import re

def test_conflict_detection():
    """Test the conflict detection logic without importing full orchestrator."""
    
    # Define keyword sets (copied from intent_classifier.py)
    software_keywords = {
        "error code", "alarm", "spn", "axs", "vib", "tcs", "lub", "hyd", "elc", "thm", "cnc",
        "severity", "fault code", "fires when", "triggers when", "signal", "diagnostic"
    }
    
    mechanical_keywords = {
        "bearing", "spindle", "wiring", "pressure", "specification", "coolant", "lubrication",
        "hydraulic", "part number", "maintenance schedule", "encoder", "motor"
    }
    
    test_cases = [
        ("Software-only", "What does error SPN-CR-001 mean?", False),
        ("Mechanical-only", "What bearing type does the spindle use?", False),
        ("Conflict: bearing+alarm", "When does the spindle bearing vibration alarm fire?", True),
        ("Conflict: bearing+error code", "What's the error code for bearing pressure signal?", True),
        ("Conflict: spindle+vib", "What causes spindle vibration faults?", True),
        ("Conflict: wiring+signal", "What wiring carries the diagnostic signal?", True),
        ("No keywords", "Tell me about the machine", False),
    ]
    
    print(f"{'Scenario':<35} | {'Has Conflict?':<15} | {'Expected':<10} | {'Result'}")
    print("-" * 80)
    
    passed = 0
    for label, query, expected_conflict in test_cases:
        query_lower = query.lower()
        
        # Check for conflict
        has_software = any(kw in query_lower for kw in software_keywords)
        has_mechanical = any(kw in query_lower for kw in mechanical_keywords)
        has_conflict = has_software and has_mechanical
        
        status = "✓ PASS" if has_conflict == expected_conflict else "✗ FAIL"
        if has_conflict == expected_conflict:
            passed += 1
        
        print(f"{label:<35} | {str(has_conflict):<15} | {str(expected_conflict):<10} | {status}")
    
    print("-" * 80)
    print(f"Results: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


if __name__ == "__main__":
    success = test_conflict_detection()
    exit(0 if success else 1)
