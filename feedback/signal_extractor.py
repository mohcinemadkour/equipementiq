"""Signal extraction from user feedback using LLM classification."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from anthropic import Anthropic


def extract_signal(
    query: str,
    answer: str,
    free_text: Optional[str] = None,
    rating: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract root cause signal from feedback using Claude classification.
    
    If rating is "negative" AND free_text is provided:
        - Call Claude Haiku with feedback_classifier.txt prompt
        - Parse JSON response with failure_mode, affected_agent, chunk_blamed, confidence
    
    Otherwise:
        - Return neutral "correct" classification
    
    Args:
        query: The original user query
        answer: The generated answer
        free_text: Optional user-provided feedback text
        rating: Rating (positive|negative|neutral)
        
    Returns:
        Dictionary:
        {
            "failure_mode": str,
            "affected_agent": str,
            "chunk_blamed": bool,
            "confidence": float
        }
    """
    
    # Default: neutral/correct classification
    if not rating or rating != "negative" or not free_text:
        return {
            "failure_mode": "correct",
            "affected_agent": "unknown",
            "chunk_blamed": False,
            "confidence": 1.0
        }
    
    # Negative rating with free text: use Claude to classify
    classifier_prompt_path = Path(__file__).parent.parent / "prompts" / "feedback_classifier.txt"
    with open(classifier_prompt_path, 'r') as f:
        base_prompt = f.read()
    
    # Use string replacement instead of format() to avoid brace conflicts
    prompt = base_prompt.replace('{query}', query)
    prompt = prompt.replace('{answer}', answer)
    prompt = prompt.replace('{free_text}', free_text or '')
    prompt = prompt.replace('{rating}', rating or '')
    
    client = Anthropic()
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        
        # Parse JSON response
        try:
            result = json.loads(response_text)
            return {
                "failure_mode": result.get("failure_mode", "correct"),
                "affected_agent": result.get("affected_agent", "unknown"),
                "chunk_blamed": bool(result.get("chunk_blamed", False)),
                "confidence": float(result.get("confidence", 0.0))
            }
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                result = json.loads(match.group())
                return {
                    "failure_mode": result.get("failure_mode", "correct"),
                    "affected_agent": result.get("affected_agent", "unknown"),
                    "chunk_blamed": bool(result.get("chunk_blamed", False)),
                    "confidence": float(result.get("confidence", 0.0))
                }
            
            # Fallback if no JSON found
            return {
                "failure_mode": "correct",
                "affected_agent": "unknown",
                "chunk_blamed": False,
                "confidence": 0.0
            }
    
    except Exception as e:
        print(f"[WARN] Failed to extract signal: {e}")
        return {
            "failure_mode": "correct",
            "affected_agent": "unknown",
            "chunk_blamed": False,
            "confidence": 0.0
        }
