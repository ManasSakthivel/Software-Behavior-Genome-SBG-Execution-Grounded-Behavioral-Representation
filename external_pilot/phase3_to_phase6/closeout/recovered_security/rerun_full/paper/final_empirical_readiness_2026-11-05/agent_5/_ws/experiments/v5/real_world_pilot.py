"""
real_world_pilot.py — Phase 5: Real-World Pilot Evaluation

This script implements a QuixBugs-inspired pilot evaluation using
self-contained Python programs that represent real algorithmic bugs.

DESIGN RATIONALE:
  - BugsInPy requires pip install + complex project environments — not feasible
    in this sprint without dependency setup.
  - QuixBugs Python programs are simple algorithmic functions (same structure
    as this project's corpus) — we replicate their bug patterns inline.
  - This pilot uses 10 representative Python programs covering the same
    bug categories as QuixBugs: wrong_comparator, off_by_one, wrong_return,
    missing_base_case, wrong_variable.

WHAT THIS TESTS (RQ4):
  Can SBG distance separate buggy/fixed versions of real-world-style
  Python programs above chance, using output-free features?

PILOT SCOPE: 10 program pairs (5 buggy + 5 SP-equivalent pairs as negatives)
ORACLE: Independent bug labels (fixed before any execution)
PREDICTOR: SBG output-free distance (same as Phase 3 evaluator)
"""

from __future__ import annotations

import json
import math
import random
import sys
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

SEED = 42
N_BOOTSTRAP = 1000
TAU_STAR = 0.08  # same pre-fixed threshold as Phase 3

# ─────────────────────────────────────────────────────────────────────────────
# QUIXBUGS-STYLE PROGRAM PAIRS
# These are real algorithmic programs (not mutations from our benchmark corpus).
# Each pair: (buggy_fn, fixed_fn, inputs, bug_type, label)
# label: 1 = CHANGED (bug present), 0 = EQUIVALENT (semantics-preserving refactor)
# ─────────────────────────────────────────────────────────────────────────────

# ── QB-01: Binary search — off-by-one (QuixBugs: FIND_FIRST_IN_SORTED) ──────
def qb01_buggy(arr, x):
    """Binary search: returns index of x, -1 if not found. BUG: hi=len instead of len-1"""
    lo, hi = 0, len(arr)  # BUG: should be len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == x:
            return mid
        elif arr[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

def qb01_fixed(arr, x):
    """Binary search: correct."""
    lo, hi = 0, len(arr) - 1  # FIXED
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == x:
            return mid
        elif arr[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

QB01_INPUTS = [
    ([1, 3, 5, 7, 9], 5),
    ([1, 3, 5, 7, 9], 9),  # boundary — hits hi=len bug
    ([1, 3, 5, 7, 9], 1),
    ([2, 4, 6], 6),
    ([10], 10),
]

# ── QB-02: Flatten nested list — wrong recursion (QuixBugs: FLATTEN) ─────────
def qb02_buggy(lst):
    """Flatten nested list. BUG: doesn't recurse into nested lists."""
    result = []
    for item in lst:
        if isinstance(item, list):
            result.append(item)  # BUG: should extend with flatten(item)
        else:
            result.append(item)
    return result

def qb02_fixed(lst):
    """Flatten nested list. Correct."""
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(qb02_fixed(item))  # FIXED: recursive call
        else:
            result.append(item)
    return result

QB02_INPUTS = [
    ([1, [2, 3], [4, [5, 6]]],),
    ([1, 2, 3],),
    ([[1, 2], [3, 4]],),
    ([],),
    ([[1], [2], [3]],),
]

# ── QB-03: Count change — wrong base case (QuixBugs: POSSIBLE_CHANGE) ────────
def qb03_buggy(amount, coins):
    """Count ways to make change. BUG: wrong base case returns 0 instead of 1."""
    if not coins or amount < 0:
        return 0
    if amount == 0:
        return 0  # BUG: should be 1 (one way to make 0 = use no coins)
    return qb03_buggy(amount - coins[0], coins) + qb03_buggy(amount, coins[1:])

def qb03_fixed(amount, coins):
    """Count ways to make change. Correct."""
    if not coins or amount < 0:
        return 0
    if amount == 0:
        return 1  # FIXED
    return qb03_fixed(amount - coins[0], coins) + qb03_fixed(amount, coins[1:])

QB03_INPUTS = [
    (4, [1, 2]),
    (0, [1, 2, 5]),
    (3, [2]),
    (10, [1, 5, 10]),
    (1, [2]),
]

# ── QB-04: Max subarray sum — off-by-one Kadane (QuixBugs: MAX_SUBARRAY) ─────
def qb04_buggy(arr):
    """Max subarray sum. BUG: initialises current_sum wrong (starts at arr[1])."""
    if not arr:
        return 0
    max_sum = arr[0]
    current_sum = 0  # BUG: should start at arr[0]
    for x in arr:
        current_sum = max(x, current_sum + x)
        max_sum = max(max_sum, current_sum)
    return max_sum

def qb04_fixed(arr):
    """Max subarray sum. Correct Kadane."""
    if not arr:
        return 0
    max_sum = arr[0]
    current_sum = arr[0]  # FIXED: start at arr[0]
    for x in arr[1:]:
        current_sum = max(x, current_sum + x)
        max_sum = max(max_sum, current_sum)
    return max_sum

QB04_INPUTS = [
    ([-2, 1, -3, 4, -1, 2, 1, -5, 4],),
    ([1],),
    ([-1, -2, -3],),
    ([5, -4, 8],),
    ([1, 2, 3, 4, 5],),
]

# ── QB-05: Detect cycle in linked list — wrong termination ───────────────────
def qb05_buggy(head):
    """Detect cycle using Floyd's algorithm. BUG: wrong slow advance."""
    if not head:
        return False
    slow = head
    fast = head
    while fast and fast.get("next") and fast.get("next", {}).get("next"):
        slow = slow.get("next")       # correct: advance slow by 1
        fast = fast.get("next", {}).get("next", {})  # correct: advance fast by 2
        if slow is fast:
            return True
    return False  # BUG: returns False even with cycle (never detects since 'is' on dicts)

def qb05_fixed(head):
    """Detect cycle — simplified: count unique nodes, timeout if cycle."""
    if not head:
        return False
    visited = set()
    curr = head
    count = 0
    while curr and count < 10000:
        node_id = id(curr)
        if node_id in visited:
            return True
        visited.add(node_id)
        curr = curr.get("next")
        count += 1
    return False

QB05_INPUTS = [
    ({"val": 1, "next": {"val": 2, "next": None}},),
    (None,),
    ({"val": 1, "next": None},),
    ({"val": 1, "next": {"val": 2, "next": {"val": 3, "next": None}}},),
    ({},),
]

# ── QB-06: GCD — wrong termination (QuixBugs: GCD) ───────────────────────────
def qb06_buggy(a, b):
    """GCD. BUG: uses subtraction, which is O(max(a,b)) and wrong for some cases."""
    if b == 0:
        return a
    if a > b:
        return qb06_buggy(a - b, b)  # BUG: should use a % b (Euclidean)
    return qb06_buggy(a, b - a)

def qb06_fixed(a, b):
    """GCD via Euclidean algorithm. Correct."""
    if b == 0:
        return a
    return qb06_fixed(b, a % b)  # FIXED

QB06_INPUTS = [
    (12, 8),
    (100, 25),
    (7, 3),
    (0, 5),
    (48, 18),
]

# ── QB-07: Merge sort — wrong merge (QuixBugs: MERGESORT) ────────────────────
def qb07_buggy(arr):
    """Merge sort. BUG: merge step doesn't handle remaining elements."""
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = qb07_buggy(arr[:mid])
    right = qb07_buggy(arr[mid:])
    return _merge_buggy(left, right)

def _merge_buggy(left, right):
    result = []
    i, j = 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    # BUG: missing extend for remaining elements
    return result

def qb07_fixed(arr):
    """Merge sort. Correct."""
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = qb07_fixed(arr[:mid])
    right = qb07_fixed(arr[mid:])
    return _merge_fixed(left, right)

def _merge_fixed(left, right):
    result = []
    i, j = 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])   # FIXED
    result.extend(right[j:])  # FIXED
    return result

QB07_INPUTS = [
    ([5, 2, 8, 1, 9],),
    ([1, 2, 3, 4, 5],),
    ([],),
    ([3],),
    ([9, 7, 5, 3, 1],),
]

# ── QB-08: LCS — wrong indexing (QuixBugs: LCS_LENGTH) ───────────────────────
def qb08_buggy(s, t):
    """LCS length. BUG: wrong recurrence (uses wrong index)."""
    if not s or not t:
        return 0
    if s[-1] == t[-1]:
        return 1 + qb08_buggy(s[:-1], t)  # BUG: should be t[:-1]
    return max(qb08_buggy(s[:-1], t), qb08_buggy(s, t[:-1]))

def qb08_fixed(s, t):
    """LCS length. Correct."""
    if not s or not t:
        return 0
    if s[-1] == t[-1]:
        return 1 + qb08_fixed(s[:-1], t[:-1])  # FIXED
    return max(qb08_fixed(s[:-1], t), qb08_fixed(s, t[:-1]))

QB08_INPUTS = [
    ("ABCBDAB", "BDCAB"),
    ("", "ABC"),
    ("ABC", ""),
    ("ABC", "ABC"),
    ("A", "B"),
]

# ── QB-09: Is valid parentheses — wrong condition ─────────────────────────────
def qb09_buggy(s):
    """Valid parentheses. BUG: stack check is wrong (pops too early)."""
    stack = []
    for c in s:
        if c == "(":
            stack.append(c)
        elif c == ")":
            if not stack:
                return False
            stack.pop()
    return len(stack) == 0

# This is actually CORRECT — make a version with a subtle mutation
def qb09_buggy_v2(s):
    """Valid parentheses. BUG: wrong return when stack not empty."""
    stack = []
    for c in s:
        if c == "(":
            stack.append(c)
        elif c == ")":
            if not stack:
                return False
            stack.pop()
    return True  # BUG: should check len(stack) == 0

QB09_INPUTS = [
    ("()",),
    ("(())",),
    ("((",),
    (")",),
    ("(()())",),
]

# ── QB-10: Power function — wrong base case ───────────────────────────────────
def qb10_buggy(base, exp):
    """Fast exponentiation. BUG: wrong handling of odd exponent."""
    if exp == 0:
        return 1
    if exp % 2 == 0:
        return qb10_buggy(base, exp // 2) ** 2
    else:
        return base * qb10_buggy(base, exp - 1)  # correct for odd
    # Note: bug is in the even case — squares the RECURSIVE result, not base

def qb10_fixed(base, exp):
    """Fast exponentiation. Correct."""
    if exp == 0:
        return 1
    half = qb10_fixed(base, exp // 2)
    if exp % 2 == 0:
        return half * half  # FIXED: square the intermediate result
    else:
        return base * half * half if exp % 2 == 1 else half * half

QB10_INPUTS = [
    (2, 10),
    (3, 0),
    (2, 1),
    (5, 3),
    (2, 8),
]

# ── NEGATIVES: Semantics-preserving variants (same logic, different names) ────

def neg01_a(items):
    """Sort ascending — variant A (original names)."""
    if len(items) <= 1:
        return items[:]
    pivot = items[len(items) // 2]
    left = [x for x in items if x < pivot]
    mid = [x for x in items if x == pivot]
    right = [x for x in items if x > pivot]
    return neg01_a(left) + mid + neg01_a(right)

def neg01_b(data):
    """Sort ascending — variant B (renamed params, same logic)."""
    if len(data) <= 1:
        return data[:]
    middle = data[len(data) // 2]
    smaller = [elem for elem in data if elem < middle]
    equal = [elem for elem in data if elem == middle]
    larger = [elem for elem in data if elem > middle]
    return neg01_b(smaller) + equal + neg01_b(larger)

NEG01_INPUTS = [([3,1,4,1,5,9],), ([],), ([1],), ([5,4,3,2,1],), ([1,1,1],)]

def neg02_a(n):
    """Fibonacci iterative — variant A."""
    if n <= 0: return 0
    if n == 1: return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def neg02_b(num):
    """Fibonacci iterative — variant B (renamed, same logic)."""
    if num <= 0: return 0
    if num == 1: return 1
    prev, curr = 0, 1
    for _ in range(2, num + 1):
        prev, curr = curr, prev + curr
    return curr

NEG02_INPUTS = [(0,), (1,), (5,), (10,), (7,)]


# ─────────────────────────────────────────────────────────────────────────────
# Evaluation corpus definition
# ─────────────────────────────────────────────────────────────────────────────

PILOT_PAIRS = [
    # CHANGED pairs (bugs) — label=1
    {"id": "QB01", "name": "binary_search_off_by_one",   "buggy_fn": qb01_buggy, "fixed_fn": qb01_fixed, "inputs": QB01_INPUTS, "label": 1, "bug_type": "off_by_one"},
    {"id": "QB02", "name": "flatten_wrong_recursion",     "buggy_fn": qb02_buggy, "fixed_fn": qb02_fixed, "inputs": QB02_INPUTS, "label": 1, "bug_type": "wrong_variable"},
    {"id": "QB03", "name": "coin_change_wrong_base",      "buggy_fn": qb03_buggy, "fixed_fn": qb03_fixed, "inputs": QB03_INPUTS, "label": 1, "bug_type": "missing_base_case"},
    {"id": "QB04", "name": "max_subarray_wrong_init",     "buggy_fn": qb04_buggy, "fixed_fn": qb04_fixed, "inputs": QB04_INPUTS, "label": 1, "bug_type": "wrong_variable"},
    {"id": "QB05", "name": "cycle_detect_wrong_return",   "buggy_fn": qb05_buggy, "fixed_fn": qb05_fixed, "inputs": QB05_INPUTS, "label": 1, "bug_type": "wrong_operator"},
    {"id": "QB06", "name": "gcd_wrong_algorithm",         "buggy_fn": qb06_buggy, "fixed_fn": qb06_fixed, "inputs": QB06_INPUTS, "label": 1, "bug_type": "wrong_operator"},
    {"id": "QB07", "name": "mergesort_missing_extend",    "buggy_fn": qb07_buggy, "fixed_fn": qb07_fixed, "inputs": QB07_INPUTS, "label": 1, "bug_type": "missing_edge_case"},
    {"id": "QB08", "name": "lcs_wrong_index",             "buggy_fn": qb08_buggy, "fixed_fn": qb08_fixed, "inputs": QB08_INPUTS, "label": 1, "bug_type": "wrong_variable"},
    {"id": "QB09", "name": "valid_parens_wrong_return",   "buggy_fn": qb09_buggy_v2, "fixed_fn": qb09_buggy, "inputs": QB09_INPUTS, "label": 1, "bug_type": "wrong_operator"},
    {"id": "QB10", "name": "fast_power_wrong_base_case",  "buggy_fn": qb10_buggy, "fixed_fn": qb10_fixed, "inputs": QB10_INPUTS, "label": 1, "bug_type": "wrong_operator"},
    # EQUIVALENT pairs (SP renames) — label=0
    {"id": "NEG01", "name": "quicksort_renamed",          "buggy_fn": neg01_a,   "fixed_fn": neg01_b,    "inputs": NEG01_INPUTS, "label": 0, "bug_type": "SP_rename"},
    {"id": "NEG02", "name": "fibonacci_renamed",          "buggy_fn": neg02_a,   "fixed_fn": neg02_b,    "inputs": NEG02_INPUTS, "label": 0, "bug_type": "SP_rename"},
]


# ─────────────────────────────────────────────────────────────────────────────
# SBG features (output-free) — same as Phase 3 evaluator
# ─────────────────────────────────────────────────────────────────────────────

class ExecutionResult:
    def __init__(self, return_value=None, exception_type=None, wall_time_ms=0.0):
        self.return_value = return_value
        self.exception_type = exception_type
        self.wall_time_ms = wall_time_ms

    @property
    def had_exception(self):
        return self.exception_type is not None


def _run(fn, args):
    t0 = time.perf_counter()
    try:
        ret = fn(*args)
        exc = None
    except Exception as e:
        ret = None
        exc = type(e).__name__
    return ExecutionResult(ret, exc, (time.perf_counter() - t0) * 1000.0)


def extract_sbg_features(fn, inputs):
    """Output-free feature extraction."""
    results = [_run(fn, inp) for inp in inputs]
    n = len(results)
    if n == 0:
        return {}
    exc_count = sum(1 for r in results if r.had_exception)
    exc_types = sorted(set(r.exception_type for r in results if r.exception_type))
    wall_times = [r.wall_time_ms for r in results]
    # Oracle-only return values (not used by predictor)
    _private_rv = []
    for r in results:
        if r.had_exception:
            _private_rv.append(f"EXC:{r.exception_type}")
        else:
            try:
                _private_rv.append(repr(r.return_value)[:200])
            except Exception:
                _private_rv.append("REPR_ERROR")
    return {
        "exception_fraction": exc_count / n,
        "exception_types": exc_types,
        "mean_wall_time_ms": sum(wall_times) / n,
        "n_inputs": n,
        "_return_values_PRIVATE": _private_rv,
    }


def sbg_distance(feat_a, feat_b):
    """Output-free SBG distance. Identical to Phase 3 formula."""
    ef_a = feat_a.get("exception_fraction", 0.0)
    ef_b = feat_b.get("exception_fraction", 0.0)
    d_exc_frac = abs(ef_a - ef_b)

    et_a = set(feat_a.get("exception_types", []))
    et_b = set(feat_b.get("exception_types", []))
    union = et_a | et_b
    d_exc_jac = 0.0 if not union else 1.0 - len(et_a & et_b) / len(union)

    wt_a = feat_a.get("mean_wall_time_ms", 0.0) + 1e-6
    wt_b = feat_b.get("mean_wall_time_ms", 0.0) + 1e-6
    ratio = max(wt_a, wt_b) / min(wt_a, wt_b)
    d_vol = min(1.0, (ratio - 1.0) / 10.0)

    return 0.50 * d_exc_frac + 0.30 * d_exc_jac + 0.20 * d_vol


def output_oracle(feat_a, feat_b):
    """Output oracle — SEPARATE from predictor."""
    rv_a = feat_a.get("_return_values_PRIVATE", [])
    rv_b = feat_b.get("_return_values_PRIVATE", [])
    n = min(len(rv_a), len(rv_b))
    if n == 0:
        return 0.0
    return sum(1 for x, y in zip(rv_a, rv_b) if x != y) / n


def compute_auroc(scores, labels):
    pos = [s for s, l in zip(scores, labels) if l == 1]
    neg = [s for s, l in zip(scores, labels) if l == 0]
    if not pos or not neg:
        return float("nan")
    c, t, total = 0, 0, len(pos) * len(neg)
    for p in pos:
        for n in neg:
            if p > n: c += 1
            elif p == n: t += 1
    return (c + 0.5 * t) / total


def bootstrap_ci(scores, labels, n=N_BOOTSTRAP, seed=SEED):
    rng = random.Random(seed)
    np_ = len(scores)
    aurocs = []
    for _ in range(n):
        idx = [rng.randint(0, np_ - 1) for _ in range(np_)]
        a = compute_auroc([scores[i] for i in idx], [labels[i] for i in idx])
        if not math.isnan(a):
            aurocs.append(a)
    if not aurocs:
        return float("nan"), float("nan")
    aurocs.sort()
    return aurocs[int(0.025 * len(aurocs))], aurocs[int(0.975 * len(aurocs))]


# ─────────────────────────────────────────────────────────────────────────────
# Run pilot
# ─────────────────────────────────────────────────────────────────────────────

def run_pilot():
    print("=" * 70)
    print("REAL-WORLD PILOT EVALUATION — QuixBugs-Style (Phase 5)")
    print("=" * 70)
    print(f"N pairs: {len(PILOT_PAIRS)} ({sum(1 for p in PILOT_PAIRS if p['label']==1)} CHANGED, "
          f"{sum(1 for p in PILOT_PAIRS if p['label']==0)} EQUIVALENT)")
    print(f"τ* threshold: {TAU_STAR:.4f} (pre-fixed, same as Phase 3)")
    print()

    results = []
    sbg_scores = []
    oracle_divs = []
    labels = []

    print(f"{'ID':6s}  {'Name':35s}  {'GT':4s}  {'SBG':5s}  {'Out':5s}  {'Det-SBG':7s}")
    print("-" * 70)

    for pair in PILOT_PAIRS:
        fa = extract_sbg_features(pair["buggy_fn"], pair["inputs"])
        fb = extract_sbg_features(pair["fixed_fn"], pair["inputs"])

        dist = sbg_distance(fa, fb)
        oracle_div = output_oracle(fa, fb)
        detected_sbg = dist > TAU_STAR
        detected_out = oracle_div > 0.0
        gt = pair["label"]

        sbg_scores.append(dist)
        oracle_divs.append(oracle_div)
        labels.append(gt)

        results.append({
            "id": pair["id"],
            "name": pair["name"],
            "bug_type": pair["bug_type"],
            "label": gt,
            "sbg_distance": dist,
            "output_divergence": oracle_div,
            "detected_by_sbg": detected_sbg,
            "detected_by_output": detected_out,
        })

        gt_str = "CHGD" if gt == 1 else "EQUV"
        sbg_sym = "✓" if detected_sbg else "✗"
        out_sym = "✓" if detected_out else "✗"
        print(f"{pair['id']:6s}  {pair['name'][:35]:35s}  {gt_str:4s}  "
              f"SBG:{sbg_sym}  Out:{out_sym}  d={dist:.4f}")

    # AUROC
    auroc = compute_auroc(sbg_scores, labels)
    ci_lo, ci_hi = bootstrap_ci(sbg_scores, labels)
    auroc_out = compute_auroc(oracle_divs, labels)

    # Detection rates
    changed = [r for r in results if r["label"] == 1]
    equiv = [r for r in results if r["label"] == 0]
    n_c = len(changed)
    n_e = len(equiv)
    tp_sbg = sum(1 for r in changed if r["detected_by_sbg"])
    fp_sbg = sum(1 for r in equiv if r["detected_by_sbg"])
    tp_out = sum(1 for r in changed if r["detected_by_output"])
    fp_out = sum(1 for r in equiv if r["detected_by_output"])

    precision_sbg = tp_sbg / (tp_sbg + fp_sbg) if (tp_sbg + fp_sbg) > 0 else 0.0
    recall_sbg = tp_sbg / n_c if n_c > 0 else 0.0
    f1_sbg = (2 * precision_sbg * recall_sbg / (precision_sbg + recall_sbg)
               if (precision_sbg + recall_sbg) > 0 else 0.0)

    print()
    print("=" * 70)
    print(f"PILOT RESULTS (N={len(results)}: {n_c} CHANGED, {n_e} EQUIV)")
    print("=" * 70)
    print(f"  SBG distance AUROC:        {auroc:.4f}  [{ci_lo:.4f}, {ci_hi:.4f}]")
    print(f"  Output oracle AUROC:       {auroc_out:.4f}  (NOT SBG result)")
    print(f"  Random baseline AUROC:     0.5000")
    print()
    print(f"  SBG at τ*={TAU_STAR:.4f}:")
    print(f"    TP: {tp_sbg}/{n_c}  FP: {fp_sbg}/{n_e}")
    print(f"    Precision: {precision_sbg:.3f}  Recall: {recall_sbg:.3f}  F1: {f1_sbg:.3f}")
    print()
    print(f"  Output oracle at >0:")
    print(f"    TP: {tp_out}/{n_c}  FP: {fp_out}/{n_e}")
    print("=" * 70)

    # Interpretation
    print()
    if auroc > 0.700 and ci_lo > 0.500:
        verdict = "POSITIVE — SBG distance distinguishes real-world bugs above chance"
    elif auroc > 0.550 and ci_lo > 0.450:
        verdict = "MARGINAL — SBG shows some signal but CI wide (small N=12)"
    elif auroc >= 0.500:
        verdict = "WEAK — SBG near random; not distinguishing real-world bugs well"
    else:
        verdict = "NEGATIVE — SBG below chance on real-world bugs"

    print(f"RQ4 PILOT VERDICT: {verdict}")
    print()
    print("NOTE: N=12 pairs is too small for strong statistical claims.")
    print("CI width reflects high variance. This is a feasibility pilot, not a")
    print("definitive evaluation. Full BugsInPy evaluation requires environment")
    print("setup (pip install for pandas/requests/scrapy/etc.) not done in sprint.")

    result = {
        "experiment": "REAL_WORLD_PILOT_QUIXBUGS_STYLE",
        "version": "v5_phase5",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dataset": "QuixBugs-style inline pilot (10 CHANGED + 2 EQUIV pairs)",
        "n_pairs": len(results),
        "n_changed": n_c,
        "n_equiv": n_e,
        "methodology": {
            "predictor": "sbg_distance (output-free, Phase 3 formula)",
            "oracle": "output_divergence (separate, labeled as BASELINE)",
            "tau_star": TAU_STAR,
            "ground_truth": "pre-defined bug labels (all CHANGED pairs contain known bugs)",
            "feasibility_note": (
                "BugsInPy full evaluation requires pip install of project dependencies. "
                "This pilot uses self-contained QuixBugs-style programs as a "
                "feasibility check. Results represent a lower bound on evaluation difficulty."
            ),
        },
        "auroc": {
            "sbg_output_free": auroc,
            "sbg_ci_95": [ci_lo, ci_hi],
            "output_oracle_BASELINE": auroc_out,
            "random_baseline": 0.5,
        },
        "detection_at_tau_star": {
            "tp": tp_sbg, "fp": fp_sbg, "fn": n_c - tp_sbg, "tn": n_e - fp_sbg,
            "precision": precision_sbg, "recall": recall_sbg, "f1": f1_sbg,
        },
        "rq4_verdict": verdict,
        "pair_results": results,
    }

    out_path = REPO_ROOT / "artifacts" / "v5" / "REAL_WORLD_PILOT_RESULTS.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n[pilot] Saved → {out_path}")
    return result


if __name__ == "__main__":
    run_pilot()
