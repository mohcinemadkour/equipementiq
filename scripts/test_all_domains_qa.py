#!/usr/bin/env python
"""Test 80 Q&A pairs across mechanical, software, support, and cross-domain routing.

Validates:
1. Domain routing accuracy (expected vs actual)
2. Answer term coverage (does answer contain expected terms)
3. Overall quality metrics

Outputs:
- Console: Full results table + summary sections
- File: evaluation/results/domain_qa_test_YYYYMMDD.json
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ══════════════════════════════════════════════════════════════════════════════
# 80 Q&A PAIRS — 4 domains × 20 queries each
# ══════════════════════════════════════════════════════════════════════════════

QA_PAIRS = [
    # ══════════════════════════════════════════════════════
    # MECHANICAL DOMAIN — 20 queries
    # ══════════════════════════════════════════════════════
    {"id": "M01", "query": "What is the X-axis travel distance on the VMC-3000?", "expected_domain": "mechanical", "expected_terms": ["800 mm", "800"]},
    {"id": "M02", "query": "What type of ball screw is used on the Z-axis?", "expected_domain": "mechanical", "expected_terms": ["40 mm", "C3", "Z-axis"]},
    {"id": "M03", "query": "What is the maximum spindle speed of the VMC-3000?", "expected_domain": "mechanical", "expected_terms": ["8,000", "8000", "RPM"]},
    {"id": "M04", "query": "How many tools does the ATC magazine hold?", "expected_domain": "mechanical", "expected_terms": ["30", "magazine"]},
    {"id": "M05", "query": "What is the rated spindle motor power?", "expected_domain": "mechanical", "expected_terms": ["18.5 kW", "18.5"]},
    {"id": "M06", "query": "What grease is used for spindle bearing repack?", "expected_domain": "mechanical", "expected_terms": ["Kluber", "Isoflex", "NBU 15"]},
    {"id": "M07", "query": "What is the part number for the spindle front bearing pair?", "expected_domain": "mechanical", "expected_terms": ["EIQ-SPN-BRG-7014", "7014"]},
    {"id": "M08", "query": "What is the chip-to-chip tool change time?", "expected_domain": "mechanical", "expected_terms": ["3.5 s", "3.5"]},
    {"id": "M09", "query": "What signal connects the X-axis encoder to the CNC controller?", "expected_domain": "mechanical", "expected_terms": ["encoder", "AX1-ENC", "CNC-500"]},
    {"id": "M10", "query": "What is the lubrication oil grade for the linear guides?", "expected_domain": "mechanical", "expected_terms": ["ISO VG 32", "VG 32"]},
    {"id": "M11", "query": "What is the coolant tank volume on the VMC-3000?", "expected_domain": "mechanical", "expected_terms": ["300 L", "300"]},
    {"id": "M12", "query": "What is the positioning accuracy of the VMC-3000?", "expected_domain": "mechanical", "expected_terms": ["0.005 mm", "ISO 230-2"]},
    {"id": "M13", "query": "What type of encoder does the Z-axis servo motor use?", "expected_domain": "mechanical", "expected_terms": ["17-bit", "absolute"]},
    {"id": "M14", "query": "What is the hydraulic system nominal pressure?", "expected_domain": "mechanical", "expected_terms": ["70 bar", "70"]},
    {"id": "M15", "query": "What maintenance is required every 4000 operating hours?", "expected_domain": "mechanical", "expected_terms": ["bearing", "grease", "repack"]},
    {"id": "M16", "query": "What is the supply voltage requirement for the VMC-3000?", "expected_domain": "mechanical", "expected_terms": ["380", "420", "3-phase"]},
    {"id": "M17", "query": "What wire gauge connects the spindle motor U-phase to the drive?", "expected_domain": "mechanical", "expected_terms": ["6 mm2", "6mm"]},
    {"id": "M18", "query": "What is the table load capacity of the VMC-3000?", "expected_domain": "mechanical", "expected_terms": ["600 kg", "600"]},
    {"id": "M19", "query": "Which PLC output controls the coolant pump?", "expected_domain": "mechanical", "expected_terms": ["Y0.1", "coolant pump"]},
    {"id": "M20", "query": "What is the spindle bearing grease repack interval?", "expected_domain": "mechanical", "expected_terms": ["4,000 h", "4000", "2 years"]},

    # ══════════════════════════════════════════════════════
    # SOFTWARE / ERROR CODE DOMAIN — 20 queries
    # ══════════════════════════════════════════════════════
    {"id": "S01", "query": "What severity level is error code SPN-CR-001?", "expected_domain": "software", "expected_terms": ["CRITICAL", "critical", "level 1"]},
    {"id": "S02", "query": "What does error AXS-CR-001 indicate?", "expected_domain": "software", "expected_terms": ["following error", "emergency", "axis"]},
    {"id": "S03", "query": "What is the remedy for error TCS-MJ-001?", "expected_domain": "software", "expected_terms": ["clamp", "pressure", "draw-bar"]},
    {"id": "S04", "query": "What parameter P004 monitors and what is its critical limit?", "expected_domain": "software", "expected_terms": ["bearing vibration", "11.2", "mm/s"]},
    {"id": "S05", "query": "List all CRITICAL severity error codes for the spindle subsystem.", "expected_domain": "software", "expected_terms": ["SPN-CR-001", "SPN-CR-002", "SPN-CR-003"]},
    {"id": "S06", "query": "What diagnostic steps are required for error LUB-CR-001?", "expected_domain": "software", "expected_terms": ["oil level", "pump", "distributor"]},
    {"id": "S07", "query": "What is the normal range for parameter P002 spindle load?", "expected_domain": "software", "expected_terms": ["0", "85", "percent"]},
    {"id": "S08", "query": "What action does a WARNING severity error require?", "expected_domain": "software", "expected_terms": ["end of shift", "log", "review"]},
    {"id": "S09", "query": "Which error codes are related to SPN-MJ-002?", "expected_domain": "software", "expected_terms": ["SPN-CR-001", "VIB-MN-061", "SPN-SR-003"]},
    {"id": "S10", "query": "What does error CLS-CR-001 mean and when is it triggered?", "expected_domain": "software", "expected_terms": ["coolant flow", "5 L/min", "emergency"]},
    {"id": "S11", "query": "What is the MID number for the spindle drive subsystem?", "expected_domain": "software", "expected_terms": ["128", "MID 128"]},
    {"id": "S12", "query": "What does error ELC-CR-001 indicate?", "expected_domain": "software", "expected_terms": ["DC bus", "undervoltage", "drives disabled"]},
    {"id": "S13", "query": "What is the probable cause of error SPN-MJ-004?", "expected_domain": "software", "expected_terms": ["chatter", "stability", "unstable"]},
    {"id": "S14", "query": "What parameter monitors hydraulic system pressure?", "expected_domain": "software", "expected_terms": ["P050", "hydraulic", "bar"]},
    {"id": "S15", "query": "How many severity levels does the EquipmentIQ error code system have?", "expected_domain": "software", "expected_terms": ["8", "eight"]},
    {"id": "S16", "query": "What error code fires when the ATC arm collides?", "expected_domain": "software", "expected_terms": ["TCS-CR-001", "ATC", "collision"]},
    {"id": "S17", "query": "What is the normal range for DC bus voltage parameter P090?", "expected_domain": "software", "expected_terms": ["560", "620", "V"]},
    {"id": "S18", "query": "What does a NOTICE severity error require the operator to do?", "expected_domain": "software", "expected_terms": ["maintenance window", "approaching limit", "informational"]},
    {"id": "S19", "query": "Which subsystem does error code VIB-CR-001 belong to?", "expected_domain": "software", "expected_terms": ["VIB", "vibration", "MID 144"]},
    {"id": "S20", "query": "What is the required action for error code THM-CR-001?", "expected_domain": "software", "expected_terms": ["stop", "cooling", "temperature", "emergency"]},

    # ══════════════════════════════════════════════════════
    # SUPPORT / COMPLAINT DOMAIN — 20 queries
    # ══════════════════════════════════════════════════════
    {"id": "P01", "query": "Show me complaint case CMP-2019-1000.", "expected_domain": "support", "expected_terms": ["CMP-2019-1000", "machine", "fault"]},
    {"id": "P02", "query": "What are the most common failure modes reported on machine M01?", "expected_domain": "support", "expected_terms": ["M01", "fault", "failure"]},
    {"id": "P03", "query": "How many RMA cases involved spindle bearing faults?", "expected_domain": "support", "expected_terms": ["RMA", "bearing", "spindle"]},
    {"id": "P04", "query": "What remedy was applied to cases involving tool wear on M02?", "expected_domain": "support", "expected_terms": ["tool", "replace", "M02"]},
    {"id": "P05", "query": "Which customer had the most complaints in 2019?", "expected_domain": "support", "expected_terms": ["customer", "2019", "complaint"]},
    {"id": "P06", "query": "What investigation notes were recorded for chatter vibration cases?", "expected_domain": "support", "expected_terms": ["chatter", "vibration", "investigation"]},
    {"id": "P07", "query": "What is the average resolution time for CRITICAL priority cases?", "expected_domain": "support", "expected_terms": ["critical", "P1", "resolution", "hours"]},
    {"id": "P08", "query": "Which cases have RMA credit issued as YES?", "expected_domain": "support", "expected_terms": ["RMA", "credit", "YES"]},
    {"id": "P09", "query": "What phone call notes were recorded for spindle cooling fan complaints?", "expected_domain": "support", "expected_terms": ["cooling fan", "spindle", "phone"]},
    {"id": "P10", "query": "Show all ESCALATED cases from machine M03.", "expected_domain": "support", "expected_terms": ["ESCALATED", "M03"]},
    {"id": "P11", "query": "What parts were replaced in actuator fault cases?", "expected_domain": "support", "expected_terms": ["actuator", "replace", "parts"]},
    {"id": "P12", "query": "Which cases involved RMA type BEARING RETURN?", "expected_domain": "support", "expected_terms": ["BEARING_RETURN", "bearing", "RMA"]},
    {"id": "P13", "query": "What was the failure mode for cases on Face Milling operation OP01?", "expected_domain": "support", "expected_terms": ["OP01", "Face Milling", "failure"]},
    {"id": "P14", "query": "How many cases were closed vs still in progress?", "expected_domain": "support", "expected_terms": ["CLOSED", "IN_PROGRESS", "cases"]},
    {"id": "P15", "query": "What remedy notes describe spindle bearing replacement?", "expected_domain": "support", "expected_terms": ["bearing", "replaced", "spindle"]},
    {"id": "P16", "query": "Which PLATINUM contract customers had P1 critical cases?", "expected_domain": "support", "expected_terms": ["PLATINUM", "P1", "CRITICAL"]},
    {"id": "P17", "query": "What sensor readings were recorded for spindle bearing fault cases in 2021?", "expected_domain": "support", "expected_terms": ["2021", "spindle", "bearing", "sensor"]},
    {"id": "P18", "query": "Which cases have parts cost above 500 dollars?", "expected_domain": "support", "expected_terms": ["parts", "cost", "500"]},
    {"id": "P19", "query": "What are the investigation findings for chatter vibration on M02?", "expected_domain": "support", "expected_terms": ["chatter", "M02", "investigation"]},
    {"id": "P20", "query": "Show cases where the remedy involved lubricant system repair.", "expected_domain": "support", "expected_terms": ["lubric", "SSV", "distributor"]},

    # ══════════════════════════════════════════════════════
    # CROSS-DOMAIN — 20 queries
    # ══════════════════════════════════════════════════════
    {"id": "X01", "query": "M01 spindle bearing is vibrating and we have an active ATC alarm.", "expected_domain": "cross_domain", "expected_terms": ["spindle", "bearing", "ATC"]},
    {"id": "X02", "query": "What error codes fire when spindle bearing vibration enters Zone C and how have customers responded to this failure?", "expected_domain": "cross_domain", "expected_terms": ["VIB-MJ-001", "Zone C", "complaint"]},
    {"id": "X03", "query": "The coolant pump failed on M02 — what is the error code and are there any prior complaint cases for this?", "expected_domain": "cross_domain", "expected_terms": ["CLS-CR-001", "coolant", "complaint"]},
    {"id": "X04", "query": "What wiring connects the lubrication pump and what error triggers when it fails?", "expected_domain": "cross_domain", "expected_terms": ["LUB", "wiring", "pump"]},
    {"id": "X05", "query": "Customer reports axis following error on M03 — what is the error code and what parts were replaced in similar cases?", "expected_domain": "cross_domain", "expected_terms": ["AXS", "following error", "parts"]},
    {"id": "X06", "query": "What does error SPN-MJ-002 mean and how have field engineers resolved it in past cases?", "expected_domain": "cross_domain", "expected_terms": ["SPN-MJ-002", "bearing", "resolved"]},
    {"id": "X07", "query": "Spindle kurtosis is above 8.0 on M01 — which alarm fires and what do complaint records say about this failure?", "expected_domain": "cross_domain", "expected_terms": ["kurtosis", "SPN", "complaint"]},
    {"id": "X08", "query": "What is the part number for the Z-axis brake and what error triggers when it fails?", "expected_domain": "cross_domain", "expected_terms": ["EIQ-AXS-BRK-Z", "brake", "AXS"]},
    {"id": "X09", "query": "Tool change is taking longer than normal on M02 — what is the error code and what remedy was applied in prior cases?", "expected_domain": "cross_domain", "expected_terms": ["TCS", "tool change", "remedy"]},
    {"id": "X10", "query": "What PLC input monitors the coolant flow switch and what error fires when flow drops?", "expected_domain": "cross_domain", "expected_terms": ["X0.7", "CLS-CR-001", "flow"]},
    {"id": "X11", "query": "Machine M01 has both a spindle temperature alarm and a customer complaint open — what are the details?", "expected_domain": "cross_domain", "expected_terms": ["spindle", "temperature", "M01"]},
    {"id": "X12", "query": "What bearing type is in the VMC-3000 spindle and what error code fires when it fails?", "expected_domain": "cross_domain", "expected_terms": ["7014", "SPN-CR-001", "bearing"]},
    {"id": "X13", "query": "Hydraulic pressure dropped below 60 bar — what is the error code, what is the wiring for the pressure switch, and are there any open cases?", "expected_domain": "cross_domain", "expected_terms": ["HYD-MJ-001", "P050", "pressure"]},
    {"id": "X14", "query": "What is the lubrication cycle interval and what error fires when pressure drops?", "expected_domain": "cross_domain", "expected_terms": ["15 min", "LUB-CR-001", "pressure"]},
    {"id": "X15", "query": "M03 spindle bearing fault in 2021 — what were the sensor readings and what error codes were triggered?", "expected_domain": "cross_domain", "expected_terms": ["M03", "2021", "spindle", "SPN"]},
    {"id": "X16", "query": "What does error VIB-MJ-001 require and have any customers complained about this specific alarm?", "expected_domain": "cross_domain", "expected_terms": ["VIB-MJ-001", "Zone C", "complaint"]},
    {"id": "X17", "query": "DC bus voltage dropped on M01 — what error fires, what is the wiring, and is there an open complaint case?", "expected_domain": "cross_domain", "expected_terms": ["ELC-CR-001", "DC bus", "P090"]},
    {"id": "X18", "query": "What are the diagnostic steps for SPN-SR-003 and what remedies have been applied in field cases?", "expected_domain": "cross_domain", "expected_terms": ["SPN-SR-003", "kurtosis", "bearing"]},
    {"id": "X19", "query": "Coolant temperature is rising on M02 — what error code applies, what is the normal range for P031, and have there been complaints about this?", "expected_domain": "cross_domain", "expected_terms": ["CLS-MJ-001", "P031", "temperature"]},
    {"id": "X20", "query": "What wiring connects the Z-axis over-travel switch and what happens in the control system when it triggers?", "expected_domain": "cross_domain", "expected_terms": ["OT-Z", "EMG-CHAIN", "overtravel"]},
]


def check_terms_in_answer(answer: str, expected_terms: list) -> bool:
    """Check if at least one expected term appears in answer (case-insensitive)."""
    answer_lower = answer.lower()
    for term in expected_terms:
        if term.lower() in answer_lower:
            return True
    return False


def run_tests() -> tuple:
    """Run all 80 queries and return results."""
    try:
        from orchestrator.graph import run_query
    except Exception as e:
        print(f"✗ Failed to import run_query: {e}")
        sys.exit(1)

    results = []
    pass_count = 0
    fail_count = 0

    print("\n" + "=" * 120)
    print("TESTING 80 Q&A PAIRS ACROSS 4 DOMAINS")
    print("=" * 120 + "\n")

    for i, qa in enumerate(QA_PAIRS, 1):
        query_id = qa["id"]
        query_text = qa["query"]
        expected_domain = qa["expected_domain"]
        expected_terms = qa["expected_terms"]

        print(f"[{i:2d}/80] Query {query_id}: ", end="", flush=True)

        try:
            # Run query through orchestrator
            result = run_query(query_text)

            # Extract results
            actual_domain = result.get("domain", "unknown")
            confidence = result.get("confidence", 0.0)
            answer = result.get("final_answer", "")
            chunk_ids = result.get("chunk_ids", [])

            # Check domain accuracy
            domain_match = actual_domain == expected_domain
            domain_check = "✓" if domain_match else "✗"

            # Check answer terms
            terms_match = check_terms_in_answer(answer, expected_terms)
            terms_check = "✓" if terms_match else "✗"

            # Overall result
            overall = "PASS" if (domain_match and terms_match) else "FAIL"
            if overall == "PASS":
                pass_count += 1
            else:
                fail_count += 1

            result_entry = {
                "id": query_id,
                "expected_domain": expected_domain,
                "actual_domain": actual_domain,
                "confidence": confidence,
                "domain_match": domain_match,
                "terms_match": terms_match,
                "overall": overall,
                "answer": answer,
                "chunk_ids": chunk_ids,
            }
            results.append(result_entry)

            print(f"{overall}")

        except Exception as e:
            print(f"ERROR: {str(e)[:50]}")
            result_entry = {
                "id": query_id,
                "expected_domain": expected_domain,
                "actual_domain": "error",
                "confidence": 0.0,
                "domain_match": False,
                "terms_match": False,
                "overall": "ERROR",
                "answer": f"Exception: {str(e)}",
                "chunk_ids": [],
            }
            results.append(result_entry)
            fail_count += 1

    return results, pass_count, fail_count


def print_summary_table(results: list) -> None:
    """Print results table."""
    print("\n" + "=" * 160)
    print("RESULTS TABLE")
    print("=" * 160)
    print(f"{'ID':<5} {'Expected':<12} {'Actual':<12} {'Conf':<6} {'Domain':<7} {'Terms':<7} {'Overall':<8}")
    print("-" * 160)

    for r in results:
        conf_str = f"{r['confidence']:.0%}"
        print(
            f"{r['id']:<5} {r['expected_domain']:<12} {r['actual_domain']:<12} "
            f"{conf_str:<6} {r['domain_match']:<7} {r['terms_match']:<7} {r['overall']:<8}"
        )


def print_section_a(pass_count: int, fail_count: int) -> None:
    """Print overall score section."""
    total = pass_count + fail_count
    percentage = (pass_count / total * 100) if total > 0 else 0
    print("\n" + "=" * 120)
    print("SECTION A — OVERALL SCORE")
    print("=" * 120)
    print(f"✓ PASS:  {pass_count}/{total} ({percentage:.1f}%)")
    print(f"✗ FAIL:  {fail_count}/{total} ({100-percentage:.1f}%)")


def print_section_b(results: list) -> None:
    """Print domain accuracy per category."""
    domains = {
        "mechanical": [r for r in results if r["id"].startswith("M")],
        "software": [r for r in results if r["id"].startswith("S")],
        "support": [r for r in results if r["id"].startswith("P")],
        "cross_domain": [r for r in results if r["id"].startswith("X")],
    }

    print("\n" + "=" * 120)
    print("SECTION B — DOMAIN ACCURACY PER CATEGORY")
    print("=" * 120)

    for domain_name, domain_results in domains.items():
        pass_count = sum(1 for r in domain_results if r["overall"] == "PASS")
        total = len(domain_results)
        percentage = (pass_count / total * 100) if total > 0 else 0
        status = "✓" if percentage >= 80 else "✗"
        print(
            f"{status} {domain_name.upper():<15} {pass_count:2d}/{total:2d} ({percentage:5.1f}%)"
        )


def print_section_c(results: list) -> None:
    """Print failing queries grouped by failure type."""
    failures = [r for r in results if r["overall"] != "PASS"]

    if not failures:
        print("\n" + "=" * 120)
        print("SECTION C — FAILING QUERIES")
        print("=" * 120)
        print("✓ No failures — all queries passed!")
        return

    # Categorize failures
    routing_failures = [
        r for r in failures if not r["domain_match"]
    ]
    retrieval_failures = [
        r for r in failures if r["domain_match"] and not r["terms_match"] and r["overall"] != "ERROR"
    ]
    errors = [r for r in failures if r["overall"] == "ERROR"]

    print("\n" + "=" * 120)
    print("SECTION C — FAILING QUERIES BY TYPE")
    print("=" * 120)

    # Routing failures
    if routing_failures:
        print(f"\n[ROUTING FAILURE] — {len(routing_failures)} queries")
        print("-" * 120)
        for r in routing_failures:
            print(f"  {r['id']:<5} Expected: {r['expected_domain']:<15} Actual: {r['actual_domain']:<15} (Conf: {r['confidence']:.0%})")

    # Retrieval/synthesis failures
    if retrieval_failures:
        print(f"\n[RETRIEVAL/SYNTHESIS FAILURE] — {len(retrieval_failures)} queries (right domain, wrong answer)")
        print("-" * 120)
        for r in retrieval_failures:
            short_answer = r["answer"][:80] + "..." if len(r["answer"]) > 80 else r["answer"]
            print(f"  {r['id']:<5} Answer preview: {short_answer}")

    # Errors
    if errors:
        print(f"\n[ERROR] — {len(errors)} queries")
        print("-" * 120)
        for r in errors:
            print(f"  {r['id']:<5} Error: {r['answer']}")


def print_section_d(results: list) -> None:
    """Print recommendations for fixes."""
    failures = [r for r in results if r["overall"] != "PASS"]

    if not failures:
        return

    print("\n" + "=" * 120)
    print("SECTION D — RECOMMENDATIONS FOR FIXES")
    print("=" * 120)

    for r in failures:
        if not r["domain_match"]:
            fix_type = "PROMPT EXAMPLES NEEDED (routing failure)"
        elif r["overall"] == "ERROR":
            fix_type = "INFRASTRUCTURE FIX NEEDED (API/import error)"
        else:
            fix_type = "GOLDEN SET ENTRY NEEDED or RE-INGESTION (coverage/retrieval gap)"

        print(f"{r['id']:<5} {fix_type:<50} — {r['expected_domain']}")


def save_results_json(results: list, pass_count: int, fail_count: int) -> str:
    """Save results to JSON file."""
    results_dir = PROJECT_ROOT / "evaluation" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d")
    filepath = results_dir / f"domain_qa_test_{timestamp}.json"

    output = {
        "timestamp": datetime.now().isoformat(),
        "total_queries": len(results),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass_percentage": (pass_count / len(results) * 100) if results else 0,
        "results": results,
    }

    with open(filepath, "w") as f:
        json.dump(output, f, indent=2)

    return str(filepath)


def main():
    """Run test suite and print all output."""
    results, pass_count, fail_count = run_tests()

    print_summary_table(results)
    print_section_a(pass_count, fail_count)
    print_section_b(results)
    print_section_c(results)
    print_section_d(results)

    # Save to JSON
    filepath = save_results_json(results, pass_count, fail_count)
    print("\n" + "=" * 120)
    print(f"✓ Results saved to: {filepath}")
    print("=" * 120 + "\n")

    # Exit code
    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
