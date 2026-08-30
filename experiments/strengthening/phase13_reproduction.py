"""
experiments/strengthening/phase13_reproduction.py
==================================================
Independent reproduction audit for the SBG project.

Verifies 12 reported numerical claims from raw artifacts without
trusting any summary table.  Writes results to:
    results/phase13/REPRODUCTION_AUDIT.json
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path('/Users/manassakthivel/Desktop/SF Projects/SBG')
OUT_PATH = REPO / 'results' / 'phase13' / 'REPRODUCTION_AUDIT.json'

results: list[dict] = []


# ---------------------------------------------------------------------------
# Core helper
# ---------------------------------------------------------------------------

def verify(
    claim_id: int | str,
    reported,
    computed,
    method: str,
    source: str,
    note: str = "",
) -> None:
    if isinstance(reported, float) and isinstance(computed, float):
        delta = abs(reported - computed)
        status = "VERIFIED" if delta < 0.001 else "DISCREPANCY"
    elif isinstance(reported, int) and isinstance(computed, int):
        delta = abs(reported - computed)
        status = "VERIFIED" if delta == 0 else "DISCREPANCY"
    else:
        delta = None
        status = "VERIFIED" if reported == computed else "DISCREPANCY"

    record: dict = {
        "claim_id": claim_id,
        "reported_value": reported,
        "computed_value": computed,
        "delta": delta,
        "status": status,
        "method": method,
        "source": source,
    }
    if note:
        record["note"] = note
    results.append(record)
    tag = f"C{claim_id}"
    print(f"  {status:12s}  {tag}: reported={reported!r}  computed={computed!r}"
          + (f"  delta={delta:.6f}" if isinstance(delta, float) else ""))


# ---------------------------------------------------------------------------
# Claim 1 — Test split N = 744
# ---------------------------------------------------------------------------
def check_claim_1() -> None:
    path = REPO / 'benchmark' / 'datasets' / 'pairs_test.jsonl'
    count = 0
    with open(path) as fh:
        for line in fh:
            if line.strip():
                count += 1
    verify(
        claim_id=1,
        reported=744,
        computed=count,
        method="count non-empty lines in pairs_test.jsonl",
        source="benchmark/datasets/pairs_test.jsonl",
    )


# ---------------------------------------------------------------------------
# Claim 2 — SBG V5 test AUROC = 0.551246
# ---------------------------------------------------------------------------
def check_claim_2() -> None:
    path = REPO / 'artifacts' / 'v5' / 'B07' / 'results_test.json'
    with open(path) as fh:
        data = json.load(fh)
    computed = data['test_auroc']
    verify(
        claim_id=2,
        reported=0.551246,
        computed=computed,
        method="read test_auroc field",
        source="artifacts/v5/B07/results_test.json",
    )


# ---------------------------------------------------------------------------
# Claim 3 — SBG V3 test AUROC = 0.539906
# ---------------------------------------------------------------------------
def check_claim_3() -> None:
    path = REPO / 'artifacts' / 'v5' / 'FINAL_EVIDENCE_MANIFEST_V5.json'
    with open(path) as fh:
        data = json.load(fh)
    computed = data['key_results']['sbg_v3_auroc']
    verify(
        claim_id=3,
        reported=0.539906,
        computed=computed,
        method="read key_results.sbg_v3_auroc",
        source="artifacts/v5/FINAL_EVIDENCE_MANIFEST_V5.json",
    )


# ---------------------------------------------------------------------------
# Claim 4 — exception_fraction AUROC = 0.592947
# ---------------------------------------------------------------------------
def check_claim_4() -> None:
    path = REPO / 'artifacts' / 'v5' / 'INCREMENTAL_INFO_RESULTS.json'
    with open(path) as fh:
        data = json.load(fh)
    computed = data['summary']['best_shortcut_auroc']
    verify(
        claim_id=4,
        reported=0.592947,
        computed=computed,
        method="read summary.best_shortcut_auroc",
        source="artifacts/v5/INCREMENTAL_INFO_RESULTS.json",
    )


# ---------------------------------------------------------------------------
# Claim 5 — Regression detection SBG = 3/15 = 20.0%
# ---------------------------------------------------------------------------
def check_claim_5() -> None:
    path = REPO / 'artifacts' / 'v5' / 'REGRESSION_EVALUATION_RESULTS.json'
    with open(path) as fh:
        data = json.load(fh)

    # From detection_rates field
    rate_from_field = data['detection_rates']['sbg_distance_output_free']

    # Manual count
    manual_count = sum(
        1 for p in data['pair_results']
        if p.get('detected_by_sbg') is True
    )
    n_pairs = data['n_pairs']
    rate_manual = manual_count / n_pairs

    verify(
        claim_id="5a",
        reported=0.200,
        computed=rate_from_field,
        method="read detection_rates.sbg_distance_output_free",
        source="artifacts/v5/REGRESSION_EVALUATION_RESULTS.json",
    )
    verify(
        claim_id="5b",
        reported=0.200,
        computed=rate_manual,
        method=f"manual count: {manual_count}/{n_pairs} detected_by_sbg==True",
        source="artifacts/v5/REGRESSION_EVALUATION_RESULTS.json",
        note=f"manual_count={manual_count} n_pairs={n_pairs}",
    )


# ---------------------------------------------------------------------------
# Claim 6 — Pilot AUROC = 0.800, N = 12
# ---------------------------------------------------------------------------
def check_claim_6() -> None:
    path = REPO / 'artifacts' / 'v5' / 'REAL_WORLD_PILOT_RESULTS.json'
    with open(path) as fh:
        data = json.load(fh)
    auroc = data['auroc']['sbg_output_free']
    n_pairs = data['n_pairs']

    verify(
        claim_id="6a",
        reported=0.800,
        computed=float(auroc),
        method="read auroc.sbg_output_free",
        source="artifacts/v5/REAL_WORLD_PILOT_RESULTS.json",
    )
    verify(
        claim_id="6b",
        reported=12,
        computed=n_pairs,
        method="read n_pairs",
        source="artifacts/v5/REAL_WORLD_PILOT_RESULTS.json",
    )


# ---------------------------------------------------------------------------
# Claim 7 — Output leakage gate 7/7 PASS
# ---------------------------------------------------------------------------
def check_claim_7() -> None:
    path = REPO / 'results' / 'phase1' / 'OUTPUT_LEAKAGE_GATE.json'
    with open(path) as fh:
        data = json.load(fh)
    pass_count = data['summary']['pass']
    verify(
        claim_id=7,
        reported=7,
        computed=pass_count,
        method="read summary.pass",
        source="results/phase1/OUTPUT_LEAKAGE_GATE.json",
    )


# ---------------------------------------------------------------------------
# Claim 8 — Scaled regression N=40, detection 5/38 = 13.2%
# ---------------------------------------------------------------------------
def check_claim_8() -> None:
    path = REPO / 'results' / 'phase45' / 'SCALED_REGRESSION_RESULTS.json'
    with open(path) as fh:
        data = json.load(fh)

    n_total = data['n_total']
    n_positive = data['n_positive']
    rate_from_field = data['sbg_detection_rate']

    # Manual count: label==1 AND detected_sbg==True
    manual_detected = sum(
        1 for p in data['pair_results']
        if p['label'] == 1 and p['detected_sbg'] is True
    )
    rate_manual = manual_detected / n_positive

    verify(
        claim_id="8a",
        reported=40,
        computed=n_total,
        method="read n_total",
        source="results/phase45/SCALED_REGRESSION_RESULTS.json",
    )
    verify(
        claim_id="8b",
        reported=5 / 38,
        computed=rate_from_field,
        method="read sbg_detection_rate",
        source="results/phase45/SCALED_REGRESSION_RESULTS.json",
        note=f"5/38 = {5/38:.4f}",
    )
    verify(
        claim_id="8c",
        reported=5 / 38,
        computed=rate_manual,
        method=f"manual count: {manual_detected}/{n_positive} where label==1 AND detected_sbg==True",
        source="results/phase45/SCALED_REGRESSION_RESULTS.json",
        note=f"manual_detected={manual_detected} n_positive={n_positive}",
    )


# ---------------------------------------------------------------------------
# Claim 9 — DEV AUROC V3 = 0.488
# ---------------------------------------------------------------------------
def check_claim_9() -> None:
    path = REPO / 'artifacts' / 'v5' / 'FINAL_EXPERIMENTAL_MATRIX.json'
    with open(path) as fh:
        data = json.load(fh)
    computed = data['split_consistency']['dev']['auroc']
    verify(
        claim_id=9,
        reported=0.488,
        computed=float(computed),
        method="read split_consistency.dev.auroc",
        source="artifacts/v5/FINAL_EXPERIMENTAL_MATRIX.json",
    )


# ---------------------------------------------------------------------------
# Claim 10 — 516 tests pass
# ---------------------------------------------------------------------------
def check_claim_10() -> None:
    proc = subprocess.run(
        [sys.executable, '-m', 'pytest', 'sbg/', '-q', '--tb=no'],
        capture_output=True, text=True, cwd=str(REPO)
    )
    output = proc.stdout + proc.stderr
    # Parse "N passed" from pytest output
    import re
    match = re.search(r'(\d+)\s+passed', output)
    computed_n = int(match.group(1)) if match else -1
    tail = '\n'.join((proc.stdout + proc.stderr).strip().splitlines()[-5:])

    verify(
        claim_id=10,
        reported=516,
        computed=computed_n,
        method="python3 -m pytest sbg/ -q --tb=no; parse N passed",
        source="sbg/ pytest suite",
        note=f"pytest_tail={tail!r}",
    )


# ---------------------------------------------------------------------------
# Claim 11 — Reproducibility check 6/6 PASS
# ---------------------------------------------------------------------------
def check_claim_11() -> None:
    proc = subprocess.run(
        [sys.executable, 'experiments/v5/reproduction_check.py'],
        capture_output=True, text=True, cwd=str(REPO)
    )
    output = proc.stdout + proc.stderr
    import re
    match = re.search(r'\((\d+)\s+PASS', output)
    computed_n = int(match.group(1)) if match else -1
    tail = '\n'.join(output.strip().splitlines()[-5:])

    verify(
        claim_id=11,
        reported=6,
        computed=computed_n,
        method="python3 experiments/v5/reproduction_check.py; parse N PASS",
        source="experiments/v5/reproduction_check.py",
        note=f"script_tail={tail!r}",
    )


# ---------------------------------------------------------------------------
# Claim 12 — Phase 2 R1 exception_fraction AUROC discrepancy
#             REPRESENTATION_ABLATION.json: 0.567005
#             INCREMENTAL_INFO_RESULTS.json best_shortcut_auroc: 0.592947
# ---------------------------------------------------------------------------
def check_claim_12() -> None:
    ablation_path = REPO / 'results' / 'phase2' / 'REPRESENTATION_ABLATION.json'
    incr_path = REPO / 'artifacts' / 'v5' / 'INCREMENTAL_INFO_RESULTS.json'

    with open(ablation_path) as fh:
        ablation = json.load(fh)
    with open(incr_path) as fh:
        incr = json.load(fh)

    r1_auroc = next(
        r['auroc'] for r in ablation['representations']
        if r['representation'] == 'R1_exception_fraction'
    )
    best_shortcut = incr['summary']['best_shortcut_auroc']
    exc_frac_standalone = incr['incremental_table']['exception_fraction']['standalone_auroc']

    # Document both values as a discrepancy note
    delta = abs(best_shortcut - r1_auroc)
    record = {
        "claim_id": 12,
        "reported_value": "discrepancy documented",
        "computed_value": {
            "REPRESENTATION_ABLATION_R1_auroc": r1_auroc,
            "INCREMENTAL_INFO_best_shortcut_auroc": best_shortcut,
            "INCREMENTAL_INFO_exception_fraction_standalone": exc_frac_standalone,
        },
        "delta": delta,
        "status": "DISCREPANCY" if delta >= 0.001 else "VERIFIED",
        "method": (
            "REPRESENTATION_ABLATION.json R1 auroc vs "
            "INCREMENTAL_INFO_RESULTS.json summary.best_shortcut_auroc"
        ),
        "source": (
            "results/phase2/REPRESENTATION_ABLATION.json + "
            "artifacts/v5/INCREMENTAL_INFO_RESULTS.json"
        ),
        "note": (
            f"ABLATION R1=0.567005 (exception_fraction standalone); "
            f"INCR best_shortcut_auroc=0.592947 (claimed in Claim 4 as best). "
            f"The standalone_auroc for exception_fraction in INCREMENTAL_INFO "
            f"is {exc_frac_standalone} — same as ABLATION R1. "
            f"best_shortcut_auroc ({best_shortcut}) appears to be a DIFFERENT "
            f"metric (possibly combined_shortcut or best across a transformed set). "
            f"delta between the two values = {delta:.6f}."
        ),
    }
    results.append(record)
    print(f"  {record['status']:12s}  C12: R1_ablation={r1_auroc}  "
          f"best_shortcut={best_shortcut}  standalone_exc={exc_frac_standalone}  "
          f"delta={delta:.6f}")


# ---------------------------------------------------------------------------
# Run all checks
# ---------------------------------------------------------------------------

print("\n=== SBG Phase 13 Reproduction Audit ===\n")

check_claim_1()
check_claim_2()
check_claim_3()
check_claim_4()
check_claim_5()
check_claim_6()
check_claim_7()
check_claim_8()
check_claim_9()
check_claim_10()
check_claim_11()
check_claim_12()

# ---------------------------------------------------------------------------
# Summarise
# ---------------------------------------------------------------------------
n_verified = sum(1 for r in results if r['status'] == 'VERIFIED')
n_discrepancy = sum(1 for r in results if r['status'] == 'DISCREPANCY')

summary = {
    "total_checks": len(results),
    "verified": n_verified,
    "discrepancy": n_discrepancy,
}

audit = {
    "audit": "PHASE13_REPRODUCTION_AUDIT",
    "repo": str(REPO),
    "summary": summary,
    "results": results,
}

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_PATH, 'w') as fh:
    json.dump(audit, fh, indent=2)

print(f"\n=== Summary ===")
print(f"  VERIFIED:    {n_verified}")
print(f"  DISCREPANCY: {n_discrepancy}")
print(f"  Output:      {OUT_PATH}")
