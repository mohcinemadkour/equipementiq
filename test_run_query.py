import sys
sys.path.insert(0, '.')
from orchestrator.graph import run_query
import json

print('[DEBUG] Starting test...')
try:
    result = run_query('what are all complaints related to AXS-SR-001?')
    print(f'[DEBUG] Domain: {result.get("domain", "N/A")}')
    print(f'[DEBUG] Confidence: {result.get("confidence", "N/A")}')
    print(f'[DEBUG] Agents Used: {result.get("agents_used", "NOT FOUND")}')
    print(f'[DEBUG] Merged Context Chunks: {len(result.get("merged_context", []))}')
    print(f'[DEBUG] Answer Length: {len(result.get("final_answer", ""))}')
    print(f'[DEBUG] Citations: {len(result.get("citations", []))}')
except Exception as e:
    import traceback
    traceback.print_exc()
