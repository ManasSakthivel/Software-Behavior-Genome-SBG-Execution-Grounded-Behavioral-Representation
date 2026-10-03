"""
experiments/final/extraction.py
===============================
One shared execution pass per program, reused by every predictor.

Why this exists
---------------
In the V4/V5 scripts each predictor ran its own extraction with its own entry
function discovery, its own input set and its own run count:

  baselines/v5/b07_dynamic_v5.py    11 canonical inputs, 5 runs, max_events 5000,
                                    entry discovery with invariant-identity step
  experiments/v4/phase1_volume_control.py
                                     V3 input set,      3 runs, max_events 3000,
                                    simpler entry discovery

Any AUROC difference between SBG and a "shortcut control" measured that way
confounds the representation with the execution protocol, and the two runs can
disagree about which pairs are evaluable. This module executes each program
exactly once under one protocol and hands every predictor the same traces, so
comparisons differ only in the feature used.

It also records *why* a program could not be executed, instead of dropping it
silently the way ``_score_pairs`` did.
"""
from __future__ import annotations

import ast
import copy
import importlib.util
import inspect
import io
import json
import pathlib
import sys
import types
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sbg.v2.execution.runner import SandboxRunner
from sbg.v3.genome import DynamicGenomeExtractorV3, DynamicGenomeV3, distance_v3
from sbg.v5.invariant_identity import (
    compute_function_fingerprint, compute_program_identity, fingerprint_similarity,
)
from sbg.v5.state_transition_genome import StateTransitionGenome
from sbg.v5.temporal_genome_v5 import distance as temporal_distance
from sbg.v5.temporal_genome_v5 import extract as extract_temporal

from experiments.final.protocol import select_entry_output_free
from experiments.final.class_driver import select_class_entry

SEED = 42
N_RUNS = 5
MAX_EVENTS = 5000

# Execution budgets.
#
# PROTOCOL "published" keeps the tracer's own 5 s per-trace default and no
# per-program budget, so it reproduces the published run exactly.
#
# PROTOCOL "output_free_v6" traces a real API function over 11 synthesised
# inputs rather than a zero-argument driver over one, so it performs 55 traced
# executions per program instead of 5. Mutants that fail to terminate then cost
# 55 x 5 s each. Both budgets below are fixed constants, declared before any
# result was computed, and applied identically to the base and the variant of
# every pair -- so they cannot favour one predictor over another. Every program
# that hits the program budget is recorded in the failure ledger rather than
# dropped. The base programs complete in milliseconds; 1 s is three orders of
# magnitude of headroom.
TRACE_TIMEOUT_S = {"published": None, "output_free_v6": 1.0, "output_free_v7": 1.0}
PROGRAM_BUDGET_S = {"published": None, "output_free_v6": 60.0, "output_free_v7": 60.0}
# A timed-out trace leaves an unkillable worker thread behind. Under
# output_free_v6 a mutant that loops forever would leave one per input per run;
# after two of them the program is recorded as nonterminating and its pairs go
# into the failure ledger. Base programs terminate in milliseconds, so this
# only ever fires on a mutant.
# output_free_v7 (docs/current/PHASE2_PREREGISTRATION.md §1) uses the v6
# budgets unchanged.
MAX_TIMEOUTS = {"published": None, "output_free_v6": 2, "output_free_v7": 2}

# Identical to baselines/v5/b07_dynamic_v5.py::V5_CANONICAL_INPUTS.
CANONICAL_INPUTS: List[Any] = [
    [], [1], [3, 1, 4, 1, 5, 9, 2, 6], [10, 9, 8, 7, 6, 5], [0, 0, 0, 0],
    [2, 1], [-3, 0, 3], list(range(8)), list(range(1)), list(range(3)),
    list(range(16)),
]

PRIORITY_NAMES = (
    "sort", "search", "run", "main", "solve", "process", "compute",
    "encode", "decode", "parse", "validate", "execute", "transform",
    "merge", "split", "compress", "decompress", "insert", "remove",
    "add", "find", "build", "evaluate",
)

# Failure taxonomy. Every unevaluable program lands in exactly one bucket.
FAILURE_KINDS = (
    "file_missing",          # path not on disk
    "syntax_error",          # source does not compile: corrupt generated variant
    "import_error",          # module-level code raised while loading
    "no_entry_function",     # no module-level function: outside the protocol's scope
    "unsupported_signature", # output_free_v6: no API function synthesisable from the battery
    "trace_error",           # the sandbox itself raised
    "empty_trace",           # executed but produced no usable trace
    "nonterminating",        # exceeded the per-trace budget on >= 2 inputs
)

PROTOCOLS = ("published", "output_free_v6", "output_free_v7")

_runner = SandboxRunner()
_extractor_v3 = DynamicGenomeExtractorV3()
_state_genome = StateTransitionGenome()


@dataclass
class ProgramRecord:
    """Everything any predictor needs about one program, from one execution."""
    path: str
    ok: bool
    failure_kind: Optional[str] = None
    failure_detail: Optional[str] = None
    entry_function: Optional[str] = None
    entry_discovery: Optional[str] = None
    entry_detail: Dict[str, Any] = field(default_factory=dict)
    genome_v3: Optional[DynamicGenomeV3] = None
    temporal: Any = None
    state: Any = None
    stats: Dict[str, float] = field(default_factory=dict)

    def summary(self) -> dict:
        return {
            "path": self.path,
            "ok": self.ok,
            "failure_kind": self.failure_kind,
            "failure_detail": self.failure_detail,
            "entry_function": self.entry_function,
            "entry_discovery": self.entry_discovery,
            **({"entry_detail": self.entry_detail} if self.entry_detail else {}),
            "stats": self.stats,
        }


def _load_module(path: pathlib.Path) -> Tuple[Optional[types.ModuleType], Optional[str], Optional[str]]:
    if not path.exists():
        return None, "file_missing", str(path)
    source = path.read_text()
    try:
        compile(source, str(path), "exec")
    except SyntaxError as exc:
        return None, "syntax_error", f"{exc.msg} (line {exc.lineno})"

    spec = importlib.util.spec_from_file_location("_sbg_eval_prog", str(path))
    if spec is None or spec.loader is None:
        return None, "import_error", "no module spec"
    module = types.ModuleType("_sbg_eval_prog")
    saved_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        spec.loader.exec_module(module)            # type: ignore[union-attr]
    except BaseException as exc:                   # noqa: BLE001 - record, never abort
        return None, "import_error", f"{type(exc).__name__}: {exc}"
    finally:
        sys.stdout = saved_stdout
    return module, None, None


def _discover_entry(module: types.ModuleType, path: pathlib.Path
                    ) -> Tuple[Optional[Callable], Optional[str]]:
    """Same three-step rule as baselines/v5/b07_dynamic_v5.py."""
    for name in PRIORITY_NAMES:
        fn = getattr(module, name, None)
        if callable(fn) and isinstance(fn, types.FunctionType):
            return fn, f"priority:{name}"

    try:
        identity = compute_program_identity(path.read_text())
        tree = ast.parse(path.read_text())
        ast_functions = {
            node.name: node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        }
        if ast_functions and identity.root_index < len(identity.fingerprints):
            root = identity.fingerprints[identity.root_index]
            best_name, best_score = None, -1.0
            for name, node in ast_functions.items():
                try:
                    score = fingerprint_similarity(root, compute_function_fingerprint(node))
                except Exception:                  # noqa: BLE001
                    continue
                if score > best_score:
                    best_name, best_score = name, score
            if best_name:
                fn = getattr(module, best_name, None)
                if callable(fn):
                    return fn, f"invariant_identity:{best_name}"
    except Exception:                              # noqa: BLE001
        pass

    candidates = sorted(
        (name, obj) for name, obj in vars(module).items()
        if callable(obj) and isinstance(obj, types.FunctionType)
        and not name.startswith("_")
    )
    if candidates:
        return candidates[0][1], f"alphabetical:{candidates[0][0]}"
    return None, None


def extract_program(source_path: str, cache: Dict[str, ProgramRecord],
                    protocol: str = "published") -> ProgramRecord:
    """Execute one program under ``protocol``. Cached by path.

    ``cache`` must not be shared between protocols; each protocol run owns one.
    """
    if protocol not in PROTOCOLS:
        raise ValueError(f"unknown protocol {protocol!r}")
    if source_path in cache:
        return cache[source_path]

    path = pathlib.Path(source_path)
    module, kind, detail = _load_module(path)
    if module is None:
        record = ProgramRecord(path=source_path, ok=False, failure_kind=kind,
                               failure_detail=detail)
        cache[source_path] = record
        return record

    if protocol == "published":
        entry_fn, discovery = _discover_entry(module, path)
        if entry_fn is None:
            record = ProgramRecord(path=source_path, ok=False,
                                   failure_kind="no_entry_function",
                                   failure_detail="no module-level function found")
            cache[source_path] = record
            return record
        try:
            n_params = len(inspect.signature(entry_fn).parameters)
        except (ValueError, TypeError):
            n_params = 1
        if n_params == 0:
            traced_fn: Callable = lambda _inp: entry_fn()     # noqa: E731
            inputs: List[Any] = [None]
        else:
            traced_fn, inputs = entry_fn, CANONICAL_INPUTS
    else:
        entry_fn, discovery, synthesised = select_entry_output_free(module, path.read_text())
        class_detail: Dict[str, Any] = {}
        if (entry_fn is None or synthesised is None) and protocol == "output_free_v7":
            # Class tier: only reached when the v6 function tier found nothing,
            # so every program v6 covers keeps its v6 entry and inputs.
            entry_fn, discovery, synthesised, class_detail = select_class_entry(
                module, path.read_text())
            if entry_fn is not None and synthesised is not None:
                return _trace_and_record(source_path, cache, protocol, entry_fn,
                                         discovery, entry_fn, synthesised,
                                         entry_detail=class_detail)
        if entry_fn is None or synthesised is None:
            detail_text = ("no API function synthesisable from the fixed input battery"
                           + (" and no drivable class" if protocol == "output_free_v7" else ""))
            record = ProgramRecord(path=source_path, ok=False,
                                   failure_kind="unsupported_signature",
                                   failure_detail=detail_text,
                                   entry_detail=class_detail)
            cache[source_path] = record
            return record
        inputs = synthesised
        if inputs == [None]:
            traced_fn = lambda _inp: entry_fn()               # noqa: E731
        elif isinstance(inputs[0], tuple):
            traced_fn = lambda args: entry_fn(*args)          # noqa: E731
        else:
            traced_fn = entry_fn

    return _trace_and_record(source_path, cache, protocol, entry_fn, discovery,
                             traced_fn, inputs)


def _trace_and_record(source_path: str, cache: Dict[str, ProgramRecord], protocol: str,
                      entry_fn: Optional[Callable], discovery: Optional[str],
                      traced_fn: Callable, inputs: List[Any],
                      entry_detail: Optional[Dict[str, Any]] = None) -> ProgramRecord:
    """Trace ``traced_fn`` over ``inputs`` and build the ProgramRecord.

    Shared by every entry-selection rule, so a program is featurised the same
    way whether its entry came from a protocol or was declared by a corpus.
    """
    path = pathlib.Path(source_path)
    program_id = path.stem
    try:
        sandbox = _runner.run(program_id, traced_fn, inputs,
                              n_runs=N_RUNS, seed=SEED, max_events=MAX_EVENTS,
                              timeout_s=TRACE_TIMEOUT_S[protocol],
                              program_budget_s=PROGRAM_BUDGET_S[protocol],
                              max_timeouts=MAX_TIMEOUTS[protocol])
    except BaseException as exc:                   # noqa: BLE001
        record = ProgramRecord(path=source_path, ok=False, failure_kind="trace_error",
                               failure_detail=f"{type(exc).__name__}: {exc}",
                               entry_function=getattr(entry_fn, "__name__", None),
                               entry_discovery=discovery,
                               entry_detail=entry_detail or {})
        cache[source_path] = record
        return record

    if sandbox.error == "NONTERMINATING":
        record = ProgramRecord(path=source_path, ok=False, failure_kind="nonterminating",
                               failure_detail="exceeded the per-trace budget on "
                                              f"{MAX_TIMEOUTS[protocol]} inputs",
                               entry_function=getattr(entry_fn, "__name__", None),
                               entry_discovery=discovery,
                               entry_detail=entry_detail or {})
        cache[source_path] = record
        return record

    if not sandbox.traces or not any(sandbox.traces):
        record = ProgramRecord(path=source_path, ok=False, failure_kind="empty_trace",
                               failure_detail=sandbox.error or "no traces produced",
                               entry_function=getattr(entry_fn, "__name__", None),
                               entry_discovery=discovery,
                               entry_detail=entry_detail or {})
        cache[source_path] = record
        return record

    genome = _extractor_v3.extract_from_traces(program_id, sandbox.traces)

    flat_traces, events = [], []
    n_traces = n_exceptions = total_calls = 0
    function_names: set = set()
    total_events = 0
    n_truncated = 0
    for run in sandbox.traces:
        for trace in run:
            flat_traces.append(trace)
            n_traces += 1
            if trace.exception:
                n_exceptions += 1
            if getattr(trace, "truncated", False):
                n_truncated += 1
            for event in trace.events:
                total_events += 1
                if event.event_type == "call":
                    total_calls += 1
                    function_names.add(event.function_name)
                events.append({
                    "event_type": event.event_type,
                    "function_name": event.function_name,
                    "depth": getattr(event, "depth", 0),
                })

    try:
        temporal = extract_temporal(events, program_id=program_id)
    except Exception:                              # noqa: BLE001
        temporal = None
    try:
        state = _state_genome.extract(flat_traces)
    except Exception:                              # noqa: BLE001
        state = None

    record = ProgramRecord(
        path=source_path, ok=True,
        entry_function=getattr(entry_fn, "__name__", None),
        entry_discovery=discovery,
                               entry_detail=entry_detail or {},
        genome_v3=genome, temporal=temporal, state=state,
        stats={
            "n_traces": n_traces,
            "n_exception_traces": n_exceptions,
            "exception_fraction": n_exceptions / n_traces if n_traces else 0.0,
            "genome_exception_rate": genome.exception_rate,
            "call_count": total_calls,
            "n_functions": len(function_names),
            "coverage_size": genome.coverage_size,
            "n_events": total_events,
            "n_truncated_traces": n_truncated,
            "temporal_available": temporal is not None,
            "state_available": state is not None,
            "runs_completed": len(sandbox.traces),
            "program_budget_exceeded": sandbox.error == "PROGRAM_BUDGET_EXCEEDED",
        },
    )
    cache[source_path] = record
    return record


def extract_with_inputs(source_path: str, cache: Dict[str, ProgramRecord],
                        entry_name: str, inputs: List[Any],
                        budgets_from: str = "output_free_v6",
                        cache_key: Optional[str] = None) -> ProgramRecord:
    """Trace a *named* function over *declared* inputs.

    For external corpora whose inputs are supplied by the corpus (e.g. the
    input half of QuixBugs' test cases) rather than synthesised by a protocol.
    Only the inputs are used; expected outputs must never reach this function.
    Each element of ``inputs`` is the positional-argument tuple for one call.
    Budgets (per-trace timeout, program budget, non-termination rule) are taken
    from ``budgets_from`` so external runs obey the same limits.
    """
    key = cache_key or f"{source_path}::{entry_name}::declared"
    if key in cache:
        return cache[key]
    path = pathlib.Path(source_path)
    module, kind, detail = _load_module(path)
    if module is None:
        record = ProgramRecord(path=source_path, ok=False, failure_kind=kind,
                               failure_detail=detail)
        cache[key] = record
        return record
    entry_fn = getattr(module, entry_name, None)
    if not callable(entry_fn):
        record = ProgramRecord(path=source_path, ok=False,
                               failure_kind="no_entry_function",
                               failure_detail=f"{entry_name} not defined")
        cache[key] = record
        return record
    traced_fn = lambda args: entry_fn(*copy.deepcopy(args))   # noqa: E731
    record = _trace_and_record(source_path, {}, budgets_from, entry_fn,
                               f"declared:{entry_name}", traced_fn, list(inputs))
    cache[key] = record
    return record


# ---------------------------------------------------------------------------
# Predictors — every one derived from the shared ProgramRecord pair
# ---------------------------------------------------------------------------

W_V3, W_TEMPORAL, W_STATE = 0.50, 0.25, 0.25


def _ratio_distance(a: float, b: float) -> float:
    """|a - b| / (1 + |a - b|): monotone in the absolute difference, bounded.

    Monotonicity is what matters — AUROC is rank-based, so this gives the same
    ordering (and the same AUROC) as the ``1/(1 + |delta|)`` pseudo-similarity
    used by experiments/v4/phase1_volume_control.py, while staying a distance.
    """
    delta = abs(a - b)
    return delta / (1.0 + delta)


def score_pair(base: ProgramRecord, variant: ProgramRecord) -> Optional[Dict[str, float]]:
    """All predictor distances for one pair, or None if either side failed."""
    if not (base.ok and variant.ok) or base.genome_v3 is None or variant.genome_v3 is None:
        return None

    g1, g2 = base.genome_v3, variant.genome_v3
    d_v3 = distance_v3(g1, g2)

    if base.temporal is not None and variant.temporal is not None:
        try:
            d_temporal = temporal_distance(base.temporal, variant.temporal)
            temporal_ok = True
        except Exception:                          # noqa: BLE001
            d_temporal, temporal_ok = d_v3, False
    else:
        d_temporal, temporal_ok = d_v3, False

    if base.state is not None and variant.state is not None:
        try:
            d_state = _state_genome.distance(base.state, variant.state)
            state_ok = True
        except Exception:                          # noqa: BLE001
            d_state, state_ok = d_v3, False
    else:
        d_state, state_ok = d_v3, False

    v5_full = temporal_ok and state_ok
    d_v5 = (W_V3 * d_v3 + W_TEMPORAL * d_temporal + W_STATE * d_state) if v5_full else d_v3

    exc_types_1, exc_types_2 = set(g1.exception_type_set), set(g2.exception_type_set)
    union = len(exc_types_1 | exc_types_2)
    jaccard_distance = 0.0 if union == 0 else 1.0 - len(exc_types_1 & exc_types_2) / union
    exception_component = (0.5 * jaccard_distance
                           + 0.5 * abs(g1.exception_rate - g2.exception_rate))

    s1, s2 = base.stats, variant.stats
    combined = (0.30 * _ratio_distance(s1["call_count"], s2["call_count"])
                + 0.30 * _ratio_distance(s1["coverage_size"], s2["coverage_size"])
                + 0.25 * _ratio_distance(s1["n_functions"], s2["n_functions"])
                + 0.15 * _ratio_distance(s1["exception_fraction"], s2["exception_fraction"]))

    return {
        "sbg_v5": round(min(1.0, max(0.0, d_v5)), 9),
        "sbg_v3": round(d_v3, 9),
        "sbg_temporal": round(d_temporal, 9),
        "sbg_state": round(d_state, 9),
        "exception_fraction": round(_ratio_distance(s1["exception_fraction"],
                                                    s2["exception_fraction"]), 9),
        "exception_component_v3": round(exception_component, 9),
        "exception_type_jaccard": round(jaccard_distance, 9),
        "call_count": round(_ratio_distance(s1["call_count"], s2["call_count"]), 9),
        "n_functions": round(_ratio_distance(s1["n_functions"], s2["n_functions"]), 9),
        "coverage_size": round(_ratio_distance(s1["coverage_size"], s2["coverage_size"]), 9),
        "combined_shortcut": round(combined, 9),
        "v5_full": float(v5_full),
    }


PREDICTORS = (
    "sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state",
    "exception_fraction", "exception_component_v3", "exception_type_jaccard",
    "call_count", "n_functions", "coverage_size", "combined_shortcut",
    # Structural baselines, merged in afterwards by
    # experiments/final/static_baselines.py. They need no execution, so they are
    # computed from the same pair list rather than the same traces.
    "static_token", "static_ast",
)
