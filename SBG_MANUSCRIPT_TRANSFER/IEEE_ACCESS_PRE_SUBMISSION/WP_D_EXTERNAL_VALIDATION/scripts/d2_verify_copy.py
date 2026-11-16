#!/usr/bin/env python3
"""WP-D / D2: verify a copy of SBG against the committed freeze files (stdlib only).

    d2_verify_copy.py ROOT OUT_JSON [ORIG_ROOT]

* BugsInPy: recompute per-file SHA-256 of external/bugsinpy/manifest.json + units/**/*.py
  and the combined digest (formula of external_bugsinpy._freeze_digest, re-implemented
  here) and compare with artifacts/final/freeze_bugsinpy.json.
* QuixBugs: manifest sha256, combined digest over external/quixbugs/variants/*.py,
  and combined digest over python_programs/*.py + correct_python_programs/*.py +
  json_testcases/*.json (formula of external_common.hash_files), compared with
  artifacts/final/freeze_quixbugs.json.
* If ORIG_ROOT is given: sha256 of every file in the copy compared with the original
  (excluding __pycache__), reporting missing / extra / differing files.
"""
import hashlib
import json
import os
import pathlib
import sys


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def bugsinpy(root):
    root = pathlib.Path(root)
    fr = json.loads((root / "artifacts/final/freeze_bugsinpy.json").read_text())
    files = [root / "external/bugsinpy/manifest.json"] + sorted(
        (root / "external/bugsinpy/units").rglob("*.py"))
    per = {str(p.relative_to(root)): sha(p) for p in files}
    combined = hashlib.sha256("".join(f"{k}\0{v}\n" for k, v in sorted(per.items())).encode()).hexdigest()
    mism = [k for k in set(per) | set(fr["files"]) if per.get(k) != fr["files"].get(k)]
    return {"frozen_combined": fr["combined_sha256"], "recomputed_combined": combined,
            "combined_match": combined == fr["combined_sha256"],
            "n_files_frozen": fr["n_files"], "n_files_recomputed": len(per),
            "per_file_mismatches": sorted(mism)}


def quixbugs(root):
    root = pathlib.Path(root)
    fr = json.loads((root / "artifacts/final/freeze_quixbugs.json").read_text())

    def hash_files(paths):
        per = {str(p.relative_to(root)): sha(p) for p in paths}
        comb = hashlib.sha256("\n".join(f"{k} {v}" for k, v in sorted(per.items())).encode()).hexdigest()
        return per, comb

    q = root / "external/quixbugs"
    vper, vcomb = hash_files(sorted((q / "variants").glob("*.py")))
    cfiles = sorted(list((q / "python_programs").glob("*.py")) + list((q / "correct_python_programs").glob("*.py"))
                    + list((q / "json_testcases").glob("*.json")))
    cper, ccomb = hash_files(cfiles)
    man = sha(q / "manifest.json")
    vm = sorted(k for k in set(vper) | set(fr["negatives"]["files"]) if vper.get(k) != fr["negatives"]["files"].get(k))
    return {"manifest_sha256_frozen": fr["manifest"]["sha256"], "manifest_sha256_recomputed": man,
            "manifest_match": man == fr["manifest"]["sha256"],
            "negatives_combined_frozen": fr["negatives"]["combined_sha256"], "negatives_combined_recomputed": vcomb,
            "negatives_match": vcomb == fr["negatives"]["combined_sha256"],
            "negatives_n_frozen": fr["negatives"]["n_files"], "negatives_n_recomputed": len(vper),
            "negatives_per_file_mismatches": vm,
            "corpus_combined_frozen": fr["corpus"]["combined_sha256"], "corpus_combined_recomputed": ccomb,
            "corpus_match": ccomb == fr["corpus"]["combined_sha256"],
            "corpus_n_frozen": fr["corpus"]["n_files"], "corpus_n_recomputed": len(cper)}


def tree(root):
    out = {}
    root = pathlib.Path(root)
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d != "__pycache__"]
        for f in fn:
            p = pathlib.Path(dp) / f
            if p.is_symlink() or not p.is_file():
                continue
            out[str(p.relative_to(root))] = sha(p)
    return out


def main():
    root, out = sys.argv[1], sys.argv[2]
    res = {"root": root, "bugsinpy": bugsinpy(root), "quixbugs": quixbugs(root)}
    if len(sys.argv) > 3:
        a, b = tree(sys.argv[3]), tree(root)
        res["tree_compare_vs_original"] = {
            "original_root": sys.argv[3], "n_original": len(a), "n_copy": len(b),
            "missing_in_copy": sorted(set(a) - set(b))[:50], "extra_in_copy": sorted(set(b) - set(a))[:50],
            "n_missing": len(set(a) - set(b)), "n_extra": len(set(b) - set(a)),
            "differing": sorted(k for k in set(a) & set(b) if a[k] != b[k])[:50],
            "n_differing": sum(1 for k in set(a) & set(b) if a[k] != b[k])}
    ok = (res["bugsinpy"]["combined_match"] and not res["bugsinpy"]["per_file_mismatches"]
          and res["quixbugs"]["manifest_match"] and res["quixbugs"]["negatives_match"]
          and res["quixbugs"]["corpus_match"])
    res["all_freeze_checks_pass"] = ok
    pathlib.Path(out).write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k not in ("bugsinpy", "quixbugs")}, indent=1))
    print("bugsinpy combined match:", res["bugsinpy"]["combined_match"], "| quix manifest/neg/corpus:",
          res["quixbugs"]["manifest_match"], res["quixbugs"]["negatives_match"], res["quixbugs"]["corpus_match"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
