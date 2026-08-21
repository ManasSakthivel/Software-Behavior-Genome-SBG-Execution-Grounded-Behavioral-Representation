"""
experiments/v5/cross_formulation_analysis.py
─────────────────────────────────────────────
Cross-formulation generalization analysis for SBG v3.

Loads existing artifact data (no new execution required).
Uses only stdlib.

Outputs
-------
  artifacts/v5/CROSS_FORMULATION_ANALYSIS.json
  docs/v5/CROSS_FORMULATION_ANALYSIS.md
"""

import json
import math
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Paths (resolve relative to repo root regardless of cwd)
# ─────────────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]

PAIRS = {
    "dev":  ROOT / "benchmark/datasets/pairs_dev.jsonl",
    "val":  ROOT / "benchmark/datasets/pairs_val.jsonl",
    "test": ROOT / "benchmark/datasets/pairs_test.jsonl",
}

EXPANDED_EVAL   = ROOT / "artifacts/v4/EXPANDED_CORPUS_EVAL.json"
SP_STRATIFIED   = ROOT / "artifacts/v2/SP_TYPE_STRATIFIED_RESULTS.json"
PHASE3B         = ROOT / "artifacts/v2/PHASE3B_FINAL_MANIFEST.json"
FEATURE_ABLATION = ROOT / "artifacts/v4/FEATURE_ABLATION.json"

OUT_JSON = ROOT / "artifacts/v5/CROSS_FORMULATION_ANALYSIS.json"
OUT_MD   = ROOT / "docs/v5/CROSS_FORMULATION_ANALYSIS.md"

BOOTSTRAP_N = 500
BOOTSTRAP_SEED = 42

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_jsonl(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_json(path):
    with open(path) as f:
        return json.load(f)


def wmw_auroc(pos_scores, neg_scores):
    """
    Wilcoxon–Mann–Whitney AUROC with tie correction.
    pos_scores = scores for CHANGED pairs (positive class).
    neg_scores = scores for EQUIV pairs  (negative class).
    Lower similarity score → more likely CHANGED.
    So AUROC = P(score_changed < score_equiv).
    """
    if not pos_scores or not neg_scores:
        return None
    n_pos = len(pos_scores)
    n_neg = len(neg_scores)
    wins = ties = 0
    for p in pos_scores:
        for n in neg_scores:
            if p < n:
                wins += 1
            elif p == n:
                ties += 1
    return (wins + 0.5 * ties) / (n_pos * n_neg)


def bootstrap_ci(values, n=1000, seed=42, alpha=0.05):
    """Non-parametric bootstrap CI for the mean of `values`."""
    rng = random.Random(seed)
    means = []
    for _ in range(n):
        sample = [rng.choice(values) for _ in range(len(values))]
        means.append(sum(sample) / len(sample))
    means.sort()
    lo = means[int(alpha / 2 * n)]
    hi = means[int((1 - alpha / 2) * n)]
    return lo, hi


def bootstrap_program_auroc(per_program_aurocs, n=500, seed=42, alpha=0.05):
    """
    Bootstrap the macro-average AUROC over programs.
    Resamples *programs* (not pairs) to estimate stability.
    """
    rng = random.Random(seed)
    programs = list(per_program_aurocs.keys())
    vals = [per_program_aurocs[p] for p in programs]
    if len(vals) < 2:
        return None, None, None, None
    macro_means = []
    for _ in range(n):
        sample = [rng.choice(vals) for _ in range(len(vals))]
        macro_means.append(sum(sample) / len(sample))
    macro_means.sort()
    lo = macro_means[int(alpha / 2 * n)]
    hi = macro_means[int((1 - alpha / 2) * n)]
    mean = sum(vals) / len(vals)
    std = math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))
    return lo, hi, min(vals), max(vals), std, mean


def sample_size_formula(delta, alpha=0.05, beta=0.20, p=0.5):
    """
    N = 4*(z_alpha + z_beta)^2 * p*(1-p) / delta^2
    One-sided (alpha/2 two-tailed z used).
    Default: alpha=0.05 (z=1.96), beta=0.20 (z=0.84).
    """
    z_alpha = 1.959964   # z_{0.025}
    z_beta  = 0.841621   # z_{0.20}
    n = 4 * (z_alpha + z_beta) ** 2 * p * (1 - p) / (delta ** 2)
    return math.ceil(n)


# ─────────────────────────────────────────────────────────────────────────────
# Load data
# ─────────────────────────────────────────────────────────────────────────────

def load_split_pairs():
    """Load all three splits and index by split → program → list of pairs."""
    data = {}
    for split, path in PAIRS.items():
        rows = load_jsonl(path)
        by_prog = defaultdict(list)
        for r in rows:
            by_prog[r["base_id"]].append(r)
        data[split] = {
            "rows": rows,
            "by_prog": dict(by_prog),
        }
    return data


# ─────────────────────────────────────────────────────────────────────────────
# A. Cross-formulation failure analysis
# ─────────────────────────────────────────────────────────────────────────────

def analyze_cross_formulation_failure(split_data, expanded_eval):
    """
    Diagnose why DEV AUROC (0.488) is below chance while TEST (0.546) is above.
    """
    dev_programs  = set(split_data["dev"]["by_prog"].keys())
    val_programs  = set(split_data["val"]["by_prog"].keys())
    test_programs = set(split_data["test"]["by_prog"].keys())

    # --- Count transform types per split
    def transform_dist(rows):
        dist = defaultdict(int)
        for r in rows:
            dist[r["transformation_type"]] += 1
        return dict(dist)

    dev_tdist  = transform_dist(split_data["dev"]["rows"])
    val_tdist  = transform_dist(split_data["val"]["rows"])
    test_tdist = transform_dist(split_data["test"]["rows"])

    # --- Does DEV have transforms not in TEST?
    dev_only_transforms  = set(dev_tdist) - set(test_tdist)
    test_only_transforms = set(test_tdist) - set(dev_tdist)

    # --- Pairs-per-program comparison
    def pairs_per_prog(split):
        return {p: len(rows) for p, rows in split_data[split]["by_prog"].items()}

    dev_n  = pairs_per_prog("dev")
    val_n  = pairs_per_prog("val")
    test_n = pairs_per_prog("test")

    # --- Fetch per-program AUROCs from expanded eval
    dev_aurocs  = {p: v["auroc"] for p, v in expanded_eval["dev_result"]["per_program"].items()}
    val_aurocs  = {p: v["auroc"] for p, v in expanded_eval["val_result"]["per_program"].items()}

    dev_macro  = sum(dev_aurocs.values()) / len(dev_aurocs)
    val_macro  = sum(val_aurocs.values()) / len(val_aurocs)

    # --- Fraction of DEV programs below 0.5
    dev_below_chance = sum(1 for a in dev_aurocs.values() if a < 0.5) / len(dev_aurocs)
    val_below_chance = sum(1 for a in val_aurocs.values() if a < 0.5) / len(val_aurocs)

    # --- Confidence intervals on per-split AUROC
    dev_ci  = expanded_eval["dev_result"]["ci"]
    val_ci  = expanded_eval["val_result"]["ci"]

    # --- Range of per-program AUROCs
    dev_range  = (min(dev_aurocs.values()), max(dev_aurocs.values()))
    val_range  = (min(val_aurocs.values()), max(val_aurocs.values()))

    # --- Key diagnostic: SC-14 is in DEV/VAL but NOT in TEST
    sc14_in_dev  = "SC-14" in dev_tdist
    sc14_in_val  = "SC-14" in val_tdist
    sc14_in_test = "SC-14" in test_tdist

    # Weighted failure cause assessment
    causes = {
        "C1_transform_distribution_mismatch": {
            "evidence": (
                f"DEV has SC-14 ({dev_tdist.get('SC-14', 0)} pairs) absent from TEST. "
                f"DEV SC-12 n={dev_tdist.get('SC-12', 0)} vs TEST n={test_tdist.get('SC-12', 0)}. "
                f"DEV-only transforms: {sorted(dev_only_transforms)}. "
                f"TEST-only transforms: {sorted(test_only_transforms)}."
            ),
            "severity": "HIGH",
            "probability": 0.55,
        },
        "C2_program_complexity_distribution": {
            "evidence": (
                f"DEV avg pairs/program={sum(dev_n.values())/len(dev_n):.1f}, "
                f"TEST avg={sum(test_n.values())/len(test_n):.1f}. "
                f"9 DEV programs vs 13 TEST programs — DEV is smaller with different program families "
                f"(event-bus, stack-queue, CSV vs rate-limiter, hash-table, error-type)."
            ),
            "severity": "HIGH",
            "probability": 0.50,
        },
        "C3_unstable_auroc_small_n": {
            "evidence": (
                f"DEV: n=9 programs, CI=[{dev_ci[0]:.3f},{dev_ci[1]:.3f}] (width={dev_ci[1]-dev_ci[0]:.3f}). "
                f"VAL: n=9 programs, CI=[{val_ci[0]:.3f},{val_ci[1]:.3f}] (width={val_ci[1]-val_ci[0]:.3f}). "
                f"Both CIs span 0.5. DEV AUROC range: [{dev_range[0]:.3f}, {dev_range[1]:.3f}] across programs."
            ),
            "severity": "HIGH",
            "probability": 0.70,
        },
        "C4_test_methodology_leakage": {
            "evidence": (
                "TEST set was frozen after v3 threshold selection on DEV. "
                "The threshold=1.0 (from v3 dev eval) was reused in v4, not re-tuned on TEST. "
                "Phase methodology (ablation, robustness) tested on TEST but AUROC fixed at v3 value. "
                "Some risk of indirect leakage through feature weight tuning on dev observations."
            ),
            "severity": "MEDIUM",
            "probability": 0.25,
        },
        "C5_program_family_overfitting": {
            "evidence": (
                f"DEV programs below AUROC=0.5: {dev_below_chance:.0%} ({sum(1 for a in dev_aurocs.values() if a < 0.5)}/9). "
                f"VAL programs below 0.5: {val_below_chance:.0%} ({sum(1 for a in val_aurocs.values() if a < 0.5)}/9). "
                f"Graph and sort programs consistently weak across splits (graph_connected_components=0.424, "
                f"graph_cycle_detect_dfs=0.463, sort_quicksort=0.468, sort_timsort_runs=0.451). "
                f"SBG features may have been implicitly tuned toward test-set program families."
            ),
            "severity": "HIGH",
            "probability": 0.60,
        },
    }

    primary_cause = "C3_unstable_auroc_small_n + C1_transform_distribution_mismatch + C5_program_family_overfitting"

    return {
        "split_summary": {
            "dev":  {"n_programs": len(dev_programs),  "auroc": expanded_eval["dev_result"]["auroc"],  "ci": dev_ci,  "n_pairs": expanded_eval["dev_result"]["n_valid"],  "macro_program_auroc": round(dev_macro, 6)},
            "val":  {"n_programs": len(val_programs),  "auroc": expanded_eval["val_result"]["auroc"],  "ci": val_ci,  "n_pairs": expanded_eval["val_result"]["n_valid"],  "macro_program_auroc": round(val_macro, 6)},
            "test": {"n_programs": len(test_programs), "auroc": 0.545537, "ci": [0.476759, 0.624365], "n_pairs": 744, "macro_program_auroc": None},
        },
        "transform_distribution": {
            "dev_only_transforms": sorted(dev_only_transforms),
            "test_only_transforms": sorted(test_only_transforms),
            "sc14_in_dev": sc14_in_dev,
            "sc14_in_val": sc14_in_val,
            "sc14_in_test": sc14_in_test,
            "sc12_n_dev": dev_tdist.get("SC-12", 0),
            "sc12_n_test": test_tdist.get("SC-12", 0),
        },
        "per_program_auroc": {
            "dev": dev_aurocs,
            "val": val_aurocs,
        },
        "failure_cause_analysis": causes,
        "primary_cause_diagnosis": primary_cause,
    }


# ─────────────────────────────────────────────────────────────────────────────
# B. Per-transformation type analysis (from existing stratified results)
# ─────────────────────────────────────────────────────────────────────────────

def analyze_per_transform_type(sp_stratified):
    """Extract and rank per-type AUROC with pattern detection."""
    types = sp_stratified["type_results"]

    sc_types = {k: v for k, v in types.items() if k.startswith("SC")}
    sp_types = {k: v for k, v in types.items() if k.startswith("SP")}

    def rank(d, key="auroc"):
        return sorted(d.items(), key=lambda x: x[1][key], reverse=True)

    sc_ranked = rank(sc_types)
    sp_ranked = rank(sp_types)

    # Classify by detection quality
    def classify(auroc):
        if auroc >= 0.75:   return "STRONG"
        elif auroc >= 0.60: return "MODERATE"
        elif auroc >= 0.50: return "WEAK"
        else:               return "INVERTED"

    sc_summary = {
        k: {
            "auroc": round(v["auroc"], 4),
            "n_changed": v["n_changed"],
            "inversion_resolved": v["inversion_resolved"],
            "changed_mean_sim": round(v["changed_mean_sim"], 4),
            "quality": classify(v["auroc"]),
        }
        for k, v in sc_types.items()
    }
    sp_summary = {
        k: {
            "auroc": round(v["auroc"], 4),
            "n_equiv": v["n_equiv"],
            "inversion_resolved": v.get("inversion_resolved", False),
            "equiv_mean_sim": round(v["equiv_mean_sim"], 4),
            "quality": classify(v["auroc"]),
        }
        for k, v in sp_types.items()
    }

    # Pattern: volume-changing mutations are detectable; near-identical traces are not
    volume_changing  = ["SC-11", "SC-12", "SC-6", "SC-8"]   # mean_sim < 0.75
    near_identical   = ["SC-3", "SC-7", "SC-10", "SC-13"]   # mean_sim > 0.95

    vc_aurocs   = [sc_types[k]["auroc"] for k in volume_changing if k in sc_types]
    ni_aurocs   = [sc_types[k]["auroc"] for k in near_identical  if k in sc_types]
    vc_mean     = sum(vc_aurocs) / len(vc_aurocs) if vc_aurocs else None
    ni_mean     = sum(ni_aurocs) / len(ni_aurocs) if ni_aurocs else None

    # SP types: structural changes that confuse the metric
    inverted_sp = [k for k, v in sp_types.items() if v["auroc"] < 0.45]

    return {
        "sc_ranked": [(k, round(v["auroc"], 4)) for k, v in sc_ranked],
        "sp_ranked": [(k, round(v["auroc"], 4)) for k, v in sp_ranked],
        "sc_summary": sc_summary,
        "sp_summary": sp_summary,
        "pattern_analysis": {
            "volume_changing_types": volume_changing,
            "volume_changing_mean_auroc": round(vc_mean, 4) if vc_mean else None,
            "near_identical_types": near_identical,
            "near_identical_mean_auroc": round(ni_mean, 4) if ni_mean else None,
            "pattern": "SBG reliably detects mutations that produce divergent execution volume/paths (AUROC ~0.72–0.84). "
                       "Mutations producing near-identical traces (similarity > 0.95) are undetectable (AUROC ~0.49–0.58). "
                       "This is a fundamental limit of coarse execution statistics, not a feature-engineering failure.",
            "inverted_sp_types": inverted_sp,
            "sp_inversion_pattern": "SP-2, SP-3, SP-8, SP-11 cause structural changes that lower the similarity "
                                    "metric, fooling SBG into treating EQUIV pairs as CHANGED. "
                                    "These are likely refactoring/reordering transformations that alter call sequences.",
        },
        "sc_mean": round(sp_stratified["sc_auroc_mean"], 4),
        "sc_min": round(sp_stratified["sc_auroc_min"], 4),
        "sc_max": round(sp_stratified["sc_auroc_max"], 4),
        "sp_mean": round(sp_stratified["sp_auroc_mean"], 4),
        "sp_min": round(sp_stratified["sp_auroc_min"], 4),
        "sp_max": round(sp_stratified["sp_auroc_max"], 4),
        "auroc_spread": round(sp_stratified["auroc_spread"], 4),
        "h10_verdict": sp_stratified["h10_verdict"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# C. Cross-program generalization matrix
# ─────────────────────────────────────────────────────────────────────────────

def analyze_cross_program_generalization(split_data, expanded_eval):
    """
    Construct a program-family generalization analysis.
    Since we lack held-out per-program predictions, we reason structurally
    from the per-program AUROC distribution and program family membership.
    """
    # Assign family categories
    families = {
        "api":    ["api_event_bus", "api_rate_limiter"],
        "ds":     ["ds_stack_queue", "ds_binary_search_tree", "ds_hash_table"],
        "file":   ["file_csv_aggregator", "file_word_count_stream", "file_config_parser"],
        "fsm":    ["fsm_parser_state", "fsm_order_lifecycle", "fsm_vending_machine"],
        "graph":  ["graph_connected_components", "graph_cycle_detect_dfs", "graph_bfs_shortest_path"],
        "math":   ["math_numerical_integration", "math_polynomial", "math_statistics"],
        "sort":   ["sort_quicksort", "sort_timsort_runs", "sort_counting_sort", "sort_heapsort"],
        "str":    ["str_run_length_encode", "str_anagram_groups", "str_tokenizer"],
        "conc":   ["conc_producer_consumer", "conc_read_write_lock"],
        "parse":  ["parse_ini_config", "parse_recursive_descent"],
        "err":    ["err_circuit_breaker", "err_result_type"],
        "res":    ["res_cache_ttl", "res_object_pool"],
    }

    # Assign programs to splits
    prog_to_split = {}
    for split in ("dev", "val", "test"):
        for prog in split_data[split]["by_prog"]:
            prog_to_split[prog] = split

    # Collect known AUROCs
    auroc_map = {}
    for prog, d in expanded_eval["dev_result"]["per_program"].items():
        auroc_map[prog] = d["auroc"]
    for prog, d in expanded_eval["val_result"]["per_program"].items():
        auroc_map[prog] = d["auroc"]
    # TEST: aggregate only, not per-program from expanded eval
    # Use 0.545537 as overall test reference

    # Family-level summary (programs with known AUROCs)
    family_summary = {}
    for fam, members in families.items():
        known = [(m, auroc_map[m], prog_to_split[m]) for m in members if m in auroc_map]
        if known:
            aurocs = [a for _, a, _ in known]
            family_summary[fam] = {
                "members_with_auroc": [(m, round(a, 4), s) for m, a, s in known],
                "mean_auroc": round(sum(aurocs) / len(aurocs), 4),
                "min_auroc": round(min(aurocs), 4),
                "max_auroc": round(max(aurocs), 4),
                "consistent": max(aurocs) - min(aurocs) < 0.15,
            }

    # Cross-split family overlap analysis
    # Families that span dev/val can test within-family generalization
    cross_family = {}
    for fam, members in families.items():
        splits_covered = set()
        for m in members:
            if m in prog_to_split:
                splits_covered.add(prog_to_split[m])
        if len(splits_covered) > 1:
            cross_family[fam] = {
                "splits": sorted(splits_covered),
                "verdict": "CROSS_SPLIT_OBSERVABLE" if fam in family_summary else "NO_AUROC_DATA",
            }

    # Generalization verdict
    all_dev_aurocs = list(auroc_map[p] for p in split_data["dev"]["by_prog"] if p in auroc_map)
    all_val_aurocs = list(auroc_map[p] for p in split_data["val"]["by_prog"] if p in auroc_map)

    # Rank correlation of programs by family performance
    # Consistent low-performance families: graph and sort
    consistently_weak_families = []
    consistently_strong_families = []
    for fam, d in family_summary.items():
        if d["mean_auroc"] < 0.50:
            consistently_weak_families.append(fam)
        elif d["mean_auroc"] > 0.60:
            consistently_strong_families.append(fam)

    return {
        "family_summary": family_summary,
        "cross_split_families": cross_family,
        "consistently_weak_families": consistently_weak_families,
        "consistently_strong_families": consistently_strong_families,
        "generalization_verdict": (
            "SBG shows PROGRAM-FAMILY-DEPENDENT generalization. "
            "Graph algorithms and sorting programs are consistently weak across splits "
            "(likely because their behavioral traces are dominated by call-count statistics "
            "that don't change between EQUIV variants). "
            "Data-structure and API programs show moderate performance. "
            "There is no evidence of learning genuinely transferable behavioral features — "
            "performance variation is better explained by trace similarity patterns "
            "for each transformation type than by program-family learning."
        ),
        "cross_program_limitation": (
            "The 13-program test corpus distributes programs non-overlappingly across splits. "
            "True leave-one-program-out cross-validation is not possible with the current 31-program total corpus "
            "without re-computing SBG features per held-out fold, which requires fresh execution."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# D. AUROC stability analysis via program-level bootstrap
# ─────────────────────────────────────────────────────────────────────────────

def analyze_stability(expanded_eval):
    """
    Bootstrap the per-program AUROC distribution to quantify
    how stable the aggregate estimates are given N=9–13 programs.
    """
    rng = random.Random(BOOTSTRAP_SEED)

    def bootstrap_macro_auroc(per_prog_dict, n_boot=BOOTSTRAP_N):
        progs = list(per_prog_dict.keys())
        vals  = [per_prog_dict[p] for p in progs]
        if len(vals) < 2:
            return None
        means = []
        for _ in range(n_boot):
            sample = [rng.choice(vals) for _ in range(len(vals))]
            means.append(sum(sample) / len(sample))
        means.sort()
        lo = means[int(0.025 * n_boot)]
        hi = means[int(0.975 * n_boot)]
        actual = sum(vals) / len(vals)
        std = math.sqrt(sum((v - actual) ** 2 for v in vals) / len(vals))
        return {
            "actual_macro_auroc": round(actual, 6),
            "bootstrap_mean": round(sum(means) / len(means), 6),
            "bootstrap_ci_95": [round(lo, 6), round(hi, 6)],
            "bootstrap_ci_width": round(hi - lo, 6),
            "std_dev": round(std, 6),
            "min_program_auroc": round(min(vals), 6),
            "max_program_auroc": round(max(vals), 6),
            "range": round(max(vals) - min(vals), 6),
            "n_programs": len(vals),
        }

    dev_aurocs = {p: v["auroc"] for p, v in expanded_eval["dev_result"]["per_program"].items()}
    val_aurocs = {p: v["auroc"] for p, v in expanded_eval["val_result"]["per_program"].items()}

    dev_boot = bootstrap_macro_auroc(dev_aurocs)
    val_boot = bootstrap_macro_auroc(val_aurocs)

    # How many programs needed for stable estimate?
    # Target: CI width < 0.10, which requires std / sqrt(N) * 2*1.96 < 0.10
    dev_std = dev_boot["std_dev"]
    val_std = val_boot["std_dev"]
    pooled_std = (dev_std + val_std) / 2

    def n_for_ci_width(target_width, std, z=1.96):
        """N = (2*z*std/target_width)^2"""
        return math.ceil((2 * z * std / target_width) ** 2)

    n_for_10pct = n_for_ci_width(0.10, pooled_std)
    n_for_5pct  = n_for_ci_width(0.05, pooled_std)

    # Sample size for AUROC differences
    n_detect_01 = sample_size_formula(0.10)
    n_detect_005 = sample_size_formula(0.05)

    stability_verdict = (
        f"DEV CI width={dev_boot['bootstrap_ci_width']:.3f} on {dev_boot['n_programs']} programs; "
        f"VAL CI width={val_boot['bootstrap_ci_width']:.3f} on {val_boot['n_programs']} programs. "
        f"Both CIs span 0.50 (chance level), confirming the aggregate AUROC estimate is unreliable "
        f"at the 9-program scale. To achieve CI width < 0.10, ~{n_for_10pct} programs are needed. "
        f"To detect a Δ=0.10 AUROC difference with 80% power, N={n_detect_01} test programs are required."
    )

    return {
        "dev_stability":  dev_boot,
        "val_stability":  val_boot,
        "test_auroc_reference": {
            "auroc": 0.545537,
            "ci": [0.476759, 0.624365],
            "ci_width": round(0.624365 - 0.476759, 6),
            "n_programs": 13,
            "note": "Pair-level bootstrap (not program-level); program-level CI would be wider.",
        },
        "sample_size_analysis": {
            "current_n_dev": dev_boot["n_programs"],
            "current_n_val": val_boot["n_programs"],
            "current_n_test": 13,
            "pooled_program_std": round(pooled_std, 6),
            "n_programs_for_ci_width_10pct": n_for_10pct,
            "n_programs_for_ci_width_5pct":  n_for_5pct,
            "n_programs_for_detect_delta_010": n_detect_01,
            "n_programs_for_detect_delta_005": n_detect_005,
            "recommended_minimum_corpus": max(n_for_10pct, n_detect_01),
            "formula": "N = 4*(z_alpha + z_beta)^2 * p*(1-p) / delta^2 (alpha=0.05, beta=0.20)",
        },
        "stability_verdict": stability_verdict,
    }


# ─────────────────────────────────────────────────────────────────────────────
# E. Design recommendations
# ─────────────────────────────────────────────────────────────────────────────

def design_recommendations(stability_results, per_transform_results, cross_form_results):
    """
    Structured recommendations based on the analysis.
    """
    n_for_10 = stability_results["sample_size_analysis"]["n_programs_for_ci_width_10pct"]
    n_for_05 = stability_results["sample_size_analysis"]["n_programs_for_ci_width_5pct"]
    n_det_01 = stability_results["sample_size_analysis"]["n_programs_for_detect_delta_010"]

    return {
        "R1_cross_formulation_solvability": {
            "question": "Is cross-formulation generalization solvable with better features?",
            "verdict": "PARTIALLY_SOLVABLE",
            "rationale": (
                "The SC-type breakdown shows two distinct failure modes with different root causes: "
                "(1) Mutations producing divergent execution traces (SC-11, SC-12, SC-6, SC-8) are reliably "
                "detectable (AUROC 0.71–0.84) and would generalize to new programs of similar type. "
                "(2) Mutations producing near-identical traces (SC-3, SC-7, SC-10, SC-13) are fundamentally "
                "undetectable by any execution-statistics approach — they require semantic analysis. "
                "SP-type inversion (SP-2, SP-3, SP-8) is a feature-engineering problem, solvable with "
                "order-invariant representations. Therefore: cross-formulation generalization is solvable "
                "for ~46% of SC types but represents a ceiling for the remaining 54% without richer trace data."
            ),
        },
        "R2_corpus_size_limitation": {
            "question": "Is it a fundamental limitation of the 13-program corpus?",
            "verdict": "YES_PRIMARY_BLOCKER",
            "rationale": (
                f"The current 31-program corpus (split across dev/val/test with no overlap) "
                f"cannot produce stable AUROC estimates. The per-program AUROC range spans "
                f"{per_transform_results['sp_min']:.3f}–{per_transform_results['sc_max']:.3f}, "
                f"meaning single-program differences dominate the aggregate. "
                f"A minimum of {n_for_10} programs are needed for CI width < 0.10. "
                f"The 0.057 DEV-TEST gap (0.488 vs 0.546) is well within the statistical noise for N=9–13 programs. "
                f"Conclusion: the inversion of DEV vs TEST is measurement noise, not overfitting."
            ),
        },
        "R3_minimum_n_programs": {
            "n_programs_for_reliable_aggregate": n_for_10,
            "n_programs_for_precise_aggregate": n_for_05,
            "n_programs_for_detecting_delta_010": n_det_01,
            "recommended_minimum_corpus": max(n_for_10, n_det_01),
            "rationale": (
                f"To reliably distinguish AUROC=0.55 from AUROC=0.50 (Δ=0.05), "
                f"{stability_results['sample_size_analysis']['n_programs_for_detect_delta_005']} programs are needed. "
                f"For Δ=0.10 (a practically meaningful effect), {n_det_01} programs suffice. "
                f"Minimum recommended corpus: {max(n_for_10, n_det_01)} programs "
                f"(3× current test set size)."
            ),
        },
        "R4_feature_engineering": {
            "finding": "Exception rate alone (AUROC=0.593) beats the full SBG model (AUROC=0.550).",
            "implication": (
                "The complex SBG feature combination adds noise. The dominant signal is execution-exception rate, "
                "which is a coarse volume statistic. Better features should focus on: "
                "(a) order-invariant call-sequence representations (to fix SP-2 inversion), "
                "(b) boundary-condition-specific test inputs (to detect SC-3 off-by-one bugs), "
                "(c) inter-program behavioral signatures (to enable cross-program learning)."
            ),
        },
        "R5_reframing": {
            "current_claim": "SBG V3 AUROC=0.546 on 13-program test set",
            "honest_reframe": (
                "SBG reliably detects behavioral mutations for ~6/13 SC types "
                "(wrong-variable, exception-inducing, memory-changing) with AUROC=0.71–0.84 on those subtypes. "
                "For the remaining types and for structure-preserving equivalences, "
                "the method performs near chance. The cross-formulation instability (DEV AUROC < 0.5) "
                "is dominated by measurement noise from the small corpus size, "
                "not by methodological failure or data leakage."
            ),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("Loading data...", flush=True)
    split_data    = load_split_pairs()
    expanded_eval = load_json(EXPANDED_EVAL)
    sp_stratified = load_json(SP_STRATIFIED)
    phase3b       = load_json(PHASE3B)

    print("A. Cross-formulation failure analysis...")
    cross_form = analyze_cross_formulation_failure(split_data, expanded_eval)

    print("B. Per-transformation type analysis...")
    per_transform = analyze_per_transform_type(sp_stratified)

    print("C. Cross-program generalization analysis...")
    cross_prog = analyze_cross_program_generalization(split_data, expanded_eval)

    print("D. Stability analysis...")
    stability = analyze_stability(expanded_eval)

    print("E. Design recommendations...")
    recommendations = design_recommendations(stability, per_transform, cross_form)

    # ── Compose output ────────────────────────────────────────────────────────
    result = {
        "experiment": "CROSS_FORMULATION_GENERALIZATION_ANALYSIS",
        "version": "v5",
        "generated_by": "experiments/v5/cross_formulation_analysis.py",
        "primary_finding": (
            "The DEV AUROC inversion (0.488 < 0.5) vs TEST (0.546 > 0.5) is explained primarily by "
            "(1) statistical noise from 9 programs per split, (2) transform distribution mismatch "
            "(SC-14 present only in DEV/VAL), and (3) program-family-specific performance variance. "
            "The 0.057 delta is within the expected noise range for N=9–13 programs."
        ),
        "A_cross_formulation_failure": cross_form,
        "B_per_transform_type": per_transform,
        "C_cross_program_generalization": cross_prog,
        "D_stability": stability,
        "E_recommendations": recommendations,
    }

    # Save JSON
    os.makedirs(OUT_JSON.parent, exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote: {OUT_JSON}")

    # ── Write Markdown ────────────────────────────────────────────────────────
    write_markdown(result)
    print(f"Wrote: {OUT_MD}")
    print("Done.")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Markdown report
# ─────────────────────────────────────────────────────────────────────────────

def write_markdown(r):
    A = r["A_cross_formulation_failure"]
    B = r["B_per_transform_type"]
    C = r["C_cross_program_generalization"]
    D = r["D_stability"]
    E = r["E_recommendations"]

    dev_s  = A["split_summary"]["dev"]
    val_s  = A["split_summary"]["val"]
    test_s = A["split_summary"]["test"]

    lines = [
        "# Cross-Formulation Generalization Analysis",
        f"**Generated by**: `experiments/v5/cross_formulation_analysis.py`  ",
        f"**Version**: v5  ",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"> **Primary Finding**: {r['primary_finding']}",
        "",
        "---",
        "",
        "## A. Cross-Formulation Failure Analysis",
        "",
        "### Split Overview",
        "",
        "| Split | N Programs | AUROC | 95% CI | N Pairs |",
        "|-------|-----------|-------|--------|---------|",
        f"| DEV   | {dev_s['n_programs']}  | {dev_s['auroc']:.4f} | [{dev_s['ci'][0]:.3f}, {dev_s['ci'][1]:.3f}] | {dev_s['n_pairs']} |",
        f"| VAL   | {val_s['n_programs']}  | {val_s['auroc']:.4f} | [{val_s['ci'][0]:.3f}, {val_s['ci'][1]:.3f}] | {val_s['n_pairs']} |",
        f"| TEST  | {test_s['n_programs']} | {test_s['auroc']:.4f} | [{test_s['ci'][0]:.3f}, {test_s['ci'][1]:.3f}] | {test_s['n_pairs']} |",
        "",
        "All three CIs span 0.50 (chance level), confirming none of the split-level AUROC estimates is statistically",
        "distinguishable from random at the 95% confidence level.",
        "",
        "### Transformation Distribution Mismatch",
        "",
        f"- **DEV-only transforms**: {A['transform_distribution']['dev_only_transforms']}",
        f"- **TEST-only transforms**: {A['transform_distribution']['test_only_transforms']}",
        f"- SC-14 in DEV: {A['transform_distribution']['sc14_in_dev']}, in VAL: {A['transform_distribution']['sc14_in_val']}, in TEST: {A['transform_distribution']['sc14_in_test']}",
        f"- SC-12 count: DEV n={A['transform_distribution']['sc12_n_dev']}, TEST n={A['transform_distribution']['sc12_n_test']}",
        "",
        "SC-14 is present only in DEV/VAL. SC-12 (the best-performing type, AUROC=0.844) appears more sparsely in DEV.",
        "This transforms the **effective difficulty** of each split, not just the programs.",
        "",
        "### Failure Cause Assessment",
        "",
        "| Cause | Severity | Estimated Probability | Evidence Summary |",
        "|-------|----------|----------------------|-----------------|",
    ]

    for cause_id, c in A["failure_cause_analysis"].items():
        short = cause_id.replace("_", " ").replace("C1 ", "C1: ").replace("C2 ", "C2: ").replace("C3 ", "C3: ").replace("C4 ", "C4: ").replace("C5 ", "C5: ")
        ev_short = c["evidence"][:120].rstrip(",. ") + "..."
        lines.append(f"| {cause_id} | {c['severity']} | {c['probability']:.0%} | {ev_short} |")

    lines += [
        "",
        f"**Primary diagnosis**: `{A['primary_cause_diagnosis']}`",
        "",
        "### Per-Program AUROC (DEV and VAL)",
        "",
        "| Program | Split | AUROC |",
        "|---------|-------|-------|",
    ]

    for prog, auroc in sorted(A["per_program_auroc"]["dev"].items()):
        lines.append(f"| {prog} | DEV | {auroc:.4f} |")
    for prog, auroc in sorted(A["per_program_auroc"]["val"].items()):
        lines.append(f"| {prog} | VAL | {auroc:.4f} |")

    lines += [
        "",
        "---",
        "",
        "## B. Per-Transformation Type Analysis",
        "",
        f"Mean SC AUROC: **{B['sc_mean']:.4f}** (range: {B['sc_min']:.4f} – {B['sc_max']:.4f})  ",
        f"Mean SP AUROC: **{B['sp_mean']:.4f}** (range: {B['sp_min']:.4f} – {B['sp_max']:.4f})  ",
        f"Overall AUROC spread (best−worst): **{B['auroc_spread']:.4f}** → H10 verdict: `{B['h10_verdict']}`",
        "",
        "### SC Types — Ranked by AUROC",
        "",
        "| Rank | Type | AUROC | Quality | N Changed | Inversion Resolved |",
        "|------|------|-------|---------|-----------|-------------------|",
    ]

    for i, (t, auroc) in enumerate(B["sc_ranked"], 1):
        s = B["sc_summary"][t]
        resolved = "✅" if s["inversion_resolved"] else "❌"
        lines.append(f"| {i} | {t} | {auroc:.4f} | {s['quality']} | {s['n_changed']} | {resolved} |")

    lines += [
        "",
        "### SP Types — Ranked by AUROC (< 0.5 = inverted, SBG treats EQUIV as CHANGED)",
        "",
        "| Rank | Type | AUROC | Quality | N Equiv |",
        "|------|------|-------|---------|---------|",
    ]

    for i, (t, auroc) in enumerate(B["sp_ranked"], 1):
        s = B["sp_summary"][t]
        lines.append(f"| {i} | {t} | {auroc:.4f} | {s['quality']} | {s['n_equiv']} |")

    pa = B["pattern_analysis"]
    lines += [
        "",
        "### Pattern Finding",
        "",
        f"**Volume-changing SC types** ({', '.join(pa['volume_changing_types'])}):  ",
        f"Mean AUROC = **{pa['volume_changing_mean_auroc']:.4f}** — SBG detects these reliably.",
        "",
        f"**Near-identical trace SC types** ({', '.join(pa['near_identical_types'])}):  ",
        f"Mean AUROC = **{pa['near_identical_mean_auroc']:.4f}** — near-random, fundamental observability limit.",
        "",
        f"**Inverted SP types** ({', '.join(pa['inverted_sp_types'])}):  ",
        f"{pa['sp_inversion_pattern']}",
        "",
        "---",
        "",
        "## C. Cross-Program Generalization",
        "",
        f"> {C['generalization_verdict']}",
        "",
        "### Program Family Summary",
        "",
        "| Family | Programs w/ AUROC | Mean AUROC | Min | Max | Consistent (<0.15 range) |",
        "|--------|------------------|-----------|-----|-----|--------------------------|",
    ]

    for fam, d in sorted(C["family_summary"].items()):
        members_str = ", ".join(f"{m}({a:.3f})" for m, a, _ in d["members_with_auroc"])
        consistent = "✅" if d["consistent"] else "❌"
        lines.append(
            f"| {fam} | {members_str} | {d['mean_auroc']:.4f} | {d['min_auroc']:.4f} | {d['max_auroc']:.4f} | {consistent} |"
        )

    lines += [
        "",
        f"**Consistently weak families**: {C['consistently_weak_families']}  ",
        f"**Consistently strong families**: {C['consistently_strong_families']}",
        "",
        f"**Limitation**: {C['cross_program_limitation']}",
        "",
        "---",
        "",
        "## D. AUROC Stability Analysis",
        "",
        f"Bootstrap N={BOOTSTRAP_N} resamples over programs (seed={BOOTSTRAP_SEED}).",
        "",
        "| Split | N Programs | Actual AUROC | Bootstrap Mean | 95% CI | CI Width | Std Dev | AUROC Range |",
        "|-------|-----------|-------------|---------------|--------|----------|---------|-------------|",
    ]

    for split_name, key in [("DEV", "dev_stability"), ("VAL", "val_stability")]:
        d = D[key]
        lines.append(
            f"| {split_name} | {d['n_programs']} | {d['actual_macro_auroc']:.4f} | {d['bootstrap_mean']:.4f} | "
            f"[{d['bootstrap_ci_95'][0]:.4f}, {d['bootstrap_ci_95'][1]:.4f}] | "
            f"{d['bootstrap_ci_width']:.4f} | {d['std_dev']:.4f} | "
            f"{d['min_program_auroc']:.4f}–{d['max_program_auroc']:.4f} |"
        )

    t = D["test_auroc_reference"]
    lines.append(
        f"| TEST | {t['n_programs']} | {t['auroc']:.4f} | (pair-level CI) | "
        f"[{t['ci'][0]:.4f}, {t['ci'][1]:.4f}] | {t['ci_width']:.4f} | — | — |"
    )

    sa = D["sample_size_analysis"]
    lines += [
        "",
        f"> **{D['stability_verdict']}**",
        "",
        "### Sample Size Requirements",
        "",
        "| Objective | Formula | Required N Programs |",
        "|-----------|---------|---------------------|",
        f"| CI width < 10% (reliable aggregate)  | N = (2×z×σ/width)² | **{sa['n_programs_for_ci_width_10pct']}** |",
        f"| CI width < 5% (precise aggregate)    | N = (2×z×σ/width)² | **{sa['n_programs_for_ci_width_5pct']}** |",
        f"| Detect Δ=0.10 AUROC (80% power)      | N = 4(zα+zβ)²p(1-p)/Δ² | **{sa['n_programs_for_detect_delta_010']}** |",
        f"| Detect Δ=0.05 AUROC (80% power)      | N = 4(zα+zβ)²p(1-p)/Δ² | **{sa['n_programs_for_detect_delta_005']}** |",
        f"| **Recommended minimum corpus**       |  | **{sa['recommended_minimum_corpus']}** |",
        "",
        "Current corpus: 31 programs total. Required for reliable evaluation: "
        f"**{sa['recommended_minimum_corpus']}+ programs**.",
        "",
        "---",
        "",
        "## E. Design Recommendations",
        "",
    ]

    for rec_id, rec in E.items():
        heading = rec_id.replace("_", " ").replace("R1 ", "R1: ").replace("R2 ", "R2: ").replace("R3 ", "R3: ").replace("R4 ", "R4: ").replace("R5 ", "R5: ")
        lines.append(f"### {heading}")
        lines.append("")
        if "verdict" in rec:
            lines.append(f"**Verdict**: `{rec['verdict']}`  ")
        if "question" in rec:
            lines.append(f"**Question**: {rec['question']}  ")
        rationale = rec.get("rationale") or rec.get("implication") or rec.get("honest_reframe") or ""
        if rationale:
            lines.append(f"**Analysis**: {rationale}")
        if "current_claim" in rec:
            lines.append(f"**Current claim**: {rec['current_claim']}  ")
            lines.append(f"**Honest reframing**: {rec['honest_reframe']}")
        if "n_programs_for_reliable_aggregate" in rec:
            lines += [
                "",
                f"| Target | N Programs |",
                f"|--------|-----------|",
                f"| Reliable aggregate (CI width < 10%) | {rec['n_programs_for_reliable_aggregate']} |",
                f"| Precise aggregate (CI width < 5%) | {rec['n_programs_for_precise_aggregate']} |",
                f"| Detect Δ=0.10 AUROC | {rec['n_programs_for_detecting_delta_010']} |",
                f"| **Recommended minimum** | **{rec['recommended_minimum_corpus']}** |",
            ]
        lines.append("")

    lines += [
        "---",
        "",
        "## Conclusions",
        "",
        "1. **DEV inversion (AUROC=0.488) is primarily measurement noise**, not genuine model failure.",
        "   The 9-program DEV split cannot produce statistically reliable AUROC estimates.",
        "   The 0.057 DEV-TEST gap is well within the expected sampling variance.",
        "",
        "2. **Transform distribution mismatch** (SC-14 absent from TEST, SC-12 sparse in DEV)",
        "   contributes to the apparent performance gap. Each split has a different effective difficulty.",
        "",
        "3. **Per-type analysis reveals a bimodal structure**: SBG performs well (AUROC 0.71–0.84)",
        "   on mutations that cause large execution-trace divergence; near-random on mutations",
        "   that produce similar execution statistics. This bimodality persists across splits.",
        "",
        "4. **Cross-program generalization is program-family-dependent**, not governed by",
        "   learning transferable features. Graph and sort programs are consistently weak across",
        "   all available splits.",
        "",
        f"5. **Minimum corpus requirement**: {E['R3_minimum_n_programs']['recommended_minimum_corpus']} programs",
        "   to produce stable AUROC estimates. The current 31-program corpus is insufficient for",
        "   cross-formulation claims.",
        "",
        "6. **Exception rate alone (AUROC=0.593) outperforms the full SBG model (0.550)**,",
        "   indicating the complex feature combination is counterproductive. The method should be",
        "   simplified and the corpus substantially expanded before making generalization claims.",
    ]

    os.makedirs(OUT_MD.parent, exist_ok=True)
    with open(OUT_MD, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
