#!/usr/bin/env python3
"""
benchmark/scripts/validate_fresh_program.py
============================================
Validates a fresh program against the FRESH_PROGRAM_PROTOCOL criteria:

  1. Syntax check (ast.parse)
  2. Compile check (compile)
  3. Entry-point selection (select_entry_structural)
  4. Battery execution (no crashes on standard battery inputs)
  5. Non-trivial check (at least one conditional + loop or recursion)
  6. Jaccard overlap check against all known programs
  7. Standard-library only (no third-party imports)
  8. Deterministic execution (repeated call returns same result)

Usage:
    python3 benchmark/scripts/validate_fresh_program.py path/to/program.py [--verbose]
    python3 benchmark/scripts/validate_fresh_program.py --all-fresh       # validate all in fresh_programs/
    python3 benchmark/scripts/validate_fresh_program.py --report           # JSON report for all fresh programs
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "final"))

from entry_policy import (  # noqa: E402
    select_entry_structural,
    NoEntryPoint,
    AmbiguousEntryPoint,
    UnsupportedSignature,
    EntryPointError,
)

FRESH_DIR = REPO_ROOT / "benchmark" / "corpus" / "fresh_programs"
BASE_DIR = REPO_ROOT / "benchmark" / "corpus" / "base_programs"

# Standard library modules — anything outside this is a third-party dependency.
# We use sys.stdlib_module_names (3.10+) or a curated list for older Pythons.
try:
    STDLIB_NAMES = sys.stdlib_module_names  # type: ignore[attr-defined]
except AttributeError:
    STDLIB_NAMES = frozenset({
        "abc", "ast", "bisect", "collections", "copy", "dataclasses",
        "decimal", "enum", "functools", "heapq", "inspect", "io",
        "itertools", "json", "math", "operator", "os", "pathlib",
        "queue", "random", "re", "shutil", "signal", "socket", "stat",
        "statistics", "string", "struct", "sys", "textwrap", "threading",
        "time", "traceback", "types", "typing", "unicodedata",
        "unittest", "uuid", "weakref",
    })

# Minimal batteries duplicated here to avoid importing protocol.py
# (which has heavier deps).
LIST_BATTERY: List[Any] = [
    [], [1], [3, 1, 4, 1, 5, 9, 2, 6], [10, 9, 8, 7, 6, 5], [0, 0, 0, 0],
    [2, 1], [-3, 0, 3], list(range(8)), list(range(1)), list(range(3)),
    list(range(16)),
]
STR_BATTERY: List[str] = [
    "", "a", "abc", "3 + 4 * 2", "racecar", "hello world", "1,2,3",
    "key=value", "  padded  ", "AaBbCc", "0123456789",
]
INT_BATTERY: List[int] = [0, 1, 2, 3, 5, 8, 10, -1, -5, 16, 100]
FLOAT_BATTERY: List[float] = [0.0, 1.0, 2.5, -1.5, 0.5, 10.0, 3.14159,
                               -0.25, 100.0, 0.001, 7.0]
BOOL_BATTERY: List[bool] = [True, False] * 6
DICT_BATTERY: List[dict] = [
    {}, {"a": []}, {"a": ["b"], "b": []},
    {"a": ["b", "c"], "b": ["c"], "c": []},
    {1: [2], 2: [3], 3: [1]},
]


# Python keywords and ubiquitous builtins to exclude from Jaccard comparison.
# We want to detect algorithmically similar programs, not common Python idioms.
_STOP_WORDS = frozenset({
    # Python keywords
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
    "while", "with", "yield",
    # Ubiquitous builtins
    "abs", "all", "any", "bool", "dict", "enumerate", "float", "format",
    "getattr", "hasattr", "hash", "hex", "id", "input", "int", "isinstance",
    "issubclass", "iter", "len", "list", "map", "max", "min", "next",
    "object", "open", "ord", "print", "range", "repr", "reversed", "set",
    "setattr", "slice", "sorted", "str", "sum", "super", "tuple", "type",
    "vars", "zip",
    # Very common variable names / single letters
    "i", "j", "k", "n", "m", "x", "y", "z", "a", "b", "c", "d", "e",
    "f", "r", "s", "t", "v", "w", "lo", "hi",
    # Common attribute/method names
    "append", "pop", "get", "set", "add", "remove", "update", "clear",
    "keys", "values", "items", "split", "join", "strip", "replace",
    "startswith", "endswith", "index", "count", "copy", "extend",
    "lower", "upper", "format",
    # File-header tokens (present in every program)
    "program_id", "category", "spec_version", "provenance", "license",
    "authored", "original",
    # Docstring filler words
    "Given", "Return", "Returns", "Spec", "the", "of", "a", "an", "in",
    "to", "with", "for", "and", "or", "not", "is", "are", "be", "by",
    "that", "this", "if", "all", "any", "each", "every", "which",
    "using", "use", "used", "can", "may", "must", "will", "no", "non",
    "where", "when", "than", "from", "at", "on", "as", "its", "their",
    # Common test/assertion names
    "test", "assert", "passed", "failed", "error", "main", "run",
    "__main__", "__name__", "__init__", "__repr__", "__str__",
    # Common parameter names
    "result", "output", "value", "values", "val", "item", "items",
    "node", "nodes", "edge", "edges", "size", "length", "count", "num",
    "pos", "idx", "index", "key", "keys", "left", "right", "top", "end",
    "start", "current", "prev", "next", "temp", "tmp", "buf",
})


def _tokenize(source: str) -> List[str]:
    """Tokenise source for Jaccard overlap, excluding stop words.

    We use only alphabetic identifiers (not numbers, not single letters,
    not Python keywords) to focus on algorithm-specific names.
    """
    raw = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", source)
    return [tok for tok in raw if tok not in _STOP_WORDS and len(tok) >= 3]


def _jaccard(a_tokens: List[str], b_tokens: List[str]) -> float:
    sa, sb = set(a_tokens), set(b_tokens)
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _has_branch_and_loop(tree: ast.AST) -> bool:
    """Return True if the tree contains at least one if/elif and at least one
    loop or recursive call."""
    has_if = any(isinstance(n, (ast.If,)) for n in ast.walk(tree))
    has_loop = any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(tree))
    has_return = any(isinstance(n, ast.Return) for n in ast.walk(tree))
    # Count recursive calls crudely
    func_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    call_names = {n.func.id for n in ast.walk(tree)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    has_recursion = bool(func_names & call_names)
    return has_if and (has_loop or has_recursion) and has_return


def _third_party_imports(tree: ast.AST) -> List[str]:
    """Return list of import names that are not in stdlib."""
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top not in STDLIB_NAMES:
                    bad.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                if top not in STDLIB_NAMES:
                    bad.append(node.module)
    return bad


def _load_module(source: str, module_name: str = "_fresh_program"):
    """Compile and load source into a fresh module namespace."""
    code = compile(source, module_name, "exec")
    mod = type(sys)("_fresh_program")
    exec(code, mod.__dict__)  # noqa: S102
    return mod


def _call_one(fn, arg) -> Any:
    """Call fn with a single battery arg (tuple → unpack, otherwise pass directly)."""
    if isinstance(arg, tuple):
        return fn(*arg)
    return fn(arg)


def _call_with_battery(fn, inputs: List[Any]) -> Tuple[int, int, List[str]]:
    """Call fn with each input; return (n_ok, n_err, error_msgs)."""
    n_ok = 0
    n_err = 0
    errors = []
    for arg in inputs:
        try:
            _call_one(fn, arg)
            n_ok += 1
        except Exception as exc:  # noqa: BLE001
            n_err += 1
            errors.append(f"{type(exc).__name__}: {exc}")
    return n_ok, n_err, errors


def _determinism_check(fn, inputs: List[Any], n_repeats: int = 3) -> bool:
    """Return True if fn produces identical output on identical inputs across repeats."""
    for arg in inputs[:5]:  # spot-check first 5 inputs
        results = []
        for _ in range(n_repeats):
            try:
                r = _call_one(fn, arg)
                results.append(repr(r))
            except Exception:  # noqa: BLE001
                results.append(None)
        if len(set(results)) > 1:
            return False
    return True


def validate_program(path: Path, known_tokens: Optional[Dict[str, List[str]]] = None,
                     verbose: bool = False) -> Dict:
    """Validate a single fresh program. Returns a result dict."""
    result: Dict = {
        "path": str(path),
        "name": path.stem,
        "checks": {},
        "eligible": False,
        "exclusion_reason": None,
        "entry_name": None,
        "arity": None,
        "n_battery_inputs": None,
        "n_battery_ok": None,
        "n_battery_err": None,
        "max_jaccard": None,
        "max_jaccard_against": None,
        "warnings": [],
    }

    try:
        source = path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        result["checks"]["read"] = False
        result["exclusion_reason"] = f"cannot read: {exc}"
        return result
    result["checks"]["read"] = True

    # 1. Syntax
    try:
        tree = ast.parse(source)
        result["checks"]["syntax"] = True
    except SyntaxError as exc:
        result["checks"]["syntax"] = False
        result["exclusion_reason"] = f"SyntaxError: {exc}"
        return result

    # 2. Compile
    try:
        compile(source, str(path), "exec")
        result["checks"]["compile"] = True
    except Exception as exc:  # noqa: BLE001
        result["checks"]["compile"] = False
        result["exclusion_reason"] = f"compile error: {exc}"
        return result

    # 3. Third-party imports
    bad_imports = _third_party_imports(tree)
    if bad_imports:
        result["checks"]["stdlib_only"] = False
        result["exclusion_reason"] = f"third-party imports: {bad_imports}"
        return result
    result["checks"]["stdlib_only"] = True

    # 4. Non-trivial
    if not _has_branch_and_loop(tree):
        result["checks"]["non_trivial"] = False
        result["exclusion_reason"] = "trivial: no branch+loop/recursion pattern"
        return result
    result["checks"]["non_trivial"] = True

    # 5. Entry point selection
    try:
        entry = select_entry_structural(source)
        result["checks"]["entry_point"] = True
        result["entry_name"] = entry.name
        result["arity"] = entry.arity
        result["n_battery_inputs"] = len(entry.inputs)
        if verbose:
            print(f"  entry: {entry.name} (arity={entry.arity}, inputs={len(entry.inputs)})")
    except NoEntryPoint as exc:
        result["checks"]["entry_point"] = False
        result["exclusion_reason"] = f"NoEntryPoint: {exc}"
        return result
    except AmbiguousEntryPoint as exc:
        result["checks"]["entry_point"] = False
        result["exclusion_reason"] = f"AmbiguousEntryPoint: {exc}"
        return result
    except UnsupportedSignature as exc:
        result["checks"]["entry_point"] = False
        result["exclusion_reason"] = f"UnsupportedSignature: {exc}"
        return result
    except EntryPointError as exc:
        result["checks"]["entry_point"] = False
        result["exclusion_reason"] = f"EntryPointError: {exc}"
        return result

    # 6. Load and execute with battery
    try:
        mod = _load_module(source)
        fn = getattr(mod, entry.name)
        n_ok, n_err, errors = _call_with_battery(fn, entry.inputs)
        result["n_battery_ok"] = n_ok
        result["n_battery_err"] = n_err
        all_ok = n_err == 0
        result["checks"]["battery_execution"] = all_ok
        if not all_ok:
            result["warnings"].extend(errors[:3])
            if n_ok == 0:
                result["exclusion_reason"] = f"all {n_err} battery calls raised exceptions"
                return result
            # partial failures: warn but don't exclude if >50% succeed
            if n_ok < n_err:
                result["exclusion_reason"] = f"majority battery calls failed ({n_err}/{n_ok+n_err})"
                return result
    except Exception as exc:  # noqa: BLE001
        result["checks"]["battery_execution"] = False
        result["exclusion_reason"] = f"module load error: {exc}"
        return result

    # 7. Determinism check
    try:
        fn2 = getattr(mod, entry.name)
        is_det = _determinism_check(fn2, entry.inputs)
        result["checks"]["deterministic"] = is_det
        if not is_det:
            result["exclusion_reason"] = "non-deterministic output on repeated calls"
            return result
    except Exception as exc:  # noqa: BLE001
        result["checks"]["deterministic"] = False
        result["exclusion_reason"] = f"determinism check failed: {exc}"
        return result

    # 8. Jaccard overlap
    if known_tokens is not None:
        my_tokens = _tokenize(source)
        max_j = 0.0
        max_against = None
        for known_name, known_tok in known_tokens.items():
            j = _jaccard(my_tokens, known_tok)
            if j > max_j:
                max_j = j
                max_against = known_name
        result["max_jaccard"] = round(max_j, 4)
        result["max_jaccard_against"] = max_against
        result["checks"]["jaccard_ok"] = max_j <= 0.10
        if max_j > 0.10:
            result["exclusion_reason"] = (
                f"Jaccard overlap {max_j:.3f} > 0.10 with {max_against}"
            )
            return result
    else:
        result["checks"]["jaccard_ok"] = None  # skipped

    result["eligible"] = True
    return result


def _load_known_tokens() -> Dict[str, List[str]]:
    """Load token sets from all known programs (base + QuixBugs etc.)."""
    known: Dict[str, List[str]] = {}

    for py_file in BASE_DIR.glob("*.py"):
        if py_file.name.startswith("_"):
            continue
        try:
            src = py_file.read_text(encoding="utf-8")
            known[py_file.stem] = _tokenize(src)
        except Exception:  # noqa: BLE001
            pass

    # also scan v6 variants for overlap
    v6_base = REPO_ROOT / "benchmark" / "datasets" / "v6"
    for split_dir in (v6_base / "variants").glob("*"):
        for py_file in split_dir.glob("*.py"):
            stem = py_file.stem.split("__")[0]  # strip variant suffix
            if stem not in known:
                try:
                    src = py_file.read_text(encoding="utf-8")
                    known[stem] = _tokenize(src)
                except Exception:  # noqa: BLE001
                    pass

    return known


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate fresh SBG programs")
    parser.add_argument("path", nargs="?", help="Path to a single program.py")
    parser.add_argument("--all-fresh", action="store_true",
                        help="Validate all programs in benchmark/corpus/fresh_programs/")
    parser.add_argument("--report", action="store_true",
                        help="Write JSON report to benchmark/corpus/fresh_programs/validation_report.json")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    known_tokens = _load_known_tokens()
    if args.verbose:
        print(f"Loaded {len(known_tokens)} known programs for Jaccard check")

    if args.all_fresh or args.report:
        FRESH_DIR.mkdir(parents=True, exist_ok=True)
        paths = sorted(FRESH_DIR.glob("*.py"))
        paths = [p for p in paths if not p.name.startswith("_")]
        if not paths:
            print("No fresh programs found in", FRESH_DIR)
            return

        results = []
        eligible = []
        for p in paths:
            if args.verbose:
                print(f"\nValidating {p.name}...")
            r = validate_program(p, known_tokens, verbose=args.verbose)
            results.append(r)
            if r["eligible"]:
                eligible.append(r["name"])
            else:
                print(f"  EXCLUDED {p.name}: {r['exclusion_reason']}")

        print(f"\nSummary: {len(eligible)}/{len(paths)} programs eligible")
        if eligible:
            print("Eligible:", ", ".join(eligible))

        if args.report:
            report_path = FRESH_DIR / "validation_report.json"
            with open(report_path, "w") as f:
                json.dump({
                    "validated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
                    "n_candidates": len(paths),
                    "n_eligible": len(eligible),
                    "eligible_names": eligible,
                    "results": results,
                }, f, indent=2)
            print(f"Report written to {report_path}")

    elif args.path:
        p = Path(args.path)
        r = validate_program(p, known_tokens, verbose=args.verbose)
        if r["eligible"]:
            print(f"ELIGIBLE: {p.name}")
            print(f"  entry={r['entry_name']}, arity={r['arity']}, battery_ok={r['n_battery_ok']}/{r['n_battery_ok']+r['n_battery_err']}")
        else:
            print(f"EXCLUDED: {p.name} — {r['exclusion_reason']}")
        if args.verbose:
            print(json.dumps(r, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
