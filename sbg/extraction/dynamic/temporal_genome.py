"""
sbg.extraction.dynamic.temporal_genome
=========================================
Temporal Genome extraction from execution traces.

Formal grounding
----------------
* TemporalGenome  ↔  g_T              (Definition 13, FORMAL_MODEL.md)
* extract         ↔  Φ_T              (Definition 7)
* distance        ↔  d_T              (Definition 17)
* canonicalize    ↔  𝒩_dist / 𝒞_ε   (Definition 22b)

Constraints
-----------
* No third-party imports.
* All analysis is derived from ExecutionTrace objects produced by Tracer.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from sbg.extraction.dynamic.tracer import ExecutionTrace


# ---------------------------------------------------------------------------
# TemporalGenome  (g_T — Definition 13)
# ---------------------------------------------------------------------------

@dataclass
class TemporalGenome:
    """
    Aggregated TEMPORAL-dimension genome — g_T per Definition 13.

    Fields
    ------
    call_return_latency_profile:
        Maps function_name → mean event count between "call" and matching
        "return" across all traces.  Portable proxy for CLV (Definition 13).
    event_sequence_ngrams:
        Bigrams of (event_type/function_name) pairs accumulated across traces.
        Key: "<et1>/<fn1>→<et2>/<fn2>".  Approximates IEL structurally.
    phase_timing:
        Maps function_name → mean fraction of total events attributable to
        that function across traces.  Corresponds to PT (Definition 13).
    temporal_entropy:
        Shannon entropy (nats) of the aggregated event_type distribution.
    provenance:
        Metadata dictionary.
    """

    call_return_latency_profile: Dict[str, float]
    event_sequence_ngrams: Dict[str, int]
    phase_timing: Dict[str, float]
    temporal_entropy: float
    provenance: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# TemporalGenomeExtractor
# ---------------------------------------------------------------------------

class TemporalGenomeExtractor:
    """
    Implements Φ_T: List[ExecutionTrace] → TemporalGenome.
    """

    def extract(self, traces: List[ExecutionTrace]) -> TemporalGenome:
        if not traces:
            return TemporalGenome(
                call_return_latency_profile={},
                event_sequence_ngrams={},
                phase_timing={},
                temporal_entropy=0.0,
                provenance={"n_traces": 0},
            )

        n = len(traces)

        # --- Call→return latency (event-count units) ----------------------
        latency_sums: Dict[str, float] = {}
        latency_counts: Dict[str, int] = {}
        for trace in traces:
            call_stack: List[tuple] = []
            for idx, ev in enumerate(trace.events):
                if ev.event_type == "call":
                    call_stack.append((ev.function_name, idx))
                elif ev.event_type == "return" and call_stack:
                    fn, call_idx = call_stack[-1]
                    if fn == ev.function_name:
                        call_stack.pop()
                        lat = float(idx - call_idx)
                        latency_sums[fn] = latency_sums.get(fn, 0.0) + lat
                        latency_counts[fn] = latency_counts.get(fn, 0) + 1

        latency_profile = {
            fn: latency_sums[fn] / latency_counts[fn] for fn in latency_sums
        }

        # --- Bigrams ------------------------------------------------------
        ngrams: Dict[str, int] = {}
        for trace in traces:
            evs = trace.events
            for i in range(len(evs) - 1):
                e1, e2 = evs[i], evs[i + 1]
                key = (
                    f"{e1.event_type}/{e1.function_name}"
                    f"→{e2.event_type}/{e2.function_name}"
                )
                ngrams[key] = ngrams.get(key, 0) + 1

        # --- Phase timing -------------------------------------------------
        phase_sums: Dict[str, float] = {}
        phase_n = 0
        for trace in traces:
            total = len(trace.events)
            if total == 0:
                continue
            fn_cnt: Dict[str, int] = {}
            for ev in trace.events:
                fn_cnt[ev.function_name] = fn_cnt.get(ev.function_name, 0) + 1
            for fn, cnt in fn_cnt.items():
                phase_sums[fn] = phase_sums.get(fn, 0.0) + cnt / total
            phase_n += 1
        phase_timing: Dict[str, float] = (
            {fn: s / phase_n for fn, s in phase_sums.items()} if phase_n else {}
        )

        # --- Temporal entropy ----------------------------------------------
        type_counts: Dict[str, int] = {}
        for trace in traces:
            for ev in trace.events:
                type_counts[ev.event_type] = type_counts.get(ev.event_type, 0) + 1
        total_ev = sum(type_counts.values())
        entropy = 0.0
        if total_ev > 0:
            for cnt in type_counts.values():
                p = cnt / total_ev
                if p > 0:
                    entropy -= p * math.log(p)

        program_ids = list({t.program_id for t in traces})
        provenance: Dict[str, Any] = {
            "program_ids": program_ids,
            "n_traces": n,
            "extraction_timestamp": time.time(),
        }

        return TemporalGenome(
            call_return_latency_profile=latency_profile,
            event_sequence_ngrams=ngrams,
            phase_timing=phase_timing,
            temporal_entropy=entropy,
            provenance=provenance,
        )


# ---------------------------------------------------------------------------
# distance  (Definition 17, row T)
# ---------------------------------------------------------------------------

def distance(g1: TemporalGenome, g2: TemporalGenome) -> float:
    """
    Pseudometric on TemporalGenome in [0, 1].

    d = 0.5 * jaccard_distance(ngram_keys)
      + 0.5 * normalised_L1(phase_timing)
    """
    # Jaccard on ngram key sets
    keys1, keys2 = set(g1.event_sequence_ngrams), set(g2.event_sequence_ngrams)
    union_size = len(keys1 | keys2)
    jaccard_dist = 0.0 if union_size == 0 else 1.0 - len(keys1 & keys2) / union_size

    # Normalised L1 on phase_timing
    all_fns = set(g1.phase_timing) | set(g2.phase_timing)
    if not all_fns:
        phase_dist = 0.0
    else:
        l1 = sum(
            abs(g1.phase_timing.get(fn, 0.0) - g2.phase_timing.get(fn, 0.0))
            for fn in all_fns
        )
        phase_dist = min(l1 / 2.0, 1.0)

    return 0.5 * jaccard_dist + 0.5 * phase_dist


# ---------------------------------------------------------------------------
# canonicalize  (Definition 22b)
# ---------------------------------------------------------------------------

def canonicalize(g: TemporalGenome) -> TemporalGenome:
    """
    Return a canonical form of *g* (idempotent).

    * Drop non-positive latency / ngram / phase entries.
    * Clamp temporal_entropy to ≥ 0.
    * provenance gains a ``canonicalized`` marker.
    """
    prov = dict(g.provenance)
    prov["canonicalized"] = True

    return TemporalGenome(
        call_return_latency_profile={
            fn: max(0.0, float(v))
            for fn, v in g.call_return_latency_profile.items()
            if v > 0
        },
        event_sequence_ngrams={k: int(v) for k, v in g.event_sequence_ngrams.items() if v > 0},
        phase_timing={
            fn: max(0.0, min(1.0, float(v)))
            for fn, v in g.phase_timing.items()
            if v > 0
        },
        temporal_entropy=max(0.0, float(g.temporal_entropy)),
        provenance=prov,
    )
