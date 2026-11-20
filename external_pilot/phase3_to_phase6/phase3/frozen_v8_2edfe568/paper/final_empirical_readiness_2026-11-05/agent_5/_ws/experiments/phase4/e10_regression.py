"""
experiments/phase4/e10_regression.py
=======================================
E10: Software Regression Detection.

Frames the SBG benchmark as a regression detection problem:
- EQUIVALENT pairs = new version that preserved behavior (non-regression)
- CHANGED pairs = new version that changed behavior (potential regression)

Evaluates which mutation types are easiest/hardest to flag as regressions,
using the Phase 3 baseline results and re-scored test pairs.

Also analyzes: at a fixed low false-positive rate (FPR ≤ 5%), what is
the true positive rate for regression detection? This is the practical
operating point for a real regression detector.

Hypothesis addressed: H5 (SBG detects behavioral regressions)
"""
import json
import pathlib
import random
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from experiments.phase4.utils import ensure_token_initialized

from baselines.common import load_pairs, load_source, compute_auroc, compute_auprc, pairs_to_labels
from baselines.b02_ast import score_fn as ast_fn
from baselines.b01_token import score_fn as token_fn
from baselines.b07_static_sbg import score_fn as static_sbg_fn

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "phase4" / "E10"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
N_BOOTSTRAP = 1000
PHASE3_DIR = REPO_ROOT / "artifacts" / "phase3"


def tpr_at_fpr(similarities: list, labels: list, target_fpr: float = 0.05) -> dict:
    """
    Compute TPR at a given FPR threshold for regression detection.
    CHANGED = 1 = positive class (regressions).
    """
    n_pos = sum(1 for l in labels if l == 1)
    n_neg = sum(1 for l in labels if l == 0)
    if n_pos == 0 or n_neg == 0:
        return {"tpr": None, "fpr": None, "threshold": None}

    # Sort ascending by similarity (ascending sim = higher chance of CHANGED)
    sorted_pairs = sorted(zip(similarities, labels), key=lambda x: x[0])

    best = {"tpr": 0.0, "fpr": 0.0, "threshold": 1.0}
    tp = fp = 0
    for sim, lbl in sorted_pairs:
        if lbl == 1:
            tp += 1
        else:
            fp += 1
        fpr = fp / n_neg
        tpr = tp / n_pos
        if fpr <= target_fpr:
            best = {"tpr": round(tpr, 4), "fpr": round(fpr, 4), "threshold": round(sim, 4)}
    return best


def bootstrap_auroc(sims: list, labels: list, n_resamples=N_BOOTSTRAP, seed=SEED) -> tuple:
    rng = random.Random(seed)
    n = len(sims)
    aurocs = []
    for _ in range(n_resamples):
        idx = [rng.randint(0, n - 1) for _ in range(n)]
        bs = [sims[i] for i in idx]
        bl = [labels[i] for i in idx]
        aurocs.append(compute_auroc(bs, bl))
    aurocs.sort()
    return (
        compute_auroc(sims, labels),
        aurocs[int(0.025 * n_resamples)],
        aurocs[int(0.975 * n_resamples)],
    )


def run_e10():
    print("=" * 60)
    print("E10: Software Regression Detection")
    print("=" * 60)

    ensure_token_initialized()
    test_pairs = load_pairs("test")
    labels = pairs_to_labels(test_pairs)  # 0=EQUIV, 1=CHANGED

    print(f"  Test pairs: {len(test_pairs)} ({labels.count(0)} equiv, {labels.count(1)} changed)")

    methods = {
        "AST": ast_fn,
        "Token": token_fn,
        "Static_SBG": static_sbg_fn,
    }

    # Load Phase 3 dynamic result for comparison
    b06_result = {}
    b06_path = PHASE3_DIR / "B06" / "results_test.json"
    if b06_path.exists():
        with open(b06_path) as f:
            b06_result = json.load(f)

    # Score all test pairs
    all_sims = {m: [] for m in methods}
    by_mutation_type = {}  # mutation_type -> {method: [sims], labels: [labels]}

    for i, p in enumerate(test_pairs):
        if (i + 1) % 100 == 0:
            print(f"    {i+1}/{len(test_pairs)}...")
        src_base = load_source(p["base_path"])
        src_var = load_source(p["variant_path"])
        tt = p["transformation_type"]

        if p["semantic_relation"] == "CHANGED":
            if tt not in by_mutation_type:
                by_mutation_type[tt] = {m: [] for m in methods}
                by_mutation_type[tt]["_labels"] = []

        for m_name, fn in methods.items():
            try:
                s = float(fn(src_base, src_var))
            except Exception:
                s = 0.5
            all_sims[m_name].append(s)
            if p["semantic_relation"] == "CHANGED" and tt in by_mutation_type:
                by_mutation_type[tt][m_name].append(s)

        if p["semantic_relation"] == "CHANGED" and tt in by_mutation_type:
            by_mutation_type[tt]["_labels"].append(1)

    # Overall regression detection metrics
    overall_metrics = {}
    for m_name in methods:
        sims = all_sims[m_name]
        auroc, lo, hi = bootstrap_auroc(sims, labels, seed=SEED)
        auprc = compute_auprc(sims, labels)
        tpr5 = tpr_at_fpr(sims, labels, target_fpr=0.05)
        tpr10 = tpr_at_fpr(sims, labels, target_fpr=0.10)
        overall_metrics[m_name] = {
            "auroc": round(auroc, 4),
            "auroc_ci": [round(lo, 4), round(hi, 4)],
            "auprc": round(auprc, 4),
            "tpr_at_fpr5pct": tpr5,
            "tpr_at_fpr10pct": tpr10,
            "practical_regression_detection": (
                f"At FPR≤5%: TPR={tpr5['tpr']:.2%} "
                f"(catches {tpr5['tpr']:.0%} of regressions while mis-flagging "
                f"≤5% of non-regressions)"
                if tpr5["tpr"] is not None else "N/A"
            ),
        }

    # Per-mutation-type detectability
    mutation_detectability = {}
    for mt, data in by_mutation_type.items():
        n = len(data["_labels"])
        if n < 3:
            continue
        mutation_detectability[mt] = {"n": n}
        for m_name in methods:
            mt_sims = data[m_name]
            # For CHANGED-only: compare to overall equiv similarity (sim should be LOW)
            # Since all labels=1, AUROC is undefined — use mean similarity instead
            if mt_sims:
                mean_sim = sum(mt_sims) / len(mt_sims)
                mutation_detectability[mt][m_name] = {
                    "mean_sim": round(mean_sim, 4),
                    "near_identical_frac": round(
                        sum(1 for s in mt_sims if s > 0.95) / len(mt_sims), 4
                    ),
                    "detectability": (
                        "HARD" if mean_sim > 0.95
                        else ("MEDIUM" if mean_sim > 0.80 else "EASY")
                    ),
                }

    # Sort mutation types by detectability (hardest first, by AST mean_sim)
    mutation_ranking = sorted(
        [(mt, mutation_detectability[mt].get("AST", {}).get("mean_sim", 0.5))
         for mt in mutation_detectability],
        key=lambda x: -x[1]
    )

    # H5 verdict
    best_auroc = max(
        (overall_metrics[m]["auroc"] for m in methods), default=0.0
    )
    h5_supported = best_auroc > 0.65  # meaningful regression detection threshold
    h5_verdict = {
        "status": "SUPPORTED" if h5_supported else "NOT_SUPPORTED",
        "best_method_auroc": round(best_auroc, 4),
        "threshold_used": 0.65,
        "interpretation": (
            f"Best regression detection AUROC={best_auroc:.4f}. "
            f"H5 requires AUROC>0.65 for 'can detect regressions'. "
            f"H5 is {'SUPPORTED' if h5_supported else 'NOT SUPPORTED'}."
        ),
    }

    # Phase 3 dynamic baseline comparison
    b06_auroc = b06_result.get("metrics", {}).get("auroc")
    if b06_auroc:
        print(f"  Phase 3 Dynamic (B06) AUROC = {b06_auroc:.4f}")

    result = {
        "experiment": "E10",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hypothesis_addressed": ["H5"],
        "n_test_pairs": len(test_pairs),
        "n_equiv": labels.count(0),
        "n_changed": labels.count(1),
        "overall_regression_detection": overall_metrics,
        "per_mutation_detectability": mutation_detectability,
        "mutation_ranking_hardest_first": [
            {"mutation_type": mt, "ast_mean_sim": round(s, 4)} for mt, s in mutation_ranking
        ],
        "phase3_dynamic_auroc": b06_auroc,
        "h5_verdict": h5_verdict,
        "finding": h5_verdict["interpretation"],
        "seed": SEED,
    }

    out_path = ARTIFACT_DIR / "results.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n=== E10 Regression Detection ===")
    for m_name, m in overall_metrics.items():
        print(f"  {m_name}: AUROC={m['auroc']:.4f} [{m['auroc_ci'][0]:.3f}–{m['auroc_ci'][1]:.3f}]  "
              f"TPR@FPR5%={m['tpr_at_fpr5pct']['tpr']}")
    print(f"\n  H5: {h5_verdict['status']}")
    print(f"  Hardest mutations (by AST):")
    for entry in mutation_ranking[:5]:
        mt = entry["mutation_type"] if isinstance(entry, dict) else entry[0]
        sim = entry.get("ast_mean_sim", entry[1]) if isinstance(entry, dict) else entry[1]
        print(f"    {mt}: mean_sim={sim:.4f}")
    print(f"\nResults saved to: {out_path}")
    return result


if __name__ == "__main__":
    run_e10()
