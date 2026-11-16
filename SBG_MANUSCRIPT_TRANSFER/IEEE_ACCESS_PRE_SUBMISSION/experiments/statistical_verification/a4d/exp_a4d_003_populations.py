#!/usr/bin/env python3
"""EXP-A4D-003  Independent re-derivation of labels / matched groups / base ids / edit sizes / variant-AST hashes from raw dataset metadata
(SBG/benchmark/datasets, read-only) and comparison with configs/populations/*.json (primary rows).  Also: matched-set structure, de-dup groups.

  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python exp_a4d_003_populations.py
"""
import collections
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a4dlib as L  # noqa: E402

EXP = "EXP-A4D-003"
RAW = L.PKG / "results" / "raw" / EXP
RAW.mkdir(parents=True, exist_ok=True)


def main():
    t0 = time.time()
    out = {}
    edit_cache, ast_cache = {}, {}
    for name in ("v10_test", "v9c_val", "v9c_dev", "v9c_train"):
        raw = L.raw_labels_groups(name)
        rows = L.load_pop(name)
        allrows = L.load_pop(name, primary=False)
        mism = {"missing_in_raw": [], "label": [], "group": [], "base_id": [], "base_path": [], "variant_path": [], "edit": []}
        for r in rows:
            m = raw.get(r["pair_id"])
            if m is None:
                mism["missing_in_raw"].append(r["pair_id"])
                continue
            if m[0] != r["label"]:
                mism["label"].append(r["pair_id"])
            if m[1] != r["group"]:
                mism["group"].append(r["pair_id"])
            if m[2] != r["base_id"]:
                mism["base_id"].append(r["pair_id"])
            if m[3] != r["base_path"]:
                mism["base_path"].append(r["pair_id"])
            if m[4] != r["variant_path"]:
                mism["variant_path"].append(r["pair_id"])
            key = (r["base_path"], r["variant_path"])
            if key not in edit_cache:
                edit_cache[key] = L.edit_size(*key)
            if float(edit_cache[key]) != float(r["edit"]):
                mism["edit"].append((r["pair_id"], edit_cache[key], r["edit"]))
        g = collections.defaultdict(list)
        for r in rows:
            g[r["group"]].append(r["label"])
        bad_sets = [k for k, v in g.items() if sorted(v) != [0, 1]]
        evalset = {r["pair_id"] for r in allrows if r.get("evaluated")}
        gg = collections.defaultdict(list)
        for pid in evalset:
            m = raw.get(pid)
            if m:
                gg[m[1]].append((pid, m[0]))
        derived = {pid for v in gg.values() if len(v) == 2 and sorted(l for _, l in v) == [0, 1] for pid, _ in v}
        have = {r["pair_id"] for r in rows}
        grp = collections.defaultdict(list)
        for r in rows:
            vp = r["variant_path"]
            if vp not in ast_cache:
                ast_cache[vp] = L.ast_hash(vp)
            grp[(r["base_id"], r["label"], ast_cache[vp])].append(r["pair_id"])
        mixed = collections.defaultdict(set)
        for r in rows:
            mixed[(r["base_id"], ast_cache[r["variant_path"]])].add(r["label"])
        dup_groups = {k: v for k, v in grp.items() if len(v) > 1}
        out[name] = {"n_primary": len(rows), "n_programs": len({r["base_id"] for r in rows}), "n_changed": sum(r["label"] for r in rows),
                     "mismatch_counts": {k: len(v) for k, v in mism.items()}, "mismatch_examples": {k: v[:5] for k, v in mism.items() if v},
                     "sets_not_1CH_1EQ": len(bad_sets), "n_sets": len(g), "primary_rederived_equal": derived == have,
                     "primary_only_in_population": sorted(have - derived)[:10], "primary_only_rederived": sorted(derived - have)[:10],
                     "dedup": {"n_dup_groups": len(dup_groups), "rows_in_dup_groups": sum(len(v) for v in dup_groups.values()),
                               "rows_after_dedup": len(rows) - sum(len(v) - 1 for v in dup_groups.values()),
                               "label_conflicting_ast": sum(1 for v in mixed.values() if len(v) > 1)}}
        print(name, json.dumps({k: out[name][k] for k in ("n_primary", "mismatch_counts", "sets_not_1CH_1EQ", "primary_rederived_equal", "dedup")}), flush=True)
    out["runtime_s"] = time.time() - t0
    (RAW / "population_rederivation.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
