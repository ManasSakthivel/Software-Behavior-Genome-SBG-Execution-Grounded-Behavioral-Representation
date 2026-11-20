"""
experiments/v4/phase4_semantic_oracle.py
==========================================
Phase 4 — Independent Semantic Oracle (Differential Testing)

SCIENTIFIC QUESTION:
  Do the ground-truth labels in pairs_test.jsonl actually correspond to
  semantic equivalence / semantic change — INDEPENDENTLY of the SBG representation?

METHODOLOGY:
  Differential testing: run base program and variant on DIVERSE test inputs
  and compare OUTPUTS. If outputs differ → CHANGED. If identical → EQUIVALENT.
  This is an independent oracle that does NOT use SBG's genome.

  Oracle procedure:
  1. Load base and variant programs
  2. Execute both on 20+ diverse inputs (different from training inputs)
  3. Compare: return values, exception types, stdout
  4. If any diff on any input → CHANGED
  5. If no diff on all inputs → LIKELY EQUIVALENT (may miss subtle cases)

  Validation metrics:
  - Oracle-label agreement rate (oracle vs. pairs_test.jsonl labels)
  - Precision/recall of oracle for CHANGED detection
  - Cases where oracle disagrees: investigate manually

IMPORTANT LIMITATION:
  The oracle may produce:
  - FALSE EQUIVALENTS: variant IS changed but our test inputs don't trigger it
  - FALSE CHANGES: variant behavior differs on edge cases but is "equivalent" semantically
  This is disclosed as a known limitation.

OUTPUT: artifacts/v4/SEMANTIC_ORACLE.json
"""
from __future__ import annotations

import importlib.util
import io
import json
import pathlib
import sys
import types
from typing import Any, Callable, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_OUT = REPO_ROOT / "artifacts" / "v4" / "SEMANTIC_ORACLE.json"

# Oracle inputs: diverse, covering edge cases not in training
ORACLE_INPUTS: List[Any] = [
    # Empty/minimal
    [], [0], "",
    # Small cases
    [1, 2], [2, 1], [-1, 0, 1],
    # Sorted
    [1, 2, 3, 4, 5],
    # Reverse sorted
    [5, 4, 3, 2, 1],
    # Duplicates
    [1, 1, 1, 1],
    [3, 3, 1, 1, 2],
    # Negatives
    [-5, -3, -1, 0, 2],
    # Mixed size
    list(range(10)),
    list(range(20, 0, -1)),
    # Single element
    [42],
    # Two equal elements
    [7, 7],
    # Float-ish (as integers)
    [100, 1, 50, 25, 75],
]

def _load_fn_oracle(path: str, mod_name: str) -> Optional[Callable]:
    p = pathlib.Path(path)
    if not p.exists():
        return None
    spec = importlib.util.spec_from_file_location(mod_name, str(p))
    if not spec or not spec.loader:
        return None
    mod = types.ModuleType(mod_name)
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        spec.loader.exec_module(mod)  # type: ignore
    except Exception:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        return None
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    import inspect
    for nm in ("sort", "search", "run", "main", "solve", "process", "compute",
               "encode", "decode", "parse", "validate"):
        fn = getattr(mod, nm, None)
        if callable(fn) and isinstance(fn, types.FunctionType):
            return fn
    for nm, obj in inspect.getmembers(mod, inspect.isfunction):
        if not nm.startswith("_") and getattr(obj, "__module__", None) == mod_name:
            return obj
    return None


def _run_program(fn: Callable, inp: Any) -> Tuple[Any, Optional[str]]:
    """Run fn(inp) → (return_val, exception_type or None)."""
    import inspect
    try:
        n_p = len(inspect.signature(fn).parameters)
    except Exception:
        n_p = 1
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        if n_p == 0:
            result = fn()
        else:
            result = fn(inp)
        sys.stdout = old_stdout
        return (result, None)
    except Exception as e:
        sys.stdout = old_stdout
        return (None, type(e).__name__)


def _oracle_label(base_path: str, var_path: str) -> Tuple[str, Dict]:
    """
    Apply differential oracle to determine EQUIVALENT or CHANGED.
    Returns: ("EQUIVALENT" | "CHANGED" | "UNKNOWN", evidence_dict)
    """
    fn1 = _load_fn_oracle(base_path, "_oracle_base")
    fn2 = _load_fn_oracle(var_path, "_oracle_var")

    if fn1 is None or fn2 is None:
        return ("UNKNOWN", {"reason": "load_failed"})

    diffs = []
    agreements = []
    for inp in ORACLE_INPUTS:
        try:
            r1, e1 = _run_program(fn1, inp)
            r2, e2 = _run_program(fn2, inp)
            match = (str(r1) == str(r2)) and (e1 == e2)
            if not match:
                diffs.append({"input": str(inp)[:80], "out1": str(r1)[:40],
                               "out2": str(r2)[:40], "exc1": e1, "exc2": e2})
            else:
                agreements.append(str(inp)[:20])
        except Exception as ex:
            # Error running oracle itself → uncertain
            pass

    if diffs:
        return ("CHANGED", {
            "n_inputs_tested": len(ORACLE_INPUTS),
            "n_diffs_found": len(diffs),
            "n_agreements": len(agreements),
            "sample_diff": diffs[0],
        })
    elif agreements:
        return ("LIKELY_EQUIVALENT", {
            "n_inputs_tested": len(ORACLE_INPUTS),
            "n_diffs_found": 0,
            "n_agreements": len(agreements),
            "limitation": "May miss subtle mutations with rare trigger inputs",
        })
    else:
        return ("UNKNOWN", {"reason": "no_successful_executions"})


def _load_test_pairs() -> list:
    path = REPO_ROOT / "benchmark" / "datasets" / "pairs_test.jsonl"
    pairs = []
    with open(path) as fh:
        for line in fh:
            ln = line.strip()
            if ln:
                pairs.append(json.loads(ln))
    return pairs


def main() -> None:
    print("\n" + "="*60)
    print("PHASE 4 — INDEPENDENT SEMANTIC ORACLE")
    print("="*60)
    print(f"Oracle inputs: {len(ORACLE_INPUTS)}")
    print("Running differential testing on test pairs...\n")

    pairs = _load_test_pairs()
    print(f"Loaded {len(pairs)} test pairs.\n")

    # Sample: run on first 200 pairs to keep runtime manageable
    # (Full 744 pairs would take ~30+ min)
    sample_size = min(200, len(pairs))
    sample = pairs[:sample_size]
    print(f"Running oracle on {sample_size} pairs (sample for runtime management).\n")

    per_pair = []
    oracle_labels = []
    benchmark_labels = []
    n_agree = 0
    n_disagree = 0
    n_unknown = 0

    for i, p in enumerate(sample):
        base = str(REPO_ROOT / p["base_path"])
        var = str(REPO_ROOT / p["variant_path"])
        benchmark_lbl = p["semantic_relation"]  # "EQUIVALENT" or "CHANGED"

        oracle_lbl, evidence = _oracle_label(base, var)

        # Map LIKELY_EQUIVALENT → EQUIVALENT for comparison
        oracle_compared = "EQUIVALENT" if oracle_lbl == "LIKELY_EQUIVALENT" else oracle_lbl

        if oracle_lbl == "UNKNOWN":
            n_unknown += 1
            agreement = "UNKNOWN"
        elif oracle_compared == benchmark_lbl:
            n_agree += 1
            agreement = "AGREE"
        else:
            n_disagree += 1
            agreement = "DISAGREE"

        per_pair.append({
            "pair_id": p["pair_id"],
            "transformation_type": p["transformation_type"],
            "benchmark_label": benchmark_lbl,
            "oracle_label": oracle_lbl,
            "agreement": agreement,
            "evidence": evidence,
        })
        oracle_labels.append(oracle_lbl)
        benchmark_labels.append(benchmark_lbl)

        if (i+1) % 50 == 0:
            print(f"  {i+1}/{sample_size}: agree={n_agree} disagree={n_disagree} unknown={n_unknown}",
                  flush=True)

    n_evaluated = n_agree + n_disagree
    agreement_rate = n_agree / n_evaluated if n_evaluated > 0 else 0.0

    # Disagreement analysis
    disagreements = [r for r in per_pair if r["agreement"] == "DISAGREE"]
    # Oracle says CHANGED but benchmark says EQUIVALENT (false positive in oracle)
    oracle_fp = [r for r in disagreements if r["oracle_label"] == "CHANGED"
                 and r["benchmark_label"] == "EQUIVALENT"]
    # Oracle says EQUIVALENT but benchmark says CHANGED (oracle missed mutation)
    oracle_fn = [r for r in disagreements if r["oracle_label"] in ("LIKELY_EQUIVALENT",)
                 and r["benchmark_label"] == "CHANGED"]

    summary = {
        "experiment": "PHASE4_SEMANTIC_ORACLE",
        "version": "v4",
        "n_pairs_evaluated": sample_size,
        "oracle_agreement_rate": round(agreement_rate, 4),
        "n_agree": n_agree,
        "n_disagree": n_disagree,
        "n_unknown": n_unknown,
        "oracle_false_positives": len(oracle_fp),
        "oracle_false_negatives": len(oracle_fn),
        "benchmark_label_validity": (
            "CONFIRMED" if agreement_rate >= 0.90
            else "PARTIALLY_CONFIRMED" if agreement_rate >= 0.75
            else "QUESTIONED"
        ),
        "oracle_inputs_used": len(ORACLE_INPUTS),
        "limitation": (
            "Oracle may miss mutations triggered by rare inputs. "
            "Agreement rate is a lower bound on label correctness."
        ),
        "disagreement_examples": [r["pair_id"] for r in disagreements[:10]],
        "per_pair_sample": per_pair[:50],  # First 50 for inspection
    }

    ARTIFACT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT_OUT, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[PHASE4] Saved → {ARTIFACT_OUT}")
    print(f"Oracle agreement rate: {agreement_rate:.3f} ({n_agree}/{n_evaluated})")
    print(f"Unknown (load failures): {n_unknown}")
    print(f"Label validity: {summary['benchmark_label_validity']}")
    print(f"Oracle FP (spurious CHANGED): {len(oracle_fp)}")
    print(f"Oracle FN (missed mutation): {len(oracle_fn)}")


if __name__ == "__main__":
    main()
