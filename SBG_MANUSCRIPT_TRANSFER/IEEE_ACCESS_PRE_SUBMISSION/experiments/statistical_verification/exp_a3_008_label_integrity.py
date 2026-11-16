#!/usr/bin/env python3
"""EXP-A3-008: trace-based independent label integrity, invalid-mutation, timeout/truncation and missing-trace analysis.
Inputs: raw trace dumps (executed by the frozen extraction harness; experiments/common/dump_traces.py; cached run 0 per input: ret/exc/stdout/trunc/cov)
        in PKG/results/raw/trace_cache/<design>_<split>/<prog> (orchestrator) or PKG/results/raw/EXP-A3-005/trace_cache/... (my own dump);
        raw pair metadata via a3lib (own re-implementation); frozen scored files for the replication check.
Rule: CHANGED must differ from its base in some observable output (return value, exception, stdout) on >=1 protocol input; EQUIVALENT must not.
Limitation: the cached traces do NOT record argument mutation (part of the repo's oracle) so 'CH without visible diff' are labelled
'no-visible-diff' (could be mutation-only) and EQ-with-diff are the hard label errors.
  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python exp_a3_008_label_integrity.py
"""
import collections, csv, gzip, hashlib, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import a3lib as L

RAW = L.PKG / "results/raw/EXP-A3-008"; RAW.mkdir(parents=True, exist_ok=True); TAB = L.PKG / "results/tables"
ADDR = re.compile(r"0x[0-9a-fA-F]+")

def cache_dir(design, split, prog):
    for root in (L.PKG / "results/raw/trace_cache", L.PKG / "results/raw/EXP-A3-005/trace_cache"):
        d = root / f"{design}_{split}" / prog
        if (d / "DONE").exists(): return d
    return None

_rec = {}
def rec(design, split, prog, path):
    k = (design, split, prog, path)
    if k not in _rec:
        d = cache_dir(design, split, prog)
        fn = d / (hashlib.sha1(path.encode()).hexdigest()[:12] + "__" + pathlib.Path(path).stem + ".json.gz")
        _rec[k] = json.load(gzip.open(fn, "rt"))
    return _rec[k]

def norm(t):
    return (ADDR.sub("0x?", t["ret"]), t["exc"], t["stdout"])

def exc_type(e):
    return None if e in (None, "None") else str(e).split(":")[0]

def compare(a, b):
    ta, tb = (a["sandbox"] or {}).get("traces", []), (b["sandbox"] or {}).get("traces", [])
    n = min(len(ta), len(tb)); d = {"ret": 0, "exc_msg": 0, "exc_type": 0, "stdout": 0, "any_strict": 0, "any_lenient": 0, "input_mismatch": 0}
    for x, y in zip(ta[:n], tb[:n]):
        r1, e1, o1 = norm(x); r2, e2, o2 = norm(y)
        dr, de, do = r1 != r2, e1 != e2, o1 != o2
        dt = exc_type(x["exc"]) != exc_type(y["exc"])
        d["ret"] += dr; d["exc_msg"] += de; d["exc_type"] += dt; d["stdout"] += do
        d["any_strict"] += (dr or de or do); d["any_lenient"] += (dr or dt or do)
        d["input_mismatch"] += x["input"] != y["input"]
    d["n_cmp"], d["len_base"], d["len_var"] = n, len(ta), len(tb)
    return d

def load_design(design, split):
    if design == "v10":
        meta = {m["pair_id"]: m for m in L.jl(L.V10D / "pairs_test.jsonl")}
        allrows, prim = L.build_v10(with_static=False)
        for r in allrows: r.setdefault("scores", None)
        frozen = {r["pair_id"]: r for r in L.jl(L.ART / "pairs_v10_test_v6exp.jsonl")}
        sp = lambda m: m.get("sp_type"); sc = lambda m: m.get("sc_type")   # noqa: E731
    else:
        m9 = {m["pair_id"]: m for m in L.jl(L.V9D / f"pairs_{split}.jsonl")}
        v8 = {m["pair_id"]: m for m in L.jl(L.V8D / f"pairs_{split}.jsonl")}
        meta = dict(m9)
        for m in m9.values(): meta[m["matched_equivalent_pair_id"]] = v8[m["matched_equivalent_pair_id"]]
        allrows, prim = L.build_v9c(split)
        frozen = {r["pair_id"]: r for r in allrows}
        sp = lambda m: m.get("sp_type") or m.get("transformation_type"); sc = lambda m: m.get("sc_type")  # noqa: E731
    return meta, allrows, prim, frozen, sp, sc

def analyse(design, split):
    meta, allrows, prim, frozen, sp, sc = load_design(design, split)
    prim_ids = {r["pair_id"] for r in prim}
    rowid = {r["pair_id"]: r for r in allrows}
    out = []; scorecmp = []
    for pid, m in meta.items():
        label = int(m["semantic_relation"] == "CHANGED")
        if m["base_id"] not in {x["base_id"] for x in allrows}:   # stale programs removed by repo loader
            continue
        d = cache_dir(design, split, m["base_id"])
        if d is None:
            out.append({"pair_id": pid, "missing_cache": True}); continue
        a, b = rec(design, split, m["base_id"], m["base_path"]), rec(design, split, m["base_id"], m["variant_path"])
        cmpd = compare(a, b) if (a["ok"] and b["ok"]) else None
        # replication of the frozen score
        ps = {x["pair_id"]: x for x in json.loads((d / "pairs_scores.json").read_text())}[pid]
        fz = frozen.get(pid)
        if ps["evaluated"] and fz and fz.get("evaluated") and fz.get("scores"):
            diffs = [abs(ps["scores"][k] - fz["scores"][k]) for k in ps["scores"] if k in fz["scores"] and isinstance(ps["scores"][k], (int, float))]
            scorecmp.append(max(diffs) if diffs else 0.0)
        flags = []
        for rr in (a, b):
            sb = rr["sandbox"]
            if sb:
                flags.append({"trunc_traces": sum(1 for t in sb["traces"] if t["trunc"]), "n_traces": len(sb["traces"]),
                              "timeout_fraction": sb["timeout_fraction"], "sb_error": sb["error"], "nondeterministic": len(set(sb["run_digests"])) > 1,
                              "budget": rr["stats"].get("program_budget_exceeded") if rr["stats"] else None})
            else:
                flags.append(None)
        row = {"pair_id": pid, "base_id": m["base_id"], "label": label, "type": sp(m), "sc": sc(m), "transformation_type": m["transformation_type"],
               "dump_evaluated": ps["evaluated"], "frozen_evaluated": bool(fz and fz.get("evaluated")), "in_primary": pid in prim_ids,
               "base_ok": a["ok"], "var_ok": b["ok"], "base_fail": a["failure_kind"], "var_fail": b["failure_kind"],
               "base_entry": a["entry_function"], "var_entry": b["entry_function"], "cmp": cmpd, "flags_base": flags[0], "flags_var": flags[1]}
        out.append(row)
    return meta, allrows, prim, out, scorecmp

def classify(out):
    tab = collections.Counter(); errs = []
    for r in out:
        if r.get("missing_cache") or r["cmp"] is None: continue
        c = r["cmp"]; vis_s, vis_l = c["any_strict"] > 0, c["any_lenient"] > 0
        key = ("CH" if r["label"] else "EQ", "diff" if vis_s else "same")
        tab[key] += 1
        if (r["label"] == 0 and vis_s) or (r["label"] == 1 and not vis_s):
            errs.append({"pair_id": r["pair_id"], "label": r["label"], "type": r["type"], "sc": r["sc"], "in_primary": r["in_primary"],
                         "n_cmp": c["n_cmp"], "n_diff_strict": c["any_strict"], "n_diff_lenient": c["any_lenient"], "ret": c["ret"], "exc_msg": c["exc_msg"],
                         "exc_type": c["exc_type"], "stdout": c["stdout"], "input_mismatch": c["input_mismatch"], "base_entry": r["base_entry"], "var_entry": r["var_entry"]})
    return tab, errs

def main():
    summary = {}
    for design, split in (("v10", "test"), ("v9c", "val")):
        meta, allrows, prim, out, scorecmp = analyse(design, split)
        tag = f"{design}_{split}"
        tab, errs = classify(out)
        miss = [r["pair_id"] for r in out if r.get("missing_cache")]
        evals = [r for r in out if not r.get("missing_cache")]
        # --- primary-only classification
        tabp, errp = classify([r for r in out if r.get("in_primary")])
        # pairs where both traces exist but variant/base failed extraction
        fail = collections.Counter((r["label"], r["base_fail"] or "ok", r["var_fail"] or "ok") for r in evals if not (r["base_ok"] and r["var_ok"]))
        # timeouts / truncation over evaluated (primary)
        def agg(rows):
            n = len(rows); pt = pb = ptf = nd = bud = 0; ttr = ttot = 0
            for r in rows:
                fl = [r["flags_base"], r["flags_var"]]
                trunc = sum((f["trunc_traces"] if f else 0) for f in fl); ttr += trunc; ttot += sum((f["n_traces"] if f else 0) for f in fl)
                pt += trunc > 0
                ptf += any(f and f["timeout_fraction"] for f in fl)
                nd += any(f and f["nondeterministic"] for f in fl)
                bud += any(f and f["budget"] for f in fl)
            return {"pairs": n, "pairs_with_truncated_trace": pt, "pairs_with_timeout_fraction>0": ptf, "pairs_with_nondeterministic_run_digests": nd,
                    "pairs_budget_exceeded": bud, "trace_trunc": ttr, "traces": ttot, "trunc_trace_fraction": round(ttr / ttot, 5) if ttot else None}
        prim_rows = [r for r in evals if r["in_primary"]]
        # truncation vs label
        trunc_lab = {lab: agg([r for r in prim_rows if r["label"] == lab]) for lab in (0, 1)}
        # frozen vs dump: evaluated flag agreement
        agree = collections.Counter((r["dump_evaluated"], r["frozen_evaluated"]) for r in evals)
        # EQ transformation breakdown of diffs
        by_type = collections.defaultdict(lambda: collections.Counter())
        for r in evals:
            if r["cmp"] is None: continue
            by_type[(("CH" if r["label"] else "EQ"), r["type"] if r["label"] == 0 else (r["sc"] or "?"))][("diff" if r["cmp"]["any_strict"] else "same")] += 1
        summary[tag] = {"n_meta_pairs": len(out), "missing_cache_pairs": miss, "classification_all_extractable": {f"{k[0]}_{k[1]}": v for k, v in tab.items()},
                        "classification_primary": {f"{k[0]}_{k[1]}": v for k, v in tabp.items()},
                        "label_error_candidates_all": errs, "label_error_candidates_primary": errp, "extraction_failures": {str(k): v for k, v in fail.items()},
                        "score_replication": {"n_compared": len(scorecmp), "max_abs_diff_dump_vs_frozen_scores": max(scorecmp) if scorecmp else None,
                                              "n_nonzero_diff": sum(1 for x in scorecmp if x > 1e-9)},
                        "evaluated_flag_agreement(dump,frozen)": {str(k): v for k, v in agree.items()},
                        "truncation_primary_by_label": trunc_lab, "truncation_primary_all": agg(prim_rows),
                        "diff_by_type": {f"{k[0]}|{k[1]}": dict(v) for k, v in sorted(by_type.items(), key=str)}}
        with open(TAB / f"EXP-A3-008_{tag}_label_error_candidates.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["pair_id", "label", "type", "sc", "in_primary", "n_cmp", "n_diff_strict", "n_diff_lenient", "ret", "exc_msg", "exc_type", "stdout", "input_mismatch", "base_entry", "var_entry"])
            w.writeheader(); w.writerows(errs)
        (RAW / f"{tag}_pair_level.json").write_text(json.dumps(out, default=str))
        print(tag, json.dumps({k: summary[tag][k] for k in ("n_meta_pairs", "classification_all_extractable", "classification_primary", "extraction_failures", "score_replication", "evaluated_flag_agreement(dump,frozen)", "truncation_primary_all")}, indent=1, default=str)[:2500], flush=True)
        print("missing", miss[:5], "n_err", len(errs), "n_err_primary", len(errp), flush=True)
    (RAW / "label_integrity_summary.json").write_text(json.dumps(summary, indent=1, default=str))

if __name__ == "__main__":
    main()
