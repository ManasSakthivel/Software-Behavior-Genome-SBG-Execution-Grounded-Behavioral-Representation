"""Exploratory: where do the heapsort 8771 vs 8024 events come from? Traces output_free_v6 extraction's underlying events via ex.extract_program is opaque,
so replicate: call entry fn on one list battery input under Tracer; report event-type/function breakdown. Stdout only."""
import sys, json, os, pathlib, collections, importlib.util
root = pathlib.Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root)); os.chdir(root)
from sbg.extraction.dynamic.tracer import Tracer
src = root/"benchmark/corpus/base_programs/sort_heapsort.py"
s = importlib.util.spec_from_file_location("hs", src); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
fn = [getattr(m,n) for n in dir(m) if "sort" in n and callable(getattr(m,n)) and getattr(getattr(m,n),"__module__","")=="hs"][0]
print(fn.__name__, file=sys.stderr)
out = {}
for inp in ([3,1,4,1,5,9,2,6],[10,9,8,7,6,5],[0,0,0,0],list(range(16))):
    tr = Tracer().trace(fn, [list(inp)], max_events=5000)[0]
    c = collections.Counter(e.event_type for e in tr.events)
    out[str(inp)] = {"n": len(tr.events), "types": dict(c), "funcs": dict(collections.Counter(e.function_name for e in tr.events if e.event_type=="call")), "trunc": tr.truncated}
print(json.dumps({"python": ".".join(map(str, sys.version_info[:3])), "res": out}))
