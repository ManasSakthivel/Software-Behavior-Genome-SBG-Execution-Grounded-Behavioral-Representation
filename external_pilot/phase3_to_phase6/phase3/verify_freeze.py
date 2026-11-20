"""Integrity check for the frozen SBG V8 snapshot. Read-only.

Recomputes SHA-256 for every file listed in SBG_V8_CHECKSUMS.sha256 under frozen_v8_2edfe568/
and compares. Exit 0 = every listed file matches and no unlisted file exists (except __pycache__).
Exit 1 = mismatch, missing or extra file. Run with: python3 -I verify_freeze.py
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(HERE, "frozen_v8_2edfe568")
SUMS = os.path.join(HERE, "SBG_V8_CHECKSUMS.sha256")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


expected = {}
for line in open(SUMS, encoding="utf-8"):
    line = line.rstrip("\n")
    if not line:
        continue
    digest, rel = line.split("  ", 1)
    expected[rel[2:] if rel.startswith("./") else rel] = digest

bad, missing = [], []
for rel, digest in expected.items():
    p = os.path.join(SNAP, rel)
    if not os.path.isfile(p):
        missing.append(rel)
    elif sha256(p) != digest:
        bad.append(rel)

extra = []
for dp, dn, fn in os.walk(SNAP):
    dn[:] = [d for d in dn if d != "__pycache__"]
    for f in fn:
        rel = os.path.relpath(os.path.join(dp, f), SNAP)
        if rel not in expected and "__pycache__" not in rel:
            extra.append(rel)

print(f"listed={len(expected)} mismatched={len(bad)} missing={len(missing)} extra={len(extra)}")
for label, items in (("MISMATCH", bad), ("MISSING", missing), ("EXTRA", extra)):
    for x in items[:20]:
        print(label, x)
sys.exit(0 if not (bad or missing or extra) else 1)
