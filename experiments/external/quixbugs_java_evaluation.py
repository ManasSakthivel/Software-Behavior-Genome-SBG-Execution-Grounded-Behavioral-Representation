"""
experiments/external/quixbugs_java_evaluation.py
=================================================
QuixBugs Java — Zero-Shot Cross-Language EEP Evaluation

PROTOCOL:
  - Parameters FROZEN from synthetic Python evaluation:
      τ* = 0.08
      No re-tuning on Java data
  - Zero-shot: Python-frozen configuration → Java evaluation
  - Output-free constraint maintained for Java:
      Only stderr trace events (ENTER/EXIT/EXCEPTION) consumed
      stdout (functional output) never read
  - Selection criteria frozen BEFORE inspecting results

INSTRUMENTATION:
  Methods inside the target Java class are instrumented with
  TRACE ENTER / TRACE EXIT / TRACE EXCEPTION on stderr.
  This is the Java analog of Python's sys.settrace:
  - Python: sys.settrace captures every line event
  - Java:   Method-boundary injection captures ENTER/EXIT events
  Both are output-free: trace structure, not values.

SELECTION CRITERIA (frozen pre-evaluation):
  E_NODE:         Uses Node/graph class
  E_COMPLEX_TYPE: Non-trivial type serialization (nested objects, mixed lists)
  E_NO_TC:        No json_testcases file
  E_NO_SIG:       Method signature not mapped
  E_COMPILE:      Source fails to compile (either version)
  E_TIMEOUT:      Execution exceeds timeout
  E_NO_TRACE:     No trace events produced

Usage:
    python3 experiments/external/quixbugs_java_evaluation.py
    python3 experiments/external/quixbugs_java_evaluation.py \\
        --quixbugs-dir /tmp/quixbugs_full
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "results" / "external"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# FROZEN PARAMETERS
# ============================================================
TAU_STAR = 0.08
SEED = 42
DEFAULT_QUIXBUGS_DIR = "/tmp/quixbugs_full"
TIMEOUT_S = 15
MAX_TESTCASES = 10
MAX_TRACE_LINES = 5000  # hard cap per run

JAVAC_PATH = "/usr/bin/javac"
JAVA_PATH  = "/usr/bin/java"

W_EXC_FRAC   = 0.40
W_EXC_JAC    = 0.10
W_TRACE_LEN  = 0.30
W_METHOD_SEQ = 0.15
W_DRIFT      = 0.05

# ============================================================
# Bug types (same classification as Python QuixBugs)
# ============================================================
BUG_TYPES = {
    "BITCOUNT":                   "wrong_operator",
    "BUCKETSORT":                 "wrong_return",
    "FIND_FIRST_IN_SORTED":       "off_by_one",
    "FIND_IN_SORTED":             "wrong_variable",
    "FLATTEN":                    "wrong_return",
    "GCD":                        "wrong_variable",
    "GET_FACTORS":                "missing_return",
    "HANOI":                      "wrong_variable",
    "IS_VALID_PARENTHESIZATION":  "wrong_condition",
    "KHEAPSORT":                  "off_by_one",
    "KNAPSACK":                   "wrong_condition",
    "KTH":                        "wrong_variable",
    "LCS_LENGTH":                 "wrong_operator",
    "LEVENSHTEIN":                "wrong_recursion",
    "LIS":                        "wrong_condition",
    "LONGEST_COMMON_SUBSEQUENCE": "wrong_recursion",
    "MAX_SUBLIST_SUM":            "wrong_variable",
    "MERGESORT":                  "wrong_condition",
    "NEXT_PALINDROME":            "off_by_one",
    "NEXT_PERMUTATION":           "wrong_variable",
    "PASCAL":                     "off_by_one",
    "POSSIBLE_CHANGE":            "wrong_condition",
    "POWERSET":                   "wrong_return",
    "QUICKSORT":                  "off_by_one",
    "RPN_EVAL":                   "wrong_operator",
    "SHUNTING_YARD":              "wrong_condition",
    "SIEVE":                      "wrong_condition",
    "SQRT":                       "off_by_one",
    "SUBSEQUENCES":               "wrong_recursion",
    "TO_BASE":                    "wrong_operator",
    "WRAP":                       "wrong_condition",
}

# Programs requiring Node/graph data structures
NODE_PROGRAMS = {
    "BREADTH_FIRST_SEARCH", "DEPTH_FIRST_SEARCH", "DETECT_CYCLE",
    "REVERSE_LINKED_LIST", "MINIMUM_SPANNING_TREE", "SHORTEST_PATH_LENGTH",
    "SHORTEST_PATH_LENGTHS", "SHORTEST_PATHS", "TOPOLOGICAL_ORDERING",
}

# Programs with non-trivial type serialization
COMPLEX_TYPE_PROGRAMS = {
    "FLATTEN",       # Object recursion — nested lists without type schema
    "RPN_EVAL",      # ArrayList<Object> with mixed types (int/String operators)
    "SHUNTING_YARD", # Same mixed type issue
    "KNAPSACK",      # int[][] — excluded from harness for simplicity
}


# ============================================================
# Java source instrumentation
# ============================================================

_METHOD_RE = re.compile(
    r"""
    (                                   # group 1: full declaration
      (?:(?:public|private|protected|static|final|synchronized)\s+)+
      [\w<>\[\],\s]+?                   # return type
      \s+
      (\w+)                             # group 2: method name
      \s*
      \([^)]*\)                         # params
      (?:\s+throws\s+[\w,\s]+)?         # optional throws
      \s*
    )
    \{                                  # opening brace
    """,
    re.VERBOSE,
)


def instrument_java_source(source: str, class_name: str) -> str:
    """
    Inject TRACE ENTER/EXIT/EXCEPTION into every non-constructor,
    non-main method of the Java source.

    Output-free guarantee:
    - Trace lines go to System.err
    - stdout is untouched
    - Only method names and depth are emitted (no values)
    """
    # If already instrumented, skip
    if "TRACE ENTER" in source:
        return source

    # Insert static depth counter after class opening brace
    source = re.sub(
        r"(class\s+\w+[^{]*\{)",
        r"\1\n    static int _eepDepth = 0;\n",
        source,
        count=1,
    )

    result_parts: List[str] = []
    pos = 0

    for m in _METHOD_RE.finditer(source):
        method_name = m.group(2)
        # Skip constructors, main, <clinit>, <init>
        if method_name in ("main", "clinit", "init") or method_name == class_name:
            continue

        open_brace_pos = m.end() - 1  # position of '{'
        close_pos = _find_matching_brace(source, open_brace_pos)
        if close_pos is None:
            continue

        # Emit everything up to and including opening brace
        result_parts.append(source[pos:open_brace_pos + 1])

        # Inject ENTER + try{
        result_parts.append(
            f'\n        _eepDepth++;\n'
            f'        System.err.println("TRACE ENTER {method_name} depth=" + _eepDepth);\n'
            f'        try {{\n'
        )

        # Emit original method body
        result_parts.append(source[open_brace_pos + 1:close_pos])

        # Inject catch/finally + closing brace for the method
        result_parts.append(
            f'\n        }} catch (Throwable _eepT) {{\n'
            f'            System.err.println("TRACE EXCEPTION " + _eepT.getClass().getSimpleName() + " depth=" + _eepDepth);\n'
            f'            throw _eepT;\n'
            f'        }} finally {{\n'
            f'            System.err.println("TRACE EXIT {method_name} depth=" + _eepDepth);\n'
            f'            _eepDepth--;\n'
            f'        }}\n'
            f'    }}\n'    # close the method itself (replaces original closing brace)
        )

        pos = close_pos + 1  # skip the original closing brace (replaced above)

    result_parts.append(source[pos:])
    return "".join(result_parts)


def _find_matching_brace(source: str, open_pos: int) -> Optional[int]:
    depth = 0
    in_string = False
    in_char = False
    in_line_comment = False
    in_block_comment = False
    i = open_pos
    while i < len(source):
        c = source[i]
        # Handle comments
        if in_line_comment:
            if c == '\n':
                in_line_comment = False
        elif in_block_comment:
            if c == '*' and i + 1 < len(source) and source[i + 1] == '/':
                in_block_comment = False
                i += 1
        elif in_string:
            if c == '\\':
                i += 1
            elif c == '"':
                in_string = False
        elif in_char:
            if c == '\\':
                i += 1
            elif c == "'":
                in_char = False
        else:
            if c == '/' and i + 1 < len(source):
                if source[i + 1] == '/':
                    in_line_comment = True
                    i += 1
                elif source[i + 1] == '*':
                    in_block_comment = True
                    i += 1
            elif c == '"':
                in_string = True
            elif c == "'":
                in_char = True
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return None


# ============================================================
# Known method signatures for harness generation
# ============================================================

_KNOWN_SIGNATURES: Dict[str, Dict] = {
    "BITCOUNT":      {"method": "bitcount",      "params": [("n", "int")]},
    "BUCKETSORT":    {"method": "bucketsort",     "params": [("arr", "List<Integer>"), ("k", "int")]},
    "FIND_FIRST_IN_SORTED": {"method": "find_first_in_sorted",
                              "params": [("arr", "List<Integer>"), ("x", "int")]},
    "FIND_IN_SORTED":{"method": "find_in_sorted", "params": [("arr", "List<Integer>"), ("x", "int")]},
    "GCD":           {"method": "gcd",            "params": [("a", "int"), ("b", "int")]},
    "GET_FACTORS":   {"method": "get_factors",    "params": [("n", "int")]},
    "HANOI":         {"method": "hanoi",          "params": [("height", "int"), ("start", "int"), ("end", "int")]},
    "IS_VALID_PARENTHESIZATION": {"method": "is_valid_parenthesization",
                                   "params": [("parens", "String")]},
    "KHEAPSORT":     {"method": "kheapsort",      "params": [("arr", "List<Integer>"), ("k", "int")]},
    "KTH":           {"method": "kth",            "params": [("arr", "List<Integer>"), ("k", "int")]},
    "LCS_LENGTH":    {"method": "lcs_length",     "params": [("s", "String"), ("t", "String")]},
    "LEVENSHTEIN":   {"method": "levenshtein",    "params": [("source", "String"), ("target", "String")]},
    "LIS":           {"method": "lis",            "params": [("arr", "List<Integer>")]},
    "LONGEST_COMMON_SUBSEQUENCE": {"method": "longest_common_subsequence",
                                    "params": [("s", "String"), ("t", "String")]},
    "MAX_SUBLIST_SUM": {"method": "max_sublist_sum", "params": [("arr", "List<Integer>")]},
    "MERGESORT":     {"method": "mergesort",      "params": [("arr", "List<Integer>")]},
    "NEXT_PALINDROME": {"method": "next_palindrome", "params": [("digit_list", "int[]")]},
    "NEXT_PERMUTATION": {"method": "next_permutation", "params": [("perm", "List<Integer>")]},
    "PASCAL":        {"method": "pascal",         "params": [("n", "int")]},
    "POSSIBLE_CHANGE": {"method": "possible_change",
                        "params": [("coins", "List<Integer>"), ("total", "int")]},
    "POWERSET":      {"method": "powerset",       "params": [("arr", "List<Integer>")]},
    "QUICKSORT":     {"method": "quicksort",      "params": [("arr", "List<Integer>")]},
    "SIEVE":         {"method": "sieve",          "params": [("max", "int")]},
    "SQRT":          {"method": "sqrt",           "params": [("x", "int"), ("approx", "double")]},
    "SUBSEQUENCES":  {"method": "subsequences",   "params": [("a", "int"), ("b", "int"), ("k", "int")]},
    "TO_BASE":       {"method": "to_base",        "params": [("num", "int"), ("b", "int")]},
    "WRAP":          {"method": "wrap",           "params": [("text", "String"), ("cols", "int")]},
}


# ============================================================
# Test case parsing and argument serialization
# ============================================================

def load_testcases(prog_name: str, quixbugs_dir: str) -> Optional[List]:
    path = Path(quixbugs_dir) / "json_testcases" / f"{prog_name.lower()}.json"
    if not path.exists():
        return None
    cases = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                tc = json.loads(line)
                if isinstance(tc, list) and len(tc) >= 2:
                    cases.append(tc[0])
            except json.JSONDecodeError:
                pass
    return cases[:MAX_TESTCASES] if cases else None


def py_to_java_literal(value: Any, jtype: str) -> Optional[str]:
    """Convert a Python value to a Java literal or constructor expression."""
    if value is None:
        return "null"

    # int
    if jtype == "int":
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(int(value))
        return None

    # double
    if jtype == "double":
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(float(value))
        return None

    # String
    if jtype == "String":
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return None

    # List<Integer> / ArrayList<Integer>
    if "List<Integer>" in jtype:
        if isinstance(value, list) and all(
            isinstance(v, (int, float)) and not isinstance(v, bool) for v in value
        ):
            items = ", ".join(f"Integer.valueOf({int(v)})" for v in value)
            return f"new ArrayList<>(Arrays.asList({items}))"
        return None

    # int[]
    if jtype == "int[]":
        if isinstance(value, list) and all(
            isinstance(v, (int, float)) and not isinstance(v, bool) for v in value
        ):
            items = ", ".join(str(int(v)) for v in value)
            return f"new int[]{{{items}}}"
        return None

    return None


def build_harness_java(class_name: str, sig: Dict, test_cases: List) -> Optional[str]:
    """Build a Java main harness that drives class_name.method."""
    method = sig["method"]
    params = sig["params"]

    case_methods = []
    for i, tc_args in enumerate(test_cases):
        if not isinstance(tc_args, list):
            tc_args = [tc_args]
        if len(tc_args) != len(params):
            return None
        arg_lits = []
        for arg, (pname, ptype) in zip(tc_args, params):
            lit = py_to_java_literal(arg, ptype)
            if lit is None:
                return None
            arg_lits.append(lit)

        call = f"{class_name}.{method}({', '.join(arg_lits)});"
        case_methods.append(
            f"    static void case_{i}() {{ {call} }}"
        )

    dispatch = "\n".join(
        f"        if (idx == {i}) case_{i}();" for i in range(len(test_cases))
    )

    return f"""\
package java_programs;
import java.util.*;
import java.io.*;

public class {class_name}_EEPHarness {{
    public static void main(String[] args) {{
        int idx = 0;
        if (args.length > 0) {{
            try {{ idx = Integer.parseInt(args[0]); }} catch (Exception e) {{}}
        }}
{dispatch}
    }}
{chr(10).join(case_methods)}
}}
"""


# ============================================================
# Compilation and execution
# ============================================================

def compile_program(
    prog_name: str,
    source: str,
    harness: str,
    class_dir: Path,
) -> bool:
    """Compile instrumented source + harness into class_dir."""
    src_path = class_dir / f"{prog_name}.java"
    src_path.write_text(source, encoding="utf-8")
    harness_path = class_dir / f"{prog_name}_EEPHarness.java"
    harness_path.write_text(harness, encoding="utf-8")

    try:
        result = subprocess.run(
            [JAVAC_PATH, "-d", str(class_dir.parent),
             str(src_path), str(harness_path)],
            capture_output=True, text=True, timeout=30,
        )
        return result.returncode == 0
    except Exception:
        return False


def run_case(
    class_dir: Path,
    class_name: str,
    case_idx: int,
    timeout: float = TIMEOUT_S,
) -> Tuple[List[str], bool]:
    """
    Run the harness for case_idx.
    Returns (stderr_lines, timed_out).
    stdout is captured and DISCARDED (never used for scoring).
    """
    harness_cls = f"java_programs.{class_name}_EEPHarness"
    try:
        result = subprocess.run(
            [JAVA_PATH, "-cp", str(class_dir), harness_cls, str(case_idx)],
            input="",
            capture_output=True, text=True, timeout=timeout,
        )
        # Limit trace lines to MAX_TRACE_LINES
        lines = result.stderr.splitlines()[:MAX_TRACE_LINES]
        return lines, False
    except subprocess.TimeoutExpired:
        return ["TRACE EXCEPTION TimeoutExpired depth=0"], True
    except Exception:
        return [], False


# ============================================================
# Trace parsing
# ============================================================

_TRACE_RE = re.compile(
    r"^TRACE\s+(ENTER|EXIT|EXCEPTION)\s+(\S+)(?:\s+depth=(\d+))?(?:\s+(.+))?$"
)


def parse_events(lines: List[str]) -> List[Dict]:
    events = []
    for line in lines:
        m = _TRACE_RE.match(line.strip())
        if m:
            events.append({
                "type": m.group(1),
                "method": m.group(2),
                "depth": int(m.group(3) or 0),
                "exc": m.group(4) if m.group(1) == "EXCEPTION" else None,
            })
    return events


# ============================================================
# EEP distance (Java adapter)
# ============================================================

def compute_java_eep(
    traces_b: List[List[Dict]],
    traces_f: List[List[Dict]],
) -> Tuple[float, Dict]:
    """Java-adapted EEP distance. Same formula, Java-appropriate features."""
    n = min(len(traces_b), len(traces_f))
    if n == 0:
        return 0.0, {}

    # d1: exception fraction
    def exc_frac(traces):
        return sum(
            1 for t in traces if any(e["type"] == "EXCEPTION" for e in t)
        ) / max(len(traces), 1)

    d1 = abs(exc_frac(traces_b[:n]) - exc_frac(traces_f[:n]))

    # d2: exception type jaccard
    def exc_types(traces):
        s: Set[str] = set()
        for t in traces:
            for e in t:
                if e["type"] == "EXCEPTION" and e["exc"]:
                    s.add(e["exc"])
        return s

    et_b = exc_types(traces_b[:n])
    et_f = exc_types(traces_f[:n])
    union_sz = len(et_b | et_f)
    d2 = 0.0 if union_sz == 0 else 1.0 - len(et_b & et_f) / union_sz

    # d3: trace length distance (all events)
    lens_b = [len(t) for t in traces_b[:n]]
    lens_f = [len(t) for t in traces_f[:n]]
    max_len = max(max(lens_b, default=1), max(lens_f, default=1), 1)
    d3 = min(1.0, sum(abs(a - b) / max_len for a, b in zip(lens_b, lens_f)) / n)

    # d4: method-call sequence divergence (anonymized ENTER sequences)
    name_map: Dict[str, int] = {}

    def method_hash(trace: List[Dict]) -> str:
        parts = []
        for e in trace:
            if e["type"] == "ENTER":
                nm = e["method"]
                if nm not in name_map:
                    name_map[nm] = len(name_map)
                parts.append(str(name_map[nm]))
        return hashlib.md5("|".join(parts).encode()).hexdigest()[:12]

    hashes_b = [method_hash(t) for t in traces_b[:n]]
    hashes_f = [method_hash(t) for t in traces_f[:n]]
    d4 = sum(1 for a, b in zip(hashes_b, hashes_f) if a != b) / n

    d5 = 0.0  # sequential drift: 0 for stateless programs

    total = (
        W_EXC_FRAC * d1 + W_EXC_JAC * d2 +
        W_TRACE_LEN * d3 + W_METHOD_SEQ * d4 + W_DRIFT * d5
    )
    total = max(0.0, min(1.0, total))

    return round(total, 6), {
        "d_exc_frac":    round(d1, 6),
        "d_exc_jac":     round(d2, 6),
        "d_trace_length": round(d3, 6),
        "d_method_seq":  round(d4, 6),
        "d_sequential_drift": 0.0,
    }


# ============================================================
# Per-program evaluation
# ============================================================

def evaluate_program(
    prog_name: str,
    quixbugs_dir: str,
    test_cases: List,
) -> Dict:
    sig = _KNOWN_SIGNATURES.get(prog_name)
    if sig is None:
        return {"status": "E_NO_SIG", "prog": prog_name}

    # Load source files
    buggy_src_path = Path(quixbugs_dir) / "java_programs" / f"{prog_name}.java"
    fixed_src_path = Path(quixbugs_dir) / "correct_java_programs" / f"{prog_name}.java"
    if not buggy_src_path.exists():
        return {"status": "E_COMPILE", "prog": prog_name, "detail": "buggy source missing"}
    if not fixed_src_path.exists():
        return {"status": "E_COMPILE", "prog": prog_name, "detail": "fixed source missing"}

    buggy_src = buggy_src_path.read_text(encoding="utf-8", errors="ignore")
    fixed_src = fixed_src_path.read_text(encoding="utf-8", errors="ignore")

    # Normalize package to java_programs for both
    buggy_src = re.sub(r"package\s+\w+;", "package java_programs;", buggy_src)
    fixed_src = re.sub(r"package\s+\w+;", "package java_programs;", fixed_src)

    # Instrument both sources
    buggy_instr = instrument_java_source(buggy_src, prog_name)
    fixed_instr = instrument_java_source(fixed_src, prog_name)

    # Generate harness
    harness = build_harness_java(prog_name, sig, test_cases)
    if harness is None:
        return {"status": "E_COMPLEX_TYPE", "prog": prog_name}

    with tempfile.TemporaryDirectory(prefix=f"qbj_{prog_name}_") as tmpdir:
        tmp = Path(tmpdir)
        buggy_dir = tmp / "buggy"
        fixed_dir = tmp / "fixed"
        buggy_pkg = buggy_dir / "java_programs"
        fixed_pkg = fixed_dir / "java_programs"
        buggy_pkg.mkdir(parents=True)
        fixed_pkg.mkdir(parents=True)

        # Compile buggy
        if not compile_program(prog_name, buggy_instr, harness, buggy_pkg):
            return {"status": "E_COMPILE", "prog": prog_name, "detail": "buggy compile failed"}

        # Compile fixed
        if not compile_program(prog_name, fixed_instr, harness, fixed_pkg):
            return {"status": "E_COMPILE", "prog": prog_name, "detail": "fixed compile failed"}

        # Run all test cases
        traces_b: List[List[Dict]] = []
        traces_f: List[List[Dict]] = []
        timed_out = False

        for i in range(len(test_cases)):
            lines_b, to_b = run_case(buggy_dir, prog_name, i)
            lines_f, to_f = run_case(fixed_dir, prog_name, i)
            if to_b or to_f:
                timed_out = True
                break
            traces_b.append(parse_events(lines_b))
            traces_f.append(parse_events(lines_f))

        if timed_out:
            return {"status": "E_TIMEOUT", "prog": prog_name}

        # Sanity: at least some trace events produced
        total_events = sum(len(t) for t in traces_b + traces_f)
        if total_events == 0:
            return {"status": "E_NO_TRACE", "prog": prog_name}

        d_eep, comps = compute_java_eep(traces_b, traces_f)
        detected = d_eep > TAU_STAR

        # Collect per-case trace lengths for analysis
        lens_b = [len(t) for t in traces_b]
        lens_f = [len(t) for t in traces_f]

        return {
            "status": "OK",
            "prog": prog_name,
            "bug_type": BUG_TYPES.get(prog_name, "unknown"),
            "eep_distance": d_eep,
            "detected_eep": detected,
            "n_test_cases": len(test_cases),
            "mean_trace_len_buggy": round(sum(lens_b) / max(len(lens_b), 1), 1),
            "mean_trace_len_fixed": round(sum(lens_f) / max(len(lens_f), 1), 1),
            **comps,
        }


# ============================================================
# Statistics helpers
# ============================================================

def wilson_ci(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def binomial_p(k: int, n: int, p0: float = 0.5) -> float:
    from math import comb
    return sum(comb(n, i) * (p0**i) * ((1 - p0)**(n - i)) for i in range(k, n + 1))


# ============================================================
# Main
# ============================================================

def main(quixbugs_dir: str = DEFAULT_QUIXBUGS_DIR):
    t0 = time.time()
    print("=" * 70)
    print("QUIXBUGS JAVA — EEP ZERO-SHOT CROSS-LANGUAGE EVALUATION")
    print("=" * 70)
    print(f"QuixBugs dir: {quixbugs_dir}")
    print(f"τ* = {TAU_STAR}  (FROZEN — no tuning on Java data)")
    print(f"Instrumentation: method-boundary TRACE ENTER/EXIT/EXCEPTION → stderr")
    print(f"Output-free: stdout (functional output) never read for scoring")
    print()

    if not os.path.isfile(JAVAC_PATH):
        print(f"ERROR: javac not found at {JAVAC_PATH}")
        sys.exit(1)

    java_progs_dir   = Path(quixbugs_dir) / "java_programs"
    correct_progs_dir = Path(quixbugs_dir) / "correct_java_programs"

    buggy_progs   = {f.stem for f in java_progs_dir.glob("*.java")
                     if f.stem not in ("Node", "WeightedEdge")}
    correct_progs = {f.stem for f in correct_progs_dir.glob("*.java")}
    all_candidates = sorted(buggy_progs & correct_progs)

    print(f"Total Java program pairs: {len(all_candidates)}")

    results: List[Dict] = []
    excluded: List[Dict] = []

    print(f"\n{'Program':<35} {'Status':<22} {'EEP':<7} {'Det'}")
    print(f"{'─'*35} {'─'*22} {'─'*7} {'─'*3}")

    for prog in all_candidates:
        # E_NODE
        if prog in NODE_PROGRAMS:
            excluded.append({"prog": prog, "reason": "E_NODE"})
            print(f"  {prog:<33} E_NODE")
            continue

        # E_COMPLEX_TYPE
        if prog in COMPLEX_TYPE_PROGRAMS:
            excluded.append({"prog": prog, "reason": "E_COMPLEX_TYPE"})
            print(f"  {prog:<33} E_COMPLEX_TYPE")
            continue

        # E_NO_TC
        tcs = load_testcases(prog, quixbugs_dir)
        if not tcs:
            excluded.append({"prog": prog, "reason": "E_NO_TC"})
            print(f"  {prog:<33} E_NO_TC")
            continue

        # E_NO_SIG
        if prog not in _KNOWN_SIGNATURES:
            excluded.append({"prog": prog, "reason": "E_NO_SIG"})
            print(f"  {prog:<33} E_NO_SIG")
            continue

        r = evaluate_program(prog, quixbugs_dir, tcs)

        if r["status"] != "OK":
            excluded.append({"prog": prog, "reason": r["status"],
                              "detail": r.get("detail", "")})
            print(f"  {prog:<33} {r['status']:<22} {r.get('detail','')}")
            continue

        sym = "✓" if r["detected_eep"] else "✗"
        print(f"  {prog:<33} OK                     "
              f"d={r['eep_distance']:.3f}  {sym}")
        results.append(r)

    # ── Aggregate ──
    n_total     = len(all_candidates)
    n_evaluated = len(results)
    n_excluded  = len(excluded)
    n_detected  = sum(1 for r in results if r["detected_eep"])
    det_rate    = n_detected / max(n_evaluated, 1)
    wi_lo, wi_hi = wilson_ci(n_detected, n_evaluated)
    p_binom     = binomial_p(n_detected, n_evaluated)

    print(f"\n{'─'*70}")
    print(f"QUIXBUGS JAVA RESULTS")
    print(f"{'─'*70}")
    print(f"  Total candidates:        {n_total}")
    print(f"  Excluded:                {n_excluded}")
    print(f"  Evaluated:               {n_evaluated}")
    print(f"  Detected (EEP):          {n_detected}")
    print(f"  Detection rate:          {det_rate:.1%}")
    print(f"  Wilson 95% CI:           [{wi_lo:.3f}, {wi_hi:.3f}]")
    print(f"  Binomial p (H0: p=0.5):  {p_binom:.4f}")
    print()

    # Defect-class breakdown
    by_class: Dict[str, List] = defaultdict(list)
    for r in results:
        by_class[r["bug_type"]].append(r)

    print(f"  {'Bug Type':<30} {'N':<4} {'Det':<4} {'Rate'}")
    print(f"  {'─'*30} {'─'*4} {'─'*4} {'─'*5}")
    class_results: Dict[str, Dict] = {}
    for bt in sorted(by_class.keys()):
        cases = by_class[bt]
        n = len(cases)
        d = sum(1 for c in cases if c["detected_eep"])
        print(f"  {bt:<30} {n:<4} {d:<4} {d/n:.0%}")
        class_results[bt] = {"n": n, "detected": d, "rate": round(d/n, 3)}

    # Exclusion breakdown
    exc_reasons: Dict[str, int] = defaultdict(int)
    for e in excluded:
        exc_reasons[e["reason"]] += 1
    print(f"\n  Exclusion breakdown:")
    for reason, count in sorted(exc_reasons.items()):
        print(f"    {reason}: {count}")

    # Missed programs analysis
    missed = [r for r in results if not r["detected_eep"]]
    if missed:
        print(f"\n  Missed (N={len(missed)}):")
        for r in missed:
            print(f"    {r['prog']:<35} {r['bug_type']:<25} "
                  f"d={r['eep_distance']:.3f}  "
                  f"tl_buggy={r['mean_trace_len_buggy']:.0f}  "
                  f"tl_fixed={r['mean_trace_len_fixed']:.0f}")

    # Cross-language comparison
    python_detected  = 17
    python_evaluated = 28
    python_rate      = python_detected / python_evaluated
    transfer_delta   = det_rate - python_rate
    print(f"\n  CROSS-LANGUAGE COMPARISON (zero-shot):")
    print(f"    Python QuixBugs:  {python_detected}/{python_evaluated} = {python_rate:.1%}")
    print(f"    Java QuixBugs:    {n_detected}/{n_evaluated} = {det_rate:.1%}")
    print(f"    Transfer delta:   {transfer_delta:+.1%}")
    if transfer_delta < -0.2:
        print(f"    *** NEGATIVE RESULT: significant transfer gap — instrumentation")
        print(f"        difference limits cross-language generalization claim ***")

    elapsed = time.time() - t0

    # ── Save results ──
    output = {
        "experiment": "QUIXBUGS_JAVA_EEP_EVALUATION",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tau_star": TAU_STAR,
        "seed": SEED,
        "zero_shot": True,
        "language": "Java",
        "quixbugs_dir": quixbugs_dir,
        "parameters_frozen_from": "Python_synthetic_evaluation",
        "instrumentation_method": "method_boundary_TRACE_ENTER_EXIT_stderr",
        "output_free": True,
        "stdout_used_for_scoring": False,
        "summary": {
            "n_total_candidates": n_total,
            "n_excluded": n_excluded,
            "n_evaluated": n_evaluated,
            "n_detected": n_detected,
            "detection_rate": round(det_rate, 4),
            "wilson_ci_95": [round(wi_lo, 4), round(wi_hi, 4)],
            "binomial_p": round(p_binom, 6),
        },
        "cross_language": {
            "python_quixbugs_detected":  python_detected,
            "python_quixbugs_evaluated": python_evaluated,
            "python_quixbugs_rate":      round(python_rate, 4),
            "java_quixbugs_detected":    n_detected,
            "java_quixbugs_evaluated":   n_evaluated,
            "java_quixbugs_rate":        round(det_rate, 4),
            "transfer_delta":            round(transfer_delta, 4),
            "transfer_interpretation":   (
                "POSITIVE" if transfer_delta > -0.1 else
                "MODERATE_LOSS" if transfer_delta > -0.3 else
                "SUBSTANTIAL_LOSS"
            ),
        },
        "defect_class_results": class_results,
        "per_program_results": results,
        "exclusions": excluded,
        "exclusion_breakdown": dict(exc_reasons),
        "elapsed_s": round(elapsed, 1),
    }

    out_path = RESULTS_DIR / "QUIXBUGS_JAVA_EVALUATION_RESULTS.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved: {out_path}")
    print(f"  Elapsed: {elapsed:.1f}s")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quixbugs-dir", default=DEFAULT_QUIXBUGS_DIR)
    args = parser.parse_args()
    main(args.quixbugs_dir)
