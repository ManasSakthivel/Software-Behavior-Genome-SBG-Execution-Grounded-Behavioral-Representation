"""
sbg.extraction.dynamic.interaction_genome
==========================================
Dynamic extraction of the INTERACTION genome dimension g_X.

Formal grounding
----------------
* InteractionGenome  ↔  g_X           (Definition 15, FORMAL_MODEL.md)
* InteractionGenomeExtractor  ↔  Φ_X  (Definition 7)
* distance           ↔  d_X           (Definition 17, row X)
* canonicalize       ↔  𝒩_dist / 𝒞_ε (Definition 22b)

Definition 15 specifies:
    g_X = ⟨SSD̄, ĪPC, F̄SAP, S̄H, ŌBD⟩

At the Python runtime level we approximate these using:
    • output_value_types       — type names of return values across traces
    • output_value_histogram   — distribution over value-shape categories
    • function_call_patterns   — top-10 most common ordered call sequences
    • io_pattern_signature     — stable hash of output_value_histogram
    • n_distinct_outputs       — count of distinct return value type names seen

Distance (Definition 17, row X):
    JSD on output_value_histogram  + Jaccard on function_call_patterns
    Weighted 50 / 50, result in [0, 1].

Constraints
-----------
* No third-party imports (stdlib only).
* All values in output_value_histogram are non-negative integers.
* io_pattern_signature is a SHA-256 hex prefix (16 chars).
* distance is a pseudometric: d(g,g)=0, symmetric, triangle inequality.
* canonicalize is idempotent.
"""

from __future__ import annotations

import hashlib
import math
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Value-shape classifier
# ---------------------------------------------------------------------------

# Category labels used in output_value_histogram.
_HIST_KEYS = (
    "None",
    "True",
    "False",
    "zero",
    "positive_int",
    "negative_int",
    "empty_str",
    "nonempty_str",
    "list",
    "dict",
    "exception",
)


def _classify_value(value: Any, exception_str: Optional[str]) -> str:
    """
    Map a return value (or exception) to one of the histogram category labels.

    Priority: if exception_str is set, classify as "exception" regardless of
    value (return_value is typically None when an exception occurred).
    """
    if exception_str is not None:
        return "exception"
    if value is None:
        return "None"
    if value is True:
        return "True"
    if value is False:
        return "False"
    if isinstance(value, int):
        if value == 0:
            return "zero"
        return "positive_int" if value > 0 else "negative_int"
    if isinstance(value, float):
        if value == 0.0:
            return "zero"
        return "positive_int" if value > 0 else "negative_int"
    if isinstance(value, str):
        return "empty_str" if value == "" else "nonempty_str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    # Fallback: use the type name as the category
    return type(value).__name__


# ---------------------------------------------------------------------------
# InteractionGenome dataclass
# ---------------------------------------------------------------------------

@dataclass
class InteractionGenome:
    """
    Aggregated INTERACTION-dimension genome — g_X per Definition 15.

    Fields
    ------
    output_value_types : Dict[str, int]
        Counts of each distinct *type name* (e.g. "int", "str", "NoneType")
        of return values observed across all traces.

    output_value_histogram : Dict[str, int]
        Counts of value-shape categories across all traces.
        Categories: None, True, False, zero, positive_int, negative_int,
        empty_str, nonempty_str, list, dict, exception.
        Zero-count keys are omitted in the canonical form.

    function_call_patterns : List[str]
        Top-10 most common ordered call sequences observed across traces,
        each encoded as a single pipe-delimited string of function names.
        E.g. ["main|helper|compute", "main|helper"].

    io_pattern_signature : str
        SHA-256 (first 16 hex chars) of the canonicalized
        output_value_histogram.  Stable identifier for the I/O profile.

    n_distinct_outputs : int
        Number of distinct *type names* seen in return values across traces.

    provenance : Dict
        Metadata: program_id, n_traces, extraction_timestamp, etc.
    """

    output_value_types: Dict[str, int]
    output_value_histogram: Dict[str, int]
    function_call_patterns: List[str]
    io_pattern_signature: str
    n_distinct_outputs: int
    provenance: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# _io_pattern_signature helper
# ---------------------------------------------------------------------------

def _io_pattern_signature(histogram: Dict[str, int]) -> str:
    """
    Compute a stable SHA-256 prefix for *histogram*.

    The histogram is serialised as sorted ``key:value`` pairs joined by ``|``
    (only non-zero counts, keys sorted lexicographically).
    """
    parts = sorted(
        f"{k}:{v}" for k, v in histogram.items() if v > 0
    )
    payload = "|".join(parts)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# _extract_call_sequence — extract ordered call sequence from a trace
# ---------------------------------------------------------------------------

def _extract_call_sequence(events: list) -> str:
    """
    Return the ordered sequence of function names for ``call`` events in
    *events* as a pipe-delimited string.

    This represents the SSD / IPC interaction pattern at the Python-call level.
    """
    names = [e.function_name for e in events if e.event_type == "call"]
    return "|".join(names)


# ---------------------------------------------------------------------------
# InteractionGenomeExtractor
# ---------------------------------------------------------------------------

class InteractionGenomeExtractor:
    """
    Implements Φ_X: List[ExecutionTrace] → InteractionGenome.

    Aggregation follows Definition 21:
    - output_value_types: summed counts across traces.
    - output_value_histogram: summed counts across traces.
    - function_call_patterns: top-10 most frequent call sequences.
    """

    def extract(self, traces: list) -> InteractionGenome:
        """
        Extract an InteractionGenome from *traces*.

        Parameters
        ----------
        traces : List[ExecutionTrace]
            Traces produced by :class:`~sbg.extraction.dynamic.tracer.Tracer`.

        Returns
        -------
        InteractionGenome
        """
        if not traces:
            empty_hist: Dict[str, int] = {}
            return InteractionGenome(
                output_value_types={},
                output_value_histogram=empty_hist,
                function_call_patterns=[],
                io_pattern_signature=_io_pattern_signature(empty_hist),
                n_distinct_outputs=0,
                provenance={"n_traces": 0},
            )

        # --- output value type counts ----------------------------------------
        type_counts: Dict[str, int] = {}
        for t in traces:
            type_name = type(t.return_value).__name__
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        # --- output value histogram -------------------------------------------
        histogram: Dict[str, int] = {}
        for t in traces:
            category = _classify_value(t.return_value, t.exception)
            histogram[category] = histogram.get(category, 0) + 1

        # --- function call patterns: top-10 most common sequences -------------
        sequence_counter: Counter = Counter()
        for t in traces:
            seq = _extract_call_sequence(t.events)
            if seq:  # skip empty sequences (traces with no call events)
                sequence_counter[seq] += 1

        # Top-10 by frequency, then lexicographically for stability
        top10 = [
            seq
            for seq, _ in sorted(
                sequence_counter.items(), key=lambda kv: (-kv[1], kv[0])
            )[:10]
        ]

        # --- n_distinct_outputs ----------------------------------------------
        n_distinct = len(type_counts)

        # --- provenance -------------------------------------------------------
        program_ids = list({t.program_id for t in traces})
        provenance: Dict[str, Any] = {
            "program_ids": program_ids,
            "n_traces": len(traces),
            "extraction_timestamp": time.time(),
        }

        return InteractionGenome(
            output_value_types=type_counts,
            output_value_histogram=histogram,
            function_call_patterns=top10,
            io_pattern_signature=_io_pattern_signature(histogram),
            n_distinct_outputs=n_distinct,
            provenance=provenance,
        )


# ---------------------------------------------------------------------------
# distance  (Definition 17, row X)
# ---------------------------------------------------------------------------

def _jsd(p: Dict[str, int], q: Dict[str, int]) -> float:
    """
    Jensen-Shannon divergence between two histograms, normalised to [0, 1].

    Both histograms are converted to probability distributions before computing
    JSD.  JSD is bounded in [0, ln 2]; we normalise by ln 2 to get [0, 1].

    Returns 0.0 when both histograms are empty (identical).
    """
    all_keys = set(p) | set(q)
    if not all_keys:
        return 0.0

    total_p = sum(p.values()) or 1
    total_q = sum(q.values()) or 1

    prob_p = {k: p.get(k, 0) / total_p for k in all_keys}
    prob_q = {k: q.get(k, 0) / total_q for k in all_keys}

    # Mixture distribution M = (P + Q) / 2
    m = {k: (prob_p[k] + prob_q[k]) / 2.0 for k in all_keys}

    def _kl(dist_a: Dict[str, float], dist_m: Dict[str, float]) -> float:
        """KL(A || M) — returns 0 for zero-probability a entries."""
        acc = 0.0
        for k in all_keys:
            a = dist_a[k]
            mi = dist_m[k]
            if a > 0.0 and mi > 0.0:
                acc += a * math.log(a / mi)
        return acc

    jsd_value = 0.5 * _kl(prob_p, m) + 0.5 * _kl(prob_q, m)
    # Normalise: JSD ∈ [0, ln 2] → divide by ln 2
    ln2 = math.log(2.0)
    return min(1.0, jsd_value / ln2) if ln2 > 0 else 0.0


def _jaccard_patterns(a: List[str], b: List[str]) -> float:
    """
    Jaccard similarity of function_call_patterns as sets.

    Returns 1.0 when both lists are empty (identical empty pattern sets),
    0.0 when the sets are disjoint.
    """
    sa = set(a)
    sb = set(b)
    union_size = len(sa | sb)
    if union_size == 0:
        return 1.0
    return len(sa & sb) / union_size


def distance(g1: InteractionGenome, g2: InteractionGenome) -> float:
    """
    Pseudometric on InteractionGenome in [0, 1].

    Formula (Definition 17, row X):
        d = 0.5 * JSD(output_value_histogram)
          + 0.5 * (1 - Jaccard(function_call_patterns))

    Both components are in [0, 1], so the weighted sum is in [0, 1].

    Properties:
        • distance(g, g) == 0
        • distance(g1, g2) == distance(g2, g1)   (symmetric)
        • distance ∈ [0, 1]
    """
    jsd_part = _jsd(g1.output_value_histogram, g2.output_value_histogram)
    jacc_part = 1.0 - _jaccard_patterns(
        g1.function_call_patterns, g2.function_call_patterns
    )
    return 0.5 * jsd_part + 0.5 * jacc_part


# ---------------------------------------------------------------------------
# canonicalize  (Definition 22b / 22d)
# ---------------------------------------------------------------------------

def canonicalize(g: InteractionGenome) -> InteractionGenome:
    """
    Return a canonical form of *g*.

    Operations
    ----------
    * ``output_value_types``: drop zero/negative entries; sort keys.
    * ``output_value_histogram``: drop zero/negative entries; sort keys;
      ensure all standard category keys that are present have int values.
    * ``function_call_patterns``: deduplicate while preserving order;
      cap at 10 entries.
    * ``io_pattern_signature``: recompute from cleaned histogram.
    * ``n_distinct_outputs``: recompute from cleaned output_value_types.
    * ``provenance``: gains a ``canonicalized: True`` marker.

    This function is idempotent:
        canonicalize(canonicalize(g)) == canonicalize(g)
    """
    # Clean output_value_types: drop non-positive, sort keys
    clean_types = {
        k: int(v)
        for k, v in sorted(g.output_value_types.items())
        if v > 0
    }

    # Clean output_value_histogram: drop non-positive, sort keys
    clean_hist = {
        k: int(v)
        for k, v in sorted(g.output_value_histogram.items())
        if v > 0
    }

    # Deduplicate function_call_patterns preserving order, cap at 10
    seen: dict = {}
    for seq in g.function_call_patterns:
        seen[seq] = None
    clean_patterns = list(seen.keys())[:10]

    # Recompute signature from cleaned histogram
    clean_sig = _io_pattern_signature(clean_hist)

    # Recompute n_distinct_outputs
    clean_n = len(clean_types)

    # Propagate provenance with canonicalization marker
    prov = dict(g.provenance)
    prov["canonicalized"] = True

    return InteractionGenome(
        output_value_types=clean_types,
        output_value_histogram=clean_hist,
        function_call_patterns=clean_patterns,
        io_pattern_signature=clean_sig,
        n_distinct_outputs=clean_n,
        provenance=prov,
    )
