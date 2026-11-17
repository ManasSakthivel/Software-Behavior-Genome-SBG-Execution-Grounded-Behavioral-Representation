"""V6 feature extraction for QuixBugs (declared + canonical regimes) and BugsInPy, with the SAME executions/protocol as the V5 external runs
(experiments/final/external_{quixbugs,bugsinpy}.py: output_free_v7; QuixBugs declared = declared json_testcases inputs, outputs discarded).
  PYTHONHASHSEED=0 python experiments/v6/extract_external.py quixbugs_declared|quixbugs_canonical|bugsinpy
Writes artifacts/v6/holdout/features_<name>.jsonl (same schema as DEV features; failed/unexecutable pairs are kept as UNKNOWN rows, never dropped)."""
import os, sys, json, pathlib, tempfile, multiprocessing as mp, time
REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
PROTO = "output_free_v7"

def _row(pair_id, base_id, label, ttype, split, base, var, base_src, var_src, bpath, vpath, extra):
    from sbgv6.distance import pair_record
    from sbgv6 import features as F
    from experiments.final import extraction as X
    from experiments.final import external_common as ec
    rec = pair_record(base, var)
    la, lb = F.changed_lines(base_src, var_src); rec["edit_lines"] = len(la) + len(lb)
    v5 = X.score_pair(base.record, var.record)
    rec["v5_recomputed"] = None if v5 is None else v5["sbg_v5"]
    stored = dict(v5) if v5 is not None else {}
    stored.update(ec.static_scores(base_src, var_src))     # statics exist even when V5 abstains (as in the V5 external rows)
    return {"pair_id": pair_id, "base_id": base_id, "label": label, "transformation_type": ttype, "split": split,
            "v5_stored": stored, "v5_evaluated": v5 is not None, "base_path": bpath, "variant_path": vpath, **extra, **rec}

def _lost(pair_id, base_id, label, ttype, split, why, extra):
    return {"pair_id": pair_id, "base_id": base_id, "label": label, "transformation_type": ttype, "split": split, "v5_stored": {},
            "v5_evaluated": False, "status": "UNKNOWN", "reasons": ["worker_lost:" + why], **extra}

def quixbugs_work(a):
    program_id, regime = a
    from sbgv6.observe import PythonAdapter, Observation, _rec
    from experiments.final import extraction as X
    from experiments.final import external_quixbugs as Q
    manifest = json.loads(Q.MANIFEST_PATH.read_text()); entry = next(p for p in manifest["programs"] if p["id"] == program_id)
    if not entry["eligible"][regime]:     # ineligible in this regime: every pair stays in the denominator as UNKNOWN (never dropped)
        why = "ineligible_regime:" + str((entry.get("exclusion_reason") or {}).get(regime) if isinstance(entry.get("exclusion_reason"), dict) else entry.get("exclusion_reason"))[:80]
        return [_lost(f"{pid}__{regime}", program_id, label, kind, "external_" + regime, why, {"corpus": "quixbugs", "regime": regime}) for pid, label, kind, _, _ in Q._pairs_for(entry)]
    fixed_src = (REPO / entry["fixed_path"]).read_text()
    inputs = Q.load_declared_inputs(REPO / entry["declared_inputs"]["file"]) if regime == "declared" else None
    ad = PythonAdapter(PROTO)
    def obs(rel):
        path = str(REPO / rel); src = (REPO / rel).read_text()
        if regime == "canonical": return ad.observe(path)
        name, how = Q.resolve_declared_entry(program_id, fixed_src, src)
        _rec.last = None
        if name is None: record = X.ProgramRecord(path=path, ok=False, failure_kind="no_entry_function", failure_detail="declared entry unresolved")
        else: record = X.extract_with_inputs(path, {}, name, inputs, budgets_from=PROTO)
        runs = list(_rec.last.traces) if (record.ok and _rec.last is not None) else []
        return Observation(path, src, bool(record.ok and runs), None if record.ok and runs else (record.failure_kind or "no_traces"), runs, record)
    out = []; base = obs(entry["fixed_path"]); bsrc = fixed_src
    for pid, label, kind, brel, vrel in sorted(Q._pairs_for(entry), key=lambda p: p[1] == 1):   # buggy last, as in the V5 run
        try:
            var = obs(vrel); out.append(_row(f"{pid}__{regime}", program_id, label, kind, "external_" + regime, base, var, bsrc, (REPO / vrel).read_text(), brel, vrel, {"corpus": "quixbugs", "regime": regime}))
        except BaseException as e:  # noqa: BLE001
            out.append(_lost(f"{pid}__{regime}", program_id, label, kind, "external_" + regime, type(e).__name__, {"corpus": "quixbugs", "regime": regime}))
    return out

def bugsinpy_work(a):
    bug_idx, unit_idx = a
    from sbgv6.observe import PythonAdapter
    from experiments.final import external_bugsinpy as B
    manifest = json.loads(B.MANIFEST.read_text()); entry = manifest["bugs"][bug_idx]; unit = entry["units"][unit_idx]
    os.chdir(tempfile.mkdtemp(prefix="sbgv6_bip_")); ad = PythonAdapter(PROTO)
    fixed = REPO / unit["fixed_path"]; base = ad.observe(str(fixed)); bsrc = fixed.read_text(); out = []
    cmp = [("positive", 1, "real_fix", REPO / unit["buggy_path"])] + [("negative", 0, n["transformation"], REPO / n["path"]) for n in unit.get("negatives", [])]
    for role, label, trans, other in cmp:
        pid = f"{entry['id']}::{unit['file']}::{unit['unit']}::{trans}"
        try:
            var = ad.observe(str(other)); out.append(_row(pid, entry["id"], label, trans, "external_bugsinpy", base, var, bsrc, other.read_text(), unit["fixed_path"], str(other.relative_to(REPO)), {"corpus": "bugsinpy", "project": entry["project"], "role": role}))
        except BaseException as e:  # noqa: BLE001
            out.append(_lost(pid, entry["id"], label, trans, "external_bugsinpy", type(e).__name__, {"corpus": "bugsinpy", "project": entry["project"], "role": role}))
    return out

if __name__ == "__main__":
    name = sys.argv[1]; out = REPO / "artifacts/v6/holdout"; out.mkdir(parents=True, exist_ok=True); outf = out / f"features_{name}.jsonl"
    if name.startswith("quixbugs"):
        from experiments.final import external_quixbugs as Q
        regime = name.split("_")[1]; man = json.loads(Q.MANIFEST_PATH.read_text())
        tasks = [(p["id"], regime) for p in man["programs"]]; fn = quixbugs_work
    else:
        from experiments.final import external_bugsinpy as B
        man = json.loads(B.MANIFEST.read_text()); fn = bugsinpy_work
        tasks = [(i, j) for i, e in enumerate(man["bugs"]) for j, u in enumerate(e["units"]) if u["eligible"]]
    t0 = time.time(); n = 0
    with mp.Pool(12, maxtasksperchild=1) as pool, open(outf, "w") as f:
        pend = [(t, pool.apply_async(fn, (t,))) for t in tasks]
        for t, ar in pend:
            try: res = ar.get(timeout=int(os.environ.get("SBG_GROUP_TIMEOUT", "900")))
            except BaseException as e:  # noqa: BLE001
                res = [_lost(f"{name}::{t}", str(t), -1, "unknown", name, type(e).__name__, {})]
            for r in res: f.write(json.dumps(r, default=str) + "\n")
            f.flush(); n += len(res); print(f"{name}: {n} rows {time.time()-t0:.0f}s", flush=True)
