"""
experiments/final/fit_weights.py
================================
Weight fitting for the SBG distance (docs/current/PHASE2_PREREGISTRATION.md §4).

  M0  V5 with fixed weights 0.50 / 0.25 / 0.25 (the reference)
  M1  logistic regression on the three V5 components
  M2  logistic regression on nine execution features

Fitted on TRAIN valid pairs only, selected on DEV AUROC, and scored on TEST
exactly once. Pure Python (no numpy) so it runs anywhere the pipeline runs.

Two stages, run in order:
    python3 experiments/final/fit_weights.py fit     # train + dev; writes WEIGHT_FITTING.json
    python3 experiments/final/fit_weights.py score   # adds learned_m1/learned_m2 to the
                                                     # test per-pair file (no metrics)
    python3 experiments/final/fit_weights.py test    # completes WEIGHT_FITTING.json from
                                                     # MAIN_EVALUATION_v6test_output_free_v7.json
``fit`` refuses to run if any test-split scored file already contains learned
scores, and never opens a test-split file.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import math
import pathlib
import sys
from typing import Dict, List, Sequence

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sbg.statistics import auroc                                  # noqa: E402

ART = REPO_ROOT / "artifacts" / "final"
AUDIT = ART / "BENCHMARK_VALIDITY_AUDIT_V7.json"
OUT = ART / "WEIGHT_FITTING.json"
PROTOCOL = "output_free_v7"
FILES = {split: ART / f"pairs_v6{split}_{PROTOCOL}.jsonl" for split in ("train", "dev", "test")}

MODELS = {
    "M1": ["sbg_v3", "sbg_temporal", "sbg_state"],
    "M2": ["sbg_v3", "sbg_temporal", "sbg_state", "exception_fraction",
           "exception_component_v3", "exception_type_jaccard", "call_count",
           "n_functions", "coverage_size"],
}
L2 = 1.0
LEARNING_RATE = 0.5
ITERATIONS = 5000


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_rows(split: str) -> List[dict]:
    audit = {r["pair_id"]: r for r in json.loads(AUDIT.read_text())["pairs"]
             if r["split"] == split}
    rows = []
    for line in FILES[split].read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        verdict = audit.get(row["pair_id"])
        if not row["evaluated"] or verdict is None or verdict.get("status") != "ok":
            continue
        if row["label"] == 1 and verdict.get("observable") is not True:
            continue
        rows.append(row)
    return rows


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def fit_logistic(X: List[List[float]], y: Sequence[int]) -> dict:
    """Full-batch gradient descent on mean log-loss + L2 * ||w||^2 / n."""
    n, k = len(X), len(X[0])
    means = [sum(row[j] for row in X) / n for j in range(k)]
    stds = []
    for j in range(k):
        var = sum((row[j] - means[j]) ** 2 for row in X) / n
        stds.append(math.sqrt(var) if var > 0 else 1.0)
    Z = [[(row[j] - means[j]) / stds[j] for j in range(k)] for row in X]
    w, b = [0.0] * k, 0.0
    for _ in range(ITERATIONS):
        grad_w, grad_b = [0.0] * k, 0.0
        for zrow, label in zip(Z, y):
            err = _sigmoid(b + sum(wj * zj for wj, zj in zip(w, zrow))) - label
            grad_b += err
            for j in range(k):
                grad_w[j] += err * zrow[j]
        b -= LEARNING_RATE * grad_b / n
        w = [wj - LEARNING_RATE * (gj / n + 2.0 * L2 * wj / n) for wj, gj in zip(w, grad_w)]
    loss = 0.0
    for zrow, label in zip(Z, y):
        p = min(max(_sigmoid(b + sum(wj * zj for wj, zj in zip(w, zrow))), 1e-12), 1 - 1e-12)
        loss -= label * math.log(p) + (1 - label) * math.log(1 - p)
    return {"weights_standardised": [round(v, 9) for v in w], "bias": round(b, 9),
            "feature_means": [round(v, 12) for v in means],
            "feature_stds": [round(v, 12) for v in stds],
            "final_mean_logloss": round(loss / n, 9)}


def score(model: dict, features: List[str], scores: Dict[str, float]) -> float:
    """Logit of the fitted model; monotone in the probability, so AUROC-equivalent."""
    z = model["bias"]
    for j, name in enumerate(features):
        z += model["weights_standardised"][j] * (
            (scores[name] - model["feature_means"][j]) / model["feature_stds"][j])
    return round(z, 9)


def stage_fit() -> int:
    for line in FILES["test"].read_text().splitlines() if FILES["test"].exists() else []:
        if line.strip() and "learned_m1" in json.loads(line).get("scores", {}):
            raise SystemExit("test file already carries learned scores; refusing to refit")
    train, dev = valid_rows("train"), valid_rows("dev")
    y_train = [r["label"] for r in train]
    y_dev = [r["label"] for r in dev]
    fitted, table = {}, {}
    table["M0"] = {
        "features": ["sbg_v5 (0.50 v3 + 0.25 temporal + 0.25 state)"],
        "train_auroc": round(auroc([r["scores"]["sbg_v5"] for r in train], y_train), 6),
        "dev_auroc": round(auroc([r["scores"]["sbg_v5"] for r in dev], y_dev), 6),
    }
    for name, features in MODELS.items():
        model = fit_logistic([[r["scores"][f] for f in features] for r in train], y_train)
        fitted[name] = model
        table[name] = {
            "features": features,
            **model,
            "train_auroc": round(auroc([score(model, features, r["scores"]) for r in train],
                                       y_train), 6),
            "dev_auroc": round(auroc([score(model, features, r["scores"]) for r in dev],
                                     y_dev), 6),
        }
    # Selection on dev AUROC; ties go to the simpler model (M0, then M1).
    chosen = max(("M0", "M1", "M2"), key=lambda m: (table[m]["dev_auroc"],
                                                    -("M0", "M1", "M2").index(m)))
    payload = {
        "artifact": "WEIGHT_FITTING",
        "protocol": PROTOCOL,
        "preregistration": "docs/current/PHASE2_PREREGISTRATION.md section 4",
        "procedure": {
            "fit_on": "train split, statistically valid pairs (BENCHMARK_VALIDITY_AUDIT_V7)",
            "select_on": "dev split AUROC; ties -> simpler model (M0 < M1 < M2)",
            "optimiser": f"full-batch gradient descent, lr {LEARNING_RATE}, "
                         f"{ITERATIONS} iterations, zero initialisation",
            "loss": f"mean log-loss + {L2} * ||w||^2 / n_train (bias unpenalised)",
            "standardisation": "train mean / population std; std 0 -> 1",
            "score": "linear logit of the fitted model",
        },
        "inputs": {
            "train_pairs": str(FILES["train"].relative_to(REPO_ROOT)),
            "train_pairs_sha256": sha256(FILES["train"]),
            "dev_pairs": str(FILES["dev"].relative_to(REPO_ROOT)),
            "dev_pairs_sha256": sha256(FILES["dev"]),
            "n_train_valid": len(train), "n_train_programs": len({r["base_id"] for r in train}),
            "n_dev_valid": len(dev), "n_dev_programs": len({r["base_id"] for r in dev}),
        },
        "models": table,
        "chosen_on_dev": chosen,
        "fitted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "test": None,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    for m in ("M0", "M1", "M2"):
        print(f"{m}: train {table[m]['train_auroc']:.4f}  dev {table[m]['dev_auroc']:.4f}")
    print(f"chosen on dev: {chosen}")
    return 0


def stage_score() -> int:
    """Attach learned-model scores to the test per-pair file. No metric is computed."""
    payload = json.loads(OUT.read_text())
    if payload.get("test") is not None:
        raise SystemExit("test already scored once; refusing to rescore")
    rows = []
    for line in FILES["test"].read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["evaluated"]:
            for name, features in MODELS.items():
                model = payload["models"][name]
                row["scores"][f"learned_{name.lower()}"] = score(model, features, row["scores"])
        rows.append(row)
    FILES["test"].write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"added learned_m1, learned_m2 to {FILES['test'].name}")
    return 0


def stage_test() -> int:
    payload = json.loads(OUT.read_text())
    if payload.get("test") is not None:
        raise SystemExit("test already recorded; refusing to overwrite")
    main_eval = json.loads((ART / f"MAIN_EVALUATION_v6test_{PROTOCOL}.json").read_text())
    valid = main_eval["results"]["VALID"]
    predictors = valid["predictors"]
    mapping = {"M0": "sbg_v5", "M1": "learned_m1", "M2": "learned_m2"}
    chosen = payload["chosen_on_dev"]
    test = {"set": "VALID", "n": main_eval["set_sizes"]["VALID"],
            "models": {m: {k: predictors[p].get(k) for k in
                           ("auroc", "ci95_cluster_bootstrap", "permutation_p", "n_clusters")}
                       for m, p in mapping.items()}}
    if chosen == "M0":
        decision = ("M0 selected on dev; the claim uses the fixed V5 weights.")
        claim_model = "M0"
    else:
        key = f"sbg_v5_minus_{mapping[chosen]}"
        comp = valid["paired_comparisons"].get(key, {})
        holm = valid["paired_comparisons"].get("holm_bonferroni", {}).get(key, {})
        significant = bool(holm.get("reject_at_alpha"))
        test["chosen_vs_M0"] = {"comparison": key, "delta_sbg_v5_minus_chosen": comp.get("delta"),
                                "ci95": [comp.get("ci_lower"), comp.get("ci_upper")],
                                "p_two_sided": comp.get("p_two_sided"),
                                "p_holm": holm.get("p_adjusted"), "holm_reject": significant}
        claim_model = chosen if (significant and (comp.get("delta") or 0) < 0) else "M0"
        decision = (f"{chosen} selected on dev; its test difference from M0 is "
                    f"{'significant' if significant else 'not significant'} after Holm, "
                    f"so the claim uses {claim_model}.")
    test["decision"] = decision
    test["claim_model"] = claim_model
    test["scored_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    payload["test"] = test
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(decision)
    for m, v in test["models"].items():
        print(f"{m}: test AUROC {v['auroc']} CI {v['ci95_cluster_bootstrap']}")
    return 0


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "fit"
    raise SystemExit({"fit": stage_fit, "score": stage_score, "test": stage_test}[stage]())
