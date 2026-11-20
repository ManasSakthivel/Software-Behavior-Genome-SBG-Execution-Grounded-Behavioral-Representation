"""
sbg.v5.temporal_genome_v5
==========================
Temporal Behavioral Genome (g_τ) for SBG v5.

Formal grounding
----------------
* TemporalGenomeV5  ↔  g_τ              (v5 extension — temporal ordering features)
* extract           ↔  Φ_τ              (event list → temporal genome)
* distance          ↔  d_τ              (weighted multi-family distance in [0,1])
* canonicalize      ↔  𝒩_τ             (sort dicts, round floats, sort lists)

Design principles
-----------------
1. Rename-invariance (SP-2): all dict keys use integer indices (first-call order),
   never raw function names.  Exception type strings are kept as-is — they are
   class names, not function names, and are intrinsically rename-invariant.

2. SAFEGUARD-2: all features are Output-free.  Return values and stdout are
   never read.  Only event_type, function_name, and depth are consumed.

3. Five new feature families extend V3 bigrams:
     F1  call_trigrams          — order-sensitive 3-grams of call sequences
     F2  exception transitions  — (pre_idx, exc_type, post_idx) context tuples
     F3  causal chains          — pairs (i,j) where i precedes j in >50% traces
     F4  phase diversity        — per-phase Shannon diversity (setup/main/teardown)
     F5  loop profiles          — mean contiguous run-length per repeated function

4. Distance: 7-component weighted mean in [0,1]; d(g,g)=0; symmetric.

5. stdlib only — no external dependencies.

References
----------
* sbg/v3/genome.py    — call_transition_bigrams (extended to trigrams here)
* sbg/v2/execution/normalizer.py — anonymization convention (first-call order)
* docs/v5/TEMPORAL_GENOME_DESIGN.md — design rationale
"""

from __future__ import annotations

import hashlib
import math
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass
class TemporalGenomeV5:
    """
    Temporal behavioral genome g_τ.

    All features are Output-free (SAFEGUARD-2).
    All dict keys use anonymous integer indices (rename-invariant, SP-2).
    Exception type strings are kept verbatim (intrinsically rename-invariant).

    Feature families
    ----------------
    F1 call_trigrams              : Dict[str, float]   "(i,j,k)" → normalized frequency
       bigram_entropy             : float              normalized Shannon entropy of bigrams
       trigram_entropy            : float              normalized Shannon entropy of trigrams

    F2 exception_transition_triples : List[str]       sorted "(pre_idx,exc_type,post_idx)"
       exception_recovery_rate   : float              fraction of exceptions followed by normal call

    F3 causal_precedence_set      : List[str]         sorted "(i,j)" where i precedes j in >50%
       causal_entropy             : float             mean binary entropy of causal ordering probs

    F4 phase_diversity_vector     : List[float]       [setup_div, main_div, teardown_div]

    F5 loop_mean_run_length       : Dict[str, float]  str(anon_idx) → mean contiguous run length
       loop_early_exit_score      : float             coefficient of variation of run lengths

    provenance                    : Dict              metadata (never used in distance)
    """

    program_id: str

    # --- F1: Call N-grams ---
    call_trigrams: Dict[str, float]
    bigram_entropy: float
    trigram_entropy: float

    # --- F2: Exception transitions ---
    exception_transition_triples: List[str]
    exception_recovery_rate: float

    # --- F3: Causal chains ---
    causal_precedence_set: List[str]
    causal_entropy: float

    # --- F4: Phase diversity ---
    phase_diversity_vector: List[float]

    # --- F5: Loop profiles ---
    loop_mean_run_length: Dict[str, float]
    loop_early_exit_score: float

    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "program_id": self.program_id,
            "call_trigrams": dict(sorted(self.call_trigrams.items())),
            "bigram_entropy": self.bigram_entropy,
            "trigram_entropy": self.trigram_entropy,
            "exception_transition_triples": sorted(self.exception_transition_triples),
            "exception_recovery_rate": self.exception_recovery_rate,
            "causal_precedence_set": sorted(self.causal_precedence_set),
            "causal_entropy": self.causal_entropy,
            "phase_diversity_vector": self.phase_diversity_vector,
            "loop_mean_run_length": dict(sorted(self.loop_mean_run_length.items())),
            "loop_early_exit_score": self.loop_early_exit_score,
            "provenance": self.provenance,
            "feature_classification": "OUTPUT_FREE",
            "safeguard_2_compliant": True,
            "version": "v5",
        }


# ---------------------------------------------------------------------------
# Canonicalize
# ---------------------------------------------------------------------------


def canonicalize(g: TemporalGenomeV5) -> TemporalGenomeV5:
    """
    Return canonical form of *g* (idempotent).

    Steps:
    1. Sort all dict keys lexicographically.
    2. Round all floats to 6 decimal places.
    3. Sort all list fields.
    4. Clamp all float fields to [0, 1] where semantically appropriate.
    """
    return TemporalGenomeV5(
        program_id=g.program_id,
        call_trigrams={k: round(v, 6) for k, v in sorted(g.call_trigrams.items())},
        bigram_entropy=round(max(0.0, min(1.0, g.bigram_entropy)), 6),
        trigram_entropy=round(max(0.0, min(1.0, g.trigram_entropy)), 6),
        exception_transition_triples=sorted(g.exception_transition_triples),
        exception_recovery_rate=round(max(0.0, min(1.0, g.exception_recovery_rate)), 6),
        causal_precedence_set=sorted(g.causal_precedence_set),
        causal_entropy=round(max(0.0, min(1.0, g.causal_entropy)), 6),
        phase_diversity_vector=[round(max(0.0, min(1.0, v)), 6) for v in g.phase_diversity_vector],
        loop_mean_run_length={k: round(max(0.0, v), 6) for k, v in sorted(g.loop_mean_run_length.items())},
        loop_early_exit_score=round(max(0.0, g.loop_early_exit_score), 6),
        provenance=dict(g.provenance),
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _shannon_entropy_normalized(counts: List[int]) -> float:
    """
    Normalized Shannon entropy H/log2(n) ∈ [0, 1].

    Returns 0.0 when counts is empty, has a single element, or total is zero.
    """
    total = sum(counts)
    n = len(counts)
    if total == 0 or n <= 1:
        return 0.0
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            entropy -= p * math.log2(p)
    max_h = math.log2(n)
    return round(entropy / max_h, 6) if max_h > 0 else 0.0


def _binary_entropy(p: float) -> float:
    """Binary entropy h(p) = -p*log2(p) - (1-p)*log2(1-p), clamped to [0,1]."""
    p = max(1e-9, min(1.0 - 1e-9, p))
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def _coefficient_of_variation(values: List[float]) -> float:
    """CV = std / mean; returns 0.0 if mean is 0 or fewer than 2 values."""
    if len(values) < 2:
        return 0.0
    n = len(values)
    mean = sum(values) / n
    if mean == 0.0:
        return 0.0
    var = sum((v - mean) ** 2 for v in values) / n
    return round(math.sqrt(var) / mean, 6)


def _phase_diversity(call_seq: List[int]) -> List[float]:
    """
    Split a call sequence into three equal-length phases (setup/main/teardown)
    and compute normalized Shannon diversity within each phase.

    Phase diversity = normalized entropy of function-index frequency within that
    phase.  Returns [setup_div, main_div, teardown_div].
    """
    n = len(call_seq)
    if n == 0:
        return [0.0, 0.0, 0.0]
    third = max(1, n // 3)
    phases = [
        call_seq[:third],
        call_seq[third: 2 * third],
        call_seq[2 * third:],
    ]
    result = []
    for phase in phases:
        cnt = Counter(phase)
        result.append(_shannon_entropy_normalized(list(cnt.values())))
    return result


def _run_lengths(seq: List[int]) -> Dict[int, List[int]]:
    """
    Compute contiguous run lengths per unique value in seq.

    Returns {value: [run_length_1, run_length_2, ...]}
    """
    if not seq:
        return {}
    runs: Dict[int, List[int]] = defaultdict(list)
    current = seq[0]
    length = 1
    for v in seq[1:]:
        if v == current:
            length += 1
        else:
            runs[current].append(length)
            current = v
            length = 1
    runs[current].append(length)
    return dict(runs)


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------


def extract(
    events: List[dict],
    name_to_idx: Optional[Dict[str, int]] = None,
    program_id: str = "unknown",
) -> TemporalGenomeV5:
    """
    Φ_τ: List[dict] → TemporalGenomeV5

    Parameters
    ----------
    events : list of dicts with keys:
        event_type    (str) : "call" | "return" | "exception" | "line"
        function_name (str) : name of the function (will be anonymized)
        depth         (int) : call stack depth at this event
    name_to_idx : optional pre-built anonymization mapping.
        If None, built from first-call order in this event list.
    program_id : str — identifier for provenance.

    Returns
    -------
    TemporalGenomeV5 (canonical form applied before return)
    """
    t0 = time.time()

    if not events:
        return _empty(program_id)

    # ── Build anonymization map (first-call order) ───────────────────────────
    if name_to_idx is None:
        name_to_idx = {}
        for ev in events:
            if ev.get("event_type") == "call":
                fn = ev.get("function_name", "<unknown>")
                if fn not in name_to_idx:
                    name_to_idx[fn] = len(name_to_idx)

    def _idx(fn: str) -> int:
        return name_to_idx.get(fn, -1)

    # ── Extract the call sequence (anonymous indices) ─────────────────────────
    call_seq: List[int] = [
        _idx(ev["function_name"])
        for ev in events
        if ev.get("event_type") == "call" and _idx(ev.get("function_name", "")) >= 0
    ]

    # ── F1: Bigrams and Trigrams ──────────────────────────────────────────────
    bigram_counts: Counter = Counter()
    trigram_counts: Counter = Counter()
    for i in range(len(call_seq) - 1):
        bigram_counts[f"({call_seq[i]},{call_seq[i+1]})"] += 1
    for i in range(len(call_seq) - 2):
        trigram_counts[f"({call_seq[i]},{call_seq[i+1]},{call_seq[i+2]})"] += 1

    total_bigrams = sum(bigram_counts.values()) or 1
    total_trigrams = sum(trigram_counts.values()) or 1
    call_trigrams = {k: round(v / total_trigrams, 6) for k, v in trigram_counts.items()}

    bigram_entropy = _shannon_entropy_normalized(list(bigram_counts.values()))
    trigram_entropy = _shannon_entropy_normalized(list(trigram_counts.values()))

    # ── F2: Exception transitions ─────────────────────────────────────────────
    # Walk events: find (pre_call_idx, exception_type, post_call_idx) triples.
    # Also compute recovery_rate = fraction of exception events followed by a
    # normal call (next event after exception is a "call" not "exception").
    exc_triples: List[str] = []
    n_exceptions = 0
    n_recovered = 0

    # Build parallel list of (event, anon_idx_at_this_point)
    # We track "current call idx" = most recent call event's anon index.
    pre_call_idx: int = -1
    for i, ev in enumerate(events):
        etype = ev.get("event_type", "")
        if etype == "call":
            pre_call_idx = _idx(ev.get("function_name", ""))
        elif etype == "exception":
            n_exceptions += 1
            exc_type = ev.get("function_name", "UnknownException")
            # Look forward for the next call
            post_call_idx: int = -1
            for j in range(i + 1, len(events)):
                nev = events[j]
                if nev.get("event_type") == "call":
                    post_call_idx = _idx(nev.get("function_name", ""))
                    n_recovered += 1
                    break
                elif nev.get("event_type") == "exception":
                    # Another exception before recovery — stop
                    break
            exc_triples.append(f"({pre_call_idx},{exc_type},{post_call_idx})")

    exc_triples = sorted(set(exc_triples))
    exception_recovery_rate = round(n_recovered / n_exceptions, 6) if n_exceptions > 0 else 0.0

    # ── F3: Causal precedence chains ─────────────────────────────────────────
    # "i precedes j" if, within a single trace segment (between returns),
    # index i always appears before index j in the call sequence.
    #
    # Since extract() works on a flat event list (one trace), we compute a
    # single pairwise precedence: for every ordered pair (i,j) of distinct
    # indices, count how many times i appears before j vs j before i in the
    # call subsequence.  If i precedes j in > 50% of co-occurrences → add.
    #
    # For a single-trace extractor this simplifies: we count first-occurrence
    # positions and record (i,j) as causal if pos(i) < pos(j) across the
    # entire call sequence.
    unique_in_seq = list(dict.fromkeys(call_seq))  # preserves first-occurrence order
    first_pos: Dict[int, int] = {}
    for pos, idx in enumerate(call_seq):
        if idx not in first_pos:
            first_pos[idx] = pos

    causal_precedence_set: List[str] = []
    causal_probs: List[float] = []

    for i_val, j_val in combinations(sorted(unique_in_seq), 2):
        pos_i = first_pos.get(i_val, -1)
        pos_j = first_pos.get(j_val, -1)
        if pos_i < 0 or pos_j < 0:
            continue
        # Count all occurrences of i before j and j before i
        n_ij = sum(
            1 for a in range(len(call_seq))
            for b in range(a + 1, len(call_seq))
            if call_seq[a] == i_val and call_seq[b] == j_val
        )
        n_ji = sum(
            1 for a in range(len(call_seq))
            for b in range(a + 1, len(call_seq))
            if call_seq[a] == j_val and call_seq[b] == i_val
        )
        total_pairs = n_ij + n_ji
        if total_pairs == 0:
            continue
        p_ij = n_ij / total_pairs
        causal_probs.append(p_ij)
        if p_ij > 0.5:
            causal_precedence_set.append(f"({i_val},{j_val})")

    causal_precedence_set = sorted(causal_precedence_set)
    causal_entropy = round(
        sum(_binary_entropy(p) for p in causal_probs) / len(causal_probs), 6
    ) if causal_probs else 0.0

    # ── F4: Phase diversity ───────────────────────────────────────────────────
    raw_phase = _phase_diversity(call_seq)
    phase_diversity_vector = [round(v, 6) for v in raw_phase]

    # ── F5: Loop profiles ─────────────────────────────────────────────────────
    # "Loop" = a function called ≥2 times contiguously.
    rl_map = _run_lengths(call_seq)
    loop_mean_run_length: Dict[str, float] = {}
    all_run_lengths: List[float] = []

    for fn_idx, lengths in rl_map.items():
        mean_rl = sum(lengths) / len(lengths)
        loop_mean_run_length[str(fn_idx)] = round(mean_rl, 6)
        all_run_lengths.extend(lengths)

    loop_early_exit_score = _coefficient_of_variation(all_run_lengths)

    # ── Provenance ────────────────────────────────────────────────────────────
    provenance = {
        "program_id": program_id,
        "n_events": len(events),
        "n_call_events": len(call_seq),
        "n_unique_functions": len(name_to_idx),
        "n_exception_events": n_exceptions,
        "feature_classification": "OUTPUT_FREE",
        "safeguard_2_compliant": True,
        "version": "v5",
        "extraction_time_s": round(time.time() - t0, 6),
    }

    return canonicalize(TemporalGenomeV5(
        program_id=program_id,
        call_trigrams=call_trigrams,
        bigram_entropy=bigram_entropy,
        trigram_entropy=trigram_entropy,
        exception_transition_triples=exc_triples,
        exception_recovery_rate=exception_recovery_rate,
        causal_precedence_set=causal_precedence_set,
        causal_entropy=causal_entropy,
        phase_diversity_vector=phase_diversity_vector,
        loop_mean_run_length=loop_mean_run_length,
        loop_early_exit_score=loop_early_exit_score,
        provenance=provenance,
    ))


def _empty(program_id: str) -> TemporalGenomeV5:
    """Return an empty genome for programs with no events."""
    return TemporalGenomeV5(
        program_id=program_id,
        call_trigrams={},
        bigram_entropy=0.0,
        trigram_entropy=0.0,
        exception_transition_triples=[],
        exception_recovery_rate=0.0,
        causal_precedence_set=[],
        causal_entropy=0.0,
        phase_diversity_vector=[0.0, 0.0, 0.0],
        loop_mean_run_length={},
        loop_early_exit_score=0.0,
        provenance={
            "program_id": program_id,
            "n_events": 0,
            "n_call_events": 0,
            "n_unique_functions": 0,
            "n_exception_events": 0,
            "feature_classification": "OUTPUT_FREE",
            "safeguard_2_compliant": True,
            "version": "v5",
        },
    )


# ---------------------------------------------------------------------------
# Distance
# ---------------------------------------------------------------------------


def distance(g1: TemporalGenomeV5, g2: TemporalGenomeV5) -> float:
    """
    d_τ: pseudometric on TemporalGenomeV5 in [0, 1].

    Formula (7-component weighted average)
    ---------------------------------------
    d = W_tri   * d_trigrams            (0.20)  F1: order-sensitive 3-grams
      + W_ent   * d_entropy             (0.10)  F1: bigram+trigram entropy gap
      + W_exc   * d_exc_transitions     (0.10)  F2: exception context Jaccard
      + W_rec   * d_exc_recovery        (0.15)  F2: recovery rate difference
      + W_cau   * d_causal              (0.15)  F3: causal set Jaccard
      + W_pha   * d_phase               (0.10)  F4: phase diversity L1
      + W_lop   * d_loop                (0.20)  F5: loop profile distance

    Weights sum to 1.0.

    Component definitions
    ---------------------
    d_trigrams      : L1(trigrams_1, trigrams_2) / 2          ∈ [0, 1]
    d_entropy       : mean(|H_bigram_1 - H_bigram_2|,         ∈ [0, 1]
                           |H_trigram_1 - H_trigram_2|)
    d_exc_trans     : Jaccard distance on exception_transition_triples sets
    d_exc_recovery  : |recovery_rate_1 - recovery_rate_2|     ∈ [0, 1]
    d_causal        : Jaccard distance on causal_precedence_sets
    d_phase         : L1(phase_diversity_1, phase_diversity_2) / 2  ∈ [0, 1]
    d_loop          : 0.5 * d_run_length + 0.5 * |cv_1 - cv_2|    ∈ [0, 1]
        where d_run_length = L1(mean_run_lengths_1, mean_run_lengths_2) / 2

    Properties
    ----------
    * distance(g, g) = 0.0   (reflexivity)
    * distance(g1, g2) = distance(g2, g1)   (symmetry: all sub-distances symmetric)
    * result ∈ [0, 1]
    """
    W_tri = 0.20
    W_ent = 0.10
    W_exc = 0.10
    W_rec = 0.15
    W_cau = 0.15
    W_pha = 0.10
    W_lop = 0.20
    # sum = 1.0

    # ── d_trigrams ────────────────────────────────────────────────────────────
    all_tri = set(g1.call_trigrams) | set(g2.call_trigrams)
    if not all_tri:
        d_trigrams = 0.0
    else:
        l1 = sum(
            abs(g1.call_trigrams.get(k, 0.0) - g2.call_trigrams.get(k, 0.0))
            for k in all_tri
        )
        d_trigrams = min(1.0, l1 / 2.0)

    # ── d_entropy ─────────────────────────────────────────────────────────────
    d_entropy = 0.5 * abs(g1.bigram_entropy - g2.bigram_entropy) + \
                0.5 * abs(g1.trigram_entropy - g2.trigram_entropy)

    # ── d_exc_transitions (Jaccard on sorted string sets) ─────────────────────
    s1_exc = set(g1.exception_transition_triples)
    s2_exc = set(g2.exception_transition_triples)
    union_exc = len(s1_exc | s2_exc)
    d_exc_transitions = 0.0 if union_exc == 0 else (1.0 - len(s1_exc & s2_exc) / union_exc)

    # ── d_exc_recovery ────────────────────────────────────────────────────────
    d_exc_recovery = abs(g1.exception_recovery_rate - g2.exception_recovery_rate)

    # ── d_causal (Jaccard on causal_precedence_set) ───────────────────────────
    s1_cau = set(g1.causal_precedence_set)
    s2_cau = set(g2.causal_precedence_set)
    union_cau = len(s1_cau | s2_cau)
    d_causal = 0.0 if union_cau == 0 else (1.0 - len(s1_cau & s2_cau) / union_cau)

    # ── d_phase (L1 on 3-element diversity vectors) ───────────────────────────
    pv1 = g1.phase_diversity_vector
    pv2 = g2.phase_diversity_vector
    # Ensure both are length 3 (pad with 0 defensively)
    while len(pv1) < 3:
        pv1 = list(pv1) + [0.0]
    while len(pv2) < 3:
        pv2 = list(pv2) + [0.0]
    phase_l1 = sum(abs(pv1[i] - pv2[i]) for i in range(3))
    d_phase = min(1.0, phase_l1 / 2.0)

    # ── d_loop (run-length histogram + CV gap) ────────────────────────────────
    all_fn_keys = set(g1.loop_mean_run_length) | set(g2.loop_mean_run_length)
    if not all_fn_keys:
        d_run_length = 0.0
    else:
        # Normalize mean run lengths by their own max so comparison is scale-free
        max_rl = max(
            max(g1.loop_mean_run_length.values(), default=1.0),
            max(g2.loop_mean_run_length.values(), default=1.0),
            1.0,
        )
        l1_rl = sum(
            abs(
                g1.loop_mean_run_length.get(k, 0.0) / max_rl -
                g2.loop_mean_run_length.get(k, 0.0) / max_rl
            )
            for k in all_fn_keys
        )
        d_run_length = min(1.0, l1_rl / 2.0)

    max_cv = max(g1.loop_early_exit_score, g2.loop_early_exit_score, 1.0)
    d_cv = abs(g1.loop_early_exit_score - g2.loop_early_exit_score) / max_cv

    d_loop = min(1.0, 0.5 * d_run_length + 0.5 * d_cv)

    # ── Weighted total ────────────────────────────────────────────────────────
    total = (
        W_tri * d_trigrams
        + W_ent * d_entropy
        + W_exc * d_exc_transitions
        + W_rec * d_exc_recovery
        + W_cau * d_causal
        + W_pha * d_phase
        + W_lop * d_loop
    )
    return max(0.0, min(1.0, round(total, 8)))


# ---------------------------------------------------------------------------
# Unit Tests (10) — run with: python sbg/v5/temporal_genome_v5.py
# ---------------------------------------------------------------------------


def _make_events(
    sequence: List[Tuple[str, str, int]],
) -> List[dict]:
    """
    Helper: build event list from (event_type, function_name, depth) triples.
    """
    return [
        {"event_type": et, "function_name": fn, "depth": d}
        for et, fn, d in sequence
    ]


def _run_tests() -> None:  # pragma: no cover
    """Execute all 10 unit tests inline."""
    import traceback

    failures: List[str] = []

    def _test(name: str, fn):
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001
            failures.append(name)
            print(f"  FAIL  {name}: {exc}")
            traceback.print_exc()

    # ── TEST 1: distance(g, g) == 0.0 ─────────────────────────────────────────
    def test_self_distance_zero():
        events = _make_events([
            ("call", "foo", 1), ("call", "bar", 2), ("return", "bar", 1),
            ("call", "baz", 2), ("return", "baz", 1), ("return", "foo", 0),
        ])
        g = extract(events, program_id="T1")
        assert distance(g, g) == 0.0, f"Expected 0.0, got {distance(g, g)}"

    _test("test_self_distance_zero", test_self_distance_zero)

    # ── TEST 2: distance(g1, g2) == distance(g2, g1) ──────────────────────────
    def test_symmetry():
        ev1 = _make_events([("call", "a", 1), ("call", "b", 2), ("call", "c", 3)])
        ev2 = _make_events([("call", "x", 1), ("call", "y", 2)])
        g1 = extract(ev1, program_id="T2a")
        g2 = extract(ev2, program_id="T2b")
        d12 = distance(g1, g2)
        d21 = distance(g2, g1)
        assert d12 == d21, f"Asymmetric: {d12} != {d21}"

    _test("test_symmetry", test_symmetry)

    # ── TEST 3: distance result in [0, 1] ─────────────────────────────────────
    def test_distance_range():
        ev1 = _make_events([("call", "alpha", 1), ("call", "beta", 2),
                             ("call", "gamma", 3), ("return", "gamma", 2)])
        ev2 = _make_events([("call", "omega", 1), ("exception", "ValueError", 1),
                             ("call", "omega", 1)])
        g1 = extract(ev1, program_id="T3a")
        g2 = extract(ev2, program_id="T3b")
        d = distance(g1, g2)
        assert 0.0 <= d <= 1.0, f"distance out of range: {d}"

    _test("test_distance_range", test_distance_range)

    # ── TEST 4: Rename invariance — identical call order → same trigrams ───────
    def test_rename_invariance():
        # Two programs with different function names but same call structure
        ev_a = _make_events([
            ("call", "foo", 1), ("call", "bar", 2), ("call", "baz", 3),
            ("call", "foo", 1), ("call", "bar", 2), ("call", "baz", 3),
        ])
        ev_b = _make_events([
            ("call", "x1", 1), ("call", "x2", 2), ("call", "x3", 3),
            ("call", "x1", 1), ("call", "x2", 2), ("call", "x3", 3),
        ])
        g_a = extract(ev_a, program_id="T4a")
        g_b = extract(ev_b, program_id="T4b")
        # Trigram keys should be identical (both map to (0,1,2))
        assert g_a.call_trigrams == g_b.call_trigrams, (
            f"Trigrams differ under rename:\n  {g_a.call_trigrams}\n  {g_b.call_trigrams}"
        )

    _test("test_rename_invariance", test_rename_invariance)

    # ── TEST 5: Swapped call order → different causal_precedence_set ──────────
    def test_swapped_causal():
        # Use a SHARED name_to_idx (A=0, B=1) so both programs use the same index space.
        # A-before-B: pair (0,1) present (0 precedes 1 > 50% of co-occurrences).
        # B-before-A: pair (0,1) absent (1 precedes 0 in all co-occurrences).
        shared_map = {"A": 0, "B": 1}
        ev_ab = _make_events([("call", "A", 1), ("call", "B", 2)])
        ev_ba = _make_events([("call", "B", 1), ("call", "A", 2)])
        g_ab = extract(ev_ab, name_to_idx=dict(shared_map), program_id="T5ab")
        g_ba = extract(ev_ba, name_to_idx=dict(shared_map), program_id="T5ba")
        assert g_ab.causal_precedence_set != g_ba.causal_precedence_set, (
            "Swapped order should produce different causal sets with shared index map:\n"
            f"  AB: {g_ab.causal_precedence_set}\n  BA: {g_ba.causal_precedence_set}"
        )

    _test("test_swapped_causal", test_swapped_causal)

    # ── TEST 6: Single repeated call → loop_mean_run_length > 1 ───────────────
    def test_loop_run_length():
        # "foo" called 4 times in a row
        ev = _make_events([
            ("call", "foo", 1), ("call", "foo", 1),
            ("call", "foo", 1), ("call", "foo", 1),
        ])
        g = extract(ev, program_id="T6")
        assert "0" in g.loop_mean_run_length, (
            f"Expected key '0' in loop_mean_run_length: {g.loop_mean_run_length}"
        )
        assert g.loop_mean_run_length["0"] > 1.0, (
            f"Expected mean run length > 1, got {g.loop_mean_run_length['0']}"
        )

    _test("test_loop_run_length", test_loop_run_length)

    # ── TEST 7: Program with exception → non-empty exception_transition_triples
    def test_exception_triples():
        ev = _make_events([
            ("call", "foo", 1),
            ("exception", "ValueError", 1),
            ("call", "bar", 1),
        ])
        g = extract(ev, program_id="T7")
        assert len(g.exception_transition_triples) > 0, (
            f"Expected non-empty exception_transition_triples, got: {g.exception_transition_triples}"
        )

    _test("test_exception_triples", test_exception_triples)

    # ── TEST 8: bigram_entropy == 0 when only one bigram type ─────────────────
    def test_single_bigram_entropy_zero():
        # A always followed by A (self-loop) → only one bigram type "(0,0)"
        # _shannon_entropy_normalized([n]) = 0.0 when there is only 1 distinct type.
        ev = _make_events([
            ("call", "A", 1), ("call", "A", 1),
            ("call", "A", 1), ("call", "A", 1),
            ("call", "A", 1),
        ])
        g = extract(ev, program_id="T8")
        assert g.bigram_entropy == 0.0, (
            f"Expected bigram_entropy=0.0 for single bigram type, got {g.bigram_entropy}"
        )

    _test("test_single_bigram_entropy_zero", test_single_bigram_entropy_zero)

    # ── TEST 9: phase_diversity_vector has 3 elements summing to ≤ 1.0 ────────
    def test_phase_vector_properties():
        ev = _make_events([
            ("call", "init", 1), ("call", "work", 2),
            ("call", "work", 2), ("call", "work", 2),
            ("call", "teardown", 1),
        ])
        g = extract(ev, program_id="T9")
        assert len(g.phase_diversity_vector) == 3, (
            f"Expected 3 elements in phase_diversity_vector, got {len(g.phase_diversity_vector)}"
        )
        total = sum(g.phase_diversity_vector)
        assert total <= 1.0 + 1e-9, (
            f"phase_diversity_vector sum should be ≤ 1.0, got {total}"
        )

    _test("test_phase_vector_sum", test_phase_vector_properties)

    # ── TEST 10: Trigram extraction correct for 5-call sequence ───────────────
    def test_trigram_extraction():
        # Call sequence: A B C D E → trigrams: (A,B,C), (B,C,D), (C,D,E)
        # With anonymization: (0,1,2), (1,2,3), (2,3,4)
        ev = _make_events([
            ("call", "A", 1), ("call", "B", 1),
            ("call", "C", 1), ("call", "D", 1),
            ("call", "E", 1),
        ])
        g = extract(ev, program_id="T10")
        expected_keys = {"(0,1,2)", "(1,2,3)", "(2,3,4)"}
        actual_keys = set(g.call_trigrams.keys())
        assert actual_keys == expected_keys, (
            f"Expected trigram keys {expected_keys}, got {actual_keys}"
        )
        # Each has equal frequency: 1/3
        for k in expected_keys:
            assert abs(g.call_trigrams[k] - 1 / 3) < 1e-5, (
                f"Expected freq ~0.333 for {k}, got {g.call_trigrams[k]}"
            )

    _test("test_trigram_extraction_5call", test_trigram_extraction)

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    if failures:
        raise SystemExit(f"{len(failures)} test(s) FAILED: {failures}")
    print("All 10 tests passed.")


if __name__ == "__main__":
    _run_tests()
