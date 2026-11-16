#!/usr/bin/env python3
"""A2 independent hash verifier for every file pinned by the SBG freeze / manifest files.

Pure stdlib. READ-ONLY w.r.t. REPO (only reads files and runs read-only `git` commands).
Output: PKG/results/raw/repro/hash_verification.json  and  hash_verification.tsv

Usage:  PYTHONHASHSEED=0 python verify_hashes.py [--repo PATH]   (default: ../SBG)

What it checks
  * every (path, sha256) pair found in the freeze/manifest JSON files (generic walker + explicit maps)
  * 16-hex prefixes in FINAL_EVIDENCE_MANIFEST / FINAL_REPRODUCIBILITY_MANIFEST
  * combined / tree digests (algorithms re-implemented here from experiments/final/external_*.py)
  * for each mismatch: the git history of the file is searched for a revision whose blob hash equals
    the pinned hash (so the mismatch can be explained: "file changed after freeze at commit X")
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve()
PKG = HERE.parents[1]
REPO = PKG.parent / "SBG"
OUT = PKG / "results" / "raw" / "repro"

HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX16 = re.compile(r"^[0-9a-f]{16}$")
PATHLIKE = re.compile(r"^[\w.\-/ ]+\.(py|json|jsonl|md|yaml|yml|txt|csv|cbl|java)$")


def sha256_file(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(*args: str) -> str:
    r = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def git_blob_sha(commit: str, rel: str):
    r = subprocess.run(["git", "-C", str(REPO), "show", f"{commit}:{rel}"], capture_output=True)
    return hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None


# ----------------------------------------------------------------------------------------------
# pin extraction
# ----------------------------------------------------------------------------------------------
PATH_KEYS = ("path", "file", "scored_file", "manifest", "artifact")
HASH_KEYS = ("sha256", "scored_file_sha256", "manifest_sha256")


def walk(node, source, trail, pins):
    if isinstance(node, dict):
        # (a) {relpath: hex64}
        for k, v in node.items():
            if isinstance(v, str) and HEX64.match(v) and isinstance(k, str) and "/" in k and PATHLIKE.match(k):
                pins.append(dict(source=source, trail="/".join(trail + [k]), path=k, expected=v, kind="map"))
        # (b) {path|file|scored_file|manifest|artifact: relpath, sha256|...: hex64}
        paths = [(pk, node[pk]) for pk in PATH_KEYS if isinstance(node.get(pk), str) and "/" in node[pk]
                 and PATHLIKE.match(node[pk])]
        hashes = [(hk, node[hk]) for hk in HASH_KEYS if isinstance(node.get(hk), str) and HEX64.match(node[hk])]
        if paths and hashes:
            # pair path key with the hash key that is its natural partner
            for pk, pv in paths:
                for hk, hv in hashes:
                    natural = {("scored_file", "scored_file_sha256"), ("manifest", "manifest_sha256"),
                               ("path", "sha256"), ("file", "sha256"), ("artifact", "sha256")}
                    if (pk, hk) in natural:
                        pins.append(dict(source=source, trail="/".join(trail + [pk + "+" + hk]), path=pv,
                                         expected=hv, kind="pair"))
        for k, v in node.items():
            walk(v, source, trail + [str(k)], pins)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, source, trail + [str(i)], pins)


def dedupe(pins):
    seen, out = set(), []
    for p in pins:
        key = (p["source"], p["path"], p["expected"])
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def explicit_pins():
    """Hash pins whose path is implied by the key name (not stored) -- mapped by hand from the code/docs."""
    A = "artifacts/final/"
    m = []
    f8 = A + "FREEZE_V8.json"
    for split in ("train", "dev", "val", "test"):
        m.append((f8, f"dataset.pairs_sha256.{split}", f"benchmark/datasets/v8/pairs_{split}.jsonl"))
    m.append((f8, "dataset.manifest_sha256", "benchmark/datasets/v8/manifest.json"))
    m.append((f8, "evaluation_script_sha256", "experiments/final/evaluate_v8.py"))
    f9 = A + "FREEZE_V9.json"
    m += [(f9, "models_sha256", A + "V9_MODELS_FROZEN.json"),
          (f9, "scored_v9c_val_sha256", A + "pairs_v9c_val_output_free_v8.jsonl"),
          (f9, "scored_v8_val_sha256", A + "pairs_v8val_output_free_v8.jsonl"),
          (f9, "evaluation_script_sha256", "experiments/final/evaluate_v9.py"),
          (f9, "dataset.v9c_pairs_val", "benchmark/datasets/v9_composed/pairs_val.jsonl"),
          (f9, "dataset.v9c_manifest", "benchmark/datasets/v9_composed/manifest.json"),
          (f9, "dataset.v8_pairs_val", "benchmark/datasets/v8/pairs_val.jsonl"),
          (f9, "dataset.audit_v9c", A + "BENCHMARK_VALIDITY_AUDIT_V9C.json")]
    m.append((A + "FREEZE_V8_AMENDMENT1.json", "evaluation_script_sha256", "experiments/final/evaluate_v8.py"))
    m.append((A + "FREEZE_V8_AMENDMENT2.json", "evaluation_script_sha256", "experiments/final/evaluate_v8.py"))
    m.append((A + "FREEZE_V8_AMENDMENT2.json", "run_chunked_sha256", "experiments/final/run_chunked.py"))
    m.append((A + "freeze_threshold.json", "records.0.dev_scored_pair_file_sha256", A + "pairs_v6dev_output_free_v7.jsonl"))
    return m


def getpath(d, dotted):
    cur = d
    for part in dotted.split("."):
        cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    return cur


# ----------------------------------------------------------------------------------------------
def tree_candidates(dirpath: pathlib.Path, files):
    """Candidate algorithms for the undocumented 'variants_tree_sha256' / 'base_programs_tree_sha256'."""
    out = {}
    rels = sorted(files)
    # T1: rel path bytes + content
    h = hashlib.sha256()
    for r in rels:
        h.update(r.encode()); h.update((dirpath / r).read_bytes())
    out["T1 path+content"] = h.hexdigest()
    # T2: path \0 content \0
    h = hashlib.sha256()
    for r in rels:
        h.update(r.encode()); h.update(b"\0"); h.update((dirpath / r).read_bytes()); h.update(b"\0")
    out["T2 path\\0content\\0"] = h.hexdigest()
    # T3: sha256 over lines "relpath filehash"
    lines = [f"{r} {sha256_file(dirpath / r)}" for r in rels]
    out["T3 'path hash' newline-joined"] = hashlib.sha256("\n".join(lines).encode()).hexdigest()
    out["T3b 'path hash' + trailing newline"] = hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest()
    lines2 = [f"{sha256_file(dirpath / r)}  {r}" for r in rels]
    out["T4 'hash  path' newline-joined"] = hashlib.sha256("\n".join(lines2).encode()).hexdigest()
    h = hashlib.sha256()
    for r in rels:
        h.update(sha256_file(dirpath / r).encode())
    out["T5 concat of file hashes"] = h.hexdigest()
    h = hashlib.sha256()
    for r in rels:
        h.update(r.encode()); h.update(sha256_file(dirpath / r).encode())
    out["T6 path+filehash"] = h.hexdigest()
    h = hashlib.sha256()
    for r in rels:
        h.update(r.encode()); h.update(b"\n"); h.update((dirpath / r).read_bytes())
    out["T7 path\\ncontent"] = h.hexdigest()
    out["T8 sha256(json list [rel,hash])"] = hashlib.sha256(
        json.dumps([[r, sha256_file(dirpath / r)] for r in rels]).encode()).hexdigest()
    h = hashlib.sha256()          # T10: path \0 content (no trailing separator) -- the algorithm that reproduces FREEZE_V8 (found by hand)
    for r in rels:
        h.update(r.encode()); h.update(b"\0"); h.update((dirpath / r).read_bytes())
    out["T10 path\\0content (VERIFIED for FREEZE_V8 trees)"] = h.hexdigest()
    out["T9 sha256(json dict sorted)"] = hashlib.sha256(
        json.dumps({r: sha256_file(dirpath / r) for r in rels}, sort_keys=True).encode()).hexdigest()
    return out


def main():
    global REPO
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(REPO))
    a = ap.parse_args()
    REPO = pathlib.Path(a.repo).resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    head = git("rev-parse", "HEAD").strip()

    sources = [
        "artifacts/final/FREEZE_V8.json", "artifacts/final/FREEZE_V8_AMENDMENT1.json",
        "artifacts/final/FREEZE_V8_AMENDMENT2.json", "artifacts/final/FREEZE_V9.json",
        "artifacts/final/FREEZE_V10.json", "artifacts/final/FREEZE_V10_SCORED.json",
        "artifacts/final/PHASE2_FREEZE.json", "artifacts/final/freeze_threshold.json",
        "artifacts/final/freeze_handoff.json", "artifacts/final/freeze_bugsinpy.json",
        "artifacts/final/freeze_quixbugs.json",
        "artifacts/paper_evidence/EXPERIMENT_MANIFEST_V4.json",
        "artifacts/paper_evidence/EXPERIMENT_MANIFEST_V3.json",
        "artifacts/paper_evidence/EXPERIMENT_MANIFEST.json",
        "artifacts/final/ARTIFACT_PROVENANCE.json",
    ]
    pins = []
    for s in sources:
        p = REPO / s
        if not p.exists():
            pins.append(dict(source=s, trail="(source file)", path=s, expected=None, kind="source-missing"))
            continue
        walk(json.loads(p.read_text()), s, [], pins)
    pins = dedupe(pins)
    # explicit
    for src, dotted, path in explicit_pins():
        try:
            exp = getpath(json.loads((REPO / src).read_text()), dotted)
        except Exception as e:  # noqa: BLE001
            pins.append(dict(source=src, trail=dotted, path=path, expected=None, kind=f"explicit-error {e}"))
            continue
        pins.append(dict(source=src, trail=dotted, path=path, expected=exp, kind="explicit"))

    rows = []
    for p in pins:
        row = dict(p)
        fp = REPO / p["path"]
        row["exists_worktree"] = fp.exists()
        row["actual_worktree"] = sha256_file(fp) if fp.is_file() else None
        row["actual_HEAD"] = git_blob_sha("HEAD", p["path"])
        row["tracked_in_HEAD"] = row["actual_HEAD"] is not None
        if p["expected"] is None:
            row["status"] = "NO-PIN"
        elif row["actual_worktree"] is None:
            row["status"] = "MISSING"
        elif row["actual_worktree"] == p["expected"]:
            row["status"] = "MATCH"
        else:
            row["status"] = "MISMATCH"
        rows.append(row)

    # explain mismatches via git history
    for row in rows:
        if row["status"] in ("MISMATCH", "MISSING"):
            hist = git("log", "--format=%H %h %ad %s", "--date=short", "--", row["path"]).splitlines()
            row["git_history"] = []
            row["matches_at"] = []
            for ln in hist[:40]:
                full = ln.split(" ", 1)[0]
                b = git_blob_sha(full, row["path"])
                tag = "==pinned" if b == row["expected"] else ""
                row["git_history"].append(ln[:100] + (" " + tag if tag else ""))
                if tag:
                    row["matches_at"].append(ln.split(" ")[1])
            # if never matches, test whether the working-tree file hash is a different blob
    # ---- combined / tree digests -------------------------------------------------------------
    digests = []
    # BugsInPy combined: sha256("".join(f"{k}\0{v}\n" for sorted(per_file)))
    fb = json.loads((REPO / "artifacts/final/freeze_bugsinpy.json").read_text())
    per = fb["files"]
    comb = hashlib.sha256("".join(f"{k}\0{v}\n" for k, v in sorted(per.items())).encode()).hexdigest()
    digests.append(dict(name="freeze_bugsinpy.combined_sha256 (recomputed from the pinned per-file hashes)",
                        expected=fb["combined_sha256"], actual=comb, ok=comb == fb["combined_sha256"]))
    live = {k: (sha256_file(REPO / k) if (REPO / k).is_file() else "MISSING") for k in per}
    comb2 = hashlib.sha256("".join(f"{k}\0{v}\n" for k, v in sorted(live.items())).encode()).hexdigest()
    digests.append(dict(name="freeze_bugsinpy.combined_sha256 (recomputed from LIVE files)",
                        expected=fb["combined_sha256"], actual=comb2, ok=comb2 == fb["combined_sha256"]))
    fq = json.loads((REPO / "artifacts/final/freeze_quixbugs.json").read_text())
    neg = fq["negatives"]["files"]
    live = {k: (sha256_file(REPO / k) if (REPO / k).is_file() else "MISSING") for k in neg}
    cq = hashlib.sha256("\n".join(f"{k} {v}" for k, v in sorted(live.items())).encode()).hexdigest()
    digests.append(dict(name="freeze_quixbugs.negatives.combined_sha256 (LIVE)",
                        expected=fq["negatives"]["combined_sha256"], actual=cq,
                        ok=cq == fq["negatives"]["combined_sha256"]))
    # tree hashes of variant dirs
    tree_specs = [
        ("FREEZE_V8.variants_tree_sha256", "artifacts/final/FREEZE_V8.json", "dataset.variants_tree_sha256", "benchmark/datasets/v8/variants"),
        ("FREEZE_V8.base_programs_tree_sha256", "artifacts/final/FREEZE_V8.json", "dataset.base_programs_tree_sha256", "benchmark/corpus/fresh_programs"),
        ("FREEZE_V10.variants_tree_sha256", "artifacts/final/FREEZE_V10.json", "variants_tree_sha256", "benchmark/datasets/v10_independent/variants"),
    ]
    for name, src, dotted, d in tree_specs:
        exp = getpath(json.loads((REPO / src).read_text()), dotted)
        dp = REPO / d
        tracked = [l[len(d) + 1:] for l in git("ls-files", d).splitlines()]
        pyonly = [t for t in tracked if t.endswith(".py")]
        hit, nfiles = [], {}
        for setname, files in (("tracked", tracked), ("tracked *.py", pyonly)):
            nfiles[setname] = len(files)
            if not files:
                continue
            for k, v in tree_candidates(dp, files).items():
                if v == exp:
                    hit.append(f"{setname}: {k}")
        digests.append(dict(name=name, expected=exp, n_files=nfiles, algorithm_found=hit or None,
                            ok=bool(hit), note="algorithm is not documented in code; candidates T1-T9 tried"))
    # 16-hex prefixes
    prefix_rows = []
    for src, key in (("artifacts/final/FINAL_REPRODUCIBILITY_MANIFEST.json", "artifact_hash_manifest"),):
        d = json.loads((REPO / src).read_text())[key]
        for path, pref in d.items():
            fp = REPO / path
            act = sha256_file(fp) if fp.is_file() else None
            prefix_rows.append(dict(source=src, path=path, expected_prefix=pref, actual_prefix=act[:16] if act else None,
                                    status="MATCH" if act and act[:16] == pref else ("MISSING" if not act else "MISMATCH")))
    d = json.loads((REPO / "artifacts/final/FINAL_EVIDENCE_MANIFEST.json").read_text())
    for it in d["artifacts"]:
        fp = REPO / it["path"]
        act = sha256_file(fp) if fp.is_file() else None
        prefix_rows.append(dict(source="artifacts/final/FINAL_EVIDENCE_MANIFEST.json", path=it["path"],
                                expected_prefix=it["sha256_prefix"], actual_prefix=act[:16] if act else None,
                                expected_size=it.get("size_bytes"), actual_size=fp.stat().st_size if act else None,
                                status="MATCH" if act and act[:16] == it["sha256_prefix"] else ("MISSING" if not act else "MISMATCH")))
    # ARTIFACT_PROVENANCE: sha256 + bytes of each entry
    prov = json.loads((REPO / "artifacts/final/ARTIFACT_PROVENANCE.json").read_text())["artifacts"]
    for path, rec in prov.items():
        fp = REPO / path
        act = sha256_file(fp) if fp.is_file() else None
        row = dict(path=path, expected=rec.get("sha256"), actual=act, status_label=rec.get("status"),
                   expected_bytes=rec.get("bytes"), actual_bytes=fp.stat().st_size if act else None)
        row["status"] = "MATCH" if act and act == rec.get("sha256") else ("MISSING" if not act else "MISMATCH")
        prefix_rows.append(dict(source="artifacts/final/ARTIFACT_PROVENANCE.json (already in walker)", **{
            "path": path, "expected_prefix": (rec.get("sha256") or "")[:16], "actual_prefix": act[:16] if act else None,
            "status": row["status"]}))

    # ---- summary ------------------------------------------------------------------------------
    from collections import Counter
    by_src = {}
    for r in rows:
        by_src.setdefault(r["source"], Counter())[r["status"]] += 1
    summary = dict(repo=str(REPO), head=head, n_pins=len(rows),
                   totals=dict(Counter(r["status"] for r in rows)),
                   by_source={k: dict(v) for k, v in sorted(by_src.items())},
                   digests=digests,
                   prefix_totals=dict(Counter(r["status"] for r in prefix_rows)))
    (OUT / "hash_verification.json").write_text(json.dumps(dict(summary=summary, rows=rows, prefix_rows=prefix_rows), indent=1))
    with open(OUT / "hash_verification.tsv", "w") as f:
        f.write("source\ttrail\tpath\tstatus\texpected\tactual_worktree\tactual_HEAD\tmatches_at\n")
        for r in rows:
            f.write("\t".join(str(x) for x in (r["source"], r["trail"], r["path"], r["status"], r["expected"],
                                               r["actual_worktree"], r["actual_HEAD"], ",".join(r.get("matches_at", [])))) + "\n")
    print(json.dumps(summary, indent=1))
    print("\nMISMATCH / MISSING rows:")
    for r in rows:
        if r["status"] in ("MISMATCH", "MISSING"):
            print(f"  [{r['status']}] {r['source']} :: {r['trail']}\n      path={r['path']}\n"
                  f"      expected={r['expected']}\n      actual  ={r['actual_worktree']}\n      matches_at={r.get('matches_at')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
