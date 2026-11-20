"""
Validation suite for the output_free_v7 class-driver synthesiser.

Each case is a small hand-written module with a known right answer: whether a
class should be driven, which methods the driver may call, and how execution
should end. The classes exist only to validate the mechanism; none of them is
ever used as evaluation input (docs/current/PHASE2_PREREGISTRATION.md §1).

Run as a script to write artifacts/final/DRIVER_SYNTHESIS_VALIDATION.json:
    python3 tests/test_driver_synthesis.py
"""
from __future__ import annotations

import ast
import collections
import json
import pathlib
import re
import sys
import tempfile
import textwrap

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.final.class_driver import (          # noqa: E402
    STEPS_PER_TRACE, eligible_classes, ineligible_reasons, select_class_entry,
)
from experiments.final.extraction import _load_module, extract_program  # noqa: E402

# name -> (source, expectation)
CASES = {
    "valid_constructor": (
        """
        class Counter:
            def __init__(self, start: int):
                self.value = start
            def inc(self, by: int):
                self.value += by
        """,
        {"driven": ["Counter"], "methods": {"Counter": ["inc"]}, "ok": True},
    ),
    "invalid_constructor": (
        """
        from typing import Callable
        class Hooked:
            def __init__(self, callback: Callable[[int], int]):
                self.callback = callback
            def fire(self, x: int):
                return self.callback(x)
        """,
        {"driven": [], "static_exclusions": {"Hooked": "constructor_parameter_not_synthesisable"},
         "failure_kind": "unsupported_signature"},
    ),
    "valid_method": (
        """
        class Greeter:
            def greet(self, name: str) -> int:
                return len(name)
        """,
        {"driven": ["Greeter"], "methods": {"Greeter": ["greet"]}, "ok": True},
    ),
    "invalid_method": (
        """
        from typing import Callable
        class Mapper:
            def apply(self, fn: Callable[[int], int]):
                return fn(1)
            def size(self, items: list):
                return len(items)
        """,
        {"driven": ["Mapper"], "methods": {"Mapper": ["size"]}, "ok": True},
    ),
    "state_transition": (
        """
        class Light:
            ORDER = ["red", "green", "yellow"]
            def __init__(self):
                self.state = 0
            def advance(self):
                self.state = (self.state + 1) % 3
                if self.state == 0:
                    self._wrap()
            def _wrap(self):
                pass
        """,
        {"driven": ["Light"], "methods": {"Light": ["advance"]}, "ok": True,
         "calls_per_trace": {"advance": STEPS_PER_TRACE}, "private_called": "_wrap"},
    ),
    "repeated_call": (
        """
        class Accumulator:
            def __init__(self):
                self.items = []
            def push(self, x: int):
                self.items.append(x)
        """,
        {"driven": ["Accumulator"], "methods": {"Accumulator": ["push"]}, "ok": True,
         "calls_per_trace": {"push": STEPS_PER_TRACE}},
    ),
    "argument_type_mismatch": (
        """
        class Sizer:
            def measure(self, n: int):
                return len(n)
        """,
        {"driven": ["Sizer"], "methods": {"Sizer": ["measure"]}, "ok": True,
         "exception_fraction": 1.0},
    ),
    "unsupported_abstract": (
        """
        from abc import ABC, abstractmethod
        class Shape(ABC):
            @abstractmethod
            def area(self): ...
        """,
        {"driven": [], "static_exclusions": {"Shape": "abstract_class"},
         "failure_kind": "unsupported_signature"},
    ),
    "unsupported_exception_class": (
        """
        class ParseError(ValueError):
            def describe(self):
                return "bad"
        """,
        {"driven": [], "static_exclusions": {"ParseError": "exception_class"},
         "failure_kind": "unsupported_signature"},
    ),
    "unsupported_external_base": (
        """
        class Registry(dict):
            def register(self, key: str):
                self[key] = True
        """,
        {"driven": [],
         "static_exclusions": {"Registry": "constructor_inherited_from_external_base"},
         "failure_kind": "unsupported_signature"},
    ),
    "nonterminating_method": (
        """
        import time
        class Spinner:
            def spin(self):
                # Blocks far past the 1 s per-trace budget without holding the
                # GIL, so an abandoned worker does not slow later tests.
                time.sleep(30)
        """,
        {"driven": ["Spinner"], "methods": {"Spinner": ["spin"]}, "ok": False,
         "failure_kind": "nonterminating"},
    ),
    "result_never_read": (
        """
        class Poison:
            def __eq__(self, other):
                raise RuntimeError("driver compared a result")
            def __bool__(self):
                raise RuntimeError("driver tested a result")
            def __repr__(self):
                raise RuntimeError("driver printed a result")
            __hash__ = object.__hash__
        class Factory:
            def make(self):
                return Poison()
        """,
        # Poison is itself an eligible class (zero-argument constructor, no
        # public methods), so it is constructed too -- and nothing raises,
        # because the driver never compares, tests or prints a result.
        {"driven": ["Factory", "Poison"], "methods": {"Factory": ["make"], "Poison": []},
         "ok": True, "exception_fraction": 0.0},
    ),
    "function_tier_takes_precedence": (
        """
        def total(values: list) -> int:
            return sum(values)
        class Unused:
            def noop(self):
                pass
        """,
        {"function_tier": True, "ok": True},
    ),
}

_ARITY_ERROR = re.compile(r"positional argument|takes \d+ positional|missing \d+ required")


def _write(tmp: pathlib.Path, name: str, source: str) -> pathlib.Path:
    path = tmp / f"{name}.py"
    path.write_text(textwrap.dedent(source).lstrip())
    return path


def run_case(tmp: pathlib.Path, name: str) -> dict:
    source, expect = CASES[name]
    path = _write(tmp, name, source)
    tree = ast.parse(path.read_text())
    specs = {s["name"]: [m for m, _, _ in s["methods"]] for s in eligible_classes(tree)}
    module, _, _ = _load_module(path)
    fn, discovery, inputs, detail = select_class_entry(module, path.read_text())
    record = extract_program(str(path), {}, "output_free_v7")

    outcome = {"case": name, "checks": {}, "record": {
        "ok": record.ok, "failure_kind": record.failure_kind,
        "entry_discovery": record.entry_discovery,
        "exception_fraction": record.stats.get("exception_fraction")}}
    checks = outcome["checks"]

    if expect.get("function_tier"):
        checks["function_tier_selected"] = (record.entry_discovery or "").startswith(
            ("priority:", "annotated:", "unannotated:"))
    if "driven" in expect:
        checks["driven_classes"] = detail.get("driven_classes", []) == expect["driven"]
    if "methods" in expect:
        checks["eligible_methods"] = all(specs.get(c) == m for c, m in expect["methods"].items())
    if "static_exclusions" in expect:
        reasons = ineligible_reasons(tree)
        checks["static_exclusions"] = all(reasons.get(c) == r
                                          for c, r in expect["static_exclusions"].items())
    if "ok" in expect:
        checks["execution_ok"] = record.ok is expect["ok"]
    if "failure_kind" in expect:
        checks["failure_kind"] = record.failure_kind == expect["failure_kind"]
    if "exception_fraction" in expect and record.ok:
        checks["exception_fraction"] = record.stats["exception_fraction"] == expect["exception_fraction"]

    # Mechanism-level measurements, independent of the expectation.
    trace_outcomes = collections.Counter()
    harness_visible = False
    per_trace_calls = []
    if inputs:
        from sbg.v2.execution.runner import SandboxRunner
        sandbox = SandboxRunner().run(name, fn, inputs, n_runs=1, timeout_s=1.0,
                                      max_timeouts=2, max_events=5000)
        for run in sandbox.traces:
            for trace in run:
                if trace.exception is None:
                    trace_outcomes["completed"] += 1
                elif trace.exception.startswith("TimeoutError"):
                    trace_outcomes["timeout"] += 1
                elif _ARITY_ERROR.search(trace.exception):
                    trace_outcomes["invalid_driver_call"] += 1
                else:
                    trace_outcomes["program_exception"] += 1
                harness_visible |= any(e.function_name == "drive" for e in trace.events)
                per_trace_calls.append(collections.Counter(
                    e.function_name for e in trace.events if e.event_type == "call"))
    outcome["trace_outcomes"] = dict(trace_outcomes)
    if inputs:
        checks["harness_frames_invisible"] = not harness_visible
    if "calls_per_trace" in expect and per_trace_calls:
        checks["calls_per_trace"] = all(
            calls[m] == n for calls in per_trace_calls for m, n in expect["calls_per_trace"].items())
    if "private_called" in expect and per_trace_calls:
        checks["private_helper_traced"] = any(calls[expect["private_called"]] > 0
                                              for calls in per_trace_calls)
    if record.ok:
        again = extract_program(str(path), {}, "output_free_v7")
        checks["deterministic"] = again.stats == record.stats
    outcome["passed"] = all(checks.values())
    return outcome


def run_all() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        results = [run_case(pathlib.Path(tmp), name) for name in CASES]
    totals = collections.Counter()
    for r in results:
        for k, v in r["trace_outcomes"].items():
            totals[k] += v
    n_traces = sum(totals.values())
    expected_driven = [n for n, (_, e) in CASES.items() if e.get("driven")]
    expected_rejected = [n for n, (_, e) in CASES.items() if e.get("driven") == []]
    return {
        "artifact": "DRIVER_SYNTHESIS_VALIDATION",
        "protocol": "output_free_v7",
        "supported_domain": (
            "Top-level Python classes whose constructor and methods take only "
            "parameters annotated (or unannotated) with types in the fixed v6 "
            "battery families: int, float, str, bool, list-like, dict-like. "
            "Constructors must be defined in the program itself (or absent with "
            "no external base). Driven by bounded, deterministic round-robin "
            "method sequences of length 8 from 11 battery-indexed starting "
            "states. Not supported: parameters of callable, IO, iterator or "
            "custom-object type; constructors inherited from external bases; "
            "abstract and exception classes; async methods; properties; "
            "required keyword-only parameters (called positionally, they fail)."),
        "n_cases": len(results),
        "n_cases_passed": sum(r["passed"] for r in results),
        "synthesis": {
            "expected_driven": len(expected_driven),
            "correctly_driven": sum(1 for r in results if r["case"] in expected_driven
                                    and r["checks"].get("driven_classes")),
            "expected_rejected": len(expected_rejected),
            "correctly_rejected": sum(1 for r in results if r["case"] in expected_rejected
                                      and r["checks"].get("driven_classes")),
        },
        "traces": {
            "n": n_traces,
            "completed": totals["completed"],
            "program_exception": totals["program_exception"],
            "timeout": totals["timeout"],
            "invalid_driver_call": totals["invalid_driver_call"],
            "execution_success_rate": round(totals["completed"] / n_traces, 4) if n_traces else None,
            "timeout_rate": round(totals["timeout"] / n_traces, 4) if n_traces else None,
            "invalid_driver_rate": round(totals["invalid_driver_call"] / n_traces, 4) if n_traces else None,
        },
        "cases": results,
    }


# --- pytest -----------------------------------------------------------------

_RESULTS = None


def _results():
    global _RESULTS
    if _RESULTS is None:
        _RESULTS = {r["case"]: r for r in run_all()["cases"]}
    return _RESULTS


def _case_test(name):
    def test(self=None):
        result = _results()[name]
        assert result["passed"], json.dumps(result, indent=2, default=str)
    test.__name__ = f"test_{name}"
    return test


for _name in CASES:
    globals()[f"test_{_name}"] = _case_test(_name)


def test_no_invalid_driver_calls():
    assert all(r["trace_outcomes"].get("invalid_driver_call", 0) == 0 for r in _results().values())


def corpus_coverage() -> dict:
    """Static tier assignment for every benchmark base program (no execution)."""
    from benchmark.scripts.observability_audit_v7 import static_entry_v7
    out = {"function": [], "class": [], "none": {}}
    for path in sorted((REPO_ROOT / "benchmark" / "corpus" / "base_programs").glob("*.py")):
        tree = ast.parse(path.read_text())
        entry = static_entry_v7(tree)
        if entry is None:
            out["none"][path.stem] = ineligible_reasons(tree) or {"module": "no synthesisable function and no class"}
        else:
            out[entry[0]].append(path.stem)
    out["counts"] = {"function": len(out["function"]), "class": len(out["class"]),
                     "none": len(out["none"])}
    return out


if __name__ == "__main__":
    payload = run_all()
    payload["corpus_coverage_static"] = corpus_coverage()
    out = REPO_ROOT / "artifacts" / "final" / "DRIVER_SYNTHESIS_VALIDATION.json"
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(f"{payload['n_cases_passed']}/{payload['n_cases']} cases passed")
    print(json.dumps(payload["synthesis"]), json.dumps(payload["traces"]))
    for r in payload["cases"]:
        if not r["passed"]:
            print("FAILED", r["case"], r["checks"], r["record"])
