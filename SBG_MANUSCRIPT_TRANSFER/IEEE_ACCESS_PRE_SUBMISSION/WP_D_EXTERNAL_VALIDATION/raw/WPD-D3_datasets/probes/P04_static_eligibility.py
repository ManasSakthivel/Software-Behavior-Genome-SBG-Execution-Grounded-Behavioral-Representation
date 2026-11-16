#!/usr/bin/env python3
"""P04: STATIC (ast-only, no execution of dataset code, no SBG scoring) eligibility probe against SBG's frozen entry-selection rule.
Imports the frozen rule `SBG/experiments/final/protocol.py` read-only (pure ast/typing module; PYTHONDONTWRITEBYTECODE=1) by path,
and records its sha256. Run: PYTHONDONTWRITEBYTECODE=1 python3 P04_static_eligibility.py
Outputs: P04_static_refactory.json, P04_static_humanevalpack.json"""
import ast, sys, json, os, glob, hashlib, importlib.util, collections
sys.dont_write_bytecode = True
PROT = "/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/experiments/final/protocol.py"
spec = importlib.util.spec_from_file_location("sbg_protocol_ro", PROT); P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
prot_sha = hashlib.sha256(open(PROT, "rb").read()).hexdigest()
STD = set(sys.stdlib_module_names)
def imports(tree):
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import): mods |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0: mods.add(n.module.split(".")[0])
    return mods
def entry(src):
    """Replicates select_entry_output_free's selection (static part only)."""
    try: tree = ast.parse(src)
    except SyntaxError as e: return {"status": "syntax_error", "err": str(e)[:80]}
    cands = P.eligible_candidates(tree)
    mods = imports(tree)
    nonstd = sorted(m for m in mods if m not in STD)
    fam = {}
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and not P._is_scaffolding(n.name):
            fam[n.name] = [P.annotation_family(a) for a in P._function_signature(n)]
    if not cands: return {"status": "no_synthesisable_candidate", "nonstd_imports": nonstd, "families": fam}
    by = {c[0]: c for c in cands}
    chosen = next((p for p in P.PRIORITY_NAMES if p in by), None)
    tier = "priority" if chosen else None
    if not chosen:
        for ann_only in (True, False):
            for nm in sorted(by):
                if by[nm][2] is ann_only: chosen = nm; tier = "annotated" if ann_only else "unannotated"; break
            if chosen: break
    return {"status": "eligible", "entry": chosen, "tier": tier, "annotated": by[chosen][2], "families": fam.get(chosen), "nonstd_imports": nonstd, "n_toplevel_funcs": len(fam)}
# ---------- Refactory ----------
R = {"protocol_sha256": prot_sha, "questions": {}}
for q in sorted(glob.glob("data/refactory/data/question_*")):
    qn = os.path.basename(q); rec = {}
    for kind in ("reference", "correct", "wrong"):
        files = sorted(glob.glob(f"{q}/code/{kind}/*.py")); st = collections.Counter(); fams = collections.Counter(); ents = collections.Counter(); ann = collections.Counter(); sizes = []
        for f in files:
            src = open(f, errors="replace").read(); e = entry(src); st[e["status"]] += 1; sizes.append(len(src.splitlines()))
            if e["status"] == "eligible": fams[json.dumps(e["families"])] += 1; ents[e["entry"]] += 1; ann[e["annotated"]] += 1
        rec[kind] = {"n": len(files), "status": dict(st), "entries": dict(ents.most_common(5)), "families": dict(fams.most_common(4)), "annotated": {str(k): v for k, v in ann.items()}, "median_loc": sorted(sizes)[len(sizes)//2] if sizes else None}
    R["questions"][qn] = rec
    ref = glob.glob(f"{q}/code/reference/*.py")
    if ref: rec["reference_src_head"] = open(ref[0]).read()[:400]
    rec["n_ans_files"] = len(glob.glob(f"{q}/ans/*"))
json.dump(R, open("P04_static_refactory.json", "w"), indent=1)
print("REFACTORY"); 
for q, r in R["questions"].items(): print(q, {k: (v["n"], v["status"], v["families"]) for k, v in r.items() if isinstance(v, dict)}, "ans_files", r["n_ans_files"])
# ---------- HumanEvalPack ----------
rows = json.load(open("data/humanevalpack_python.json")); H = {"protocol_sha256": prot_sha, "n_rows": len(rows), "tasks": []}
st = collections.Counter(); fam_ctr = collections.Counter(); nonstd_ctr = collections.Counter()
for r in rows:
    decl = r["declaration"]; 
    out = {"task_id": r["task_id"], "entry_point": r["entry_point"], "bug_type": r["bug_type"], "failure_symptoms": r["failure_symptoms"]}
    for kind, body in (("canonical", r["canonical_solution"]), ("buggy", r["buggy_solution"])):
        src = r["import"] and "" or ""
        full = decl + body
        e = entry(full); out[kind] = {k: v for k, v in e.items() if k != "families"}; out[kind]["entry_families"] = (e.get("families") or {}).get(r["entry_point"]) if isinstance(e.get("families"), dict) else e.get("families")
    # which function would SBG select, same on both versions?
    out["same_entry"] = out["canonical"].get("entry") == out["buggy"].get("entry")
    out["selected_is_target"] = out["canonical"].get("entry") == r["entry_point"] and out["buggy"].get("entry") == r["entry_point"]
    st[(out["canonical"]["status"], out["buggy"]["status"])] += 1
    fam_ctr[json.dumps(out["canonical"].get("entry_families"))] += 1
    for m in out["canonical"].get("nonstd_imports", []): nonstd_ctr[m] += 1
    H["tasks"].append(out)
H["status_pairs"] = {str(k): v for k, v in st.items()}; H["families_selected_entry"] = dict(fam_ctr.most_common()); H["nonstd"] = dict(nonstd_ctr)
H["n_selected_is_target"] = sum(t["selected_is_target"] for t in H["tasks"]); H["n_same_entry"] = sum(t["same_entry"] for t in H["tasks"])
H["bug_types"] = dict(collections.Counter(t["bug_type"] for t in H["tasks"]))
json.dump(H, open("P04_static_humanevalpack.json", "w"), indent=1)
print("HEP", H["status_pairs"], "selected_is_target", H["n_selected_is_target"], "same_entry", H["n_same_entry"]); print(H["families_selected_entry"]); print(H["nonstd"]); print(H["bug_types"])
