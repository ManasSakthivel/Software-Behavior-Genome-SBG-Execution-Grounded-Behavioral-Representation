#!/usr/bin/env python3
"""P14: label-only STATIC shortcut check on SeqCoBench's observability-validated pairs (P13 classes SP_ok/CH_ok). How well do trivial static features separate CH from SP?
Features (all computed from source text only; no execution outputs beyond the validated label, NO SBG):
  tok_bag  = L1 distance between token multisets (tokenize, ignoring NL/COMMENT/INDENT/DEDENT)
  ast_bag  = L1 distance between multisets of ast node-type names
  edit     = repo edit size (ast.unparse unified diff changed lines)
Reported: AUROC (CH positive; higher feature => CH) pooled and within e<=2 stratum, with program-cluster bootstrap CI (B=1000,seed 42; descriptive only).
"""
import json, collections, io, tokenize, ast, random
O = {}
for l in open("P10_seqco_outcomes.jsonl"):
    o = json.loads(l); O[o["file"]] = o
rows = [json.loads(l) for l in open("data/seqco_rows.jsonl")]
def toks(s):
    try: return collections.Counter((t.type, t.string) for t in tokenize.generate_tokens(io.StringIO(s).readline) if t.type not in (tokenize.NL, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE, tokenize.ENDMARKER))
    except Exception: return None
def astbag(s):
    try: return collections.Counter(type(n).__name__ for n in ast.walk(ast.parse(s)))
    except Exception: return None
def l1(a, b): return sum(abs(a[k] - b[k]) for k in set(a) | set(b))
keep = []
for r in rows:
    a, b = O[r["orig"]], O[r["var"]]
    if a["status"] != "ok" or b["status"] != "ok" or a["entry"] != b["entry"] or r["ast_identical"] or all(x[0] != "ret" for x in a["outcomes"]): continue
    differ = a["outcomes"] != b["outcomes"]; sbg = 1 - r["label_seqco"]
    if sbg == 0 and differ: continue     # label noise
    if sbg == 1 and not differ: continue # unobservable
    so, sv = open(r["orig"]).read(), open(r["var"]).read(); t1, t2, a1, a2 = toks(so), toks(sv), astbag(so), astbag(sv)
    if None in (t1, t2, a1, a2): continue
    keep.append({"y": sbg, "prog": r["orig_hash"], "edit": r["edit"], "tok_bag": l1(t1, t2), "ast_bag": l1(a1, a2), "T": r["transformation"]})
def auroc(pairs):
    """tie-aware AUROC via average ranks (O(n log n))."""
    n1 = sum(1 for y, _ in pairs if y == 1); n0 = len(pairs) - n1
    if not n1 or not n0: return None
    srt = sorted(pairs, key=lambda p: p[1]); ranks = {}; i = 0; rsum = 0.0
    while i < len(srt):
        j = i
        while j + 1 < len(srt) and srt[j + 1][1] == srt[i][1]: j += 1
        avg = (i + j) / 2 + 1
        rsum += avg * sum(1 for k in range(i, j + 1) if srt[k][0] == 1); i = j + 1
    return (rsum - n1 * (n1 + 1) / 2) / (n1 * n0)
def boot(rs, feat, B=1000):
    progs = collections.defaultdict(list)
    for r in rs: progs[r["prog"]].append(r)
    keys = list(progs); rnd = random.Random(42); v = []
    for _ in range(B):
        samp = [x for k in (rnd.choice(keys) for _ in keys) for x in progs[k]]
        a = auroc([(x["y"], x[feat]) for x in samp])
        if a is not None: v.append(a)
    v.sort(); return [round(v[int(.025 * len(v))], 4), round(v[int(.975 * len(v))], 4)]
res = {"n_pairs": len(keep), "n_SP": sum(r["y"] == 0 for r in keep), "n_CH": sum(r["y"] == 1 for r in keep)}
for name, sel in (("pooled", lambda r: True), ("e_le_2", lambda r: r["edit"] is not None and r["edit"] <= 2)):
    rs = [r for r in keep if sel(r)]; res[name] = {"n": len(rs), "n_progs": len({r["prog"] for r in rs})}
    for f in ("tok_bag", "ast_bag", "edit"):
        res[name][f] = {"AUROC": round(auroc([(r["y"], r[f]) for r in rs]), 4), "CI95_cluster": boot(rs, f)}
res["e_le_2_composition"] = {"SP": dict(collections.Counter(r["T"] for r in keep if r["y"] == 0 and r["edit"] is not None and r["edit"] <= 2)), "CH": dict(collections.Counter(r["T"] for r in keep if r["y"] == 1 and r["edit"] is not None and r["edit"] <= 2))}
json.dump(res, open("P14_seqco_static_shortcut.json", "w"), indent=1); print(json.dumps(res, indent=1))
