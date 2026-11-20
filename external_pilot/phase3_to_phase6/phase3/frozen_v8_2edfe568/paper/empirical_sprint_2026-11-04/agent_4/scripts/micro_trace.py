"""Exploratory micro-diagnostic (NOT a re-evaluation). Run as:
   PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 <python> micro_trace.py <copy_root> > out.json
Traces a few tiny existing toy programs with the repo Tracer (imported from the COPY, read-only)
and dumps event-type counts, function-name call counts, coverage lines, and first events. Writes only stdout."""
import sys, json, importlib.util, collections, pathlib
root = pathlib.Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root))
from sbg.extraction.dynamic.tracer import Tracer
from benchmark.v5.regression.regression_pairs import REGRESSION_PAIRS
def load(p):
    s = importlib.util.spec_from_file_location(p.parent.name + p.stem, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
HN = root / "benchmark/v5/hard_negatives"
cases = {}
for rp in REGRESSION_PAIRS:
    if rp["id"] in ("REG_03", "REG_09", "REG_11"):
        for side in ("buggy", "fixed"):
            fn = rp[side + "_fn"]
            cases[f"{rp['id']}_{side}"] = (lambda args, fn=fn: fn(*args), rp["trigger_inputs"][:1])
for name in ("pair_04_rename_invariant", "pair_07_dead_code_insertion", "pair_03_same_call_count_different_order"):
    for side in ("base", "variant"):
        m = load(HN / name / f"{side}_program.py")
        cases[f"{name}__{side}"] = (m.run, [[[3, 4]]] if "03" not in name else [[[3, None, 1]]])
out = {"python": sys.version.split()[0], "hashseed": __import__("os").environ.get("PYTHONHASHSEED"), "cases": {}}
for k, (fn, inputs) in cases.items():
    tr = Tracer().trace(fn, inputs, max_events=5000)[0]
    ev = tr.events
    out["cases"][k] = {
        "n_events": len(ev),
        "by_type": dict(collections.Counter(e.event_type for e in ev)),
        "calls_by_func": dict(collections.Counter(e.function_name for e in ev if e.event_type == "call")),
        "coverage_lines": sorted(tr.coverage),
        "exception": tr.exception,
        "events_head": [(e.event_type, e.function_name, e.lineno) for e in ev[:14]],
        "snapshot_sample": {kk: vv for kk, vv in (ev[3].local_vars_snapshot.items() if len(ev) > 3 else [])},
    }
print(json.dumps(out, indent=1))
