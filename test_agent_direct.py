"""Test agent retrieval directly."""

from agents.software_agent import SoftwareAgent

agent = SoftwareAgent()
response = agent.retrieve("What is SPN-CR-001?")

print(f"Num results: {len(response.results)}")
print(f"Insufficient context: {response.insufficient_context}")

if response.results:
    for i, r in enumerate(response.results[:3]):
        print(f"\n{i+1}. {r.source_document}")
        print(f"   Similarity: {r.similarity_score:.4f}")
        print(f"   Content: {r.content[:80]}...")
else:
    print("\nNo results returned!")
