"""Exploratory: line-event sequence for heapsort([0,0,0,0]) -- stdout only."""
import sys, os, pathlib, importlib.util, json, collections
root = pathlib.Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root)); os.chdir(root)
from sbg.extraction.dynamic.tracer import Tracer
s = importlib.util.spec_from_file_location("hs", root/"benchmark/corpus/base_programs/sort_heapsort.py"); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
tr = Tracer().trace(m.heapsort, [[3,1,4,1,5,9,2,6]], max_events=5000)[0]
c = collections.Counter((e.event_type, e.lineno) for e in tr.events)
print(json.dumps({"python": ".".join(map(str, sys.version_info[:3])), "by_line": {f"{k[0]}:{k[1]}": v for k, v in sorted(c.items(), key=lambda kv: (kv[0][1], kv[0][0]))}}))
