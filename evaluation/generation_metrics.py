"""
Generation quality metrics for EquipmentIQ RAG system.
Computes faithfulness, answer relevance, and LLM-as-Judge scores.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import math
from datetime import datetime
from typing import Optional
import os
from anthropic import Anthropic

# Try to import RAGAS
try:
    from ragas.metrics import Faithfulness, AnswerRelevancy
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False
    print("[WARN] RAGAS not available, using LLM-as-Judge fallback")

from orchestrator.graph import run_query


def faithfulness_score(query: str, context_chunks: list[str], answer: str) -> float:
    """
    Measure how faithful the answer is to the provided context.
    Tries RAGAS Faithfulness first, falls back to LLM-as-Judge.
    
    Returns: float in [0.0, 1.0]
    """
    if RAGAS_AVAILABLE:
        try:
            faithfulness = Faithfulness()
            # RAGAS expects specific data format
            score = faithfulness.score({
                "question": query,
                "answer": answer,
                "contexts": context_chunks
            })
            return float(score)
        except Exception as e:
            print(f"[RAGAS Faithfulness failed: {e}] Using LLM fallback")
    
    # Fallback: LLM-as-Judge
    return _llm_faithfulness_fallback(query, context_chunks, answer)


def _llm_faithfulness_fallback(query: str, context_chunks: list[str], answer: str) -> float:
    """
    Use Claude Haiku to evaluate faithfulness.
    Score each claim in the answer: supported or not.
    Return proportion of supported claims.
    """
    if not context_chunks or not answer:
        return 0.0
    
    context_text = "\n\n".join(context_chunks)
    
    prompt = f"""Evaluate whether each claim in the provided answer is supported by the context documents.

Context documents:
{context_text}

User query:
{query}

Answer to evaluate:
{answer}

Task: Identify each major factual claim in the answer and determine if it is:
- SUPPORTED: explicitly stated or directly implied by the context
- UNSUPPORTED: not mentioned in the context
- CONTRADICTED: directly contradicts the context

Provide your evaluation as a JSON object with:
{{
  "claims": [
    {{"claim": "...", "status": "SUPPORTED|UNSUPPORTED|CONTRADICTED"}},
    ...
  ],
  "supported_count": <int>,
  "total_claims": <int>,
  "faithfulness_score": <float 0.0-1.0>
}}
"""
    
    client = Anthropic()
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response
        text = response.content[0].text
        # Extract JSON from response
        try:
            result = json.loads(text)
            return float(result.get("faithfulness_score", 0.0))
        except json.JSONDecodeError:
            # Try to extract score from text
            if "faithfulness_score" in text:
                import re
                match = re.search(r'"faithfulness_score":\s*([0-9.]+)', text)
                if match:
                    return float(match.group(1))
            return 0.0
    except Exception as e:
        print(f"  ⚠️  Faithfulness evaluation failed: {e}")
        return 0.0


def answer_relevance_score(query: str, answer: str) -> float:
    """
    Measure how relevant the answer is to the query.
    Tries RAGAS AnswerRelevancy first, falls back to LLM.
    
    Returns: float in [0.0, 1.0]
    """
    if RAGAS_AVAILABLE:
        try:
            relevancy = AnswerRelevancy()
            score = relevancy.score({
                "question": query,
                "answer": answer
            })
            return float(score)
        except Exception as e:
            print(f"[RAGAS AnswerRelevancy failed: {e}] Using LLM fallback")
    
    # Fallback: LLM-as-Judge
    return _llm_relevance_fallback(query, answer)


def _llm_relevance_fallback(query: str, answer: str) -> float:
    """
    Use Claude Haiku to score answer relevance 1-5, return as 0.0-1.0.
    """
    if not answer:
        return 0.0
    
    prompt = f"""Rate how well the answer addresses the user's query.

Query:
{query}

Answer:
{answer}

Score from 1 to 5:
- 1: Answer is off-topic or irrelevant
- 2: Answer is partially relevant but misses key aspects
- 3: Answer addresses the query adequately
- 4: Answer directly addresses all main points
- 5: Answer thoroughly and comprehensively addresses the query

Respond with only the score (1-5) and a brief explanation.
Format: {{"score": <int>, "explanation": "<str>"}}
"""
    
    client = Anthropic()
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.content[0].text
        try:
            result = json.loads(text)
            score = float(result.get("score", 3))
            return min(1.0, score / 5.0)
        except json.JSONDecodeError:
            import re
            match = re.search(r'"score":\s*(\d)', text)
            if match:
                return float(match.group(1)) / 5.0
            return 0.6  # default acceptable
    except Exception as e:
        print(f"  ⚠️  Relevance evaluation failed: {e}")
        return 0.6


def llm_judge_score(query: str, context_chunks: list[str], answer: str) -> dict:
    """
    Comprehensive evaluation using LLM-as-Judge with 4 dimensions.
    
    Returns:
        {
            "score": int 1-5,
            "reasoning": str,
            "factual_accuracy": int 1-5,
            "completeness": int 1-5,
            "uncertainty_handling": int 1-5,
            "citation_quality": int 1-5
        }
    """
    # Load judge prompt
    judge_prompt_path = Path(__file__).parent.parent / "prompts" / "llm_judge.txt"
    with open(judge_prompt_path, 'r') as f:
        base_prompt = f.read()
    
    # Format context
    context_text = "\n\n".join([f"[{i+1}] {chunk}" for i, chunk in enumerate(context_chunks)])
    
    # Inject variables
    prompt = base_prompt.format(
        user_query=query,
        context_text=context_text,
        generated_answer=answer
    )
    
    client = Anthropic()
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.content[0].text
        
        # Parse JSON response
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown or other format
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                # Fallback: return default structure
                result = {
                    "score": 3,
                    "reasoning": "Could not parse judge response",
                    "factual_accuracy": 3,
                    "completeness": 3,
                    "uncertainty_handling": 3,
                    "citation_quality": 3
                }
        
        # Ensure all required keys exist with correct types
        return {
            "score": int(result.get("score", 3)),
            "reasoning": str(result.get("reasoning", "")),
            "factual_accuracy": int(result.get("factual_accuracy", 3)),
            "completeness": int(result.get("completeness", 3)),
            "uncertainty_handling": int(result.get("uncertainty_handling", 3)),
            "citation_quality": int(result.get("citation_quality", 3))
        }
    except Exception as e:
        print(f"  ⚠️  LLM Judge evaluation failed: {e}")
        return {
            "score": 3,
            "reasoning": f"Error: {str(e)}",
            "factual_accuracy": 3,
            "completeness": 3,
            "uncertainty_handling": 3,
            "citation_quality": 3
        }


def sample_and_evaluate(golden_path: str, sample_rate: float = 0.12) -> list[dict]:
    """
    Sample from golden set, run live queries, evaluate generation quality.
    
    Args:
        golden_path: Path to golden_set.jsonl
        sample_rate: Sampling rate (e.g., 0.12 = 12%)
    
    Returns:
        List of evaluation result dicts
    """
    # Load golden set
    with open(golden_path, 'r') as f:
        all_pairs = [json.loads(line) for line in f]
    
    # Sample
    sample_size = max(3, math.ceil(len(all_pairs) * sample_rate))
    import random
    sampled = random.sample(all_pairs, min(sample_size, len(all_pairs)))
    
    print(f"[GENERATION EVALUATION]")
    print(f"Sampled {len(sampled)} queries from {len(all_pairs)} golden pairs ({sample_rate*100:.0f}%)")
    
    results = []
    
    for i, pair in enumerate(sampled, 1):
        query = pair['query']
        expected_ids = pair['expected_doc_ids']
        
        print(f"\n  {i}. {query[:60]}...")
        
        try:
            # Get live answer
            result = run_query(query)
            answer = result.get('final_answer', '')
            
            # Extract context chunks from merged_context
            context_chunks = []
            if 'merged_context' in result and result['merged_context']:
                # DEBUG: print context structure before processing
                print(f"     [DEBUG] merged_context type={type(result['merged_context'])}, len={len(result['merged_context'])}")
                if result['merged_context']:
                    first_item = result['merged_context'][0]
                    print(f"     [DEBUG] first item type={type(first_item)}, keys={list(first_item.keys()) if isinstance(first_item, dict) else 'not a dict'}")
                
                context_chunks = [chunk.get('content', '') for chunk in result['merged_context']]
            
            # Evaluate
            faithfulness = faithfulness_score(query, context_chunks, answer)
            relevance = answer_relevance_score(query, answer)
            judge_result = llm_judge_score(query, context_chunks, answer)
            
            eval_result = {
                'query': query,
                'agent': pair.get('agent', 'unknown'),
                'answer': answer,
                'faithfulness': round(faithfulness, 4),
                'answer_relevance': round(relevance, 4),
                'judge_score': judge_result['score'],
                'judge_reasoning': judge_result['reasoning'],
                'judge_details': {
                    'factual_accuracy': judge_result['factual_accuracy'],
                    'completeness': judge_result['completeness'],
                    'uncertainty_handling': judge_result['uncertainty_handling'],
                    'citation_quality': judge_result['citation_quality']
                },
                'timestamp': datetime.now().isoformat()
            }
            
            results.append(eval_result)
            
            print(f"     Faithfulness={faithfulness:.2f} Relevance={relevance:.2f} Judge={judge_result['score']}/5")
            
        except Exception as e:
            print(f"     ⚠️  Evaluation failed: {e}")
            results.append({
                'query': query,
                'agent': pair.get('agent', 'unknown'),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_path = Path('evaluation/results') / f'generation_{timestamp}.jsonl'
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_path, 'w') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')
    
    print(f"\n[OK] Generation evaluation results saved to {results_path}")
    
    return results


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Evaluate generation quality')
    parser.add_argument('--golden', default='evaluation/golden_set.jsonl', help='Path to golden set')
    parser.add_argument('--sample-rate', type=float, default=0.12, help='Sampling rate')
    args = parser.parse_args()
    
    sample_and_evaluate(args.golden, args.sample_rate)
