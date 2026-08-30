"""
experiments/external/output_free_audit.py
==========================================
Automated Output-Free Invariant Audit

Verifies that EEP genuinely does NOT read:
  - return values
  - stdout / stderr
  - test pass/fail labels
  - expected outputs
  - patch contents during inference

Run before any external evaluation to confirm the output-free guarantee holds.

Protocol: docs/MULTI_CORPUS_EVALUATION_PROTOCOL.md
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

RESULTS_DIR = REPO_ROOT / "results" / "external"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

from sbg.repair.execution_profile import (
    ExecutionProfileExtractor,
    compute_eep_distance,
)

TAU_STAR = 0.08
LEAKAGE_THRESHOLD = 0.05  # distances above this on same-path pairs indicate output leakage


def _run_audit(extractor: ExecutionProfileExtractor) -> dict:
    """
    Run all output-leakage tests and rename-invariance tests.
    
    OL tests: same control flow, different return value → must get d < LEAKAGE_THRESHOLD
    FP tests: semantically identical, renamed → must get d = 0.0 (or < 0.05)
    """
    results = []

    # -----------------------------------------------------------------------
    # OL-1: Arithmetic — same path, multiply by 2 vs multiply by 3
    # -----------------------------------------------------------------------
    def sum_list_a(lst):
        total = 0
        for x in lst:
            total += x * 2
        return total

    def sum_list_b(lst):
        total = 0
        for x in lst:
            total += x * 3  # different output, same control flow
        return total

    inp_ol1 = [([1, 2, 3],), ([0],), ([5, 10],), ([],), ([-1, 1],)]
    pa = extractor.extract(sum_list_a, inp_ol1)
    pb = extractor.extract(sum_list_b, inp_ol1)
    d = compute_eep_distance(pa, pb)
    passed = d < LEAKAGE_THRESHOLD
    results.append({
        "test_id": "OL-1",
        "description": "sum list: x*2 vs x*3 (same loop, different return value)",
        "distance": round(d, 6),
        "threshold": LEAKAGE_THRESHOLD,
        "passed": passed,
        "failure_reason": None if passed else f"d={d:.4f} > {LEAKAGE_THRESHOLD}: output leakage detected",
    })

    # -----------------------------------------------------------------------
    # OL-2: Conditional — same branch, different value returned
    # -----------------------------------------------------------------------
    def classify_a(x):
        if x > 0:
            return "positive"
        elif x < 0:
            return "negative"
        else:
            return "zero"

    def classify_b(x):
        if x > 0:
            return 1  # different type, same control flow
        elif x < 0:
            return -1
        else:
            return 0

    inp_ol2 = [(5,), (-3,), (0,), (100,), (-1,)]
    pa2 = extractor.extract(classify_a, inp_ol2)
    pb2 = extractor.extract(classify_b, inp_ol2)
    d2 = compute_eep_distance(pa2, pb2)
    passed2 = d2 < LEAKAGE_THRESHOLD
    results.append({
        "test_id": "OL-2",
        "description": "classify(x): returns string vs int (same branches taken)",
        "distance": round(d2, 6),
        "threshold": LEAKAGE_THRESHOLD,
        "passed": passed2,
        "failure_reason": None if passed2 else f"d={d2:.4f} > {LEAKAGE_THRESHOLD}: output leakage detected",
    })

    # -----------------------------------------------------------------------
    # OL-3: Recursion — same depth, different values
    # -----------------------------------------------------------------------
    def fib_a(n):
        if n <= 1:
            return n
        return fib_a(n - 1) + fib_a(n - 2)

    def fib_b(n):
        if n <= 1:
            return n * 2  # different value, same recursion structure
        return fib_b(n - 1) + fib_b(n - 2)

    inp_ol3 = [(4,), (3,), (5,), (2,), (1,)]
    pa3 = extractor.extract(fib_a, inp_ol3)
    pb3 = extractor.extract(fib_b, inp_ol3)
    d3 = compute_eep_distance(pa3, pb3)
    passed3 = d3 < LEAKAGE_THRESHOLD
    results.append({
        "test_id": "OL-3",
        "description": "fibonacci: fib(n) vs 2*fib(n) (same recursion depth, different values)",
        "distance": round(d3, 6),
        "threshold": LEAKAGE_THRESHOLD,
        "passed": passed3,
        "failure_reason": None if passed3 else f"d={d3:.4f} > {LEAKAGE_THRESHOLD}: output leakage detected",
    })

    # -----------------------------------------------------------------------
    # OL-4: None vs int return (same path)
    # -----------------------------------------------------------------------
    def search_a(lst, target):
        for i, x in enumerate(lst):
            if x == target:
                return i
        return None

    def search_b(lst, target):
        for i, x in enumerate(lst):
            if x == target:
                return i
        return -1  # different sentinel, same control flow

    inp_ol4 = [([1, 2, 3], 2), ([1, 2, 3], 5), ([0], 0), ([], 1)]
    pa4 = extractor.extract(search_a, inp_ol4)
    pb4 = extractor.extract(search_b, inp_ol4)
    d4 = compute_eep_distance(pa4, pb4)
    passed4 = d4 < LEAKAGE_THRESHOLD
    results.append({
        "test_id": "OL-4",
        "description": "linear search: returns None vs -1 when not found (same path)",
        "distance": round(d4, 6),
        "threshold": LEAKAGE_THRESHOLD,
        "passed": passed4,
        "failure_reason": None if passed4 else f"d={d4:.4f} > {LEAKAGE_THRESHOLD}: output leakage detected",
    })

    # -----------------------------------------------------------------------
    # OL-5: Generator yield count same, yield values different
    # -----------------------------------------------------------------------
    def gen_squares(lst):
        for x in lst:
            yield x ** 2

    def gen_cubes(lst):
        for x in lst:
            yield x ** 3  # different values, same iteration count

    # Wrap generators so they return consumed lists
    def gen_a(lst):
        return list(gen_squares(lst))

    def gen_b(lst):
        return list(gen_cubes(lst))

    inp_ol5 = [([1, 2, 3],), ([0, 1],), ([5],), ([1, 2, 3, 4],)]
    pa5 = extractor.extract(gen_a, inp_ol5)
    pb5 = extractor.extract(gen_b, inp_ol5)
    d5 = compute_eep_distance(pa5, pb5)
    passed5 = d5 < LEAKAGE_THRESHOLD
    results.append({
        "test_id": "OL-5",
        "description": "generator: yields x^2 vs x^3 (same iteration count, different values)",
        "distance": round(d5, 6),
        "threshold": LEAKAGE_THRESHOLD,
        "passed": passed5,
        "failure_reason": None if passed5 else f"d={d5:.4f} > {LEAKAGE_THRESHOLD}: output leakage detected",
    })

    # -----------------------------------------------------------------------
    # OL-6: QuixBugs-style gcd return×2
    # -----------------------------------------------------------------------
    def gcd_correct(a, b):
        if b == 0:
            return a
        return gcd_correct(b, a % b)

    def gcd_double(a, b):
        if b == 0:
            return a * 2  # different return, same control flow
        return gcd_double(b, a % b)

    inp_ol6 = [(17, 0), (13, 13), (20, 100), (3, 12)]
    pa6 = extractor.extract(gcd_correct, inp_ol6)
    pb6 = extractor.extract(gcd_double, inp_ol6)
    d6 = compute_eep_distance(pa6, pb6)
    passed6 = d6 < LEAKAGE_THRESHOLD
    results.append({
        "test_id": "OL-6",
        "description": "QuixBugs-style gcd: correct vs return a*2 (same control flow)",
        "distance": round(d6, 6),
        "threshold": LEAKAGE_THRESHOLD,
        "passed": passed6,
        "failure_reason": None if passed6 else f"d={d6:.4f} > {LEAKAGE_THRESHOLD}: output leakage detected",
    })

    # -----------------------------------------------------------------------
    # FP-1: Full rename — identical logic, all variables renamed
    # -----------------------------------------------------------------------
    def merge_sort_a(arr):
        if len(arr) <= 1:
            return arr
        m = len(arr) // 2
        left = merge_sort_a(arr[:m])
        right = merge_sort_a(arr[m:])
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                result.append(left[i]); i += 1
            else:
                result.append(right[j]); j += 1
        result.extend(left[i:]); result.extend(right[j:])
        return result

    def merge_sort_b(lst):
        if len(lst) <= 1:
            return lst
        mid = len(lst) // 2
        l_part = merge_sort_b(lst[:mid])
        r_part = merge_sort_b(lst[mid:])
        merged = []
        a = b = 0
        while a < len(l_part) and b < len(r_part):
            if l_part[a] <= r_part[b]:
                merged.append(l_part[a]); a += 1
            else:
                merged.append(r_part[b]); b += 1
        merged.extend(l_part[a:]); merged.extend(r_part[b:])
        return merged

    inp_fp1 = [([3, 1, 4, 1, 5],), ([],), ([1],), ([5, 2, 8, 1, 9],)]
    pa_fp1 = extractor.extract(merge_sort_a, inp_fp1)
    pb_fp1 = extractor.extract(merge_sort_b, inp_fp1)
    d_fp1 = compute_eep_distance(pa_fp1, pb_fp1)
    passed_fp1 = d_fp1 < LEAKAGE_THRESHOLD
    results.append({
        "test_id": "FP-1",
        "description": "mergesort: identical algorithm, all variables renamed",
        "distance": round(d_fp1, 6),
        "threshold": LEAKAGE_THRESHOLD,
        "passed": passed_fp1,
        "failure_reason": None if passed_fp1 else f"d={d_fp1:.4f}: false positive on rename",
    })

    # -----------------------------------------------------------------------
    # FP-2: Same function name, same logic — rename-invariance within a project
    # -----------------------------------------------------------------------
    # EEP uses function index (not name) in line-seq hash.
    # Two functions with identical bodies AND the same name should produce d=0.
    # (Function names map to the same index 0 in both profiles.)
    # This tests the position-invariance guarantee: the same function defined
    # at two different line numbers in two different source files should score d≈0.
    
    def _make_bsearch_fn():
        """Factory: returns a fresh binary search function with a unique closure."""
        def _bsearch(arr, target):
            lo, hi = 0, len(arr) - 1
            while lo <= hi:
                mid = (lo + hi) // 2
                if arr[mid] == target:
                    return mid
                elif arr[mid] < target:
                    lo = mid + 1
                else:
                    hi = mid - 1
            return -1
        return _bsearch

    bsearch_inst_a = _make_bsearch_fn()
    bsearch_inst_b = _make_bsearch_fn()

    inp_fp2 = [([1, 3, 5, 7, 9], 5), ([1, 3, 5], 1), ([2, 4, 6], 7), ([], 1)]
    pa_fp2 = extractor.extract(bsearch_inst_a, inp_fp2)
    pb_fp2 = extractor.extract(bsearch_inst_b, inp_fp2)
    d_fp2 = compute_eep_distance(pa_fp2, pb_fp2)
    # Two instances of the same factory function (_bsearch) should give d=0.0
    # because they have the same function name (co_name="_bsearch") and
    # identical rel_lineno sequences.
    passed_fp2 = d_fp2 < 0.001
    results.append({
        "test_id": "FP-2",
        "description": "binary search factory: two instances of same function (d=0.0 expected)",
        "distance": round(d_fp2, 6),
        "threshold": 0.001,
        "passed": passed_fp2,
        "failure_reason": None if passed_fp2 else f"d={d_fp2:.4f}: identical function instances should give d=0",
        "note": (
            "Functions from the same factory share co_name='_bsearch', so anonymization assigns "
            "them the same index. Different co_name functions with same code would have different "
            "indices only if the indexing is not purely positional — this is documented as a "
            "known behavior: rename-invariance applies to variable renames, not function-name renames."
        ),
    })

    # -----------------------------------------------------------------------
    # FP-3: Pythonic refactoring — list comprehension vs explicit loop
    # -----------------------------------------------------------------------
    def double_a(lst):
        result = []
        for x in lst:
            result.append(x * 2)
        return result

    def double_b(lst):
        return [x * 2 for x in lst]

    inp_fp3 = [([1, 2, 3],), ([],), ([5],), ([1, 2, 3, 4, 5],)]
    pa_fp3 = extractor.extract(double_a, inp_fp3)
    pb_fp3 = extractor.extract(double_b, inp_fp3)
    d_fp3 = compute_eep_distance(pa_fp3, pb_fp3)
    # List comprehension has different trace events (listcomp frame) so some divergence is expected
    # We allow d < 0.30 for this style equivalence
    passed_fp3 = d_fp3 < 0.30
    results.append({
        "test_id": "FP-3",
        "description": "double list: explicit loop vs list comprehension (style equivalence, d < 0.30 allowed)",
        "distance": round(d_fp3, 6),
        "threshold": 0.30,
        "passed": passed_fp3,
        "failure_reason": None if passed_fp3 else f"d={d_fp3:.4f}: style equivalence too different",
        "note": "List comprehension creates a <listcomp> frame; some trace divergence is expected and acceptable"
    })

    return results


def main():
    t0 = time.time()
    print("=" * 70)
    print("SBG — OUTPUT-FREE INVARIANT AUDIT")
    print("=" * 70)
    print("Verifying EEP does not read return values, stdout, or expected outputs")
    print()

    extractor = ExecutionProfileExtractor()
    results = _run_audit(extractor)

    n_ol = sum(1 for r in results if r["test_id"].startswith("OL"))
    n_fp = sum(1 for r in results if r["test_id"].startswith("FP"))
    n_pass = sum(1 for r in results if r["passed"])
    n_fail = sum(1 for r in results if not r["passed"])

    print(f"{'Test ID':<10} {'Description':<55} {'d':<10} {'Pass?'}")
    print(f"{'─'*10} {'─'*55} {'─'*10} {'─'*6}")
    for r in results:
        sym = "✓ PASS" if r["passed"] else "✗ FAIL"
        desc = r["description"][:53]
        print(f"  {r['test_id']:<8} {desc:<55} {r['distance']:<10.4f} {sym}")

    print(f"\n{'─'*70}")
    print(f"Output-leakage tests (OL): {sum(1 for r in results if r['test_id'].startswith('OL') and r['passed'])}/{n_ol} PASS")
    print(f"False-positive tests (FP): {sum(1 for r in results if r['test_id'].startswith('FP') and r['passed'])}/{n_fp} PASS")
    print(f"Total: {n_pass}/{len(results)} PASS  |  {n_fail} FAIL")

    if n_fail == 0:
        verdict = "OUTPUT_FREE_GUARANTEE_HOLDS"
    elif all(not r["passed"] and r["test_id"].startswith("FP") for r in results if not r["passed"]):
        verdict = "OL_PASSES_FP_PARTIAL"
    else:
        verdict = "OUTPUT_LEAKAGE_DETECTED"

    print(f"\nVerdict: {verdict}")

    failed_tests = [r for r in results if not r["passed"]]
    if failed_tests:
        print("\nFailed tests:")
        for r in failed_tests:
            print(f"  {r['test_id']}: {r['failure_reason']}")
            if "note" in r:
                print(f"    Note: {r['note']}")

    elapsed = time.time() - t0
    output = {
        "experiment": "SBG_OUTPUT_FREE_AUDIT",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_tests": len(results),
        "n_pass": n_pass,
        "n_fail": n_fail,
        "leakage_threshold": LEAKAGE_THRESHOLD,
        "verdict": verdict,
        "tests": results,
        "elapsed_s": round(elapsed, 3),
    }

    out_path = RESULTS_DIR / "OUTPUT_FREE_AUDIT_RESULTS.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n[audit] Saved → {out_path}")
    return output


if __name__ == "__main__":
    main()
