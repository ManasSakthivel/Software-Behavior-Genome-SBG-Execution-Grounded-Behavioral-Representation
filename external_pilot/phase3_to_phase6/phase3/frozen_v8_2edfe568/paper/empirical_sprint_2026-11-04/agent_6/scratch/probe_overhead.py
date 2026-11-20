"""Scratch probe (agent 6): wall-time + determinism of the existing JDI tracer on 3 programs.
Writes nothing but stdout/this dir. NOT an evaluation: no pair is scored against a label, no AUROC.
"""
import sys, time, json, pathlib
sys.dont_write_bytecode = True
REPO = pathlib.Path("/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG")
sys.path.insert(0, str(REPO))
from experiments.final import external_java as J
from experiments.final import extraction as X

def fp(rec):
    g = rec.genome_v3
    return (rec.stats["n_events"], rec.stats["call_count"], rec.stats["coverage_size"],
            json.dumps(sorted(g.call_transition_bigrams.items())),
            json.dumps(sorted(rec.temporal.call_trigrams.items())),
            json.dumps(sorted(map(str, rec.state.transitions.items()))))

for name in ["GCD", "BITCOUNT", "QUICKSORT"]:
    src = (J.CORPUS / "correct" / f"{name}.java").read_text()
    sig = J.entry_signature(name, src)
    inputs = J.canonical_inputs(sig)
    if not inputs:
        print(name, "unsupported signature", sig["params"]); continue
    jin = J.inputs_to_java(sig, inputs)
    reprs = [repr(tuple(a)) for a in inputs]
    out = []
    for rep in range(2):
        t0 = time.monotonic()
        rec, info = J.trace_version(name, src, sig, jin, reprs, "correct")
        out.append((rec, time.monotonic() - t0, info))
    r0, r1 = out[0][0], out[1][0]
    print(name, "ok", r0.ok, "n_traces", r0.stats.get("n_traces"), "n_events", r0.stats.get("n_events"),
          "wall_s", [round(o[1], 2) for o in out],
          "events/s", round(r0.stats["n_events"] / out[0][1], 1),
          "identical_feature_fingerprint_across_2_fresh_JVM_runs", fp(r0) == fp(r1))
