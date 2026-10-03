#!/usr/bin/env python3
"""
experiments/final/external_java.py
==================================
QuixBugs Java under the SBG schema, or not at all.

The pre-registered criterion (docs/current/PHASE2_PREREGISTRATION.md §6) is
that Java counts as an SBG evaluation only if Java traces yield the same
feature schema the Python pipeline builds -- the V3 genome, the temporal genome
and the state genome. Those genomes consume exactly four things from a trace:
events of kind call / line / return / exception carrying the enclosing
function name, the source line and a repr-style snapshot of the frame's locals;
the set of lines reached; the top-level exception type; and a truncation flag.
They never read a return value or stdout.

The earlier Java experiment (experiments/external/quixbugs_java_evaluation.py)
produced only method ENTER / EXIT / EXCEPTION markers -- no line events, no
locals, no coverage -- and scored them with a different five-feature "EEP"
formula. It was not an SBG measurement.

This module produces the full schema with the JDK's debugger interface
(external/quixbugs_java/tracer/SbgJdiTracer.java): line breakpoints give line
events and coverage, method entry/exit requests give call/return, exception
requests (with CPython's propagate-through-every-frame convention) give
exception events, and frame locals are rendered as Python reprs. The Java
traces are then featurised by the *same* function that featurises Python
traces (extraction._trace_and_record), so nothing downstream is re-implemented.

Pairs:
  positive   correct version vs buggy version (the real QuixBugs bug)
  negative   correct version vs a Java-safe semantics-preserving variant of
             itself, accepted only if javac emits byte-identical code
             (ignoring the line-number table), so preservation is proven
             rather than assumed.

Input regimes:
  canonical  (primary)   the protocol's fixed batteries, mapped by Java type
  declared   (secondary) the input half of QuixBugs' json_testcases;
                         expected outputs are discarded when the corpus is
                         vendored and never reach this module

Usage:
  python3 experiments/final/external_java.py vendor     # pin + freeze corpus
  python3 experiments/final/external_java.py run        # trace + score
  python3 experiments/final/external_java.py finalize   # apply frozen tau*
"""
from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import types
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sbg.extraction.dynamic.tracer import ExecutionTrace, TraceEvent  # noqa: E402
from sbg import statistics as st                                     # noqa: E402
from experiments.final import extraction as X                          # noqa: E402
from experiments.final import protocol as P                            # noqa: E402
from experiments.final.static_baselines import multiset_distance       # noqa: E402

QUIXBUGS_URL = "https://github.com/jkoppel/QuixBugs.git"
QUIXBUGS_COMMIT = "4257f44b0ff1181dedaedee6a447e133219fcebf"
CORPUS = REPO_ROOT / "external" / "quixbugs_java"
TRACER_SRC = CORPUS / "tracer" / "SbgJdiTracer.java"
ARTIFACTS = REPO_ROOT / "artifacts" / "final"
RESULT_PATH = ARTIFACTS / "QUIXBUGS_JAVA_SBG_RESULTS.json"
PAIRS_PATH = ARTIFACTS / "pairs_quixbugs_java.jsonl"
THRESHOLD_PATH = ARTIFACTS / "THRESHOLD_FROZEN.json"
FREEZE_PATH = ARTIFACTS / "PHASE2_FREEZE.json"

# Budgets. The per-trace budget is the protocol's 1.0 s plus a fixed allowance
# per recorded event for debugger round-trips, which Python's in-process
# sys.settrace does not pay. The allowance is fixed here, before scoring.
MAX_EVENTS = X.MAX_EVENTS
N_RUNS = X.N_RUNS
TRACE_TIMEOUT_MS = 1000
PER_EVENT_ALLOWANCE_MS = 3.0
MAX_TIMEOUTS_PER_RUN = 2
PROGRAM_BUDGET_S = 600.0
N_INPUTS = P.BATTERY_SIZE
MAX_NEGATIVES = 3
ORACLE_TIMEOUT_S = 10

SUPPORT_CLASSES = ("Node", "WeightedEdge")

# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _clone(dest: pathlib.Path) -> pathlib.Path:
    if not (dest / ".git").exists():
        subprocess.run(["git", "clone", "-q", QUIXBUGS_URL, str(dest)], check=True)
    subprocess.run(["git", "-C", str(dest), "checkout", "-q", QUIXBUGS_COMMIT], check=True)
    head = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    if head != QUIXBUGS_COMMIT:
        raise RuntimeError(f"clone at {head}, expected {QUIXBUGS_COMMIT}")
    return dest


def vendor(source: Optional[pathlib.Path] = None) -> dict:
    """Copy the pinned Java programs into external/quixbugs_java and freeze them.

    Only the *input* half of each json_testcases line is kept. Expected outputs
    never enter the repository copy, so no later stage can read them.
    """
    src = source or _clone(pathlib.Path(tempfile.gettempdir()) / "sbg_quixbugs_pinned")
    for sub in ("buggy", "correct", "support"):
        (CORPUS / sub).mkdir(parents=True, exist_ok=True)
    names = sorted(p.stem for p in (src / "correct_java_programs").glob("*.java"))
    for name in names:
        shutil.copyfile(src / "java_programs" / f"{name}.java", CORPUS / "buggy" / f"{name}.java")
        shutil.copyfile(src / "correct_java_programs" / f"{name}.java",
                        CORPUS / "correct" / f"{name}.java")
    for name in SUPPORT_CLASSES:
        shutil.copyfile(src / "java_programs" / f"{name}.java", CORPUS / "support" / f"{name}.java")
    shutil.copyfile(src / "LICENSE", CORPUS / "LICENSE")

    declared: Dict[str, List[Any]] = {}
    for name in names:
        tc = src / "json_testcases" / f"{name.lower()}.json"
        if not tc.exists():
            continue
        inputs = []
        for line in tc.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(case, list) and len(case) >= 2:
                args = case[0] if isinstance(case[0], list) else [case[0]]
                inputs.append(args)            # case[1], the expected output, is dropped
            if len(inputs) == N_INPUTS:
                break
        declared[name] = inputs
    (CORPUS / "declared_inputs.json").write_text(json.dumps(declared, indent=1, sort_keys=True) + "\n")

    files = sorted(p for p in CORPUS.rglob("*") if p.is_file() and p.name != "MANIFEST.json"
                   and "tracer" not in p.parts)
    manifest = {
        "corpus": "QuixBugs (Java)",
        "source_repository": QUIXBUGS_URL,
        "commit": QUIXBUGS_COMMIT,
        "license": "MIT (external/quixbugs_java/LICENSE)",
        "language": "Java",
        "split": "external_test",
        "note": ("Vendored verbatim from the pinned commit. declared_inputs.json keeps "
                 "only the input half of json_testcases; expected outputs were dropped "
                 "at vendoring time."),
        "programs": names,
        "files": {str(p.relative_to(CORPUS)): _sha256(p) for p in files},
    }
    (CORPUS / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


# ---------------------------------------------------------------------------
# Signatures, types and inputs
# ---------------------------------------------------------------------------

_SIG_RE = re.compile(r"public\s+static\s+([\w<>\[\],\s?]+?)\s+(\w+)\s*\(([^)]*)\)")


def split_top_level(text: str) -> List[str]:
    parts, depth, cur = [], 0, []
    for ch in text:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur).strip())
    return parts


def entry_signature(name: str, source: str) -> Optional[Dict[str, Any]]:
    """The QuixBugs entry: the public static method named after the class.

    This is the corpus's own convention (every program's entry is the method
    whose name is the lower-cased class name), fixed before any trace is run.
    Overloads resolve to the first declaration.
    """
    for m in _SIG_RE.finditer(source):
        ret, method, params = m.group(1).strip(), m.group(2), m.group(3).strip()
        if method != name.lower():
            continue
        plist = []
        for p in split_top_level(params) if params else []:
            p = re.sub(r"\s+", " ", p.replace("final ", "")).strip()
            # "int [][] items" / "ArrayList<Integer> arr"
            mm = re.match(r"^(.*?)\s*(\w+)$", p)
            if not mm:
                return None
            ptype = mm.group(1).replace(" ", "")
            plist.append((mm.group(2), ptype))
        return {"method": method, "return": ret, "params": plist}
    return None


_LIST_TYPES = {"int[]", "ArrayList<Integer>", "List<Integer>", "ArrayList", "List", "Object"}


def java_family(jtype: str) -> Optional[str]:
    """Java parameter type -> protocol battery key (None: not synthesisable).

    Mirrors protocol.annotation_family: a type the fixed batteries cannot
    supply makes the program ineligible for the canonical regime. ``Object``
    and raw collections are Java's untyped parameters and take the list
    battery, as an unannotated Python parameter does.
    """
    if jtype in ("int", "long", "short", "Integer", "Long"):
        return "int"
    if jtype in ("double", "float", "Double", "Float"):
        return "float"
    if jtype in ("boolean", "Boolean"):
        return "bool"
    if jtype == "String":
        return "str"
    if jtype in _LIST_TYPES:
        return "list"
    return None


def _jlit_scalar(value: Any) -> Optional[str]:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return f"Integer.valueOf({value})"
    if isinstance(value, float):
        return f"Double.valueOf({float(value)!r})"
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        inner = [_jlit_scalar(v) for v in value]
        if any(i is None for i in inner):
            return None
        return ("new ArrayList<Object>(Arrays.asList(new Object[]{" + ", ".join(inner) + "}))")
    return None


def java_literal(value: Any, jtype: str) -> Optional[str]:
    """Java expression for ``value`` passed to a parameter of type ``jtype``."""
    fam = java_family(jtype)
    if fam == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            return None
        return f"{value}L" if jtype in ("long", "Long") else str(value)
    if fam == "float":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return f"{float(value)!r}" + ("f" if jtype in ("float", "Float") else "")
    if fam == "bool":
        return ("true" if value else "false") if isinstance(value, bool) else None
    if fam == "str":
        return json.dumps(value) if isinstance(value, str) else None
    if fam == "list":
        if not isinstance(value, list):
            return None
        if jtype == "int[]":
            if not all(isinstance(v, int) and not isinstance(v, bool) for v in value):
                return None
            return "new int[]{" + ", ".join(str(v) for v in value) + "}"
        if jtype in ("ArrayList<Integer>", "List<Integer>"):
            if not all(isinstance(v, int) and not isinstance(v, bool) for v in value):
                return None
            return ("new ArrayList<Integer>(Arrays.asList(new Integer[]{"
                    + ", ".join(str(v) for v in value) + "}))")
        return _jlit_scalar(value) if jtype == "Object" else (
            None if _jlit_scalar(value) is None
            else "new ArrayList(Arrays.asList(new Object[]{"
            + ", ".join(_jlit_scalar(v) for v in value) + "}))")
    return None


def canonical_inputs(sig: Dict[str, Any]) -> Optional[List[List[Any]]]:
    """Protocol inputs via the protocol's own zip rule over its batteries."""
    fams = [java_family(t) for _, t in sig["params"]]
    if any(f is None for f in fams):
        return None
    synthesised = P.synthesise_inputs(fams)      # annotation texts == battery keys
    if synthesised is None:
        return None
    if synthesised == [None]:
        return [[] for _ in range(1)]
    return [list(v) if isinstance(v, tuple) else [v] for v in synthesised]


def inputs_to_java(sig: Dict[str, Any], inputs: List[List[Any]]) -> Optional[List[List[str]]]:
    out = []
    for args in inputs:
        if len(args) != len(sig["params"]):
            return None
        lits = [java_literal(v, t) for v, (_, t) in zip(args, sig["params"])]
        if any(l is None for l in lits):
            return None
        out.append(lits)
    return out


# ---------------------------------------------------------------------------
# Compilation, harness, tracing
# ---------------------------------------------------------------------------

MARKER_SRC = """package sbgharness;
public final class SbgMarker {
    public static void begin(int idx) { }
    public static void end(int idx) { }
    public static void fail(String type, String msg) { }
}
"""


def harness_source(name: str, sig: Dict[str, Any], java_inputs: List[List[str]],
                   oracle: bool = False) -> str:
    """Harness that calls the entry once per input and discards the result.

    The SBG harness never inspects a return value. The oracle harness (a
    separate class, used only by the output-reading reference) prints results.
    """
    cls = "SbgOracle" if oracle else "SbgHarness"
    cases = []
    for i, lits in enumerate(java_inputs):
        call = f"java_programs.{name}.{sig['method']}({', '.join(lits)})"
        if oracle:
            cases.append(f"            case {i}: return {call};" if sig["return"] != "void"
                         else f"            case {i}: {call}; return null;")
        else:
            cases.append(f"            case {i}: {call}; return;")
    preload = "\n".join(f'        try {{ Class.forName("java_programs.{c}"); }} catch (Throwable t) {{ }}'
                        for c in (name,) + SUPPORT_CLASSES)
    if oracle:
        return f"""package sbgharness;
import java.util.*;
public class {cls} {{
    public static void main(String[] a) {{
        int i = Integer.parseInt(a[0]);
        String r;
        try {{
            Object v = run(i);
            r = v instanceof Object[] ? Arrays.deepToString((Object[]) v) : String.valueOf(v);
        }} catch (Throwable t) {{ r = "EXC:" + t.getClass().getSimpleName(); }}
        System.out.println(r);
    }}
    static Object run(int i) {{
        switch (i) {{
{chr(10).join(cases)}
        }}
        return null;
    }}
}}
"""
    return f"""package sbgharness;
import java.util.*;
public class {cls} {{
    public static void main(String[] a) {{
        int start = Integer.parseInt(a[0]);
        int total = Integer.parseInt(a[1]);
{preload}
        for (int k = start; k < total; k++) {{
            SbgMarker.begin(k);
            try {{ run(k % {len(java_inputs)}); }}
            catch (Throwable t) {{ SbgMarker.fail(t.getClass().getSimpleName(), String.valueOf(t.getMessage())); }}
            SbgMarker.end(k);
        }}
    }}
    static void run(int i) {{
        switch (i) {{
{chr(10).join(cases)}
        }}
    }}
}}
"""


def _to_package(source: str) -> str:
    return re.sub(r"^\s*package\s+[\w.]+\s*;", "package java_programs;", source, count=1, flags=re.M)


_tracer_dir: Optional[pathlib.Path] = None


def tracer_classpath() -> pathlib.Path:
    global _tracer_dir
    if _tracer_dir is None:
        d = pathlib.Path(tempfile.mkdtemp(prefix="sbg_jdi_"))
        r = subprocess.run(["javac", "-g", "-d", str(d), str(TRACER_SRC)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(r.stderr)
        _tracer_dir = d
    return _tracer_dir


def compile_version(program_src: str, name: str, harness_srcs: Dict[str, str],
                    extra_sources: Dict[str, str]) -> Tuple[Optional[pathlib.Path], str]:
    """Compile one program version with support classes and harnesses."""
    work = pathlib.Path(tempfile.mkdtemp(prefix=f"sbg_j_{name}_"))
    srcdir = work / "src"
    (srcdir / "java_programs").mkdir(parents=True)
    (srcdir / "sbgharness").mkdir(parents=True)
    (srcdir / "java_programs" / f"{name}.java").write_text(_to_package(program_src))
    for cname, text in extra_sources.items():
        (srcdir / "java_programs" / f"{cname}.java").write_text(_to_package(text))
    (srcdir / "sbgharness" / "SbgMarker.java").write_text(MARKER_SRC)
    for cls, text in harness_srcs.items():
        (srcdir / "sbgharness" / f"{cls}.java").write_text(text)
    out = work / "classes"
    out.mkdir()
    files = [str(p) for p in srcdir.rglob("*.java")]
    r = subprocess.run(["javac", "-g", "-nowarn", "-encoding", "UTF-8", "-d", str(out)] + files,
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None, r.stderr[-800:]
    return out, ""


def support_sources() -> Dict[str, str]:
    return {c: (CORPUS / "support" / f"{c}.java").read_text() for c in SUPPORT_CLASSES}


def run_traces(classes: pathlib.Path, n_inputs: int, input_reprs: List[str],
               program_id: str) -> Tuple[List[List[ExecutionTrace]], Optional[str], Dict[str, Any]]:
    """Trace N_RUNS x n_inputs executions; mirror the Python runner's rules.

    Returns (runs, error, info) where error is None, "NONTERMINATING" or
    "PROGRAM_BUDGET_EXCEEDED" -- the SandboxResult.error vocabulary.
    """
    total = N_RUNS * n_inputs
    traces: Dict[int, ExecutionTrace] = {}
    timeouts_by_run: Dict[int, int] = collections.defaultdict(int)
    start, t0 = 0, time.monotonic()
    error = None
    tcp = tracer_classpath()
    while start < total:
        if time.monotonic() - t0 > PROGRAM_BUDGET_S:
            error = "PROGRAM_BUDGET_EXCEEDED"
            break
        cmd = ["java", "-cp", str(tcp), "SbgJdiTracer", str(classes), "sbgharness.SbgHarness",
               str(start), str(total), str(MAX_EVENTS), str(TRACE_TIMEOUT_MS),
               str(PER_EVENT_ALLOWANCE_MS)]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=PROGRAM_BUDGET_S + 60)
        last_idx = start - 1
        for line in proc.stdout.splitlines():
            if not line.startswith("{"):
                continue
            rec = json.loads(line)
            idx = rec["idx"]
            last_idx = idx
            events = [TraceEvent(event_type=e[0], function_name=e[1], lineno=e[2],
                                 local_vars_snapshot=e[3], timestamp_ns=k)
                      for k, e in enumerate(rec["events"])]
            exc = rec["exception"]
            if rec["timed_out"]:
                exc = f"TimeoutError: execution exceeded {TRACE_TIMEOUT_MS / 1000:.1f} s"
                timeouts_by_run[idx // n_inputs] += 1
            traces[idx] = ExecutionTrace(
                program_id=program_id, input_repr=input_reprs[idx % n_inputs],
                events=events, return_value=None, exception=exc, stdout="",
                execution_time_ms=float(rec["elapsed_ms"]),
                coverage=set(rec["coverage"]), truncated=bool(rec["truncated"]))
        if proc.returncode == 3:
            run = last_idx // n_inputs
            if timeouts_by_run[run] >= MAX_TIMEOUTS_PER_RUN:
                error = "NONTERMINATING"
                break
            start = last_idx + 1
            continue
        if proc.returncode != 0:
            raise RuntimeError(f"tracer exited {proc.returncode}: {proc.stderr[-600:]}")
        break
    runs: List[List[ExecutionTrace]] = []
    for r in range(N_RUNS):
        run = [traces[i] for i in range(r * n_inputs, (r + 1) * n_inputs) if i in traces]
        if run:
            runs.append(run)
    info = {"wall_s": round(time.monotonic() - t0, 2), "n_traces": len(traces),
            "timeouts": sum(timeouts_by_run.values())}
    return runs, error, info


class _PreparedRunner:
    """Stands in for SandboxRunner so extraction featurises Java traces."""

    def __init__(self, result: Any):
        self.result = result

    def run(self, *args: Any, **kwargs: Any) -> Any:
        return self.result


def record_from_runs(path: str, runs: List[List[ExecutionTrace]], error: Optional[str],
                     entry: str) -> X.ProgramRecord:
    """Featurise Java traces with the Python pipeline's own function."""
    saved = X._runner
    X._runner = _PreparedRunner(types.SimpleNamespace(traces=runs, error=error))
    try:
        record = X._trace_and_record(path, {}, "output_free_v6", None,
                                     f"quixbugs_entry:{entry}", lambda _x: None, [])
    finally:
        X._runner = saved
    record.entry_function = entry
    return record


def trace_version(name: str, program_src: str, sig: Dict[str, Any],
                  java_inputs: List[List[str]], input_reprs: List[str],
                  label: str) -> Tuple[X.ProgramRecord, Dict[str, Any]]:
    harness = {"SbgHarness": harness_source(name, sig, java_inputs)}
    classes, err = compile_version(program_src, name, harness, support_sources())
    path = f"external/quixbugs_java/{label}/{name}.java"
    if classes is None:
        return X.ProgramRecord(path=path, ok=False, failure_kind="syntax_error",
                               failure_detail=err[:300]), {}
    try:
        runs, error, info = run_traces(classes, len(java_inputs), input_reprs, name)
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        return X.ProgramRecord(path=path, ok=False, failure_kind="trace_error",
                               failure_detail=str(exc)[:300]), {}
    finally:
        shutil.rmtree(classes.parent, ignore_errors=True)
    return record_from_runs(path, runs, error, sig["method"]), info


def oracle_outputs(name: str, program_src: str, sig: Dict[str, Any],
                   java_inputs: List[List[str]]) -> Optional[List[str]]:
    """Output-reading reference only. Never feeds any SBG predictor."""
    harness = {"SbgOracle": harness_source(name, sig, java_inputs, oracle=True)}
    classes, _ = compile_version(program_src, name, harness, support_sources())
    if classes is None:
        return None
    outs = []
    try:
        for i in range(len(java_inputs)):
            try:
                r = subprocess.run(["java", "-Xss8m", "-Xmx512m", "-cp", str(classes),
                                    "sbgharness.SbgOracle", str(i)],
                                   capture_output=True, text=True, timeout=ORACLE_TIMEOUT_S)
                outs.append(r.stdout.strip())
            except subprocess.TimeoutExpired:
                outs.append("TIMEOUT")
    finally:
        shutil.rmtree(classes.parent, ignore_errors=True)
    return outs


# ---------------------------------------------------------------------------
# Java-safe semantics-preserving variants
# ---------------------------------------------------------------------------

def _strip_comments(src: str) -> str:
    out, i, n = [], 0, len(src)
    in_str = None
    while i < n:
        c = src[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(src[i + 1])
                i += 2
                continue
            if c == in_str:
                in_str = None
            i += 1
            continue
        if c in "\"'":
            in_str = c
            out.append(c)
            i += 1
        elif src.startswith("//", i):
            while i < n and src[i] != "\n":
                i += 1
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def jsp4_comment_strip(src: str, sig: Dict[str, Any]) -> str:
    """J-SP4 (as SP-4): remove comments and the lines they leave empty."""
    lines = _strip_comments(src).split("\n")
    return "\n".join(l.rstrip() for l in lines if l.strip()) + "\n"


def jsp10_format_normalize(src: str, sig: Dict[str, Any]) -> str:
    """J-SP10 (as SP-10): re-indent by brace depth, drop blank lines."""
    out, depth = [], 0
    for raw in src.split("\n"):
        line = raw.strip()
        if not line:
            continue
        code = _strip_comments(line)
        opens, closes = code.count("{"), code.count("}")
        lead = depth - (1 if line.startswith("}") else 0)
        out.append("    " * max(lead, 0) + line)
        depth += opens - closes
    return "\n".join(out) + "\n"


def jsp3_dead_code(src: str, sig: Dict[str, Any]) -> str:
    """J-SP3 (as SP-3): an unreachable block at the top of the entry method."""
    m = re.search(r"public\s+static\s+[\w<>\[\],\s?]+?\s+" + re.escape(sig["method"])
                  + r"\s*\([^)]*\)\s*(throws[^{]*)?\{", src)
    if not m:
        return src
    return src[:m.end()] + "\n        if (false) { int sbgDeadCode = 0; }" + src[m.end():]


JAVA_SP = (("J-SP4", jsp4_comment_strip), ("J-SP10", jsp10_format_normalize),
           ("J-SP3", jsp3_dead_code))


def bytecode_signature(classes: pathlib.Path) -> str:
    """javap -c -p of every program class, without line or local-variable tables."""
    parts = []
    for cf in sorted((classes / "java_programs").glob("*.class")):
        r = subprocess.run(["javap", "-c", "-p", str(cf)], capture_output=True, text=True)
        parts.append(re.sub(r"^Compiled from.*$", "", r.stdout, flags=re.M))
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def make_negatives(name: str, correct_src: str, sig: Dict[str, Any]) -> List[Dict[str, Any]]:
    base_classes, _ = compile_version(correct_src, name, {}, support_sources())
    if base_classes is None:
        return []
    base_sig = bytecode_signature(base_classes)
    shutil.rmtree(base_classes.parent, ignore_errors=True)
    kept, log = [], []
    for tag, fn in JAVA_SP:
        if len(kept) == MAX_NEGATIVES:
            break
        variant = fn(correct_src, sig)
        if variant.strip() == correct_src.strip():
            log.append({"transformation": tag, "kept": False, "reason": "no_change"})
            continue
        classes, err = compile_version(variant, name, {}, support_sources())
        if classes is None:
            log.append({"transformation": tag, "kept": False, "reason": "compile_error"})
            continue
        same = bytecode_signature(classes) == base_sig
        shutil.rmtree(classes.parent, ignore_errors=True)
        if not same:
            log.append({"transformation": tag, "kept": False, "reason": "bytecode_differs"})
            continue
        kept.append({"transformation": tag, "source": variant})
        log.append({"transformation": tag, "kept": True, "reason": "bytecode_identical"})
    return [dict(k, log=log) for k in kept] if kept else [{"log": log, "source": None}]


# ---------------------------------------------------------------------------
# Static token baseline for Java
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"\s+|//[^\n]*|/\*.*?\*/|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'"
                       r"|([A-Za-z_$][\w$]*)|(\d[\w.]*)|(\S)", re.S)


def java_token_multiset(source: str) -> collections.Counter:
    """(type, text) multiset skipping comments, strings and layout (as static_token)."""
    counts: collections.Counter = collections.Counter()
    for m in _TOKEN_RE.finditer(source):
        if m.group(1):
            counts[("NAME", m.group(1))] += 1
        elif m.group(2):
            counts[("NUMBER", m.group(2))] += 1
        elif m.group(3):
            counts[("OP", m.group(3))] += 1
    return counts


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def _load_manifest() -> dict:
    return json.loads((CORPUS / "MANIFEST.json").read_text())


def _verify_manifest(manifest: dict) -> str:
    for rel, digest in manifest["files"].items():
        if _sha256(CORPUS / rel) != digest:
            raise RuntimeError(f"corpus file changed after freezing: {rel}")
    return _sha256(CORPUS / "MANIFEST.json")


def _record_freeze(stage: str, payload: dict) -> None:
    try:
        freeze = json.loads(FREEZE_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        freeze = {"artifact": "PHASE2_FREEZE", "stages": {}}
    freeze.setdefault("stages", {})[stage] = payload
    FREEZE_PATH.write_text(json.dumps(freeze, indent=2) + "\n")


def evaluate(regimes: Sequence[str] = ("canonical", "declared"),
             only: Optional[Sequence[str]] = None) -> dict:
    manifest = _load_manifest()
    manifest_hash = _verify_manifest(manifest)
    _record_freeze("quixbugs_java", {
        "manifest": "external/quixbugs_java/MANIFEST.json",
        "manifest_sha256": manifest_hash,
        "commit": QUIXBUGS_COMMIT,
        "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "note": "recorded before any Java pair was scored",
    })
    declared_all = json.loads((CORPUS / "declared_inputs.json").read_text())
    names = [n for n in manifest["programs"] if not only or n in only]

    rows: List[dict] = []
    ledger: Dict[str, dict] = {}
    negatives_cache: Dict[str, List[dict]] = {}
    for name in names:
        buggy_src = (CORPUS / "buggy" / f"{name}.java").read_text()
        correct_src = (CORPUS / "correct" / f"{name}.java").read_text()
        sig = entry_signature(name, correct_src)
        for regime in regimes:
            key = f"{regime}:{name}"
            if sig is None:
                ledger[key] = {"status": "excluded", "reason": "entry_method_not_found"}
                continue
            if regime == "canonical":
                inputs = canonical_inputs(sig)
                reason = "unsupported_signature"
            else:
                inputs = declared_all.get(name)
                reason = "no_declared_inputs" if not inputs else "unsupported_declared_input_type"
            java_inputs = inputs_to_java(sig, inputs) if inputs else None
            if not inputs or java_inputs is None:
                ledger[key] = {"status": "excluded", "reason": reason,
                               "param_types": [t for _, t in sig["params"]]}
                continue
            input_reprs = [repr(tuple(a)) for a in inputs]
            t0 = time.monotonic()
            base, binfo = trace_version(name, correct_src, sig, java_inputs, input_reprs, "correct")
            bug, uinfo = trace_version(name, buggy_src, sig, java_inputs, input_reprs, "buggy")
            if name not in negatives_cache:
                negatives_cache[name] = make_negatives(name, correct_src, sig)
            neg_specs = [n for n in negatives_cache[name] if n.get("source")]
            oracle_base = oracle_outputs(name, correct_src, sig, java_inputs)
            oracle_bug = oracle_outputs(name, buggy_src, sig, java_inputs)
            static_base = java_token_multiset(correct_src)

            def row(variant_rec, label, kind, transformation, variant_src, oracle_var):
                scores = X.score_pair(base, variant_rec)
                failure = None
                if scores is None:
                    side = "base" if not base.ok else "variant"
                    rec = base if not base.ok else variant_rec
                    failure = {"side": side, "kind": rec.failure_kind,
                               "detail": (rec.failure_detail or "")[:200]}
                else:
                    scores["static_token"] = round(
                        multiset_distance(static_base, java_token_multiset(variant_src)), 9)
                    scores["static_ast"] = None
                oracle = None
                if oracle_base is not None and oracle_var is not None:
                    oracle = {"differs": oracle_base != oracle_var}
                return {
                    "pair_id": f"quixbugs_java__{regime}__{name}__{kind}"
                               + (f"_{transformation}" if transformation else ""),
                    "program": name, "regime": regime, "label": label, "kind": kind,
                    "transformation": transformation,
                    "evaluated": scores is not None, "scores": scores, "failure": failure,
                    "base_stats": base.stats if base.ok else None,
                    "variant_stats": variant_rec.stats if variant_rec.ok else None,
                    "output_reference": oracle,
                }

            rows.append(row(bug, 1, "bug", None, buggy_src, oracle_bug))
            for spec in neg_specs:
                neg, _ = trace_version(name, spec["source"], sig, java_inputs, input_reprs,
                                       f"negative_{spec['transformation']}")
                oracle_neg = oracle_outputs(name, spec["source"], sig, java_inputs)
                rows.append(row(neg, 0, "sp_negative", spec["transformation"],
                                spec["source"], oracle_neg))
            ledger[key] = {
                "status": "scored", "entry": sig["method"],
                "param_types": [t for _, t in sig["params"]],
                "n_inputs": len(inputs), "base_ok": base.ok,
                "base_failure": base.failure_kind, "buggy_ok": bug.ok,
                "buggy_failure": bug.failure_kind,
                "negatives": negatives_cache[name][0]["log"] if negatives_cache[name] else [],
                "wall_s": round(time.monotonic() - t0, 1),
                "base_trace_info": binfo, "buggy_trace_info": uinfo,
            }
            print(f"  [{regime}] {name}: base={base.ok} buggy={bug.ok} "
                  f"negatives={len(neg_specs)} {ledger[key]['wall_s']}s", flush=True)

    with PAIRS_PATH.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    result = analyse(rows, ledger, manifest, manifest_hash)
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    return result


EXEC_PREDICTORS = ("sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state", "exception_fraction",
                   "exception_component_v3", "exception_type_jaccard", "call_count",
                   "n_functions", "coverage_size", "combined_shortcut", "static_token")
COMPARATORS = ("static_token", "exception_fraction", "call_count", "sbg_v3")


def _threshold() -> Optional[Dict[str, Any]]:
    if not THRESHOLD_PATH.exists():
        return None
    data = json.loads(THRESHOLD_PATH.read_text())
    for key in ("tau_star", "threshold", "value", "tau"):
        if isinstance(data.get(key), (int, float)):
            return {"tau_star": float(data[key]), "source": str(THRESHOLD_PATH.relative_to(REPO_ROOT)),
                    "sha256": _sha256(THRESHOLD_PATH)}
    return None


def _regime_stats(rows: List[dict], tau: Optional[Dict[str, Any]]) -> dict:
    rows_all = rows
    ev = [r for r in rows if r["evaluated"]]
    out: Dict[str, Any] = {
        "denominators": {
            "ALL_pairs": len(rows_all),
            "ALL_positives": sum(r["label"] for r in rows_all),
            "ALL_negatives": sum(1 - r["label"] for r in rows_all),
            "EVALUABLE_pairs": len(ev),
            "EVALUABLE_positives": sum(r["label"] for r in ev),
            "EVALUABLE_negatives": sum(1 - r["label"] for r in ev),
            "programs_with_any_evaluable_pair": len({r["program"] for r in ev}),
            "programs_with_evaluable_positive_and_negative": len(
                {r["program"] for r in ev if r["label"] == 1}
                & {r["program"] for r in ev if r["label"] == 0}),
        },
        "failures": dict(collections.Counter(
            f"{r['failure']['side']}:{r['failure']['kind']}" for r in rows_all if not r["evaluated"])),
    }
    labels = [r["label"] for r in ev]
    clusters = [r["program"] for r in ev]
    two_class = 0 < sum(labels) < len(labels)
    per = {}
    for pred in EXEC_PREDICTORS:
        d = [r["scores"][pred] for r in ev]
        if not two_class:
            per[pred] = {"auroc": None, "reason": "single-class evaluable set"}
            continue
        lo, hi, n_eff = st.cluster_bootstrap_ci(d, labels, clusters)
        per[pred] = {
            "auroc": round(st.auroc(d, labels), 4),
            "ci95": [round(lo, 4), round(hi, 4)], "n_clusters": n_eff,
            "permutation_p": round(st.cluster_permutation_p(d, labels, clusters), 4),
        }
    out["EVALUABLE"] = {"predictors": per}
    if two_class:
        d5 = [r["scores"]["sbg_v5"] for r in ev]
        out["EVALUABLE"]["noise_floor"] = st.label_shuffle_noise_floor(d5, labels, clusters)
        raw = {}
        deltas = {}
        for comp in COMPARATORS:
            dc = [r["scores"][comp] for r in ev]
            res = st.paired_cluster_bootstrap_delta(d5, dc, labels, clusters)
            deltas[comp] = res
            p_two = res.get("p_two_sided")
            raw[comp] = 1.0 if p_two is None else float(p_two)
        holm = st.holm_bonferroni(raw)
        out["EVALUABLE"]["paired_vs_sbg_v5"] = {
            c: dict(deltas[c], holm=holm[c]) for c in COMPARATORS}
    # ALL: unevaluable pairs scored at distance 0, as in the main evaluation.
    if 0 < sum(r["label"] for r in rows_all) < len(rows_all):
        d_all = [r["scores"]["sbg_v5"] if r["evaluated"] else 0.0 for r in rows_all]
        l_all = [r["label"] for r in rows_all]
        c_all = [r["program"] for r in rows_all]
        lo, hi, n_eff = st.cluster_bootstrap_ci(d_all, l_all, c_all)
        out["ALL"] = {"sbg_v5_auroc": round(st.auroc(d_all, l_all), 4),
                      "ci95": [round(lo, 4), round(hi, 4)], "n_clusters": n_eff}
    # Output-reading reference (not SBG).
    ref = [r for r in ev if r["output_reference"] is not None]
    pos_ref = [r for r in ref if r["label"] == 1]
    neg_ref = [r for r in ref if r["label"] == 0]
    out["output_reading_reference"] = {
        "note": "Reads program outputs. A ceiling for comparison; never an SBG result.",
        "positives_detected": sum(r["output_reference"]["differs"] for r in pos_ref),
        "positives": len(pos_ref),
        "negatives_flagged": sum(r["output_reference"]["differs"] for r in neg_ref),
        "negatives": len(neg_ref),
    }
    if tau is not None:
        t = tau["tau_star"]
        pos = [r for r in ev if r["label"] == 1]
        neg = [r for r in ev if r["label"] == 0]
        tp = sum(r["scores"]["sbg_v5"] > t for r in pos)
        fp = sum(r["scores"]["sbg_v5"] > t for r in neg)
        out["detection_at_frozen_tau"] = {
            "tau_star": t, "rule": "detected iff sbg_v5 > tau*",
            "positives_detected": tp, "positives": len(pos),
            "detection_rate": round(tp / len(pos), 4) if pos else None,
            "detection_wilson95": [round(x, 4) for x in st.wilson_interval(tp, len(pos))] if pos else None,
            "negatives_flagged": fp, "negatives": len(neg),
            "false_positive_rate": round(fp / len(neg), 4) if neg else None,
            "fpr_wilson95": [round(x, 4) for x in st.wilson_interval(fp, len(neg))] if neg else None,
        }
    else:
        out["detection_at_frozen_tau"] = {"status": "threshold_not_yet_frozen"}
    return out


def analyse(rows: List[dict], ledger: Dict[str, dict], manifest: dict,
            manifest_hash: str) -> dict:
    tau = _threshold()
    regimes = sorted({r["regime"] for r in rows} | {k.split(":")[0] for k in ledger})
    by_regime = {rg: _regime_stats([r for r in rows if r["regime"] == rg], tau) for rg in regimes}
    excl = collections.Counter(
        f"{k.split(':')[0]}:{v['reason']}" for k, v in ledger.items() if v["status"] == "excluded")
    return {
        "experiment": "QUIXBUGS_JAVA_SBG_SCHEMA_EVALUATION",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "criterion": ("Pre-registered (PHASE2_PREREGISTRATION.md §6): Java counts as an SBG "
                      "evaluation only if Java traces yield the same feature schema as Python. "
                      "Traces here carry call/line/return/exception events with function name, "
                      "line and Python-repr local snapshots, per-trace coverage, top-level "
                      "exception type and truncation, and are featurised by "
                      "extraction._trace_and_record, the function that featurises Python traces."),
        "schema_differences": [
            "Calls into the Java class library are opaque (not traced), as C-implemented "
            "builtins are opaque to sys.settrace; pure-Python stdlib callees are traced in "
            "Python, but the QuixBugs Python programs make few such calls.",
            "Line events come from breakpoints on every line-table location; a later "
            "bytecode location on the same line is not a new line event, matching "
            "sys.settrace's new-line-or-backward-jump rule. Static initialisers are not "
            "traced (module import is not traced in Python) and classes are preloaded "
            "before the first trace.",
            "Collection locals other than arrays, ArrayList and Arrays$ArrayList are "
            "rendered as size-correct placeholders; the state genome reduces collections "
            "to NULL/EMPTY/SINGLETON/MULTI_ELEMENT, which placeholders preserve.",
            "Per-trace budget is 1.0 s plus 3 ms per recorded event (debugger round-trip "
            "allowance, fixed before scoring); non-termination is 2 timeouts within a run, "
            "as in the Python runner.",
        ],
        "protocol": {
            "entry": "QuixBugs convention: public static method named after the class",
            "canonical_inputs": "experiments/final/protocol.py batteries via its zip rule, "
                                "mapped by Java parameter type (java_family)",
            "declared_inputs": "input half of json_testcases, first 11 cases; expected "
                               "outputs dropped at vendoring",
            "n_runs": N_RUNS, "max_events": MAX_EVENTS,
            "trace_timeout_ms": TRACE_TIMEOUT_MS,
            "per_event_allowance_ms": PER_EVENT_ALLOWANCE_MS,
            "negatives": "J-SP4 comment strip, J-SP10 format normalise, J-SP3 dead block; "
                         "kept only if javac output is byte-identical ignoring line tables; "
                         "SP-1/SP-2 renames are not implemented for Java and are omitted",
            "static_ast": "not computable for Java (no Java AST in the Python stdlib); "
                          "static_token uses a Java lexer with the same multiset distance",
        },
        "corpus": {
            "manifest": "external/quixbugs_java/MANIFEST.json",
            "manifest_sha256": manifest_hash,
            "source_repository": manifest["source_repository"],
            "commit": manifest["commit"], "license": manifest["license"],
            "n_programs_in_manifest": len(manifest["programs"]),
        },
        "schema_parity_evidence": {
            "tests": "tests/test_external_java.py",
            "checks": [
                "test_gcd_trace_structure_matches_python: QuixBugs GCD in Java and Python "
                "yield identical call/return/exception sequences, identical line-event "
                "counts and identical call-event local snapshots on 4 inputs",
                "test_exception_propagation_matches_python: an exception raised two frames "
                "deep, caught in one path and escaping in another, yields the identical "
                "CPython event sequence (exception/return in every frame it passes)",
                "test_java_traces_featurise_through_python_pipeline: V3, temporal and state "
                "genomes all build from Java traces via extraction._trace_and_record",
            ],
        },
        "supersedes": {
            "artifact": "results/external/QUIXBUGS_JAVA_EVALUATION_RESULTS.json",
            "reported": "6/18 detected (33.3%), 'transfer delta -27.4 pp' vs Python",
            "what_it_measured": (
                "A five-feature 'EEP' score (exception fraction 0.40, exception-type Jaccard "
                "0.10, trace length 0.30, hashed method-entry sequence 0.15, drift fixed at 0) "
                "over method ENTER/EXIT/EXCEPTION markers only -- no line events, no locals, "
                "no coverage. It is not the SBG V5 distance and none of the three SBG genomes "
                "can be built from those markers. tau* = 0.08 was taken from a different "
                "calibration. 22 of 40 programs were excluded, including 3 whose buggy "
                "version does not terminate (E_TIMEOUT) and 5 compile failures of the "
                "harness; there were no negative pairs, so no AUROC or false-positive rate "
                "existed, and the binomial test against p0 = 0.5 has no meaning for a "
                "detector without a measured false-positive rate."),
            "status": "SUPERSEDED -- not an SBG result; must not be cited as one",
        },
        "threshold": tau or {"status": "not_yet_frozen",
                             "note": "detection rates are filled in by `finalize` from the "
                                     "stored per-pair distances once THRESHOLD_FROZEN.json exists"},
        "exclusions": dict(excl),
        "ledger": ledger,
        "results": by_regime,
        "pairs_file": str(PAIRS_PATH.relative_to(REPO_ROOT)),
    }


def finalize() -> dict:
    rows = [json.loads(l) for l in PAIRS_PATH.read_text().splitlines() if l.strip()]
    prev = json.loads(RESULT_PATH.read_text())
    manifest = _load_manifest()
    result = analyse(rows, prev["ledger"], manifest, prev["corpus"]["manifest_sha256"])
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("vendor", "run", "finalize"))
    ap.add_argument("--source", type=pathlib.Path, default=None)
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--regimes", nargs="*", default=["canonical", "declared"])
    a = ap.parse_args()
    if a.command == "vendor":
        m = vendor(a.source)
        print(f"vendored {len(m['programs'])} programs at {m['commit']}")
    elif a.command == "run":
        r = evaluate(a.regimes, a.only)
        print(json.dumps({k: v["denominators"] for k, v in r["results"].items()}, indent=1))
    else:
        finalize()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
