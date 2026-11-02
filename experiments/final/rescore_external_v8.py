"""Corrected-harness re-score of the external real-bug corpora (EXPLORATORY).

Why this exists (see artifacts/paper_evidence/DIAGNOSTIC_EXTERNAL.json):
  1. `external_bugsinpy.py::stage_score` extracts every unit in ONE process with
     a shared `re` cache, so a module that calls re.sub/re.compile traces a
     different number of events depending on extraction order (cold vs warm).
  2. Under the v6/v7 entry policy an SP-2 rename of the entry function is
     scored as a behaviour change (100% of SP-2 pairs in both corpora).

This module does NOT edit the frozen drivers or the committed artifacts.  It
re-scores the same pairs (same labels, same files, same pairing) with
  * `re.purge()` before EVERY extraction, each base unit in its own subprocess
    (order independence), and
  * the structural, rename-invariant `output_free_v8` entry policy.
Results are written to NEW artifacts only.  Nothing here is tuned on any label.

    PYTHONHASHSEED=0 python experiments/final/rescore_external_v8.py [--workers 4]
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import json
import pathlib
import random
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
FINAL = REPO / "artifacts/final"
OUT_DIR = REPO / "artifacts/paper_evidence"
PROTOCOL = "output_free_v8"
SOURCES = {
    "bugsinpy": FINAL / "pairs_bugsinpy_output_free_v7.jsonl",
    "quixbugs_canonical": FINAL / "pairs_quixbugs_canonical_output_free_v7.jsonl",
}
UNIT_TIMEOUT_S = 1500


def purged_extract(rel_path: str, protocol: str = PROTOCOL):
    """Extract one program with a cold `re` cache and a fresh extraction cache."""
    from experiments.final import extraction as ex
    re.purge()
    return ex.extract_program(str(REPO / rel_path), {}, protocol)


def score_rows(rows: List[dict], protocol: str = PROTOCOL) -> List[dict]:
    """Score `rows` (all sharing one base program); every extraction is cold."""
    from experiments.final import extraction as ex
    base_path = rows[0]["base_path"]
    base = purged_extract(base_path, protocol)
    base_again = purged_extract(base_path, protocol)
    self_d = ex.score_pair(base, base_again)
    out = []
    for r in rows:
        var = purged_extract(r["variant_path"], protocol)
        s = ex.score_pair(base, var) if base.ok and var.ok else None
        out.append({
            "pair_id": r["pair_id"], "label": r["label"], "cluster": r["cluster"],
            "transformation": r["transformation"], "base_path": base_path,
            "variant_path": r["variant_path"],
            "evaluated": s is not None,
            "failure_kind": None if s is not None else (base.failure_kind if not base.ok else var.failure_kind),
            "committed_sbg_v5": r.get("committed_sbg_v5"),
            "sbg_v5": None if s is None else s["sbg_v5"],
            "scores": None if s is None else {k: s[k] for k in
                                              ("sbg_v5", "sbg_state", "sbg_temporal", "sbg_v3",
                                               "exception_fraction", "call_count", "coverage_size")
                                              if k in s},
            "base_entry": base.entry_discovery, "variant_entry": var.entry_discovery,
            "base_entry_fn": base.entry_function, "variant_entry_fn": var.entry_function,
            "base_self_distance_v5": None if self_d is None else self_d["sbg_v5"],
        })
    return out


def load_source(name: str) -> List[dict]:
    raw = [json.loads(l) for l in SOURCES[name].read_text().splitlines() if l.strip()]
    rows = []
    for r in raw:
        if name == "bugsinpy":
            if not r["evaluated"]:
                continue
            rows.append({"pair_id": r["pair_id"], "label": r["label"], "cluster": r["bug_id"],
                         "transformation": r["transformation"], "base_path": r["base_path"],
                         "variant_path": r["variant_path"],
                         "committed_sbg_v5": r["scores"]["sbg_v5"]})
        else:
            rows.append({"pair_id": r["pair_id"], "label": r["label"], "cluster": r["base_id"],
                         "transformation": ("real_bug" if r["pair_kind"] == "real_bug"
                                            else r["pair_kind"].replace("sp_negative:", "")),
                         "base_path": r["base_path"], "variant_path": r["variant_path"],
                         "committed_sbg_v5": r["scores"]["sbg_v5"] if r["evaluated"] else None})
    return rows


def worker(name: str, base_path: str) -> None:
    rows = [r for r in load_source(name) if r["base_path"] == base_path]
    print("@@" + json.dumps(score_rows(rows)))


def run_corpus(name: str, workers: int) -> List[dict]:
    rows = load_source(name)
    bases = sorted({r["base_path"] for r in rows})

    def run(b: str) -> List[dict]:
        p = subprocess.run([sys.executable, __file__, "--worker", name, "--base", b],
                           capture_output=True, text=True, cwd=str(REPO), timeout=UNIT_TIMEOUT_S)
        line = [l for l in p.stdout.splitlines() if l.startswith("@@")]
        if line:
            return json.loads(line[0][2:])
        return [{"pair_id": r["pair_id"], "label": r["label"], "cluster": r["cluster"],
                 "transformation": r["transformation"], "base_path": b,
                 "variant_path": r["variant_path"], "evaluated": False,
                 "failure_kind": "harness_error", "committed_sbg_v5": r["committed_sbg_v5"],
                 "sbg_v5": None, "scores": None}
                for r in rows if r["base_path"] == b]
    with concurrent.futures.ThreadPoolExecutor(workers) as pool:
        out = [x for chunk in pool.map(run, bases) for x in chunk]
    return out


def _ci(rows: List[dict], fn, n_boot: int = 2000, seed: int = 42) -> List[float]:
    by = collections.defaultdict(list)
    for r in rows:
        by[r["cluster"]].append(r)
    keys = sorted(by)
    rng = random.Random(seed)
    vals = []
    for _ in range(n_boot):
        s = [x for k in (rng.choice(keys) for _ in keys) for x in by[k]]
        if 0 < sum(x["label"] for x in s) < len(s):
            vals.append(fn(s))
    vals.sort()
    return [round(vals[int(.025 * len(vals))], 4), round(vals[int(.975 * len(vals)) - 1], 4)]


def summarise(name: str, rows: List[dict]) -> Dict[str, Any]:
    from sbg.statistics import auroc
    ev = [r for r in rows if r["evaluated"]]

    def block(sub: List[dict], key: str = "sbg_v5") -> Optional[Dict[str, Any]]:
        if not sub or not (0 < sum(r["label"] for r in sub) < len(sub)):
            return None
        f = lambda s: auroc([x["scores"][key] if key != "committed" else x["committed_sbg_v5"]
                             for x in s], [x["label"] for x in s])
        return {"n_pairs": len(sub), "n_pos": sum(r["label"] for r in sub),
                "n_neg": len(sub) - sum(r["label"] for r in sub),
                "n_clusters": len({r["cluster"] for r in sub}),
                "auroc": round(f(sub), 4), "ci95_cluster_bootstrap": _ci(sub, f)}
    nosp2 = [r for r in ev if r["transformation"] != "SP-2"]
    comparable = [r for r in ev if r["committed_sbg_v5"] is not None]
    sp2 = [r for r in ev if r["transformation"] == "SP-2"]
    sp_scores = collections.defaultdict(list)
    for r in ev:
        if r["label"] == 0:
            sp_scores[r["transformation"]].append(r["sbg_v5"])
    self_d = {}
    for r in ev:
        self_d[r["base_path"]] = r.get("base_self_distance_v5")
    selfs = [v for v in self_d.values() if v is not None]
    return {
        "corpus": name, "protocol": PROTOCOL,
        "n_pairs_total": len(rows), "n_evaluated": len(ev),
        "unevaluated": dict(collections.Counter(r["failure_kind"] for r in rows if not r["evaluated"])),
        "rescored_all": block(ev),
        "rescored_excluding_SP2": block(nosp2),
        "committed_v7_same_pairs": block(comparable, "committed") if all(
            r["scores"] is not None for r in comparable) else None,
        "mean_sbg_v5_by_negative_transformation": {k: round(sum(v) / len(v), 4)
                                                   for k, v in sorted(sp_scores.items())},
        "sp2_pairs": len(sp2),
        "sp2_pairs_with_nonzero_sbg_v5": sum(1 for r in sp2 if r["sbg_v5"] > 0),
        "sp2_pairs_with_entry_renamed": sum(1 for r in sp2 if r.get("base_entry_fn") != r.get("variant_entry_fn")),
        "self_distance_v5": {"n_bases": len(selfs), "n_nonzero": sum(1 for s in selfs if s > 0),
                             "max": max(selfs) if selfs else None},
        "real_bug_pairs_sbg_v5_exactly_zero": sum(1 for r in ev if r["label"] == 1 and r["sbg_v5"] == 0),
        "real_bug_pairs_evaluated": sum(1 for r in ev if r["label"] == 1),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--worker")
    ap.add_argument("--base")
    args = ap.parse_args()
    if args.worker:
        worker(args.worker, args.base)
        return
    result: Dict[str, Any] = {
        "artifact": "EXTERNAL_RESCORE_V8",
        "status": "EXPLORATORY: corrected harness (re.purge per extraction, structural rename-invariant "
                  "entry policy), same pairs/labels as the committed v7 artifacts; no tuning; "
                  "committed artifacts unchanged",
        "protocol": PROTOCOL, "sources": {}, "corpora": {}}
    pair_dump: Dict[str, List[dict]] = {}
    for name in SOURCES:
        rows = run_corpus(name, args.workers)
        pair_dump[name] = rows
        result["corpora"][name] = summarise(name, rows)
        result["sources"][name] = str(SOURCES[name].relative_to(REPO))
        print(name, json.dumps({k: v for k, v in result["corpora"][name].items()}, indent=1), flush=True)
    (OUT_DIR / "raw").mkdir(exist_ok=True)
    (OUT_DIR / "raw" / "external_rescore_v8_pairs.json").write_text(json.dumps(pair_dump, indent=1) + "\n")
    (OUT_DIR / "EXTERNAL_RESCORE_V8.json").write_text(json.dumps(result, indent=1) + "\n")


if __name__ == "__main__":
    main()
