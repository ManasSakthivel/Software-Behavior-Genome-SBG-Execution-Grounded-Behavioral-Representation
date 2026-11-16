#!/usr/bin/env python3
"""P11: STATIC edit-size confound check for a HumanEvalPack design: CH=(canonical,buggy) vs EQ=(canonical, python-minifier variant). Repo edit-size definition re-implemented (ast.unparse unified-diff changed lines).
Reports edit-size distributions and the label-only edit-size AUROC (forward/reversed) = how much a trivial static baseline would separate the classes. No SBG, no execution."""
import ast, json, difflib, statistics as S
rows = json.load(open("data/humanevalpack_python.json"))
def lines(s): return ast.unparse(ast.parse(s)).splitlines()
def edit(a, b): return sum(1 for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[0] in "+-" and not l.startswith(("+++", "---")))
def auroc(pos, neg):
    w = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg); return w / (len(pos) * len(neg))
obs = {t["task"]: t.get("observable") for t in json.load(open("P06_hep_observability.json"))["tasks"]}
ch, eq, ch_obs, eq_obs = [], [], [], []
for r in rows:
    tid = r["task_id"].split("/")[1]; c = r["declaration"] + r["canonical_solution"]; b = r["declaration"] + r["buggy_solution"]
    m = open(f"data/hep_min/{tid}_min.py").read()
    e1 = edit(lines(c), lines(b)); e2 = edit(lines(c), lines(m)); ch.append(e1); eq.append(e2)
    if obs[tid]: ch_obs.append(e1); eq_obs.append(e2)
def q(v, p): v = sorted(v); return v[int(p * (len(v) - 1))]
out = {"n": len(rows), "CH_edit": {"median": q(ch, .5), "q25": q(ch, .25), "q75": q(ch, .75), "frac_le2": sum(x <= 2 for x in ch) / len(ch)},
       "EQ_minifier_edit": {"median": q(eq, .5), "q25": q(eq, .25), "q75": q(eq, .75), "frac_le2": sum(x <= 2 for x in eq) / len(eq), "frac_0": sum(x == 0 for x in eq) / len(eq)},
       "edit_size_AUROC_forward(CH larger => CH)": round(auroc(ch, eq), 4), "edit_size_AUROC_reversed": round(1 - auroc(ch, eq), 4),
       "observable_subset": {"n": len(ch_obs), "AUROC_forward": round(auroc(ch_obs, eq_obs), 4), "AUROC_reversed": round(1 - auroc(ch_obs, eq_obs), 4), "CH_median": S.median(ch_obs), "EQ_median": S.median(eq_obs)}}
json.dump(out, open("P11_hep_editsize.json", "w"), indent=1); print(json.dumps(out, indent=1))
