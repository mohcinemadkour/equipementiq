"""SQLite feedback store for EquipmentIQ RAG system."""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


DB_PATH = Path(__file__).parent.parent / "feedback.db"


def init_db() -> None:
    """Initialize SQLite database with feedback table if not exists."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            query TEXT NOT NULL,
            agent_routed TEXT NOT NULL,
            domain TEXT,
            confidence REAL,
            retrieved_chunk_ids TEXT,
            generated_answer TEXT,
            rating TEXT,
            free_text TEXT,
            session_id TEXT,
            faithfulness_score REAL,
            llm_judge_score REAL,
            failure_mode TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def save_feedback(record: Dict[str, Any]) -> str:
    """
    Save feedback record to database.
    
    Args:
        record: Dictionary with feedback fields
        
    Returns:
        feedback_id (UUID string)
    """
    init_db()  # Ensure table exists
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    feedback_id = str(uuid.uuid4())
    timestamp = record.get('timestamp', datetime.now().isoformat())
    
    cursor.execute("""
        INSERT INTO feedback (
            feedback_id, timestamp, query, agent_routed, domain, confidence,
            retrieved_chunk_ids, generated_answer, rating, free_text, session_id,
            faithfulness_score, llm_judge_score, failure_mode
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        feedback_id,
        timestamp,
        record.get('query', ''),
        record.get('agent_routed', ''),
        record.get('domain', None),
        record.get('confidence', None),
        json.dumps(record.get('retrieved_chunk_ids', [])),
        record.get('generated_answer', ''),
        record.get('rating', None),
        record.get('free_text', None),
        record.get('session_id', None),
        record.get('faithfulness_score', None),
        record.get('llm_judge_score', None),
        record.get('failure_mode', None),
    ))
    
    conn.commit()
    conn.close()
    
    return feedback_id


def get_feedback(limit: int = 100, rating: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve feedback records from database.
    
    Args:
        limit: Maximum number of records to return
        rating: Filter by rating (positive, negative, neutral), or None for all
        
    Returns:
        List of feedback dictionaries
    """
    init_db()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if rating:
        cursor.execute(
            "SELECT * FROM feedback WHERE rating = ? ORDER BY created_at DESC LIMIT ?",
            (rating, limit)
        )
    else:
        cursor.execute(
            "SELECT * FROM feedback ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
    
    rows = cursor.fetchall()
    conn.close()
    
    records = []
    for row in rows:
        record = dict(row)
        # Deserialize JSON fields
        if record.get('retrieved_chunk_ids'):
            try:
                record['retrieved_chunk_ids'] = json.loads(record['retrieved_chunk_ids'])
            except json.JSONDecodeError:
                record['retrieved_chunk_ids'] = []
        records.append(record)
    
    return records


def get_stats() -> Dict[str, Any]:
    """
    Compute aggregate statistics from feedback.
    
    Returns:
        Dictionary with keys:
        - total: int, total feedback records
        - positive: int, count of positive ratings
        - negative: int, count of negative ratings
        - neutral: int, count of neutral ratings
        - avg_faithfulness: float
        - avg_llm_judge: float
        - by_agent: dict mapping agent → count
        - by_failure_mode: dict mapping failure_mode → count
    """
    init_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total records
    cursor.execute("SELECT COUNT(*) FROM feedback")
    total = cursor.fetchone()[0]
    
    # By rating
    cursor.execute(
        "SELECT rating, COUNT(*) FROM feedback WHERE rating IS NOT NULL GROUP BY rating"
    )
    rating_counts = dict(cursor.fetchall())
    
    # Average scores
    cursor.execute("SELECT AVG(faithfulness_score) FROM feedback WHERE faithfulness_score IS NOT NULL")
    avg_faith = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT AVG(llm_judge_score) FROM feedback WHERE llm_judge_score IS NOT NULL")
    avg_judge = cursor.fetchone()[0] or 0.0
    
    # By agent
    cursor.execute(
        "SELECT agent_routed, COUNT(*) FROM feedback WHERE agent_routed IS NOT NULL GROUP BY agent_routed"
    )
    by_agent = dict(cursor.fetchall())
    
    # By failure mode
    cursor.execute(
        "SELECT failure_mode, COUNT(*) FROM feedback WHERE failure_mode IS NOT NULL GROUP BY failure_mode"
    )
    by_failure_mode = dict(cursor.fetchall())
    
    conn.close()
    
    return {
        'total': total,
        'positive': rating_counts.get('positive', 0),
        'negative': rating_counts.get('negative', 0),
        'neutral': rating_counts.get('neutral', 0),
        'avg_faithfulness': round(avg_faith, 4),
        'avg_llm_judge': round(avg_judge, 4),
        'by_agent': by_agent,
        'by_failure_mode': by_failure_mode,
    }
