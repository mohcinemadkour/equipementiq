"""
Full evaluation pipeline: retrieval + generation + drift detection.

Produces summary table and CI gate (exit code 1 if NDCG < 0.70 or faithfulness < 0.80).
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from ingestion.config import load_config

config = load_config()
NDCG_GATE = config.get("evaluation", {}).get("ndcg_threshold", 0.70)
FAITHFULNESS_GATE = config.get("evaluation", {}).get("faithfulness_threshold", 0.80)


def run_batch_eval(golden_path: str = "evaluation/golden_set.jsonl"):
    """
    Execute full evaluation: retrieval, generation, drift.
    
    Returns:
        dict with all metrics and gate result
    """
    # Defer imports to avoid module-level hangs
    from evaluation.retrieval_metrics import evaluate_collection
    from evaluation.generation_metrics import sample_and_evaluate
    from evaluation.drift_monitor import detect_drift
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "retrieval": {},
        "generation": {},
        "drift": {},
        "gate_result": "PASS",
        "failures": []
    }
    
    # Load golden set
    with open(golden_path) as f:
        golden_pairs = [json.loads(line) for line in f]
    
    # Group by agent
    mechanical_pairs = [p for p in golden_pairs if p["agent"] == "mechanical"]
    software_pairs = [p for p in golden_pairs if p["agent"] == "software"]
    support_pairs = [p for p in golden_pairs if p["agent"] == "support"]
    
    # === RETRIEVAL EVAL ===
    print("\n[1/3] Running retrieval evaluation...")
    
    for agent, pairs, collection in [
        ("mechanical", mechanical_pairs, "mechanical_collection"),
        ("software", software_pairs, "software_collection"),
        ("support", support_pairs, "support_collection"),
    ]:
        metrics = evaluate_collection(agent, pairs)
        results["retrieval"][agent] = metrics
        
        # Check NDCG gate
        if metrics["ndcg"] < NDCG_GATE:
            results["failures"].append(f"NDCG gate FAIL ({agent}): {metrics['ndcg']:.3f} < {NDCG_GATE}")
    
    # === GENERATION EVAL ===
    print("[2/3] Running generation evaluation...")
    gen_metrics = sample_and_evaluate(golden_path, sample_rate=0.12)
    
    faithfulness = gen_metrics["faithfulness"]
    relevance = gen_metrics["answer_relevance"]
    judge_avg = gen_metrics["llm_judge_avg"]
    
    results["generation"] = {
        "faithfulness": round(faithfulness, 3),
        "answer_relevance": round(relevance, 3),
        "llm_judge_avg": round(judge_avg, 2),
        "n_sampled": gen_metrics["n_sampled"]
    }
    
    # Check faithfulness gate
    if faithfulness < FAITHFULNESS_GATE:
        results["failures"].append(f"Faithfulness gate FAIL: {faithfulness:.3f} < {FAITHFULNESS_GATE}")
    
    # === DRIFT DETECTION ===
    print("[3/3] Running drift detection...")
    for collection in ["mechanical_collection", "software_collection", "support_collection"]:
        drift_result = detect_drift(collection)
        results["drift"][collection] = drift_result
    
    # === GATE RESULT ===
    if results["failures"]:
        results["gate_result"] = "FAIL"
    
    return results


def print_summary(results: dict) -> None:
    """Print formatted evaluation summary table."""
    
    # Retrieval table
    print("\n" + "="*60)
    print("  EquipmentIQ Evaluation Summary")
    print("="*60)
    print("\nRetrieval Metrics:")
    print("┌──────────────────┬───────┬─────────┬──────┬─────────┐")
    print("│ Collection       │ NDCG  │ HitRate │ MRR  │ Drift   │")
    print("├──────────────────┼───────┼─────────┼──────┼─────────┤")
    
    collection_order = ["mechanical", "software", "support"]
    collection_names = ["mechanical_collection", "software_collection", "support_collection"]
    
    for agent, collection_name in zip(collection_order, collection_names):
        retr = results["retrieval"].get(agent, {})
        drift = results["drift"].get(collection_name, {})
        
        ndcg = retr.get("ndcg", 0)
        hit = retr.get("hit_rate", 0)
        mrr = retr.get("mrr", 0)
        drift_status = "ALERT" if drift.get("alert") else "OK"
        if drift.get("drift") is None:
            drift_status = "—"
        
        print(f"│ {agent:16s} │ {ndcg:5.2f} │ {hit:7.2f} │ {mrr:4.2f} │ {drift_status:7s} │")
    
    print("└──────────────────┴───────┴─────────┴──────┴─────────┘")
    
    # Generation metrics
    gen = results["generation"]
    print(f"\nGeneration Metrics (N={gen.get('n_sampled', 0)} sampled):")
    print(f"  Faithfulness:     {gen.get('faithfulness', 0):.3f}")
    print(f"  Answer Relevance: {gen.get('answer_relevance', 0):.3f}")
    print(f"  LLM Judge avg:    {gen.get('llm_judge_avg', 0):.1f} / 5")
    
    # Gate result
    print(f"\nGate Result: {results['gate_result']}")
    if results["failures"]:
        print("Failures:")
        for failure in results["failures"]:
            print(f"  - {failure}")
    
    print("="*60 + "\n")


def save_results(results: dict) -> Path:
    """Save results to evaluation/results/ as JSONL."""
    results_dir = Path("evaluation/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = results_dir / f"batch_{timestamp}.jsonl"
    
    with open(results_path, "w") as f:
        f.write(json.dumps(results) + "\n")
    
    print(f"Results saved to {results_path}")
    return results_path


def main():
    """Run full batch evaluation and return exit code."""
    try:
        results = run_batch_eval()
        print_summary(results)
        save_results(results)
        
        if results["gate_result"] == "FAIL":
            print("❌ CI GATE FAILED — deployment blocked")
            sys.exit(1)
        else:
            print("✅ CI GATE PASSED — ready to deploy")
            sys.exit(0)
    
    except Exception as e:
        print(f"Error during evaluation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
