"""
experiments/final/analyse_results.py
====================================
Turns the raw per-pair records into the authoritative result artifact.

Three evaluation sets are reported for every predictor, and the denominator of
each is stated explicitly. The published artifacts reported an AUROC over 643
pairs under a heading that said 744; that gap is what these sets make visible.

  ALL           every pair in the split. Pairs that could not be executed are
                not deleted: they are scored at the worst defensible value for
                the predictor (distance 0, i.e. "indistinguishable"), which
                charges every failure to the method rather than hiding it.
                This is the only set whose denominator equals the split size.

  EVALUABLE     pairs both of whose programs executed under the protocol. This
                is the set the published numbers were actually computed on.

  VALID         EVALUABLE minus pairs the static benchmark audit rejects:
                uncompilable variants, and CHANGED pairs whose mutation cannot
                be reached from the entry function. The filter is static, is
                applied identically to every predictor, and never consults a
                score. See benchmark/scripts/observability_audit.py.

Statistics use sbg.statistics: tie-aware AUROC, cluster bootstrap by base
program, within-cluster label permutation with the (b+1)/(m+1) estimator, and
a paired cluster bootstrap for the difference between two predictors -- the
last because comparing two marginal confidence intervals for overlap is not a
test of their difference, and the published comparison did exactly that.

Usage:
    python3 experiments/final/analyse_results.py --split test --protocol published
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Dict, List

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sbg.statistics import (                                    # noqa: E402
    auroc, cluster_bootstrap_ci, cluster_permutation_p, holm_bonferroni,
    label_shuffle_noise_floor, paired_cluster_bootstrap_delta,
)
from experiments.final.extraction import PREDICTORS             # noqa: E402

SEED = 42
N_BOOTSTRAP = 2000
N_PERMUTATIONS = 2000
N_SHUFFLES = 500

# Declared before any of these numbers were computed: the reference the
# research question is about. SBG's claim is that the representation adds
# something beyond the cheapest execution statistic.
PRIMARY_PREDICTOR = "sbg_v5"
REFERENCE_PREDICTORS = ("exception_fraction", "exception_component_v3",
                        "call_count", "combined_shortcut", "sbg_v3",
                        "static_ast")

# PROTOCOL output_free_v7 Holm family, fixed by
# docs/current/PHASE2_PREREGISTRATION.md §5. The last comparator is the model
# selected on dev by experiments/final/fit_weights.py (omitted when that is V5
# itself, since a predictor compared with itself is not a test).
PREREG_V7_REFERENCES = ("static_ast", "static_token", "exception_fraction",
                        "call_count", "sbg_v3")
LEARNED_PREDICTOR = {"M1": "learned_m1", "M2": "learned_m2"}


def load_rows(path: pathlib.Path) -> List[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_validity(audit_path: pathlib.Path) -> Dict[str, dict]:
    payload = json.loads(audit_path.read_text())
    return {row["pair_id"]: row for row in payload["pairs"]}


def build_sets(rows: List[dict], validity: Dict[str, dict]) -> Dict[str, List[dict]]:
    evaluable = [r for r in rows if r["evaluated"]]

    def is_valid(row: dict) -> bool:
        verdict = validity.get(row["pair_id"])
        if verdict is None:
            return False
        if verdict.get("status") != "ok":
            return False
        if row["label"] == 1 and verdict.get("observable") is not True:
            return False
        return True

    return {
        "ALL": rows,
        "EVALUABLE": evaluable,
        "VALID": [r for r in evaluable if is_valid(r)],
    }


def vectors(rows: List[dict], predictor: str) -> tuple:
    distances, labels, clusters = [], [], []
    for row in rows:
        if row["evaluated"] and predictor in row["scores"]:
            distances.append(row["scores"][predictor])
        else:
            # Unevaluable pair: the predictor produced nothing, so it cannot
            # distinguish the two programs. Distance 0 is the honest encoding
            # of "no evidence of difference" and costs the method on positives.
            distances.append(0.0)
        labels.append(row["label"])
        clusters.append(row["base_id"])
    return distances, labels, clusters


def evaluate_predictor(rows: List[dict], predictor: str) -> dict:
    present = any(predictor in r.get("scores", {}) for r in rows if r["evaluated"])
    if not present:
        return {"n": len(rows), "auroc": None,
                "note": f"{predictor} not present in this per-pair record"}
    distances, labels, clusters = vectors(rows, predictor)
    n_pos = sum(labels)
    if not rows or n_pos == 0 or n_pos == len(labels):
        return {"n": len(rows), "auroc": None,
                "note": "degenerate set (single class or empty)"}
    lower, upper, n_effective = cluster_bootstrap_ci(
        distances, labels, clusters, n_bootstrap=N_BOOTSTRAP, seed=SEED)
    return {
        "n": len(rows),
        "n_changed": n_pos,
        "n_equivalent": len(labels) - n_pos,
        "n_clusters": len(set(clusters)),
        "auroc": round(auroc(distances, labels), 6),
        "ci95_cluster_bootstrap": [lower, upper],
        "bootstrap_resamples_effective": n_effective,
        "permutation_p": round(cluster_permutation_p(
            distances, labels, clusters,
            n_permutations=N_PERMUTATIONS, seed=SEED), 6),
        "n_tied_at_zero": sum(1 for d in distances if d == 0.0),
    }


def program_table(rows: List[dict]) -> Dict[str, dict]:
    """Per base program: entry tier, pairs, evaluated pairs, failure kinds."""
    table: Dict[str, dict] = {}
    for row in rows:
        entry = table.setdefault(row["base_id"], {
            "entry": row.get("base_entry"), "n_pairs": 0, "n_evaluated": 0,
            "failures": {}})
        if entry["entry"] is None and row.get("base_entry"):
            entry["entry"] = row["base_entry"]
        entry["n_pairs"] += 1
        if row["evaluated"]:
            entry["n_evaluated"] += 1
        else:
            key = f"{row['failure_side']}:{row['failure_kind']}"
            entry["failures"][key] = entry["failures"].get(key, 0) + 1
    for entry in table.values():
        discovery = entry["entry"] or ""
        entry["tier"] = ("class" if discovery.startswith("class:")
                         else "function" if discovery else "none")
    return dict(sorted(table.items()))


def analyse(split: str, protocol: str, artifact_dir: pathlib.Path,
            audit_path: pathlib.Path, tag: str = None,
            references: tuple = REFERENCE_PREDICTORS,
            extra_predictors: tuple = (), family_note: str = None) -> dict:
    tag = tag or split
    rows = load_rows(artifact_dir / f"pairs_{tag}_{protocol}.jsonl")
    validity = load_validity(audit_path)
    sets = build_sets(rows, validity)

    failure_ledger: Dict[str, int] = {}
    for row in rows:
        if not row["evaluated"]:
            key = f"{row['failure_side']}:{row['failure_kind']}"
            failure_ledger[key] = failure_ledger.get(key, 0) + 1

    results: Dict[str, dict] = {}
    for set_name, subset in sets.items():
        block = {predictor: evaluate_predictor(subset, predictor)
                 for predictor in tuple(PREDICTORS) + tuple(extra_predictors)}

        # Paired comparisons of the primary predictor against each reference.
        comparisons = {}
        if subset and 0 < sum(r["label"] for r in subset) < len(subset):
            primary, labels, clusters = vectors(subset, PRIMARY_PREDICTOR)
            for reference in references:
                other, _, _ = vectors(subset, reference)
                comparisons[f"{PRIMARY_PREDICTOR}_minus_{reference}"] = (
                    paired_cluster_bootstrap_delta(
                        primary, other, labels, clusters,
                        n_bootstrap=N_BOOTSTRAP, seed=SEED))
            block_p = {k: v["p_two_sided"] for k, v in comparisons.items()
                       if v["p_two_sided"] is not None}
            if block_p:
                comparisons["holm_bonferroni"] = holm_bonferroni(block_p)
            noise = label_shuffle_noise_floor(primary, labels, clusters,
                                              n_shuffles=N_SHUFFLES, seed=SEED)
        else:
            noise = None

        results[set_name] = {
            "predictors": block,
            "paired_comparisons": comparisons,
            "label_shuffle_noise_floor_primary": noise,
        }

    return {
        "experiment": "AUTHORITATIVE_MAIN_EVALUATION",
        "split": split,
        "tag": tag,
        "dataset": rows[0].get("dataset") if rows else None,
        "protocol": protocol,
        "validity_audit": str(audit_path.name),
        "seed": SEED,
        "statistics": {
            "auroc": "tie-aware Wilcoxon-Mann-Whitney (sbg.statistics.auroc)",
            "ci": f"cluster bootstrap by base program, {N_BOOTSTRAP} resamples",
            "permutation": f"within-cluster label permutation, {N_PERMUTATIONS} "
                           "permutations, (b+1)/(m+1) estimator",
            "comparison": f"paired cluster bootstrap, {N_BOOTSTRAP} resamples, "
                          "Holm-Bonferroni corrected",
            "noise_floor": f"{N_SHUFFLES} within-cluster label shuffles",
        },
        "set_definitions": {
            "ALL": "every pair in the split; unevaluable pairs scored at distance 0",
            "EVALUABLE": "pairs whose base and variant both executed",
            "VALID": "EVALUABLE minus statically invalid pairs "
                     "(uncompilable, or CHANGED but unobservable)",
        },
        "set_sizes": {name: len(subset) for name, subset in sets.items()},
        "failure_ledger": dict(sorted(failure_ledger.items())),
        "primary_predictor": PRIMARY_PREDICTOR,
        "comparison_family": list(references),
        **({"comparison_family_note": family_note} if family_note else {}),
        **({"programs": program_table(rows),
            "programs_by_tier": {
                tier: sorted(b for b, e in program_table(rows).items()
                             if e["tier"] == tier and e["n_evaluated"] > 0)
                for tier in ("function", "class")},
            "programs_not_evaluated": sorted(
                b for b, e in program_table(rows).items() if e["n_evaluated"] == 0)}
           if extra_predictors or family_note else {}),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", default="test")
    parser.add_argument("--protocol", default="published")
    parser.add_argument("--artifact-dir", default=str(REPO_ROOT / "artifacts" / "final"))
    parser.add_argument("--audit", default=str(REPO_ROOT / "artifacts" / "final"
                                               / "BENCHMARK_VALIDITY_AUDIT.json"))
    parser.add_argument("--tag", default=None,
                        help="name used in the input and output filenames "
                             "(default: the split)")
    parser.add_argument("--family", default="default", choices=["default", "prereg_v7"],
                        help="prereg_v7: the Holm family of PHASE2_PREREGISTRATION.md §5")
    parser.add_argument("--weights", default=str(REPO_ROOT / "artifacts" / "final"
                                                 / "WEIGHT_FITTING.json"))
    args = parser.parse_args()

    artifact_dir = pathlib.Path(args.artifact_dir)
    references, extra, note = REFERENCE_PREDICTORS, (), None
    if args.family == "prereg_v7":
        chosen = json.loads(pathlib.Path(args.weights).read_text())["chosen_on_dev"]
        references = PREREG_V7_REFERENCES + (
            (LEARNED_PREDICTOR[chosen],) if chosen in LEARNED_PREDICTOR else ())
        extra = tuple(LEARNED_PREDICTOR.values())
        note = (f"dev-selected model: {chosen}"
                + ("" if chosen in LEARNED_PREDICTOR
                   else " (V5 itself, so no sixth comparison)"))
    payload = analyse(args.split, args.protocol, artifact_dir,
                      pathlib.Path(args.audit), args.tag, references, extra, note)
    out = artifact_dir / f"MAIN_EVALUATION_{args.tag or args.split}_{args.protocol}.json"
    out.write_text(json.dumps(payload, indent=2) + "\n")

    print(f"set sizes: {payload['set_sizes']}")
    print(f"failures : {payload['failure_ledger']}")
    for set_name, block in payload["results"].items():
        print(f"\n[{set_name}]")
        for predictor, stats in sorted(block["predictors"].items(),
                                       key=lambda kv: -(kv[1].get("auroc") or 0)):
            if stats.get("auroc") is None:
                continue
            print(f"  {predictor:24s} AUROC={stats['auroc']:.4f} "
                  f"CI={stats['ci95_cluster_bootstrap']} "
                  f"p={stats['permutation_p']:.4f} n={stats['n']}")
    print(f"\nwrote {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
