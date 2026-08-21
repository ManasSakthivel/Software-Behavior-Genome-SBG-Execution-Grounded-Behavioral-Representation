#!/usr/bin/env python3
"""
Hard Negatives Oracle
=====================
Executes every pair's base and variant programs against their test inputs,
compares outputs, and reports which shortcut detectors are fooled by each pair.

Usage:
    python3 oracle.py
"""

import importlib.util
import json
import os
import sys
import traceback

PAIRS_DIR = os.path.dirname(os.path.abspath(__file__))

PAIRS = [
    "pair_01_same_exception_different_behavior",
    "pair_02_same_volume_different_behavior",
    "pair_03_same_call_count_different_order",
    "pair_04_rename_invariant",
    "pair_05_structural_change_same_behavior",
    "pair_06_constant_mutation",
    "pair_07_dead_code_insertion",
    "pair_08_wrong_variable",
    "pair_09_operator_mutation",
    "pair_10_exception_same_behavior",
    "pair_11_loop_boundary",
    "pair_12_data_structure_equivalent",
]


# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------

def _load_module(pair_dir, filename):
    path = os.path.join(PAIRS_DIR, pair_dir, filename)
    spec = importlib.util.spec_from_file_location(
        f"{pair_dir}.{filename[:-3]}", path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Safe executor
# ---------------------------------------------------------------------------

def _safe_call(fn, inputs):
    """Call fn(inputs) and return (result, exception_string | None)."""
    try:
        return fn(inputs), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# Shortcut detectors
# (simplified heuristics that a naive evaluator might use)
# ---------------------------------------------------------------------------

def detect_exception_fraction(results):
    """Fraction of outputs that are exception strings."""
    if not results:
        return 0.0
    exc = sum(1 for r in results if isinstance(r, str) and "Error" in r)
    return exc / len(results)


def detect_volume(results):
    """Proxy for execution volume: total length of all output items."""
    total = 0
    for r in results:
        if isinstance(r, list):
            total += len(r)
        else:
            total += 1
    return total


def detect_call_count(mod):
    """
    Proxy for call-count shortcut: count top-level def statements in source.
    (A real detector would trace calls; here we count named functions.)
    """
    import ast
    src_path = mod.__spec__.origin
    with open(src_path) as f:
        tree = ast.parse(f.read())
    return sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))


# ---------------------------------------------------------------------------
# Per-pair evaluation
# ---------------------------------------------------------------------------

def evaluate_pair(pair_dir):
    meta_path = os.path.join(PAIRS_DIR, pair_dir, "metadata.json")
    with open(meta_path) as f:
        meta = json.load(f)

    base_mod = _load_module(pair_dir, "base_program.py")
    variant_mod = _load_module(pair_dir, "variant_program.py")
    inputs_mod = _load_module(pair_dir, "test_inputs.py")
    test_inputs = inputs_mod.TEST_INPUTS

    base_result, base_exc = _safe_call(base_mod.run, test_inputs)
    variant_result, variant_exc = _safe_call(variant_mod.run, test_inputs)

    # Behavioral divergence: any difference in outputs?
    outputs_match = (base_result == variant_result) and (base_exc == variant_exc)
    oracle_label = "EQUIV" if outputs_match else "CHANGED"
    ground_truth = meta["ground_truth"]
    oracle_correct = oracle_label == ground_truth

    # Shortcut detector verdicts
    base_exc_frac = detect_exception_fraction(base_result or [])
    var_exc_frac = detect_exception_fraction(variant_result or [])
    shortcut_exc_same = abs(base_exc_frac - var_exc_frac) < 0.01
    shortcut_exc_verdict = "EQUIV" if shortcut_exc_same else "CHANGED"
    shortcut_exc_correct = shortcut_exc_verdict == ground_truth

    base_vol = detect_volume(base_result or [])
    var_vol = detect_volume(variant_result or [])
    shortcut_vol_same = base_vol == var_vol
    shortcut_vol_verdict = "EQUIV" if shortcut_vol_same else "CHANGED"
    shortcut_vol_correct = shortcut_vol_verdict == ground_truth

    base_calls = detect_call_count(base_mod)
    var_calls = detect_call_count(variant_mod)
    shortcut_call_same = base_calls == var_calls
    shortcut_call_verdict = "EQUIV" if shortcut_call_same else "CHANGED"
    shortcut_call_correct = shortcut_call_verdict == ground_truth

    return {
        "pair_id": pair_dir,
        "ground_truth": ground_truth,
        "oracle_label": oracle_label,
        "oracle_correct": oracle_correct,
        "shortcut_defeated": meta["shortcut_defeated"],
        "exception_fraction": {
            "base": round(base_exc_frac, 3),
            "variant": round(var_exc_frac, 3),
            "verdict": shortcut_exc_verdict,
            "correct": shortcut_exc_correct,
        },
        "volume": {
            "base": base_vol,
            "variant": var_vol,
            "verdict": shortcut_vol_verdict,
            "correct": shortcut_vol_correct,
        },
        "call_count": {
            "base": base_calls,
            "variant": var_calls,
            "verdict": shortcut_call_verdict,
            "correct": shortcut_call_correct,
        },
        "base_exc": base_exc,
        "variant_exc": variant_exc,
    }


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

def _tick(correct):
    return "PASS" if correct else "FAIL"


def print_summary(results):
    w_id = 46
    w_gt = 7
    w_or = 7
    w_sc = 8
    w_ef = 6
    w_vol = 6
    w_cc = 6

    header = (
        f"{'Pair':<{w_id}} {'GT':<{w_gt}} {'Oracle':<{w_or}} "
        f"{'Shortcut':<{w_sc}} {'EF':<{w_ef}} {'Vol':<{w_vol}} {'CC':<{w_cc}}"
    )
    sep = "-" * len(header)
    print("\n" + sep)
    print("HARD NEGATIVES ORACLE — SUMMARY")
    print(sep)
    print(header)
    print(sep)

    oracle_correct_total = 0
    ef_correct_total = 0
    vol_correct_total = 0
    cc_correct_total = 0

    for r in results:
        oracle_flag = "✓" if r["oracle_correct"] else "✗"
        print(
            f"{r['pair_id']:<{w_id}} "
            f"{r['ground_truth']:<{w_gt}} "
            f"{r['oracle_label']:<{w_or}} "
            f"{r['shortcut_defeated']:<{w_sc}} "
            f"{_tick(r['exception_fraction']['correct']):<{w_ef}} "
            f"{_tick(r['volume']['correct']):<{w_vol}} "
            f"{_tick(r['call_count']['correct']):<{w_cc}} "
            f"{oracle_flag}"
        )
        oracle_correct_total += int(r["oracle_correct"])
        ef_correct_total += int(r["exception_fraction"]["correct"])
        vol_correct_total += int(r["volume"]["correct"])
        cc_correct_total += int(r["call_count"]["correct"])

    n = len(results)
    print(sep)
    print(
        f"{'TOTALS':<{w_id}} "
        f"{'':<{w_gt}} "
        f"{oracle_correct_total}/{n:<{w_or - 2}} "
        f"{'':<{w_sc}} "
        f"{ef_correct_total}/{n:<{w_ef - 2}} "
        f"{vol_correct_total}/{n:<{w_vol - 2}} "
        f"{cc_correct_total}/{n}"
    )
    print(sep)
    print()
    print("Columns: GT=Ground Truth  EF=exception_fraction  Vol=volume  CC=call_count")
    print("PASS = shortcut got the right label, FAIL = shortcut was fooled")
    print("✓/✗ = oracle (behavioral comparison) correct/incorrect")

    # Failures that fool each shortcut
    print()
    for label, key in [
        ("exception_fraction", "exception_fraction"),
        ("volume", "volume"),
        ("call_count", "call_count"),
    ]:
        fooled = [r["pair_id"] for r in results if not r[key]["correct"]]
        if fooled:
            print(f"Pairs that fool '{label}': {', '.join(fooled)}")
        else:
            print(f"Pairs that fool '{label}': none")

    # Oracle failures
    wrong = [r["pair_id"] for r in results if not r["oracle_correct"]]
    if wrong:
        print(f"\n⚠ Oracle WRONG on: {', '.join(wrong)}")
    else:
        print(f"\n✓ Oracle correct on all {n} pairs.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    results = []
    errors = []
    for pair in PAIRS:
        try:
            result = evaluate_pair(pair)
            results.append(result)
        except Exception as e:
            errors.append((pair, traceback.format_exc()))
            print(f"ERROR evaluating {pair}: {e}", file=sys.stderr)

    if results:
        print_summary(results)

    if errors:
        print(f"\n{len(errors)} pair(s) failed to evaluate:", file=sys.stderr)
        for pair, tb in errors:
            print(f"\n--- {pair} ---", file=sys.stderr)
            print(tb, file=sys.stderr)

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
