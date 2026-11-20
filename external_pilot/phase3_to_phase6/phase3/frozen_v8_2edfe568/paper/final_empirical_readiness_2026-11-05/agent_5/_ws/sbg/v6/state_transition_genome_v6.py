"""
sbg.v6.state_transition_genome_v6   --  EXPERIMENTAL (SBG V6-graded)
====================================================================
Versioned COPY of sbg.v5.state_transition_genome (which is frozen and untouched).  The ONLY change is `_repr_to_abstract`:
the value abstraction is made graded (exact small integers, rounded floats, exact short string / collection sizes) instead of
sign / {empty, singleton, multi}.  Extraction, event classification, the transition key and `distance` are byte-for-byte V5.
Motivation, predictions and evaluation plan: artifacts/paper_evidence/SBG_V6_EXPERIMENTAL_RATIONALE.md  (written BEFORE any V6 score).

Original V5 docstring follows.
------------------------------
State-Transition Genome (g_T) for SBG v5.

Formal grounding
----------------
* StateTransitionGraph  ↔  g_T              (v5 extension, see docs/v5/STATE_TRANSITION_DESIGN.md)
* extract               ↔  Φ_T              (trace list → transition graph)
* distance              ↔  d_T              (frequency-weighted Jaccard on transition sets)
* canonicalize          ↔  𝒩_T             (sort, deduplicate, normalise frequencies)

Design principles
-----------------
1. Abstract value domains make the representation variable-name-invariant (SP-1)
   and value-representation-invariant.
2. Transition labels use anonymous function indices (first-call order), not
   function names — rename-invariant (SP-2).
3. Transition tuples (func_idx, pre_state, event_kind, post_state) uniquely
   identify a behavioural step in abstract state space.
4. Six event categories are tracked: creation, mutation, deletion,
   resource_acquire/release, error_transition, and data_flow.
5. Sequence normalisation: sort by (func_idx, pre_state, event_kind, post_state).
6. Distance: frequency-weighted symmetric Jaccard in [0, 1].

Constraints
-----------
* stdlib only — no third-party imports.
* SAFEGUARD-2: output values are never read; only repr strings from local
  variable snapshots (which the tracer already caps at 100 chars).
"""

from __future__ import annotations

import math
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from sbg.extraction.dynamic.tracer import ExecutionTrace, TraceEvent

# ---------------------------------------------------------------------------
# Abstract Value Domain
# ---------------------------------------------------------------------------

# Numeric / scalar abstract values
AV_ZERO        = "ZERO"
AV_POSITIVE    = "POSITIVE"
AV_NEGATIVE    = "NEGATIVE"
AV_NULL        = "NULL"
AV_NON_NULL    = "NON_NULL"

# Collection abstract values
AV_EMPTY_COL   = "EMPTY_COLLECTION"
AV_SINGLETON   = "SINGLETON"
AV_MULTI       = "MULTI_ELEMENT"

# Control-flow abstract values
AV_EXCEPTION   = "EXCEPTION_STATE"
AV_NORMAL      = "NORMAL"

# Sentinel for "variable not present in snapshot"
AV_ABSENT      = "ABSENT"

# Sentinel for "not abstractable from repr"
AV_UNKNOWN     = "UNKNOWN"

# ---------------------------------------------------------------------------
# Event kind constants
# ---------------------------------------------------------------------------

EK_CREATE   = "state_creation"
EK_MUTATE   = "state_mutation"
EK_DELETE   = "state_deletion"
EK_ACQUIRE  = "resource_acquire"
EK_RELEASE  = "resource_release"
EK_ERROR    = "error_transition"
EK_RECOVER  = "error_recovery"
EK_DATAFLOW = "data_flow"

# ---------------------------------------------------------------------------
# _repr_to_abstract: repr string → abstract value label
# ---------------------------------------------------------------------------

_RE_INT    = re.compile(r"^-?\d+$")
_RE_FLOAT  = re.compile(r"^-?\d+\.\d")
_RE_STR    = re.compile(r"^'.*'$|^\".*\"$")
_RE_BYTES  = re.compile(r"^b'")


_INT_EXACT_MAX = 16      # |v| <= 16 kept exactly; larger integers -> sign + decimal digit count
_SIZE_EXACT_MAX = 8      # string / collection sizes kept exactly up to 8; larger -> "9+"
_RE_NUM = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")


def _top_level_count(inner: str) -> int:
    inner = inner.rstrip()
    if inner.endswith(","):                  # one-tuple "(1,)": the trailing comma separates nothing
        inner = inner[:-1]
    depth = commas = 0
    quote = None
    for ch in inner:
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in "'\"":
            quote = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            commas += 1
    return commas + 1


def _size_label(n: int) -> str:
    return str(n) if n <= _SIZE_EXACT_MAX else f"{_SIZE_EXACT_MAX + 1}+"


def _repr_to_abstract(r: str) -> str:
    """V6-graded abstraction of a repr string.  Name-free and value-only (rename-invariant); deterministic; no output values are read.

    None -> NULL;  bool -> POSITIVE/ZERO (as V5);  int -> ZERO | POS=<v> | NEG=<v> (|v|<=16) | POS_D<digits> | NEG_D<digits>;
    float -> ZERO | POSF=<round(v,2)> | NEGF=<round(v,2)> (0.01<=|v|<1e6) | POSF_E<exp> | NEGF_E<exp> (decimal exponent otherwise); inf/nan -> UNKNOWN;
    str -> EMPTY_COLLECTION | STR_LEN=<n|9+>;  list/tuple/dict/set -> EMPTY_COLLECTION | COL_LEN=<n|9+>;
    object reprs -> NON_NULL (never value-sensitive: they embed memory addresses).
    A repr cut at the tracer's 100-character cap cannot be sized reliably -> COL_LEN=9+ / STR_LEN=9+.
    """
    r = r.strip()
    if r == "None":
        return AV_NULL
    if r == "True":
        return AV_POSITIVE
    if r == "False":
        return AV_ZERO
    if _RE_INT.match(r):
        v = int(r)
        if v == 0:
            return AV_ZERO
        if abs(v) <= _INT_EXACT_MAX:
            return f"{'POS' if v > 0 else 'NEG'}={abs(v)}"
        return f"{'POS' if v > 0 else 'NEG'}_D{len(str(abs(v)))}"
    if _RE_NUM.match(r):
        try:
            v = float(r)
        except ValueError:
            return AV_UNKNOWN
        if v != v or v in (float("inf"), float("-inf")):
            return AV_UNKNOWN
        if v == 0.0:
            return AV_ZERO
        sgn = "POSF" if v > 0 else "NEGF"
        if 1e-2 <= abs(v) < 1e6:
            return f"{sgn}={abs(round(v, 2))}"
        return f"{sgn}_E{int(math.floor(math.log10(abs(v))))}"
    if r in ("''", '""'):
        return AV_EMPTY_COL
    if _RE_STR.match(r):
        return f"STR_LEN={_size_label(max(0, len(r) - 2))}"
    if _RE_BYTES.match(r):
        return AV_NON_NULL if len(r) > 3 else AV_EMPTY_COL
    if r[:1] in "[({":
        inner = r[1:-1].strip()
        if not inner:
            return AV_EMPTY_COL
        if len(r) >= 100:                    # truncated by the tracer's repr cap: size unknowable
            return f"COL_LEN={_SIZE_EXACT_MAX + 1}+"
        return f"COL_LEN={_size_label(_top_level_count(inner))}"
    if r.startswith("<") or re.match(r"^[A-Za-z_][A-Za-z0-9_.]*\(", r):
        return AV_NON_NULL
    return AV_UNKNOWN


# ---------------------------------------------------------------------------
# Transition key type
# ---------------------------------------------------------------------------

# (func_idx: int, var_abstract_pre: str, event_kind: str, var_abstract_post: str)
TransitionKey = Tuple[int, str, str, str]


# ---------------------------------------------------------------------------
# StateTransitionGraph — the g_T genome
# ---------------------------------------------------------------------------

@dataclass
class StateTransitionGraph:
    """
    State-Transition Genome g_T.

    Fields
    ------
    transitions : Dict[TransitionKey, int]
        Observed (func_idx, pre_state, event_kind, post_state) → frequency count.

    func_index_map : Dict[int, str]
        Reverse map from anonymous function index to original function name.
        Preserved for diagnostics only; distance computation ignores names.

    n_traces : int
        Number of execution traces used for extraction.

    event_kind_totals : Dict[str, int]
        Aggregate count per event kind (creation / mutation / deletion /
        resource_acquire / resource_release / error_transition /
        error_recovery / data_flow).

    has_error_states : bool
        True if any EXCEPTION_STATE appeared in a pre or post state.

    provenance : Dict
    """

    transitions: Dict[Tuple[int, str, str, str], int] = field(default_factory=dict)
    func_index_map: Dict[int, str] = field(default_factory=dict)
    n_traces: int = 0
    event_kind_totals: Dict[str, int] = field(default_factory=dict)
    has_error_states: bool = False
    provenance: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# StateTransitionGenome — extractor / distance / canonicalize
# ---------------------------------------------------------------------------

class StateTransitionGenome:
    """
    Φ_T: List[ExecutionTrace] → StateTransitionGraph

    Encapsulates extraction, distance, and canonicalization for g_T.

    Extraction strategy
    -------------------
    For each consecutive event-pair (e_i, e_{i+1}) within a trace:

    1. Map each variable's repr to an abstract value label.
    2. Classify the kind of transition:
       - New variable appeared           → state_creation
       - Variable disappeared            → state_deletion
       - Variable changed abstract value → state_mutation
       - Entry to exception event_type   → error_transition
       - Return from exception context   → error_recovery
       - Any EXCEPTION_STATE in snapshot → error_transition
       - File/lock acquire/release heuristic (variable name patterns) → resource_*
       - Output variable of prior step appears as input of next → data_flow
    3. Build transition key (func_idx, pre_abstract, event_kind, post_abstract)
       and increment its frequency counter.

    Anonymous function indexing (SP-2 invariance)
    -----------------------------------------------
    Functions are assigned integer indices in first-call order across the
    entire trace list, exactly as in v2 TraceNormalizer.

    Notes
    -----
    * Each variable in a snapshot pair contributes one transition independently.
      This gives O(V × E) transitions per trace, where V = variable count,
      E = event count — tractable because the tracer caps both.
    * Only abstract value changes generate transitions; stable variables are
      not counted to keep the representation compact.
    """

    # Heuristic patterns for resource variable names
    _RESOURCE_PATTERNS = re.compile(
        r"(^f$|^file|^fp$|^fd|^fh$|^lock|^mutex|^conn|^socket|^handle|^resource)",
        re.IGNORECASE,
    )

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def extract(self, traces: List[ExecutionTrace]) -> StateTransitionGraph:
        """
        Φ_T: List[ExecutionTrace] → StateTransitionGraph

        Returns an empty graph for an empty trace list.
        """
        if not traces:
            return StateTransitionGraph(
                provenance={"n_traces": 0, "program_ids": []},
            )

        # Build anonymous function index (first-call order across all traces)
        name_to_idx: Dict[str, int] = {}
        for trace in traces:
            for ev in trace.events:
                if ev.event_type == "call" and ev.function_name not in name_to_idx:
                    name_to_idx[ev.function_name] = len(name_to_idx)
        # Unknown/unnamed functions default to index -1 internally (then mapped to 0)
        idx_to_name = {v: k for k, v in name_to_idx.items()}

        transition_counts: Counter = Counter()
        event_kind_totals: Counter = Counter()
        has_error = False

        for trace in traces:
            events = trace.events
            n = len(events)
            if n < 2:
                continue

            for i in range(n - 1):
                ev_pre  = events[i]
                ev_post = events[i + 1]

                func_idx = name_to_idx.get(ev_pre.function_name, 0)

                snap_pre  = ev_pre.local_vars_snapshot
                snap_post = ev_post.local_vars_snapshot

                # Abstract pre/post snapshots
                abs_pre  = {v: _repr_to_abstract(r) for v, r in snap_pre.items()}
                abs_post = {v: _repr_to_abstract(r) for v, r in snap_post.items()}

                # ── error state detection ─────────────────────────────────
                pre_is_exc  = ev_pre.event_type == "exception"
                post_is_exc = ev_post.event_type == "exception"

                # ── data-flow: output of ev_pre appears in ev_post ---------
                # Proxy: variables added to snapshot between steps
                added_vars   = set(abs_post) - set(abs_pre)
                removed_vars = set(abs_pre)  - set(abs_post)
                common_vars  = set(abs_pre)  & set(abs_post)

                # state_creation transitions
                for var in added_vars:
                    pre_av  = AV_ABSENT
                    post_av = abs_post[var]
                    if post_av in (AV_EXCEPTION, AV_NULL) or post_is_exc:
                        ek = EK_ERROR
                        has_error = True
                    elif self._RESOURCE_PATTERNS.match(var):
                        ek = EK_ACQUIRE
                    else:
                        ek = EK_CREATE
                    key: TransitionKey = (func_idx, pre_av, ek, post_av)
                    transition_counts[key] += 1
                    event_kind_totals[ek] += 1

                # state_deletion transitions
                for var in removed_vars:
                    pre_av  = abs_pre[var]
                    post_av = AV_ABSENT
                    if self._RESOURCE_PATTERNS.match(var):
                        ek = EK_RELEASE
                    elif pre_is_exc:
                        ek = EK_RECOVER
                        has_error = True
                    else:
                        ek = EK_DELETE
                    key = (func_idx, pre_av, ek, post_av)
                    transition_counts[key] += 1
                    event_kind_totals[ek] += 1

                # mutation / error / data-flow transitions for common vars
                for var in common_vars:
                    pre_av  = abs_pre[var]
                    post_av = abs_post[var]

                    if pre_av == post_av:
                        # No abstract change — no transition recorded (compact repr)
                        continue

                    # Classify event kind
                    if pre_is_exc and not post_is_exc:
                        ek = EK_RECOVER
                        has_error = True
                    elif post_is_exc or post_av == AV_EXCEPTION:
                        ek = EK_ERROR
                        has_error = True
                    elif pre_av in (AV_EXCEPTION,):
                        ek = EK_RECOVER
                        has_error = True
                    elif self._RESOURCE_PATTERNS.match(var):
                        # Resource var changed: treat as acquire if going from
                        # NULL→NON_NULL, release if NON_NULL→NULL
                        if pre_av in (AV_NULL, AV_ABSENT) and post_av not in (AV_NULL, AV_ABSENT):
                            ek = EK_ACQUIRE
                        elif pre_av not in (AV_NULL, AV_ABSENT) and post_av in (AV_NULL, AV_ABSENT):
                            ek = EK_RELEASE
                        else:
                            ek = EK_MUTATE
                    elif pre_av in (AV_ABSENT,) and post_av not in (AV_ABSENT,):
                        # Newly non-absent (data flow from producer to consumer step)
                        ek = EK_DATAFLOW
                    else:
                        ek = EK_MUTATE

                    key = (func_idx, pre_av, ek, post_av)
                    transition_counts[key] += 1
                    event_kind_totals[ek] += 1

                # ── error_state_transitions: exception event type crossing ─
                if pre_is_exc and not post_is_exc:
                    # Recovery: EXCEPTION_STATE → NORMAL (once per event pair, not per var)
                    key = (func_idx, AV_EXCEPTION, EK_RECOVER, AV_NORMAL)
                    transition_counts[key] += 1
                    event_kind_totals[EK_RECOVER] += 1
                    has_error = True
                elif not pre_is_exc and post_is_exc:
                    key = (func_idx, AV_NORMAL, EK_ERROR, AV_EXCEPTION)
                    transition_counts[key] += 1
                    event_kind_totals[EK_ERROR] += 1
                    has_error = True

        program_ids = list({t.program_id for t in traces})

        return StateTransitionGraph(
            transitions=dict(transition_counts),
            func_index_map=idx_to_name,
            n_traces=len(traces),
            event_kind_totals=dict(event_kind_totals),
            has_error_states=has_error,
            provenance={
                "program_ids": program_ids,
                "n_traces": len(traces),
                "n_unique_functions": len(name_to_idx),
                "extraction_timestamp": time.time(),
            },
        )

    # ------------------------------------------------------------------ #

    def distance(self, g1: StateTransitionGraph, g2: StateTransitionGraph) -> float:
        """
        Frequency-weighted Jaccard distance in [0, 1] between two transition graphs.

        Formula
        -------
        Let T = T1 ∪ T2 (union of all transition keys).

        For each key k ∈ T:
            w(k) = max(freq1(k), freq2(k))   — weight of the transition

        Similarity:
            S = Σ_{k ∈ T1 ∩ T2} min(freq1(k), freq2(k))
                / Σ_{k ∈ T} max(freq1(k), freq2(k))

        Distance:
            d = 1 − S    ∈ [0, 1]

        Properties
        ----------
        * d(g, g) = 0.0
        * d(g1, g2) = d(g2, g1)   (symmetric, since min and max are symmetric)
        * result ∈ [0, 1]
        """
        t1 = g1.transitions
        t2 = g2.transitions

        all_keys: Set[TransitionKey] = set(t1) | set(t2)
        if not all_keys:
            return 0.0

        numerator   = 0.0
        denominator = 0.0

        for k in all_keys:
            f1 = t1.get(k, 0)
            f2 = t2.get(k, 0)
            numerator   += min(f1, f2)
            denominator += max(f1, f2)

        if denominator == 0.0:
            return 0.0

        return max(0.0, min(1.0, 1.0 - numerator / denominator))

    # ------------------------------------------------------------------ #

    def canonicalize(self, graph: StateTransitionGraph) -> StateTransitionGraph:
        """
        Return a canonical form of *graph* (idempotent).

        Normalisation steps
        -------------------
        1. Drop transitions with frequency ≤ 0.
        2. Sort transition keys: (func_idx ASC, pre_state LEX, event_kind LEX,
           post_state LEX) — Definition 22 sequence normalisation.
        3. Normalise frequencies to fractions of the total (so graphs extracted
           from traces of different lengths are comparable).  Stored as floats
           rounded to 6 dp.  If total is 0 nothing is changed.
        4. Rebuild event_kind_totals from the cleaned transitions.
        5. Recompute has_error_states from cleaned transition keys.
        6. Add canonicalized marker to provenance.

        Note: func_index_map is kept as-is (diagnostic only).
        """
        # 1. Drop zero/negative
        clean = {k: v for k, v in graph.transitions.items() if v > 0}

        # 2. Sort
        sorted_transitions: Dict[Tuple[int, str, str, str], Any] = dict(
            sorted(clean.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2], kv[0][3]))
        )

        # 3. Normalise to frequency fractions
        total = sum(sorted_transitions.values()) or 1
        norm_transitions: Dict[Tuple[int, str, str, str], float] = {
            k: round(v / total, 6) for k, v in sorted_transitions.items()
        }

        # 4. Rebuild event_kind_totals from sorted_transitions (pre-normalisation counts)
        ek_totals: Counter = Counter()
        for (_, _, ek, _), v in sorted_transitions.items():
            ek_totals[ek] += v

        # 5. Recompute has_error_states
        has_error = any(
            k[1] == AV_EXCEPTION or k[3] == AV_EXCEPTION or k[2] in (EK_ERROR, EK_RECOVER)
            for k in norm_transitions
        )

        prov = dict(graph.provenance)
        prov["canonicalized"] = True

        return StateTransitionGraph(
            transitions=norm_transitions,  # type: ignore[arg-type]
            func_index_map=dict(graph.func_index_map),
            n_traces=max(0, graph.n_traces),
            event_kind_totals=dict(ek_totals),
            has_error_states=has_error,
            provenance=prov,
        )


