"""
experiments/phase4/e3_invariance.py
=====================================
E3: Refactoring Invariance — Stability Analysis.

Core scientific question for H3:
Even if SBG CANNOT discriminate SP from SC (AUROC near random),
is SBG MORE STABLE (lower variance) under SP transforms than under SC mutations?

Stability is a distinct scientific property from discrimination:
- A representation is STABLE if similar programs get similar scores
- Stability under SP transforms = H3 claim

Test: Are SP similarity scores tighter/less variable than SC similarity scores?

Statistical approach:
1. Compute similarity scores for all EQUIV (SP) and CHANGED (SC) test pairs
2. Compute variance of each group
3. Permutation test (1000 permutations, seed=42) for variance difference
4. Bootstrap 95% CIs for mean and std of each group
5. Effect size: Glass's delta = (mean_CH - mean_SP) / std_SP
   (SP is the "control" since H3 claims it's more stable)
6. Levene-like statistic: W = variance ratio (larger/smaller)

H3 is SUPPORTED if:
- std(SP scores) < std(SC scores) — SP produces more consistent results
- This would mean SBG is at least stable under refactoring even if it can't discriminate

Hypothesis addressed: H3 (primary)
"""
import json
import pathlib
import random
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from experiments.phase4.utils import ensure_token_initialized

from baselines.common import load_pairs, load_source, compute_auroc
from baselines.b07_static_sbg import score_fn as sbg_static_score_fn
from baselines.b02_ast import score_fn as ast_score_fn
from baselines.b01_token import score_fn as token_score_fn

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "phase4" / "E3"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
N_BOOTSTRAP = 1000
N_PERMUTATIONS = 1000


def variance(values):
    if len(values) < 2:
        return 0.0
    m = sum(values) / len(values)
    return sum((x - m) ** 2 for x in values) / len(values)


def std_dev(values):
    return variance(values) ** 0.5


def bootstrap_stats(values, n_resamples=N_BOOTSTRAP, seed=SEED):
    """Bootstrap CI for mean and std."""
    rng = random.Random(seed)
    n = len(values)
    if n < 2:
        return {"mean": values[0] if values else 0.0, "std": 0.0,
                "ci_mean_lo": values[0] if values else 0.0,
                "ci_mean_hi": values[0] if values else 0.0,
                "ci_std_lo": 0.0, "ci_std_hi": 0.0}
    means, stds = [], []
    for _ in range(n_resamples):
        sample = [values[rng.randint(0, n - 1)] for _ in range(n)]
        m = sum(sample) / n
        s = std_dev(sample)
        means.append(m)
        stds.append(s)
    means.sort()
    stds.sort()
    return {
        "mean": round(sum(values) / n, 5),
        "std": round(std_dev(values), 5),
        "ci_mean_lo": round(means[int(0.025 * n_resamples)], 5),
        "ci_mean_hi": round(means[int(0.975 * n_resamples)], 5),
        "ci_std_lo": round(stds[int(0.025 * n_resamples)], 5),
        "ci_std_hi": round(stds[int(0.975 * n_resamples)], 5),
        "n": n,
    }


def permutation_test_variance_diff(group_a, group_b, n_perm=N_PERMUTATIONS, seed=SEED):
    """
    Permutation test: is var(B) - var(A) significantly different from 0?
    H0: the two groups have the same variance.
    H1: var(SC) > var(SP) [one-sided, testing H3 claim that SP is more stable]
    Returns: observed_stat, p_value_one_sided
    """
    rng = random.Random(seed)
    n_a, n_b = len(group_a), len(group_b)
    combined = group_a + group_b
    obs_diff = variance(group_b) - variance(group_a)  # var(SC) - var(SP)

    count_extreme = 0
    for _ in range(n_perm):
        rng.shuffle(combined)
        perm_a = combined[:n_a]
        perm_b = combined[n_a:]
        perm_diff = variance(perm_b) - variance(perm_a)
        if perm_diff >= obs_diff:
            count_extreme += 1

    p_one_sided = count_extreme / n_perm
    return obs_diff, p_one_sided


def glasses_delta(mean_b, mean_a, std_a):
    """Glass's delta: effect size using control group (A=SP) std."""
    if std_a == 0:
        return float("inf") if mean_b != mean_a else 0.0
    return (mean_b - mean_a) / std_a


def run_e3():
    print("=" * 60)
    print("E3: Refactoring Invariance — Stability Analysis")
    print("=" * 60)

    ensure_token_initialized()
    # Try to load cached scores from E1 first to avoid recomputation
    e1_cache_path = REPO_ROOT / "artifacts" / "phase4" / "E1" / "scores_cache.json"
    cached = None
    if e1_cache_path.exists():
        try:
            with open(e1_cache_path) as f:
                cached = json.load(f)
            print("  Loaded scores from E1 cache.")
        except Exception:
            cached = None

    test_pairs = load_pairs("test")
    equiv_pairs = [p for p in test_pairs if p["semantic_relation"] == "EQUIVALENT"]
    changed_pairs = [p for p in test_pairs if p["semantic_relation"] == "CHANGED"]

    methods = {
        "SBG_static": sbg_static_score_fn,
        "AST": ast_score_fn,
        "Token": token_score_fn,
    }

    # Collect scores per method per pair
    if cached:
        equiv_scores = {m: cached["equiv"][m] for m in methods if m in cached.get("equiv", {})}
        changed_scores = {m: cached["changed"][m] for m in methods if m in cached.get("changed", {})}
        # Check all methods have data
        for m in methods:
            if m not in equiv_scores:
                equiv_scores[m] = None
            if m not in changed_scores:
                changed_scores[m] = None
        # If any method missing, recompute
        needs_recompute = any(equiv_scores[m] is None for m in methods)
    else:
        needs_recompute = True

    if needs_recompute:
        print("  Computing scores from scratch...")
        equiv_scores = {m: [] for m in methods}
        changed_scores = {m: [] for m in methods}

        for i, p in enumerate(equiv_pairs):
            if (i + 1) % 50 == 0:
                print(f"    equiv {i+1}/{len(equiv_pairs)}...")
            src_base = load_source(p["base_path"])
            src_var = load_source(p["variant_path"])
            for m_name, fn in methods.items():
                try:
                    s = float(fn(src_base, src_var))
                except Exception:
                    s = 0.5
                equiv_scores[m_name].append(s)

        for i, p in enumerate(changed_pairs):
            if (i + 1) % 30 == 0:
                print(f"    changed {i+1}/{len(changed_pairs)}...")
            src_base = load_source(p["base_path"])
            src_var = load_source(p["variant_path"])
            for m_name, fn in methods.items():
                try:
                    s = float(fn(src_base, src_var))
                except Exception:
                    s = 0.5
                changed_scores[m_name].append(s)

    # Per-transform-type stability analysis
    by_transform_scores = {}
    by_mutation_scores = {}
    for p in equiv_pairs:
        tt = p["transformation_type"]
        if tt not in by_transform_scores:
            by_transform_scores[tt] = {m: [] for m in methods}

    for p in changed_pairs:
        mt = p["transformation_type"]
        if mt not in by_mutation_scores:
            by_mutation_scores[mt] = {m: [] for m in methods}

    if needs_recompute:
        for i, p in enumerate(equiv_pairs):
            tt = p["transformation_type"]
            src_base = load_source(p["base_path"])
            src_var = load_source(p["variant_path"])
            for m_name, fn in methods.items():
                try:
                    s = float(fn(src_base, src_var))
                except Exception:
                    s = 0.5
                by_transform_scores[tt][m_name].append(s)
        for i, p in enumerate(changed_pairs):
            mt = p["transformation_type"]
            src_base = load_source(p["base_path"])
            src_var = load_source(p["variant_path"])
            for m_name, fn in methods.items():
                try:
                    s = float(fn(src_base, src_var))
                except Exception:
                    s = 0.5
                by_mutation_scores[mt][m_name].append(s)
    else:
        # Rebuild by_transform and by_mutation from cached scores indexed by pair order
        eq_idx = {i: equiv_pairs[i]["transformation_type"] for i in range(len(equiv_pairs))}
        ch_idx = {i: changed_pairs[i]["transformation_type"] for i in range(len(changed_pairs))}
        for m_name in methods:
            for i, tt in eq_idx.items():
                if i < len(equiv_scores[m_name]):
                    by_transform_scores[tt][m_name].append(equiv_scores[m_name][i])
            for i, mt in ch_idx.items():
                if i < len(changed_scores[m_name]):
                    by_mutation_scores[mt][m_name].append(changed_scores[m_name][i])

    # Main stability analysis per method
    stability_results = {}
    h3_verdicts = {}

    for m_name in methods:
        sp_scores = equiv_scores[m_name]
        sc_scores = changed_scores[m_name]

        if not sp_scores or not sc_scores:
            continue

        sp_stats = bootstrap_stats(sp_scores)
        sc_stats = bootstrap_stats(sc_scores)

        var_diff, p_val = permutation_test_variance_diff(sp_scores, sc_scores, seed=SEED)
        g_delta = glasses_delta(sc_stats["mean"], sp_stats["mean"], sp_stats["std"])

        # Per-transform variance
        per_transform_std = {}
        for tt, scores_by_method in by_transform_scores.items():
            s = scores_by_method.get(m_name, [])
            per_transform_std[tt] = round(std_dev(s), 5) if s else None

        per_mutation_std = {}
        for mt, scores_by_method in by_mutation_scores.items():
            s = scores_by_method.get(m_name, [])
            per_mutation_std[mt] = round(std_dev(s), 5) if s else None

        # H3 verdict
        h3_supported = (
            sp_stats["std"] < sc_stats["std"] and
            p_val < 0.05  # one-sided permutation p-value
        )

        stability_results[m_name] = {
            "sp_stats": sp_stats,
            "sc_stats": sc_stats,
            "var_diff_sc_minus_sp": round(var_diff, 6),
            "permutation_p_one_sided": round(p_val, 4),
            "glasses_delta": round(g_delta, 4) if not (g_delta == float("inf")) else "infinity",
            "per_transform_std": per_transform_std,
            "per_mutation_std": per_mutation_std,
        }

        h3_supported_str = "SUPPORTED" if h3_supported else "NOT_SUPPORTED"
        h3_verdicts[m_name] = {
            "status": h3_supported_str,
            "sp_std": round(sp_stats["std"], 5),
            "sc_std": round(sc_stats["std"], 5),
            "p_val": round(p_val, 4),
            "interpretation": (
                f"SP std={sp_stats['std']:.4f} {'<' if h3_supported else '>='} SC std={sc_stats['std']:.4f}. "
                f"p={p_val:.4f} ({'significant' if p_val < 0.05 else 'not significant'} at α=0.05). "
                f"H3 {'SUPPORTED' if h3_supported else 'NOT SUPPORTED'}: "
                f"SBG is {'MORE' if h3_supported else 'NOT MORE'} stable under refactoring."
            ),
        }

    result = {
        "experiment": "E3",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hypothesis_addressed": ["H3"],
        "n_equiv_pairs": len(equiv_pairs),
        "n_changed_pairs": len(changed_pairs),
        "n_sp_types": len(by_transform_scores),
        "n_sc_types": len(by_mutation_scores),
        "stability_results": stability_results,
        "h3_verdicts": h3_verdicts,
        "statistical_method": "permutation_test_1000_resamples_seed42 + bootstrap_CI_1000_resamples",
        "finding": (
            "Stability analysis tests H3: is SBG more stable (lower variance) under "
            "semantics-preserving transforms than under mutations? See h3_verdicts per method. "
            "Note: even if H3 is supported, the practical utility is limited because all AUROCs "
            "are near-random — variance stability does NOT imply discrimination power."
        ),
        "scientific_verdict": "See h3_verdicts per method — H3 requires var(SP) < var(SC) AND p<0.05",
        "seed": SEED,
    }

    out_path = ARTIFACT_DIR / "results.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n=== E3 Results ===")
    for m_name in methods:
        if m_name in h3_verdicts:
            v = h3_verdicts[m_name]
            print(f"  {m_name}: H3={v['status']}  SP_std={v['sp_std']:.4f}  SC_std={v['sc_std']:.4f}  p={v['p_val']:.4f}")
            print(f"    {v['interpretation']}")

    print(f"\nResults saved to: {out_path}")
    return result


if __name__ == "__main__":
    run_e3()
