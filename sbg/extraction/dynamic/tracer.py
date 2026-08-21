"""
sbg.extraction.dynamic.tracer
==============================
Dynamic execution tracing via sys.settrace and Execution Genome extraction.

Formal grounding
----------------
* ExecutionTrace  ↔  τ(P, i)          (Definition 5, FORMAL_MODEL.md)
* TraceEvent      ↔  e_j              (Definition 5)
* ExecutionGenome ↔  g_U              (Definition 16)
* distance        ↔  d_U              (Definition 17, row U)
* canonicalize    ↔  𝒩_dist / 𝒞_ε   (Definition 22b)

Constraints
-----------
* No third-party imports.
* sys.settrace is always restored in a finally block (even on timeout/exception).
* Existing tracer (e.g. pytest-cov) is saved before installation and restored after.
"""

from __future__ import annotations

import hashlib
import math
import sys
import threading
import time
from dataclasses import dataclass, field
from io import StringIO
from typing import Any, Callable, Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# TraceEvent
# ---------------------------------------------------------------------------

@dataclass
class TraceEvent:
    """A single sys.settrace callback, corresponding to e_j in Definition 5."""

    event_type: str                      # "call", "return", "exception", "line"
    function_name: str
    lineno: int
    local_vars_snapshot: Dict[str, str]  # repr of locals, capped at 100 chars each
    timestamp_ns: int


# ---------------------------------------------------------------------------
# ExecutionTrace
# ---------------------------------------------------------------------------

@dataclass
class ExecutionTrace:
    """
    Full trace for one (program, input) pair — τ(P, i) per Definition 5.

    ``truncated`` is True when the event stream was capped at max_events before
    the function returned; this corresponds to the timeout / truncation regime
    described in Assumption A5.
    """

    program_id: str
    input_repr: str
    events: List[TraceEvent]
    return_value: Any
    exception: Optional[str]
    stdout: str
    execution_time_ms: float
    coverage: Set[int]           # line numbers reached during this trace
    truncated: bool = False      # True iff event stream hit max_events cap


# ---------------------------------------------------------------------------
# _TraceState — mutable bundle shared between the host thread and the tracer
# ---------------------------------------------------------------------------

class _TraceState:
    """Internal bookkeeping for a single trace run."""

    __slots__ = (
        "events",
        "coverage",
        "max_events",
        "truncated",
        "timed_out",
        "deadline_ns",
    )

    def __init__(self, max_events: int, timeout_s: float) -> None:
        self.events: List[TraceEvent] = []
        self.coverage: Set[int] = set()
        self.max_events: int = max_events
        self.truncated: bool = False
        self.timed_out: bool = False
        self.deadline_ns: int = time.monotonic_ns() + int(timeout_s * 1_000_000_000)


# ---------------------------------------------------------------------------
# Tracer
# ---------------------------------------------------------------------------

_TIMEOUT_SECONDS = 5.0


class Tracer:
    """
    Runs a callable under sys.settrace for each supplied input value, returning
    one ExecutionTrace per input.

    Design notes
    ------------
    * Each function call is executed in a **dedicated worker thread** so that
      the host can enforce a hard wall-clock timeout by joining with a deadline
      and abandoning the worker if it does not finish in time.  This correctly
      handles blocking C-level calls (e.g. time.sleep) that cannot be
      interrupted by PyThreadState_SetAsyncExc.
    * sys.settrace is installed inside the worker thread (each thread has its
      own trace hook) and is always restored in a ``finally`` block inside that
      thread, even on exception or timeout.  The *host* thread's tracer (e.g.
      pytest-cov's Coverage hook) is never touched.
    * Stdout is captured per-trace via a StringIO replacement of sys.stdout
      inside the worker thread.
    """

    def trace(
        self,
        func: Callable,
        inputs: List[Any],
        max_events: int = 10_000,
    ) -> List[ExecutionTrace]:
        """
        Execute ``func`` once for each element in ``inputs`` under sys.settrace.

        Parameters
        ----------
        func:
            The callable to trace.  Called as ``func(input_value)``.
        inputs:
            One trace is produced per element.
        max_events:
            Hard cap on TraceEvent objects collected per trace.  When the cap
            is reached the trace is flagged as ``truncated`` and tracing is
            disabled for the remainder of that execution.

        Returns
        -------
        List[ExecutionTrace]
            One entry per element of ``inputs``, in order.
        """
        traces: List[ExecutionTrace] = []
        program_id = getattr(func, "__qualname__", repr(func))

        for inp in inputs:
            trace = self._trace_one(func, inp, program_id, max_events)
            traces.append(trace)

        return traces

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _trace_one(
        self,
        func: Callable,
        inp: Any,
        program_id: str,
        max_events: int,
    ) -> ExecutionTrace:
        import queue as _queue

        input_repr = repr(inp)
        result_q: "_queue.Queue[ExecutionTrace]" = _queue.Queue(maxsize=1)
        start_ns = time.monotonic_ns()

        worker = _WorkerThread(
            func=func,
            inp=inp,
            program_id=program_id,
            input_repr=input_repr,
            max_events=max_events,
            result_q=result_q,
        )
        worker.start()
        worker.join(timeout=_TIMEOUT_SECONDS)

        elapsed_ms = (time.monotonic_ns() - start_ns) / 1_000_000

        if not result_q.empty():
            trace = result_q.get_nowait()
            # Overwrite elapsed_ms with wall-clock time measured by host.
            trace.execution_time_ms = elapsed_ms
            return trace

        # Worker is still running (blocked on C call, e.g. time.sleep).
        # Mark as timed-out and return a partial trace from whatever state
        # was accumulated before the join deadline.
        state = worker.state  # access shared state directly
        if state is not None:
            state.timed_out = True
        return ExecutionTrace(
            program_id=program_id,
            input_repr=input_repr,
            events=state.events if state is not None else [],
            return_value=None,
            exception="TimeoutError: execution exceeded 5 s",
            stdout="",
            execution_time_ms=elapsed_ms,
            coverage=state.coverage if state is not None else set(),
            truncated=state.truncated if state is not None else False,
        )


# ---------------------------------------------------------------------------
# _WorkerThread — runs the traced function in isolation
# ---------------------------------------------------------------------------

class _WorkerThread(threading.Thread):
    """
    Executes ``func(inp)`` under sys.settrace in a dedicated thread.

    The thread's own tracer is installed and restored here; the host thread's
    tracer is completely untouched.
    """

    def __init__(
        self,
        func: Callable,
        inp: Any,
        program_id: str,
        input_repr: str,
        max_events: int,
        result_q: "Any",
    ) -> None:
        super().__init__(daemon=True)
        self.func = func
        self.inp = inp
        self.program_id = program_id
        self.input_repr = input_repr
        self.max_events = max_events
        self.result_q = result_q
        # Exposed so the host can read partial state on timeout.
        self.state: Optional[_TraceState] = None

    def run(self) -> None:
        state = _TraceState(self.max_events, _TIMEOUT_SECONDS)
        self.state = state  # make visible to host before tracing begins

        return_value: Any = None
        exception_str: Optional[str] = None
        stdout_buf = StringIO()
        start_ns = time.monotonic_ns()

        original_stdout = sys.stdout
        sys.stdout = stdout_buf

        try:
            sys.settrace(_make_trace_fn(state))
            try:
                return_value = self.func(self.inp)
            except Exception as exc:  # noqa: BLE001
                exception_str = f"{type(exc).__name__}: {exc}"
            finally:
                # Always restore this thread's tracer.
                sys.settrace(None)
        finally:
            sys.stdout = original_stdout

        elapsed_ms = (time.monotonic_ns() - start_ns) / 1_000_000

        result = ExecutionTrace(
            program_id=self.program_id,
            input_repr=self.input_repr,
            events=state.events,
            return_value=return_value,
            exception=exception_str,
            stdout=stdout_buf.getvalue(),
            execution_time_ms=elapsed_ms,
            coverage=state.coverage,
            truncated=state.truncated,
        )
        try:
            self.result_q.put_nowait(result)
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# _make_trace_fn — factory for the sys.settrace callback
# ---------------------------------------------------------------------------

def _make_trace_fn(state: _TraceState):
    """Return a trace function closed over *state*."""

    def _trace(frame, event, arg):  # noqa: ANN001
        # If the deadline has passed, disable tracing immediately.
        if time.monotonic_ns() > state.deadline_ns:
            state.timed_out = True
            sys.settrace(None)
            frame.f_trace = None
            return None

        # Hard cap on event count.
        if len(state.events) >= state.max_events:
            state.truncated = True
            sys.settrace(None)
            frame.f_trace = None
            return None

        # Record coverage (line events carry the authoritative line number).
        lineno: int = frame.f_lineno
        state.coverage.add(lineno)

        # Snapshot local variables — repr, capped at 100 chars.
        snapshot: Dict[str, str] = {}
        try:
            for k, v in frame.f_locals.items():
                r = repr(v)
                snapshot[k] = r[:100] if len(r) > 100 else r
        except Exception:  # noqa: BLE001
            pass

        state.events.append(
            TraceEvent(
                event_type=event,
                function_name=frame.f_code.co_name,
                lineno=lineno,
                local_vars_snapshot=snapshot,
                timestamp_ns=time.monotonic_ns(),
            )
        )

        return _trace  # Must return self to trace inner calls.

    return _trace


# ---------------------------------------------------------------------------
# ExecutionGenome
# ---------------------------------------------------------------------------

@dataclass
class ExecutionGenome:
    """
    Aggregated EXECUTION-dimension genome — g_U per Definition 16.

    Fields
    ------
    coverage_vector:
        Sorted union of all line numbers reached across all traces (COV̄).
    function_call_counts:
        Aggregate call-event counts across all traces, keyed by function name
        (approximates ITH aggregated for call-type operations).
    instruction_type_histogram:
        Total event-type counts across all traces {"call", "return",
        "exception", "line"}.
    hot_path_signature:
        SHA-256 prefix of the names of the top-5 most-called functions by
        count, ordered descending then lexicographically (HPS̄).
    trace_length_stats:
        Descriptive statistics {"mean", "std", "min", "max"} of per-trace
        event counts.
    truncated_trace_fraction:
        Fraction of input traces where event collection was capped.
    provenance:
        Metadata dictionary (program_id, n_traces, extraction timestamp).
    """

    coverage_vector: List[int]
    function_call_counts: Dict[str, int]
    instruction_type_histogram: Dict[str, int]
    hot_path_signature: str
    trace_length_stats: Dict[str, float]
    truncated_trace_fraction: float
    provenance: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# ExecutionGenomeExtractor
# ---------------------------------------------------------------------------

class ExecutionGenomeExtractor:
    """
    Implements Φ_U: List[ExecutionTrace] → ExecutionGenome.

    Aggregation follows Definition 21 (frequency-weighted union for sets,
    summed counts for histograms).
    """

    def extract(self, traces: List[ExecutionTrace]) -> ExecutionGenome:
        if not traces:
            return ExecutionGenome(
                coverage_vector=[],
                function_call_counts={},
                instruction_type_histogram={},
                hot_path_signature=_hot_path_signature({}),
                trace_length_stats={"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0},
                truncated_trace_fraction=0.0,
                provenance={"n_traces": 0},
            )

        # --- Coverage: sorted union across all traces ----------------------
        coverage_union: Set[int] = set()
        for t in traces:
            coverage_union.update(t.coverage)
        coverage_vector = sorted(coverage_union)

        # --- Function call counts & instruction histogram ------------------
        call_counts: Dict[str, int] = {}
        instr_hist: Dict[str, int] = {"call": 0, "return": 0, "exception": 0, "line": 0}

        for t in traces:
            for ev in t.events:
                et = ev.event_type
                instr_hist[et] = instr_hist.get(et, 0) + 1
                if et == "call":
                    call_counts[ev.function_name] = (
                        call_counts.get(ev.function_name, 0) + 1
                    )

        # --- Trace length statistics ----------------------------------------
        lengths = [float(len(t.events)) for t in traces]
        n = len(lengths)
        mean_len = sum(lengths) / n
        variance = sum((x - mean_len) ** 2 for x in lengths) / n
        std_len = math.sqrt(variance)

        trace_length_stats = {
            "mean": mean_len,
            "std": std_len,
            "min": min(lengths),
            "max": max(lengths),
        }

        # --- Truncated fraction ---------------------------------------------
        n_truncated = sum(1 for t in traces if t.truncated)
        truncated_fraction = n_truncated / n

        # --- Provenance ------------------------------------------------------
        program_ids = list({t.program_id for t in traces})
        provenance: Dict[str, Any] = {
            "program_ids": program_ids,
            "n_traces": n,
            "extraction_timestamp": time.time(),
        }

        return ExecutionGenome(
            coverage_vector=coverage_vector,
            function_call_counts=call_counts,
            instruction_type_histogram=instr_hist,
            hot_path_signature=_hot_path_signature(call_counts),
            trace_length_stats=trace_length_stats,
            truncated_trace_fraction=truncated_fraction,
            provenance=provenance,
        )


# ---------------------------------------------------------------------------
# _hot_path_signature helper
# ---------------------------------------------------------------------------

def _hot_path_signature(call_counts: Dict[str, int]) -> str:
    """
    SHA-256 (first 16 hex chars) of the names of the top-5 most-called
    functions, ordered by descending count then lexicographically.

    Corresponds to HPS̄ in Definition 16: 'set of top-k most frequently
    executed … sequences'.
    """
    top5 = sorted(call_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    key = "|".join(name for name, _ in top5)
    return hashlib.sha256(key.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# distance  (Definition 17, row U / Definition 18)
# ---------------------------------------------------------------------------

def distance(g1: ExecutionGenome, g2: ExecutionGenome) -> float:
    """
    Pseudometric on ExecutionGenome in [0, 1].

    Formula (Definition 17, row U + Definition 18):
        d = 0.5 * jaccard_distance(coverage) + 0.5 * l1_call_count_distance

    Jaccard distance on coverage vectors
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Jaccard similarity  J = |A ∩ B| / |A ∪ B|  (0 when both empty)
    Jaccard distance  = 1 − J

    L1 distance on normalised call-count histograms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Each histogram is normalised to a probability distribution (Definition
    22b).  The L1 distance between two probability distributions is in [0, 2];
    we halve it to obtain a value in [0, 1].
    """
    # --- Jaccard on coverage ------------------------------------------------
    cov1 = set(g1.coverage_vector)
    cov2 = set(g2.coverage_vector)
    union_size = len(cov1 | cov2)
    if union_size == 0:
        jaccard_dist = 0.0
    else:
        intersection_size = len(cov1 & cov2)
        jaccard_dist = 1.0 - intersection_size / union_size

    # --- Normalised L1 on call-count histograms ------------------------------
    all_funcs = set(g1.function_call_counts) | set(g2.function_call_counts)
    if not all_funcs:
        call_dist = 0.0
    else:
        total1 = sum(g1.function_call_counts.values()) or 1
        total2 = sum(g2.function_call_counts.values()) or 1
        l1 = sum(
            abs(
                g1.function_call_counts.get(f, 0) / total1
                - g2.function_call_counts.get(f, 0) / total2
            )
            for f in all_funcs
        )
        # l1 ∈ [0, 2] for normalised distributions → scale to [0, 1]
        call_dist = l1 / 2.0

    return 0.5 * jaccard_dist + 0.5 * call_dist


# ---------------------------------------------------------------------------
# canonicalize  (Definition 22b)
# ---------------------------------------------------------------------------

def canonicalize(g: ExecutionGenome) -> ExecutionGenome:
    """
    Return a canonical form of *g* per Definition 22b (distribution
    normalisation) and ensure structural invariants hold:

    * coverage_vector is sorted and deduplicated.
    * function_call_counts and instruction_type_histogram values are
      non-negative integers.
    * hot_path_signature is recomputed from the (possibly cleaned) call counts.
    * provenance gains a ``canonicalized`` timestamp.

    This operation is idempotent: canonicalize(canonicalize(g)) == canonicalize(g).
    """
    # Clean coverage vector: sort + deduplicate.
    clean_cov = sorted(set(g.coverage_vector))

    # Clean call counts: drop zero/negative entries.
    clean_calls = {k: v for k, v in g.function_call_counts.items() if v > 0}

    # Clean instruction histogram: ensure all four standard keys exist,
    # drop non-positive values.
    clean_instr: Dict[str, int] = {}
    for key in ("call", "return", "exception", "line"):
        val = g.instruction_type_histogram.get(key, 0)
        clean_instr[key] = max(0, int(val))
    for key, val in g.instruction_type_histogram.items():
        if key not in clean_instr and val > 0:
            clean_instr[key] = int(val)

    # Recompute hot-path signature from cleaned call counts.
    clean_hps = _hot_path_signature(clean_calls)

    # Clamp truncated fraction to [0, 1].
    frac = max(0.0, min(1.0, g.truncated_trace_fraction))

    # Propagate provenance with canonicalization marker.
    prov = dict(g.provenance)
    prov["canonicalized"] = True

    return ExecutionGenome(
        coverage_vector=clean_cov,
        function_call_counts=clean_calls,
        instruction_type_histogram=clean_instr,
        hot_path_signature=clean_hps,
        trace_length_stats=dict(g.trace_length_stats),
        truncated_trace_fraction=frac,
        provenance=prov,
    )
