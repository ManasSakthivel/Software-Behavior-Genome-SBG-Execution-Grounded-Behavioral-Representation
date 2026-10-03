"""
experiments/final/derive_threshold.py
=====================================
Derives and freezes the SBG V5 detection threshold tau* under PROTOCOL
output_free_v7 (docs/current/PHASE2_PREREGISTRATION.md §3).

Data   dev split of benchmark/datasets/v6, statistically valid pairs only
       (BENCHMARK_VALIDITY_AUDIT_V7). This script opens no test-split or
       external file; it refuses any input path that does not name the dev split.
Rule   maximise Youden's J = TPR - FPR over the midpoints between consecutive
       sorted unique SBG V5 distances; a pair is "detected" iff d > tau; ties go
       to the smaller threshold.
Output artifacts/final/THRESHOLD_FROZEN.json  (written last, only when final)
       artifacts/final/freeze_threshold.json  (append-only freeze log)

A cluster bootstrap over dev programs re-derives tau* on resampled programs.
It is a stability diagnostic and is never used to choose tau*.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import pathlib
import random
import sys
from typing import List, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ART = REPO_ROOT / "artifacts" / "final"
DEV_PAIRS = ART / "pairs_v6dev_output_free_v7.jsonl"
DEV_DATASET = REPO_ROOT / "benchmark" / "datasets" / "v6" / "pairs_dev.jsonl"
AUDIT = ART / "BENCHMARK_VALIDITY_AUDIT_V7.json"
PREDICTOR = "sbg_v5"
SEED = 42
N_BOOTSTRAP = 2000


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_dev_rows() -> List[dict]:
    for path in (DEV_PAIRS, DEV_DATASET):
        if "dev" not in path.name:
            raise SystemExit(f"refusing non-dev input {path}")
    audit = {r["pair_id"]: r for r in json.loads(AUDIT.read_text())["pairs"]
             if r["split"] == "dev"}
    rows = []
    for line in DEV_PAIRS.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["split"] != "dev":
            raise SystemExit("non-dev row in dev pair file")
        if not row["evaluated"]:
            continue
        verdict = audit.get(row["pair_id"])
        if verdict is None or verdict.get("status") != "ok":
            continue
        if row["label"] == 1 and verdict.get("observable") is not True:
            continue
        rows.append(row)
    return rows


def youden(points: List[Tuple[float, int]]) -> Tuple[float, float, float, float]:
    """(tau, J, TPR, FPR) maximising J; ties -> smaller tau."""
    n_pos = sum(label for _, label in points)
    n_neg = len(points) - n_pos
    pos, neg = {}, {}
    for d, y in points:
        bucket = pos if y == 1 else neg
        bucket[d] = bucket.get(d, 0) + 1
    values = sorted(set(pos) | set(neg))
    if len(values) < 2 or n_pos == 0 or n_neg == 0:
        return (values[0] if values else 0.0), 0.0, 0.0, 0.0
    # Suffix counts: tp[k] = positives with d >= values[k].
    tp_suffix, fp_suffix = [0] * (len(values) + 1), [0] * (len(values) + 1)
    for k in range(len(values) - 1, -1, -1):
        tp_suffix[k] = tp_suffix[k + 1] + pos.get(values[k], 0)
        fp_suffix[k] = fp_suffix[k + 1] + neg.get(values[k], 0)
    best = None
    for k in range(len(values) - 1):             # ascending: first max is the smallest
        tau = (values[k] + values[k + 1]) / 2.0  # d > tau  <=>  d >= values[k + 1]
        tpr, fpr = tp_suffix[k + 1] / n_pos, fp_suffix[k + 1] / n_neg
        j = tpr - fpr
        if best is None or j > best[1] + 1e-12:
            best = (tau, j, tpr, fpr)
    return best


def main() -> int:
    rows = valid_dev_rows()
    points = [(r["scores"][PREDICTOR], r["label"]) for r in rows]
    tau, j, tpr, fpr = youden(points)

    by_program = {}
    for r in rows:
        by_program.setdefault(r["base_id"], []).append((r["scores"][PREDICTOR], r["label"]))
    programs = sorted(by_program)
    rng = random.Random(SEED)
    boot = []
    for _ in range(N_BOOTSTRAP):
        sample = [p for _ in programs for p in by_program[rng.choice(programs)]]
        if 0 < sum(y for _, y in sample) < len(sample):
            boot.append(youden(sample)[0])
    boot.sort()

    def pct(q: float) -> float:
        return round(boot[min(len(boot) - 1, int(q * len(boot)))], 6)

    payload = {
        "artifact": "THRESHOLD_FROZEN",
        "protocol": "output_free_v7",
        "predictor": PREDICTOR,
        "tau_star": round(tau, 6),
        "rule": ("maximise Youden J = TPR - FPR over midpoints of consecutive sorted "
                 "unique distances; detected iff d > tau; ties -> smaller tau"),
        "preregistration": "docs/current/PHASE2_PREREGISTRATION.md section 3",
        "derived_on": {
            "split": "dev",
            "dataset_pair_file": str(DEV_DATASET.relative_to(REPO_ROOT)),
            "dataset_pair_file_sha256": sha256(DEV_DATASET),
            "scored_pair_file": str(DEV_PAIRS.relative_to(REPO_ROOT)),
            "scored_pair_file_sha256": sha256(DEV_PAIRS),
            "validity_audit": str(AUDIT.relative_to(REPO_ROOT)),
            "n_valid_pairs": len(points),
            "n_changed": sum(y for _, y in points),
            "n_equivalent": sum(1 for _, y in points if y == 0),
            "n_programs": len(programs),
            "programs": programs,
        },
        "dev_operating_point": {"youden_j": round(j, 6), "tpr": round(tpr, 6),
                                "fpr": round(fpr, 6)},
        "stability_diagnostic_not_used_for_selection": {
            "method": f"cluster bootstrap over dev programs, {N_BOOTSTRAP} resamples, seed {SEED}",
            "n_nondegenerate": len(boot),
            "tau_p2_5": pct(0.025), "tau_median": pct(0.5), "tau_p97_5": pct(0.975),
        },
        "previous_value": {"tau_star": 0.08, "derived_under": "published protocol",
                           "status": "superseded for output_free_v7 results"},
        "reads_no_test_or_external_labels": True,
        "frozen_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
    }
    log_path = ART / "freeze_threshold.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {"records": []}
    log["records"].append({k: payload[k] for k in ("tau_star", "protocol", "frozen_at")}
                          | {"dev_scored_pair_file_sha256":
                             payload["derived_on"]["scored_pair_file_sha256"]})
    log_path.write_text(json.dumps(log, indent=2) + "\n")
    # Written last: other workstreams treat its appearance as "v7 is final".
    (ART / "THRESHOLD_FROZEN.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(f"tau* = {payload['tau_star']}  J={j:.4f} TPR={tpr:.4f} FPR={fpr:.4f} "
          f"n={len(points)} programs={len(programs)}  bootstrap 95%: "
          f"[{pct(0.025)}, {pct(0.975)}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
