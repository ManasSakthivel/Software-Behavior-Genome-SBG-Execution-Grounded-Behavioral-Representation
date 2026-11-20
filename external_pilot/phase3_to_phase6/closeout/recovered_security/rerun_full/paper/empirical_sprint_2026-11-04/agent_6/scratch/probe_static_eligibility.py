"""Scratch (agent 6): STATIC eligibility only. Parses vendored Java signatures with the repo's own
entry_signature/canonical_inputs/inputs_to_java. Executes nothing, scores nothing, writes only stdout."""
import sys, json, pathlib, collections
sys.dont_write_bytecode = True
REPO = pathlib.Path("/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG"); sys.path.insert(0, str(REPO))
from experiments.final import external_java as J
man = json.loads((J.CORPUS/"MANIFEST.json").read_text())
decl = json.loads((J.CORPUS/"declared_inputs.json").read_text())
res = collections.OrderedDict(); c = collections.Counter()
for n in man["programs"]:
    src = (J.CORPUS/"correct"/f"{n}.java").read_text()
    sig = J.entry_signature(n, src)
    if sig is None: res[n] = "no_entry"; c["canonical:no_entry"]+=1; continue
    inp = J.canonical_inputs(sig)
    ok = bool(inp) and J.inputs_to_java(sig, inp) is not None
    res[n] = {"params":[t for _,t in sig["params"]], "canonical_eligible": ok}
    c["canonical:eligible" if ok else "canonical:unsupported_signature"] += 1
    d = decl.get(n); okd = bool(d) and J.inputs_to_java(sig, d) is not None
    c["declared:eligible" if okd else "declared:excluded"] += 1
print(json.dumps(c, indent=1)); 
print("canonical-ineligible param types:", sorted({tuple(v['params']) for v in res.values() if isinstance(v,dict) and not v['canonical_eligible']}))
json.dump(res, open(REPO/"paper/empirical_sprint_2026-11-04/agent_6/scratch/static_eligibility.json","w"), indent=1)
