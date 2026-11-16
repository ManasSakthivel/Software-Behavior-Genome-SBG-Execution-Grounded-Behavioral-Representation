"""Builds artifacts/paper_evidence/DIAGNOSTIC_V6DEV_REPRO.json (dev split only).

Compares the FROZEN v6 dev scoring (artifacts/final/pairs_v6dev_output_free_v7.jsonl, never modified)
with re-scores of the same dataset/protocol made from clean git worktrees at different commits and
different PYTHONHASHSEED values.  Re-scores are NOT written into artifacts/final.

Procedure used (one run = ~90 s):

    git worktree add /tmp/wt_<name> <commit> --detach
    cd /tmp/wt_<name> && PYTHONHASHSEED=<s> $PY experiments/final/run_main_evaluation.py \
        --split dev --protocol output_free_v7 --dataset-dir benchmark/datasets/v6 \
        --tag v6dev --out-dir /tmp/bis_<name>_h<s>

    python3 experiments/final/build_v6dev_repro_diagnostic.py RUN=/tmp/bis_<name>_h<s>/pairs_v6dev_output_free_v7.jsonl ...

Only execution-derived score keys are compared (static_* are appended by a separate script).
Commits: ad7b655 = commit that introduced the frozen dev artifact; d9d6380 = first commit with the
input-aliasing fix; b54ea99 = HEAD at start of this session (adds tracer RecursionError early-stop).
"adc" = ad7b655 plus ONLY the one-line copy.deepcopy fix in protocol.synthesise_inputs.
"""
from __future__ import annotations

import collections
import hashlib
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from sbg.statistics import auroc                                                  # noqa: E402

FROZEN = REPO / "artifacts/final/pairs_v6dev_output_free_v7.jsonl"
AUDIT = REPO / "artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7.json"
OUT = REPO / "artifacts/paper_evidence/DIAGNOSTIC_V6DEV_REPRO.json"
STATIC = ("static_ast", "static_token")


def load(p):
    return {json.loads(l)["pair_id"]: json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()}


def strip(d):
    return {k: v for k, v in d.items() if k not in STATIC}


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def main(args):
    audit = {r["pair_id"]: r for r in json.loads(AUDIT.read_text())["pairs"] if r["split"] == "dev"}

    def valid(r):
        v = audit.get(r["pair_id"])
        return r["evaluated"] and v and v.get("status") == "ok" and (r["label"] == 0 or v.get("observable") is True)

    def auc(rows):
        rows = [r for r in rows.values() if valid(r)]
        return round(auroc([r["scores"]["sbg_v5"] for r in rows], [r["label"] for r in rows]), 6), len(rows)

    fz = load(FROZEN)
    out = {"purpose": "isolate why re-scoring v6 dev differs from the frozen artifact on 46/345 pairs",
           "split": "dev only", "frozen_artifact": {"path": str(FROZEN.relative_to(REPO)), "sha256": sha(FROZEN),
                                                    "sbg_v5_valid_auroc_and_n": auc(fz)},
           "comparisons": {}}
    for arg in args:
        name, path = arg.split("=", 1)
        rr = load(path)
        assert rr.keys() == fz.keys()
        status = [k for k in fz if fz[k]["evaluated"] != rr[k]["evaluated"]]
        diff = [k for k in fz if fz[k]["evaluated"] and rr[k]["evaluated"] and strip(fz[k]["scores"]) != strip(rr[k]["scores"])]
        out["comparisons"][name] = {
            "rescore_file_sha256": sha(path),
            "n_evaluated_status_differs": len(status),
            "n_score_differs_among_commonly_evaluated": len(diff),
            "differs_by_base_program": dict(collections.Counter(fz[k]["base_id"] for k in diff)),
            "max_abs_delta_sbg_v5": round(max([abs(fz[k]["scores"]["sbg_v5"] - rr[k]["scores"]["sbg_v5"]) for k in diff] or [0]), 6),
            "sbg_v5_valid_auroc_and_n": auc(rr)}
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
