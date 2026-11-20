"""
sbg.repair.execution_profile
=============================
Extended Execution Profile (EEP) — output-free representation repair.

This module implements the principled representation repair designed in
docs/representation_repair_design.md.

SCIENTIFIC DESIGN PRINCIPLE
===========================
The current SBG proxy (exception_fraction + exception_types + wall_time) misses
~87% of real regressions because these bugs change RETURN VALUES but NOT EXCEPTION
BEHAVIOR or EXECUTION VOLUME.

This repair adds three output-free structural features:

1. trace_length_profile_distance (d_tl):
   Per-input execution trace length vector comparison.
   Detects: off-by-one in loops, missing break, wrong slice in recursion,
            mutation during iteration, wrong variable in branch.

2. line_sequence_divergence (d_ls):
   Fraction of inputs where the anonymized line-execution sequence differs.
   Detects: wrong operator in conditional, wrong comparison in loop bound,
            wrong branch selection.

3. sequential_state_drift (d_sd):
   Behavioral divergence when the same input is executed TWICE sequentially.
   Detects: mutable default argument bugs, global state accumulation.

OUTPUT-FREE GUARANTEE
=====================
All three features measure STRUCTURAL control-flow properties:
- trace_length: cardinality of sys.settrace event list
- line_sequence: sequence of (anon_fn, line_number) pairs
- state_drift: change in trace behavior across sequential calls

None of these features access:
- return_value
- stdout / stderr
- test pass/fail
- mutation label
- ground-truth regression label

FORMAL INVARIANT
================
If programs A and B have IDENTICAL control flow (same branches taken,
same iteration counts, same call graph) but produce different return values,
then:
    d_tl(A, B) = 0
    d_ls(A, B) = 0
    d_sd(A, B) = 0

This is the correct behavior: such programs are structurally equivalent.
"""
from __future__ import annotations

import hashlib
import math
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple



# ---------------------------------------------------------------------------
# Argument-wrapping helper
# ---------------------------------------------------------------------------

def _make_arg_wrapper(fn: Callable, inp: Any) -> Callable:
    """
    Return a zero-argument callable that calls fn with inp.

    If inp is a tuple, calls fn(*inp).
    Otherwise calls fn(inp).

    This lets _run_and_collect always call wrapper(None) while handling
    both single-argument and multi-argument test corpora transparently.
    """
    if isinstance(inp, tuple):
        def _wrapper(_ignored):
            return fn(*inp)
    else:
        def _wrapper(_ignored):
            return fn(inp)
    return _wrapper



# ---------------------------------------------------------------------------
# Execution capture (self-contained, no dependency on full SBG pipeline)
# ---------------------------------------------------------------------------

class _TraceEvent:
    """Minimal trace event for the repair module."""
    __slots__ = ("event_type", "function_name", "rel_lineno")

    def __init__(self, event_type: str, function_name: str, rel_lineno: int) -> None:
        self.event_type = event_type
        self.function_name = function_name
        self.rel_lineno = rel_lineno


def _run_and_collect(
    fn: Callable,
    arg: Any,
    max_events: int = 5000,
    timeout_s: float = 3.0,
) -> Tuple[List[_TraceEvent], Optional[str]]:
    """
    Run fn(arg) under sys.settrace and collect trace events.

    Returns (events, exception_type_or_None).

    This function NEVER reads return_value, stdout, or stderr.
    It only collects structural trace events.

    RELATIVE LINE NUMBERS: We use (lineno - co_firstlineno) — the line offset
    within the function — not the absolute source file line number. This makes
    the representation invariant to where the function is defined in a file.
    Two functions with identical bodies will have identical rel_lineno sequences
    regardless of their position in the source file.
    """
    import sys
    import queue as _queue

    result_q: "_queue.Queue[Tuple[List[_TraceEvent], Optional[str]]]" = _queue.Queue(maxsize=1)

    def _worker() -> None:
        _events: List[_TraceEvent] = []
        _exc: Optional[str] = None
        _truncated = False

        def _tracer(frame, event, arg_):  # noqa: ANN001
            nonlocal _truncated
            if len(_events) >= max_events:
                _truncated = True
                sys.settrace(None)
                frame.f_trace = None
                return None
            if event in ("call", "return", "exception", "line"):
                # Use relative line offset: lineno - co_firstlineno
                # This is rename+reposition-invariant: two identical functions
                # at different positions in a file get the same rel_lineno.
                rel_line = frame.f_lineno - frame.f_code.co_firstlineno
                _events.append(_TraceEvent(event, frame.f_code.co_name, rel_line))
            return _tracer

        orig = sys.gettrace()
        try:
            sys.settrace(_tracer)
            try:
                fn(arg)
            except Exception as e:  # noqa: BLE001
                _exc = type(e).__name__
            finally:
                sys.settrace(orig)
        finally:
            pass

        try:
            result_q.put_nowait((_events, _exc))
        except Exception:  # noqa: BLE001
            pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout_s)

    if not result_q.empty():
        return result_q.get_nowait()

    # Timeout — return empty
    return [], "TimeoutError"


# ---------------------------------------------------------------------------
# Execution Profile Extractor
# ---------------------------------------------------------------------------

class ExecutionProfileExtractor:
    """
    Compute the Extended Execution Profile for a callable.

    Parameters
    ----------
    inputs : list of args (each element is passed as the single arg to fn)
    max_events : hard cap on trace events per input
    timeout_s : per-input execution timeout in seconds

    All features are OUTPUT-FREE. See module docstring for guarantee.
    """

    def __init__(
        self,
        max_events: int = 5000,
        timeout_s: float = 3.0,
        n_sequential_repeats: int = 2,
    ) -> None:
        self.max_events = max_events
        self.timeout_s = timeout_s
        self.n_sequential_repeats = n_sequential_repeats

    def extract(
        self,
        fn: Callable,
        inputs: List[Any],
    ) -> "ExecutionProfile":
        """
        Extract execution profile from fn over given inputs.

        Returns an ExecutionProfile with:
        - trace_lengths: [n_events per input]
        - line_seq_hashes: [hash of anon line sequence per input]
        - call_depth_maxima: [max call depth per input]
        - sequential_drift: divergence score for repeated calls
        - exception_types_per_input: [exc_type or None per input]

        INPUT HANDLING:
        If an input is a tuple, it is UNPACKED as positional arguments: fn(*inp).
        If an input is NOT a tuple, it is passed directly: fn(inp).
        This matches the convention used in regression test corpora where inputs
        are stored as (arg1, arg2, ...) tuples.
        """
        trace_lengths: List[int] = []
        line_seq_hashes: List[str] = []
        call_depth_maxima: List[int] = []
        exc_types: List[Optional[str]] = []

        # Build anonymization map on first pass
        name_to_idx: Dict[str, int] = {}

        for inp in inputs:
            # Wrap fn to handle tuple unpacking transparently
            wrapped = _make_arg_wrapper(fn, inp)
            events, exc = _run_and_collect(wrapped, None, self.max_events, self.timeout_s)

            # Update anonymization map
            for ev in events:
                if ev.event_type == "call" and ev.function_name not in name_to_idx:
                    name_to_idx[ev.function_name] = len(name_to_idx)

            trace_lengths.append(len(events))
            line_seq_hashes.append(self._line_seq_hash(events, name_to_idx))
            call_depth_maxima.append(self._max_call_depth(events))
            exc_types.append(exc)

        # Sequential state drift: run FIRST input twice in sequence, measure divergence
        drift = self._compute_sequential_drift(fn, inputs, name_to_idx)

        return ExecutionProfile(
            trace_lengths=trace_lengths,
            line_seq_hashes=line_seq_hashes,
            call_depth_maxima=call_depth_maxima,
            exception_types=exc_types,
            sequential_drift=drift,
            n_inputs=len(inputs),
            name_to_idx=dict(name_to_idx),
        )

    def _line_seq_hash(
        self,
        events: List[_TraceEvent],
        name_to_idx: Dict[str, int],
    ) -> str:
        """
        Compute a hash of the anonymized (fn_idx, rel_lineno) sequence.

        Rename-invariant: uses function index, not name.
        Position-invariant: uses rel_lineno (offset from function start),
        not absolute lineno — so two identical functions at different file
        positions get the same hash.
        Output-free: captures execution structure, not values.
        """
        parts = []
        for ev in events:
            if ev.event_type in ("call", "line"):
                fn_idx = name_to_idx.get(ev.function_name, -1)
                parts.append(f"{fn_idx}:{ev.rel_lineno}")
        key = "|".join(parts)
        return hashlib.md5(key.encode()).hexdigest()[:12]

    def _max_call_depth(self, events: List[_TraceEvent]) -> int:
        """Compute maximum call stack depth during execution."""
        depth = max_depth = 0
        for ev in events:
            if ev.event_type == "call":
                depth += 1
                max_depth = max(max_depth, depth)
            elif ev.event_type == "return":
                depth = max(0, depth - 1)
        return max_depth

    def _compute_sequential_drift(
        self,
        fn: Callable,
        inputs: List[Any],
        name_to_idx: Dict[str, int],
        make_wrapper: Callable = None,
    ) -> float:
        """
        Measure behavioral drift across sequential calls.

        Runs the FIRST input N times in sequence. If the function has
        mutable state (default arguments, global state), behavior will
        differ between call 1 and call N.

        Returns: fraction of (function, lineno) line-events that differ
        between first and last sequential run, normalized to [0, 1].

        This is output-free: measures structural (trace) change, not value change.
        """
        if not inputs:
            return 0.0

        first_inp = inputs[0]
        n_runs = self.n_sequential_repeats

        run_hashes = []
        for _ in range(n_runs):
            if make_wrapper is not None:
                wrapped = make_wrapper(fn, first_inp)
                events, _ = _run_and_collect(wrapped, None, self.max_events, self.timeout_s)
            else:
                events, _ = _run_and_collect(fn, first_inp, self.max_events, self.timeout_s)
            # Update name_to_idx with any new names
            for ev in events:
                if ev.event_type == "call" and ev.function_name not in name_to_idx:
                    name_to_idx[ev.function_name] = len(name_to_idx)
            run_hashes.append(self._line_seq_hash(events, name_to_idx))

        if len(run_hashes) < 2:
            return 0.0

        # Fraction of sequential run pairs where behavior differs
        n_pairs = len(run_hashes) - 1
        n_differ = sum(1 for i in range(n_pairs) if run_hashes[i] != run_hashes[i + 1])
        return n_differ / max(n_pairs, 1)


# ---------------------------------------------------------------------------
# ExecutionProfile dataclass
# ---------------------------------------------------------------------------

class ExecutionProfile:
    """
    Output-free execution profile for one program.

    Fields
    ------
    trace_lengths       : number of sys.settrace events per input
    line_seq_hashes     : anonymized line-execution sequence hash per input
    call_depth_maxima   : max call depth per input
    exception_types     : exception type (or None) per input
    sequential_drift    : float in [0, 1] — cross-call behavioral change
    n_inputs            : number of inputs used
    name_to_idx         : function name → anonymized index
    """

    def __init__(
        self,
        trace_lengths: List[int],
        line_seq_hashes: List[str],
        call_depth_maxima: List[int],
        exception_types: List[Optional[str]],
        sequential_drift: float,
        n_inputs: int,
        name_to_idx: Dict[str, int],
    ) -> None:
        self.trace_lengths = trace_lengths
        self.line_seq_hashes = line_seq_hashes
        self.call_depth_maxima = call_depth_maxima
        self.exception_types = exception_types
        self.sequential_drift = sequential_drift
        self.n_inputs = n_inputs
        self.name_to_idx = name_to_idx

    def exception_fraction(self) -> float:
        if not self.exception_types:
            return 0.0
        return sum(1 for e in self.exception_types if e is not None) / len(self.exception_types)

    def exception_type_set(self) -> set:
        return {e for e in self.exception_types if e is not None}

    def mean_trace_length(self) -> float:
        if not self.trace_lengths:
            return 0.0
        return sum(self.trace_lengths) / len(self.trace_lengths)

    def mean_call_depth(self) -> float:
        if not self.call_depth_maxima:
            return 0.0
        return sum(self.call_depth_maxima) / len(self.call_depth_maxima)


# ---------------------------------------------------------------------------
# Distance Function
# ---------------------------------------------------------------------------

def compute_eep_distance(pa: ExecutionProfile, pb: ExecutionProfile) -> float:
    """
    Compute the Extended Execution Profile (EEP) distance.

    Formula (output-free):
        d = 0.40 * d_exc_frac          (exception rate — existing signal)
          + 0.10 * d_exc_jaccard        (exception type overlap — existing)
          + 0.30 * d_trace_length       (NEW: per-input trace length)
          + 0.15 * d_line_seq           (NEW: line sequence divergence)
          + 0.05 * d_sequential_drift   (NEW: cross-call state drift)

    All components are in [0, 1].

    Scientific justification for new components:
    - d_trace_length: detects loop-count changes, recursion depth changes
    - d_line_seq: detects branch selection changes, path changes
    - d_sequential_drift: detects mutable state bugs

    OUTPUT-FREE: see module docstring for formal guarantee.
    """
    # --- Component 1: Exception fraction ---
    d_exc_frac = abs(pa.exception_fraction() - pb.exception_fraction())

    # --- Component 2: Exception type Jaccard ---
    sa, sb = pa.exception_type_set(), pb.exception_type_set()
    union_exc = len(sa | sb)
    d_exc_jac = 0.0 if union_exc == 0 else 1.0 - len(sa & sb) / union_exc

    # --- Component 3: Per-input trace length profile ---
    d_trace_length = _trace_length_distance(pa.trace_lengths, pb.trace_lengths)

    # --- Component 4: Line sequence divergence ---
    d_line_seq = _line_seq_divergence(pa.line_seq_hashes, pb.line_seq_hashes)

    # --- Component 5: Sequential state drift ---
    d_drift = abs(pa.sequential_drift - pb.sequential_drift)

    total = (
        0.40 * d_exc_frac
        + 0.10 * d_exc_jac
        + 0.30 * d_trace_length
        + 0.15 * d_line_seq
        + 0.05 * d_drift
    )
    return max(0.0, min(1.0, total))


def _trace_length_distance(lengths_a: List[int], lengths_b: List[int]) -> float:
    """
    Per-input normalized trace length L1 distance.

    Normalize by max observed length to put in [0, 1].
    """
    n = min(len(lengths_a), len(lengths_b))
    if n == 0:
        return 0.0

    max_len = max(max(lengths_a[:n], default=1), max(lengths_b[:n], default=1), 1)

    total = 0.0
    for la, lb in zip(lengths_a[:n], lengths_b[:n]):
        total += abs(la - lb) / max_len

    return min(1.0, total / n)


def _line_seq_divergence(hashes_a: List[str], hashes_b: List[str]) -> float:
    """
    Fraction of inputs where line execution sequence differs.

    Compares anonymized line-sequence hashes. If hash_a[i] != hash_b[i],
    the programs took different execution paths for input i.
    """
    n = min(len(hashes_a), len(hashes_b))
    if n == 0:
        return 0.0

    n_differ = sum(1 for ha, hb in zip(hashes_a[:n], hashes_b[:n]) if ha != hb)
    return n_differ / n
