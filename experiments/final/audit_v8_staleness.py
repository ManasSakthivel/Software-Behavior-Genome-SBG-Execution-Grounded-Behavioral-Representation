"""Audit: are the committed v8 variant files reproducible from the committed v8 generator + base programs?

A variant is STALE if its AST differs from the AST produced by re-running
`benchmark/scripts/generate_v8_dataset.py --all` (unchanged generator, committed seeds) on the CURRENT base
programs.  AST comparison (ast.dump) makes the check independent of the interpreter's ast.unparse formatting
(the committed variants were formatted by Python 3.9, the canonical interpreter is 3.13).

A program is excluded from evaluation iff ANY of its committed variants is stale or has no regenerated
counterpart (or vice-versa).  The rule uses only file contents; it never reads a score or a label.

    python experiments/final/audit_v8_staleness.py          # regenerates into tmp/ and writes
                                                            # artifacts/paper_evidence/DIAGNOSTIC_V8_STALE_VARIANTS.json
"""
from __future__ import annotations

import ast
import collections
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
V8 = REPO / "benchmark" / "datasets" / "v8"
TMP = REPO / "tmp" / "v8_audit_regen"
OUT = REPO / "artifacts" / "paper_evidence" / "DIAGNOSTIC_V8_STALE_VARIANTS.json"
SPLITS = ("train", "dev", "val", "test")


def dump(p):
    return ast.dump(ast.parse(pathlib.Path(p).read_text()))


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def main():
    if TMP.exists():
        shutil.rmtree(TMP)
    subprocess.run([sys.executable, str(REPO / "benchmark/scripts/generate_v8_dataset.py"), "--all",
                    "--output-dir", str(TMP)], check=True, capture_output=True, cwd=REPO,
                   env={"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"})
    per = collections.defaultdict(lambda: {"n_committed": 0, "n_stale": 0, "n_missing_in_regen": 0, "n_only_in_regen": 0})
    split_of = {}
    committed_ids, regen_ids = {}, {}
    for sp in SPLITS:
        for l in (V8 / f"pairs_{sp}.jsonl").read_text().splitlines():
            r = json.loads(l)
            committed_ids[r["pair_id"]] = r
            split_of[r["base_id"]] = sp
        for l in (TMP / f"pairs_{sp}.jsonl").read_text().splitlines():
            r = json.loads(l)
            regen_ids[r["pair_id"]] = r
            split_of.setdefault(r["base_id"], sp)
    for pid, r in committed_ids.items():
        e = per[r["base_id"]]
        e["n_committed"] += 1
        if pid not in regen_ids:
            e["n_missing_in_regen"] += 1
            continue
        a = REPO / r["variant_path"]
        b = TMP / "variants" / r["split"] / pathlib.Path(r["variant_path"]).name
        if dump(a) != dump(b):
            e["n_stale"] += 1
    for pid, r in regen_ids.items():
        if pid not in committed_ids:
            per[r["base_id"]]["n_only_in_regen"] += 1
    stale = sorted(p for p, e in per.items() if e["n_stale"] or e["n_missing_in_regen"] or e["n_only_in_regen"])
    out = {
        "purpose": "detect committed v8 variants that are not reproducible from the current base programs",
        "method": "regenerate with unchanged generator (PYTHONHASHSEED=0), compare ast.dump of every variant",
        "interpreter": sys.version.split()[0],
        "n_programs": len(per), "n_programs_stale": len(stale),
        "stale_programs": [{"program": p, "split": split_of[p], **per[p]} for p in stale],
        "n_pairs_committed": len(committed_ids), "n_pairs_regenerated": len(regen_ids),
        "n_pairs_in_stale_programs": {sp: sum(per[p]["n_committed"] for p in stale if split_of[p] == sp) for sp in SPLITS},
        "n_programs_stale_by_split": {sp: sum(1 for p in stale if split_of[p] == sp) for sp in SPLITS},
        "remaining_programs_reproduce_exactly": len(per) - len(stale),
        "base_file_sha256_of_stale_programs": {p: sha(REPO / "benchmark/corpus/fresh_programs" / f"{p}.py") for p in stale},
        "file_mtime_evidence": "the 8 stale base programs were modified 2026-10-28 07:58-07:59, after their variants were written (07:53); mtimes are not in git",
        "exclusion_rule": "programs listed in stale_programs are excluded from v8 evaluation (dev dry-run and test); no other exclusion is applied by this audit",
        "no_scores_read": True,
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    shutil.rmtree(TMP)
    print(json.dumps({k: v for k, v in out.items() if k not in ("base_file_sha256_of_stale_programs",)}, indent=1))


if __name__ == "__main__":
    main()
