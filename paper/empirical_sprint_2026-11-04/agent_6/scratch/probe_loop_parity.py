"""Scratch (agent 6): loop line-event parity Java(JDI) vs Python(sys.settrace) on QuixBugs BITCOUNT.
Structure/count comparison only. No scoring, no labels, nothing written outside this dir."""
import sys, pathlib, importlib.util, shutil, collections
sys.dont_write_bytecode = True
REPO = pathlib.Path("/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG"); sys.path.insert(0, str(REPO))
from experiments.final import external_java as J
from sbg.extraction.dynamic.tracer import Tracer
inputs = [[0],[1],[7],[255]]
src = (J.CORPUS/"correct"/"BITCOUNT.java").read_text()
sig = J.entry_signature("BITCOUNT", src); jin = J.inputs_to_java(sig, inputs)
cls, err = J.compile_version(src, "BITCOUNT", {"SbgHarness": J.harness_source("BITCOUNT", sig, jin)}, J.support_sources())
runs, e, _ = J.run_traces(cls, len(jin), [repr(tuple(i)) for i in inputs], "BITCOUNT"); shutil.rmtree(cls.parent, ignore_errors=True)
jt = runs[0]
pyp = REPO/"external/quixbugs/correct_python_programs/bitcount.py"
spec = importlib.util.spec_from_file_location("bc", pyp); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
pt = Tracer().trace(lambda a: m.bitcount(*a), [tuple(i) for i in inputs])
def summ(t, fn):
    c = collections.Counter(ev.event_type for ev in t.events if ev.function_name == fn)
    return dict(c), sorted(t.coverage)
for i, inp in enumerate(inputs):
    print(inp, "JAVA", summ(jt[i], "bitcount")[0], "cov_n", len(jt[i].coverage), "| PY", summ(pt[i], "bitcount")[0], "cov_n", len(pt[i].coverage))
print("java lines seq (input 7):", [ev.lineno for ev in jt[2].events if ev.event_type=="line"])
print("py   lines seq (input 7):", [ev.lineno for ev in pt[2].events if ev.event_type=="line"])
print("java call snapshot:", jt[2].events[0].local_vars_snapshot, "| py call snapshot:", pt[2].events[0].local_vars_snapshot)
print("java return snapshot:", [ev.local_vars_snapshot for ev in jt[2].events if ev.event_type=="return"], "| py:", [ev.local_vars_snapshot for ev in pt[2].events if ev.event_type=="return"])
