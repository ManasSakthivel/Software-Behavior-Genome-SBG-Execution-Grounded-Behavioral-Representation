"""Tiny helpers for the unit tests (synthetic cache-schema traces)."""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cn_lib as L  # noqa: E402


def trace_record(inputs, entry="f", path="x.py"):
    """inputs: list of dict(events=[[type, fn, line, snap]], ret='..', exc=None, stdout='') -> cache-schema record."""
    traces = []
    for i, d in enumerate(inputs):
        traces.append({"input": f"({i},)", "ret": d.get("ret", "None"), "ret_type": d.get("ret_type", "NoneType"), "exc": d.get("exc"), "stdout": d.get("stdout", ""),
                       "ms": 0.1, "cov": [], "trunc": False, "events": d["events"]})
    return {"path": path, "ok": True, "failure_kind": None, "entry_function": entry, "stats": {}, "sandbox": {"traces": traces}}


def rec(source=None, trace=None, path="x.py", pop="v9c_dev", base_id="b"):
    r = {"pop": pop, "base_id": base_id, "path": path}
    if source is not None:
        r["source"] = source
    if trace is not None:
        r["trace"] = trace
    return r


def wrapper():
    """driver wrapper events (removed by the loader)."""
    return [["c", "<lambda>", 99, {"args": "(1,)", "entry_fn": "<function f at 0x1>"}]], [["r", "<lambda>", 99, {"args": "(1,)", "entry_fn": "<function f at 0x1>"}]]


def call_trace(names, ret="1", exc=None, stdout="", entry=None, line_of=lambda n: 1, args=None):
    """events of a flat sequence of calls to `names` (each call immediately returns), wrapped in the driver frame."""
    w0, w1 = wrapper()
    ev = list(w0)
    for n in names:
        ev.append(["c", n, line_of(n), dict(args or {"x": "1"})])
        ev.append(["l", n, line_of(n) + 1, None])
        ev.append(["r", n, line_of(n) + 1, dict(args or {"x": "1"})])
    ev += w1
    return {"events": ev, "ret": ret, "exc": exc, "stdout": stdout}


CTX = L.Ctx
