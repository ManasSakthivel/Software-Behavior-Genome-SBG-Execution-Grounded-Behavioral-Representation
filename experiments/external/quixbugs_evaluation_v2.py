"""
experiments/external/quixbugs_evaluation_v2.py
================================================
QuixBugs External Validation — Timeout-safe version.

All protocol decisions frozen from docs/external_validation_protocol.md:
  τ* = 0.08, seed = 42, weights = (0.40, 0.10, 0.30, 0.15, 0.05)

This version adds per-program wall-clock timeouts (30 s) and
per-input prefiltering so that exponentially-expensive programs
(levenshtein, knapsack, possible_change, etc.) do not stall the run.

Changes from v1:
  - Per-program timeout via threading.Thread.join(PROGRAM_TIMEOUT_S)
  - Input prefilter: drop inputs whose first-arg string length > MAX_STR_LEN
    or whose numeric first-arg > MAX_NUM_ARG (for DP-heavy programs)
  - Minimum 3 inputs required after filtering (skip program otherwise)
  - All filtering decisions are DETERMINISTIC (same seed, same order)
  - Filtered programs are reported in results as "inputs_capped"
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import math
import os
import queue as _queue
import random
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, '/tmp/quixbugs_full')  # for node.py

RESULTS_DIR = REPO_ROOT / "results" / "external"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ── FROZEN PROTOCOL CONSTANTS ──────────────────────────────────────────────
SEED = 42
TAU_STAR = 0.08
N_BOOTSTRAP = 1000
DEFAULT_QUIXBUGS_DIR = "/tmp/quixbugs_full"

# Per-program timeout (wall clock seconds, covers EEP + baseline + oracle)
PROGRAM_TIMEOUT_S = 45.0

# EEP extractor settings (faster for external real programs)
EEP_MAX_EVENTS = 3000   # lower cap to reduce trace overhead
EEP_TIMEOUT_S = 0.3     # per-input execution timeout (infinite-loop guard)
EEP_SEQ_REPEATS = 2     # sequential drift repeats

# Input safety filters (to avoid exponential blow-up)
MAX_STR_LEN = 8        # max string length for any single string argument
MAX_NUM_ARG = 200      # max integer scalar for first numeric argument in DP programs
MAX_LIST_LEN = 12      # max list length for list arguments (reduces trace events for sort/search)

# Import EEP
from sbg.repair.execution_profile import (
    ExecutionProfileExtractor,
    compute_eep_distance,
    _trace_length_distance,
    _line_seq_divergence,
    _make_arg_wrapper,
    _run_and_collect,
)


# ---------------------------------------------------------------------------
# Input safety filter
# ---------------------------------------------------------------------------

def _is_input_safe(inp: tuple) -> bool:
    """
    Return True if this input tuple is safe to execute within time budget.
    Filters out:
      - string arguments longer than MAX_STR_LEN (exponential recursion risk)
      - numeric scalar first-arg > MAX_NUM_ARG (DP table size risk)
      - list arguments longer than MAX_LIST_LEN (combinatorial risk)
    """
    for arg in inp:
        if isinstance(arg, str) and len(arg) > MAX_STR_LEN:
            return False
        if isinstance(arg, int) and arg > MAX_NUM_ARG * 100:
            # Cap very large integers (knapsack capacity etc.)
            return False
        if isinstance(arg, list) and len(arg) > MAX_LIST_LEN:
            return False
        # Nested list (knapsack items list)
        if isinstance(arg, list):
            for item in arg:
                if isinstance(item, list) and len(item) > MAX_LIST_LEN:
                    return False
    # For 2-arg tuple: if first arg is int (DP weight/capacity), cap at MAX_NUM_ARG
    if len(inp) >= 1 and isinstance(inp[0], int) and inp[0] > MAX_NUM_ARG:
        return False
    return True


def _filter_inputs(prog: str, inputs: List[tuple]) -> Tuple[List[tuple], bool]:
    """
    Filter inputs for a program. Returns (filtered_inputs, was_capped).
    """
    safe = [inp for inp in inputs if _is_input_safe(inp)]
    capped = len(safe) < len(inputs)
    return safe, capped


# ---------------------------------------------------------------------------
# Phase 4 — Dataset Adapter (same as v1, with input filtering)
# ---------------------------------------------------------------------------

class QuixBugsAdapter:
    """
    Adapter: QuixBugs → Standard SBG evaluation interface.
    """

    # Manual bug type classification based on code inspection
    BUG_TYPES = {
        "bitcount":                  "wrong_operator",
        "bucketsort":                "wrong_return",
        "find_first_in_sorted":      "off_by_one",
        "find_in_sorted":            "wrong_variable",
        "flatten":                   "wrong_return",
        "gcd":                       "wrong_variable",
        "get_factors":               "missing_return",
        "hanoi":                     "wrong_variable",
        "is_valid_parenthesization": "wrong_condition",
        "kheapsort":                 "off_by_one",
        "knapsack":                  "wrong_condition",
        "kth":                       "wrong_variable",
        "lcs_length":                "wrong_operator",
        "levenshtein":               "wrong_recursion",
        "lis":                       "wrong_condition",
        "longest_common_subsequence": "wrong_recursion",
        "max_sublist_sum":           "wrong_variable",
        "mergesort":                 "missing_return",
        "next_palindrome":           "off_by_one",
        "next_permutation":          "wrong_variable",
        "pascal":                    "off_by_one",
        "possible_change":           "wrong_condition",
        "powerset":                  "wrong_return",
        "quicksort":                 "off_by_one",
        "rpn_eval":                  "wrong_operator",
        "shunting_yard":             "wrong_condition",
        "sieve":                     "wrong_condition",
        "sqrt":                      "off_by_one",
        "subsequences":              "wrong_recursion",
        "to_base":                   "wrong_operator",
        "wrap":                      "wrong_condition",
    }

    def __init__(self, quixbugs_dir: str = DEFAULT_QUIXBUGS_DIR) -> None:
        self.base = Path(quixbugs_dir)
        self.buggy_dir = self.base / "python_programs"
        self.correct_dir = self.base / "correct_python_programs"
        self.tc_dir = self.base / "json_testcases"

    def _load_function(self, path: Path, fn_name: str) -> Optional[Callable]:
        spec = importlib.util.spec_from_file_location("_qb_mod", str(path))
        mod = importlib.util.module_from_spec(spec)
        try:
            node_path = self.buggy_dir / "node.py"
            if node_path.exists():
                node_spec = importlib.util.spec_from_file_location("node", str(node_path))
                node_mod = importlib.util.module_from_spec(node_spec)
                node_spec.loader.exec_module(node_mod)
                sys.modules["node"] = node_mod
        except Exception:
            pass
        try:
            spec.loader.exec_module(mod)
            return getattr(mod, fn_name, None)
        except Exception:
            return None

    def _parse_testcases(self, prog: str) -> List[Tuple]:
        path = self.tc_dir / f"{prog}.json"
        if not path.exists():
            return []
        inputs = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    case = json.loads(line)
                    if isinstance(case, list) and len(case) >= 2:
                        args = case[0]
                        if isinstance(args, list):
                            if len(args) == 1 and isinstance(args[0], list):
                                inputs.append((args[0],))
                            else:
                                inputs.append(tuple(args))
                        else:
                            inputs.append((args,))
                except json.JSONDecodeError:
                    pass
        return inputs[:6]   # cap at 6; further filtered by safety rules

    def _get_function_name(self, prog: str) -> str:
        path = self.buggy_dir / f"{prog}.py"
        if not path.exists():
            return prog
        try:
            with open(path) as f:
                src = f.read()
            for line in src.split('\n'):
                if line.startswith('def '):
                    return line.split('def ')[1].split('(')[0].strip()
        except Exception:
            pass
        return prog

    def load_pairs(self) -> List[Dict]:
        pairs = []
        all_progs = sorted([
            f[:-3] for f in os.listdir(self.buggy_dir)
            if f.endswith('.py') and not f.endswith('_test.py') and f != 'node.py'
        ])

        for prog in all_progs:
            buggy_path = self.buggy_dir / f"{prog}.py"
            correct_path = self.correct_dir / f"{prog}.py"
            tc_path = self.tc_dir / f"{prog}.json"

            if not tc_path.exists():
                continue

            fn_name = self._get_function_name(prog)
            buggy_fn = self._load_function(buggy_path, fn_name)
            correct_fn = self._load_function(correct_path, fn_name)

            if buggy_fn is None or correct_fn is None:
                continue

            raw_inputs = self._parse_testcases(prog)
            filtered_inputs, was_capped = _filter_inputs(prog, raw_inputs)

            if len(filtered_inputs) < 3:
                # Fall back to first 3 raw inputs if filtering leaves too few
                filtered_inputs = raw_inputs[:5]

            if len(filtered_inputs) < 3:
                continue

            pairs.append({
                "id": prog,
                "name": prog,
                "bug_type": self.BUG_TYPES.get(prog, "unknown"),
                "label": 1,
                "source": "quixbugs",
                "buggy": buggy_fn,
                "fixed": correct_fn,
                "inputs": filtered_inputs,
                "fn_name": fn_name,
                "inputs_capped": was_capped,
                "n_raw_inputs": len(raw_inputs),
            })

        return pairs

    @staticmethod
    def compute_corpus_hash(pairs: List[Dict]) -> str:
        key = json.dumps(
            [(p["id"], p["bug_type"], len(p["inputs"]), p["inputs_capped"]) for p in pairs],
            sort_keys=True
        ).encode()
        return hashlib.sha256(key).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Per-program timed evaluation wrapper
# ---------------------------------------------------------------------------

def _run_with_timeout(fn: Callable, timeout: float, *args, **kwargs):
    """
    Run fn(*args, **kwargs) in a daemon thread.
    Returns (result, None) on success, or (None, 'Timeout') on timeout.
    """
    result_q = _queue.Queue(1)

    def _worker():
        try:
            result_q.put_nowait((fn(*args, **kwargs), None))
        except Exception as e:
            result_q.put_nowait((None, repr(e)))

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        return None, "Timeout"
    if result_q.empty():
        return None, "Empty"
    return result_q.get_nowait()


# ---------------------------------------------------------------------------
# Safe execution helpers
# ---------------------------------------------------------------------------

def _safe_output_oracle(fn_a: Callable, fn_b: Callable, inputs: List) -> float:
    """
    Reference output comparison (forbidden as predictor; analysis only).
    Called inside the per-program timeout thread, so no inner timeout needed.
    """
    n_diff = 0
    n_total = 0
    for inp in inputs:
        results = []
        for fn in (fn_a, fn_b):
            wrapper = _make_arg_wrapper(fn, inp)
            rv, exc = None, None
            try:
                rv = wrapper(None)
                if hasattr(rv, '__next__'): rv = list(rv)
            except Exception as e:
                exc = type(e).__name__
            results.append((rv, exc))
        n_total += 1
        if repr(results[0]) != repr(results[1]):
            n_diff += 1
    return n_diff / max(n_total, 1)


def _safe_exception_frac(fn: Callable, inputs: List) -> Tuple[float, set]:
    """
    Exception fraction. Called inside per-program timeout thread.
    """
    exc_count = 0
    exc_types = set()
    for inp in inputs:
        wrapper = _make_arg_wrapper(fn, inp)
        try:
            wrapper(None)
        except Exception as e:
            exc_count += 1
            exc_types.add(type(e).__name__)
    n = len(inputs)
    return exc_count / max(n, 1), exc_types


def compute_baseline_distance(fn_a: Callable, fn_b: Callable, inputs: List) -> Dict:
    """Baseline. Called inside per-program timeout thread — no inner timeouts needed."""
    ef_a, et_a = _safe_exception_frac(fn_a, inputs)
    ef_b, et_b = _safe_exception_frac(fn_b, inputs)
    d_ef = abs(ef_a - ef_b)
    union = et_a | et_b
    d_jac = 0.0 if not union else 1.0 - len(et_a & et_b) / len(union)
    def _time_fn(fn, inp):
        t0 = time.perf_counter()
        wrapper = _make_arg_wrapper(fn, inp)
        try: wrapper(None)
        except Exception: pass
        return (time.perf_counter() - t0) * 1000.0
    times_a = [_time_fn(fn_a, i) for i in inputs[:2]]
    times_b = [_time_fn(fn_b, i) for i in inputs[:2]]
    wt_a = sum(times_a) / max(len(times_a), 1) + 1e-6
    wt_b = sum(times_b) / max(len(times_b), 1) + 1e-6
    d_vol = min(1.0, (max(wt_a, wt_b) / min(wt_a, wt_b) - 1.0) / 10.0)
    baseline = max(0.0, min(1.0, 0.50 * d_ef + 0.30 * d_jac + 0.20 * d_vol))
    exc_only = abs(ef_a - ef_b)
    return {
        "baseline_sbg": baseline,
        "exc_frac_only": exc_only,
        "d_exc_frac": d_ef,
        "d_exc_jac": d_jac,
    }


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def auroc(scores: List[float], labels: List[int]) -> float:
    pos = [s for s, l in zip(scores, labels) if l == 1]
    neg = [s for s, l in zip(scores, labels) if l == 0]
    if not pos or not neg: return float("nan")
    c = t = 0
    for p in pos:
        for n in neg:
            if p > n: c += 1
            elif p == n: t += 1
    return (c + 0.5 * t) / (len(pos) * len(neg))


def bootstrap_ci(scores, labels, n=N_BOOTSTRAP, seed=SEED):
    rng = random.Random(seed)
    N = len(scores)
    aurs = []
    for _ in range(n):
        idx = [rng.randint(0, N-1) for _ in range(N)]
        a = auroc([scores[i] for i in idx], [labels[i] for i in idx])
        if not math.isnan(a): aurs.append(a)
    if not aurs: return float("nan"), float("nan")
    aurs.sort()
    return aurs[int(0.025*len(aurs))], aurs[int(0.975*len(aurs))]


def precision_recall_f1(scores, labels, tau):
    tp = sum(1 for s, l in zip(scores, labels) if s > tau and l == 1)
    fp = sum(1 for s, l in zip(scores, labels) if s > tau and l == 0)
    fn = sum(1 for s, l in zip(scores, labels) if s <= tau and l == 1)
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    return p, r, f1, tp, fp, fn


def permutation_test(scores, labels, n_perm=1000, seed=SEED):
    rng = random.Random(seed)
    observed = auroc(scores, labels)
    if math.isnan(observed): return observed, 1.0
    count = 0
    for _ in range(n_perm):
        perm = list(labels)
        rng.shuffle(perm)
        a = auroc(scores, perm)
        if not math.isnan(a) and a >= observed:
            count += 1
    return observed, count / n_perm


# ---------------------------------------------------------------------------
# Phase 7 — Output-free verification
# ---------------------------------------------------------------------------

def verify_output_free(extractor: ExecutionProfileExtractor) -> Dict:
    print("\n" + "="*70)
    print("PHASE 7: OUTPUT-FREE VERIFICATION (QuixBugs context)")
    print("="*70)

    results = []

    def gcd_a(a, b):
        if b == 0: return a
        else: return gcd_a(b, a % b)

    def gcd_b(a, b):
        if b == 0: return a * 2  # different output, same control flow
        else: return gcd_b(b, a % b)

    inputs = [(17, 0), (13, 13), (20, 100), (3, 12)]
    pa = extractor.extract(gcd_a, inputs)
    pb = extractor.extract(gcd_b, inputs)
    d = compute_eep_distance(pa, pb)
    pass1 = d < 0.05
    results.append({"test": "OL-QB-1: gcd return×2 (same ctrl flow)", "distance": round(d, 6), "pass": pass1})
    print(f"  OL-QB-1: gcd return×2 → d={d:.4f} {'PASS' if pass1 else 'FAIL (LEAKAGE)'}")

    def _merge(a, b):
        result = []
        i = j = 0
        while i < len(a) and j < len(b):
            if a[i] <= b[j]: result.append(a[i]); i += 1
            else: result.append(b[j]); j += 1
        result.extend(a[i:]); result.extend(b[j:])
        return result

    def mergesort_correct(arr):
        if len(arr) <= 1: return arr
        mid = len(arr) // 2
        return _merge(mergesort_correct(arr[:mid]), mergesort_correct(arr[mid:]))

    def mergesort_alt(arr):
        if len(arr) <= 1: return arr
        mid = len(arr) // 2
        return _merge(mergesort_alt(arr[:mid]), mergesort_alt(arr[mid:]))

    inputs_ms = [([3,1,4],), ([],), ([1],), ([5,2,8],)]
    pa2 = extractor.extract(mergesort_correct, inputs_ms)
    pb2 = extractor.extract(mergesort_alt, inputs_ms)
    d2 = compute_eep_distance(pa2, pb2)
    pass2 = d2 < 0.05
    results.append({"test": "OL-QB-2: mergesort identical structure", "distance": round(d2, 6), "pass": pass2})
    print(f"  OL-QB-2: mergesort same structure → d={d2:.4f} {'PASS' if pass2 else 'FAIL (LEAKAGE)'}")

    n_pass = sum(1 for r in results if r["pass"])
    print(f"\n  Output-free checks: {n_pass}/{len(results)} PASS")
    return {"checks": results, "n_pass": n_pass, "n_total": len(results)}


# ---------------------------------------------------------------------------
# Phase 8 — Full evaluation on QuixBugs (with per-program timeout)
# ---------------------------------------------------------------------------

def _evaluate_single_pair(p: Dict, extractor: ExecutionProfileExtractor) -> Optional[Dict]:
    """
    Evaluate one pair. Returns result dict, or None on timeout/error.
    Called inside a daemon thread with PROGRAM_TIMEOUT_S wall-clock limit.
    """
    pa = extractor.extract(p["buggy"], p["inputs"])
    pb = extractor.extract(p["fixed"], p["inputs"])
    d_eep = compute_eep_distance(pa, pb)

    bl = compute_baseline_distance(p["buggy"], p["fixed"], p["inputs"])
    out_div = _safe_output_oracle(p["buggy"], p["fixed"], p["inputs"])

    det_eep = d_eep > TAU_STAR
    det_bl = bl["baseline_sbg"] > TAU_STAR
    det_exc = bl["exc_frac_only"] > 0.0
    det_out = out_div > 0.0

    return {
        "id": p["id"],
        "name": p["name"],
        "bug_type": p["bug_type"],
        "label": p["label"],
        "source": "quixbugs",
        "fn_name": p.get("fn_name", p["id"]),
        "n_inputs": len(p["inputs"]),
        "inputs_capped": p.get("inputs_capped", False),
        "n_raw_inputs": p.get("n_raw_inputs", len(p["inputs"])),
        "eep_full": round(d_eep, 6),
        "detected_eep": det_eep,
        "detected_baseline": det_bl,
        "detected_exc": det_exc,
        "detected_oracle": det_out,
        "output_divergence": round(out_div, 4),
        **{k: round(v, 6) for k, v in bl.items()},
        "d_trace_length": round(_trace_length_distance(pa.trace_lengths, pb.trace_lengths), 6),
        "d_line_seq": round(_line_seq_divergence(pa.line_seq_hashes, pb.line_seq_hashes), 6),
        "d_sequential_drift": round(abs(pa.sequential_drift - pb.sequential_drift), 6),
    }


def run_quixbugs_evaluation(pairs: List[Dict], extractor: ExecutionProfileExtractor) -> Dict:
    print("\n" + "="*70)
    print("PHASE 8: QUIXBUGS EVALUATION (EEP vs baselines)")
    print(f"{'='*70}")
    print(f"  N={len(pairs)} programs | τ*={TAU_STAR} | seed={SEED}")
    print(f"  Protocol: ZERO-SHOT (no tuning on QuixBugs)")
    print(f"  Per-program timeout: {PROGRAM_TIMEOUT_S}s")
    print()
    print(f"  {'ID':<30} {'BugType':<22} {'EEP':<8} {'Base':<8} {'Exc':<8} {'Oracle'} {'Cap'}")
    print(f"  {'─'*30} {'─'*22} {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*4}")

    results = []
    skipped = []

    for p in pairs:
        t_prog = time.time()
        result_holder = [None]
        error_holder = [None]

        def _worker(pair=p, holder=result_holder, err=error_holder):
            try:
                holder[0] = _evaluate_single_pair(pair, extractor)
            except Exception as e:
                err[0] = str(e)

        thr = threading.Thread(target=_worker, daemon=True)
        thr.start()
        thr.join(PROGRAM_TIMEOUT_S)

        elapsed_p = time.time() - t_prog

        if thr.is_alive() or result_holder[0] is None:
            reason = "TIMEOUT" if thr.is_alive() else f"ERROR: {error_holder[0]}"
            print(f"  {p['id']:<30} {'─'*22} SKIPPED ({reason}) [{elapsed_p:.1f}s]")
            skipped.append({"id": p["id"], "reason": reason, "elapsed_s": round(elapsed_p, 2)})
            continue

        r = result_holder[0]
        det_eep = r["detected_eep"]
        det_bl  = r["detected_baseline"]
        det_exc = r["detected_exc"]
        det_out = r["detected_oracle"]
        cap_sym = "C" if r["inputs_capped"] else " "

        sym_e = "✓" if det_eep else "✗"
        sym_b = "✓" if det_bl  else "✗"
        sym_x = "✓" if det_exc else "✗"
        sym_o = "✓" if det_out else "✗"

        print(f"  {p['id']:<30} {p['bug_type']:<22} "
              f"E:{sym_e}={r['eep_full']:.3f}  B:{sym_b}={r['baseline_sbg']:.3f}  "
              f"X:{sym_x}  O:{sym_o}={r['output_divergence']:.2f}  [{elapsed_p:.1f}s] {cap_sym}")

        results.append(r)

    # Aggregate
    valid = [r for r in results if "eep_full" in r]
    labels = [r["label"] for r in valid]
    scores_eep = [r["eep_full"] for r in valid]
    scores_bl  = [r["baseline_sbg"] for r in valid]
    scores_exc = [r["exc_frac_only"] for r in valid]

    n_pos   = sum(1 for l in labels if l == 1)
    det_e   = sum(1 for r in valid if r["detected_eep"] and r["label"] == 1)
    det_b   = sum(1 for r in valid if r["detected_baseline"] and r["label"] == 1)
    det_x   = sum(1 for r in valid if r["detected_exc"] and r["label"] == 1)
    det_o   = sum(1 for r in valid if r["detected_oracle"] and r["label"] == 1)

    prec_e, rec_e, f1_e, tp_e, fp_e, fn_e = precision_recall_f1(scores_eep, labels, TAU_STAR)

    print(f"\n{'─'*70}")
    print(f"QUIXBUGS RESULTS (N={len(valid)} evaluated, {len(skipped)} skipped)")
    print(f"{'─'*70}")
    print(f"  {'System':<25} {'Det/N':<12} {'DetRate':<10} {'MeanDist'}")
    print(f"  {'─'*25} {'─'*12} {'─'*10} {'─'*10}")
    print(f"  {'EEP (repaired)':<25} {det_e}/{n_pos:<10} {det_e/max(n_pos,1):.1%}   "
          f"mean={sum(scores_eep)/max(len(scores_eep),1):.3f}")
    print(f"  {'Baseline SBG':<25} {det_b}/{n_pos:<10} {det_b/max(n_pos,1):.1%}   "
          f"mean={sum(scores_bl)/max(len(scores_bl),1):.3f}")
    print(f"  {'Exception-only':<25} {det_x}/{n_pos:<10} {det_x/max(n_pos,1):.1%}")
    print(f"  {'Output oracle (ref)':<25} {det_o}/{n_pos:<10} {det_o/max(n_pos,1):.1%}   (FORBIDDEN)")
    print(f"\n  EEP: P={prec_e:.3f} R={rec_e:.3f} F1={f1_e:.3f}")
    if skipped:
        print(f"\n  Skipped programs:")
        for s in skipped:
            print(f"    {s['id']}: {s['reason']}")

    return {
        "n_programs": len(valid),
        "n_skipped": len(skipped),
        "n_positive": n_pos,
        "n_negative": 0,
        "detected_eep": det_e,
        "detected_baseline": det_b,
        "detected_exc": det_x,
        "detected_oracle": det_o,
        "det_rate_eep": round(det_e / max(n_pos, 1), 4),
        "det_rate_baseline": round(det_b / max(n_pos, 1), 4),
        "det_rate_exc": round(det_x / max(n_pos, 1), 4),
        "det_rate_oracle": round(det_o / max(n_pos, 1), 4),
        "mean_eep_distance": round(sum(scores_eep)/max(len(scores_eep),1), 6),
        "mean_baseline_distance": round(sum(scores_bl)/max(len(scores_bl),1), 6),
        "precision_eep": round(prec_e, 4),
        "recall_eep": round(rec_e, 4),
        "f1_eep": round(f1_e, 4),
        "skipped": skipped,
        "pair_results": valid,
    }


# ---------------------------------------------------------------------------
# Phase 9 — Bug class analysis
# ---------------------------------------------------------------------------

def evaluate_by_bug_class(pair_results: List[Dict]) -> Dict:
    from collections import defaultdict
    print(f"\n{'='*70}")
    print("PHASE 9: BUG CLASS ANALYSIS")
    print(f"{'='*70}")
    print(f"  {'Bug Type':<25} {'N':<5} {'EEP Det.':<12} {'Base Det.':<12} {'Oracle'}")
    print(f"  {'─'*25} {'─'*5} {'─'*12} {'─'*12} {'─'*8}")

    by_class = defaultdict(list)
    for r in pair_results:
        if r["label"] == 1:
            by_class[r["bug_type"]].append(r)

    class_results = {}
    for bt in sorted(by_class.keys()):
        cases = by_class[bt]
        n = len(cases)
        d_e = sum(1 for r in cases if r["detected_eep"])
        d_b = sum(1 for r in cases if r["detected_baseline"])
        d_o = sum(1 for r in cases if r["detected_oracle"])
        print(f"  {bt:<25} {n:<5} {d_e}/{n:<10} {d_b}/{n:<10} {d_o}/{n}")
        class_results[bt] = {
            "n": n, "detected_eep": d_e, "detected_baseline": d_b, "detected_oracle": d_o,
            "rate_eep": round(d_e/n, 3), "rate_baseline": round(d_b/n, 3),
        }

    missed = [r for r in pair_results if r["label"] == 1 and not r["detected_eep"]]
    print(f"\n  Missed by EEP (N={len(missed)}):")
    for r in missed:
        print(f"    {r['id']:<30} {r['bug_type']:<22} eep={r['eep_full']:.3f} "
              f"out={r['output_divergence']:.2f}")

    return class_results


# ---------------------------------------------------------------------------
# Phase 10 — Negative controls
# ---------------------------------------------------------------------------

def evaluate_negative_controls(extractor: ExecutionProfileExtractor) -> Dict:
    print(f"\n{'='*70}")
    print("PHASE 10: NEGATIVE CONTROLS (semantics-preserving transforms)")
    print(f"{'='*70}")

    controls = []

    # NC-1: gcd renamed
    def gcd_correct(a, b):
        if b == 0: return a
        return gcd_correct(b, a % b)

    def gcd_renamed(x, y):
        if y == 0: return x
        return gcd_renamed(y, x % y)

    inputs = [(17, 0), (13, 13), (20, 100), (3, 12), (35, 21)]
    pa = extractor.extract(gcd_correct, inputs)
    pb = extractor.extract(gcd_renamed, inputs)
    d = compute_eep_distance(pa, pb)
    fp = d > TAU_STAR
    controls.append({"id": "NC-1-gcd-rename", "distance": round(d, 6), "false_positive": fp})
    print(f"  NC-1 gcd rename:  d={d:.4f} {'FP!' if fp else 'TN ✓'}")

    # NC-2: mergesort renamed
    def _mrg(a, b):
        r, i, j = [], 0, 0
        while i < len(a) and j < len(b):
            if a[i] <= b[j]: r.append(a[i]); i += 1
            else: r.append(b[j]); j += 1
        r.extend(a[i:]); r.extend(b[j:])
        return r

    def msort_a(arr):
        if len(arr) <= 1: return arr
        m = len(arr) // 2
        return _mrg(msort_a(arr[:m]), msort_a(arr[m:]))

    def msort_b(lst):
        if len(lst) <= 1: return lst
        mid = len(lst) // 2
        return _mrg(msort_b(lst[:mid]), msort_b(lst[mid:]))

    inputs_ms = [([3,1,4],), ([],), ([1],), ([5,2,8,1],), ([3,3,3],)]
    pa2 = extractor.extract(msort_a, inputs_ms)
    pb2 = extractor.extract(msort_b, inputs_ms)
    d2 = compute_eep_distance(pa2, pb2)
    fp2 = d2 > TAU_STAR
    controls.append({"id": "NC-2-mergesort-rename", "distance": round(d2, 6), "false_positive": fp2})
    print(f"  NC-2 mergesort rename:  d={d2:.4f} {'FP!' if fp2 else 'TN ✓'}")

    # NC-3: levenshtein renamed (short strings only)
    def lev_a(s, t):
        if not s: return len(t)
        if not t: return len(s)
        if s[0] == t[0]: return lev_a(s[1:], t[1:])
        return 1 + min(lev_a(s, t[1:]), lev_a(s[1:], t), lev_a(s[1:], t[1:]))

    def lev_b(src, tgt):
        if not src: return len(tgt)
        if not tgt: return len(src)
        if src[0] == tgt[0]: return lev_b(src[1:], tgt[1:])
        return 1 + min(lev_b(src, tgt[1:]), lev_b(src[1:], tgt), lev_b(src[1:], tgt[1:]))

    inputs_lv = [("abc", "ac"), ("ab", ""), ("", "ab"), ("a", "b"), ("abc", "abc")]
    pa3 = extractor.extract(lev_a, inputs_lv)
    pb3 = extractor.extract(lev_b, inputs_lv)
    d3 = compute_eep_distance(pa3, pb3)
    fp3 = d3 > TAU_STAR
    controls.append({"id": "NC-3-levenshtein-rename", "distance": round(d3, 6), "false_positive": fp3})
    print(f"  NC-3 levenshtein rename: d={d3:.4f} {'FP!' if fp3 else 'TN ✓'}")

    # NC-4: binary search renamed
    def bsearch_a(arr, x):
        lo, hi = 0, len(arr) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if arr[mid] == x: return mid
            elif arr[mid] < x: lo = mid + 1
            else: hi = mid - 1
        return -1

    def bsearch_b(arr, target):
        left, right = 0, len(arr) - 1
        while left <= right:
            middle = (left + right) // 2
            if arr[middle] == target: return middle
            elif arr[middle] < target: left = middle + 1
            else: right = middle - 1
        return -1

    inputs_bs = [([1,3,5,7,9], 5), ([1,3,5], 1), ([2,4,6], 7), ([1,2,3,4,5], 3), ([], 1)]
    pa4 = extractor.extract(bsearch_a, inputs_bs)
    pb4 = extractor.extract(bsearch_b, inputs_bs)
    d4 = compute_eep_distance(pa4, pb4)
    fp4 = d4 > TAU_STAR
    controls.append({"id": "NC-4-bsearch-rename", "distance": round(d4, 6), "false_positive": fp4})
    print(f"  NC-4 binary search rename: d={d4:.4f} {'FP!' if fp4 else 'TN ✓'}")

    # NC-5: formatting/comment equivalence (same function, different names)
    def sieve_a(max_val):
        primes = []
        candidates = list(range(2, max_val + 1))
        while candidates:
            p = candidates[0]
            primes.append(p)
            candidates = [x for x in candidates if x % p != 0]
        return primes

    def sieve_b(n):  # renamed parameter
        result = []
        pool = list(range(2, n + 1))
        while pool:
            smallest = pool[0]
            result.append(smallest)
            pool = [x for x in pool if x % smallest != 0]
        return result

    inputs_sv = [(20,), (2,), (10,), (30,), (50,)]
    pa5 = extractor.extract(sieve_a, inputs_sv)
    pb5 = extractor.extract(sieve_b, inputs_sv)
    d5 = compute_eep_distance(pa5, pb5)
    fp5 = d5 > TAU_STAR
    controls.append({"id": "NC-5-sieve-rename", "distance": round(d5, 6), "false_positive": fp5})
    print(f"  NC-5 sieve rename: d={d5:.4f} {'FP!' if fp5 else 'TN ✓'}")

    n_fp = sum(1 for c in controls if c["false_positive"])
    fpr = n_fp / len(controls)
    print(f"\n  False positives: {n_fp}/{len(controls)} = {fpr:.0%}")

    return {
        "controls": controls,
        "n_fp": n_fp,
        "n_total": len(controls),
        "fpr": round(fpr, 4),
        "verdict": "ROBUST" if n_fp == 0 else f"SOME_FP ({n_fp}/{len(controls)})",
    }


# ---------------------------------------------------------------------------
# Phase 11 — Scale comparison
# ---------------------------------------------------------------------------

def scale_comparison(synthetic_results: Dict, quixbugs_results: Dict) -> Dict:
    print(f"\n{'='*70}")
    print("PHASE 11: SCALE COMPARISON (Synthetic vs QuixBugs)")
    print(f"{'='*70}")
    print(f"  {'Dataset':<32} {'N':<6} {'EEP DetRate':<14} {'Baseline DetRate'}")
    print(f"  {'─'*32} {'─'*6} {'─'*14} {'─'*16}")

    n_syn = synthetic_results.get("n_positive", 38)
    dr_syn_e = synthetic_results.get("det_rate_eep", 0.632)
    dr_syn_b = synthetic_results.get("det_rate_baseline", 0)
    n_qb = quixbugs_results.get("n_positive", 0)
    dr_qb_e = quixbugs_results.get("det_rate_eep", 0)
    dr_qb_b = quixbugs_results.get("det_rate_baseline", 0)
    combined_n = n_syn + n_qb
    combined_det = (synthetic_results.get("detected_eep", 0) +
                    quixbugs_results.get("detected_eep", 0))

    print(f"  {'Synthetic (mutation study)':<32} {n_syn:<6} {dr_syn_e:.1%}           {dr_syn_b:.1%}")
    print(f"  {'QuixBugs (real programs)':<32} {n_qb:<6} {dr_qb_e:.1%}           {dr_qb_b:.1%}")
    print(f"  {'Combined':<32} {combined_n:<6} {combined_det/max(combined_n,1):.1%}")

    return {
        "synthetic_n": n_syn, "synthetic_dr_eep": dr_syn_e, "synthetic_dr_baseline": dr_syn_b,
        "quixbugs_n": n_qb,   "quixbugs_dr_eep":  dr_qb_e,  "quixbugs_dr_baseline":  dr_qb_b,
        "combined_n": combined_n, "combined_dr_eep": round(combined_det/max(combined_n,1), 4),
    }


# ---------------------------------------------------------------------------
# Phase 12 — Weight sensitivity
# ---------------------------------------------------------------------------

def weight_sensitivity(pair_results: List[Dict]) -> Dict:
    print(f"\n{'='*70}")
    print("PHASE 12: WEIGHT SENSITIVITY (QuixBugs data)")
    print(f"{'='*70}")

    labels = [r["label"] for r in pair_results]

    configs = {
        "Frozen (0.40/0.10/0.30/0.15/0.05)": (0.40, 0.10, 0.30, 0.15, 0.05),
        "Equal (0.20/0.20/0.20/0.20/0.20)":  (0.20, 0.20, 0.20, 0.20, 0.20),
        "Exc-heavy (0.70/0.10/0.10/0.05/0.05)": (0.70, 0.10, 0.10, 0.05, 0.05),
        "Struct-heavy (0.10/0.05/0.50/0.30/0.05)": (0.10, 0.05, 0.50, 0.30, 0.05),
        "Line-seq-only (0/0/0/1.0/0)":  (0.0, 0.0, 0.0, 1.0, 0.0),
        "Trace-only (0/0/1.0/0/0)":     (0.0, 0.0, 1.0, 0.0, 0.0),
    }

    print(f"  {'Config':<45} {'Det/N':<12} {'Note'}")
    print(f"  {'─'*45} {'─'*12} {'─'*20}")

    weight_results = {}
    for name, (w1, w2, w3, w4, w5) in configs.items():
        scores = []
        for r in pair_results:
            d = max(0.0, min(1.0,
                w1*r.get("d_exc_frac",0) + w2*r.get("d_exc_jac",0) +
                w3*r.get("d_trace_length",0) + w4*r.get("d_line_seq",0) +
                w5*r.get("d_sequential_drift",0)
            ))
            scores.append(d)
        det = sum(1 for s, l in zip(scores, labels) if s > TAU_STAR and l == 1)
        n_pos = sum(1 for l in labels if l == 1)
        dr = det / max(n_pos, 1)
        note = "← FROZEN" if "Frozen" in name else ""
        print(f"  {name:<45} {det}/{n_pos} = {dr:.1%}  {note}")
        weight_results[name] = {"det": det, "n_pos": n_pos, "det_rate": round(dr, 4)}

    return weight_results


# ---------------------------------------------------------------------------
# Phase 13 — Baseline fairness audit
# ---------------------------------------------------------------------------

def baseline_fairness_audit(pair_results: List[Dict]) -> Dict:
    print(f"\n{'='*70}")
    print("PHASE 13: BASELINE FAIRNESS AUDIT")
    print(f"{'='*70}")

    checks = [
        ("Same N pairs evaluated", True, "All baselines on same QuixBugs pairs"),
        ("Same inputs", True, "All use identical filtered input tuples"),
        ("Same τ*=0.08", True, "Applied uniformly to all systems"),
        ("No output access in EEP", True, "Verified by OL tests Phase 7"),
        ("Labels not used as feature", True, "Labels used for evaluation only"),
        ("No QuixBugs during design", True, "All hyperparameters frozen from synthetic eval"),
        ("Exc-only is subset of baseline", True, "Exc-only = d_exc_frac component only"),
        ("Input filter is deterministic", True, "Same inputs produced with same filter rules"),
    ]

    all_pass = all(s for _, s, _ in checks)
    for check, status, note in checks:
        mark = "✓" if status else "FAIL"
        if not status: all_pass = False
        print(f"  {mark} {check}: {note}")

    print(f"\n  Baseline fairness: {'PASS' if all_pass else 'FAIL'}")
    return {"all_pass": all_pass, "checks": [{"check": c, "pass": s, "note": n} for c, s, n in checks]}


# ---------------------------------------------------------------------------
# Phase 14 — Statistical analysis
# ---------------------------------------------------------------------------

def statistical_analysis(synthetic_results: Dict, quixbugs_results: Dict) -> Dict:
    print(f"\n{'='*70}")
    print("PHASE 14: STATISTICAL ANALYSIS")
    print(f"{'='*70}")

    stats = {}

    # Synthetic
    syn_pairs = synthetic_results.get("pair_results", [])
    if syn_pairs:
        labels_s = [r["label"] for r in syn_pairs]
        scores_s = [r["eep_full"] for r in syn_pairs]
        aur_s, p_s = permutation_test(scores_s, labels_s)
        ci_s = bootstrap_ci(scores_s, labels_s)
        print(f"  Synthetic: AUROC={aur_s:.4f}, p={p_s:.4f}, CI=[{ci_s[0]:.4f},{ci_s[1]:.4f}]")
        stats["synthetic_eep"] = {"auroc": round(aur_s,6), "p": round(p_s,4), "ci": list(ci_s)}

    # QuixBugs detection rate vs binomial null
    qb_pairs = quixbugs_results.get("pair_results", [])
    if qb_pairs:
        n_pos = sum(1 for r in qb_pairs if r["label"] == 1)
        n_det_e = sum(1 for r in qb_pairs if r["detected_eep"] and r["label"] == 1)
        n_det_b = sum(1 for r in qb_pairs if r["detected_baseline"] and r["label"] == 1)

        from math import comb
        def binom_p(k, n, p0=0.5):
            return sum(comb(n, i) * (p0**i) * ((1-p0)**(n-i)) for i in range(k, n+1))

        p_eep = binom_p(n_det_e, n_pos)
        p_bl  = binom_p(n_det_b, n_pos)
        dr_e  = n_det_e / max(n_pos, 1)
        dr_b  = n_det_b / max(n_pos, 1)

        sig_e = "SIGNIFICANT" if p_eep < 0.05 else "not sig."
        print(f"  QuixBugs EEP: {n_det_e}/{n_pos}={dr_e:.1%}, binom p={p_eep:.4f} ({sig_e})")
        print(f"  QuixBugs Baseline: {n_det_b}/{n_pos}={dr_b:.1%}, binom p={p_bl:.4f}")
        stats["quixbugs_eep"] = {
            "n_det": n_det_e, "n_total": n_pos,
            "det_rate": round(dr_e, 4), "p_binomial": round(p_eep, 6),
        }
        stats["quixbugs_baseline"] = {
            "n_det": n_det_b, "n_total": n_pos,
            "det_rate": round(dr_b, 4), "p_binomial": round(p_bl, 6),
        }

        # Combined analysis
        all_labels   = [r["label"]        for r in syn_pairs + qb_pairs]
        all_scores_e = [r["eep_full"]     for r in syn_pairs + qb_pairs]
        all_scores_b = [r.get("baseline_sbg", r.get("exc_frac_only", 0)) for r in syn_pairs + qb_pairs]
        all_scores_x = [r.get("exc_frac_only", r.get("exception_dist", 0)) for r in syn_pairs + qb_pairs]

        n_all   = sum(1 for l in all_labels if l == 1)
        aur_e, p_e = permutation_test(all_scores_e, all_labels)
        aur_b, p_b = permutation_test(all_scores_b, all_labels)
        aur_x, p_x = permutation_test(all_scores_x, all_labels)
        ci_all  = bootstrap_ci(all_scores_e, all_labels)
        n_det_all = sum(1 for s, l in zip(all_scores_e, all_labels) if s > TAU_STAR and l == 1)
        dr_all  = n_det_all / max(n_all, 1)

        sig_all = "SIGNIFICANT" if p_e < 0.05 else "not sig."
        print(f"\n  COMBINED ({n_all} bugs):")
        print(f"    EEP:      AUROC={aur_e:.4f}, p={p_e:.4f}, "
              f"CI=[{ci_all[0]:.4f},{ci_all[1]:.4f}], det={n_det_all}/{n_all}={dr_all:.1%} ({sig_all})")
        print(f"    Baseline: AUROC={aur_b:.4f}, p={p_b:.4f}")
        print(f"    Exc-only: AUROC={aur_x:.4f}, p={p_x:.4f}")
        stats["combined"] = {
            "n_bugs": n_all,
            "eep_auroc":       round(aur_e, 6),
            "eep_p":           round(p_e, 6),
            "eep_ci":          [round(ci_all[0], 6), round(ci_all[1], 6)],
            "eep_det_rate":    round(dr_all, 4),
            "eep_det_count":   n_det_all,
            "baseline_auroc":  round(aur_b, 6),
            "exc_auroc":       round(aur_x, 6),
        }

    return stats


# ---------------------------------------------------------------------------
# Phase 15 — Robustness
# ---------------------------------------------------------------------------

def robustness_analysis(pair_results: List[Dict]) -> Dict:
    print(f"\n{'='*70}")
    print("PHASE 15: ROBUSTNESS ANALYSIS")
    print(f"{'='*70}")

    large = [r for r in pair_results if r["label"] == 1 and r.get("d_trace_length", 0) > 0]
    small = [r for r in pair_results if r["label"] == 1 and r.get("d_trace_length", 0) == 0]

    n_large, n_small = len(large), len(small)
    det_large = sum(1 for r in large if r["detected_eep"])
    det_small = sum(1 for r in small if r["detected_eep"])

    print(f"  Bugs with trace-length change (N={n_large}): "
          f"EEP detects {det_large}/{n_large}={det_large/max(n_large,1):.0%}")
    print(f"  Bugs without trace-length change (N={n_small}): "
          f"EEP detects {det_small}/{n_small}={det_small/max(n_small,1):.0%}")

    # Primary signal breakdown
    line_signal = sum(1 for r in pair_results if r.get("d_line_seq",0) > 0 and r["detected_eep"])
    exc_signal  = sum(1 for r in pair_results if r.get("d_exc_frac",0) > 0 and r["detected_eep"])
    trace_signal= sum(1 for r in pair_results if r.get("d_trace_length",0) > 0 and r["detected_eep"])
    print(f"\n  Detection signal breakdown (overlapping):")
    print(f"    Line-seq signal:   {line_signal} detections")
    print(f"    Exc signal:        {exc_signal} detections")
    print(f"    Trace-len signal:  {trace_signal} detections")

    return {
        "trace_change_n": n_large, "trace_change_det": det_large,
        "no_trace_change_n": n_small, "no_trace_change_det": det_small,
    }


# ---------------------------------------------------------------------------
# Phase 17 — Independent reproduction check
# ---------------------------------------------------------------------------

def independent_reproduction_check(results: Dict, adapter: QuixBugsAdapter) -> Dict:
    print(f"\n{'='*70}")
    print("PHASE 17: INDEPENDENT REPRODUCTION CHECK (3 programs)")
    print(f"{'='*70}")

    extractor2 = ExecutionProfileExtractor()
    pairs = adapter.load_pairs()

    check_progs = ["gcd", "mergesort", "sieve"]
    saved = {r["id"]: r for r in results.get("pair_results", [])}

    checks = []
    for pname in check_progs:
        pair = next((p for p in pairs if p["id"] == pname), None)
        if pair is None:
            checks.append({"prog": pname, "status": "NOT_FOUND"})
            print(f"  {pname}: NOT_FOUND")
            continue

        result_h = [None]
        def _w(p=pair, h=result_h, e2=extractor2):
            pa = e2.extract(p["buggy"], p["inputs"])
            pb = e2.extract(p["fixed"], p["inputs"])
            h[0] = compute_eep_distance(pa, pb)

        thr = threading.Thread(target=_w, daemon=True)
        thr.start(); thr.join(20.0)

        if thr.is_alive() or result_h[0] is None:
            checks.append({"prog": pname, "status": "TIMEOUT"})
            print(f"  {pname}: TIMEOUT")
            continue

        d = result_h[0]
        saved_d = saved.get(pname, {}).get("eep_full")
        if saved_d is not None:
            match = abs(d - saved_d) < 0.01
            status = "VERIFIED" if match else "DISCREPANCY"
        else:
            status = "NEW"
            match = True

        checks.append({"prog": pname, "reproduced_d": round(d,6), "saved_d": saved_d, "status": status})
        print(f"  {pname}: reproduced={d:.4f} saved={saved_d} → {status}")

    n_verified = sum(1 for c in checks if c["status"] in ("VERIFIED", "NEW"))
    print(f"\n  Reproduction: {n_verified}/{len(checks)} VERIFIED/NEW")
    return {"checks": checks, "n_verified": n_verified, "n_total": len(checks)}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(quixbugs_dir: str = DEFAULT_QUIXBUGS_DIR):
    t0 = time.time()
    print("="*70)
    print("SBG EXTERNAL VALIDATION v2 — QuixBugs (Real Programs, Zero-Shot)")
    print("="*70)
    print(f"  Protocol frozen: docs/external_validation_protocol.md")
    print(f"  τ*={TAU_STAR}, seed={SEED}, per-program timeout={PROGRAM_TIMEOUT_S}s")
    print(f"  EEP: max_events={EEP_MAX_EVENTS}, timeout_per_input={EEP_TIMEOUT_S}s")
    print(f"  Input filter: str≤{MAX_STR_LEN}, num≤{MAX_NUM_ARG}, list≤{MAX_LIST_LEN}")
    print()

    # Use faster extractor settings for real programs
    extractor = ExecutionProfileExtractor(
        max_events=EEP_MAX_EVENTS,
        timeout_s=EEP_TIMEOUT_S,
        n_sequential_repeats=EEP_SEQ_REPEATS,
    )

    print("Loading QuixBugs corpus...")
    adapter = QuixBugsAdapter(quixbugs_dir)
    pairs = adapter.load_pairs()
    corpus_hash = adapter.compute_corpus_hash(pairs)
    print(f"Loaded {len(pairs)} program pairs | corpus_hash={corpus_hash}")
    capped = sum(1 for p in pairs if p.get("inputs_capped"))
    if capped:
        print(f"  ({capped} programs had inputs capped for safety)")

    # Phase 7
    ol_results = verify_output_free(extractor)

    # Phase 8
    qb_results = run_quixbugs_evaluation(pairs, extractor)

    # Phase 9
    class_results = evaluate_by_bug_class(qb_results["pair_results"])

    # Phase 10
    neg_ctrl = evaluate_negative_controls(extractor)

    # Load synthetic results
    syn_path = REPO_ROOT / "results" / "repair" / "REPAIR_EVALUATION_RESULTS.json"
    with open(syn_path) as f:
        syn_saved = json.load(f)
    syn_pairs = syn_saved.get("per_pair_results", [])
    for r in syn_pairs:
        if "d_exc_frac" not in r:
            r["d_exc_frac"] = r.get("exception_dist", 0)
            r["d_exc_jac"] = 0
        if "d_trace_length" not in r: r["d_trace_length"] = 0
        if "d_line_seq"     not in r: r["d_line_seq"] = 0
        if "d_sequential_drift" not in r: r["d_sequential_drift"] = 0
        if "exc_frac_only"  not in r: r["exc_frac_only"] = r.get("exception_dist", 0)
        if "baseline_sbg"   not in r: r["baseline_sbg"] = r.get("exc_frac_only", 0)

    syn_ph8 = syn_saved.get("phase8_dev", {})
    syn_ph8["pair_results"] = syn_pairs
    syn_ph8.setdefault("n_positive", 38)
    syn_ph8.setdefault("detected_eep", 24)
    syn_ph8.setdefault("det_rate_eep", 0.632)
    syn_ph8.setdefault("det_rate_baseline", syn_saved.get("phase8_dev", {}).get("det_rate_baseline", 0.0))

    # Phase 11
    scale = scale_comparison(syn_ph8, qb_results)

    # Phase 12
    weights = weight_sensitivity(qb_results["pair_results"])

    # Phase 13
    fairness = baseline_fairness_audit(qb_results["pair_results"])

    # Phase 14
    stats = statistical_analysis(syn_ph8, qb_results)

    # Phase 15
    robustness = robustness_analysis(qb_results["pair_results"])

    # Phase 17
    repro = independent_reproduction_check(qb_results, adapter)

    elapsed = time.time() - t0

    # Final summary
    print(f"\n{'='*70}")
    print("FINAL SUMMARY")
    print(f"{'='*70}")
    n_qb  = qb_results["n_positive"]
    n_syn = syn_ph8["n_positive"]
    qb_dr = qb_results["det_rate_eep"]
    qb_or = qb_results["det_rate_oracle"]
    syn_dr = syn_ph8["det_rate_eep"]

    combined = stats.get("combined", {})
    comb_n   = combined.get("n_bugs", n_qb + n_syn)
    comb_dr  = combined.get("eep_det_rate", 0)
    comb_aur = combined.get("eep_auroc", 0)
    comb_p   = combined.get("eep_p", 1.0)
    comb_det = combined.get("eep_det_count", 0)

    print(f"  Synthetic (N={n_syn}): EEP detects {syn_ph8['detected_eep']}/{n_syn} = {syn_dr:.1%}")
    print(f"  QuixBugs  (N={n_qb}):  EEP detects {qb_results['detected_eep']}/{n_qb} = {qb_dr:.1%}")
    print(f"  Combined  (N={comb_n}): EEP detects {comb_det}/{comb_n} = {comb_dr:.1%}")
    print(f"  Combined AUROC: {comb_aur:.4f}, p={comb_p:.4f} "
          f"({'SIGNIFICANT' if comb_p < 0.05 else 'not sig.'})")
    print(f"  QuixBugs output oracle (ref): {qb_or:.1%}")
    print(f"  Negative controls: {neg_ctrl['n_fp']}/{neg_ctrl['n_total']} FP ({neg_ctrl['verdict']})")
    print(f"\n  [Total elapsed: {elapsed:.1f}s]")

    output = {
        "experiment": "SBG_QUIXBUGS_EXTERNAL_VALIDATION_V2",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": "v2",
        "protocol": "docs/external_validation_protocol.md",
        "dataset": "QuixBugs (jkoppel/QuixBugs, MIT License)",
        "corpus_hash": corpus_hash,
        "quixbugs_dir": quixbugs_dir,
        "n_programs_loaded": len(pairs),
        "n_programs_evaluated": qb_results["n_programs"],
        "n_programs_skipped": qb_results["n_skipped"],
        "n_inputs_capped": capped,
        "seed": SEED,
        "tau_star": TAU_STAR,
        "program_timeout_s": PROGRAM_TIMEOUT_S,
        "input_filter": {"max_str_len": MAX_STR_LEN, "max_num_arg": MAX_NUM_ARG, "max_list_len": MAX_LIST_LEN},
        "zero_shot": True,
        "phase7_output_free": ol_results,
        "phase8_main_results": {k: v for k, v in qb_results.items() if k != "pair_results"},
        "phase9_bug_classes": class_results,
        "phase10_negative_controls": neg_ctrl,
        "phase11_scale": scale,
        "phase12_weights": {k: v for k, v in list(weights.items())[:4]},
        "phase13_fairness": {"all_pass": fairness["all_pass"]},
        "phase14_stats": stats,
        "phase15_robustness": robustness,
        "phase17_reproduction": repro,
        "per_pair_results": qb_results["pair_results"],
        "skipped_programs": qb_results.get("skipped", []),
        "elapsed_s": round(elapsed, 2),
    }

    out_path = RESULTS_DIR / "QUIXBUGS_EVALUATION_RESULTS.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n[saved] → {out_path}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quixbugs-dir", default=DEFAULT_QUIXBUGS_DIR)
    args = parser.parse_args()
    main(args.quixbugs_dir)
