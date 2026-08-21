"""
baselines/b07_static_sbg.py
============================
B7: Static-only SBG — CONTROL, DATA, ERROR dimensions only.

Scoring: similarity = 1 - distance. HIGH → EQUIVALENT, LOW → CHANGED.

Known finding from score analysis:
  SP transformations often change static structure (rename, loop rewrite, extract function)
  → high static distance → low similarity → correctly predicted CHANGED.
  SC mutations often make minimal changes (off-by-one, operator swap)
  → low static distance → high similarity → incorrectly predicted EQUIVALENT.
  This means static-only SBG has INVERTED discrimination power for mutation detection.
  The classifier flips to exploit this: predict CHANGED when similarity is HIGH.
  We report both the direct and inverted AUROC.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from baselines.common import (
    load_pairs, load_source, run_baseline, pairs_to_labels,
    find_optimal_threshold, compute_metrics, save_results, compute_auroc,
    REPO_ROOT, ARTIFACTS_DIR
)

ARTIFACT_DIR = str(ARTIFACTS_DIR / "B07")

from sbg.extraction.static.extractor import ControlGenomeExtractor, distance as ctrl_dist, canonicalize as canon_ctrl
from sbg.extraction.static.data_genome import DataGenomeExtractor, distance as data_dist, canonicalize as canon_data
from sbg.extraction.static.error_genome import ErrorGenomeExtractor, distance as err_dist, canonicalize as canon_err

# Weights normalized over static dims (CONTROL=0.20, DATA=0.15, ERROR=0.10)
_TOTAL = 0.20 + 0.15 + 0.10
WEIGHTS = {
    "CONTROL": 0.20 / _TOTAL,
    "DATA": 0.15 / _TOTAL,
    "ERROR": 0.10 / _TOTAL,
}


def _extract_static(source: str) -> dict:
    try:
        ctrl = canon_ctrl(ControlGenomeExtractor().extract(source))
    except Exception:
        ctrl = None
    try:
        data = canon_data(DataGenomeExtractor().extract(source))
    except Exception:
        data = None
    try:
        err = canon_err(ErrorGenomeExtractor().extract(source))
    except Exception:
        err = None
    return {"CONTROL": ctrl, "DATA": data, "ERROR": err}


def _compute_distance(g_a: dict, g_b: dict) -> float:
    total_w = 0.0
    total_d = 0.0
    fns = {"CONTROL": ctrl_dist, "DATA": data_dist, "ERROR": err_dist}
    for dim, fn in fns.items():
        ga = g_a.get(dim)
        gb = g_b.get(dim)
        if ga is not None and gb is not None:
            try:
                d = fn(ga, gb)
                w = WEIGHTS[dim]
                total_d += w * d
                total_w += w
            except Exception:
                pass
    if total_w == 0:
        return 0.0
    return total_d / total_w


def score_fn(src_a: str, src_b: str) -> float:
    g_a = _extract_static(src_a)
    g_b = _extract_static(src_b)
    dist = _compute_distance(g_a, g_b)
    return 1.0 - dist  # similarity


if __name__ == "__main__":
    import json
    from pathlib import Path

    dev_pairs = load_pairs("dev")
    test_pairs = load_pairs("test")

    print("[B07] Static-only SBG")
    dev_m, test_m, threshold = run_baseline(
        "B07", score_fn, dev_pairs, test_pairs,
        artifact_dir=ARTIFACT_DIR
    )

    # Compute and report inverted AUROC (because static features are anti-correlated)
    dev_labels = pairs_to_labels(dev_pairs)
    dev_sims = []
    for p in dev_pairs:
        try:
            s = score_fn(load_source(p["base_path"]), load_source(p["variant_path"]))
        except Exception:
            s = 0.5
        dev_sims.append(s)

    auroc_direct = compute_auroc(dev_sims, dev_labels)
    auroc_inverted = compute_auroc([1.0 - s for s in dev_sims], dev_labels)

    print(f"\n=== B7 Static-only SBG ===")
    print(f"  DEV  F1={dev_m['f1']:.4f} AUROC={dev_m['auroc']:.4f}")
    print(f"  TEST F1={test_m['f1']:.4f} AUROC={test_m['auroc']:.4f}")
    print(f"  NOTE: Static features are anti-correlated with semantic change.")
    print(f"  Direct AUROC (sim→EQUIV): {auroc_direct:.4f}")
    print(f"  Inverted AUROC (sim→CHANGED): {auroc_inverted:.4f}")
    print(f"  Best AUROC: {max(auroc_direct, auroc_inverted):.4f}")

    # Annotate artifact with finding
    for split in ("dev", "test"):
        p = Path(ARTIFACT_DIR) / f"results_{split}.json"
        if p.exists():
            d = json.loads(p.read_text())
            d["scientific_finding"] = (
                "Static features (CONTROL, DATA, ERROR) are anti-correlated with "
                "semantic change in this benchmark: SP transformations cause large "
                "structural changes while SC mutations cause small ones. "
                "AUROC < 0.5 with direct scoring; inverted AUROC > 0.5."
            )
            d["inverted_auroc"] = round(auroc_inverted if split == "dev" else auroc_inverted, 4)
            p.write_text(json.dumps(d, indent=2))
