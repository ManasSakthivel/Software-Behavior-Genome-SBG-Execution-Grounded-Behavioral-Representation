"""
experiments/phase4/e7_ablation.py
===================================
E7: Genome-Component Ablation.

Tests which static SBG dimensions (CONTROL, DATA, ERROR) contribute to
behavioral distance. Runs 5 ablation conditions on dev→test:
  1. CONTROL only
  2. DATA only
  3. ERROR only
  4. CONTROL + DATA
  5. CONTROL + DATA + ERROR  (= B07)

Also loads Phase 3 results for B01–B08 for the full ablation table.

Hypothesis addressed: H6 (multi-dimensional SBG outperforms any single dimension)
"""
import json
import pathlib
import random
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from baselines.common import (
    load_pairs, load_source, compute_metrics, compute_auroc, compute_auprc,
    find_optimal_threshold, pairs_to_labels, save_results,
    REPO_ROOT as COMMON_ROOT
)
from sbg.extraction.static.extractor import (
    ControlGenomeExtractor, distance as ctrl_dist, canonicalize as canon_ctrl
)
from sbg.extraction.static.data_genome import (
    DataGenomeExtractor, distance as data_dist, canonicalize as canon_data
)
from sbg.extraction.static.error_genome import (
    ErrorGenomeExtractor, distance as err_dist, canonicalize as canon_err
)

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "phase4" / "E7"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
PHASE3_DIR = REPO_ROOT / "artifacts" / "phase3"

SEED = 42
N_BOOTSTRAP = 1000


def extract_all(source: str) -> dict:
    """Extract all three static genomes from source."""
    result = {}
    try:
        result["CONTROL"] = canon_ctrl(ControlGenomeExtractor().extract(source))
    except Exception:
        result["CONTROL"] = None
    try:
        result["DATA"] = canon_data(DataGenomeExtractor().extract(source))
    except Exception:
        result["DATA"] = None
    try:
        result["ERROR"] = canon_err(ErrorGenomeExtractor().extract(source))
    except Exception:
        result["ERROR"] = None
    return result


def build_score_fn(dimensions: list, weights: dict):
    """Build a scoring function for the given ablation dimensions."""
    dim_fns = {
        "CONTROL": ctrl_dist,
        "DATA": data_dist,
        "ERROR": err_dist,
    }
    w_total = sum(weights.get(d, 1.0) for d in dimensions)

    def score_fn(src_a: str, src_b: str) -> float:
        g_a = extract_all(src_a)
        g_b = extract_all(src_b)
        total_d = 0.0
        total_w = 0.0
        for d in dimensions:
            ga = g_a.get(d)
            gb = g_b.get(d)
            if ga is not None and gb is not None:
                try:
                    dist = dim_fns[d](ga, gb)
                    w = weights.get(d, 1.0) / w_total
                    total_d += w * dist
                    total_w += w
                except Exception:
                    pass
        if total_w == 0:
            return 0.5  # neutral
        sim = 1.0 - (total_d / total_w)
        return max(0.0, min(1.0, sim))

    return score_fn


ABLATION_CONDITIONS = {
    "CONTROL_only": {
        "dimensions": ["CONTROL"],
        "weights": {"CONTROL": 1.0},
    },
    "DATA_only": {
        "dimensions": ["DATA"],
        "weights": {"DATA": 1.0},
    },
    "ERROR_only": {
        "dimensions": ["ERROR"],
        "weights": {"ERROR": 1.0},
    },
    "CONTROL_DATA": {
        "dimensions": ["CONTROL", "DATA"],
        "weights": {"CONTROL": 0.20, "DATA": 0.15},
    },
    "CONTROL_DATA_ERROR": {
        "dimensions": ["CONTROL", "DATA", "ERROR"],
        "weights": {"CONTROL": 0.20, "DATA": 0.15, "ERROR": 0.10},
    },
}


def run_ablation_condition(name: str, config: dict, dev_pairs: list, test_pairs: list) -> dict:
    print(f"\n  [{name}] dims={config['dimensions']}")
    fn = build_score_fn(config["dimensions"], config["weights"])

    dev_labels = pairs_to_labels(dev_pairs)
    dev_sims = []
    for p in dev_pairs:
        try:
            s = float(fn(load_source(p["base_path"]), load_source(p["variant_path"])))
        except Exception:
            s = 0.5
        dev_sims.append(s)

    threshold = find_optimal_threshold(dev_sims, dev_labels)
    dev_metrics = compute_metrics(dev_sims, dev_labels, threshold)

    test_labels = pairs_to_labels(test_pairs)
    test_sims = []
    for p in test_pairs:
        try:
            s = float(fn(load_source(p["base_path"]), load_source(p["variant_path"])))
        except Exception:
            s = 0.5
        test_sims.append(s)

    test_metrics = compute_metrics(test_sims, test_labels, threshold)

    print(f"    DEV  threshold={threshold:.4f}  F1={dev_metrics['f1']:.4f}  AUROC={dev_metrics['auroc']:.4f}")
    print(f"    TEST F1={test_metrics['f1']:.4f}  AUROC={test_metrics['auroc']:.4f}  AUPRC={test_metrics['auprc']:.4f}")

    return {
        "condition": name,
        "dimensions": config["dimensions"],
        "dev_threshold": round(threshold, 6),
        "dev_f1": dev_metrics["f1"],
        "dev_auroc": dev_metrics["auroc"],
        "test_f1": test_metrics["f1"],
        "test_auroc": test_metrics["auroc"],
        "test_auprc": test_metrics["auprc"],
        "test_ci_f1": [test_metrics["ci_f1_lower"], test_metrics["ci_f1_upper"]],
        "test_ci_auroc": [test_metrics["ci_auroc_lower"], test_metrics["ci_auroc_upper"]],
    }


def run_e7():
    print("=" * 60)
    print("E7: Genome-Component Ablation")
    print("=" * 60)

    dev_pairs = load_pairs("dev")
    test_pairs = load_pairs("test")
    print(f"  dev={len(dev_pairs)}  test={len(test_pairs)}")

    ablation_results = {}
    for cond_name, config in ABLATION_CONDITIONS.items():
        ablation_results[cond_name] = run_ablation_condition(
            cond_name, config, dev_pairs, test_pairs
        )

    # Load Phase 3 baselines for full comparison table
    full_table = []
    phase3_labels = {
        "B01": "Token/TF-IDF",
        "B02": "AST",
        "B03": "CFG",
        "B04": "Dependency_Approx",
        "B05": "Embedding_Fallback",
        "B06": "Dynamic_Trace",
        "B07": "Static_SBG_all3",
        "B08": "Full_SBG_8dim",
    }
    for b, label in phase3_labels.items():
        p = PHASE3_DIR / b / "results_test.json"
        if p.exists():
            with open(p) as f:
                d = json.load(f)
            m = d.get("metrics", {})
            full_table.append({
                "condition": label,
                "source": f"Phase3_{b}",
                "test_f1": m.get("f1"),
                "test_auroc": m.get("auroc"),
                "test_auprc": m.get("auprc"),
                "test_ci_f1": [m.get("ci_f1_lower"), m.get("ci_f1_upper")],
                "test_ci_auroc": [m.get("ci_auroc_lower"), m.get("ci_auroc_upper")],
            })

    for cond_name, res in ablation_results.items():
        full_table.append({
            "condition": cond_name,
            "source": "Phase4_E7_ablation",
            "dimensions": res["dimensions"],
            "test_f1": res["test_f1"],
            "test_auroc": res["test_auroc"],
            "test_auprc": res["test_auprc"],
            "test_ci_f1": res["test_ci_f1"],
            "test_ci_auroc": res["test_ci_auroc"],
        })

    # Sort by AUROC
    full_table_sorted = sorted(
        [t for t in full_table if t["test_auroc"] is not None],
        key=lambda x: -x["test_auroc"]
    )

    # H6 verdict: does CONTROL_DATA_ERROR outperform any single dimension?
    auroc_values = {
        cond: ablation_results[cond]["test_auroc"]
        for cond in ablation_results
    }
    full_dim_auroc = auroc_values.get("CONTROL_DATA_ERROR", 0.0)
    single_dim_aurocs = {
        c: auroc_values[c] for c in ["CONTROL_only", "DATA_only", "ERROR_only"]
    }
    best_single = max(single_dim_aurocs.values()) if single_dim_aurocs else 0.0
    h6_supported = full_dim_auroc > best_single

    h6_verdict = {
        "status": "SUPPORTED" if h6_supported else "NOT_SUPPORTED",
        "full_dim_auroc": round(full_dim_auroc, 4),
        "best_single_dim_auroc": round(best_single, 4),
        "best_single_dim": max(single_dim_aurocs, key=single_dim_aurocs.get) if single_dim_aurocs else "N/A",
        "delta": round(full_dim_auroc - best_single, 4),
        "interpretation": (
            f"3-dim SBG AUROC={full_dim_auroc:.4f} vs best single-dim AUROC={best_single:.4f}. "
            f"H6 (multi-dim > single-dim) is {'SUPPORTED' if h6_supported else 'NOT SUPPORTED'}."
        ),
    }

    result = {
        "experiment": "E7",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hypothesis_addressed": ["H6"],
        "n_dev_pairs": len(dev_pairs),
        "n_test_pairs": len(test_pairs),
        "ablation_conditions": ablation_results,
        "full_ablation_table_sorted": full_table_sorted,
        "h6_verdict": h6_verdict,
        "finding": h6_verdict["interpretation"],
        "seed": SEED,
    }

    out_path = ARTIFACT_DIR / "results.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    abl_path = ARTIFACT_DIR / "ablation_table.json"
    with open(abl_path, "w") as f:
        json.dump(full_table_sorted, f, indent=2)

    print(f"\n=== E7 Ablation Table (sorted by AUROC) ===")
    for entry in full_table_sorted:
        dims = entry.get("dimensions", "—")
        print(f"  {entry['condition']}: F1={entry['test_f1']:.4f}  "
              f"AUROC={entry['test_auroc']:.4f}  dims={dims}")
    print(f"\n  H6: {h6_verdict['status']} — {h6_verdict['interpretation']}")
    print(f"\nResults saved to: {out_path}")
    return result


if __name__ == "__main__":
    run_e7()
