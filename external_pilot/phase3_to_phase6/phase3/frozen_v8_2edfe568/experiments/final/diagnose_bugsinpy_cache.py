"""Diagnostic (exploratory, not a replacement for BUGSINPY_output_free_v7.json).

Hypothesis: SBG traces depend on process-global interpreter state.  A module that
calls re.sub/re.compile traces ~5.9k events on a cold `re` cache and ~0.9k on a
warm one, so the distance between a file and itself is large (0.6-0.7) depending
on which extraction in the process ran first.  The committed BugsInPy driver
(`external_bugsinpy.py::stage_score`) scores all units in ONE process.

This script re-extracts every pair that was evaluated in the committed artifact,
calling re.purge() before every extraction so each is cold and order-independent,
and (a) measures self-distance of each fixed unit (two purged extractions),
(b) recomputes SBG V5 AUROC with unchanged protocol (output_free_v7), labels, pairs.
The committed artifact is not modified.   Output: raw/bugsinpy_purge_rescore.json

    PYTHONHASHSEED=0 python experiments/final/diagnose_bugsinpy_cache.py [--workers 4]
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

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
PAIRS = REPO / "artifacts/final/pairs_bugsinpy_output_free_v7.jsonl"
OUT = REPO / "artifacts/paper_evidence/raw/bugsinpy_purge_rescore.json"
PROTOCOL = "output_free_v7"


def worker(unit_base: str) -> None:
    import os
    from experiments.final import extraction as ex
    rows = [json.loads(l) for l in PAIRS.read_text().splitlines() if l.strip()]
    rows = [r for r in rows if r["evaluated"] and r["base_path"] == unit_base]

    def ext(rel):
        re.purge()
        return ex.extract_program(str(REPO / rel), {}, PROTOCOL)
    a1, a2 = ext(unit_base), ext(unit_base)
    self_d = ex.score_pair(a1, a2)["sbg_v5"] if a1.ok and a2.ok else None
    res = []
    for r in rows:
        v = ext(r["variant_path"])
        s = ex.score_pair(a1, v) if a1.ok and v.ok else None
        res.append({"pair_id": r["pair_id"], "label": r["label"], "bug_id": r["bug_id"],
                    "transformation": r["transformation"],
                    "committed_sbg_v5": r["scores"]["sbg_v5"],
                    "purged_sbg_v5": None if s is None else s["sbg_v5"],
                    "base_events": a1.stats.get("n_events"), "variant_events": v.stats.get("n_events")})
    print("@@" + json.dumps({"unit": unit_base, "self_distance_purged": self_d,
                             "imports_re": "import re" in (REPO / unit_base).read_text(),
                             "pairs": res}))


def main() -> None:
    from sbg.statistics import auroc
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--worker-unit")
    args = ap.parse_args()
    if args.worker_unit:
        worker(args.worker_unit)
        return
    rows = [json.loads(l) for l in PAIRS.read_text().splitlines() if l.strip()]
    units = sorted({r["base_path"] for r in rows if r["evaluated"]})

    def run(u):
        p = subprocess.run([sys.executable, __file__, "--worker-unit", u], capture_output=True, text=True,
                           cwd=str(REPO), timeout=1500)
        line = [l for l in p.stdout.splitlines() if l.startswith("@@")]
        return json.loads(line[0][2:]) if line else {"unit": u, "error": p.stderr[-300:], "pairs": []}
    with concurrent.futures.ThreadPoolExecutor(args.workers) as ex:
        results = list(ex.map(run, units))
    pairs = [p for r in results for p in r["pairs"] if p["purged_sbg_v5"] is not None]
    y = [p["label"] for p in pairs]

    def ci(key, fn):
        by = collections.defaultdict(list)
        for p in pairs:
            by[p["bug_id"]].append(p)
        ks = sorted(by)
        rng = random.Random(42)
        o = []
        for _ in range(2000):
            s = [x for k in (rng.choice(ks) for _ in ks) for x in by[k]]
            yy = [x["label"] for x in s]
            if 0 < sum(yy) < len(yy):
                o.append(fn(s))
        o.sort()
        return [round(o[int(.025 * len(o))], 6), round(o[int(.975 * len(o)) - 1], 6)]
    f_p = lambda s: auroc([x["purged_sbg_v5"] for x in s], [x["label"] for x in s])
    f_c = lambda s: auroc([x["committed_sbg_v5"] for x in s], [x["label"] for x in s])
    selfs = [r["self_distance_purged"] for r in results if r.get("self_distance_purged") is not None]
    out = {"purpose": "does process-global (re cache) state explain BugsInPy below-chance AUROC?",
           "protocol": PROTOCOL, "source_pairs": str(PAIRS.relative_to(REPO)),
           "n_units": len(results), "n_pairs": len(pairs), "n_pos": sum(y), "n_neg": len(y) - sum(y),
           "n_bugs": len({p["bug_id"] for p in pairs}),
           "committed_auroc_same_pairs": round(f_c(pairs), 6), "committed_ci": ci("c", f_c),
           "purged_auroc": round(f_p(pairs), 6), "purged_ci": ci("p", f_p),
           "self_distance_purged": {"n": len(selfs), "n_nonzero": sum(1 for s in selfs if s > 0),
                                    "max": max(selfs) if selfs else None},
           "n_pairs_score_changed_by_purge": sum(1 for p in pairs if abs(p["purged_sbg_v5"] - p["committed_sbg_v5"]) > 1e-9),
           "status": "EXPLORATORY diagnostic; committed artifact unchanged", "units": results}
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print({k: v for k, v in out.items() if k != "units"})


if __name__ == "__main__":
    main()
