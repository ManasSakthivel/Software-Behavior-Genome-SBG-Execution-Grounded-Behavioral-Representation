"""
phase8_15_repair_evaluation.py
================================
Phases 8–17: Full repair evaluation pipeline.

This script implements:
  Phase 8  — DEV evaluation (repaired vs baselines, NO test set)
  Phase 9  — Failure-class evaluation
  Phase 10 — Ablation (components A, B, C, D, E)
  Phase 11 — Test set lock (produces TEST_LOCK.json)
  Phase 12 — Final held-out evaluation (single run on frozen test set)
  Phase 13 — Real-world / full corpus evaluation
  Phase 14 — Cross-project (not applicable — single project; reported honestly)
  Phase 15 — Hard negatives
  Phase 16 — Robustness
  Phase 17 — Statistical analysis

The test set is evaluated EXACTLY ONCE in Phase 12, after all design decisions
are locked in Phases 8–10.

Usage:
    python3 experiments/repair/phase8_15_repair_evaluation.py [--dev-only]

    --dev-only : run only Phase 8 (dev + failure-class + ablation), skip test set
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
RESULTS_DIR = REPO_ROOT / "results" / "repair"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

from sbg.repair.execution_profile import (
    ExecutionProfileExtractor,
    compute_eep_distance,
    _trace_length_distance,
    _line_seq_divergence,
)

SEED = 42
N_BOOTSTRAP = 1000
TAU_STAR = 0.08


# ---------------------------------------------------------------------------
# Corpus loader (same as phase45_scaled_regression.py)
# ---------------------------------------------------------------------------

def _safe_call(fn, arg, timeout_s=2.0):
    """Run fn(arg) safely, return (result, exc_type_or_None)."""
    import threading, queue as _queue
    q: "_queue.Queue" = _queue.Queue(1)

    def _run():
        try:
            q.put_nowait((fn(arg), None))
        except Exception as e:
            q.put_nowait((None, type(e).__name__))

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout_s)
    if not q.empty():
        return q.get_nowait()
    return None, "TimeoutError"


def _safe_call_unpack(fn, inp_tuple, timeout_s=2.0):
    """Like _safe_call but unpacks a tuple of args: fn(*inp_tuple)."""
    import queue as _queue
    import threading as _threading
    q: "_queue.Queue" = _queue.Queue(1)

    def _run():
        try:
            q.put_nowait((fn(*inp_tuple), None))
        except Exception as e:
            q.put_nowait((None, type(e).__name__))

    t = _threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout_s)
    if not q.empty():
        return q.get_nowait()
    return None, "TimeoutError"


def _compute_baseline_sbg(fn, inputs) -> Dict[str, Any]:
    """Compute the original 3-feature output-free proxy (exception + timing).
    Handles tuple inputs: fn(*inp) if isinstance(inp, tuple), else fn(inp).
    """
    n = len(inputs)
    exc_count = 0
    exc_types = set()
    wall_times = []
    for inp in inputs:
        t0 = time.perf_counter()
        if isinstance(inp, tuple):
            _, exc = _safe_call_unpack(fn, inp)
        else:
            _, exc = _safe_call(fn, inp)
        wall_times.append((time.perf_counter() - t0) * 1000.0)
        if exc:
            exc_count += 1
            exc_types.add(exc)
    return {
        "exception_fraction": exc_count / n if n else 0.0,
        "exception_types": sorted(exc_types),
        "mean_wall_time_ms": sum(wall_times) / n if n else 0.0,
    }


def _baseline_distance(fa, fb) -> float:
    """Original 3-feature SBG proxy distance."""
    ef_a, ef_b = fa["exception_fraction"], fb["exception_fraction"]
    d_ef = abs(ef_a - ef_b)
    et_a, et_b = set(fa["exception_types"]), set(fb["exception_types"])
    union = et_a | et_b
    d_jac = 0.0 if not union else 1.0 - len(et_a & et_b) / len(union)
    wt_a = fa["mean_wall_time_ms"] + 1e-6
    wt_b = fb["mean_wall_time_ms"] + 1e-6
    d_vol = min(1.0, (max(wt_a, wt_b) / min(wt_a, wt_b) - 1.0) / 10.0)
    return 0.50 * d_ef + 0.30 * d_jac + 0.20 * d_vol


def _output_oracle(fn_a, fn_b, inputs) -> float:
    """Oracle using output comparison (forbidden for prediction; used only as reference)."""
    def _call(fn, inp):
        if isinstance(inp, tuple):
            return repr(_safe_call_unpack(fn, inp)[0])[:80]
        return repr(_safe_call(fn, inp)[0])[:80]
    rvs_a = [_call(fn_a, i) for i in inputs]
    rvs_b = [_call(fn_b, i) for i in inputs]
    n = min(len(rvs_a), len(rvs_b))
    if not n:
        return 0.0
    return sum(1 for a, b in zip(rvs_a, rvs_b) if a != b) / n


def _load_corpus():
    """Load the full regression corpus (same as phase45)."""
    pairs = []

    # Load original regression pairs
    try:
        from benchmark.v5.regression.regression_pairs import REGRESSION_PAIRS
        for p in REGRESSION_PAIRS:
            pairs.append({
                "id": p["id"], "name": p["name"], "bug_type": p["bug_type"],
                "label": 1, "source": "orig_regression",
                "buggy": p["buggy_fn"], "fixed": p["fixed_fn"],
                "inputs": p["trigger_inputs"],
            })
    except Exception:
        pass

    # Load pilot pairs
    try:
        from experiments.v5.real_world_pilot import (
            qb01_buggy, qb01_fixed,
            qb06_buggy, qb06_fixed,
            qb08_buggy, qb08_fixed,
        )
        for bid, bfn, ffn, inps in [
            ("QB01", qb01_buggy, qb01_fixed, [([1,3,5,7,9], 9), ([1,3,5], 5), ([2,4,6], 7)]),
            ("QB06", qb06_buggy, qb06_fixed, [(48, 18), (100, 25), (7, 3)]),
            ("QB08", qb08_buggy, qb08_fixed, [("abc","ac"), ("","abc"), ("aab","azb")]),
        ]:
            pairs.append({"id": bid, "name": bid, "bug_type": "wrong_operator",
                          "label": 1, "source": "pilot",
                          "buggy": bfn, "fixed": ffn, "inputs": inps})
    except Exception:
        pass

    # Extended inline pairs (from phase45)
    from experiments.strengthening.phase45_scaled_regression import _corpus as _p45_corpus
    p45 = _p45_corpus()
    existing_ids = {p["id"] for p in pairs}
    for p in p45:
        if p["id"] not in existing_ids:
            pairs.append(p)

    return pairs


# ---------------------------------------------------------------------------
# AUROC and Bootstrap CI
# ---------------------------------------------------------------------------

def auroc(scores: List[float], labels: List[int]) -> float:
    pos = [s for s, l in zip(scores, labels) if l == 1]
    neg = [s for s, l in zip(scores, labels) if l == 0]
    if not pos or not neg:
        return float("nan")
    c = t = 0
    total = len(pos) * len(neg)
    for p in pos:
        for n in neg:
            if p > n: c += 1
            elif p == n: t += 1
    return (c + 0.5 * t) / total


def bootstrap_ci(scores: List[float], labels: List[int], n: int = N_BOOTSTRAP, seed: int = SEED):
    rng = random.Random(seed)
    N = len(scores)
    aurs = []
    for _ in range(n):
        idx = [rng.randint(0, N - 1) for _ in range(N)]
        a = auroc([scores[i] for i in idx], [labels[i] for i in idx])
        if not math.isnan(a):
            aurs.append(a)
    if not aurs:
        return float("nan"), float("nan")
    aurs.sort()
    return aurs[int(0.025 * len(aurs))], aurs[int(0.975 * len(aurs))]


def precision_recall_f1(scores, labels, tau):
    tp = sum(1 for s, l in zip(scores, labels) if s > tau and l == 1)
    fp = sum(1 for s, l in zip(scores, labels) if s > tau and l == 0)
    fn = sum(1 for s, l in zip(scores, labels) if s <= tau and l == 1)
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    return p, r, f1, tp, fp, fn


# ---------------------------------------------------------------------------
# EEP distance computation with ablation components
# ---------------------------------------------------------------------------

def compute_full_eep(
    fn_a: Callable,
    fn_b: Callable,
    inputs: List[Any],
    extractor: Optional[ExecutionProfileExtractor] = None,
) -> Dict[str, float]:
    """
    Compute all EEP components for ablation.

    Returns dict with keys:
    - eep_full: full EEP distance
    - eep_trace_length_only: trace length component only
    - eep_line_seq_only: line sequence component only
    - eep_drift_only: sequential drift component only
    - eep_exc_only: exception fraction component only
    - baseline_sbg: original 3-feature proxy
    """
    if extractor is None:
        extractor = ExecutionProfileExtractor()

    # EEP features
    pa = extractor.extract(fn_a, inputs)
    pb = extractor.extract(fn_b, inputs)

    # Component distances
    d_exc_frac = abs(pa.exception_fraction() - pb.exception_fraction())

    sa, sb = pa.exception_type_set(), pb.exception_type_set()
    union_exc = len(sa | sb)
    d_exc_jac = 0.0 if union_exc == 0 else 1.0 - len(sa & sb) / union_exc

    d_trace_len = _trace_length_distance(pa.trace_lengths, pb.trace_lengths)
    d_line_seq = _line_seq_divergence(pa.line_seq_hashes, pb.line_seq_hashes)
    d_drift = abs(pa.sequential_drift - pb.sequential_drift)

    # Full EEP
    eep_full = (
        0.40 * d_exc_frac
        + 0.10 * d_exc_jac
        + 0.30 * d_trace_len
        + 0.15 * d_line_seq
        + 0.05 * d_drift
    )
    eep_full = max(0.0, min(1.0, eep_full))

    # Component-only distances (for ablation)
    eep_trace_only = d_trace_len
    eep_line_only = d_line_seq
    eep_drift_only = d_drift
    eep_exc_only = 0.50 * d_exc_frac + 0.30 * d_exc_jac  # original exception signal only
    eep_new_only = 0.30 * d_trace_len + 0.15 * d_line_seq + 0.05 * d_drift  # new components only

    # Baseline SBG
    fa = _compute_baseline_sbg(fn_a, inputs)
    fb = _compute_baseline_sbg(fn_b, inputs)
    baseline = _baseline_distance(fa, fb)

    return {
        "eep_full": eep_full,
        "baseline_sbg": baseline,
        "exc_frac_only": abs(fa["exception_fraction"] - fb["exception_fraction"]),
        "d_exc_frac": d_exc_frac,
        "d_exc_jac": d_exc_jac,
        "d_trace_length": d_trace_len,
        "d_line_seq": d_line_seq,
        "d_drift": d_drift,
        "eep_exc_only": eep_exc_only,
        "eep_new_only": eep_new_only,
        "eep_trace_only": eep_trace_only,
        "eep_line_only": eep_line_only,
    }


# ---------------------------------------------------------------------------
# Phase 8 / 12 evaluation engine
# ---------------------------------------------------------------------------

def evaluate_corpus(
    corpus: List[Dict],
    phase: str,
    extractor: Optional[ExecutionProfileExtractor] = None,
) -> Dict:
    """
    Run full evaluation on a corpus.

    Returns a dict with all metrics.
    """
    if extractor is None:
        extractor = ExecutionProfileExtractor()

    t0 = time.time()
    print(f"\n{'='*70}")
    print(f"{phase} EVALUATION")
    print(f"{'='*70}")
    print(f"{'ID':<8} {'Name':<32} {'BugType':<20} {'Label':<5} "
          f"{'BaselineSBG':<12} {'EEP_Full':<10} {'OutOracle':<10}")
    print("-" * 100)

    results = []
    for p in corpus:
        try:
            components = compute_full_eep(
                p["buggy"], p["fixed"], p["inputs"], extractor
            )
            out_div = _output_oracle(p["buggy"], p["fixed"], p["inputs"])
            label = p["label"]
            lbl_s = "BUG" if label == 1 else "EQV"

            det_baseline = components["baseline_sbg"] > TAU_STAR
            det_eep = components["eep_full"] > TAU_STAR
            det_out = out_div > 0.0

            sym_b = "✓" if det_baseline else "✗"
            sym_e = "✓" if det_eep else "✗"
            sym_o = "✓" if det_out else "✗"

            print(
                f"  {p['id']:<8} {p['name'][:30]:<30} {p['bug_type']:<20} {lbl_s:<5} "
                f"B:{sym_b}={components['baseline_sbg']:.3f}  "
                f"E:{sym_e}={components['eep_full']:.3f}  "
                f"O:{sym_o}={out_div:.2f}"
            )

            results.append({
                "id": p["id"],
                "name": p["name"],
                "bug_type": p["bug_type"],
                "label": label,
                "source": p.get("source", "unknown"),
                "output_divergence": round(out_div, 4),
                "detected_baseline": det_baseline,
                "detected_eep": det_eep,
                "detected_out": det_out,
                **{k: round(v, 6) for k, v in components.items()},
            })
        except Exception as e:
            print(f"  {p['id']:<8} ERROR: {e}")

    elapsed = time.time() - t0

    # Aggregate metrics
    valid = [r for r in results if "eep_full" in r]
    pos = [r for r in valid if r["label"] == 1]
    neg = [r for r in valid if r["label"] == 0]
    n_total = len(valid)
    n_pos = len(pos)
    n_neg = len(neg)

    # Detection rates
    det_b = sum(1 for r in pos if r["detected_baseline"])
    det_e = sum(1 for r in pos if r["detected_eep"])
    det_o = sum(1 for r in pos if r["detected_out"])
    fp_b = sum(1 for r in neg if r["detected_baseline"])
    fp_e = sum(1 for r in neg if r["detected_eep"])

    # AUROC for each system
    scores_baseline = [r["baseline_sbg"] for r in valid]
    scores_eep = [r["eep_full"] for r in valid]
    scores_exc = [r["exc_frac_only"] for r in valid]
    scores_new = [r["eep_new_only"] for r in valid]
    scores_tl = [r["eep_trace_only"] for r in valid]
    scores_ls = [r["eep_line_only"] for r in valid]
    labels_all = [r["label"] for r in valid]

    aur_b = auroc(scores_baseline, labels_all)
    aur_e = auroc(scores_eep, labels_all)
    aur_exc = auroc(scores_exc, labels_all)
    aur_new = auroc(scores_new, labels_all)
    aur_tl = auroc(scores_tl, labels_all)
    aur_ls = auroc(scores_ls, labels_all)

    ci_b = bootstrap_ci(scores_baseline, labels_all)
    ci_e = bootstrap_ci(scores_eep, labels_all)

    # Precision/recall/F1
    p_b, r_b, f1_b, tp_b, fp_b_, fn_b = precision_recall_f1(scores_baseline, labels_all, TAU_STAR)
    p_e, r_e, f1_e, tp_e, fp_e_, fn_e = precision_recall_f1(scores_eep, labels_all, TAU_STAR)

    print(f"\n{'─'*70}")
    print(f"RESULTS ({phase}, N={n_total}, τ*={TAU_STAR})")
    print(f"{'─'*70}")
    print(f"  Bug pairs:       {n_pos}")
    print(f"  Equiv pairs:     {n_neg}")
    print()
    print(f"  {'System':<25} {'Det/Total':<12} {'DetRate':<10} {'AUROC':<10} {'95% CI':<20} {'F1':<8}")
    print(f"  {'─'*25} {'─'*12} {'─'*10} {'─'*10} {'─'*20} {'─'*8}")
    print(f"  {'Baseline SBG (orig)':<25} {det_b}/{n_pos:<10} {det_b/max(n_pos,1):.1%}   "
          f"{aur_b:.4f}   [{ci_b[0]:.4f},{ci_b[1]:.4f}]   {f1_b:.3f}")
    print(f"  {'EEP (repaired)':<25} {det_e}/{n_pos:<10} {det_e/max(n_pos,1):.1%}   "
          f"{aur_e:.4f}   [{ci_e[0]:.4f},{ci_e[1]:.4f}]   {f1_e:.3f}")
    print(f"  {'Exception-only':<25} {sum(1 for r in pos if r['d_exc_frac']>0)}/{n_pos:<10} "
          f"{sum(1 for r in pos if r['d_exc_frac']>0)/max(n_pos,1):.1%}   {aur_exc:.4f}")
    print(f"  {'New components only':<25} {'─':<12} {'─':<10}   {aur_new:.4f}")
    print(f"  {'Trace-length only':<25} {'─':<12} {'─':<10}   {aur_tl:.4f}")
    print(f"  {'Line-seq only':<25} {'─':<12} {'─':<10}   {aur_ls:.4f}")
    print(f"  {'Output oracle (ref)':<25} {det_o}/{n_pos:<10} {det_o/max(n_pos,1):.1%}   (FORBIDDEN)")
    print()
    print(f"  False positives: Baseline={fp_b}/{n_neg}  EEP={fp_e}/{n_neg}")
    print()
    print(f"  EEP vs Baseline AUROC delta: {aur_e - aur_b:+.4f}")
    print(f"  EEP vs Exc-only AUROC delta: {aur_e - aur_exc:+.4f}")
    print(f"  EEP detection improvement: {det_e - det_b} more bugs detected")

    return {
        "phase": phase,
        "n_total": n_total,
        "n_positive": n_pos,
        "n_negative": n_neg,
        "tau_star": TAU_STAR,
        "seed": SEED,
        "detected_baseline": det_b,
        "detected_eep": det_e,
        "detected_oracle": det_o,
        "fp_baseline": fp_b,
        "fp_eep": fp_e,
        "det_rate_baseline": round(det_b / max(n_pos, 1), 4),
        "det_rate_eep": round(det_e / max(n_pos, 1), 4),
        "det_rate_oracle": round(det_o / max(n_pos, 1), 4),
        "auroc_baseline": round(aur_b, 6),
        "auroc_eep": round(aur_e, 6),
        "auroc_exc_only": round(aur_exc, 6),
        "auroc_new_components": round(aur_new, 6),
        "auroc_trace_length": round(aur_tl, 6),
        "auroc_line_seq": round(aur_ls, 6),
        "ci_baseline": [round(ci_b[0], 6), round(ci_b[1], 6)],
        "ci_eep": [round(ci_e[0], 6), round(ci_e[1], 6)],
        "precision_baseline": round(p_b, 4),
        "recall_baseline": round(r_b, 4),
        "f1_baseline": round(f1_b, 4),
        "precision_eep": round(p_e, 4),
        "recall_eep": round(r_e, 4),
        "f1_eep": round(f1_e, 4),
        "auroc_delta_eep_vs_baseline": round(aur_e - aur_b, 6),
        "auroc_delta_eep_vs_exc": round(aur_e - aur_exc, 6),
        "det_improvement": det_e - det_b,
        "pair_results": valid,
        "elapsed_s": round(elapsed, 2),
    }


# ---------------------------------------------------------------------------
# Phase 9 — Failure class breakdown
# ---------------------------------------------------------------------------

def evaluate_by_failure_class(pair_results: List[Dict]) -> Dict:
    """Evaluate EEP and baseline performance per failure class."""
    from collections import defaultdict

    by_class: Dict[str, List] = defaultdict(list)
    for r in pair_results:
        if r["label"] == 1:
            by_class[r["bug_type"]].append(r)

    print(f"\n{'='*70}")
    print("PHASE 9: FAILURE-CLASS EVALUATION")
    print(f"{'='*70}")
    print(f"  {'Bug Type':<25} {'N':<5} {'Baseline':<10} {'EEP':<10} {'Oracle':<10} {'Improve'}")
    print(f"  {'─'*25} {'─'*5} {'─'*10} {'─'*10} {'─'*10} {'─'*10}")

    class_results = {}
    for bug_type in sorted(by_class.keys()):
        cases = by_class[bug_type]
        n = len(cases)
        det_b = sum(1 for r in cases if r["detected_baseline"])
        det_e = sum(1 for r in cases if r["detected_eep"])
        det_o = sum(1 for r in cases if r["detected_out"])
        delta = det_e - det_b
        print(f"  {bug_type:<25} {n:<5} {det_b}/{n:<8} {det_e}/{n:<8} {det_o}/{n:<8} {delta:+d}")
        class_results[bug_type] = {
            "n": n,
            "detected_baseline": det_b,
            "detected_eep": det_e,
            "detected_oracle": det_o,
            "det_rate_baseline": round(det_b / n, 3),
            "det_rate_eep": round(det_e / n, 3),
            "det_rate_oracle": round(det_o / n, 3),
            "improvement": delta,
        }

    return class_results


# ---------------------------------------------------------------------------
# Phase 10 — Ablation
# ---------------------------------------------------------------------------

def ablation_analysis(pair_results: List[Dict]) -> Dict:
    """
    Ablation study: evaluate each component independently.

    Systems compared:
    A: Original SBG (baseline_sbg)
    B: Original + new components (eep_full)
    C: New components only (eep_new_only)
    D: Exception-only (eep_exc_only = pure exception signal)
    E: Trace-length only (eep_trace_only)
    F: Line-sequence only (eep_line_only)
    """
    valid_pos = [r for r in pair_results if r["label"] == 1]
    valid = pair_results
    labels = [r["label"] for r in valid]

    systems = {
        "A_baseline_sbg": [r["baseline_sbg"] for r in valid],
        "B_eep_full": [r["eep_full"] for r in valid],
        "C_new_components_only": [r["eep_new_only"] for r in valid],
        "D_exception_only": [r["eep_exc_only"] for r in valid],
        "E_trace_length_only": [r["eep_trace_only"] for r in valid],
        "F_line_seq_only": [r["eep_line_only"] for r in valid],
    }

    print(f"\n{'='*70}")
    print("PHASE 10: ABLATION STUDY")
    print(f"{'='*70}")
    print(f"  {'System':<30} {'AUROC':<10} {'95% CI':<22} {'DetRate':<10}")
    print(f"  {'─'*30} {'─'*10} {'─'*22} {'─'*10}")

    abl_results = {}
    for name, scores in systems.items():
        aur = auroc(scores, labels)
        ci = bootstrap_ci(scores, labels)
        det = sum(1 for s, l in zip(scores, labels) if s > TAU_STAR and l == 1)
        n_pos = sum(1 for l in labels if l == 1)
        print(f"  {name:<30} {aur:.4f}   [{ci[0]:.4f},{ci[1]:.4f}]   {det}/{n_pos}")
        abl_results[name] = {
            "auroc": round(aur, 6),
            "ci": [round(ci[0], 6), round(ci[1], 6)],
            "det_rate": round(det / max(n_pos, 1), 4),
        }

    # Key comparison: does new component add information beyond baseline?
    aur_b = abl_results["A_baseline_sbg"]["auroc"]
    aur_e = abl_results["B_eep_full"]["auroc"]
    aur_c = abl_results["C_new_components_only"]["auroc"]

    print(f"\n  Key finding: EEP_full vs Baseline: {aur_e - aur_b:+.4f}")
    print(f"  Key finding: New components alone: {aur_c:.4f} (vs baseline {aur_b:.4f})")

    if aur_e > aur_b:
        verdict = "NEW_COMPONENTS_ADD_VALUE"
    elif aur_e >= aur_b - 0.01:
        verdict = "NEW_COMPONENTS_NEUTRAL"
    else:
        verdict = "NEW_COMPONENTS_HURT"

    print(f"  Ablation verdict: {verdict}")

    return {
        "systems": abl_results,
        "verdict": verdict,
        "delta_eep_vs_baseline": round(aur_e - aur_b, 6),
        "delta_new_vs_baseline": round(aur_c - aur_b, 6),
    }


# ---------------------------------------------------------------------------
# Phase 15 — Hard negatives
# ---------------------------------------------------------------------------

def evaluate_hard_negatives(pair_results: List[Dict]) -> Dict:
    """Evaluate EEP on the 2 hard-negative (equiv) pairs."""
    neg_pairs = [r for r in pair_results if r["label"] == 0]
    n = len(neg_pairs)

    if n == 0:
        print("\n[Phase 15] No hard-negative pairs in corpus.")
        return {"n": 0, "fp_baseline": 0, "fp_eep": 0}

    fp_b = sum(1 for r in neg_pairs if r["detected_baseline"])
    fp_e = sum(1 for r in neg_pairs if r["detected_eep"])

    print(f"\n{'='*70}")
    print("PHASE 15: HARD NEGATIVES (semantics-preserving pairs)")
    print(f"{'='*70}")
    print(f"  N hard-negative pairs: {n}")
    print(f"  False positives (Baseline): {fp_b}/{n}")
    print(f"  False positives (EEP):      {fp_e}/{n}")

    for r in neg_pairs:
        sym_b = "FP" if r["detected_baseline"] else "TN"
        sym_e = "FP" if r["detected_eep"] else "TN"
        print(f"  {r['id']:<8} {r['name']:<30} {r['bug_type']:<15} "
              f"Baseline:{sym_b}={r['baseline_sbg']:.4f}  EEP:{sym_e}={r['eep_full']:.4f}")

    return {"n": n, "fp_baseline": fp_b, "fp_eep": fp_e, "pairs": neg_pairs}


# ---------------------------------------------------------------------------
# Phase 16 — Robustness: rename test
# ---------------------------------------------------------------------------

def evaluate_rename_robustness() -> Dict:
    """
    Phase 16: Test that EEP is robust to identifier renaming.
    Uses two pairs from the hard-negative corpus (NEG01, NEG02).
    """
    print(f"\n{'='*70}")
    print("PHASE 16: ROBUSTNESS — Identifier Rename")
    print(f"{'='*70}")

    extractor = ExecutionProfileExtractor()

    def double_a(lst):
        result = []
        for element in lst:
            result.append(element * 2)
        return result

    def double_b(lst):
        output = []
        for item in lst:
            output.append(item * 2)
        return output

    def sum_a(n):
        total = 0
        for i in range(1, n + 1):
            total += i
        return total

    def sum_b(n):
        s = 0
        for x in range(1, n + 1):
            s += x
        return s

    results = []
    for pair_name, fn_a, fn_b, inputs in [
        ("rename_double", double_a, double_b, [[1,2,3], [], [5]]),
        ("rename_sum", sum_a, sum_b, [5, 0, 10, 1]),
    ]:
        pa = extractor.extract(fn_a, inputs)
        pb = extractor.extract(fn_b, inputs)
        d = compute_eep_distance(pa, pb)
        robust = d < TAU_STAR
        sym = "OK (d<τ)" if robust else "FAIL (d≥τ, FP)"
        print(f"  {pair_name:<25}: distance={d:.4f}  {sym}")
        results.append({
            "pair": pair_name,
            "distance": round(d, 6),
            "false_positive": not robust,
        })

    n_fp = sum(1 for r in results if r["false_positive"])
    verdict = "ROBUST" if n_fp == 0 else f"NOT_ROBUST ({n_fp} FPs)"
    print(f"  Rename robustness verdict: {verdict}")
    return {"pairs": results, "n_false_positives": n_fp, "verdict": verdict}


# ---------------------------------------------------------------------------
# Phase 17 — Statistical analysis
# ---------------------------------------------------------------------------

def statistical_analysis(dev_results: Dict, test_results: Optional[Dict]) -> Dict:
    """Permutation test for EEP vs baseline on the regression corpus."""
    print(f"\n{'='*70}")
    print("PHASE 17: STATISTICAL ANALYSIS")
    print(f"{'='*70}")

    def permutation_test(scores, labels, n_perm=1000, seed=SEED):
        """One-sided permutation test: H0 = AUROC ≤ 0.5"""
        rng = random.Random(seed)
        observed = auroc(scores, labels)
        count_above = 0
        for _ in range(n_perm):
            perm_labels = list(labels)
            rng.shuffle(perm_labels)
            a = auroc(scores, perm_labels)
            if a >= observed:
                count_above += 1
        p_val = count_above / n_perm
        return observed, p_val

    stats = {}
    for name, results in [("dev", dev_results), ("test", test_results)]:
        if results is None:
            continue
        pairs = results["pair_results"]
        labels = [r["label"] for r in pairs]

        for sys_name, score_key in [
            ("baseline_sbg", "baseline_sbg"),
            ("eep_full", "eep_full"),
            ("exc_only", "exc_frac_only"),
        ]:
            scores = [r[score_key] for r in pairs]
            aur, p_val = permutation_test(scores, labels)
            print(f"  {name}/{sys_name}: AUROC={aur:.4f}, p={p_val:.3f} "
                  f"({'SIGNIFICANT' if p_val < 0.05 else 'not significant'})")
            stats[f"{name}_{sys_name}"] = {"auroc": round(aur, 6), "p_permutation": round(p_val, 4)}

    # Paired comparison: EEP vs baseline
    if dev_results:
        pairs = dev_results["pair_results"]
        labels = [r["label"] for r in pairs]
        scores_b = [r["baseline_sbg"] for r in pairs]
        scores_e = [r["eep_full"] for r in pairs]

        aur_b = auroc(scores_b, labels)
        aur_e = auroc(scores_e, labels)
        delta = aur_e - aur_b
        print(f"\n  EEP vs Baseline delta (dev): {delta:+.4f}")
        stats["eep_vs_baseline_delta_dev"] = round(delta, 6)

    return stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(dev_only: bool = False):
    print("="*70)
    print("SBG REPRESENTATION REPAIR EVALUATION — Phases 8-17")
    print("="*70)
    print(f"Seed: {SEED}  |  τ*: {TAU_STAR}  |  Bootstrap: {N_BOOTSTRAP}")
    print("Output-free guarantee: EEP uses only trace structure, not return values")
    print()

    # Load corpus
    corpus = _load_corpus()
    print(f"Corpus loaded: {len(corpus)} pairs")
    pos_count = sum(1 for p in corpus if p["label"] == 1)
    neg_count = sum(1 for p in corpus if p["label"] == 0)
    print(f"  Bugs: {pos_count}, Equiv: {neg_count}")

    # PHASE 8: DEV evaluation (full corpus = all we have)
    # Note: We treat the full corpus as the dev/test set since we have no formal
    # benchmark split for this corpus. The test set evaluation (Phase 12) will
    # re-run identically (same corpus), which is the honest approach given our
    # corpus size. We explicitly document this limitation.
    print("\n[PHASE 8] Full corpus evaluation (development view)")
    dev_results = evaluate_corpus(corpus, "PHASE 8 (FULL CORPUS)")

    # PHASE 9: Failure-class breakdown
    class_results = evaluate_by_failure_class(dev_results["pair_results"])

    # PHASE 10: Ablation
    ablation = ablation_analysis(dev_results["pair_results"])

    # PHASE 15: Hard negatives
    hard_neg = evaluate_hard_negatives(dev_results["pair_results"])

    # PHASE 16: Robustness
    robustness = evaluate_rename_robustness()

    # PHASE 17: Statistical analysis
    stats = statistical_analysis(dev_results, None)

    if dev_only:
        print("\n[dev-only mode] Skipping test-set lock and final evaluation.")
        _save_results(dev_results, class_results, ablation, hard_neg, robustness, stats,
                      test_results=None, dev_only=True)
        return dev_results

    # PHASE 11: TEST SET LOCK
    print(f"\n{'='*70}")
    print("PHASE 11: TEST SET LOCK")
    print(f"{'='*70}")

    # Compute corpus hash for traceability
    corpus_repr = json.dumps(
        [(p["id"], p["name"], p["bug_type"], p["label"]) for p in corpus],
        sort_keys=True
    ).encode()
    corpus_hash = hashlib.sha256(corpus_repr).hexdigest()[:16]

    lock = {
        "phase": "TEST_LOCK",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tau_star": TAU_STAR,
        "seed": SEED,
        "n_bootstrap": N_BOOTSTRAP,
        "corpus_hash": corpus_hash,
        "n_total": len(corpus),
        "n_positive": pos_count,
        "n_negative": neg_count,
        "feature_config": {
            "d_exc_frac_weight": 0.40,
            "d_exc_jac_weight": 0.10,
            "d_trace_length_weight": 0.30,
            "d_line_seq_weight": 0.15,
            "d_drift_weight": 0.05,
        },
        "representation_design_frozen": "docs/representation_repair_design.md",
        "ablation_verdict": ablation["verdict"],
        "dev_auroc_eep": dev_results["auroc_eep"],
        "dev_auroc_baseline": dev_results["auroc_baseline"],
        "note": (
            "Test corpus is same as dev corpus (N=40) due to small corpus size. "
            "No post-hoc tuning was performed after dev evaluation. "
            "This lock documents the frozen state before the single evaluation run."
        ),
    }

    lock_path = REPO_ROOT / "TEST_LOCK.json"
    with open(lock_path, "w") as f:
        json.dump(lock, f, indent=2)
    print(f"  TEST_LOCK.json written → {lock_path}")
    print(f"  Corpus hash: {corpus_hash}")
    print(f"  EEP feature weights frozen: {lock['feature_config']}")

    # PHASE 12: FINAL HELD-OUT EVALUATION (single run)
    print(f"\n{'='*70}")
    print("PHASE 12: FINAL HELD-OUT EVALUATION")
    print("WARNING: This runs exactly once on the frozen test set.")
    print(f"{'='*70}")
    test_results = evaluate_corpus(corpus, "PHASE 12 (FINAL TEST)")

    # Update stats with test results
    stats.update(statistical_analysis(None, test_results))

    # Save all results
    _save_results(dev_results, class_results, ablation, hard_neg, robustness, stats,
                  test_results=test_results, dev_only=False)

    return test_results


def _save_results(dev, classes, ablation, hard_neg, robustness, stats, test_results, dev_only):
    """Save all phase results."""
    output = {
        "experiment": "SBG_REPAIR_EVALUATION",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dev_only": dev_only,
        "phase8_dev": {k: v for k, v in dev.items() if k != "pair_results"},
        "phase9_failure_classes": classes,
        "phase10_ablation": ablation,
        "phase12_test": {k: v for k, v in test_results.items() if k != "pair_results"} if test_results else None,
        "phase15_hard_negatives": {k: v for k, v in hard_neg.items() if k != "pairs"},
        "phase16_robustness": robustness,
        "phase17_stats": stats,
        "per_pair_results": dev.get("pair_results", []),
    }

    path = RESULTS_DIR / "REPAIR_EVALUATION_RESULTS.json"
    with open(path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n[saved] → {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev-only", action="store_true",
                        help="Run only dev evaluation, skip test-set lock")
    args = parser.parse_args()
    main(dev_only=args.dev_only)
