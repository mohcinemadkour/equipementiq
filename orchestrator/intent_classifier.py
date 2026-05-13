"""
Intent classification for orchestrator routing.

Classifies incoming queries to determine which agent(s) to invoke.
- Single-agent routing: confidence >= 0.80
- Cross-domain routing: confidence < 0.80 (invoke all agents in parallel)

Optimization: Rule-based fast-path pre-classifier skips Claude API for common patterns.
"""

import json
import re
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


# ============================================================================
# Rule-based Pre-Classifier (Fast Path)
# ============================================================================

def _rule_based_classify(query: str) -> IntentClassification | None:
    """Apply rule-based pre-classification to skip Claude API on common patterns.
    
    Rules (in priority order):
    1. Conflict detection: If query contains BOTH software AND mechanical keywords, 
       skip fast-path rules and return None (defer to Claude)
    2. Query contains "CMP-" + digits → SUPPORT (confidence 0.99)
    3. Query contains error code pattern (e.g., SPN-CR-001) → SOFTWARE (confidence 0.99)
    4. Query contains keywords: "complaint", "case", "RMA", "remedy" → SUPPORT (0.90)
    5. Query contains keywords: "part number", "wiring", "bearing type", "maintenance" → MECHANICAL (0.90)
    
    Returns:
        IntentClassification if a rule matched, else None (fall through to Claude)
    """
    query_lower = query.lower()
    
    # =========================================================================
    # CONFLICT DETECTION GUARD (runs before all domain rules)
    # =========================================================================
    # Software keywords: error codes, alarms, subsystems, severity, fault indicators
    software_keywords = {
        "error code", "alarm", "spn", "axs", "vib", "tcs", "lub", "hyd", "elc", "thm", "cnc",
        "severity", "fault code", "fires when", "triggers when", "signal", "diagnostic"
    }
    
    # Mechanical keywords: physical components, specs, maintenance, hydraulics
    mechanical_keywords = {
        "bearing", "spindle", "wiring", "pressure", "specification", "coolant", "lubrication",
        "hydraulic", "part number", "maintenance schedule", "encoder", "motor"
    }
    
    # Check for conflict: both software AND mechanical keywords present
    has_software = any(kw in query_lower for kw in software_keywords)
    has_mechanical = any(kw in query_lower for kw in mechanical_keywords)
    has_conflict = has_software and has_mechanical
    
    if has_conflict:
        # Skip all fast-path rules, defer to Claude for nuanced understanding
        return None
    
    # =========================================================================
    # DOMAIN-SPECIFIC RULES (only run if no conflict detected)
    # =========================================================================
    
    # Rule 2: Case ID pattern CMP-XXXX-XXXX
    if re.search(r'CMP-\d+', query):
        return IntentClassification(
            domain="support",
            confidence=0.99,
            reasoning="Query contains complaint case ID (CMP-XXXX pattern)",
            suggested_filters={}
        )
    
    # Rule 3: Error code pattern XXX-YY-ZZZ (e.g., SPN-CR-001, AXS-MD-002)
    if re.search(r'\b[A-Z]{3}-[A-Z]{2}-\d{3}\b', query):
        return IntentClassification(
            domain="software",
            confidence=0.99,
            reasoning="Query contains error code pattern (XXX-YY-ZZZ)",
            suggested_filters={}
        )
    
    # Rule 4: Support keywords
    support_keywords = ["complaint", "case", "rma", "remedy", "warranty"]
    if any(keyword in query_lower for keyword in support_keywords):
        return IntentClassification(
            domain="support",
            confidence=0.90,
            reasoning="Query contains support-related keyword",
            suggested_filters={}
        )
    
    # Rule 5: Mechanical keywords
    mech_keywords = ["part number", "wiring", "bearing type", "maintenance schedule", "spindle"]
    if any(keyword in query_lower for keyword in mech_keywords):
        return IntentClassification(
            domain="mechanical",
            confidence=0.90,
            reasoning="Query contains mechanical-related keyword",
            suggested_filters={}
        )
    
    # No rule matched
    return None


def classify(query: str, history: list[dict] | None = None) -> IntentClassification:
    """Classify user query to determine routing domain.
    
    Args:
        query: User question
        history: Last 5 (query, answer) turns for context (optional)
    
    Returns:
        IntentClassification with domain, confidence, reasoning, filters
    
    Process:
        1. Try rule-based pre-classifier (fast path, skips Claude)
        2. If no rule matches, call Claude API with JSON mode
        3. Parse JSON response into IntentClassification
        4. If confidence < cfg.orchestrator.intent_confidence_threshold:
           override domain to "cross_domain"
        5. Return validated IntentClassification
    """
    cfg = load_config()
    threshold = cfg["orchestrator"]["intent_confidence_threshold"]
    
    # =========================================================================
    # Step 1: Try rule-based pre-classifier (fast path)
    # =========================================================================
    rule_result = _rule_based_classify(query)
    if rule_result is not None:
        # Rule matched - return immediately without Claude API call
        if rule_result.confidence < threshold:
            rule_result.domain = "cross_domain"
        return rule_result
    
    # =========================================================================
    # Step 2: Fall through to Claude API (slow path)
    # =========================================================================
    
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
