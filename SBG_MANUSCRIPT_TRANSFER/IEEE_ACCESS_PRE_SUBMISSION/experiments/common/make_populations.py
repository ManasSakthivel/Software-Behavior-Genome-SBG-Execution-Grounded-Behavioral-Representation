#!/usr/bin/env python3
"""EXP-ORCH-005: freeze the evaluation populations used by every comparative / ablation experiment.

Uses the repository's own population code (evaluate_v9.load; evaluate_v10 row construction) read-only,
then writes plain JSON to configs/populations/.  Subagent 3 re-derives the same populations independently
from raw files and must reproduce these pair lists exactly.

  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python make_populations.py
"""
import collections
import hashlib
import json
import pathlib
import sys

PKG = pathlib.Path(__file__).resolve().parents[2]
REPO = PKG.parent / "SBG"
sys.path[:0] = [str(REPO), str(REPO / "experiments" / "final")]
import evaluate_v9 as e                                                     # noqa: E402
from edit_size_analysis import _edit_size                                   # noqa: E402
from static_baselines import token_multiset, ast_multiset, multiset_distance  # noqa: E402

OUT = PKG / "configs" / "populations"
OUT.mkdir(parents=True, exist_ok=True)
SCORE_KEYS = ["sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state", "exception_fraction", "call_count", "n_functions", "coverage_size"]


def meta_v10():
    return {m["pair_id"]: m for m in e.jl(REPO / "benchmark/datasets/v10_independent/pairs_test.jsonl")}


def meta_v9c(split):
    meta = {m["pair_id"]: m for m in e.jl(e.V9 / f"pairs_{split}.jsonl")}
    v8 = {m["pair_id"]: m for m in e.jl(e.V8 / f"pairs_{split}.jsonl")}
    for m in list(meta.values()):
        meta[m["matched_equivalent_pair_id"]] = v8[m["matched_equivalent_pair_id"]]
    return meta


def static(m, cache):
    for pth in (m["base_path"], m["variant_path"]):
        if pth not in cache:
            src = (REPO / pth).read_text()
            cache[pth] = (token_multiset(src), ast_multiset(src))
    return (multiset_distance(cache[m["base_path"]][0], cache[m["variant_path"]][0]),
            multiset_distance(cache[m["base_path"]][1], cache[m["variant_path"]][1]))


def build_v10():
    meta, scored = meta_v10(), {r["pair_id"]: r for r in e.jl(REPO / "artifacts/final/pairs_v10_test_v6exp.jsonl")}
    rows, cache = [], {}
    for pid, m in meta.items():
        r = scored[pid]
        if not r["evaluated"]:
            rows.append({"pair_id": pid, "evaluated": False, "base_id": m["base_id"], "failure": r.get("failure")})
            continue
        tok, ast_ = static(m, cache)
        rows.append({"pair_id": pid, "evaluated": True, "base_id": m["base_id"], "label": int(m["semantic_relation"] == "CHANGED"),
                     "group": m["pair_id"] if m["semantic_relation"] == "EQUIVALENT" else m["matched_pair_id"],
                     "transformation_type": m["transformation_type"], "sc_type": m.get("sc_type"), "sp_type": m.get("sp_type"),
                     "base_path": m["base_path"], "variant_path": m["variant_path"],
                     "edit": float(_edit_size(m["base_path"], m["variant_path"])),
                     "scores": {**{k: r["scores"][k] for k in SCORE_KEYS}, "sbg_v6": r["sbg_v6"], "sbg_state_v6": r["sbg_state_v6"],
                                "static_token": tok, "static_ast": ast_}})
    return rows


def build_v9c(split):
    rows = e.load("v9c", split)           # repo loader: valid flag (static audit), edit size, group
    meta, cache, out = meta_v9c(split), {}, []
    for r in rows:
        m = meta[r["pair_id"]]
        d = {"pair_id": r["pair_id"], "evaluated": bool(r["evaluated"]), "base_id": r["base_id"], "valid": bool(r["_valid"])}
        if r["evaluated"]:
            tok, ast_ = static(m, cache)
            d.update(label=r["label"], group=r["group"], transformation_type=m["transformation_type"], sc_type=m.get("sc_type"),
                     sp_type=m.get("sp_type"), base_path=m["base_path"], variant_path=m["variant_path"], edit=r["scores"]["edit"],
                     scores={**{k: r["scores"][k] for k in SCORE_KEYS}, "static_token": tok, "static_ast": ast_})
        out.append(d)
    return out


def matched(rows, need_valid):
    ok = collections.defaultdict(list)
    for r in rows:
        if r["evaluated"] and (r.get("valid", True) if need_valid else True):
            ok[r["group"]].append(r)
    return [x for g in ok.values() if len(g) == 2 and {y["label"] for y in g} == {0, 1} for x in g]


def main():
    summary = {}
    jobs = [("v10_test", build_v10(), False)] + [(f"v9c_{s}", build_v9c(s), True) for s in ("train", "dev", "val")]
    for name, rows, need_valid in jobs:
        pop = matched(rows, need_valid)
        ids = {p["pair_id"] for p in pop}
        for r in rows:
            r["in_primary_population"] = r["pair_id"] in ids
        (OUT / f"{name}.json").write_text(json.dumps({"name": name, "n_rows": len(rows), "n_primary": len(pop),
                                                     "n_programs": len({p["base_id"] for p in pop}), "rows": rows}))
        summary[name] = {"rows": len(rows), "primary_pairs": len(pop), "programs": len({p["base_id"] for p in pop}),
                         "changed": sum(p["label"] for p in pop),
                         "sha256": hashlib.sha256((OUT / f"{name}.json").read_bytes()).hexdigest()}
        print(name, summary[name])
    (OUT / "SUMMARY.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
