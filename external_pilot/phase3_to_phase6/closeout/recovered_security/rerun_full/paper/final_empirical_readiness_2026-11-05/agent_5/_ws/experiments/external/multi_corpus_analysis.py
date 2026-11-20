"""
experiments/external/multi_corpus_analysis.py
==============================================
Multi-Corpus Statistical Analysis

Aggregates results from all evaluated datasets and produces:
  1. Per-dataset statistics
  2. Cross-dataset comparison
  3. Combined statistical analysis
  4. Defect-class analysis (across all datasets)
  5. Project-level variance
  6. Representation limit analysis

Protocol: docs/MULTI_CORPUS_EVALUATION_PROTOCOL.md
"""

from __future__ import annotations

import json
import math
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

RESULTS_DIR = REPO_ROOT / "results" / "external"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
TAU_STAR = 0.08
N_BOOTSTRAP = 1000


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------

def auroc(scores, labels):
    pos = [s for s, l in zip(scores, labels) if l == 1]
    neg = [s for s, l in zip(scores, labels) if l == 0]
    if not pos or not neg:
        return float("nan")
    c = t = 0
    for p in pos:
        for n in neg:
            if p > n:
                c += 1
            elif p == n:
                t += 1
    return (c + 0.5 * t) / (len(pos) * len(neg))


def bootstrap_ci(scores, labels, n=N_BOOTSTRAP, seed=SEED):
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


def permutation_test(scores, labels, n_perm=1000, seed=SEED):
    rng = random.Random(seed)
    observed = auroc(scores, labels)
    if math.isnan(observed):
        return observed, 1.0
    count = 0
    for _ in range(n_perm):
        perm = list(labels)
        rng.shuffle(perm)
        a = auroc(scores, perm)
        if not math.isnan(a) and a >= observed:
            count += 1
    return observed, count / n_perm


def binomial_p(k, n, p0=0.5):
    from math import comb
    return sum(comb(n, i) * (p0 ** i) * ((1 - p0) ** (n - i)) for i in range(k, n + 1))


def prf1(scores, labels, tau):
    tp = sum(1 for s, l in zip(scores, labels) if s > tau and l == 1)
    fp = sum(1 for s, l in zip(scores, labels) if s > tau and l == 0)
    fn = sum(1 for s, l in zip(scores, labels) if s <= tau and l == 1)
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    return p, r, f1, tp, fp, fn


# ---------------------------------------------------------------------------
# Load results
# ---------------------------------------------------------------------------

def load_synthetic():
    """Load synthetic evaluation results."""
    path = REPO_ROOT / "results" / "repair" / "REPAIR_EVALUATION_RESULTS.json"
    with open(path) as f:
        d = json.load(f)
    pairs = d.get("per_pair_results", [])
    # Normalize field names for cross-dataset analysis
    norm = []
    for r in pairs:
        norm.append({
            "id": r.get("id", ""),
            "dataset": "synthetic",
            "project": "synthetic_inline",
            "bug_type": r.get("bug_type", "unknown"),
            "label": r.get("label", 1),
            "eep_full": r.get("eep_full", 0.0),
            "baseline_sbg": r.get("baseline_sbg", r.get("baseline_distance", 0.0)),
            "exc_frac_only": r.get("exc_frac_only", r.get("exception_dist", 0.0)),
            "detected_eep": r.get("detected_eep", False),
            "detected_baseline": r.get("detected_baseline", False),
            "detected_oracle": r.get("detected_oracle", False),
            "output_divergence": r.get("output_divergence", 0.0),
            "d_trace_length": r.get("d_trace_length", 0.0),
            "d_line_seq": r.get("d_line_seq", 0.0),
            "d_sequential_drift": r.get("d_sequential_drift", 0.0),
        })
    return norm


def load_quixbugs():
    """Load QuixBugs evaluation results."""
    path = REPO_ROOT / "results" / "external" / "QUIXBUGS_EVALUATION_RESULTS.json"
    with open(path) as f:
        d = json.load(f)
    pairs = d.get("per_pair_results", [])
    norm = []
    for r in pairs:
        norm.append({
            "id": r.get("id", ""),
            "dataset": "quixbugs",
            "project": r.get("name", ""),
            "bug_type": r.get("bug_type", "unknown"),
            "label": r.get("label", 1),
            "eep_full": r.get("eep_full", 0.0),
            "baseline_sbg": r.get("baseline_sbg", 0.0),
            "exc_frac_only": r.get("exc_frac_only", 0.0),
            "detected_eep": r.get("detected_eep", False),
            "detected_baseline": r.get("detected_baseline", False),
            "detected_oracle": r.get("detected_oracle", False),
            "output_divergence": r.get("output_divergence", 0.0),
            "d_trace_length": r.get("d_trace_length", 0.0),
            "d_line_seq": r.get("d_line_seq", 0.0),
            "d_sequential_drift": r.get("d_sequential_drift", 0.0),
        })
    return norm


def load_bugsinpy():
    """Load BugsInPy evaluation results."""
    path = REPO_ROOT / "results" / "external" / "BUGSINPY_EVALUATION_RESULTS.json"
    with open(path) as f:
        d = json.load(f)
    pairs = d.get("per_pair_results", [])
    norm = []
    for r in pairs:
        norm.append({
            "id": r.get("id", ""),
            "dataset": "bugsinpy",
            "project": r.get("project", ""),
            "bug_type": r.get("bug_type", "unknown"),
            "label": r.get("label", 1),
            "eep_full": r.get("eep_full", 0.0),
            "baseline_sbg": r.get("baseline_sbg", 0.0),
            "exc_frac_only": r.get("exc_frac_only", 0.0),
            "detected_eep": r.get("detected_eep", False),
            "detected_baseline": r.get("detected_baseline", False),
            "detected_oracle": r.get("detected_oracle", False),
            "output_divergence": r.get("output_divergence", 0.0),
            "d_trace_length": r.get("d_trace_length", 0.0),
            "d_line_seq": r.get("d_line_seq", 0.0),
            "d_sequential_drift": r.get("d_sequential_drift", 0.0),
        })
    return norm


# ---------------------------------------------------------------------------
# Per-dataset statistics
# ---------------------------------------------------------------------------

def compute_dataset_stats(pairs, dataset_name, n_projects):
    """Compute statistics for a single dataset."""
    bugs = [r for r in pairs if r["label"] == 1]
    negs = [r for r in pairs if r["label"] == 0]

    n_bugs = len(bugs)
    n_negs = len(negs)

    if n_bugs == 0:
        return {"dataset": dataset_name, "error": "no positive examples"}

    scores_eep = [r["eep_full"] for r in bugs]
    scores_bl = [r["baseline_sbg"] for r in bugs]
    scores_exc = [r["exc_frac_only"] for r in bugs]

    det_eep = sum(1 for r in bugs if r["detected_eep"])
    det_bl = sum(1 for r in bugs if r["detected_baseline"])
    det_exc = sum(1 for r in bugs if (r.get("detected_exc", False) or r["exc_frac_only"] > 0))
    det_out = sum(1 for r in bugs if r["detected_oracle"])
    fp_eep = sum(1 for r in negs if r["detected_eep"])

    # AUROC requires negatives
    all_scores = [r["eep_full"] for r in pairs]
    all_labels = [r["label"] for r in pairs]
    all_scores_bl = [r["baseline_sbg"] for r in pairs]
    all_scores_exc = [r["exc_frac_only"] for r in pairs]

    aur_eep = float("nan")
    ci_eep = (float("nan"), float("nan"))
    p_eep = 1.0
    aur_bl = float("nan")
    aur_exc = float("nan")

    if n_negs > 0:
        aur_eep, p_eep = permutation_test(all_scores, all_labels)
        ci_eep = bootstrap_ci(all_scores, all_labels)
        aur_bl, _ = permutation_test(all_scores_bl, all_labels)
        aur_exc, _ = permutation_test(all_scores_exc, all_labels)

    prec, rec, f1, tp, fp, fn = prf1(all_scores, all_labels, TAU_STAR)

    p_binom = binomial_p(det_eep, n_bugs)

    return {
        "dataset": dataset_name,
        "n_projects": n_projects,
        "n_bugs": n_bugs,
        "n_negatives": n_negs,
        "n_total": len(pairs),
        "detected_eep": det_eep,
        "detected_baseline": det_bl,
        "detected_oracle": det_out,
        "fp_eep": fp_eep,
        "det_rate_eep": round(det_eep / n_bugs, 4),
        "det_rate_baseline": round(det_bl / n_bugs, 4),
        "det_rate_oracle": round(det_out / n_bugs, 4),
        "fpr_eep": round(fp_eep / max(n_negs, 1), 4),
        "auroc_eep": round(aur_eep, 6) if not math.isnan(aur_eep) else None,
        "auroc_ci_eep": [round(ci_eep[0], 6), round(ci_eep[1], 6)] if not math.isnan(ci_eep[0]) else None,
        "p_permutation": round(p_eep, 4),
        "auroc_baseline": round(aur_bl, 6) if not math.isnan(aur_bl) else None,
        "auroc_exc": round(aur_exc, 6) if not math.isnan(aur_exc) else None,
        "precision_eep": round(prec, 4),
        "recall_eep": round(rec, 4),
        "f1_eep": round(f1, 4),
        "p_binomial": round(p_binom, 6),
        "mean_eep_score": round(sum(scores_eep) / max(n_bugs, 1), 4),
        "eep_outperforms_baseline": det_eep > det_bl,
        "eep_outperforms_exc": det_eep > det_exc,
    }


# ---------------------------------------------------------------------------
# Defect class analysis (across all datasets)
# ---------------------------------------------------------------------------

def defect_class_analysis(all_pairs):
    """Compute detection rates by defect class across all datasets."""
    by_class = defaultdict(list)
    for r in all_pairs:
        if r["label"] == 1:
            by_class[r["bug_type"]].append(r)

    results = {}
    for bt in sorted(by_class.keys()):
        if bt.startswith("SP_"):
            continue  # skip negative control types
        cases = by_class[bt]
        n = len(cases)
        d_e = sum(1 for r in cases if r["detected_eep"])
        d_b = sum(1 for r in cases if r["detected_baseline"])
        d_o = sum(1 for r in cases if r["detected_oracle"])
        # Classify as detectable vs invisible
        trace_changing = [r for r in cases if r["d_trace_length"] > 0 or r["d_line_seq"] > 0]
        trace_preserving = [r for r in cases if r["d_trace_length"] == 0 and r["d_line_seq"] == 0]
        results[bt] = {
            "n_total": n,
            "detected_eep": d_e,
            "detected_baseline": d_b,
            "detected_oracle": d_o,
            "rate_eep": round(d_e / n, 3),
            "rate_baseline": round(d_b / n, 3),
            "rate_oracle": round(d_o / n, 3),
            "n_trace_changing": len(trace_changing),
            "n_trace_preserving": len(trace_preserving),
            "datasets": list(set(r["dataset"] for r in cases)),
        }
    return results


# ---------------------------------------------------------------------------
# Representation limit analysis
# ---------------------------------------------------------------------------

def representation_limit_analysis(all_pairs):
    """
    Formal analysis of EEP's information-theoretic limitations.
    
    Theorem (implied by EEP's output-free guarantee):
    If programs A and B induce identical execution traces under all provided inputs,
    then d_EEP(A, B) = 0, regardless of their output behavior.
    
    This analysis measures how many evaluated bugs fall into this category.
    """
    bugs = [r for r in all_pairs if r["label"] == 1]

    trace_changing = [r for r in bugs if r["d_trace_length"] > 0 or r["d_line_seq"] > 0 or
                      r.get("d_sequential_drift", 0) > 0]
    trace_preserving = [r for r in bugs
                        if r["d_trace_length"] == 0 and r["d_line_seq"] == 0
                        and r.get("d_sequential_drift", 0) == 0]

    n_tc = len(trace_changing)
    n_tp = len(trace_preserving)

    det_tc = sum(1 for r in trace_changing if r["detected_eep"])
    det_tp = sum(1 for r in trace_preserving if r["detected_eep"])
    det_tc_oracle = sum(1 for r in trace_changing if r["detected_oracle"])
    det_tp_oracle = sum(1 for r in trace_preserving if r["detected_oracle"])

    return {
        "total_bugs": len(bugs),
        "trace_changing_n": n_tc,
        "trace_changing_det_eep": det_tc,
        "trace_changing_det_rate_eep": round(det_tc / max(n_tc, 1), 3),
        "trace_changing_det_oracle": det_tc_oracle,
        "trace_preserving_n": n_tp,
        "trace_preserving_det_eep": det_tp,
        "trace_preserving_det_rate_eep": round(det_tp / max(n_tp, 1), 3),
        "trace_preserving_det_oracle": det_tp_oracle,
        "pct_fundamentally_invisible": round(n_tp / max(len(bugs), 1) * 100, 1),
        "formal_statement": (
            "If d_trace_length = 0 AND d_line_seq = 0 AND d_sequential_drift = 0, "
            "then d_EEP = 0 by construction (output-free guarantee). "
            "These bugs produce identical control-flow traces under available instrumentation "
            "and are information-theoretically invisible to any output-free trace method."
        ),
    }


# ---------------------------------------------------------------------------
# Cross-dataset consistency
# ---------------------------------------------------------------------------

def cross_dataset_consistency(dataset_stats):
    """Analyze consistency of EEP performance across datasets."""
    det_rates = {d["dataset"]: d["det_rate_eep"] for d in dataset_stats if "det_rate_eep" in d}
    if not det_rates:
        return {}

    rates = list(det_rates.values())
    mean_rate = sum(rates) / len(rates)
    max_rate = max(rates)
    min_rate = min(rates)
    variance = sum((r - mean_rate) ** 2 for r in rates) / max(len(rates), 1)
    std = variance ** 0.5

    return {
        "dataset_detection_rates": det_rates,
        "macro_mean_det_rate": round(mean_rate, 4),
        "max_det_rate": round(max_rate, 4),
        "min_det_rate": round(min_rate, 4),
        "std_det_rate": round(std, 4),
        "range_det_rate": round(max_rate - min_rate, 4),
        "consistency_verdict": (
            "CONSISTENT" if std < 0.15
            else "MODERATE_VARIANCE" if std < 0.30
            else "HIGH_VARIANCE"
        ),
        "interpretation": (
            "Detection rates vary across datasets. This variation reflects "
            "differences in: (1) bug class composition per dataset, "
            "(2) program complexity and trace structure, "
            "(3) quality and diversity of test inputs. "
            "High variance is expected and scientifically informative — "
            "it reveals which contexts EEP works best in."
        ),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    t0 = time.time()
    print("=" * 70)
    print("SBG — MULTI-CORPUS STATISTICAL ANALYSIS")
    print("=" * 70)
    print()

    # Load all datasets
    synthetic = load_synthetic()
    quixbugs = load_quixbugs()
    bugsinpy = load_bugsinpy()

    print(f"Loaded: Synthetic N={len(synthetic)}, QuixBugs N={len(quixbugs)}, BugsInPy N={len(bugsinpy)}")

    # Per-dataset statistics
    # Synthetic: bugs only (no in-corpus negatives)
    syn_bugs = [r for r in synthetic if r["label"] == 1]
    syn_negs = [r for r in synthetic if r["label"] == 0]
    # Add synthetic data stats
    syn_stats = {
        "dataset": "synthetic",
        "n_projects": 1,
        "n_bugs": len(syn_bugs),
        "n_negatives": len(syn_negs),
        "n_total": len(synthetic),
        "detected_eep": sum(1 for r in syn_bugs if r["detected_eep"]),
        "detected_baseline": sum(1 for r in syn_bugs if r["detected_baseline"]),
        "detected_oracle": sum(1 for r in syn_bugs if r["detected_oracle"]),
        "fp_eep": sum(1 for r in syn_negs if r["detected_eep"]) if syn_negs else 0,
        "det_rate_eep": 0.6316,  # from frozen baseline doc
        "det_rate_baseline": 0.1053,
        "det_rate_oracle": 0.8158,
        "auroc_eep": 0.829,
        "auroc_ci_eep": [0.750, 0.905],
        "p_permutation": 0.162,
        "p_binomial": None,
        "precision_eep": 1.0,
        "recall_eep": 0.6316,
        "f1_eep": 0.774,
        "mean_eep_score": None,
        "eep_outperforms_baseline": True,
        "eep_outperforms_exc": True,
    }

    qb_stats = compute_dataset_stats(quixbugs, "quixbugs", n_projects=31)
    bip_stats = compute_dataset_stats(bugsinpy, "bugsinpy", n_projects=10)

    dataset_stats = [syn_stats, qb_stats, bip_stats]

    # Print per-dataset table
    print(f"\n{'─'*70}")
    print(f"PER-DATASET RESULTS")
    print(f"{'─'*70}")
    print(f"{'Dataset':<15} {'N_bugs':<8} {'Det/N':>8} {'DetRate':>9} {'AUROC':>8} {'p':>8} {'F1':>7}")
    print(f"{'─'*15} {'─'*8} {'─'*8} {'─'*9} {'─'*8} {'─'*8} {'─'*7}")
    for ds in dataset_stats:
        n = ds.get("n_bugs", 0)
        det = ds.get("detected_eep", 0)
        dr = ds.get("det_rate_eep", 0)
        aur = ds.get("auroc_eep")
        p = ds.get("p_permutation") or ds.get("p_binomial", "—")
        f1 = ds.get("f1_eep", "—")
        aur_str = f"{aur:.3f}" if aur else "—"
        p_str = f"{p:.3f}" if isinstance(p, float) else str(p)
        f1_str = f"{f1:.3f}" if isinstance(f1, float) else str(f1)
        print(f"  {ds['dataset']:<13} {n:<8} {det}/{n:<6} {dr:.1%}     {aur_str:>8} {p_str:>8} {f1_str:>7}")

    # Macro-average
    macro_avg = sum(d["det_rate_eep"] for d in dataset_stats) / len(dataset_stats)
    print(f"\n  Macro-average detection rate: {macro_avg:.1%}")
    print(f"  (NOT a pooled score — see per-dataset above for primary result)")

    # All pairs combined (for defect class analysis)
    all_pairs = synthetic + quixbugs + bugsinpy

    # Defect class analysis
    print(f"\n{'─'*70}")
    print(f"DEFECT CLASS ANALYSIS (across all datasets)")
    print(f"{'─'*70}")
    class_results = defect_class_analysis(all_pairs)
    print(f"  {'BugType':<25} {'N':<5} {'EEP Det':<10} {'Rate':<8} {'Oracle Rate':<12} {'Trace-Changing?'}")
    print(f"  {'─'*25} {'─'*5} {'─'*10} {'─'*8} {'─'*12} {'─'*15}")
    for bt, cr in sorted(class_results.items(), key=lambda x: -x[1]["rate_eep"]):
        tc_note = f"TC={cr['n_trace_changing']}/TP={cr['n_trace_preserving']}"
        print(f"  {bt:<25} {cr['n_total']:<5} {cr['detected_eep']}/{cr['n_total']:<7} "
              f"{cr['rate_eep']:.0%}     {cr['rate_oracle']:.0%}          {tc_note}")

    # Representation limit analysis
    print(f"\n{'─'*70}")
    print(f"REPRESENTATION LIMIT ANALYSIS")
    print(f"{'─'*70}")
    rl = representation_limit_analysis(all_pairs)
    print(f"  Total bugs: {rl['total_bugs']}")
    print(f"  Trace-changing (detectable class):  N={rl['trace_changing_n']}, "
          f"EEP detects {rl['trace_changing_det_eep']}/{rl['trace_changing_n']} "
          f"= {rl['trace_changing_det_rate_eep']:.0%}")
    print(f"  Trace-preserving (invisible class): N={rl['trace_preserving_n']}, "
          f"EEP detects {rl['trace_preserving_det_eep']}/{rl['trace_preserving_n']} "
          f"= {rl['trace_preserving_det_rate_eep']:.0%}")
    print(f"  Fundamentally invisible: {rl['pct_fundamentally_invisible']}% of all bugs")
    print(f"\n  Formal limitation:")
    print(f"  {rl['formal_statement'][:80]}")
    print(f"  {rl['formal_statement'][80:]}")

    # Cross-dataset consistency
    print(f"\n{'─'*70}")
    print(f"CROSS-DATASET CONSISTENCY")
    print(f"{'─'*70}")
    consistency = cross_dataset_consistency(dataset_stats)
    for ds, rate in consistency.get("dataset_detection_rates", {}).items():
        print(f"  {ds}: {rate:.1%}")
    print(f"  Macro-mean: {consistency.get('macro_mean_det_rate', 0):.1%}")
    print(f"  Std: {consistency.get('std_det_rate', 0):.3f}")
    print(f"  Verdict: {consistency.get('consistency_verdict', 'UNKNOWN')}")

    elapsed = time.time() - t0

    output = {
        "experiment": "SBG_MULTI_CORPUS_ANALYSIS",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "datasets_included": ["synthetic", "quixbugs", "bugsinpy"],
        "per_dataset_stats": dataset_stats,
        "macro_mean_detection_rate": round(macro_avg, 4),
        "defect_class_results": class_results,
        "representation_limit_analysis": rl,
        "cross_dataset_consistency": consistency,
        "elapsed_s": round(elapsed, 2),
        "reporting_note": (
            "Macro-average is mean of per-dataset detection rates, NOT a pooled score. "
            "Per-dataset results are the primary scientific evidence. "
            "The macro-average summarizes generalization across independent contexts."
        ),
    }

    out_path = RESULTS_DIR / "MULTI_CORPUS_ANALYSIS_RESULTS.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n[multi_corpus] Saved → {out_path}")
    return output


if __name__ == "__main__":
    main()
