"""List per-pair sbg_v5 / component deltas among tags. Exploratory; reads outputs/ only."""
import json, pathlib
O = pathlib.Path(__file__).resolve().parent.parent / "outputs"
comps = ["sbg_v5","sbg_v3","temporal","state"]
def vec(tag):
    R = json.load(open(O/tag/"REGRESSION_V5_RESULTS.json")); H = json.load(open(O/tag/"HARD_NEGATIVE_V5_RESULTS.json")); d = {}
    for p in R["pairs"]: d[("REG",p["id"])] = (p["distances"], p["n_events_buggy"], p["n_events_fixed"])
    for rg,b in H["regimes"].items():
        for p in b["pairs"]: d[("HN_"+rg,p["pair_id"])] = (p["distances"], None, None)
    return d
A, B, C = vec("py39"), vec("py311_seed0"), vec("py313")
print("py3.9 vs py3.11 (both pre-PEP709):")
for k in A:
    if A[k][0]!=B[k][0] or A[k][1:]!=B[k][1:]: print(" ",k,{c:(A[k][0][c],B[k][0][c]) for c in comps if A[k][0][c]!=B[k][0][c]}, A[k][1:], B[k][1:])
print("py3.11 vs py3.13 (PEP709 boundary):")
for k in B:
    if B[k][0]!=C[k][0] or B[k][1:]!=C[k][1:]: print(" ",k,{c:(round(B[k][0][c],4),round(C[k][0][c],4)) for c in comps if B[k][0][c]!=C[k][0][c]}, B[k][1:], C[k][1:])
