"""
Drift detection for embedding quality degradation.

Computes embedding centroids and detects cosine distance changes
between baseline and current centroid. Used to flag potential
model degradation or data distribution shift.
"""

import json
import numpy as np
import os
from pathlib import Path

import chromadb
from ingestion.config import load_config

config = load_config()
DRIFT_THRESHOLD = config.get("evaluation", {}).get("drift_threshold", 0.15)
BASELINE_DIR = Path("evaluation/baselines")


def compute_centroid(collection_name: str) -> np.ndarray:
    """
    Compute mean embedding vector for all documents in a ChromaDB collection.
    
    Args:
        collection_name: Name of the ChromaDB collection (e.g., 'mechanical_collection')
    
    Returns:
        np.ndarray: Mean embedding vector (1536 dims for text-embedding-3-small)
    """
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(name=collection_name)
    
    # Get all embeddings (ChromaDB returns them in include=['embeddings'])
    results = collection.get(include=["embeddings"])
    
    if not results or not results["embeddings"]:
        raise ValueError(f"No embeddings found in {collection_name}")
    
    embeddings = np.array(results["embeddings"])
    centroid = np.mean(embeddings, axis=0)
    
    return centroid


def cosine_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine distance (1 - cosine similarity) between two vectors.
    
    Args:
        vec1, vec2: 1D numpy arrays
    
    Returns:
        float: Distance in [0, 2], where 0 = identical, 2 = opposite
    """
    similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    return 1 - similarity


def detect_drift(collection_name: str) -> dict:
    """
    Compare current collection centroid to saved baseline.
    
    Args:
        collection_name: Name of the ChromaDB collection
    
    Returns:
        dict with keys:
            - collection: str (name)
            - drift: float (cosine distance from baseline)
            - alert: bool (True if drift > DRIFT_THRESHOLD = 0.15)
            - baseline_exists: bool
    """
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    baseline_path = BASELINE_DIR / f"{collection_name}_baseline.npy"
    
    current_centroid = compute_centroid(collection_name)
    
    if not baseline_path.exists():
        return {
            "collection": collection_name,
            "drift": None,
            "alert": False,
            "baseline_exists": False
        }
    
    baseline_centroid = np.load(baseline_path)
    drift = float(cosine_distance(baseline_centroid, current_centroid))
    alert = drift > DRIFT_THRESHOLD
    
    return {
        "collection": collection_name,
        "drift": round(drift, 4),
        "alert": alert,
        "baseline_exists": True
    }


def update_baseline(collection_name: str) -> None:
    """
    Compute and save current collection centroid as baseline.
    
    Args:
        collection_name: Name of the ChromaDB collection
    """
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    baseline_path = BASELINE_DIR / f"{collection_name}_baseline.npy"
    
    centroid = compute_centroid(collection_name)
    np.save(baseline_path, centroid)
    print(f"Baseline updated: {baseline_path}")
