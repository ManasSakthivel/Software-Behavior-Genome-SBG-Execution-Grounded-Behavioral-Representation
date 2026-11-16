#!/usr/bin/env python3
"""WP-D / D1 step 3 -- EXECUTED label-observability / negative-validity oracle on COPIES of the vendored external programs.

Question answered (label compatibility with the SBG task definition, PROTOCOL.md section 2):
  SBG label CHANGED == (return value | exception type | stdout | in-place argument state) differs on the protocol's 11
  synthesised inputs; EQUIVALENT == identical on all of them.
  For every external pair (base=fixed program, variant=buggy program or SP-transformed fixed program) we evaluate that very
  definition, with the V10-style oracle, and tabulate
    * how many REAL-BUG positives are actually CHANGED under that definition (label agreement of positives), and
    * how many SP NEGATIVES are actually CHANGED (invalid negatives -> label noise in the 'EQUIVALENT' class).
  This is NOT an SBG score and is never used to select, tune or exclude anything; it is a label-compatibility audit.

Execution safety: copies of the programs are made under raw/WPD-D1_compat/unit_copies (sha256-verified against SBG/);
each program runs in its own child process (scripts/d1_exec_child.py): temp cwd, CPU/file rlimits, sockets/subprocess stubs,
per-input SIGALRM 1.0 s, hard 120 s wall limit per file.  Nothing is written under SBG/.

PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 venvs/py313/bin/python scripts/d1_03_label_oracle.py [--workers 4]
"""
import argparse
import ast
import concurrent.futures
import csv
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve()
WP = HERE.parents[1]
PKG = WP.parent
REPO = PKG.parent / "SBG"
PY = sys.executable
RAW = WP / "raw" / "WPD-D1_compat"
COPY = RAW / "unit_copies"
ORA = RAW / "oracle"
DATA = RAW / "data"
for d in (COPY, ORA, DATA):
    d.mkdir(parents=True, exist_ok=True)
CHILD = HERE.parent / "d1_exec_child.py"
FILE_TIMEOUT = 120


def jl(p):
    return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def top_funcs(src):
    return [n.name for n in ast.parse(src).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def load_declared_inputs(path):
    """input half only (expected outputs dropped), as SBG's own loader does."""
    ins = []
    for line in pathlib.Path(path).read_text().splitlines():
        if line.strip():
            case = json.loads(line)
            ins.append(case[0])
    return ins


def copy_files(rels):
    n = 0
    for rel in sorted(set(rels)):
        src, dst = REPO / rel, COPY / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or sha(src) != sha(dst):
            shutil.copyfile(src, dst)
        assert sha(src) == sha(dst), rel
        n += 1
    return n


def run_child(args):
    key, argv = args
    out = ORA / f"{key}.json"
    if out.exists():
        return key, json.loads(out.read_text()), 0.0
    env = {"PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1", "D1_SBG_REPO": str(REPO),
           "PATH": "/usr/bin:/bin", "HOME": "/nonexistent"}
    t0 = time.time()
    try:
        p = subprocess.run([PY, str(CHILD)] + argv, capture_output=True, text=True, timeout=FILE_TIMEOUT, env=env,
                           stdin=subprocess.DEVNULL)
        lines = [l for l in p.stdout.splitlines() if l.startswith("@@")]
        if lines:
            rec = json.loads(lines[-1][2:])
        else:
            rec = {"status": "harness_crash", "detail": f"rc={p.returncode} stderr={p.stderr[-300:]}"}
    except subprocess.TimeoutExpired:
        rec = {"status": "file_wall_timeout", "detail": f">{FILE_TIMEOUT}s wall"}
    rec["wall_s"] = round(time.time() - t0, 2)
    out.write_text(json.dumps(rec))
    return key, rec, rec["wall_s"]


def diff_components(a, b):
    """compare two per-input observation lists. Returns (n_differ, comp_counts, n_both_exc_same)."""
    comp = {"status_or_value": 0, "args_after_call": 0, "stdout": 0}
    n = 0
    for x, y in zip(a, b):
        if x != y:
            n += 1
            if x[0] != y[0] or x[1] != y[1]:
                comp["status_or_value"] += 1
            elif x[2] != y[2]:
                comp["args_after_call"] += 1
            else:
                comp["stdout"] += 1
    return n, comp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()

    bp = jl(REPO / "artifacts/final/pairs_bugsinpy_output_free_v7.jsonl")
    qc = jl(REPO / "artifacts/final/pairs_quixbugs_canonical_output_free_v7.jsonl")
    qd = jl(REPO / "artifacts/final/pairs_quixbugs_declared_output_free_v7.jsonl")
    qman = json.loads((REPO / "external/quixbugs/manifest.json").read_text())
    qprog = {p["id"]: p for p in qman["programs"]}

    pairs = []  # (corpus, regime, pair_id, label, transformation, cluster, base_rel, var_rel)
    for r in bp:
        pairs.append(("bugsinpy", "canonical", r["pair_id"], r["label"], r["transformation"], r["bug_id"],
                      r["base_path"], r["variant_path"], r["unit_kind"]))
    for r in qc:
        t = "real_bug" if r["pair_kind"] == "real_bug" else r["pair_kind"].replace("sp_negative:", "")
        pairs.append(("quixbugs", "canonical", r["pair_id"], r["label"], t, r["base_id"], r["base_path"],
                      r["variant_path"], "function"))
    for r in qd:
        t = "real_bug" if r["pair_kind"] == "real_bug" else r["pair_kind"].replace("sp_negative:", "")
        pairs.append(("quixbugs", "declared", r["pair_id"], r["label"], t, r["base_id"], r["base_path"],
                      r["variant_path"], "function"))
    files = sorted({p[6] for p in pairs} | {p[7] for p in pairs})
    n_copied = copy_files(files)
    print(f"copied+verified {n_copied} program files under {COPY.relative_to(WP)}", flush=True)

    # job list
    jobs = []
    for rel in files:
        cp = COPY / rel
        key = "canon__" + hashlib.sha1(rel.encode()).hexdigest()[:16]
        jobs.append((key, ["canonical", str(cp)]))
    # declared jobs: QuixBugs declared pairs (eligible programs only)
    decl_jobs = {}
    for corpus, regime, pid, lab, t, cl, brel, vrel, uk in pairs:
        if regime != "declared":
            continue
        prog = qprog[cl]
        if not prog["eligible"]["declared"]:
            continue
        fixed_src = (REPO / prog["fixed_path"]).read_text()
        fixed_funcs = top_funcs(fixed_src)
        for rel in (brel, vrel):
            src = (REPO / rel).read_text()
            names = top_funcs(src)
            if cl in names:
                ent = cl
            elif cl in fixed_funcs and fixed_funcs.index(cl) < len(names):
                ent = names[fixed_funcs.index(cl)]
            else:
                continue
            inputs_json = RAW / "declared_inputs" / f"{cl}.json"
            inputs_json.parent.mkdir(exist_ok=True)
            if not inputs_json.exists():
                inputs_json.write_text(json.dumps(load_declared_inputs(REPO / prog["declared_inputs"]["file"])))
            key = "decl__" + hashlib.sha1(rel.encode()).hexdigest()[:16]
            decl_jobs[key] = ["declared", str(COPY / rel), ent, str(inputs_json)]
    jobs += list(decl_jobs.items())
    print(f"{len(jobs)} child jobs ({len(decl_jobs)} declared)", flush=True)

    t0 = time.time()
    results = {}
    with concurrent.futures.ThreadPoolExecutor(a.workers) as ex:
        for i, (key, rec, wall) in enumerate(ex.map(run_child, jobs), 1):
            results[key] = rec
            if i % 40 == 0:
                print(f"  {i}/{len(jobs)} done ({time.time()-t0:.0f}s)", flush=True)
    print(f"all child jobs done in {time.time()-t0:.0f}s", flush=True)

    # --------------------------------------------------------------- pair comparison
    def rec_of(rel, regime):
        k = ("canon__" if regime == "canonical" else "decl__") + hashlib.sha1(rel.encode()).hexdigest()[:16]
        return results.get(k)

    out_rows = []
    for corpus, regime, pid, lab, t, cl, brel, vrel, uk in pairs:
        rb, rv = rec_of(brel, regime), rec_of(vrel, regime)
        row = {"corpus": corpus, "regime": regime, "pair_id": pid, "cluster": cl, "label": lab, "transformation": t,
               "unit_kind": uk, "base_status": rb and rb["status"], "variant_status": rv and rv["status"],
               "base_entry": rb and rb.get("entry"), "variant_entry": rv and rv.get("entry"),
               "base_tier": rb and rb.get("tier"),
               "base_n_exc_inputs": None, "base_n_timeouts": rb and rb.get("n_timeouts"),
               "variant_n_timeouts": rv and rv.get("n_timeouts"),
               "n_inputs": None, "n_differ": None, "oracle_changed": None, "n_differ_value_or_exc": None,
               "n_differ_args": None, "n_differ_stdout": None, "oracle_note": ""}
        if rb and rb["status"] == "ok":
            row["base_n_exc_inputs"] = sum(1 for o in rb["obs"] if o[0] == "exc")
            row["base_n_exc_types"] = ";".join(sorted({o[1] for o in rb["obs"] if o[0] == "exc"}))
        if rb and rv and rb["status"] == "ok" and rv["status"] == "ok" and rb["n_inputs"] == rv["n_inputs"]:
            n, comp = diff_components(rb["obs"], rv["obs"])
            row.update(n_inputs=rb["n_inputs"], n_differ=n, oracle_changed=int(n > 0),
                       n_differ_value_or_exc=comp["status_or_value"], n_differ_args=comp["args_after_call"],
                       n_differ_stdout=comp["stdout"])
            if rb["n_timeouts"] or rv["n_timeouts"]:
                row["oracle_note"] = "timeouts present (timeout vs timeout counted as equal)"
        else:
            row["oracle_note"] = (f"not comparable: base={rb and rb['status']} variant={rv and rv['status']}"
                                  f"; entry_base={rb and rb.get('entry')} entry_var={rv and rv.get('entry')}")
        out_rows.append(row)

    cols = list(out_rows[0].keys())
    for r in out_rows:
        for c in r:
            if c not in cols:
                cols.append(c)
    with open(DATA / "label_oracle_pairs.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(out_rows)
    (DATA / "label_oracle_file_records.json").write_text(json.dumps(results, indent=0))
    print("wrote label_oracle_pairs.csv, label_oracle_file_records.json")


if __name__ == "__main__":
    main()
