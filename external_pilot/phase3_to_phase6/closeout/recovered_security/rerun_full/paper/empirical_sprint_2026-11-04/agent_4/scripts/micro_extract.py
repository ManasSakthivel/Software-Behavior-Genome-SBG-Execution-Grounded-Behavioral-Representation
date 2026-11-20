"""Exploratory micro-diagnostic. usage: <python> micro_extract.py <copy_root> <protocol> <prog.py> ...
Prints JSON [python, hashseed, protocol, prog, ok, n_events] using experiments.final.extraction from the COPY. Stdout only."""
import sys, json, os, pathlib
root = pathlib.Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root)); os.chdir(root)
from experiments.final import extraction as ex
proto = sys.argv[2]; res = []
for prog in sys.argv[3:]:
    r = ex.extract_program(f"benchmark/corpus/base_programs/{prog}", {}, proto)
    res.append({"python": ".".join(map(str, sys.version_info[:3])), "hashseed": os.environ.get("PYTHONHASHSEED"), "protocol": proto,
                "prog": prog, "ok": r.ok, "n_events": r.stats.get("n_events"), "fail": r.failure_kind})
print(json.dumps(res))
