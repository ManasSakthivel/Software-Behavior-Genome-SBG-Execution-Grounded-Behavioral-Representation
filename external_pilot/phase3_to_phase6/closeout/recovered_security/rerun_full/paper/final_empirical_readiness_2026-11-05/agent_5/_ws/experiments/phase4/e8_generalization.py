"""
experiments/phase4/e8_generalization.py
=========================================
E8: Unseen-Program Generalization.

Evaluates whether the SBG and baseline approaches generalize across programs
not seen during threshold selection. The test split contains programs from
different base_ids than those in dev/train.

Measures:
- Per-program AUROC (variance = generalization gap)
- Best/worst programs for each method
- Distribution of per-program AUROC values

High variance in per-program AUROC indicates poor generalization.

Hypothesis addressed: H1 (sub-hypothesis: generalization across unseen programs)
"""
import json
import pathlib
import random
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from experiments.phase4.utils import ensure_token_initialized

from baselines.common import load_pairs, load_source, compute_auroc, pairs_to_labels
from baselines.b02_ast import score_fn as ast_fn
from baselines.b01_token import score_fn as token_fn
from baselines.b07_static_sbg import score_fn as static_sbg_fn

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "phase4" / "E8"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
N_BOOTSTRAP = 1000


def std_dev(values):
    if len(values) < 2:
        return 0.0
    m = sum(values) / len(values)
    return (sum((x - m) ** 2 for x in values) / len(values)) ** 0.5


def bootstrap_ci(values, n_resamples=N_BOOTSTRAP, seed=SEED):
    if len(values) < 2:
        m = values[0] if values else 0.0
        return m, m, m
    rng = random.Random(seed)
    means = []
    n = len(values)
    for _ in range(n_resamples):
        sample = [values[rng.randint(0, n - 1)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    return sum(values) / n, means[int(0.025 * n_resamples)], means[int(0.975 * n_resamples)]


def run_e8():
    print("=" * 60)
    print("E8: Unseen-Program Generalization")
    print("=" * 60)

    ensure_token_initialized()
    test_pairs = load_pairs("test")
    dev_pairs = load_pairs("dev")
    train_pairs = load_pairs("train")

    # Get base_ids in train/dev to confirm test programs are unseen
    train_base_ids = set(p["base_id"] for p in train_pairs)
    dev_base_ids = set(p["base_id"] for p in dev_pairs)
    test_base_ids = set(p["base_id"] for p in test_pairs)
    seen_base_ids = train_base_ids | dev_base_ids
    unseen_test_ids = test_base_ids - seen_base_ids

    print(f"  Train programs: {len(train_base_ids)}")
    print(f"  Dev programs: {len(dev_base_ids)}")
    print(f"  Test programs: {len(test_base_ids)}")
    print(f"  Test programs NOT in train/dev: {len(unseen_test_ids)} / {len(test_base_ids)}")

    methods = {
        "AST": ast_fn,
        "Token": token_fn,
        "Static_SBG": static_sbg_fn,
    }

    # Group test pairs by base_id
    pairs_by_program = {}
    for p in test_pairs:
        bid = p["base_id"]
        if bid not in pairs_by_program:
            pairs_by_program[bid] = []
        pairs_by_program[bid].append(p)

    # Score all test pairs
    per_pair_scores = {m: [] for m in methods}
    all_labels = []

    print(f"\n  Scoring {len(test_pairs)} test pairs...")
    for i, p in enumerate(test_pairs):
        if (i + 1) % 100 == 0:
            print(f"    {i+1}/{len(test_pairs)}...")
        src_base = load_source(p["base_path"])
        src_var = load_source(p["variant_path"])
        label = 0 if p["semantic_relation"] == "EQUIVALENT" else 1
        all_labels.append(label)
        for m_name, fn in methods.items():
            try:
                s = float(fn(src_base, src_var))
            except Exception:
                s = 0.5
            per_pair_scores[m_name].append(s)

    # Per-program AUROC
    per_program_results = {}
    for bid, prog_pairs in pairs_by_program.items():
        # Find indices in test_pairs for this program
        indices = [i for i, p in enumerate(test_pairs) if p["base_id"] == bid]
        prog_labels = [all_labels[i] for i in indices]

        # Need both classes for AUROC
        has_both = 0 in prog_labels and 1 in prog_labels

        per_program_results[bid] = {
            "n_pairs": len(prog_pairs),
            "n_equiv": prog_labels.count(0),
            "n_changed": prog_labels.count(1),
            "unseen": bid in unseen_test_ids,
        }

        for m_name in methods:
            prog_sims = [per_pair_scores[m_name][i] for i in indices]
            if has_both:
                auroc = compute_auroc(prog_sims, prog_labels)
                per_program_results[bid][f"{m_name}_auroc"] = round(auroc, 4)
            else:
                per_program_results[bid][f"{m_name}_auroc"] = None

    # Generalization stats per method
    generalization_stats = {}
    for m_name in methods:
        valid_aurocs = [
            v[f"{m_name}_auroc"]
            for v in per_program_results.values()
            if v[f"{m_name}_auroc"] is not None
        ]
        if not valid_aurocs:
            continue
        mean_auroc = sum(valid_aurocs) / len(valid_aurocs)
        std_auroc = std_dev(valid_aurocs)
        m, lo, hi = bootstrap_ci(valid_aurocs)
        best_prog = max(per_program_results.items(),
                        key=lambda x: x[1].get(f"{m_name}_auroc") or 0.0)
        worst_prog = min(per_program_results.items(),
                         key=lambda x: x[1].get(f"{m_name}_auroc") or 1.0
                         if x[1].get(f"{m_name}_auroc") is not None else 1.0)
        generalization_stats[m_name] = {
            "n_programs_evaluated": len(valid_aurocs),
            "mean_per_program_auroc": round(mean_auroc, 4),
            "std_per_program_auroc": round(std_auroc, 4),
            "ci_lo": round(lo, 4),
            "ci_hi": round(hi, 4),
            "min_auroc": round(min(valid_aurocs), 4),
            "max_auroc": round(max(valid_aurocs), 4),
            "generalization_gap": round(std_auroc, 4),
            "best_program": best_prog[0],
            "best_program_auroc": best_prog[1].get(f"{m_name}_auroc"),
            "worst_program": worst_prog[0],
            "worst_program_auroc": worst_prog[1].get(f"{m_name}_auroc"),
        }

    result = {
        "experiment": "E8",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hypothesis_addressed": ["H1_generalization"],
        "n_test_pairs": len(test_pairs),
        "n_test_programs": len(pairs_by_program),
        "n_unseen_programs": len(unseen_test_ids),
        "unseen_program_fraction": round(len(unseen_test_ids) / max(1, len(test_base_ids)), 4),
        "per_program_results": per_program_results,
        "generalization_stats": generalization_stats,
        "finding": (
            "High std of per-program AUROC = poor generalization across programs. "
            "Low std = consistent (even if uniformly poor) performance. "
            "See generalization_stats per method."
        ),
        "seed": SEED,
    }

    out_path = ARTIFACT_DIR / "results.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n=== E8 Generalization Stats ===")
    for m_name, stats in generalization_stats.items():
        print(f"  {m_name}: mean_AUROC={stats['mean_per_program_auroc']:.4f}  "
              f"std={stats['std_per_program_auroc']:.4f}  "
              f"[{stats['min_auroc']:.3f}–{stats['max_auroc']:.3f}]  "
              f"gap={stats['generalization_gap']:.4f}")
    print(f"\nResults saved to: {out_path}")
    return result


if __name__ == "__main__":
    run_e8()
