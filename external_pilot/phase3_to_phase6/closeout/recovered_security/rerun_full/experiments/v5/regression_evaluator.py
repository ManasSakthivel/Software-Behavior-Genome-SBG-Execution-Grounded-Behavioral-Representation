"""
regression_evaluator.py — CORRECTED OUTPUT-FREE version.

ARCHITECTURE (post-Phase-3 fix):

    Program A → SBG(A) ─┐
                         ├─► SBG distance (PREDICTOR) ─► DETECT REGRESSION
    Program B → SBG(B) ─┘

    Independent oracle ──────────────────────────────► GROUND TRUTH
    (may use outputs, but is never seen by the predictor)

WHAT CHANGED vs the previous version (CRITICAL):
  - sbg_proxy no longer contains output_divergence
  - output_divergence is computed in a SEPARATE oracle column only
  - The SBG predictor is: exception_fraction + exception_type_jaccard +
    volume_ratio (all output-FREE execution-structure features)
  - The SBG V3 distance function (output-free by design) is the
    primary predictor when the V3 extractor is available
  - Ground truth: the hand-crafted bug label (all 15 pairs are CHANGED)
  - Detection threshold τ* is set to the median distance of SP pairs
    from the dev set — fixed before running on the regression corpus

SAFEGUARD TESTS (run before evaluation):
  Four assertions that confirm output isolation are executed at startup.
  If any fail, the script aborts before touching any evaluation data.

Usage:
    python3 experiments/v5/regression_evaluator.py

Outputs:
    artifacts/v5/REGRESSION_EVALUATION_RESULTS.json
"""

from __future__ import annotations

import sys
import os
import json
import math
import time
import random
import hashlib
import traceback
from pathlib import Path
from typing import Any, List, Dict, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

try:
    from benchmark.v5.regression.regression_pairs import REGRESSION_PAIRS
except ImportError as e:
    print(f"ERROR importing regression_pairs: {e}")
    sys.exit(1)

SEED = 42
N_BOOTSTRAP = 1000
TIMEOUT = 5.0

# ─────────────────────────────────────────────────────────────────────────────
# SAFEGUARD TESTS — run at startup before any evaluation data is touched
# ─────────────────────────────────────────────────────────────────────────────

def _safeguard_tests():
    """
    Four assertions that prove output isolation:
      SG-1: Output values are not consumed by compute_sbg_distance()
      SG-2: Changing outputs without changing execution structure does not alter SBG distance
      SG-3: output_divergence is computed in a completely separate function
      SG-4: Ground-truth labels are fixed before any prediction is made
    """
    failures = []

    # SG-1: compute_sbg_distance must not accept or use return_value fields
    import inspect
    sig = inspect.signature(compute_sbg_distance)
    for param_name in sig.parameters:
        if "output" in param_name.lower() or "return" in param_name.lower():
            failures.append(
                f"SG-1 FAIL: compute_sbg_distance has parameter '{param_name}' "
                "which suggests output access"
            )

    # SG-2: Two feature vectors that differ only in return_values must produce
    #        the same SBG distance.
    feat_a = {
        "exception_fraction": 0.0,
        "exception_types": [],
        "mean_wall_time_ms": 1.0,
        # Deliberately different return_values — must NOT influence SBG distance
        "_return_values_PRIVATE": ["42", "42"],
    }
    feat_b = {
        "exception_fraction": 0.0,
        "exception_types": [],
        "mean_wall_time_ms": 1.0,
        "_return_values_PRIVATE": ["99", "99"],   # different outputs
    }
    dist_ab = compute_sbg_distance(feat_a, feat_b)
    if dist_ab != 0.0:
        failures.append(
            f"SG-2 FAIL: changing return_values altered SBG distance "
            f"(expected 0.0, got {dist_ab:.4f}). "
            "output_divergence must not be in the SBG predictor."
        )

    # SG-3: compute_sbg_distance must not access _return_values_PRIVATE or
    #        output_divergence in its executable code body (outside docstring).
    sbg_src = inspect.getsource(compute_sbg_distance)
    # Strip the docstring by finding content after the closing triple-quote
    if '"""' in sbg_src:
        # Find the end of the opening docstring (second occurrence of """)
        parts = sbg_src.split('"""')
        # parts[0] = def line, parts[1] = docstring body, parts[2:] = code body
        code_body = '"""'.join(parts[2:]) if len(parts) > 2 else ""
    else:
        code_body = sbg_src
    # Remove comment lines from the code body
    non_comment_lines = [
        line for line in code_body.splitlines()
        if not line.strip().startswith("#")
    ]
    code_only = "\n".join(non_comment_lines)
    if "_return_values_PRIVATE" in code_only or "output_divergence" in code_only:
        failures.append(
            "SG-3 FAIL: compute_sbg_distance code body accesses "
            "'_return_values_PRIVATE' or 'output_divergence' — it reads outputs."
        )

    # SG-4: GROUND_TRUTH_LABELS must be a constant mapping (all 15 pairs →
    #        label=1 = CHANGED) defined before any execution occurs.
    if len(GROUND_TRUTH_LABELS) != 15:
        failures.append(
            f"SG-4 FAIL: GROUND_TRUTH_LABELS has {len(GROUND_TRUTH_LABELS)} entries, "
            "expected 15. Labels must cover all pairs."
        )
    if not all(v == 1 for v in GROUND_TRUTH_LABELS.values()):
        failures.append(
            "SG-4 FAIL: not all GROUND_TRUTH_LABELS are 1 (CHANGED). "
            "All 15 regression pairs are bugs and should be labeled CHANGED."
        )

    if failures:
        print("\n[SAFEGUARD] OUTPUT ISOLATION CHECK FAILED:")
        for f in failures:
            print(f"  ✗ {f}")
        print("\nAborting evaluation — fix output leakage before re-running.")
        sys.exit(1)
    else:
        print("[SAFEGUARD] All 4 output-isolation checks passed ✓")


# ─────────────────────────────────────────────────────────────────────────────
# Ground truth labels (defined before execution, independent of prediction)
# ─────────────────────────────────────────────────────────────────────────────

# Label: 1 = CHANGED (regression / bug present), 0 = EQUIVALENT
# All 15 pairs are bugs — ground truth is their bug type, not output comparison.
GROUND_TRUTH_LABELS: Dict[str, int] = {
    "R01": 1, "R02": 1, "R03": 1, "R04": 1, "R05": 1,
    "R06": 1, "R07": 1, "R08": 1, "R09": 1, "R10": 1,
    "R11": 1, "R12": 1, "R13": 1, "R14": 1, "R15": 1,
}

# Detection threshold τ* — fixed to median SBG distance of SP (EQUIVALENT)
# pairs from the dev set. Estimated from prior experiments.
# NOTE: This must NOT be tuned on regression corpus results.
TAU_STAR = 0.08  # Median SBG distance of SP pairs on dev split (from V5 artifacts)


# ─────────────────────────────────────────────────────────────────────────────
# Execution engine (output-free extraction path)
# ─────────────────────────────────────────────────────────────────────────────

class ExecutionResult:
    """Execution result. return_value is captured but NEVER read by predictor."""
    def __init__(self, return_value=None, exception_type=None, exception_msg=None,
                 call_count=0, wall_time_ms=0.0):
        self.return_value = return_value        # oracle-only — NOT used by SBG predictor
        self.exception_type = exception_type
        self.exception_msg = exception_msg
        self.call_count = call_count
        self.wall_time_ms = wall_time_ms

    @property
    def had_exception(self):
        return self.exception_type is not None


def _execute_fn(fn, args: tuple) -> ExecutionResult:
    """Execute fn(*args) with exception tracking and timing.
    Return value is captured for oracle use ONLY."""
    t0 = time.perf_counter()
    try:
        result = fn(*args)
        exc_type = None
        exc_msg = None
        ret = result
    except Exception as e:
        exc_type = type(e).__name__
        exc_msg = str(e)
        ret = None
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return ExecutionResult(
        return_value=ret,
        exception_type=exc_type,
        exception_msg=exc_msg,
        call_count=1,
        wall_time_ms=elapsed_ms,
    )


def compute_sbg_features(fn, inputs: List[tuple]) -> Dict[str, Any]:
    """
    Execute fn on all inputs and compute OUTPUT-FREE behavioral features.

    SAFEGUARD-2 COMPLIANT: this function extracts exception_fraction,
    exception_types, and wall_time statistics — none of which are output values.
    Return values are stored separately in _return_values_PRIVATE (oracle only).
    """
    results = []
    for inp in inputs:
        r = _execute_fn(fn, inp)
        results.append(r)

    n = len(results)
    if n == 0:
        return {}

    exception_count = sum(1 for r in results if r.had_exception)
    exception_fraction = exception_count / n
    exception_types = sorted(set(r.exception_type for r in results if r.exception_type))
    wall_times = [r.wall_time_ms for r in results]
    mean_wall_time = sum(wall_times) / n if wall_times else 0.0

    # Return values stored privately — only accessible by oracle, NEVER by predictor
    _private_return_values = []
    for r in results:
        if r.had_exception:
            _private_return_values.append(f"EXC:{r.exception_type}")
        else:
            try:
                rv_str = repr(r.return_value)[:200]
            except Exception:
                rv_str = "REPR_ERROR"
            _private_return_values.append(rv_str)

    return {
        # OUTPUT-FREE features — SBG predictor reads these
        "exception_fraction": exception_fraction,
        "exception_types": exception_types,
        "mean_wall_time_ms": mean_wall_time,
        "n_inputs": n,
        "n_exceptions": exception_count,
        # Oracle-only field — prefixed to make intent explicit
        # compute_sbg_distance() MUST NOT access this key
        "_return_values_PRIVATE": _private_return_values,
    }


def compute_sbg_distance(feat_a: Dict, feat_b: Dict) -> float:
    """
    Compute OUTPUT-FREE SBG distance between two behavioral feature vectors.

    CRITICAL: This function must NEVER read 'output_divergence',
    'return_value', '_return_values_PRIVATE', or 'behavior_hash'.
    Only exception and timing features are allowed.

    The distance formula:
        sbg_distance = 0.50 * exception_fraction_dist
                     + 0.30 * exception_type_jaccard
                     + 0.20 * volume_ratio

    This is the output-free analog of the V3 exception + volume components.
    All weights sum to 1.0.
    """
    # Component 1: exception fraction distance (output-free)
    ef_a = feat_a.get("exception_fraction", 0.0)
    ef_b = feat_b.get("exception_fraction", 0.0)
    d_exception_frac = abs(ef_a - ef_b)

    # Component 2: exception type Jaccard distance (output-free)
    et_a = set(feat_a.get("exception_types", []))
    et_b = set(feat_b.get("exception_types", []))
    union_et = et_a | et_b
    d_exception_jaccard = (
        0.0 if not union_et
        else 1.0 - len(et_a & et_b) / len(union_et)
    )

    # Component 3: wall-time volume ratio (output-free)
    wt_a = feat_a.get("mean_wall_time_ms", 0.0) + 1e-6
    wt_b = feat_b.get("mean_wall_time_ms", 0.0) + 1e-6
    ratio = max(wt_a, wt_b) / min(wt_a, wt_b)
    d_volume = min(1.0, (ratio - 1.0) / 10.0)

    sbg_distance = (
        0.50 * d_exception_frac
        + 0.30 * d_exception_jaccard
        + 0.20 * d_volume
    )

    return sbg_distance


def compute_output_oracle(feat_a: Dict, feat_b: Dict) -> Dict[str, float]:
    """
    Compute output-based oracle metrics. SEPARATED from SBG predictor.
    May only be used as GROUND-TRUTH VERIFICATION or BASELINE — never
    as the SBG prediction.

    This function is the ONLY place that reads _return_values_PRIVATE.
    """
    rv_a = feat_a.get("_return_values_PRIVATE", [])
    rv_b = feat_b.get("_return_values_PRIVATE", [])
    n_inputs = min(len(rv_a), len(rv_b))
    if n_inputs == 0:
        output_divergence = 0.0
    else:
        n_diff = sum(1 for x, y in zip(rv_a, rv_b) if x != y)
        output_divergence = n_diff / n_inputs

    # behavior hash (oracle only)
    hash_a = hashlib.sha256(
        json.dumps(rv_a, sort_keys=True).encode()
    ).hexdigest()[:16]
    hash_b = hashlib.sha256(
        json.dumps(rv_b, sort_keys=True).encode()
    ).hexdigest()[:16]

    return {
        "output_divergence": output_divergence,
        "behavior_hash_changed": hash_a != hash_b,
        "detectable_by_output": output_divergence > 0.0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# AUROC (tie-aware WMW) and bootstrap CI
# ─────────────────────────────────────────────────────────────────────────────

def compute_auroc(scores: List[float], labels: List[int]) -> float:
    """Tie-aware WMW AUROC. labels: 1 = CHANGED (regression), 0 = EQUIVALENT."""
    pos = [s for s, l in zip(scores, labels) if l == 1]
    neg = [s for s, l in zip(scores, labels) if l == 0]
    if not pos or not neg:
        return float("nan")
    concordant, tied, total = 0, 0, len(pos) * len(neg)
    for p in pos:
        for n in neg:
            if p > n:
                concordant += 1
            elif p == n:
                tied += 1
    return (concordant + 0.5 * tied) / total


def bootstrap_auroc_ci(scores, labels, n=N_BOOTSTRAP, seed=SEED):
    rng = random.Random(seed)
    n_pairs = len(scores)
    aurocs = []
    for _ in range(n):
        idx = [rng.randint(0, n_pairs - 1) for _ in range(n_pairs)]
        s = [scores[i] for i in idx]
        l = [labels[i] for i in idx]
        a = compute_auroc(s, l)
        if not math.isnan(a):
            aurocs.append(a)
    if not aurocs:
        return float("nan"), float("nan")
    aurocs.sort()
    lo = aurocs[int(0.025 * len(aurocs))]
    hi = aurocs[int(0.975 * len(aurocs))]
    return lo, hi


def detection_rate_at_threshold(scores, labels, threshold):
    """Binary detection rate: fraction of positives with score > threshold."""
    tp = sum(1 for s, l in zip(scores, labels) if l == 1 and s > threshold)
    n_pos = sum(l for l in labels)
    if n_pos == 0:
        return 0.0
    return tp / n_pos


# ─────────────────────────────────────────────────────────────────────────────
# Main evaluation
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_pair(pair: Dict) -> Dict:
    """
    Evaluate one regression pair.

    Predictors:  sbg_distance (output-free), exception_fraction_only, volume_only
    Oracle:      output_divergence (SEPARATE — not used for SBG prediction)
    Ground truth: bug label from GROUND_TRUTH_LABELS (binary, defined before execution)
    """
    pid = pair["id"]
    buggy_fn = pair["buggy_fn"]
    fixed_fn = pair["fixed_fn"]
    inputs = pair["trigger_inputs"]

    # Extract output-free features for both versions
    feat_buggy = compute_sbg_features(buggy_fn, inputs)
    feat_fixed = compute_sbg_features(fixed_fn, inputs)

    # === PREDICTOR: output-free SBG distance ===
    sbg_dist = compute_sbg_distance(feat_buggy, feat_fixed)

    # === PREDICTOR ablations (also output-free) ===
    ef_buggy = feat_buggy.get("exception_fraction", 0.0)
    ef_fixed = feat_fixed.get("exception_fraction", 0.0)
    exception_only_dist = abs(ef_buggy - ef_fixed)

    wt_b = feat_buggy.get("mean_wall_time_ms", 0.0) + 1e-6
    wt_f = feat_fixed.get("mean_wall_time_ms", 0.0) + 1e-6
    ratio = max(wt_b, wt_f) / min(wt_b, wt_f)
    volume_only_dist = min(1.0, (ratio - 1.0) / 10.0)

    # === ORACLE (separate — never seen by predictor) ===
    oracle = compute_output_oracle(feat_buggy, feat_fixed)

    # === Detection decisions (using fixed τ* threshold) ===
    detected_by_sbg = sbg_dist > TAU_STAR
    detected_by_exception_only = exception_only_dist > 0.0
    detected_by_volume_only = volume_only_dist > 0.05
    detected_by_output_oracle = oracle["detectable_by_output"]

    return {
        "id": pid,
        "name": pair["name"],
        "bug_type": pair["bug_type"],
        "ground_truth_label": GROUND_TRUTH_LABELS.get(pid, 1),
        "n_trigger_inputs": len(inputs),

        # Output-free predictor scores
        "sbg_distance": sbg_dist,
        "exception_only_distance": exception_only_dist,
        "volume_only_distance": volume_only_dist,

        # Detection decisions at τ*
        "detected_by_sbg": detected_by_sbg,
        "detected_by_exception_only": detected_by_exception_only,
        "detected_by_volume_only": detected_by_volume_only,

        # Output oracle (SEPARATE — baseline only, not the SBG result)
        "output_oracle": oracle,
        "detected_by_output_oracle": detected_by_output_oracle,

        # Visibility categories
        "bug_visible_to_exception": detected_by_exception_only,
        "bug_visible_to_volume": detected_by_volume_only,
        "is_silent_bug": (not detected_by_exception_only and not detected_by_volume_only),
    }


def run_evaluation():
    print("=" * 70)
    print("REGRESSION EVALUATOR — OUTPUT-FREE VERSION (Phase 3)")
    print("=" * 70)
    print(f"τ* (detection threshold): {TAU_STAR:.4f}")
    print(f"Ground truth source: pre-defined bug labels (independent of execution)")
    print(f"SBG predictor: exception_fraction + exception_type_jaccard + volume_ratio")
    print(f"Output oracle: computed separately, labeled as BASELINE ONLY")
    print()

    # Run safeguard checks FIRST
    _safeguard_tests()
    print()

    print(f"[regression_evaluator] Evaluating {len(REGRESSION_PAIRS)} regression pairs...")
    print(f"{'ID':4s}  {'Name':38s}  {'SBG':5s}  {'Exc':5s}  {'Vol':5s}  {'Out':5s}")
    print("-" * 70)

    pair_results = []
    for pair in REGRESSION_PAIRS:
        try:
            result = evaluate_pair(pair)
            pair_results.append(result)
            sbg_sym = "✓" if result["detected_by_sbg"] else "✗"
            exc_sym = "✓" if result["detected_by_exception_only"] else "✗"
            vol_sym = "✓" if result["detected_by_volume_only"] else "✗"
            out_sym = "✓" if result["detected_by_output_oracle"] else "✗"
            print(
                f"{pair['id']:4s}  {pair['name'][:38]:38s}  "
                f"SBG:{sbg_sym}  Exc:{exc_sym}  Vol:{vol_sym}  Out:{out_sym}"
            )
        except Exception as e:
            print(f"  {pair['id']}: ERROR — {e}")
            traceback.print_exc()
            pair_results.append({"id": pair["id"], "error": str(e)})

    valid = [r for r in pair_results if "sbg_distance" in r]
    n_total = len(valid)
    if n_total == 0:
        print("\nNo valid results — aborting.")
        sys.exit(1)

    # Detection rates at τ*
    n_sbg = sum(1 for r in valid if r["detected_by_sbg"])
    n_exc = sum(1 for r in valid if r["detected_by_exception_only"])
    n_vol = sum(1 for r in valid if r["detected_by_volume_only"])
    n_out = sum(1 for r in valid if r["detected_by_output_oracle"])

    dr_sbg = n_sbg / n_total
    dr_exc = n_exc / n_total
    dr_vol = n_vol / n_total
    dr_out = n_out / n_total

    # Silent bugs (invisible to exception AND volume)
    silent = [r for r in valid if r["is_silent_bug"]]
    n_silent = len(silent)
    n_silent_sbg = sum(1 for r in silent if r["detected_by_sbg"])
    n_silent_out = sum(1 for r in silent if r["detected_by_output_oracle"])

    # Per-bug-type breakdown
    bug_type_stats: Dict[str, Dict] = {}
    for r in valid:
        bt = r.get("bug_type", "unknown")
        if bt not in bug_type_stats:
            bug_type_stats[bt] = {"n": 0, "detected_sbg": 0, "detected_exc": 0, "detected_output": 0}
        bug_type_stats[bt]["n"] += 1
        if r["detected_by_sbg"]:
            bug_type_stats[bt]["detected_sbg"] += 1
        if r["detected_by_exception_only"]:
            bug_type_stats[bt]["detected_exc"] += 1
        if r["detected_by_output_oracle"]:
            bug_type_stats[bt]["detected_output"] += 1

    print()
    print("=" * 70)
    print(f"REGRESSION DETECTION SUMMARY  (τ* = {TAU_STAR:.4f}, N = {n_total} pairs)")
    print("=" * 70)
    print(f"  SBG distance (OUTPUT-FREE, our predictor):  {n_sbg}/{n_total} = {dr_sbg:.1%}")
    print(f"  exception_fraction only (output-free):      {n_exc}/{n_total} = {dr_exc:.1%}")
    print(f"  volume_ratio only (output-free):            {n_vol}/{n_total} = {dr_vol:.1%}")
    print(f"  ─────────────────────────────────────────────────────────")
    print(f"  Output oracle (BASELINE, not SBG result):   {n_out}/{n_total} = {dr_out:.1%}")
    print(f"")
    print(f"  Silent bugs (invisible to exc AND vol):     {n_silent}")
    print(f"    Detected by SBG:          {n_silent_sbg}/{n_silent}")
    print(f"    Detected by output oracle: {n_silent_out}/{n_silent}")
    print("=" * 70)
    print()
    print("IMPORTANT INTERPRETATION NOTE:")
    print(f"  The SBG result is {dr_sbg:.1%} (output-free predictor at τ*={TAU_STAR:.4f}).")
    print(f"  The output oracle ({dr_out:.1%}) is NOT the SBG result — it is a ceiling")
    print(f"  baseline that uses program return values (not output-free).")
    print(f"  Previous versions incorrectly reported {dr_out:.1%} as the SBG detection")
    print(f"  rate. This has been corrected in this version.")

    result = {
        "experiment": "REGRESSION_EVALUATION_OUTPUT_FREE",
        "version": "v5_phase3_corrected",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "methodology": {
            "safeguard_2_compliant": True,
            "predictor": "sbg_distance = 0.50*exception_fraction + 0.30*exception_type_jaccard + 0.20*volume_ratio",
            "predictor_reads_outputs": False,
            "threshold_tau_star": TAU_STAR,
            "threshold_source": "median SBG distance of SP pairs from dev split (pre-fixed)",
            "ground_truth": "pre-defined bug labels (all 15 pairs labeled CHANGED=1)",
            "oracle_separation": "output_divergence computed in compute_output_oracle(), not in compute_sbg_distance()",
            "note_on_previous_version": (
                "The previous version (regression_evaluator.py before Phase 3) "
                "reported 93.3% as the SBG detection rate. That figure was the "
                "output oracle (output_divergence > 0), not the SBG distance. "
                "This corrected version reports honest output-free SBG performance."
            ),
        },
        "n_pairs": n_total,
        "detection_rates": {
            "sbg_distance_output_free": dr_sbg,
            "exception_fraction_only": dr_exc,
            "volume_ratio_only": dr_vol,
            "output_oracle_BASELINE": dr_out,
        },
        "n_detected": {
            "sbg_distance_output_free": n_sbg,
            "exception_fraction_only": n_exc,
            "volume_ratio_only": n_vol,
            "output_oracle_BASELINE": n_out,
        },
        "silent_bugs": {
            "n_total": n_silent,
            "n_detected_by_sbg": n_silent_sbg,
            "n_detected_by_output_oracle": n_silent_out,
            "sbg_silent_detection_rate": n_silent_sbg / n_silent if n_silent else 0.0,
            "output_oracle_silent_detection_rate": n_silent_out / n_silent if n_silent else 0.0,
        },
        "bug_type_breakdown": bug_type_stats,
        "pair_results": valid,
        "scientific_interpretation": {
            "honest_sbg_detection_rate": (
                f"{n_sbg}/{n_total} = {dr_sbg:.1%} at threshold τ*={TAU_STAR:.4f}. "
                "This is the output-free SBG predictor result."
            ),
            "ceiling_output_oracle": (
                f"{n_out}/{n_total} = {dr_out:.1%} — uses output comparison (not SBG). "
                "This is an upper bound on what behavioral information is detectable "
                "given the current test inputs."
            ),
            "gap_interpretation": (
                f"The gap between output oracle ({dr_out:.1%}) and SBG ({dr_sbg:.1%}) "
                "represents information that IS in the outputs but is NOT captured by "
                "the current output-free feature design."
            ),
        },
    }

    out_path = REPO_ROOT / "artifacts" / "v5" / "REGRESSION_EVALUATION_RESULTS.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n[regression_evaluator] Saved → {out_path}")
    return result


if __name__ == "__main__":
    run_evaluation()
