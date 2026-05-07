"""
Intent classification for orchestrator routing.

Classifies incoming queries to determine which agent(s) to invoke.
- Single-agent routing: confidence >= 0.80
- Cross-domain routing: confidence < 0.80 (invoke all agents in parallel)
"""

import json
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field
from anthropic import Anthropic

from ingestion.config import load_config


class IntentClassification(BaseModel):
    """Intent classification result from Claude.
    
    Fields:
        domain: Target domain (mechanical, software, support, cross_domain)
        confidence: Confidence in classification [0.0, 1.0]
        reasoning: Explanation of routing decision
        suggested_filters: Domain-specific metadata filters (e.g., subsystem=SPN)
    """
    domain: Literal["mechanical", "software", "support", "cross_domain"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    suggested_filters: dict = Field(default_factory=dict)


@lru_cache(maxsize=1)
def _get_prompt_text() -> str:
    """Load intent classification prompt from disk (cached)."""
    cfg = load_config()
    prompt_path = cfg["paths"]["prompts_dir"] + "/intent_classification.txt"
    with open(prompt_path, "r") as f:
        return f.read()


@lru_cache(maxsize=1)
def _get_client() -> Anthropic:
    """Get cached Anthropic client."""
    return Anthropic()


def classify(query: str, history: list[dict] | None = None) -> IntentClassification:
    """Classify user query to determine routing domain.
    
    Args:
        query: User question
        history: Last 5 (query, answer) turns for context (optional)
    
    Returns:
        IntentClassification with domain, confidence, reasoning, filters
    
    Process:
        1. Load prompt template from prompts/intent_classification.txt
        2. Inject query + history into prompt
        3. Call Claude API with JSON mode (not JSON schema)
        4. Parse JSON response into IntentClassification
        5. If confidence < cfg.orchestrator.intent_confidence_threshold:
           override domain to "cross_domain"
        6. Return validated IntentClassification
    """
    cfg = load_config()
    threshold = cfg["orchestrator"]["intent_confidence_threshold"]
    
    # Load prompt template
    prompt_template = _get_prompt_text()
    
    # Format conversation history for context
    history_str = ""
    if history:
        history_str = "\n".join(
            f"Q: {turn['query']}\nA: {turn['answer'][:200]}..."
            for turn in history[-5:]
        )
        history_str = f"\nRecent conversation:\n{history_str}\n"
    
    # Inject query into prompt
    full_prompt = prompt_template.format(
        current_query=query,
        conversation_context=history_str
    )
    
    # Call Claude with JSON mode (not JSON schema)
    client = _get_client()
    response = client.messages.create(
        model=cfg["llm"]["generation_model"],
        max_tokens=500,
        temperature=0.0,
        messages=[
            {
                "role": "user",
                "content": full_prompt
            }
        ]
    )
    
    # Parse response as JSON
    response_text = response.content[0].text.strip()
    
    # Extract JSON from potential markdown code blocks
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()
    
    # Handle empty response
    if not response_text:
        return IntentClassification(
            domain="cross_domain",
            confidence=0.0,
            reasoning="Claude returned empty response",
            suggested_filters={}
        )
    
    try:
        json_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        # If JSON parsing fails, return a default classification
        return IntentClassification(
            domain="cross_domain",
            confidence=0.0,
            reasoning=f"Failed to parse Claude response as JSON: {str(e)}",
            suggested_filters={}
        )
    
    # Validate with Pydantic
    classification = IntentClassification(**json_data)
    
    # Override to cross_domain if confidence below threshold
    if classification.confidence < threshold:
        classification.domain = "cross_domain"
    
    return classification
