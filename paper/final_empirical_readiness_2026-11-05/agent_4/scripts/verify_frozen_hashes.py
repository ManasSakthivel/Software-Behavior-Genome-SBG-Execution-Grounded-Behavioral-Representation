#!/usr/bin/env python3
"""Agent 4: compare current sha256 of every protected file against the baseline (read-only)."""
import sys, hashlib, pathlib, json
sys.dont_write_bytecode = True
REPO = pathlib.Path(__file__).resolve().parents[4]
B = REPO / "paper/final_empirical_readiness_2026-11-05/_baseline/sha256_before.txt"
OUT = pathlib.Path(__file__).resolve().parents[1] / "tables"
mism, miss, n = [], [], 0
for line in B.read_text().splitlines():
    if not line.strip():
        continue
    h, f = line.split("  ", 1)
    p = REPO / f
    n += 1
    if not p.is_file():
        miss.append(f); continue
    d = hashlib.sha256()
    with open(p, "rb") as fh:
        for ch in iter(lambda: fh.read(1 << 20), b""):
            d.update(ch)
    if d.hexdigest() != h:
        mism.append(f)
res = {"n_checked": n, "n_mismatch": len(mism), "n_missing": len(miss), "mismatch": mism, "missing": miss}
(OUT / "hash_verify.json").write_text(json.dumps(res, indent=1))
print(json.dumps({k: (v if not isinstance(v, list) else v[:20]) for k, v in res.items()}, indent=1))
