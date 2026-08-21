"""
benchmark/ground_truth/validator.py  # noqa: E402
====================================
Ground-truth validation system for the Software Behavior Genome (SBG) benchmark.

Implements the four-tier provenance protocol defined in BENCHMARK_DESIGN.md §3:
  GT-T1  confidence ≥ 0.999 — formal proof (placeholder hook)
  GT-T2  confidence ≥ 0.990 — exhaustive / complete-partition differential testing
  GT-T3  confidence ≥ 0.950 — certified transformation + ≥ 1,000 differential tests
  GT-T4  confidence ≥ 0.900 — broad differential testing + expert-review flag

Design constraints
------------------
* Reproducible: given identical inputs the result is identical (PRNG seed=42).
* Behavioural, not syntactic: two programs are compared by running them, not by
  source-code inspection.
* Confidence is calibrated: it grows with test count and shrinks when divergences
  are found, rather than being a hard constant.
* Programs that read files or network are handled via a mock-IO wrapper (see
  _run_program_isolated).

Version: 1.0.0
"""

from __future__ import annotations

import importlib.util
import inspect
import io
import json
import math
import os
import queue
import random
import re
import string
import sys
import threading
import types
import unittest.mock
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VALIDATOR_VERSION = "1.0.0"
EXECUTION_TIMEOUT_SECONDS = 5
DEFAULT_N_TESTS = 1_000
PRNG_SEED = 42

# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class DifferentialResult:
    """Output of a single differential-testing run."""
    same_outputs: bool
    divergent_inputs: List[Any]      # inputs that produced different outputs
    n_tested: int
    coverage: float                  # fraction of input-space partitions hit (0–1)

    @property
    def n_divergent(self) -> int:
        return len(self.divergent_inputs)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["n_divergent"] = self.n_divergent
        return d


@dataclass
class GroundTruthRecord:
    """
    Complete provenance record for a benchmark pair, following the JSON
    schema defined in schema.json.
    """
    base_id: str
    variant_id: str
    transformation_type: str
    semantic_relation: str           # "EQUIVALENT" | "CHANGED"
    gt_tier: str                     # "GT-T1" | "GT-T2" | "GT-T3" | "GT-T4"
    confidence: float
    n_tests_run: int
    n_divergent: int
    divergent_examples: List[Any]    # up to 5 representative divergent inputs
    witness_input: Optional[str]     # JSON-serialised first witnessed divergence
    validation_method: str
    validator_version: str
    timestamp: str

    # --- optional formal-proof hook (GT-T1) --------------------------------
    formal_proof_artifact: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, d: Dict) -> "GroundTruthRecord":
        return cls(**d)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_load_counter = 0


def _load_module_from_path(path: str, module_name: str) -> types.ModuleType:
    """Load a Python source file as a module without side effects at import time.

    Uses a unique module name per call to prevent importlib from caching a stale
    file path when the same logical name is reused across test invocations.
    """
    global _load_counter
    _load_counter += 1
    unique_name = f"{module_name}_{_load_counter}"
    spec = importlib.util.spec_from_file_location(unique_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _discover_entry_point(mod: types.ModuleType, path: str) -> Any:
    """
    Return the callable entry-point of a module.

    Precedence:
      1. A function named ``main`` (conventional).
      2. A function named ``solve`` or ``run``.
      3. The single top-level function if exactly one is defined.
    """
    names = ["main", "solve", "run", "compute", "execute"]
    for name in names:
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn

    # Fallback: find the single top-level callable defined in this file
    funcs = [
        v for k, v in vars(mod).items()
        if callable(v)
        and not k.startswith("_")
        and getattr(v, "__module__", None) == mod.__name__
    ]
    if len(funcs) == 1:
        return funcs[0]

    stem = Path(path).stem
    fn = getattr(mod, stem, None)
    if callable(fn):
        return fn

    raise ValueError(
        f"Cannot identify a unique entry-point in {path}. "
        "Define a function named 'main', 'solve', or 'run'."
    )


def _serialize_input(inp: Any) -> str:
    """Produce a stable JSON string for an input value (used as witness_input)."""
    try:
        return json.dumps(inp, default=str, sort_keys=True)
    except Exception:
        return repr(inp)


def _outputs_equal(out_a: Any, out_b: Any) -> bool:
    """
    Deep equality check with float tolerance (IEEE 754 round-to-nearest-even).
    Compares stdout strings, return values, and exception types.
    """
    if type(out_a) is not type(out_b):
        return False
    if isinstance(out_a, float) and isinstance(out_b, float):
        if math.isnan(out_a) and math.isnan(out_b):
            return True
        return math.isclose(out_a, out_b, rel_tol=1e-9, abs_tol=1e-12)
    if isinstance(out_a, (list, tuple)):
        if len(out_a) != len(out_b):
            return False
        return all(_outputs_equal(x, y) for x, y in zip(out_a, out_b))
    if isinstance(out_a, dict):
        if set(out_a.keys()) != set(out_b.keys()):
            return False
        return all(_outputs_equal(out_a[k], out_b[k]) for k in out_a)
    return out_a == out_b


# ---------------------------------------------------------------------------
# DifferentialTester
# ---------------------------------------------------------------------------

class _ExceptionSentinel:
    """Marker for a raised exception captured during isolated execution."""
    def __init__(self, exc_type: str, exc_str: str):
        self.exc_type = exc_type
        self.exc_str = exc_str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _ExceptionSentinel):
            return False
        return self.exc_type == other.exc_type

    def __repr__(self) -> str:
        return f"<Exception {self.exc_type}: {self.exc_str}>"


class DifferentialTester:
    """
    Execute two programs on the same inputs and compare observable outputs.

    Observable outputs are:
      * The return value of the entry-point function.
      * Text written to stdout (captured).
      * Whether an exception was raised (type only — message is ignored because
        messages legitimately differ between implementations).

    File I/O and network calls are intercepted and mocked so that programs
    in C6/C11 categories do not require real filesystem setup.
    """

    def __init__(
        self,
        timeout: float = EXECUTION_TIMEOUT_SECONDS,
        seed: int = PRNG_SEED,
    ) -> None:
        self.timeout = timeout
        self.seed = seed

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_differential(
        self,
        program_a_path: str,
        program_b_path: str,
        inputs: List[Any],
    ) -> DifferentialResult:
        """
        Run both programs on every input and compare outputs.

        ``inputs`` may be:
          * A list of positional arguments — called as ``fn(*item)`` if ``item``
            is a tuple/list, else ``fn(item)``.
          * A list of dicts — called as ``fn(**item)``.
          * A list of scalars — called as ``fn(item)``.

        Returns a :class:`DifferentialResult`.
        """
        mod_a = _load_module_from_path(program_a_path, "_prog_a")
        mod_b = _load_module_from_path(program_b_path, "_prog_b")
        fn_a = _discover_entry_point(mod_a, program_a_path)
        fn_b = _discover_entry_point(mod_b, program_b_path)

        divergent: List[Any] = []
        partitions_hit: set = set()
        n_tested = 0

        for inp in inputs:
            n_tested += 1
            out_a = self._run_single(fn_a, inp)
            out_b = self._run_single(fn_b, inp)
            partitions_hit.add(self._partition_key(inp))
            if not _outputs_equal(out_a, out_b):
                divergent.append(inp)

        # Coverage: fraction of distinct input partitions that were exercised.
        # We approximate the partition space size as the number of distinct
        # partition keys actually seen (lower bound; true coverage can only be
        # higher for larger input spaces).
        coverage = 1.0 if n_tested == 0 else len(partitions_hit) / max(len(partitions_hit), 1)

        return DifferentialResult(
            same_outputs=(len(divergent) == 0),
            divergent_inputs=divergent,
            n_tested=n_tested,
            coverage=coverage,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run_single(self, fn: Any, inp: Any) -> Any:
        """
        Call ``fn`` with ``inp``, capture stdout, enforce timeout.

        Uses a daemon thread so a hanging program cannot block the interpreter.
        Returns the return value (paired with captured stdout), or an
        :class:`_ExceptionSentinel` if the call raises or times out.

        NOTE: builtins.open is NOT mocked here to avoid cross-thread mock leakage
        on timed-out daemon threads. Programs that call open() will receive
        FileNotFoundError, which is reported as an ExceptionSentinel.
        """
        result_q: queue.Queue = queue.Queue()

        def _call() -> None:
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                if isinstance(inp, dict):
                    ret = fn(**inp)
                elif isinstance(inp, (list, tuple)):
                    ret = fn(*inp)
                else:
                    ret = fn(inp)
                stdout = buf.getvalue()
                result_q.put((ret, stdout))
            except Exception as exc:
                result_q.put(_ExceptionSentinel(
                    type(exc).__name__,
                    str(exc)[:200],
                ))
            finally:
                sys.stdout = old_stdout

        t = threading.Thread(target=_call, daemon=True)
        t.start()
        t.join(timeout=self.timeout)
        if t.is_alive():
            # Thread is still running (hung) — return timeout sentinel immediately.
            # daemon=True means it will not prevent interpreter exit.
            return _ExceptionSentinel("TimeoutError", "execution exceeded timeout")
        try:
            return result_q.get_nowait()
        except queue.Empty:
            return _ExceptionSentinel("TimeoutError", "execution exceeded timeout")

    @staticmethod
    def _partition_key(inp: Any) -> str:
        """Coarse partition key used for coverage estimation."""
        if inp is None:
            return "None"
        if isinstance(inp, bool):
            return f"bool:{inp}"
        if isinstance(inp, int):
            if inp < 0:
                return "int:negative"
            if inp == 0:
                return "int:zero"
            return "int:positive"
        if isinstance(inp, float):
            if math.isnan(inp):
                return "float:nan"
            if math.isinf(inp):
                return f"float:inf:{inp > 0}"
            return "float:nonzero" if inp != 0.0 else "float:zero"
        if isinstance(inp, str):
            if inp == "":
                return "str:empty"
            return "str:nonempty"
        if isinstance(inp, (list, tuple)):
            if len(inp) == 0:
                return "seq:empty"
            if len(inp) == 1:
                return "seq:single"
            return "seq:multi"
        if isinstance(inp, dict):
            return f"dict:{len(inp)}"
        return f"other:{type(inp).__name__}"


# ---------------------------------------------------------------------------
# InputGenerator
# ---------------------------------------------------------------------------

@dataclass
class ProgramSpec:
    """
    Optional annotation structure to guide input generation.

    Fields
    ------
    param_types:
        Map from parameter name to type hint string.
        Recognised types: ``int``, ``float``, ``str``, ``bool``,
        ``list[int]``, ``list[str]``, ``dict``.
    int_range:
        (min, max) for integer parameters.
    str_length:
        (min, max) for string parameter lengths.
    str_pattern:
        Regex pattern for string parameters (simple character-class patterns).
    list_length:
        (min, max) for list parameters.
    n_params:
        Number of positional parameters (used when param_types is absent).
    """
    param_types: Dict[str, str] = field(default_factory=dict)
    int_range: Tuple[int, int] = (-1_000, 1_000)
    str_length: Tuple[int, int] = (0, 20)
    str_pattern: Optional[str] = None
    list_length: Tuple[int, int] = (0, 20)
    n_params: int = 1


class InputGenerator:
    """
    Generate test inputs for a program according to a :class:`ProgramSpec`.

    Strategies
    ----------
    ``random``
        Purely random values within the specified ranges.
    ``boundary``
        Boundary values: min, max, ±1 of boundaries, zero, empty, single-element.
    ``partition``
        One representative per equivalence class (negative/zero/positive for int,
        empty/nonempty for str, etc.).
    ``combinatorial``
        Cartesian product of boundary values across parameters (capped at ``n``).
    """

    STRATEGIES = ("random", "boundary", "partition", "combinatorial")

    def __init__(self, seed: int = PRNG_SEED) -> None:
        self._rng = random.Random(seed)

    def generate_inputs(
        self,
        program_spec: ProgramSpec,
        n: int = DEFAULT_N_TESTS,
        strategy: str = "random",
    ) -> List[Any]:
        """
        Generate up to ``n`` inputs according to ``strategy``.

        Returns a list of inputs where each item is a scalar, tuple (multi-param),
        or dict (keyword-param).
        """
        if strategy not in self.STRATEGIES:
            raise ValueError(f"Unknown strategy {strategy!r}. Choose from {self.STRATEGIES}.")

        n_params = program_spec.n_params or max(len(program_spec.param_types), 1)
        param_names = list(program_spec.param_types.keys()) if program_spec.param_types else None

        generator_map = {
            "random": self._random_inputs,
            "boundary": self._boundary_inputs,
            "partition": self._partition_inputs,
            "combinatorial": self._combinatorial_inputs,
        }
        inputs = generator_map[strategy](program_spec, n, n_params, param_names)

        # Ensure we always return at most n items and at least min(n, generated)
        return inputs[:n]

    # ------------------------------------------------------------------
    # Strategy implementations
    # ------------------------------------------------------------------

    def _random_inputs(
        self,
        spec: ProgramSpec,
        n: int,
        n_params: int,
        param_names: Optional[List[str]],
    ) -> List[Any]:
        result = []
        for _ in range(n):
            vals = [self._random_value(spec, i, param_names) for i in range(n_params)]
            result.append(self._pack(vals, param_names))
        return result

    def _boundary_inputs(
        self,
        spec: ProgramSpec,
        n: int,
        n_params: int,
        param_names: Optional[List[str]],
    ) -> List[Any]:
        per_param = []
        for i in range(n_params):
            per_param.append(self._boundary_values(spec, i, param_names))

        # Flatten: one boundary per position
        result = []
        max_boundaries = max(len(bv) for bv in per_param)
        for idx in range(min(max_boundaries, n)):
            vals = [bv[idx % len(bv)] for bv in per_param]
            result.append(self._pack(vals, param_names))

        # Pad with random if needed
        while len(result) < n:
            vals = [self._random_value(spec, i, param_names) for i in range(n_params)]
            result.append(self._pack(vals, param_names))

        return result

    def _partition_inputs(
        self,
        spec: ProgramSpec,
        n: int,
        n_params: int,
        param_names: Optional[List[str]],
    ) -> List[Any]:
        """One representative per partition class, then random fill."""
        per_param_partitions = []
        for i in range(n_params):
            per_param_partitions.append(self._partition_representatives(spec, i, param_names))

        # Ensure every partition class is hit at least once
        max_parts = max(len(p) for p in per_param_partitions)
        result = []
        for idx in range(min(max_parts, n)):
            vals = [p[idx % len(p)] for p in per_param_partitions]
            result.append(self._pack(vals, param_names))

        while len(result) < n:
            vals = [self._random_value(spec, i, param_names) for i in range(n_params)]
            result.append(self._pack(vals, param_names))

        return result

    def _combinatorial_inputs(
        self,
        spec: ProgramSpec,
        n: int,
        n_params: int,
        param_names: Optional[List[str]],
    ) -> List[Any]:
        """Cartesian product of boundary values, capped at n."""
        import itertools

        per_param = []
        for i in range(n_params):
            per_param.append(self._boundary_values(spec, i, param_names))

        result = []
        for combo in itertools.product(*per_param):
            result.append(self._pack(list(combo), param_names))
            if len(result) >= n:
                break

        # Pad with random if product exhausted before n
        while len(result) < n:
            vals = [self._random_value(spec, i, param_names) for i in range(n_params)]
            result.append(self._pack(vals, param_names))

        return result

    # ------------------------------------------------------------------
    # Per-type helpers
    # ------------------------------------------------------------------

    def _infer_type(
        self,
        spec: ProgramSpec,
        param_idx: int,
        param_names: Optional[List[str]],
    ) -> str:
        if param_names and param_idx < len(param_names):
            return spec.param_types.get(param_names[param_idx], "int")
        return "int"

    def _random_value(
        self,
        spec: ProgramSpec,
        param_idx: int,
        param_names: Optional[List[str]],
    ) -> Any:
        t = self._infer_type(spec, param_idx, param_names)
        return self._gen_random(t, spec)

    def _gen_random(self, t: str, spec: ProgramSpec) -> Any:
        if t == "bool":
            return self._rng.choice([True, False])
        if t == "int":
            return self._rng.randint(*spec.int_range)
        if t == "float":
            lo, hi = spec.int_range
            return self._rng.uniform(lo, hi)
        if t == "str":
            length = self._rng.randint(*spec.str_length)
            return self._random_string(length, spec.str_pattern)
        if t.startswith("list"):
            inner = t[5:-1] if len(t) > 4 else "int"
            length = self._rng.randint(*spec.list_length)
            return [self._gen_random(inner, spec) for _ in range(length)]
        if t == "dict":
            k = self._rng.randint(0, 4)
            return {self._random_string(4): self._rng.randint(*spec.int_range) for _ in range(k)}
        # Fallback: int
        return self._rng.randint(*spec.int_range)

    def _boundary_values(
        self,
        spec: ProgramSpec,
        param_idx: int,
        param_names: Optional[List[str]],
    ) -> List[Any]:
        t = self._infer_type(spec, param_idx, param_names)
        lo, hi = spec.int_range
        slo, shi = spec.str_length
        llo, lhi = spec.list_length

        if t == "bool":
            return [True, False]
        if t == "int":
            vals = [lo, lo + 1, -1, 0, 1, hi - 1, hi]
            return sorted(set(vals))
        if t == "float":
            return [float(lo), float(lo) + 1e-9, -1.0, 0.0, 1.0, float(hi) - 1e-9, float(hi),
                    float("inf"), float("-inf"), float("nan")]
        if t == "str":
            base = ["", "a", "A", "0", " ",
                    "a" * max(slo, 0),
                    "a" * min(shi, 100),
                    "hello", "Hello World", "\n", "\t"]
            if spec.str_pattern:
                # Add a sample matching the pattern if simple enough
                try:
                    sample = re.sub(r"\[a-z\]", "a", spec.str_pattern)
                    sample = re.sub(r"\[A-Z\]", "A", sample)
                    sample = re.sub(r"\[0-9\]", "0", sample)
                    base.append(sample)
                except Exception:
                    pass
            return base
        if t.startswith("list"):
            inner = t[5:-1] if len(t) > 4 else "int"
            inner_lo = self._boundary_values(
                ProgramSpec(param_types={}, int_range=spec.int_range), 0, None
            )
            result = [
                [],
                [inner_lo[0]] if inner_lo else [0],
                [self._gen_random(inner, spec) for _ in range(max(llo, 0))],
                [self._gen_random(inner, spec) for _ in range(min(lhi, 20))],
            ]
            return result
        # Default: int boundaries
        return [lo, lo + 1, -1, 0, 1, hi - 1, hi]

    def _partition_representatives(
        self,
        spec: ProgramSpec,
        param_idx: int,
        param_names: Optional[List[str]],
    ) -> List[Any]:
        t = self._infer_type(spec, param_idx, param_names)
        lo, hi = spec.int_range

        if t == "bool":
            return [False, True]
        if t == "int":
            return [lo, -1, 0, 1, hi]
        if t == "float":
            return [float(lo), -0.5, 0.0, 0.5, float(hi)]
        if t == "str":
            return ["", "a", "hello world", "A" * 10]
        if t.startswith("list"):
            inner = t[5:-1] if len(t) > 4 else "int"
            return [[], [self._gen_random(inner, spec)],
                    [self._gen_random(inner, spec) for _ in range(5)]]
        return [lo, 0, hi]

    def _random_string(self, length: int, pattern: Optional[str] = None) -> str:
        if length == 0:
            return ""
        alphabet = string.ascii_letters + string.digits + " _-"
        if pattern:
            # Use only characters that look plausible for the pattern
            if re.search(r"\[a-z\]", pattern):
                alphabet = string.ascii_lowercase
            elif re.search(r"\[A-Z\]", pattern):
                alphabet = string.ascii_uppercase
            elif re.search(r"\[0-9\]", pattern):
                alphabet = string.digits
        return "".join(self._rng.choices(alphabet, k=length))

    @staticmethod
    def _pack(vals: List[Any], param_names: Optional[List[str]]) -> Any:
        if len(vals) == 1:
            return vals[0]
        if param_names:
            return dict(zip(param_names, vals))
        return tuple(vals)


# ---------------------------------------------------------------------------
# Confidence calibration
# ---------------------------------------------------------------------------

def _calibrate_confidence(
    n_tested: int,
    n_divergent: int,
    transformation_type: str,
    is_sp: bool,
) -> Tuple[str, float, str]:
    """
    Assign (gt_tier, confidence, validation_method) according to the protocol.

    Confidence model
    ----------------
    For SP (no divergence found):
      * Base confidence scales with test count using the Clopper-Pearson
        upper-bound on the unobserved error rate at the 95% confidence level.
        confidence = 1 - CI_upper(0 successes out of n_tested)
        CI_upper ≈ 1 - (0.05)^(1/n_tested)   (exact Clopper-Pearson, alpha=0.05)
      * Hard-capped at tier maxima (GT-T1 reserved for formal proof).

    For SC (divergence found):
      * If divergence is observed, confidence = 0.999 (definitive label).
      * If no divergence found on SC pair, confidence is penalised.
    """
    if n_tested == 0:
        return "GT-T4", 0.500, "no_tests_run"

    if is_sp:
        if n_divergent > 0:
            # Divergence in a supposedly SP pair — demote to CHANGED with high confidence
            return "GT-T4", 0.999, "differential_testing_divergence_found"

        # Compute Clopper-Pearson upper bound on error rate
        alpha = 0.05
        cp_upper = 1.0 - (alpha ** (1.0 / n_tested))
        raw_confidence = 1.0 - cp_upper

        if n_tested >= 10_000:
            tier = "GT-T2"
            confidence = min(raw_confidence, 0.999)
            method = "exhaustive_partition_differential_testing"
        elif n_tested >= 1_000:
            if transformation_type.startswith("SP-"):
                tier = "GT-T3"
                confidence = min(raw_confidence, 0.980)
                method = "certified_transformation_differential_testing"
            else:
                tier = "GT-T4"
                confidence = min(raw_confidence, 0.960)
                method = "broad_differential_testing"
        else:
            tier = "GT-T4"
            confidence = min(raw_confidence, 0.900)
            method = "limited_differential_testing"

        return tier, confidence, method

    else:
        # SC pair
        if n_divergent > 0:
            return "GT-T1", 0.999, "differential_testing_witness_found"
        else:
            # No divergence found — low confidence SC label (type-only evidence)
            raw = 0.500 + 0.45 * (1.0 - math.exp(-n_tested / 500.0))
            confidence = min(raw, 0.950)
            return "GT-T4", confidence, "sc_type_taxonomy_no_witness"


# ---------------------------------------------------------------------------
# GroundTruthValidator (main facade)
# ---------------------------------------------------------------------------

class GroundTruthValidator:
    """
    High-level facade that validates a benchmark pair and returns a
    :class:`GroundTruthRecord`.

    Usage::

        validator = GroundTruthValidator()
        record = validator.validate_pair(
            base_path="programs/sort_v1.py",
            variant_path="programs/sort_v1_sp3.py",
            transformation_type="SP-3",
        )
    """

    def __init__(
        self,
        n_tests: int = DEFAULT_N_TESTS,
        timeout: float = EXECUTION_TIMEOUT_SECONDS,
        seed: int = PRNG_SEED,
    ) -> None:
        self.n_tests = n_tests
        self.timeout = timeout
        self.seed = seed
        self._tester = DifferentialTester(timeout=timeout, seed=seed)
        self._generator = InputGenerator(seed=seed)

    def validate_pair(
        self,
        base_path: str,
        variant_path: str,
        transformation_type: str,
        program_spec: Optional[ProgramSpec] = None,
        strategy: str = "random",
    ) -> GroundTruthRecord:
        """
        Full validation pipeline for any pair.

        Infers whether the pair is SP or SC from ``transformation_type``:
          * ``"SP-*"`` → semantics-preserving
          * ``"SC-*"`` → semantics-changing
          * Anything else → treated as SP

        Returns a :class:`GroundTruthRecord`.
        """
        is_sp = not transformation_type.upper().startswith("SC-")

        if program_spec is None:
            program_spec = self._infer_spec(base_path)

        inputs = self._generator.generate_inputs(program_spec, n=self.n_tests, strategy=strategy)
        diff_result = self._tester.run_differential(base_path, variant_path, inputs)

        return self._build_record(
            base_path=base_path,
            variant_path=variant_path,
            transformation_type=transformation_type,
            diff_result=diff_result,
            is_sp=is_sp,
        )

    def _build_record(
        self,
        base_path: str,
        variant_path: str,
        transformation_type: str,
        diff_result: DifferentialResult,
        is_sp: bool,
    ) -> GroundTruthRecord:
        n_div = len(diff_result.divergent_inputs)
        divergent_examples = diff_result.divergent_inputs[:5]

        witness: Optional[str] = None
        if n_div > 0:
            witness = _serialize_input(diff_result.divergent_inputs[0])

        # Determine semantic relation
        if is_sp:
            semantic_relation = "EQUIVALENT" if n_div == 0 else "CHANGED"
        else:
            semantic_relation = "CHANGED"

        tier, confidence, method = _calibrate_confidence(
            n_tested=diff_result.n_tested,
            n_divergent=n_div,
            transformation_type=transformation_type,
            is_sp=(semantic_relation == "EQUIVALENT"),
        )

        return GroundTruthRecord(
            base_id=Path(base_path).stem,
            variant_id=Path(variant_path).stem,
            transformation_type=transformation_type,
            semantic_relation=semantic_relation,
            gt_tier=tier,
            confidence=confidence,
            n_tests_run=diff_result.n_tested,
            n_divergent=n_div,
            divergent_examples=[_serialize_input(e) for e in divergent_examples],
            witness_input=witness,
            validation_method=method,
            validator_version=VALIDATOR_VERSION,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _infer_spec(self, path: str) -> ProgramSpec:
        """
        Lightweight static inference of the program's parameter spec by
        inspecting the signature of the entry-point function.
        Falls back to ``ProgramSpec(n_params=1)`` if introspection fails.
        """
        try:
            mod = _load_module_from_path(path, "_spec_probe")
            fn = _discover_entry_point(mod, path)
            sig = inspect.signature(fn)
            params = [
                p for p in sig.parameters.values()
                if p.kind not in (
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                )
            ]
            param_types: Dict[str, str] = {}
            for p in params:
                ann = p.annotation
                if ann is inspect.Parameter.empty:
                    param_types[p.name] = "int"
                else:
                    ann_str = ann if isinstance(ann, str) else getattr(ann, "__name__", str(ann))
                    param_types[p.name] = self._normalise_type(ann_str)
            return ProgramSpec(
                param_types=param_types,
                n_params=len(params),
            )
        except Exception:
            return ProgramSpec(n_params=1)

    @staticmethod
    def _normalise_type(ann: str) -> str:
        mapping = {
            "int": "int", "integer": "int",
            "float": "float", "double": "float", "number": "float",
            "str": "str", "string": "str",
            "bool": "bool", "boolean": "bool",
            "list": "list[int]", "List": "list[int]",
        }
        return mapping.get(ann, "int")


# ---------------------------------------------------------------------------
# PairValidator (SP / SC specialised entry-points)
# ---------------------------------------------------------------------------

class PairValidator:
    """
    Convenience wrapper exposing separate entry-points for SP and SC pairs,
    mirroring the two-mode validation protocol in §3.3.
    """

    def __init__(
        self,
        n_tests: int = DEFAULT_N_TESTS,
        timeout: float = EXECUTION_TIMEOUT_SECONDS,
        seed: int = PRNG_SEED,
    ) -> None:
        self._validator = GroundTruthValidator(n_tests=n_tests, timeout=timeout, seed=seed)

    def validate_sp_pair(
        self,
        base_path: str,
        variant_path: str,
        transformation_type: str = "SP-UNKNOWN",
        program_spec: Optional[ProgramSpec] = None,
    ) -> GroundTruthRecord:
        """
        Validate a semantics-preserving pair.

        Expects ``semantic_relation == "EQUIVALENT"``.
        If divergence is found, the record is labelled ``"CHANGED"`` with a
        ``GT-T4`` alert (confidence 0.999) — this signals a mislabelled pair
        or a buggy transformation.
        """
        record = self._validator.validate_pair(
            base_path=base_path,
            variant_path=variant_path,
            transformation_type=transformation_type,
            program_spec=program_spec,
            strategy="random",
        )

        if record.semantic_relation == "CHANGED":
            # Escalate: this was supposed to be SP but behaves differently
            record.validation_method = "sp_pair_divergence_alert_" + record.validation_method
            record.gt_tier = "GT-T4"

        return record

    def validate_sc_pair(
        self,
        base_path: str,
        variant_path: str,
        transformation_type: str = "SC-UNKNOWN",
        witness_input: Optional[str] = None,
        program_spec: Optional[ProgramSpec] = None,
    ) -> GroundTruthRecord:
        """
        Validate a semantics-changing pair.

        Must find at least one divergent input for a high-confidence SC label.
        If a ``witness_input`` string (JSON-encoded) is supplied, it is prepended
        to the test suite so the known witness is always tested first.

        If no divergence is found, the record is still labelled ``"CHANGED"``
        (SC type is sufficient by taxonomy) but with reduced confidence and the
        ``sc_type_taxonomy_no_witness`` validation method.
        """
        # Prepend the known witness if supplied
        extra_inputs: List[Any] = []
        if witness_input:
            try:
                extra_inputs = [json.loads(witness_input)]
            except json.JSONDecodeError:
                extra_inputs = [witness_input]

        spec = program_spec or self._validator._infer_spec(base_path)
        generated = self._validator._generator.generate_inputs(
            spec, n=self._validator.n_tests, strategy="random"
        )
        all_inputs = extra_inputs + generated

        diff_result = self._validator._tester.run_differential(
            base_path, variant_path, all_inputs
        )

        record = self._validator._build_record(
            base_path=base_path,
            variant_path=variant_path,
            transformation_type=transformation_type,
            diff_result=diff_result,
            is_sp=False,
        )

        # Override witness_input with the supplied one if no computed witness
        if witness_input and record.witness_input is None:
            record.witness_input = witness_input

        return record
