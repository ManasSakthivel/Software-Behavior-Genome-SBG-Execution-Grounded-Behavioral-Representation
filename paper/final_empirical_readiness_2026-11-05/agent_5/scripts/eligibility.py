import sys, pathlib, json
HERE = pathlib.Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent/"_ws"))
from experiments.final import external_java as J
ok=[];bad=[]
for p in sorted((J.CORPUS/"correct").glob("*.java")):
    n=p.stem; sig=J.entry_signature(n,p.read_text())
    inp=None if sig is None else J.canonical_inputs(sig)
    jin=None if inp is None else J.inputs_to_java(sig,inp)
    (ok if jin else bad).append(n)
print(len(ok),len(bad),bad)
json.dump({"eligible":ok,"ineligible":bad},open(HERE.parent/"eligibility_quixbugs_java.json","w"),indent=1)
