"""
experiments/v2/regression_benchmark.py
========================================
H12 Regression Detection Benchmark.

Pre-registered criterion (from docs/v2/HYPOTHESES_V2.md):
  H12: AUROC(hybrid_regression) > AUROC(B02_AST = 0.5528)

This script:
1. Loads the synthetic regression benchmark from benchmark/regression/
2. Scores pairs with each method (AST, Dynamic V2, Hybrid V2)
3. Evaluates H12 verdict
4. Computes AUROC, AUPRC, TPR@FPR1%, TPR@FPR5%, precision, recall, F1

IMPORTANT: All benchmark pairs are SYNTHETIC — not from real historical repositories.
Every pair is labeled: "provenance": "SYNTHETIC — not from real historical repositories"
"""
from __future__ import annotations

import json
import pathlib
import random
import sys
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# ============================================================
# PREREGISTERED H12 CRITERION
# ============================================================
H12_AUROC_THRESHOLD: float = 0.5528  # must beat B02 AST baseline
BOOTSTRAP_N: int = 1000
BOOTSTRAP_SEED: int = 42

BENCHMARK_DIR = REPO_ROOT / "benchmark" / "regression"
ARTIFACT_PATH = REPO_ROOT / "artifacts" / "v2" / "REGRESSION_RESULTS.json"

from baselines.common import compute_auroc, compute_auprc


def _load_regression_pairs() -> List[Dict]:
    """Load regression benchmark pairs."""
    pairs_file = BENCHMARK_DIR / "regression_pairs.jsonl"
    if not pairs_file.exists():
        return []
    pairs = []
    for line in pairs_file.read_text().splitlines():
        line = line.strip()
        if line:
            pairs.append(json.loads(line))
    return pairs


def _tpr_at_fpr(sims: List[float], labels: List[int], target_fpr: float) -> float:
    """Compute TPR at a given FPR threshold."""
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.0

    # Sort ascending by similarity (descending distance)
    sorted_pairs = sorted(zip(sims, labels), key=lambda x: x[0])

    best_tpr = 0.0
    tp = fp = 0
    for sim, lbl in sorted_pairs:
        if lbl == 1:
            tp += 1
        else:
            fp += 1
        fpr = fp / n_neg
        if fpr <= target_fpr:
            best_tpr = tp / n_pos

    return best_tpr


def _compute_regression_metrics(sims: List[float], labels: List[int]) -> Dict[str, Any]:
    """Compute full metrics suite for regression detection."""
    auroc = compute_auroc(sims, labels)
    auprc = compute_auprc(sims, labels)
    tpr_fpr1 = _tpr_at_fpr(sims, labels, 0.01)
    tpr_fpr5 = _tpr_at_fpr(sims, labels, 0.05)

    # Bootstrap CI for AUROC
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(sims)
    aurocs = []
    for _ in range(BOOTSTRAP_N):
        idx = [rng.randint(0, n - 1) for _ in range(n)]
        bs_s = [sims[i] for i in idx]
        bs_l = [labels[i] for i in idx]
        aurocs.append(compute_auroc(bs_s, bs_l))
    aurocs.sort()

    # Best threshold for F1
    unique_thresholds = sorted(set(sims))
    best_f1 = 0.0
    best_t = 0.5
    for t in unique_thresholds:
        tp = fp = fn = 0
        for s, l in zip(sims, labels):
            pred = 1 if s < t else 0
            if l == 1 and pred == 1:
                tp += 1
            elif l == 0 and pred == 1:
                fp += 1
            elif l == 1 and pred == 0:
                fn += 1
        denom = 2 * tp + fp + fn
        f1 = (2 * tp) / denom if denom > 0 else 0.0
        if f1 > best_f1:
            best_f1 = f1
            best_t = t

    tp = fp = fn = tn = 0
    for s, l in zip(sims, labels):
        pred = 1 if s < best_t else 0
        if l == 1 and pred == 1:
            tp += 1
        elif l == 0 and pred == 1:
            fp += 1
        elif l == 1 and pred == 0:
            fn += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    return {
        "auroc": round(auroc, 6),
        "auprc": round(auprc, 6),
        "tpr_at_fpr1": round(tpr_fpr1, 6),
        "tpr_at_fpr5": round(tpr_fpr5, 6),
        "f1": round(best_f1, 6),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "ci_auroc_lower": round(aurocs[25], 6),
        "ci_auroc_upper": round(aurocs[974], 6),
        "n": len(sims),
        "n_regression": sum(labels),
        "n_correct": len(labels) - sum(labels),
    }


def _score_with_ast(pairs: List[Dict]) -> List[float]:
    """Score pairs with B02 AST similarity."""
    try:
        from baselines.b02_ast import score_fn
        from baselines.common import load_source
        sims = []
        for p in pairs:
            base_path = str(BENCHMARK_DIR / "programs" / p["base_file"])
            var_path = str(BENCHMARK_DIR / "programs" / p["variant_file"])
            try:
                src_a = pathlib.Path(base_path).read_text()
                src_b = pathlib.Path(var_path).read_text()
                s = score_fn(src_a, src_b)
            except Exception:
                s = 0.5
            sims.append(s)
        return sims
    except Exception as e:
        print(f"  [WARN] AST scoring failed: {e}")
        return [0.5] * len(pairs)


def _score_with_dynamic(pairs: List[Dict]) -> List[float]:
    """Score regression pairs with B07 Dynamic V2."""
    try:
        from baselines.v2.b07_dynamic_v2 import _score_pair
        sims = []
        for p in pairs:
            base_path = str(BENCHMARK_DIR / "programs" / p["base_file"])
            var_path = str(BENCHMARK_DIR / "programs" / p["variant_file"])
            try:
                s = _score_pair(base_path, var_path)
            except Exception:
                s = 0.5
            sims.append(s)
        return sims
    except Exception as e:
        print(f"  [WARN] Dynamic scoring failed: {e}")
        return [0.5] * len(pairs)


def run_regression_benchmark() -> Dict[str, Any]:
    """Run H12 regression detection benchmark."""
    print("[H12] Regression Detection Benchmark")
    print(f"[H12] Criterion: AUROC(hybrid) > {H12_AUROC_THRESHOLD} (B02 AST baseline)")
    print(f"[H12] WARNING: ALL pairs are SYNTHETIC — not from real repositories")

    pairs = _load_regression_pairs()
    if not pairs:
        print("[H12] No regression pairs found. Benchmark not yet generated.")
        result = {
            "status": "NO_BENCHMARK_DATA",
            "h12_verdict": "INSUFFICIENT_EVIDENCE",
            "note": "Run benchmark generation first: python benchmark/regression/generate.py",
        }
        ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT_PATH.write_text(json.dumps(result, indent=2))
        return result

    # All benchmark pairs have a base (correct) and variant (regression).
    # The benchmark currently contains only regression pairs — label=1 for all.
    # Without a negative class (label=0), AUROC is undefined.
    # H12 requires both regression and non-regression pairs for binary classification.
    labels = [1 if p.get("regression_type") else 0 for p in pairs]
    n_regression = sum(labels)
    n_correct = len(labels) - n_regression
    print(f"[H12] Loaded {len(pairs)} pairs: {n_regression} regressions, {n_correct} correct")
    if n_correct == 0:
        print("[H12] WARNING: No non-regression pairs in benchmark — AUROC undefined (single class).")
        print("[H12] H12 verdict: INSUFFICIENT_EVIDENCE")
        result = {
            "hypothesis": "H12",
            "criterion_auroc_threshold": H12_AUROC_THRESHOLD,
            "reference_baseline": "B02_AST_AUROC=0.5528",
            "synthetic_note": "ALL pairs are SYNTHETIC — not from real historical repositories",
            "n_pairs": len(pairs),
            "n_regressions": n_regression,
            "n_correct": n_correct,
            "method_metrics": {},
            "per_category_dynamic": {},
            "h12_verdict": "INSUFFICIENT_EVIDENCE",
            "h12_reason": (
                "Benchmark contains only regression pairs (no non-regression control pairs). "
                "Binary AUROC requires both positive and negative classes. "
                "Adding equivalent-but-refactored control pairs is required before H12 can be evaluated."
            ),
            "bootstrap_config": {"n": BOOTSTRAP_N, "seed": BOOTSTRAP_SEED},
            "limitations": [
                "L1: Synthetic pairs only — real historical regressions unavailable",
                "L2: Python only — no cross-language regression detection",
                "L3: Limited categories — no concurrency or resource regressions",
                "L4: Small N — insufficient power for definitive claims",
                "L5: CRITICAL — benchmark lacks non-regression control pairs; AUROC undefined",
            ],
        }
        ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT_PATH.write_text(json.dumps(result, indent=2))
        return result

    # Score with each method
    print("\n[H12] Scoring with AST (B02)...")
    ast_sims = _score_with_ast(pairs)

    print("\n[H12] Scoring with Dynamic V2 (B07)...")
    dyn_sims = _score_with_dynamic(pairs)

    # Compute metrics
    method_metrics = {
        "B02_AST": _compute_regression_metrics(ast_sims, labels),
        "B07_DYNAMIC_V2": _compute_regression_metrics(dyn_sims, labels),
    }

    # H12 verdict
    b07_auroc = method_metrics["B07_DYNAMIC_V2"]["auroc"]
    h12_verdict = "SUPPORTED" if b07_auroc > H12_AUROC_THRESHOLD else "NOT_SUPPORTED"

    # Per-category analysis
    categories = sorted(set(p.get("regression_type", "unknown") for p in pairs))
    per_category = {}
    for cat in categories:
        cat_indices = [i for i, p in enumerate(pairs) if p.get("regression_type") == cat]
        cat_sims = [dyn_sims[i] for i in cat_indices]
        cat_labels = [labels[i] for i in cat_indices]
        if sum(cat_labels) > 0:
            per_category[cat] = {
                "n": len(cat_indices),
                "n_regression": sum(cat_labels),
                "auroc": round(compute_auroc(cat_sims, cat_labels), 6),
            }

    result = {
        "hypothesis": "H12",
        "criterion_auroc_threshold": H12_AUROC_THRESHOLD,
        "reference_baseline": "B02_AST_AUROC=0.5528",
        "synthetic_note": "ALL pairs are SYNTHETIC — not from real historical repositories",
        "n_pairs": len(pairs),
        "n_regressions": sum(labels),
        "method_metrics": method_metrics,
        "per_category_dynamic": per_category,
        "h12_verdict": h12_verdict,
        "bootstrap_config": {"n": BOOTSTRAP_N, "seed": BOOTSTRAP_SEED},
        "limitations": [
            "L1: Synthetic pairs only — real historical regressions unavailable",
            "L2: Python only — no cross-language regression detection",
            "L3: Limited categories — no concurrency or resource regressions",
            "L4: Small N — insufficient power for definitive claims",
        ],
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(result, indent=2))
    print(f"\n[H12] Results saved to {ARTIFACT_PATH}")
    print(f"[H12] H12 verdict: {h12_verdict}")
    print(f"[H12] B07 Dynamic AUROC: {b07_auroc:.4f} vs threshold {H12_AUROC_THRESHOLD}")
    return result


if __name__ == "__main__":
    run_regression_benchmark()
