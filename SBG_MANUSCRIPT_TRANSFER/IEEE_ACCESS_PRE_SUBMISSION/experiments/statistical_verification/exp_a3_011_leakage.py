#!/usr/bin/env python3
"""EXP-A3-011: train/test leakage and novelty.
 (a) program overlap by base_id / file sha256 / normalised-AST hash between V10-test and V9c train/dev/val and V8 train/dev/val/test (+ variant-level AST overlap)
 (b) own-tokenizer similarity of each V10 base program against ALL reference programs; four measures:
     J_repo  : identifier-set Jaccard (len>=3, repo-style stop list extracted from validate_fresh_program.py by ast.literal_eval, not imported)
     J_ident : identifier-set Jaccard, only Python keywords+builtins removed (len>=2)
     J_5gram : Jaccard of 5-gram shingles of the lexical token stream with identifiers/numbers/strings abstracted (structure clone detection)
     J_ast3  : Jaccard of preorder AST node-type 3-grams (rename/format-invariant structure)
 reference groups: V9c-train/dev/val bases, V8-test bases, corpus/base_programs, other fresh_programs, BugsInPy units (fixed+buggy), QuixBugs (correct+buggy)
  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python exp_a3_011_leakage.py
"""
import ast, builtins, collections, csv, hashlib, io, json, keyword, pathlib, re, sys, tokenize
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import a3lib as L
RAW = L.PKG / "results/raw/EXP-A3-011"; RAW.mkdir(parents=True, exist_ok=True); TAB = L.PKG / "results/tables"
R = L.REPO

def stop_from_repo():
    src = (R / "benchmark/scripts/validate_fresh_program.py").read_text()
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "_STOP_WORDS":
            return {e.value for e in node.value.args[0].elts}
STOP_REPO = stop_from_repo()
STOP_MIN = set(keyword.kwlist) | set(dir(builtins))
IDRE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

def j(a, b):
    return len(a & b) / len(a | b) if (a or b) else 0.0

def feats(src):
    ids = IDRE.findall(src)
    f = {"repo": {t for t in ids if t not in STOP_REPO and len(t) >= 3}, "ident": {t for t in ids if t not in STOP_MIN and len(t) >= 2}}
    toks = []
    try:
        for t in tokenize.generate_tokens(io.StringIO(src).readline):
            if t.type == tokenize.NAME: toks.append(t.string if keyword.iskeyword(t.string) else "N")
            elif t.type == tokenize.NUMBER: toks.append("0")
            elif t.type == tokenize.STRING: toks.append("S")
            elif t.type == tokenize.OP: toks.append(t.string)
    except Exception: pass
    f["g5"] = {tuple(toks[i:i + 5]) for i in range(max(0, len(toks) - 4))}
    seq = []
    try:
        for n in ast.walk(ast.parse(src)): seq.append(type(n).__name__)
    except SyntaxError: pass
    # ast.walk is BFS; use explicit preorder for determinism of structure
    seq = []
    def pre(n):
        seq.append(type(n).__name__)
        for c in ast.iter_child_nodes(n): pre(c)
    try: pre(ast.parse(src))
    except SyntaxError: pass
    f["a3"] = {tuple(seq[i:i + 3]) for i in range(max(0, len(seq) - 2))}
    return f

def ahash(src):
    try: return hashlib.sha256(ast.dump(ast.parse(src)).encode()).hexdigest()
    except SyntaxError: return None

meta10 = L.jl(L.V10D / "pairs_test.jsonl")
v10_progs = sorted({m["base_id"]: m["base_path"] for m in meta10}.items())
refs = {}                       # name -> (group, path)
def add(group, name, path):
    refs[f"{group}:{name}"] = (group, path)
for split in ("train", "dev", "val"):
    for m in L.jl(L.V9D / f"pairs_{split}.jsonl"): add(f"V9c-{split}", m["base_id"], m["base_path"])
stale = L.stale_programs()
for split in ("train", "dev", "val", "test"):
    for m in L.jl(L.V8D / f"pairs_{split}.jsonl"): add(f"V8-{split}", m["base_id"], m["base_path"])
for p in sorted((R / "benchmark/corpus/base_programs").glob("*.py")): add("corpus/base_programs", p.stem, str(p.relative_to(R)))
v10_ids = {b for b, _ in v10_progs}
used = {v[1] for v in refs.values()} | {p for _, p in v10_progs}
for p in sorted((R / "benchmark/corpus/fresh_programs").glob("*.py")):
    if str(p.relative_to(R)) not in used: add("fresh_programs:unused-by-V8/V9/V10", p.stem, str(p.relative_to(R)))
for d in sorted((R / "external/bugsinpy/units").glob("*")):
    for fn in ("fixed.py", "buggy.py"):
        if (d / fn).exists(): add("BugsInPy", f"{d.name}/{fn}", str((d / fn).relative_to(R)))
for sub in ("python_programs", "correct_python_programs"):
    for p in sorted((R / "external/quixbugs" / sub).glob("*.py")): add("QuixBugs", f"{sub}/{p.stem}", str(p.relative_to(R)))
F = {}
def fe(path):
    if path not in F:
        src = (R / path).read_text(); F[path] = (feats(src), ahash(src), hashlib.sha256(src.encode()).hexdigest())
    return F[path]
# ---------------------------------------------------------------- (a) overlap
ov = {}
v10_by_id = dict(v10_progs)
for name, grp_prefix in (("V9c", "V9c-"), ("V8", "V8-")):
    gref = {k: v for k, v in refs.items() if v[0].startswith(grp_prefix)}
    ids = {k.split(":", 1)[1] for k in gref}
    byte = {fe(v[1])[2] for v in gref.values()}; ast_ = {fe(v[1])[1] for v in gref.values()}
    ov[name] = {"n_reference_programs": len(ids), "base_id_overlap_with_V10": sorted(ids & v10_ids),
                "file_sha256_overlap": sorted(b for b, p in v10_progs if fe(p)[2] in byte), "normalised_AST_hash_overlap": sorted(b for b, p in v10_progs if fe(p)[1] in ast_)}
# variant-level AST hash overlap
v10_var = collections.defaultdict(set)
for m in meta10: v10_var[ahash((R / m["variant_path"]).read_text())].add(m["pair_id"])
other_var = {}
for split in ("train", "dev", "val"):
    for m in L.jl(L.V9D / f"pairs_{split}.jsonl"): other_var[ahash((R / m["variant_path"]).read_text())] = m["pair_id"]
for split in ("train", "dev", "val", "test"):
    for m in L.jl(L.V8D / f"pairs_{split}.jsonl"): other_var.setdefault(ahash((R / m["variant_path"]).read_text()), m["pair_id"])
ov["variant_AST_hash_overlap_V10_vs_V8V9"] = sum(1 for h in v10_var if h in other_var)
# ---------------------------------------------------------------- (b) similarity
rows = []; summ = {}
for b, p in v10_progs:
    fb = fe(p)[0]
    best = {}
    for key, (grp, rp) in refs.items():
        if rp == p: continue
        fr = fe(rp)[0]
        for mname in ("repo", "ident", "g5", "a3"):
            s = j(fb[mname], fr[mname])
            for scope in (grp, "ALL", "V9c(any split)" if grp.startswith("V9c-") else None, "V8/V9c(any)" if grp.startswith(("V8-", "V9c-")) else None):
                if scope is None: continue
                k = (mname, scope)
                if k not in best or s > best[k][0]: best[k] = (round(s, 4), key)
    for (mname, scope), (s, who) in sorted(best.items()):
        rows.append({"v10_program": b, "measure": mname, "scope": scope, "max_similarity": s, "most_similar_reference": who})
    summ[b] = {f"{m}|{sc}": best[(m, sc)] for (m, sc) in best if sc in ("ALL", "V9c(any split)", "BugsInPy", "QuixBugs", "V8/V9c(any)")}
with open(TAB / "EXP-A3-011_v10_similarity_per_program.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["v10_program", "measure", "scope", "max_similarity", "most_similar_reference"]); w.writeheader(); w.writerows(rows)
# compact table: per program the max over V8/V9c per measure
compact = []
for b, _ in v10_progs:
    r = {"v10_program": b}
    for m in ("repo", "ident", "g5", "a3"):
        s, who = summ[b][f"{m}|V8/V9c(any)"]; r[f"{m}_max_V8V9c"] = s; r[f"{m}_argmax"] = who
        r[f"{m}_max_ALL"] = summ[b][f"{m}|ALL"][0]
    compact.append(r)
with open(TAB / "EXP-A3-011_v10_similarity_compact.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(compact[0])); w.writeheader(); w.writerows(compact)
stat = {}
for m in ("repo", "ident", "g5", "a3"):
    v = [r[f"{m}_max_V8V9c"] for r in compact]
    stat[m] = {"min": min(v), "median": sorted(v)[len(v) // 2], "max": max(v), "n_gt_0.10": sum(x > 0.10 for x in v), "n_gt_0.15": sum(x > 0.15 for x in v), "n_gt_0.5": sum(x > 0.5 for x in v)}
# similarity of the V9c programs (train vs val) for context: how similar are V8/V9c programs to each other (population baseline)
base_pairs = collections.defaultdict(list)
names = [k for k, v in refs.items() if v[0] in ("V9c-train", "V9c-val", "V9c-dev")]
import itertools
vals = []
for a, bb in itertools.combinations(names, 2):
    if refs[a][1] == refs[bb][1]: continue
    vals.append((j(fe(refs[a][1])[0]["repo"], fe(refs[bb][1])[0]["repo"]), j(fe(refs[a][1])[0]["g5"], fe(refs[bb][1])[0]["g5"])))
vals.sort()
stat["V9c_internal_baseline_repoJ"] = {"pairs": len(vals), "median": vals[len(vals) // 2][0], "p95": sorted(v[0] for v in vals)[int(.95 * len(vals))], "max": max(v[0] for v in vals),
                                      "g5_median": sorted(v[1] for v in vals)[len(vals) // 2], "g5_p95": sorted(v[1] for v in vals)[int(.95 * len(vals))], "g5_max": max(v[1] for v in vals)}
# claim: V10 programs excluded from v8 by Jaccard 0.101-0.146 vs corpus sibling => recompute vs v8 corpus (base_programs + V8/V9c)
rep = {r["name"]: r for r in json.loads((R / "benchmark/corpus/fresh_programs/validation_report.json").read_text())["results"]}
claim = []
for b, _ in v10_progs:
    r = rep.get(b, {})
    claim.append({"v10_program": b, "repo_report_max_jaccard": r.get("max_jaccard"), "repo_report_against": r.get("max_jaccard_against"), "repo_report_eligible": r.get("eligible"),
                  "own_repo_style_max_V8V9c": next(c for c in compact if c["v10_program"] == b)["repo_max_V8V9c"], "own_argmax": next(c for c in compact if c["v10_program"] == b)["repo_argmax"]})
with open(TAB / "EXP-A3-011_v10_novelty_claim_check.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(claim[0])); w.writeheader(); w.writerows(claim)
out = {"overlap": ov, "similarity_summary_V10_vs_V8V9c": stat, "n_reference_programs": len(refs), "n_v10": len(v10_progs), "novelty_claim_rows": claim}
(RAW / "leakage_summary.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(ov, indent=1)); print(json.dumps(stat, indent=1))
for r in compact: print(r["v10_program"], r["repo_max_V8V9c"], r["repo_argmax"], "| g5", r["g5_max_V8V9c"], r["g5_argmax"], "| a3", r["a3_max_V8V9c"], "| ALL g5", r["g5_max_ALL"])
