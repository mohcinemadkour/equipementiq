"""Check what agent_results contain."""

from orchestrator.graph import run_query
import json

result = run_query("What is SPN-CR-001?")

print("Agent Results:")
print(json.dumps(result.get('agent_results', {}), indent=2, default=str))
