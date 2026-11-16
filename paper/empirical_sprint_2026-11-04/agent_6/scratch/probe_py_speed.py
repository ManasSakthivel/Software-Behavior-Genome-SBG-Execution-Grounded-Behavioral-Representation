"""Scratch (agent 6): Python Tracer wall time on QuixBugs python QUICKSORT (same 11 inputs x5 runs as protocol) for overhead ratio. No scoring."""
import sys, time, pathlib, importlib.util
sys.dont_write_bytecode = True
REPO = pathlib.Path("/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG"); sys.path.insert(0, str(REPO))
from sbg.extraction.dynamic.tracer import Tracer
from experiments.final import protocol as P
p = REPO/"external/quixbugs/correct_python_programs/quicksort.py"
spec = importlib.util.spec_from_file_location("qs", p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
inputs = [(x,) for x in P.LIST_BATTERY]
t0 = time.monotonic(); n = 0
for _ in range(5):
    for tr in Tracer().trace(lambda a: m.quicksort(*a), inputs, max_events=5000, timeout_s=1.0):
        n += len(tr.events)
dt = time.monotonic() - t0
print("python QUICKSORT: events", n, "wall_s", round(dt, 3), "events/s", round(n/dt))
