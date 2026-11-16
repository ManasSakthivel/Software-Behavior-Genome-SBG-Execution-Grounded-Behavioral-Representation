#!/usr/bin/env python3
"""EXP-A3-009: mutation-aware re-execution of the V9c-val CHANGED pairs without a visible return/exception/stdout difference (EXP-A3-008) and
of the 16 EQUIVALENT pairs with differing outputs; plus a no-op test (variant AST identical to base AST after normalisation).
Own harness (_exec_probe.py), fresh interpreter per file, 5 s alarm per input. Writes only PKG/results/*/EXP-A3-009*."""
import ast, collections, csv, gzip, hashlib, json, pathlib, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import a3lib as L
HERE = pathlib.Path(__file__).resolve().parent
RAW = L.PKG / "results/raw/EXP-A3-009"; RAW.mkdir(parents=True, exist_ok=True)

def probe(path, entry, inputs):
    o = subprocess.run([sys.executable, str(HERE / "_exec_probe.py"), str(L.REPO / path), entry, json.dumps(inputs)], capture_output=True, text=True, timeout=120,
                       env={"PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"})
    try: return json.loads(o.stdout)
    except Exception: return {"probe_error": o.stderr[-200:]}

def astnorm(path):
    return ast.dump(ast.parse((L.REPO / path).read_text()))

def trace_rec(base_id, path):
    for root in (L.PKG / "results/raw/trace_cache", L.PKG / "results/raw/EXP-A3-005/trace_cache"):
        d = root / "v9c_val" / base_id
        fn = d / (hashlib.sha1(path.encode()).hexdigest()[:12] + "__" + pathlib.Path(path).stem + ".json.gz")
        if fn.exists(): return json.load(gzip.open(fn, "rt"))

rows = json.loads((L.PKG / "results/raw/EXP-A3-008/v9c_val_pair_level.json").read_text())
meta = {m["pair_id"]: m for m in L.jl(L.V9D / "pairs_val.jsonl")}
for m in list(meta.values()): pass
v8 = {m["pair_id"]: m for m in L.jl(L.V8D / "pairs_val.jsonl")}
meta.update({k: v for k, v in v8.items()})
targets = [r for r in rows if r.get("cmp") and r["in_primary"] and ((r["label"] == 1 and r["cmp"]["any_strict"] == 0) or (r["label"] == 0 and r["cmp"]["any_strict"] > 0))]
res = []
for r in targets:
    m = meta[r["pair_id"]]
    brec = trace_rec(r["base_id"], m["base_path"]); vrec = trace_rec(r["base_id"], m["variant_path"])
    inputs = [t["input"] for t in brec["sandbox"]["traces"]]
    pb = probe(m["base_path"], brec["entry_function"], inputs); pv = probe(m["variant_path"], vrec["entry_function"], inputs)
    noop = astnorm(m["base_path"]) == astnorm(m["variant_path"])
    if isinstance(pb, list) and isinstance(pv, list):
        n_ret = sum(1 for a, b in zip(pb, pv) if a[:2] != b[:2]); n_mut = sum(1 for a, b in zip(pb, pv) if a[2] != b[2]); n_out = sum(1 for a, b in zip(pb, pv) if a[3] != b[3])
        n_any = sum(1 for a, b in zip(pb, pv) if a != b); st = "ok"
    else:
        n_ret = n_mut = n_out = n_any = -1; st = f"probe_failed base={str(pb)[:60]} var={str(pv)[:60]}"
    res.append({"pair_id": r["pair_id"], "label": r["label"], "type": r["type"], "sc": r["sc"], "base_id": r["base_id"], "ast_identical_to_base": noop,
                "n_inputs": len(inputs), "n_ret_exc_diff": n_ret, "n_argmutation_diff": n_mut, "n_stdout_diff": n_out, "n_any_diff": n_any, "status": st})
    print(r["pair_id"], r["label"], noop, n_ret, n_mut, n_out, st, flush=True)
(RAW / "mutation_aware.json").write_text(json.dumps(res, indent=1))
with open(L.PKG / "results/tables/EXP-A3-009_mutation_aware_recheck.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(res[0])); w.writeheader(); w.writerows(res)
ch = [x for x in res if x["label"] == 1]
print("CH_same (ret/exc/stdout) :", len(ch), "| AST-identical to base:", sum(x["ast_identical_to_base"] for x in ch),
      "| differ only via arg mutation:", sum(1 for x in ch if x["n_any_diff"] > 0), "| still no observable diff:", sum(1 for x in ch if x["n_any_diff"] == 0))
print("EQ_diff:", sum(1 for x in res if x["label"] == 0), "| confirmed differing:", sum(1 for x in res if x["label"] == 0 and x["n_any_diff"] > 0))
