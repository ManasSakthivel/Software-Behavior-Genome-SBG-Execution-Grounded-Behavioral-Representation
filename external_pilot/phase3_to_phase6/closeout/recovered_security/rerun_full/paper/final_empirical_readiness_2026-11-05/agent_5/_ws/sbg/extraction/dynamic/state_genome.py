"""
sbg/extraction/dynamic/state_genome.py
========================================
Dynamic extraction of the STATE genome dimension g_S.

Formal grounding
----------------
* StateGenome  <->  g_S             (Definition 11, FORMAL_MODEL.md)
* distance     <->  d_S             (Definition 17, row S)
* canonicalize <->  N_dist          (Definition 22)

Design notes
------------
g_S is extracted from a list of ExecutionTrace objects produced by
sbg.extraction.dynamic.tracer.Tracer.  The trace events carry snapshots of
local variable bindings at every traced step, approximating:

  variable_assignment_counts  - appearances of each variable name across events
  state_space_size            - distinct frozenset(locals.items()) snapshots
  mutation_rate               - fraction of consecutive-event pairs with change
  heap_object_types           - type-name histogram inferred from repr strings
  stack_depth_profile         - call-depth histogram
  state_transition_count      - total variable-value changes across all pairs

Distance formula:
  Normalised L2 on stack_depth_profile + |mutation_rate diff| + Jaccard on heap keys

Uses only Python stdlib.
"""

from __future__ import annotations

import math
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple

from sbg.extraction.dynamic.tracer import ExecutionTrace, TraceEvent


@dataclass
class StateGenome:
    """
    Dynamic approximation of the STATE genome dimension g_S (Definition 11).

    Fields
    ------
    variable_assignment_counts : Dict[str, int]
        How many times each variable name was observed in local-variable
        snapshots across all traces and events.

    state_space_size : int
        Number of distinct variable-binding snapshots seen.

    mutation_rate : float
        Fraction of consecutive-event pairs within a trace where any variable
        changed value.  Averaged across traces.  In [0, 1].

    heap_object_types : Dict[str, int]
        Histogram of inferred type names of objects in local snapshots.

    stack_depth_profile : Dict[int, int]
        Histogram mapping call-stack depth to observation count.

    state_transition_count : int
        Total number of variable-value changes across all consecutive-event pairs.

    provenance : Dict
        program_ids, n_traces, extraction_timestamp.
    """

    variable_assignment_counts: Dict[str, int] = field(default_factory=dict)
    state_space_size: int = 0
    mutation_rate: float = 0.0
    heap_object_types: Dict[str, int] = field(default_factory=dict)
    stack_depth_profile: Dict[int, int] = field(default_factory=dict)
    state_transition_count: int = 0
    provenance: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Type inference from repr strings
# ---------------------------------------------------------------------------

_TYPE_PATTERNS = [
    ("int",     re.compile(r"^-?\d+$")),
    ("float",   re.compile(r"^-?\d+\.\d")),
    ("bool",    re.compile(r"^(True|False)$")),
    ("NoneType", re.compile(r"^None$")),
    ("str",     re.compile(r"^'.*'$|^\".*\"$")),
    ("list",    re.compile(r"^\[")),
    ("dict",    re.compile(r"^\{")),
    ("set",     re.compile(r"^set\(\)|^\{[^:]+\}$")),
    ("tuple",   re.compile(r"^\(")),
    ("bytes",   re.compile(r"^b'")),
]

_CLASS_PAREN = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*)\(")
_CLASS_ANGLE = re.compile(r"^<([A-Za-z_][A-Za-z0-9_.]+)")


def _infer_type_from_repr(r):
    # type: (str) -> str
    r = r.strip()
    for type_name, pattern in _TYPE_PATTERNS:
        if pattern.match(r):
            return type_name
    m = _CLASS_PAREN.match(r)
    if m:
        return m.group(1)
    m = _CLASS_ANGLE.match(r)
    if m:
        return m.group(1)
    return "unknown"


# ---------------------------------------------------------------------------
# StateGenomeExtractor
# ---------------------------------------------------------------------------

class StateGenomeExtractor:
    """
    Extracts the STATE genome dimension (g_S) from a list of ExecutionTraces.

    Implements Phi_S: List[ExecutionTrace] -> StateGenome (Definition 7 / 11).
    """

    def extract(self, traces):
        # type: (List[ExecutionTrace]) -> StateGenome
        """Aggregate STATE features from traces into a StateGenome."""
        if not traces:
            return StateGenome(provenance={"n_traces": 0, "program_ids": []})

        var_counts = Counter()
        seen_snapshots = set()
        heap_types = Counter()
        depth_counts = Counter()
        total_transitions = 0
        total_mutation_pairs = 0
        total_consecutive_pairs = 0

        for trace in traces:
            events = trace.events
            if not events:
                continue

            depth = 0
            prev_snapshot = {}

            for i, ev in enumerate(events):
                et = ev.event_type

                if et == "call":
                    depth += 1
                elif et == "return":
                    depth = max(0, depth - 1)

                depth_counts[depth] += 1

                snap = ev.local_vars_snapshot

                for var_name, val_repr in snap.items():
                    var_counts[var_name] += 1
                    type_name = _infer_type_from_repr(val_repr)
                    heap_types[type_name] += 1

                frozen = frozenset(snap.items())
                seen_snapshots.add(frozen)

                if i > 0:
                    total_consecutive_pairs += 1
                    changed = 0
                    all_vars = set(prev_snapshot) | set(snap)
                    for var in all_vars:
                        if prev_snapshot.get(var) != snap.get(var):
                            changed += 1
                    if changed > 0:
                        total_mutation_pairs += 1
                        total_transitions += changed

                prev_snapshot = snap

        mutation_rate = (
            total_mutation_pairs / total_consecutive_pairs
            if total_consecutive_pairs > 0 else 0.0
        )

        program_ids = list({t.program_id for t in traces})
        provenance = {
            "program_ids": program_ids,
            "n_traces": len(traces),
            "extraction_timestamp": time.time(),
        }

        return StateGenome(
            variable_assignment_counts=dict(var_counts),
            state_space_size=len(seen_snapshots),
            mutation_rate=mutation_rate,
            heap_object_types=dict(heap_types),
            stack_depth_profile=dict(depth_counts),
            state_transition_count=total_transitions,
            provenance=provenance,
        )


# ---------------------------------------------------------------------------
# distance  (Definition 17, row S)
# ---------------------------------------------------------------------------

def _normalise_counts(d):
    total = sum(d.values())
    if total == 0:
        return {k: 0.0 for k in d}
    return {k: v / total for k, v in d.items()}


def _l2_stack_depth(a, b):
    """Normalised L2 distance between two stack-depth histograms, in [0, 1]."""
    all_keys = set(a) | set(b)
    if not all_keys:
        return 0.0
    pa = _normalise_counts(a)
    pb = _normalise_counts(b)
    l2_sq = sum((pa.get(k, 0.0) - pb.get(k, 0.0)) ** 2 for k in all_keys)
    return math.sqrt(l2_sq) / math.sqrt(2.0)


def _jaccard_distance_keys(a, b):
    """Jaccard distance on key sets of two dicts, in [0, 1]."""
    keys_a = set(a.keys())
    keys_b = set(b.keys())
    union_size = len(keys_a | keys_b)
    if union_size == 0:
        return 0.0
    intersection_size = len(keys_a & keys_b)
    return 1.0 - intersection_size / union_size


def distance(g1, g2):
    # type: (StateGenome, StateGenome) -> float
    """
    Symmetric distance in [0, 1] between two StateGenomes.

    Three components averaged equally (1/3 each):
      1. |mutation_rate1 - mutation_rate2|
      2. Normalised L2 on stack_depth_profile
      3. Jaccard distance on heap_object_types key sets

    Properties: distance(g, g) == 0, symmetric, in [0, 1].
    """
    d_mutation = abs(g1.mutation_rate - g2.mutation_rate)
    d_stack = _l2_stack_depth(g1.stack_depth_profile, g2.stack_depth_profile)
    d_heap = _jaccard_distance_keys(g1.heap_object_types, g2.heap_object_types)
    return (d_mutation + d_stack + d_heap) / 3.0


# ---------------------------------------------------------------------------
# canonicalize  (Definition 22)
# ---------------------------------------------------------------------------

def canonicalize(g):
    # type: (StateGenome) -> StateGenome
    """
    Return a canonical form of g per Definition 22.

    - Dict keys in variable_assignment_counts, heap_object_types, and
      stack_depth_profile are sorted.
    - mutation_rate is rounded to 4 dp and clamped to [0, 1].
    - state_transition_count and state_space_size are clamped to >= 0.
    - Provenance gains a 'canonicalized' marker.

    Idempotent: canonicalize(canonicalize(g)) == canonicalize(g).
    """
    prov = dict(g.provenance)
    prov["canonicalized"] = True

    return StateGenome(
        variable_assignment_counts={
            k: max(0, int(g.variable_assignment_counts[k]))
            for k in sorted(g.variable_assignment_counts)
        },
        state_space_size=max(0, int(g.state_space_size)),
        mutation_rate=round(max(0.0, min(1.0, g.mutation_rate)), 4),
        heap_object_types={
            k: max(0, int(g.heap_object_types[k]))
            for k in sorted(g.heap_object_types)
        },
        stack_depth_profile={
            int(k): max(0, int(g.stack_depth_profile[k]))
            for k in sorted(g.stack_depth_profile, key=int)
        },
        state_transition_count=max(0, int(g.state_transition_count)),
        provenance=prov,
    )
