"""
Simple check of support query keywords to understand routing issues.
"""

import json

# Load and extract support queries
with open("evaluation/golden_set.jsonl", "r") as f:
    lines = [line.strip() for line in f if line.strip()]
    golden_set = [json.loads(line) for line in lines]

support_queries = [item for item in golden_set if item["agent"] == "support"]

# Define keywords from intent_classifier.py
software_keywords = {
    "error code", "alarm", "spn", "axs", "vib", "tcs", "lub", "hyd", "elc", "thm", "cnc",
    "severity", "fault code", "fires when", "triggers when", "signal", "diagnostic"
}

mechanical_keywords = {
    "bearing", "spindle", "wiring", "pressure", "specification", "coolant", "lubrication",
    "hydraulic", "part number", "maintenance schedule", "encoder", "motor"
}

support_keywords = ["complaint", "case", "rma", "remedy", "warranty"]

print("\n" + "="*120)
print(f"SUPPORT QUERY KEYWORD ANALYSIS ({len(support_queries)} queries)")
print("="*120 + "\n")

for i, item in enumerate(support_queries, 1):
    query = item["query"]
    query_lower = query.lower()
    
    # Check for keywords
    has_software = any(kw in query_lower for kw in software_keywords)
    has_mechanical = any(kw in query_lower for kw in mechanical_keywords)
    has_support = any(kw in query_lower for kw in support_keywords)
    has_conflict = has_software and has_mechanical
    
    # Find which keywords matched
    matched_software = [kw for kw in software_keywords if kw in query_lower]
    matched_mechanical = [kw for kw in mechanical_keywords if kw in query_lower]
    matched_support = [kw for kw in support_keywords if kw in query_lower]
    
    print(f"Query {i}: {query}")
    print(f"  Software keywords matched: {matched_software if matched_software else 'NONE'}")
    print(f"  Mechanical keywords matched: {matched_mechanical if matched_mechanical else 'NONE'}")
    print(f"  Support keywords matched: {matched_support if matched_support else 'NONE'}")
    print(f"  Conflict detected: {has_conflict}")
    
    # Predict routing
    if has_conflict:
        prediction = "→ DEFER TO CLAUDE (conflict)"
    elif any(kw in query_lower for kw in support_keywords):
        prediction = "→ ROUTE TO SUPPORT (Rule 4: support keyword)"
    else:
        prediction = "→ DEFER TO CLAUDE (no matching rule)"
    
    print(f"  Prediction: {prediction}\n")
