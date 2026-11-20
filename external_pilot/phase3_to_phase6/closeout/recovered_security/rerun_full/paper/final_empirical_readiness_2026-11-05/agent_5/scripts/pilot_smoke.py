"""Agent 5 mechanical smoke run (NOT an evaluation).

Runs the *existing* SBG Java bridge (copied workspace `_ws`) on 3 fresh
author-written Java programs, each with one behaviour-preserving (SP) and one
behaviour-changing (SC) variant, labels them with an output-reading oracle,
and reports V5 distances descriptively. n=3 programs: no AUROC, no inference.
All compile output goes to OS temp dirs; nothing is written to frozen paths.
"""
import json, pathlib, sys, re
HERE = pathlib.Path(__file__).resolve().parent
WS = HERE.parent / "_ws"
sys.path.insert(0, str(WS))
from experiments.final import external_java as J      # noqa: E402
from experiments.final import extraction as X          # noqa: E402

PROG = HERE.parent / "programs"
VARIANTS = {   # name -> (SP renames {old: new}, SC literal edits [(old,new)])
    "SUMDIGITS": ({"total": "acc", "m": "rest"}, [("m > 0", "m > 9")]),
    "COUNTVOWELS": ({"count": "n", "i": "k"}, [("c == 'u'", "c == 'y'")]),
    "MAXRUN": ({"best": "top", "cur": "run"}, [("i > 0 &&", "i > 1 &&")]),
}
def apply(src, edits):
    if isinstance(edits, dict):       # whole-word identifier renames (SP)
        for a, b in edits.items():
            src = re.sub(r"(?<!')\b" + re.escape(a) + r"\b(?!')", b, src)
        return src
    for a, b in edits:
        src = src.replace(a, b)
    return src

def label_and_trace(name, src, sig, jin, reprs):
    rec, info = J.trace_version(name, src, sig, jin, reprs, "pilot")
    return rec

out = {"note": "mechanical smoke run, n=3 programs, NOT an evaluation", "jdk": None, "programs": []}
import subprocess
out["jdk"] = subprocess.run(["java", "-version"], capture_output=True, text=True).stderr.splitlines()[1]
for name, (sp, sc) in VARIANTS.items():
    base = (PROG / f"{name}.java").read_text()
    variants = {"SP": apply(base, sp), "SC": apply(base, sc)}
    sig = J.entry_signature(name, base)
    inputs = J.canonical_inputs(sig)
    row = {"program": name, "signature": sig, "n_inputs": None if inputs is None else len(inputs)}
    if inputs is None:
        row["status"] = "ineligible: no canonical inputs"; out["programs"].append(row); continue
    jin = J.inputs_to_java(sig, inputs)
    if jin is None:
        row["status"] = "ineligible: inputs not expressible as Java literals"; out["programs"].append(row); continue
    reprs = [repr(tuple(i)) for i in inputs]
    ob = J.oracle_outputs(name, base, sig, jin)
    brec = label_and_trace(name, base, sig, jin, reprs)
    row["base_ok"] = brec.ok
    for k, v in variants.items():
        ov = J.oracle_outputs(name, v, sig, jin)
        ndiff = None if (ob is None or ov is None) else sum(a != b for a, b in zip(ob, ov))
        vrec = label_and_trace(name, v, sig, jin, reprs)
        sc_ = X.score_pair(brec, vrec) if (brec.ok and vrec.ok) else None
        row[k] = {"oracle_inputs_differing": ndiff, "variant_ok": vrec.ok,
                  "edit_lines": sum(1 for a, b in zip(base.splitlines(), v.splitlines()) if a != b),
                  "sbg_v5": None if sc_ is None else round(sc_["sbg_v5"], 4)}
    row["status"] = "ran"; out["programs"].append(row)
print(json.dumps(out, indent=1))
(HERE.parent / "pilot_smoke_run2_output.json").write_text(json.dumps(out, indent=1))
