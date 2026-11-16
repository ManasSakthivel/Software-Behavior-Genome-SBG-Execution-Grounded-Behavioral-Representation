#!/usr/bin/env python3
"""P12: STATIC check (ast only, no execution) of EquiBench OJ_A/OJ_V/OJ_VA (Python competitive-programming pairs; Apache-2.0 repo Anjiang-Wei/EquiBench; arXiv 2502.12466 per README)
against SBG's frozen eligibility rule + 'reads stdin at module level' (I/O-script) flag. Output: P12_equibench_static.json"""
import ast, json, sys, collections, importlib.util
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("p", "/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/experiments/final/protocol.py"); P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
def info(src):
    try: t = ast.parse(src)
    except SyntaxError: return {"syntax": False}
    cands = [c[0] for c in P.eligible_candidates(t)]
    stdin = any((isinstance(n, ast.Attribute) and n.attr in ("stdin",)) or (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "input") for n in ast.walk(t))
    mod_stmts = sum(1 for n in t.body if not isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign)))
    return {"syntax": True, "n_cands": len(cands), "reads_stdin": stdin, "module_level_exec_stmts": mod_stmts}
out = {}
for cat in ("OJ_A", "OJ_V", "OJ_VA"):
    rows = [json.loads(l) for l in open(f"data/equibench/{cat}.jsonl")]; c = collections.Counter(); tl = collections.Counter(str(r["truth_label"]) for r in rows)
    for r in rows:
        a, b = info(r["program_1_code"]), info(r["program_2_code"])
        c["pairs"] += 1; c["both_syntax"] += a["syntax"] and b["syntax"]
        c["both_have_candidate"] += bool(a.get("n_cands")) and bool(b.get("n_cands"))
        c["either_reads_stdin"] += bool(a.get("reads_stdin") or b.get("reads_stdin"))
        c["both_no_stdin_and_candidate"] += bool(a.get("n_cands")) and bool(b.get("n_cands")) and not (a.get("reads_stdin") or b.get("reads_stdin"))
        c["both_no_module_level_exec_and_candidate"] += bool(a.get("n_cands")) and bool(b.get("n_cands")) and a.get("module_level_exec_stmts") == 0 and b.get("module_level_exec_stmts") == 0
    out[cat] = {"truth_label_counts": dict(tl), **c}
json.dump(out, open("P12_equibench_static.json", "w"), indent=1); print(json.dumps(out, indent=1))
