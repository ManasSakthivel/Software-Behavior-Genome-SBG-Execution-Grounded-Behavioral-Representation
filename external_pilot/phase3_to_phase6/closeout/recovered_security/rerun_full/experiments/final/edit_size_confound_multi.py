"""Edit-size confound + weight-model check for any scored pair file (dev/train only).

Reuses edit_size_analysis._edit_size (canonical AST-line diff). Reports forward and
reversed edit-size AUROC, SBG V5 AUROC, a cluster-bootstrap CI (by base program), and
the fitted M0/M1/M2 AUROCs from WEIGHT_FITTING.json when the pair file carries the
needed scores. Refuses test-split pair files.

    python3 experiments/final/edit_size_confound_multi.py \
        --pairs artifacts/final/pairs_v8devrescore_output_free_v8.jsonl \
        --dataset-dir benchmark/datasets/v8 --out artifacts/paper_evidence/raw/x.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from experiments.final.edit_size_analysis import _edit_size          # noqa: E402
from experiments.final.fit_weights import MODELS, score as lin_score  # noqa: E402
from sbg.statistics import auroc, cluster_bootstrap_ci                # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--dataset-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--weights", default=str(REPO / "artifacts/final/WEIGHT_FITTING.json"))
    a = ap.parse_args()
    pairs_path = pathlib.Path(a.pairs)
    rows = [json.loads(l) for l in pairs_path.read_text().splitlines() if l.strip()]
    if any(r["split"] == "test" for r in rows):
        raise SystemExit("refusing: test-split pair file")
    meta = {}
    for sp in ("train", "dev", "val"):
        p = pathlib.Path(a.dataset_dir) / f"pairs_{sp}.jsonl"
        if p.exists():
            for l in p.read_text().splitlines():
                if l.strip():
                    m = json.loads(l)
                    meta[m["pair_id"]] = m
    ev = [r for r in rows if r["evaluated"]]
    size = [float(_edit_size(meta[r["pair_id"]]["base_path"], meta[r["pair_id"]]["variant_path"]))
            for r in ev]
    y = [r["label"] for r in ev]
    cl = [r["base_id"] for r in ev]
    sbg = [r["scores"]["sbg_v5"] for r in ev]
    out = {
        "pairs_file": a.pairs, "dataset_dir": a.dataset_dir,
        "n_evaluated": len(ev), "n_changed": sum(y), "n_equivalent": len(y) - sum(y),
        "n_programs": len(set(cl)),
        "edit_size_forward_auroc": round(auroc(size, y), 6),
        "edit_size_reversed_auroc": round(1 - auroc(size, y), 6),
        "edit_size_forward_ci95": cluster_bootstrap_ci(size, y, cl, n_bootstrap=2000, seed=42),
        "sbg_v5_auroc": round(auroc(sbg, y), 6),
        "sbg_v5_ci95": cluster_bootstrap_ci(sbg, y, cl, n_bootstrap=2000, seed=42),
        "edit_size_stats": {
            "mean_changed": round(sum(s for s, l in zip(size, y) if l) / max(1, sum(y)), 3),
            "mean_equivalent": round(sum(s for s, l in zip(size, y) if not l)
                                     / max(1, len(y) - sum(y)), 3),
        },
    }
    w = json.loads(pathlib.Path(a.weights).read_text())
    for name, feats in MODELS.items():
        if all(f in ev[0]["scores"] for f in feats):
            sc = [lin_score(w["models"][name], feats, r["scores"]) for r in ev]
            out[f"{name}_auroc_with_train_fit_weights"] = round(auroc(sc, y), 6)
            out[f"{name}_ci95"] = cluster_bootstrap_ci(sc, y, cl, n_bootstrap=2000, seed=42)
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
