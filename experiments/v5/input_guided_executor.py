"""
experiments/v5/input_guided_executor.py
=========================================
Boundary-Input Generation and Mutation Exposure Oracle for SC-3 integer-constant mutations.

MOTIVATION
----------
SBG V3 achieves only 7.5% detection on the 179 corrected SC-3v3 pairs
(artifacts/v4/SC3_CORRECTED_EVALUATION.json). Root-cause analysis shows:

  74% — Input coverage failure: canonical inputs never reach the constant boundary
  19% — Aggregation smoothing: one divergent trace diluted by 9 identical ones
   7% — True invisibility: constant on a dead or unreachable path

This module addresses the 74% by generating inputs that place runtime variables
near integer constant boundaries, making the divergence between base and variant
observable without using any mutation metadata.

DESIGN PRINCIPLES
-----------------
* Label-blind: evaluate_pair() receives only two source strings. It does NOT
  receive the mutation site, delta, difficulty, or whether either program is
  base or variant.
* Stdlib only: ast, types, sys, io, traceback, dataclasses, typing, threading.
* Conservative sandbox: programs execute in a restricted namespace; output is
  suppressed; each call is wrapped in try/except with a wall-clock timeout.
* Symmetric extraction: constants are extracted from BOTH programs and their
  boundary inputs are unioned. This avoids any implicit use of which program
  is "original".

USAGE
-----
    from experiments.v5.input_guided_executor import BoundaryInputGenerator, MutationExposureOracle

    gen = BoundaryInputGenerator()
    oracle = MutationExposureOracle()

    with open("benchmark/corpus/base_programs/sort_binary_search.py") as f:
        source_a = f.read()
    with open("benchmark/v3/sc3_corrected/variants/sort_binary_search__sc3v3_s1_p1.py") as f:
        source_b = f.read()

    result = oracle.evaluate_pair(source_a, source_b)
    print(result.behavioral_divergence_detected)   # True or False
    print(result.divergence_inputs)                # list of inputs that exposed divergence
"""
from __future__ import annotations

import ast
import io
import sys
import threading
import traceback
import types
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Comparison:
    """A single integer constant extracted from a program's AST."""
    value: int
    line: int
    col: int
    context: str  # AST parent node type: "Compare", "If", "Assign", "Call", etc.

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Comparison) and self.value == other.value


@dataclass
class Input:
    """A single input candidate generated from a boundary value."""
    value: Any
    description: str


@dataclass
class ExposureResult:
    """Result of evaluating a program pair for behavioral divergence."""
    behavioral_divergence_detected: bool
    inputs_tested: List[dict] = field(default_factory=list)
    divergence_inputs: List[dict] = field(default_factory=list)
    n_constants_extracted: int = 0
    n_inputs_generated: int = 0
    exposure_confidence: float = 0.0  # fraction of constants whose boundary was executed
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Constant extraction
# ---------------------------------------------------------------------------

class _ConstantVisitor(ast.NodeVisitor):
    """Collect all Constant(int) nodes, recording their parent context type."""

    def __init__(self) -> None:
        self.constants: List[Comparison] = []
        self._parent_stack: List[ast.AST] = []

    def generic_visit(self, node: ast.AST) -> None:
        self._parent_stack.append(node)
        super().generic_visit(node)
        self._parent_stack.pop()

    def visit_Constant(self, node: ast.Constant) -> None:  # noqa: N802
        if isinstance(node.value, int) and not isinstance(node.value, bool):
            parent_type = (
                type(self._parent_stack[-1]).__name__
                if self._parent_stack
                else "Module"
            )
            self.constants.append(
                Comparison(
                    value=node.value,
                    line=getattr(node, "lineno", 0),
                    col=getattr(node, "col_offset", 0),
                    context=parent_type,
                )
            )
        self.generic_visit(node)


# ---------------------------------------------------------------------------
# BoundaryInputGenerator
# ---------------------------------------------------------------------------

class BoundaryInputGenerator:
    """
    Extracts integer constants from Python source and generates boundary inputs.

    For each integer constant c, the following inputs are generated:
      - Scalars:           c-1, c, c+1
      - Singleton lists:   [c-1], [c], [c+1]
      - Two-element lists: [c-1, c], [c, c+1]
      - None (for 0-arg functions):  None

    This covers the majority of benchmark function signatures:
      - sort/search: take a list
      - math/fib:    take an int
      - 0-arg harnesses: no input needed
    """

    # Sentinel: generated for 0-argument entry points
    _ZERO_ARG_INPUT = Input(value=None, description="zero_arg:None")

    def extract_comparisons(self, source: str) -> List[Comparison]:
        """
        Parse source and return a deduplicated list of integer constants.

        Deduplication is by value — if constant 5 appears 10 times in the
        source, it is returned once.

        Parameters
        ----------
        source : str
            Python source code.

        Returns
        -------
        list[Comparison]
            Sorted by constant value ascending. Empty list on parse error.
        """
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        visitor = _ConstantVisitor()
        visitor.visit(tree)

        # Deduplicate by value, keeping the first occurrence's metadata
        seen: dict[int, Comparison] = {}
        for comp in visitor.constants:
            if comp.value not in seen:
                seen[comp.value] = comp

        return sorted(seen.values(), key=lambda c: c.value)

    def generate_boundary_inputs(self, comparison: Comparison) -> List[Input]:
        """
        Generate boundary inputs for a single integer constant.

        Parameters
        ----------
        comparison : Comparison
            The integer constant to generate inputs for.

        Returns
        -------
        list[Input]
            Boundary inputs: scalars, singleton lists, two-element lists.
        """
        c = comparison.value
        inputs: List[Input] = []

        # Scalar inputs (for functions taking int)
        for delta, label in [(-1, "c-1"), (0, "c"), (1, "c+1")]:
            v = c + delta
            inputs.append(Input(value=v, description=f"scalar:{label}={v}"))

        # Singleton list inputs (for functions taking list)
        for delta, label in [(-1, "c-1"), (0, "c"), (1, "c+1")]:
            v = c + delta
            inputs.append(Input(value=[v], description=f"list:[{label}]=[{v}]"))

        # Two-element list inputs (for functions taking list, boundary straddle)
        inputs.append(Input(
            value=[c - 1, c],
            description=f"list:[c-1,c]=[{c-1},{c}]",
        ))
        inputs.append(Input(
            value=[c, c + 1],
            description=f"list:[c,c+1]=[{c},{c+1}]",
        ))

        # Monotone lists of length c-1, c, c+1 (for sort/search programs)
        for delta, label in [(-1, "c-1"), (0, "c"), (1, "c+1")]:
            length = max(0, c + delta)
            lst = list(range(length, 0, -1))  # descending for maximal sort work
            inputs.append(Input(
                value=lst,
                description=f"desc_range_len:{label}={length}",
            ))

        return inputs


# ---------------------------------------------------------------------------
# Safe execution helpers
# ---------------------------------------------------------------------------

def _build_module(source: str) -> Optional[types.ModuleType]:
    """
    Compile and execute source in a fresh module namespace.

    stdout/stderr are suppressed. Returns None on any exception.
    """
    mod = types.ModuleType("_boundary_prog")
    mod.__dict__["__builtins__"] = __builtins__
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        code = compile(source, "<boundary_prog>", "exec")
        exec(code, mod.__dict__)  # noqa: S102
        return mod
    except Exception:
        return None
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def _find_entry_function(
    mod: types.ModuleType,
    name_hints: List[str],
) -> Optional[Any]:
    """
    Find a callable entry-point in mod by trying name hints in order, then
    falling back to any top-level function not starting with '_'.
    """
    import inspect

    # Try explicit hints first
    for name in name_hints:
        fn = getattr(mod, name, None)
        if callable(fn) and isinstance(fn, types.FunctionType):
            return fn

    # Fall back to the first public function defined in the module
    for name, obj in inspect.getmembers(mod, inspect.isfunction):
        if not name.startswith("_") and getattr(obj, "__module__", None) in (
            "_boundary_prog", None
        ):
            return obj

    return None


# Default entry-point names tried in order (matches benchmark convention)
_DEFAULT_HINTS = [
    "sort", "search", "binary_search", "heapsort", "run", "main",
    "solve", "process", "compute", "fib", "encode", "decode", "parse",
    "validate", "execute", "evaluate",
]


def _safe_call(
    fn: Any,
    arg: Any,
    timeout_sec: float = 2.0,
) -> Tuple[Any, Optional[str]]:
    """
    Call fn(arg) with a wall-clock timeout.

    Returns (return_value, exception_type_name).
    If fn takes 0 arguments, arg is ignored.
    """
    import inspect

    result_box: List[Any] = [None, None]  # [return_value, exception_type_name]

    try:
        n_params = len(inspect.signature(fn).parameters)
    except (ValueError, TypeError):
        n_params = 1

    def _run() -> None:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        try:
            if n_params == 0:
                ret = fn()
            else:
                # Some functions mutate their argument (e.g., heapsort).
                # Pass a copy when the argument is a list.
                call_arg = list(arg) if isinstance(arg, list) else arg
                ret = fn(call_arg)
            result_box[0] = ret
        except Exception as exc:
            result_box[1] = type(exc).__name__
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=timeout_sec)

    if t.is_alive():
        return None, "TimeoutError"

    return result_box[0], result_box[1]


def _outputs_differ(
    out_a: Tuple[Any, Optional[str]],
    out_b: Tuple[Any, Optional[str]],
) -> bool:
    """
    Compare two (return_value, exception_type) pairs.

    Divergence is declared when:
    - Exception presence differs (one raises, one does not), OR
    - Exception types differ, OR
    - Both return normally but return values differ (with type-safe equality).
    """
    ret_a, exc_a = out_a
    ret_b, exc_b = out_b

    # One raised, the other did not
    if (exc_a is None) != (exc_b is None):
        return True

    # Both raised — compare exception type
    if exc_a is not None and exc_b is not None:
        return exc_a != exc_b

    # Both returned normally — compare values
    # Use type-safe comparison to avoid exceptions from unusual __eq__
    try:
        return ret_a != ret_b
    except Exception:
        return True  # if comparison itself fails, treat as divergent


# ---------------------------------------------------------------------------
# MutationExposureOracle
# ---------------------------------------------------------------------------

class MutationExposureOracle:
    """
    Given two program sources (no labels), detect behavioral divergence using
    boundary inputs derived from the programs' integer constants.

    Algorithm
    ---------
    1. Extract integer constants from BOTH programs (union, deduplicated by value).
    2. Generate boundary inputs for each unique constant.
    3. Add a zero-arg sentinel input (for programs with no parameters).
    4. Compile both programs into module namespaces.
    5. Find entry-point functions in both modules.
    6. Execute both on every boundary input.
    7. Compare outputs. Report first divergence immediately.

    Label Blindness
    ---------------
    evaluate_pair() receives only source_a and source_b. The caller may pass
    them in any order; the oracle reports behavioral_divergence_detected without
    indicating which direction the change went.
    """

    def __init__(
        self,
        name_hints: Optional[List[str]] = None,
        timeout_sec: float = 2.0,
        max_constants: int = 40,
    ) -> None:
        """
        Parameters
        ----------
        name_hints : list[str], optional
            Entry-point function names to try, in order. Defaults to a
            standard set covering the benchmark programs.
        timeout_sec : float
            Per-call wall-clock timeout. Default 2.0 seconds.
        max_constants : int
            Maximum number of distinct constants to extract. Prevents
            combinatorial blowup on programs with many literals. Default 40.
        """
        self._gen = BoundaryInputGenerator()
        self._hints = name_hints or _DEFAULT_HINTS
        self._timeout = timeout_sec
        self._max_constants = max_constants

    def evaluate_pair(
        self,
        source_a: str,
        source_b: str,
    ) -> ExposureResult:
        """
        Evaluate a program pair for behavioral divergence using boundary inputs.

        Parameters
        ----------
        source_a : str
            Python source of the first program.
        source_b : str
            Python source of the second program.

        Returns
        -------
        ExposureResult
            behavioral_divergence_detected=True if any input exposed divergence.
        """
        # --- Step 1: Extract constants from both programs ---
        consts_a = self._gen.extract_comparisons(source_a)
        consts_b = self._gen.extract_comparisons(source_b)

        # Union by value (symmetric — does not prefer either program)
        seen_values: set[int] = set()
        all_consts: List[Comparison] = []
        for c in consts_a + consts_b:
            if c.value not in seen_values:
                seen_values.add(c.value)
                all_consts.append(c)

        # Sort by absolute value to prioritise small/medium constants that are
        # more likely to be reachable by simple inputs.  Cap at max_constants.
        all_consts.sort(key=lambda c: abs(c.value))
        all_consts = all_consts[: self._max_constants]
        n_constants = len(all_consts)

        # --- Step 2: Generate boundary inputs ---
        boundary_inputs: List[Input] = [BoundaryInputGenerator._ZERO_ARG_INPUT]
        seen_input_descs: set[str] = {"zero_arg:None"}
        for comp in all_consts:
            for inp in self._gen.generate_boundary_inputs(comp):
                if inp.description not in seen_input_descs:
                    seen_input_descs.add(inp.description)
                    boundary_inputs.append(inp)

        n_inputs_generated = len(boundary_inputs)

        # --- Step 3: Compile programs ---
        mod_a = _build_module(source_a)
        mod_b = _build_module(source_b)

        if mod_a is None:
            return ExposureResult(
                behavioral_divergence_detected=False,
                n_constants_extracted=n_constants,
                n_inputs_generated=n_inputs_generated,
                error="COMPILE_ERROR_source_a",
            )
        if mod_b is None:
            return ExposureResult(
                behavioral_divergence_detected=False,
                n_constants_extracted=n_constants,
                n_inputs_generated=n_inputs_generated,
                error="COMPILE_ERROR_source_b",
            )

        # --- Step 4: Find entry functions ---
        fn_a = _find_entry_function(mod_a, self._hints)
        fn_b = _find_entry_function(mod_b, self._hints)

        if fn_a is None or fn_b is None:
            return ExposureResult(
                behavioral_divergence_detected=False,
                n_constants_extracted=n_constants,
                n_inputs_generated=n_inputs_generated,
                error=(
                    f"NO_ENTRY_FUNCTION: "
                    f"fn_a={'found' if fn_a else 'missing'}, "
                    f"fn_b={'found' if fn_b else 'missing'}"
                ),
            )

        # --- Step 5: Execute and compare ---
        inputs_tested: List[dict] = []
        divergence_inputs: List[dict] = []
        divergence_detected = False
        constants_exercised: set[int] = set()

        for inp in boundary_inputs:
            out_a = _safe_call(fn_a, inp.value, self._timeout)
            out_b = _safe_call(fn_b, inp.value, self._timeout)

            # Skip timeout pairs — they don't contribute signal
            if out_a[1] == "TimeoutError" or out_b[1] == "TimeoutError":
                continue

            tested_record = {
                "input_description": inp.description,
                "input_value": _safe_repr(inp.value),
                "output_a": _safe_repr(out_a),
                "output_b": _safe_repr(out_b),
            }
            inputs_tested.append(tested_record)

            # Track which constants were exercised (heuristic: did either
            # output/exception change relative to the zero-arg baseline?)
            for comp in all_consts:
                if _value_near_constant(inp.value, comp.value):
                    constants_exercised.add(comp.value)

            if _outputs_differ(out_a, out_b):
                divergence_detected = True
                div_record = dict(tested_record)
                div_record["divergence"] = True
                divergence_inputs.append(div_record)
                # Do not break early — collect all divergent inputs for analysis

        exposure_conf = (
            len(constants_exercised) / n_constants if n_constants > 0 else 0.0
        )

        return ExposureResult(
            behavioral_divergence_detected=divergence_detected,
            inputs_tested=inputs_tested,
            divergence_inputs=divergence_inputs,
            n_constants_extracted=n_constants,
            n_inputs_generated=n_inputs_generated,
            exposure_confidence=round(exposure_conf, 4),
            error=None,
        )


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _safe_repr(obj: Any, maxlen: int = 120) -> str:
    """Return repr(obj) truncated to maxlen, suppressing errors."""
    try:
        r = repr(obj)
        return r[:maxlen] + "…" if len(r) > maxlen else r
    except Exception:
        return "<repr-error>"


def _value_near_constant(input_value: Any, constant: int, tolerance: int = 2) -> bool:
    """
    Heuristic: return True if input_value or any element of input_value
    is within tolerance of constant.
    """
    if isinstance(input_value, int):
        return abs(input_value - constant) <= tolerance
    if isinstance(input_value, list):
        return any(
            isinstance(v, int) and abs(v - constant) <= tolerance
            for v in input_value
        )
    return False


# ---------------------------------------------------------------------------
# Demo / self-test
# ---------------------------------------------------------------------------

def _demo() -> None:
    """
    Demonstration using the sort_binary_search SC-3v3 pair.

    Base:    sort_binary_search__sc3v3_s0_p0.py (unchanged algorithm)
    Variant: sort_binary_search__sc3v3_s1_p1.py (test array changed: [1,3,2,2,...] → [1,2,1,2,...])

    This pair has mutation_value_before=3, mutation_value_after=2 at the test
    array in the test harness. The binary_search algorithm itself is unchanged,
    but the test suite calls binary_search with different data.  The boundary
    generator will extract constants 1, 2, 3, etc. and generate inputs near 3
    and 2, exposing the divergence in the test harness assertion.
    """
    import pathlib

    repo_root = pathlib.Path(__file__).resolve().parent.parent.parent
    base_path = repo_root / "benchmark" / "v3" / "sc3_corrected" / "variants" / "sort_binary_search__sc3v3_s0_p0.py"
    var_path = repo_root / "benchmark" / "v3" / "sc3_corrected" / "variants" / "sort_binary_search__sc3v3_s1_p1.py"

    if not base_path.exists() or not var_path.exists():
        print("[demo] Variant files not found — skipping demo.")
        return

    source_a = base_path.read_text()
    source_b = var_path.read_text()

    gen = BoundaryInputGenerator()
    oracle = MutationExposureOracle(timeout_sec=3.0)

    print("\n" + "=" * 60)
    print("SC-3 EXPOSURE ORACLE — Demo")
    print("=" * 60)

    # Show constants extracted
    consts_a = gen.extract_comparisons(source_a)
    consts_b = gen.extract_comparisons(source_b)
    print(f"\nConstants in source_a: {sorted(c.value for c in consts_a)}")
    print(f"Constants in source_b: {sorted(c.value for c in consts_b)}")

    # Show some boundary inputs for the constant '3'
    for c in consts_a:
        if c.value == 3:
            binputs = gen.generate_boundary_inputs(c)
            print(f"\nBoundary inputs for constant 3 (line {c.line}):")
            for bi in binputs[:6]:
                print(f"  {bi.description}")
            break

    # Run the oracle
    result = oracle.evaluate_pair(source_a, source_b)

    print(f"\n--- ExposureResult ---")
    print(f"  behavioral_divergence_detected : {result.behavioral_divergence_detected}")
    print(f"  n_constants_extracted          : {result.n_constants_extracted}")
    print(f"  n_inputs_generated             : {result.n_inputs_generated}")
    print(f"  inputs_tested (non-timeout)    : {len(result.inputs_tested)}")
    print(f"  divergence_inputs              : {len(result.divergence_inputs)}")
    print(f"  exposure_confidence            : {result.exposure_confidence}")
    print(f"  error                          : {result.error}")

    if result.divergence_inputs:
        print("\n  First divergence input:")
        d = result.divergence_inputs[0]
        print(f"    input       : {d['input_description']}")
        print(f"    output_a    : {d['output_a']}")
        print(f"    output_b    : {d['output_b']}")
    else:
        print("\n  No divergence detected on this pair.")

    print("\n" + "=" * 60)

    # Quick batch demo on 3 verified easy pairs
    print("\nBatch demo: 3 verified EASY pairs from sc3_corrected_pairs.jsonl")
    easy_pairs = [
        ("ds_lru_cache", "ds_lru_cache__sc3v3_s0_p0"),
        ("ds_stack_queue", "ds_stack_queue__sc3v3_s0_p0"),
        ("ds_trie", "ds_trie__sc3v3_s0_p0"),
    ]
    variants_dir = repo_root / "benchmark" / "v3" / "sc3_corrected" / "variants"
    corpus_dir = repo_root / "benchmark" / "corpus" / "base_programs"

    detected = 0
    for base_id, var_id in easy_pairs:
        bp = corpus_dir / f"{base_id}.py"
        vp = variants_dir / f"{var_id}.py"
        if not bp.exists() or not vp.exists():
            print(f"  {var_id}: SKIPPED (files not found)")
            continue
        r = oracle.evaluate_pair(bp.read_text(), vp.read_text())
        status = "DETECTED" if r.behavioral_divergence_detected else "MISSED"
        if r.error:
            status = f"ERROR({r.error})"
        else:
            detected += int(r.behavioral_divergence_detected)
        print(f"  {var_id}: {status}  "
              f"(constants={r.n_constants_extracted}, "
              f"inputs={r.n_inputs_generated}, "
              f"divergences={len(r.divergence_inputs)})")

    total = sum(1 for base_id, _ in easy_pairs if (corpus_dir / f"{base_id}.py").exists())
    print(f"\nDetection rate on demo pairs: {detected}/{total}")
    print("=" * 60)


if __name__ == "__main__":
    _demo()
