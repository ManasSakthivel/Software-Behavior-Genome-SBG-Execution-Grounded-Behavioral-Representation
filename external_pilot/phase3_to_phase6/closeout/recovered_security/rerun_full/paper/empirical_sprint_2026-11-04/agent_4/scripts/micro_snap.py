"""Exploratory: per-event locals snapshot keys for REG_03 buggy (a listcomp) -- stdout only."""
import sys, os, pathlib, json
root = pathlib.Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root)); os.chdir(root)
from sbg.extraction.dynamic.tracer import Tracer
from benchmark.v5.regression.regression_pairs import REGRESSION_PAIRS
rp = [r for r in REGRESSION_PAIRS if r["id"]=="REG_03"][0]
tr = Tracer().trace(lambda a: rp["buggy_fn"](*a), rp["trigger_inputs"][:1], max_events=500)[0]
print(json.dumps({"python": ".".join(map(str, sys.version_info[:3])), "ev": [(e.event_type, e.function_name, e.lineno, e.local_vars_snapshot) for e in tr.events]}))
