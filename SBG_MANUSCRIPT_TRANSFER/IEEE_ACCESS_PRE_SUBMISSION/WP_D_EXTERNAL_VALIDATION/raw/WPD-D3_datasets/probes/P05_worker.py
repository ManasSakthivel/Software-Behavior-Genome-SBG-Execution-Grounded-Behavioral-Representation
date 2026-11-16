#!/usr/bin/env python3
"""P05 worker: run ONE dataset program on SBG's frozen 11-input battery and print outcome signatures as JSON.
NOT SBG scoring: no trace features, no distance, no model. Uses SBG's frozen entry-selection+input-synthesis (read-only import of protocol.py).
usage: P05_worker.py <source_file> [entry_override]"""
import sys, json, types, copy, signal, io, contextlib, importlib.util, os, tempfile
sys.dont_write_bytecode = True
PROT = "/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/experiments/final/protocol.py"
spec = importlib.util.spec_from_file_location("sbg_protocol_ro", PROT); P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
class TO(BaseException): pass
def h(*a): raise TO()
signal.signal(signal.SIGALRM, h)
src = open(sys.argv[1], errors="replace").read()
res = {"file": sys.argv[1]}
os.chdir(tempfile.mkdtemp(prefix="p05_"))
mod = types.ModuleType("prog"); mod.__dict__["__name__"] = "prog"
try:
    signal.setitimer(signal.ITIMER_REAL, 2.0)
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(src, sys.argv[1], "exec"), mod.__dict__)
    signal.setitimer(signal.ITIMER_REAL, 0)
except BaseException as e:
    signal.setitimer(signal.ITIMER_REAL, 0)
    res.update(status="import_fail", err=type(e).__name__); print(json.dumps(res)); sys.exit(0)
fn, tag, inputs = P.select_entry_output_free(mod, src)
if fn is None:
    res.update(status="no_entry"); print(json.dumps(res)); sys.exit(0)
res.update(status="ok", entry=tag, outcomes=[])
for inp in inputs:
    inp = copy.deepcopy(inp); buf = io.StringIO()
    try:
        signal.setitimer(signal.ITIMER_REAL, 1.0)
        with contextlib.redirect_stdout(buf):
            r = fn(*inp) if isinstance(inputs[0], tuple) else (fn() if inputs == [None] else fn(inp))
        signal.setitimer(signal.ITIMER_REAL, 0)
        o = ["ret", repr(r)[:300]]
    except TO:
        o = ["timeout"]
    except BaseException as e:
        signal.setitimer(signal.ITIMER_REAL, 0); o = ["exc", type(e).__name__]
    signal.setitimer(signal.ITIMER_REAL, 0)
    o += [buf.getvalue()[:200], repr(inp)[:300]]   # stdout, post-call argument state (mutation)
    res["outcomes"].append(o)
print(json.dumps(res))
