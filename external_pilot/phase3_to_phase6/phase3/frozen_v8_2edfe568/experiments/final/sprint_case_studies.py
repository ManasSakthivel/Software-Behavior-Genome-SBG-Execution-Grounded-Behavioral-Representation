#!/usr/bin/env python3
"""FINAL SPRINT, Part 3: trace-backed representation case studies (V10, frozen scores; READ-ONLY).

  PYTHONHASHSEED=0 python experiments/final/sprint_case_studies.py select   # deterministic selection -> artifacts/paper_evidence/REPRESENTATION_CASES_selection.json
  PYTHONHASHSEED=0 python experiments/final/sprint_case_studies.py trace    # re-traces ONLY the selected pairs with the frozen extractor, asserts scores == frozen,
                                                                            # dumps source diffs + state-transition evidence -> REPRESENTATION_CASES_traces.json

Selection rules (fixed in code before any individual case was inspected; ties broken by sorted pair_id):
  C1 correct detection          : matched sets where sbg_v5 ranks CHANGED>EQUIVALENT AND M_EX ranks it wrong.  MEDIAN set by CHANGED sbg_v5.
  C2 correct equivalence        : EQUIVALENT pairs with edit>=11, sbg_v5==0 and all three execution statistics==0.  MEDIAN by edit size.
  C3 failure to detect          : CHANGED pairs with sbg_v5==0 and all execution statistics==0; first by pair_id in the most frequent SC family.
  C4a/C4b SBG vs combined model : sets where adding SBG to M_EX flips the set outcome 1.0->0.0 (hurts) / 0.0->1.0 (helps).  MEDIAN of each by CHANGED sbg_v5.
"""
from __future__ import annotations

import ast
import collections
import difflib
import json
import re as _re
import sys

import sprint_common as C

OUTSEL = C.OUT / "REPRESENTATION_CASES_selection.json"
OUTTR = C.OUT / "REPRESENTATION_CASES_traces.json"
SCORE_KEYS = ("sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state", "sbg_v6", "exception_fraction", "call_count", "coverage_size", "edit", "M_E", "M_EX", "M_EX+V5")


def med(xs, key):
    xs = sorted(xs, key=key)
    return xs[(len(xs) - 1) // 2] if xs else None


def select():
    pop, _ = C.load_v10_population()
    sets = C.matched_sets(pop)
    ex0 = lambda r: all(r["scores"][k] == 0 for k in ("exception_fraction", "call_count", "coverage_size"))   # noqa: E731
    sel = {}
    pool = [(g, s) for g, s in sorted(sets.items()) if C.set_outcome(s, "sbg_v5") == 1.0 and C.set_outcome(s, "M_EX") == 0.0]
    g, s = med(pool, lambda t: (t[1][1]["scores"]["sbg_v5"], t[0]))
    sel["C1_correct_detection"] = {"rule_pool_size": len(pool), "group": g, "changed": s[1]["pair_id"], "equivalent": s[0]["pair_id"]}
    pool = [r for r in sorted(pop, key=lambda r: r["pair_id"]) if r["label"] == 0 and r["_edit"] >= 11 and r["scores"]["sbg_v5"] == 0 and ex0(r)]
    r = med(pool, lambda r: (r["_edit"], r["pair_id"]))
    sel["C2_correct_equivalence"] = {"rule_pool_size": len(pool), "equivalent": r["pair_id"], "changed": sets[r["group"]][1]["pair_id"]}
    pool = [r for r in sorted(pop, key=lambda r: r["pair_id"]) if r["label"] == 1 and r["scores"]["sbg_v5"] == 0 and ex0(r)]
    fam = collections.Counter(r["sc_type"] for r in pool)
    top = sorted(fam.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    r = next(r for r in pool if r["sc_type"] == top)
    sel["C3_failure_to_detect"] = {"rule_pool_size": len(pool), "pool_by_sc_family": dict(fam), "selected_family": top, "changed": r["pair_id"], "equivalent": sets[r["group"]][0]["pair_id"]}
    for tag, a, b in (("C4a_adding_sbg_hurts", 1.0, 0.0), ("C4b_adding_sbg_helps", 0.0, 1.0)):
        pool = [(g, s) for g, s in sorted(sets.items()) if C.set_outcome(s, "M_EX") == a and C.set_outcome(s, "M_EX+V5") == b]
        g, s = med(pool, lambda t: (t[1][1]["scores"]["sbg_v5"], t[0]))
        sel[tag] = {"rule_pool_size": len(pool), "group": g, "changed": s[1]["pair_id"], "equivalent": s[0]["pair_id"]}
    byid = {r["pair_id"]: r for r in pop}
    for k, v in sel.items():
        for role in ("changed", "equivalent"):
            r = byid[v[role]]
            v[f"{role}_scores"] = {p: r["scores"][p] for p in SCORE_KEYS}
            v[f"{role}_meta"] = {"base_id": r["base_id"], "transformation_type": r["transformation_type"], "edit_size": r["_edit"],
                                 "variant_path": r["variant_path"], "base_path": r["base_path"]}
    OUTSEL.write_text(json.dumps(sel, indent=1) + "\n")
    for k, v in sel.items():
        print(k, "pool", v["rule_pool_size"], v["changed"], v["equivalent"])


def src_diff(base_path, variant_path):
    a = (C.REPO / base_path).read_text().splitlines()
    b = (C.REPO / variant_path).read_text().splitlines()
    return list(difflib.unified_diff(a, b, "base", "variant", lineterm="", n=0))


def canon_diff(base_path, variant_path):
    a = ast.unparse(ast.parse((C.REPO / base_path).read_text())).splitlines()
    b = ast.unparse(ast.parse((C.REPO / variant_path).read_text())).splitlines()
    return list(difflib.unified_diff(a, b, "base", "variant", lineterm="", n=0))


def trace(need):
    from experiments.final import extraction as ex
    out, cache = {}, {}
    for pid, (bp, vp) in need.items():
        _re.purge()
        A = ex.extract_program(str(C.REPO / bp), cache, "output_free_v8")
        B = ex.extract_program(str(C.REPO / vp), cache, "output_free_v8")
        sc = ex.score_pair(A, B)

        def graph(rec):
            return {str(k): v for k, v in (rec.state.transitions.items() if rec.state is not None else [])}

        def summ(rec):
            g = rec.genome_v3
            return {"ok": rec.ok, "entry": rec.entry_function, "stats": rec.stats, "failure": rec.failure_kind,
                    "genome": {"coverage_size": g.coverage_size, "exception_rate": g.exception_rate, "exception_type_set": sorted(g.exception_type_set),
                               "call_depth_max": g.call_depth_max, "n_unique_functions": g.n_unique_functions} if g is not None else None}

        ta, tb = graph(A), graph(B)
        oa = {k: v for k, v in ta.items() if k not in tb}
        ob = {k: v for k, v in tb.items() if k not in ta}
        sd = {k: [ta[k], tb[k]] for k in ta if k in tb and ta[k] != tb[k]}
        out[pid] = {"rescored": sc, "base": {**summ(A), "n_state_transitions": len(ta)}, "variant": {**summ(B), "n_state_transitions": len(tb)},
                    "n_transitions_only_in_base": len(oa), "n_transitions_only_in_variant": len(ob), "n_shared_with_different_frequency": len(sd),
                    "transitions_only_in_base_top8": dict(sorted(oa.items(), key=lambda kv: (-kv[1], kv[0]))[:8]),
                    "transitions_only_in_variant_top8": dict(sorted(ob.items(), key=lambda kv: (-kv[1], kv[0]))[:8]),
                    "shared_freq_diff_top6": dict(sorted(sd.items(), key=lambda kv: (-abs(kv[1][0] - kv[1][1]), kv[0]))[:6])}
    return out


def run_trace():
    sel = json.loads(OUTSEL.read_text())
    pop, _ = C.load_v10_population()
    byid = {r["pair_id"]: r for r in pop}
    need = {}
    for v in sel.values():
        for role in ("changed", "equivalent"):
            r = byid[v[role]]
            need[r["pair_id"]] = (r["base_path"], r["variant_path"])
    tr = trace(need)
    res = {"note": "Selected pairs re-traced with the frozen extractor (protocol output_free_v8, CPython 3.13); rescored values compared with the frozen scored file.",
           "rescore_matches_frozen": {}, "cases": {}}
    for pid, t in tr.items():
        fr = byid[pid]["scores"]
        res["rescore_matches_frozen"][pid] = bool(t["rescored"] is not None and all(abs(t["rescored"][k] - fr[k]) < 1e-9 for k in
                                                  ("sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state", "exception_fraction", "call_count", "coverage_size")))
    for k, v in sel.items():
        c = {}
        for role in ("changed", "equivalent"):
            pid = v[role]
            r = byid[pid]
            c[role] = {"pair_id": pid, "meta": v[f"{role}_meta"], "scores_frozen": v[f"{role}_scores"],
                       "source_diff_raw": src_diff(r["base_path"], r["variant_path"])[:80],
                       "source_diff_canonical": canon_diff(r["base_path"], r["variant_path"])[:80], "trace": tr[pid]}
        res["cases"][k] = c
    OUTTR.write_text(json.dumps(res, indent=1, default=str) + "\n")
    print("rescore matches frozen:", sum(res["rescore_matches_frozen"].values()), "/", len(res["rescore_matches_frozen"]))


if __name__ == "__main__":
    {"select": select, "trace": run_trace}[sys.argv[1]]()
