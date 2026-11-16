#!/usr/bin/env python3
"""EXP-WPC-001: per-program genome bundles for the WP-C component ablations.

Why this exists (and why the shared trace cache is NOT sufficient):
  The shared cache (results/raw/trace_cache) stores locals snapshots only for call/return/exception events;
  `line`-event snapshots are dropped (dump_traces.compact).  The frozen state genome consumes line-event snapshots, so
  the state genome (and every state-variant) cannot be recomputed from the cache.  This script therefore re-executes the
  FROZEN extraction (experiments.final.extraction, protocol output_free_v8, unchanged entry policy / inputs / budgets)
  in-process, captures the very same sandbox traces, and persists:
    * frozen genome objects (V3, temporal, state)           -> original-SBG representation (verified against the cache)
    * state-genome variants + return-value (RV) multisets   -> EXPLORATORY modified representations (never original SBG)
    * label-free leakage diagnostics (is the return value visible in locals at return events?)

READ-ONLY w.r.t. SBG/.  The tracer is wrapped IN MEMORY (monkeypatch of sbg.extraction.dynamic.tracer._make_trace_fn) only to
attach `ret_repr` (= the `arg` of sys.settrace 'return' events) to the already-recorded TraceEvent; nothing else about the
recorded events changes, so frozen genomes are unaffected (verified: frozen scores recomputed == cache pairs_scores).

  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python wpc_extract.py --split v9c_dev --workers 4
Resumable: a program directory containing DONE is skipped.  Splits allowed: v9c_dev, v9c_train ONLY (v10_test / v9c_val are
refused by design: WP-C must not rescore them).
"""
from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import gzip
import hashlib
import json
import os
import pathlib
import random
import re
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve()
WPC = HERE.parents[1]
PKG = WPC.parent
REPO = PKG.parent / "SBG"
POP = PKG / "configs" / "populations"
OUT_ROOT = WPC / "raw" / "EXP-WPC-001"
ALLOWED = ("v9c_dev", "v9c_train")


# ---------------------------------------------------------------------------------------------- variants
def _event_copy(ev, **kw):
    d = dict(event_type=ev.event_type, function_name=ev.function_name, lineno=ev.lineno,
             local_vars_snapshot=ev.local_vars_snapshot, timestamp_ns=ev.timestamp_ns)
    d.update(kw)
    return type(ev)(**d)


def _retrace(traces, fn):
    """Return new ExecutionTrace list whose events are fn(trace_index, [events]) (events only changed)."""
    out = []
    for ti, t in enumerate(traces):
        evs = fn(ti, t.events)
        out.append(type(t)(program_id=t.program_id, input_repr=t.input_repr, events=evs, return_value=t.return_value,
                           exception=t.exception, stdout=t.stdout, execution_time_ms=t.execution_time_ms,
                           coverage=t.coverage, truncated=t.truncated))
    return out


def make_variants(flat_traces):
    """name -> transformed trace list.  s0 is the identity (== frozen)."""
    # argument names per function = keys of the snapshot at that function's first call event
    args = {}
    for t in flat_traces:
        for e in t.events:
            if e.event_type == "call" and e.function_name not in args:
                args[e.function_name] = set(e.local_vars_snapshot)

    def noret(ti, evs):
        return [e for e in evs if e.event_type != "return"]

    def restrict_args(evs):
        out = []
        for e in evs:
            keep = args.get(e.function_name, set())
            out.append(_event_copy(e, local_vars_snapshot={k: v for k, v in e.local_vars_snapshot.items() if k in keep}))
        return out

    def boundary(ti, evs):
        return [e for e in evs if e.event_type != "line"]

    def structure(ti, evs):          # keep variable existence, collapse every value to the same abstract class
        return [_event_copy(e, local_vars_snapshot={k: "0" for k in e.local_vars_snapshot}) for e in evs]

    def shuffle(ti, evs):            # permute values among the variables of each snapshot (deterministic seed)
        out = []
        for ei, e in enumerate(evs):
            snap = e.local_vars_snapshot
            if len(snap) >= 2:
                keys = sorted(snap)
                vals = [snap[k] for k in keys]
                random.Random(f"wpc-shuffle:{ti}:{ei}").shuffle(vals)
                snap = dict(zip(keys, vals))
            out.append(_event_copy(e, local_vars_snapshot=snap))
        return out

    return {
        "s0": flat_traces,
        "s_noret": _retrace(flat_traces, noret),
        "s_args": _retrace(flat_traces, lambda ti, evs: restrict_args(evs)),
        "s_args_noret": _retrace(flat_traces, lambda ti, evs: restrict_args(noret(ti, evs))),
        "s_boundary": _retrace(flat_traces, boundary),
        "s_boundary_noret": _retrace(flat_traces, lambda ti, evs: noret(ti, boundary(ti, evs))),
        "s_structure": _retrace(flat_traces, structure),
        "s_shuffle": _retrace(flat_traces, shuffle),
    }


def trans_to_json(tr):
    return [[k[0], k[1], k[2], k[3], v] for k, v in sorted(tr.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2], kv[0][3]))]


# ---------------------------------------------------------------------------------------------- return-value multisets
def rv_multisets(flat_traces, abstract):
    """Multisets over return events; key=(func_idx, token).  Functions indexed in first-call order (as the frozen state genome)."""
    idx = {}
    for t in flat_traces:
        for e in t.events:
            if e.event_type == "call" and e.function_name not in idx:
                idx[e.function_name] = len(idx)
    out = {"rv_abs100": {}, "rv_abs_full": {}, "rv_type_abs": {}, "rv_hash": {}, "rv_entry_hash": {}}
    n_ret = n_ret_with_repr = 0
    entry_top = None
    for t in flat_traces:
        # entry function of this trace = function of the first call event
        first_call = next((e.function_name for e in t.events if e.event_type == "call"), None)
        for e in t.events:
            if e.event_type != "return":
                continue
            n_ret += 1
            rr = getattr(e, "ret_repr", None)
            if rr is None:
                continue
            n_ret_with_repr += 1
            fi = idx.get(e.function_name, 0)
            typ = re.match(r"^[A-Za-z_][A-Za-z0-9_.]*(?=\()", rr)
            tname = "scalar/collection"
            ab100 = abstract(rr[:100])
            abfull = abstract(rr)
            for name, token in (("rv_abs100", ab100), ("rv_abs_full", abfull),
                                ("rv_type_abs", f"{_pytype(rr)}|{abfull}"),
                                ("rv_hash", hashlib.md5(rr.encode()).hexdigest()[:10])):
                k = f"{fi}|{token}"
                out[name][k] = out[name].get(k, 0) + 1
            if e.function_name == first_call:
                k = f"{fi}|{hashlib.md5(rr.encode()).hexdigest()[:10]}"
                out["rv_entry_hash"][k] = out["rv_entry_hash"].get(k, 0) + 1
    return out, {"n_return_events": n_ret, "n_return_events_with_repr": n_ret_with_repr}


def _pytype(rr):
    r = rr.strip()
    if r in ("None",):
        return "NoneType"
    if r in ("True", "False"):
        return "bool"
    if re.match(r"^-?\d+$", r):
        return "int"
    if re.match(r"^-?\d+\.\d", r) or r in ("inf", "-inf", "nan"):
        return "float"
    if r[:1] in ("'", '"'):
        return "str"
    if r[:1] == "[":
        return "list"
    if r[:1] == "(":
        return "tuple"
    if r[:1] == "{":
        return "dict/set"
    return "other"


def leakage_diag(flat_traces):
    """Label-free: is the function's return value visible in some local at its own return event (snapshot cap 100)?"""
    trivial = {"None", "True", "False", "0", "1", "-1", "2"}
    tot = vis = nt_tot = nt_vis = ent_tot = ent_vis = ent_nt_tot = ent_nt_vis = 0
    for t in flat_traces:
        first_call = next((e.function_name for e in t.events if e.event_type == "call"), None)
        for e in t.events:
            if e.event_type != "return":
                continue
            rr = getattr(e, "ret_repr", None)
            if rr is None:
                continue
            key = rr[:100]
            seen = any(v == key for v in e.local_vars_snapshot.values())
            nontriv = rr not in trivial
            tot += 1
            vis += seen
            if nontriv:
                nt_tot += 1
                nt_vis += seen
            if e.function_name == first_call:
                ent_tot += 1
                ent_vis += seen
                if nontriv:
                    ent_nt_tot += 1
                    ent_nt_vis += seen
    return {"ret_events": tot, "ret_visible_in_locals": vis, "ret_events_nontrivial": nt_tot, "nontrivial_visible": nt_vis,
            "entry_ret_events": ent_tot, "entry_visible": ent_vis, "entry_nontrivial": ent_nt_tot,
            "entry_nontrivial_visible": ent_nt_vis}


# ---------------------------------------------------------------------------------------------- worker
def worker(split, prog, outdir):
    sys.path.insert(0, str(REPO))
    os.chdir(REPO)
    from experiments.final import extraction as ex
    import sbg.extraction.dynamic.tracer as tr
    from sbg.v5.state_transition_genome import StateTransitionGenome, _repr_to_abstract

    orig_make = tr._make_trace_fn

    def patched(state):
        inner = orig_make(state)

        def _t(frame, event, arg):
            n0 = len(state.events)
            r = inner(frame, event, arg)
            if event == "return" and len(state.events) == n0 + 1:
                try:
                    rr = repr(arg)
                except Exception:                                  # noqa: BLE001
                    rr = "<repr-error>"
                state.events[-1].ret_repr = rr[:1500]
            return _t if r is not None else None
        return _t
    tr._make_trace_fn = patched

    captured = {}
    orig_run = ex._runner.run

    def wrapped(program_id, *a, **k):
        res = orig_run(program_id, *a, **k)
        captured[program_id] = res
        return res
    ex._runner.run = wrapped

    rows = json.loads((POP / f"{split}.json").read_text())["rows"]
    # rows without paths are unevaluated/invalid placeholders in the population file (no source to execute)
    paths = sorted({r[k] for r in rows if r["base_id"] == prog for k in ("base_path", "variant_path") if r.get(k)})
    od = pathlib.Path(outdir)
    od.mkdir(parents=True, exist_ok=True)
    sg = StateTransitionGenome()
    cache = {}
    n_ok = 0
    for path in paths:
        re.purge()
        t0 = time.time()
        rec = ex.extract_program(str(REPO / path), cache, "output_free_v8")
        sb = captured.pop(pathlib.Path(path).stem, None)
        info = {"path": path, "ok": rec.ok, "failure_kind": rec.failure_kind, "failure_detail": rec.failure_detail,
                "entry_function": rec.entry_function, "stats": rec.stats}
        if rec.ok and sb is not None and sb.traces:
            flat = [t for run in sb.traces for t in run]
            info["n_runs"] = len(sb.traces)
            info["v3"] = _jsonable(dataclasses.asdict(rec.genome_v3))
            info["temporal"] = _jsonable(dataclasses.asdict(rec.temporal)) if rec.temporal is not None else None
            info["state_frozen"] = trans_to_json(rec.state.transitions) if rec.state is not None else None
            variants = {}
            for name, trs in make_variants(flat).items():
                g = sg.extract(trs)
                variants[name] = trans_to_json(g.transitions)
            info["state_variants"] = variants
            # self-check: re-extraction of the identity variant must equal the frozen state graph
            info["s0_equals_frozen"] = (rec.state is not None and
                                        {tuple(x[:4]): x[4] for x in variants["s0"]} == dict(rec.state.transitions))
            rvs, rvmeta = rv_multisets(flat, _repr_to_abstract)
            info["rv"] = rvs
            info["rv_meta"] = rvmeta
            info["leakage_diag"] = leakage_diag(flat)
            n_ok += 1
        info["seconds"] = round(time.time() - t0, 3)
        fn = od / (hashlib.sha1(path.encode()).hexdigest()[:12] + "__" + pathlib.Path(path).stem + ".json.gz")
        with gzip.open(fn, "wt") as f:
            json.dump(info, f)
    (od / "DONE").write_text(f"{time.time()} files={len(paths)} ok={n_ok}")
    print("@@ok", prog, len(paths), "files", n_ok, "ok")


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--worker")
    ap.add_argument("--outdir")
    ap.add_argument("--timeout", type=int, default=1200)
    ap.add_argument("--skip", default="", help="comma list of programs to skip (logged)")
    a = ap.parse_args()
    if a.split not in ALLOWED:
        sys.exit(f"refused: WP-C may only process {ALLOWED} (V10 test / V9c validation are not rescored)")
    if a.worker:
        worker(a.split, a.worker, a.outdir)
        return
    root = OUT_ROOT / a.split
    root.mkdir(parents=True, exist_ok=True)
    rows = json.loads((POP / f"{a.split}.json").read_text())["rows"]
    progs = sorted({r["base_id"] for r in rows})
    skip = {s for s in a.skip.split(",") if s}
    env = dict(os.environ, PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")
    log = []

    def run(pr):
        if pr in skip:
            return pr, "SKIPPED(by --skip; no trace cache / known rc=-9)", 0.0
        od = root / pr
        if (od / "DONE").exists():
            return pr, "skipped(done)", 0.0
        t0 = time.time()
        try:
            o = subprocess.run([sys.executable, str(HERE), "--split", a.split, "--worker", pr, "--outdir", str(od)],
                               env=env, capture_output=True, text=True, timeout=a.timeout)
            st = "ok" if (od / "DONE").exists() else f"FAILED rc={o.returncode} {o.stderr[-400:]}"
        except subprocess.TimeoutExpired:
            st = f"TIMEOUT>{a.timeout}s"
        return pr, st, time.time() - t0

    with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
        for pr, st, dt in pool.map(run, progs):
            print(f"{pr:40s} {st} {dt:.1f}s", flush=True)
            log.append({"program": pr, "status": st, "seconds": round(dt, 1)})
    (root / "RUN_LOG.json").write_text(json.dumps(log, indent=1))


if __name__ == "__main__":
    main()
