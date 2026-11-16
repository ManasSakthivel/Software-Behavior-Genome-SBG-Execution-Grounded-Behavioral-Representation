"""Shared harness for the A4R recovery tests (stdlib unittest).

A4R_SRC=original (default) tests the predecessor modules in competitor_baselines/.
A4R_SRC=fixed tests the recovery/fixed/ copies.

Tests that document a KNOWN BUG of the original code are wrapped with bug(): they are expectedFailure
when testing the original (so the suite stays green while the defect is recorded) and must pass on the fixed copy.
"""
from __future__ import annotations

import os
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent            # .../competitor_baselines/recovery
CB = HERE.parent                                            # .../competitor_baselines
SRC = os.environ.get("A4R_SRC", "original")
SRC_DIR = CB if SRC == "original" else HERE / "fixed"
if SRC not in ("original", "fixed"):
    raise SystemExit("A4R_SRC must be original|fixed")
sys.dont_write_bytecode = True
sys.path[:0] = [str(SRC_DIR)]


def bug(bug_id: str):
    """Mark a test as documenting a known defect of the ORIGINAL code (id = BUG-xx in EXPERIMENT_RECOVERY_AND_REGISTRY.md)."""
    def deco(fn):
        if SRC == "fixed":
            return fn
        return unittest.expectedFailure(fn)
    deco.__name__ = f"bug_{bug_id}"
    return deco


def brute_lev(a, b):
    n, m = len(a), len(b)
    D = list(range(m + 1))
    for i in range(1, n + 1):
        prev, D[0] = D[0], i
        for j in range(1, m + 1):
            cur = D[j]
            D[j] = min(D[j] + 1, D[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev = cur
    return D[m]


def brute_lcs(a, b):
    n, m = len(a), len(b)
    T = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            T[i][j] = T[i - 1][j - 1] + 1 if a[i - 1] == b[j - 1] else max(T[i - 1][j], T[i][j - 1])
    return T[n][m]


class FakeTrace:
    """Minimal stand-in for bl_common.FileTrace (only the attributes the baselines read)."""

    def __init__(self, inputs, entry="f", stats=None, lines=None):
        self.inputs = inputs
        self.entry = entry
        self.stats = stats or {}
        self.ok = True
        self._lines = lines or []

    def source_lines(self):
        return self._lines


def mk_input(events, ret="1", exc=None, stdout="", cov=(), input_="()"):
    return {"events": events, "ret": ret, "ret_type": "int", "exc": exc, "stdout": stdout, "cov": list(cov), "trunc": False, "input": input_}
