"""
experiments/v2/run_feature_ablation_wave8.py
==============================================
Phase 4 Wave 8 — Feature ablation of the full 8-dimension genome.

Uses the SAME 8-dimension genome extraction machinery already used by
sbg/v2/static_proxy.py (the v1 full genome: CONTROL, DATA, STATE,
RESOURCE, TEMPORAL, ERROR, INTERACTION, EXECUTION) and sbg/distance.py's
behavioral_distance(), which supports a `dimensions=[...]` restriction
parameter natively — no new distance code is written; this ablation
purely restricts WHICH of the 8 already-implemented, already-tested
dimension distances are included in the weighted aggregate.

Design
------
For each of:
  - 8 single-dimension configurations (CONTROL alone, DATA alone, ...)
  - 8 leave-one-out configurations (all except CONTROL, all except DATA, ...)
  - 1 full 8-dimension configuration (all dimensions, DEFAULT_WEIGHTS)

...compute similarity = 1 - behavioral_distance(g1, g2, dimensions=subset)
for every pair in the frozen TEST split, then AUROC + bootstrap CI +
noise-floor comparison, using the SAME evaluation harness as H7-H10.

IMPORTANT: dimension SUBSETS are fixed a priori (all single dims, all
leave-one-out dims, full set) — 17 conditions total, decided BEFORE
looking at any per-condition AUROC. No dimension was selected or
excluded based on test performance (Phase 4 mandate: "Do NOT select
dimensions based on test performance").

This uses the v1 8-dim genome via sbg/v2/static_proxy.py's genome
extraction pipeline (same code B08_hybrid's static component uses),
NOT the V2-only DynamicGenome (5 dims) used by B07. This is intentional:
the Phase 4 spec explicitly names all 8 dimensions (CONTROL, DATA,
STATE, RESOURCE, TEMPORAL, ERROR, INTERACTION, EXECUTION), which only
exist together in the v1 8-dim genome architecture.
"""
from __future__ import annotations

import itertools
import json
import pathlib
import random
import sys
from typing import Dict, List

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from baselines.common import load_pairs, pairs_to_labels, compute_auroc  # noqa: E402
from sbg.distance import behavioral_distance, DEFAULT_WEIGHTS  # noqa: E402
from sbg.v2.static_proxy import _cached_extract_genome  # noqa: E402

ARTIFACT_PATH = REPO_ROOT / "artifacts" / "v2" / "H10_FEATURE_ABLATION.json"

ALL_DIMS = list(DEFAULT_WEIGHTS.keys())  # CONTROL, DATA, STATE, RESOURCE, TEMPORAL, ERROR, INTERACTION, EXECUTION
BOOTSTRAP_N = 1000
BOOTSTRAP_SEED = 42
NOISE_FLOOR_UPPER = 0.544121  # artifacts/v2/NEGATIVE_CONTROL_RESULTS.json

# Pre-registered (a-priori) set of 17 ablation configurations — fixed BEFORE
# any test-performance was observed.
CONFIGS: Dict[str, List[str]] = {}
for dim in ALL_DIMS:
    CONFIGS[f"SINGLE_{dim}"] = [dim]
for dim in ALL_DIMS:
    CONFIGS[f"LOO_{dim}"] = [d for d in ALL_DIMS if d != dim]
CONFIGS["FULL_8DIM"] = list(ALL_DIMS)


def _similarity(path_a: str, path_b: str, dims: List[str]) -> float:
    rpa = str((REPO_ROOT / path_a).resolve())
    rpb = str((REPO_ROOT / path_b).resolve())
    ga = _cached_extract_genome(rpa)
    gb = _cached_extract_genome(rpb)
    if ga is None or gb is None:
        return 0.5
    result = behavioral_distance(ga, gb, DEFAULT_WEIGHTS, dimensions=dims)
    return max(0.0, min(1.0, 1.0 - result["total_distance"]))


def _bootstrap_ci(sims, labels):
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(sims)
    boots = []
    for _ in range(BOOTSTRAP_N):
        idx = [rng.randint(0, n - 1) for _ in range(n)]
        boots.append(compute_auroc([sims[i] for i in idx], [labels[i] for i in idx]))
    boots.sort()
    return boots[25], boots[974]


def _cohens_d(sims, labels):
    import math
    eq = [s for s, l in zip(sims, labels) if l == 0]
    ch = [s for s, l in zip(sims, labels) if l == 1]
    if len(eq) < 2 or len(ch) < 2:
        return 0.0
    m1, m2 = sum(eq) / len(eq), sum(ch) / len(ch)
    v1 = sum((x - m1) ** 2 for x in eq) / (len(eq) - 1)
    v2 = sum((x - m2) ** 2 for x in ch) / (len(ch) - 1)
    pooled = math.sqrt(((len(eq) - 1) * v1 + (len(ch) - 1) * v2) / (len(eq) + len(ch) - 2))
    return 0.0 if pooled == 0 else (m1 - m2) / pooled


def main():
    print("[Wave8-Ablation] Loading frozen TEST pairs (744)...")
    test_pairs = load_pairs("test")
    labels = pairs_to_labels(test_pairs)

    print("[Wave8-Ablation] Extracting v1 8-dim genomes for all unique programs (cached)...")
    # Warm the cache once per unique path to avoid duplicate extraction cost.
    unique_paths = set()
    for p in test_pairs:
        unique_paths.add(p["base_path"])
        unique_paths.add(p["variant_path"])
    for i, path in enumerate(sorted(unique_paths)):
        _cached_extract_genome(str((REPO_ROOT / path).resolve()))
        if (i + 1) % 100 == 0:
            print(f"  genome-extracted {i+1}/{len(unique_paths)} unique programs")

    results = {}
    for config_name, dims in CONFIGS.items():
        sims = [_similarity(p["base_path"], p["variant_path"], dims) for p in test_pairs]
        auroc = compute_auroc(sims, labels)
        ci_lower, ci_upper = _bootstrap_ci(sims, labels)
        d = _cohens_d(sims, labels)
        eq_mean = sum(s for s, l in zip(sims, labels) if l == 0) / max(1, labels.count(0))
        ch_mean = sum(s for s, l in zip(sims, labels) if l == 1) / max(1, labels.count(1))
        results[config_name] = {
            "dimensions": dims,
            "n_dimensions": len(dims),
            "n": len(sims),
            "auroc": round(auroc, 6),
            "ci_lower": round(ci_lower, 6),
            "ci_upper": round(ci_upper, 6),
            "cohens_d": round(d, 6),
            "eq_mean_similarity": round(eq_mean, 6),
            "changed_mean_similarity": round(ch_mean, 6),
            "inversion": bool(ch_mean > eq_mean),
            "above_noise_floor": bool(auroc > NOISE_FLOOR_UPPER),
        }
        print(f"  {config_name}: AUROC={auroc:.4f} CI=[{ci_lower:.4f},{ci_upper:.4f}] "
              f"{'ABOVE' if auroc > NOISE_FLOOR_UPPER else 'within'} noise floor")

    single_aurocs = {k: v["auroc"] for k, v in results.items() if k.startswith("SINGLE_")}
    loo_aurocs = {k: v["auroc"] for k, v in results.items() if k.startswith("LOO_")}
    full_auroc = results["FULL_8DIM"]["auroc"]

    best_single = max(single_aurocs, key=single_aurocs.get)
    worst_single = min(single_aurocs, key=single_aurocs.get)
    # LOO dimension whose removal HURTS most = the LOO config with LOWEST auroc
    # (i.e. removing that dimension is most damaging => that dim is most important)
    most_important_dim_by_loo = min(loo_aurocs, key=loo_aurocs.get).replace("LOO_", "")
    least_important_dim_by_loo = max(loo_aurocs, key=loo_aurocs.get).replace("LOO_", "")

    n_single_above_floor = sum(1 for v in results.values() if v["auroc"] > NOISE_FLOOR_UPPER and "SINGLE" in "")
    n_single_above_floor = sum(
        1 for k, v in results.items() if k.startswith("SINGLE_") and v["above_noise_floor"]
    )
    n_loo_above_floor = sum(
        1 for k, v in results.items() if k.startswith("LOO_") and v["above_noise_floor"]
    )

    summary = {
        "purpose": (
            "Determine whether SBG's (weak) discriminative signal is driven by "
            "one dominant feature family or represents genuinely multidimensional "
            "behavioral structure, per Phase 4 Wave 8 mandate."
        ),
        "methodology_note": (
            "Uses the v1 8-dimension genome (sbg/distance.py behavioral_distance "
            "with a dimensions= restriction) because CONTROL/DATA/STATE/RESOURCE/"
            "TEMPORAL/ERROR/INTERACTION/EXECUTION as 8 distinct named dimensions "
            "only exist together in the v1 architecture; B07's V2 DynamicGenome "
            "condenses execution-derived signal into 5 output-free fields (not "
            "8 named genomes) by design (SAFEGUARD-2/3), so it is not the right "
            "vehicle for THIS specific 8-way ablation as literally specified."
        ),
        "no_test_tuning_statement": (
            "All 17 configurations (8 single, 8 leave-one-out, 1 full) were fixed "
            "a priori as the complete, exhaustive, non-cherry-picked set implied "
            "by 'at minimum: [8 named dimensions] ... single ... leave-one-out ... "
            "full'. No dimension subset was chosen or discarded based on any "
            "observed test AUROC."
        ),
        "full_8dim_auroc": full_auroc,
        "best_single_dimension": {"dimension": best_single.replace("SINGLE_", ""), "auroc": single_aurocs[best_single]},
        "worst_single_dimension": {"dimension": worst_single.replace("SINGLE_", ""), "auroc": single_aurocs[worst_single]},
        "most_important_dimension_by_loo_drop": most_important_dim_by_loo,
        "least_important_dimension_by_loo_drop": least_important_dim_by_loo,
        "n_single_dims_above_noise_floor": n_single_above_floor,
        "n_loo_configs_above_noise_floor": n_loo_above_floor,
        "n_single_dims_total": len(ALL_DIMS),
        "interpretation": (
            "See docs analysis for full narrative interpretation of whether "
            "performance is concentrated in one dimension or distributed."
        ),
    }

    output = {
        "hypothesis_context": "Phase 4 Wave 8 — Feature ablation (supports RQ4)",
        "genome_architecture": "v1 8-dimension genome (sbg/distance.py behavioral_distance)",
        "default_weights": DEFAULT_WEIGHTS,
        "noise_floor_upper_bound": NOISE_FLOOR_UPPER,
        "bootstrap_config": {"n": BOOTSTRAP_N, "seed": BOOTSTRAP_SEED},
        "configurations": results,
        "summary": summary,
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n[Wave8-Ablation] Wrote {ARTIFACT_PATH}")
    print(f"[Wave8-Ablation] FULL_8DIM AUROC: {full_auroc:.4f}")
    print(f"[Wave8-Ablation] Best single dim: {best_single} ({single_aurocs[best_single]:.4f})")
    print(f"[Wave8-Ablation] Worst single dim: {worst_single} ({single_aurocs[worst_single]:.4f})")
    print(f"[Wave8-Ablation] Most important (by LOO drop): {most_important_dim_by_loo}")

    return output


if __name__ == "__main__":
    main()
