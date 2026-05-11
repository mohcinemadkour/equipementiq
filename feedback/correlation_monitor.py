"""Correlation monitoring between feedback ratings and evaluation metrics."""

from typing import Dict, List, Any
from .feedback_store import get_feedback


def correlate(limit: int = 50) -> Dict[str, Any]:
    """
    Analyze correlation between user ratings and evaluation metrics.
    
    Identifies discordant cases: rating=="negative" AND faithfulness_score >= 0.80
    This indicates potential metric calibration issues.
    
    Args:
        limit: Maximum number of recent feedback records to analyze
        
    Returns:
        Dictionary with keys:
        - n_records: int, number of records analyzed
        - n_with_scores: int, records that have both rating and faithfulness_score
        - discordant_cases: list[dict], cases where rating=negative but faithfulness >= 0.80
        - metric_calibration_flag: bool, True if >20% of records are discordant
        - summary: str, human-readable summary
    """
    
    # Load recent feedback
    records = get_feedback(limit=limit)
    
    n_records = len(records)
    n_with_scores = 0
    discordant_cases = []
    
    for record in records:
        rating = record.get('rating')
        faithfulness = record.get('faithfulness_score')
        
        # Only consider records with both rating and faithfulness score
        if rating is not None and faithfulness is not None:
            n_with_scores += 1
            
            # Discordant: negative rating but high faithfulness
            if rating == 'negative' and faithfulness >= 0.80:
                discordant_cases.append({
                    'feedback_id': record.get('feedback_id'),
                    'query': record.get('query', ''),
                    'rating': rating,
                    'faithfulness_score': faithfulness,
                    'failure_mode': record.get('failure_mode', 'unknown'),
                    'created_at': record.get('created_at')
                })
    
    # Compute calibration flag
    discordance_rate = (
        (len(discordant_cases) / n_with_scores) if n_with_scores > 0 else 0.0
    )
    metric_calibration_flag = discordance_rate > 0.20  # >20% = flag
    
    # Generate summary
    summary = (
        f"Analyzed {n_records} feedback records, {n_with_scores} have both rating and faithfulness_score. "
        f"Found {len(discordant_cases)} discordant cases (discordance rate: {discordance_rate*100:.1f}%). "
        f"Metric calibration: {'NEEDS REVIEW' if metric_calibration_flag else 'OK'}"
    )
    
    return {
        'n_records': n_records,
        'n_with_scores': n_with_scores,
        'discordant_cases': discordant_cases,
        'metric_calibration_flag': metric_calibration_flag,
        'summary': summary
    }
