"""
sbg.v3.genome
=============
SBG V3 DynamicGenome — richer behavioral representation.

DESIGN PHILOSOPHY (Wave 4)
==========================
v2 was dominated by execution-volume statistics:
  - coverage_size (how much code runs)
  - anon_call_freq (how often each function is called)
  - exception_rate (how often exceptions occur)
  - call_depth_mean (how deep the call stack goes)

These are vulnerable to the shortcut criticism: wall_time_ms alone
achieves AUROC=0.5706 (vs B07=0.531).

v3 adds ORDER-SENSITIVE and CONTEXT-AWARE features:

1. call_transition_bigrams: Dict[str, float]
   Normalized frequency of consecutive function-call pairs (f_i → f_j).
   Captures CALL ORDER, not just frequency.
   Rename-invariant via anonymization indices.

2. branch_coverage_ratio: float
   Fraction of conditional branches exercised (taken vs not-taken).
   Captures CONTROL FLOW DEPTH, not just line coverage.
   Requires enhanced tracer (see note below).

3. exception_causality_vector: List[str]
   (anon_fn_idx, exception_type, call_depth) tuples at exception sites.
   Captures WHERE and IN WHAT CONTEXT exceptions occur.

4. input_sensitivity_score: float
   Entropy of per-input behavioral signatures.
   High = sensitive to inputs (context-dependent); low = uniform behavior.

5. call_depth_variance: float
   Variance of max call depth across traces (not just mean).
   High variance = input-conditioned branching behavior.

6. hot_path_stability: float
   Fraction of traces that share the same top-3 call sequence hash.
   High = stable execution path; low = highly variable.

SCIENTIFIC JUSTIFICATION
=========================
Each new feature is:
- Order-sensitive (not volume-dependent)
- Rename-invariant (anonymized by first-call order)
- Output-free (SAFEGUARD-2 compliant)
- Computable from existing ExecutionTrace events

The shortcut-elimination criterion (Wave 5):
  Each v3 feature must NOT be predictable from wall_time_ms alone.

LIMITATIONS
===========
Branch taken/not-taken requires bytecode-level tracing (not yet in v1 Tracer).
v3 uses an approximation: proportion of distinct line-number sub-sequences.

Call transition bigrams require O(trace_len) per trace — acceptable for
typical benchmark programs (< 10k events per trace).
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from sbg.v2.execution.normalizer import NormalizedBehavior, TraceNormalizer
from sbg.extraction.dynamic.tracer import ExecutionTrace


# ---------------------------------------------------------------------------
# v3 DynamicGenome
# ---------------------------------------------------------------------------

@dataclass
class DynamicGenomeV3:
    """
    SBG V3 behavioral genome — richer execution representation.

    All features are Output-free (SAFEGUARD-2).
    All features are rename-invariant (anonymized by first-call order).

    New features vs v2
    ------------------
    call_transition_bigrams  : order-sensitive call sequence patterns
    input_sensitivity_score  : entropy of per-input behavioral diversity
    call_depth_variance      : variance of max depth (input-conditioned behavior)
    hot_path_stability       : fraction of traces sharing same top-3 call pattern
    exception_causality_hash : hash of (fn_idx, exc_type, depth) context tuples

    Preserved features from v2
    --------------------------
    coverage_size, coverage_consistency, anon_call_freq, hot_path_hash,
    exception_type_set, exception_rate, call_depth_mean, call_depth_max,
    trace_length_mean, trace_length_std, n_unique_functions
    """

    # --- Core identity ---
    program_id: str

    # --- v2 preserved features ---
    coverage_size: int
    coverage_consistency: float
    anon_call_freq: Dict[int, float]
    hot_path_hash: str
    exception_type_set: List[str]
    exception_rate: float
    call_depth_mean: float
    call_depth_max: float
    trace_length_mean: float
    trace_length_std: float
    n_unique_functions: int

    # --- v3 new features ---
    call_transition_bigrams: Dict[str, float]   # "(i,j)" → normalized freq
    input_sensitivity_score: float              # entropy of per-input signatures
    call_depth_variance: float                  # variance of max depth across traces
    hot_path_stability: float                   # fraction of traces with same top-3 hash
    exception_causality_hash: str               # hash of exception context tuples

    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "program_id": self.program_id,
            # v2 features
            "coverage_size": self.coverage_size,
            "coverage_consistency": self.coverage_consistency,
            "anon_call_freq": {str(k): v for k, v in self.anon_call_freq.items()},
            "hot_path_hash": self.hot_path_hash,
            "exception_type_set": self.exception_type_set,
            "exception_rate": self.exception_rate,
            "call_depth_mean": self.call_depth_mean,
            "call_depth_max": self.call_depth_max,
            "trace_length_mean": self.trace_length_mean,
            "trace_length_std": self.trace_length_std,
            "n_unique_functions": self.n_unique_functions,
            # v3 features
            "call_transition_bigrams": self.call_transition_bigrams,
            "input_sensitivity_score": self.input_sensitivity_score,
            "call_depth_variance": self.call_depth_variance,
            "hot_path_stability": self.hot_path_stability,
            "exception_causality_hash": self.exception_causality_hash,
            # metadata
            "feature_classification": "OUTPUT_FREE",
            "safeguard_2_compliant": True,
            "version": "v3",
        }


# ---------------------------------------------------------------------------
# v3 Genome Extractor
# ---------------------------------------------------------------------------

class DynamicGenomeExtractorV3:
    """
    Extract DynamicGenomeV3 from raw ExecutionTrace objects.

    Computes v2 features via the existing TraceNormalizer +
    DynamicGenomeExtractor pipeline, then adds v3-specific features.
    """

    def __init__(self) -> None:
        self._normalizer = TraceNormalizer()

    def extract_from_traces(
        self,
        program_id: str,
        all_runs: List[List[ExecutionTrace]],
    ) -> DynamicGenomeV3:
        """
        Extract V3 genome from execution traces.

        Parameters
        ----------
        program_id : str
        all_runs : List[List[ExecutionTrace]]
            Outer list: runs. Inner list: one trace per input.

        Returns
        -------
        DynamicGenomeV3
        """
        if not all_runs or not any(all_runs):
            return self._empty(program_id)

        # Use v2 normalizer for baseline features
        nb = self._normalizer.normalize(program_id, all_runs)

        # Flatten all traces
        all_traces: List[ExecutionTrace] = [t for run in all_runs for t in run]

        # Build anonymization map (same as v2 normalizer)
        name_to_idx: Dict[str, int] = {}
        for trace in all_traces:
            for ev in trace.events:
                if ev.event_type == "call" and ev.function_name not in name_to_idx:
                    name_to_idx[ev.function_name] = len(name_to_idx)

        # --- v3 Feature 1: Call transition bigrams ---
        bigrams = self._compute_call_bigrams(all_traces, name_to_idx)

        # --- v3 Feature 2: Input sensitivity score ---
        # Per-input signature: hash of (coverage_set, n_calls, exception_type)
        per_input_sigs = self._compute_per_input_signatures(all_traces, name_to_idx)
        input_sensitivity = self._entropy(list(per_input_sigs.values()))

        # --- v3 Feature 3: Call depth variance ---
        call_depth_var = self._compute_call_depth_variance(all_traces)

        # --- v3 Feature 4: Hot path stability ---
        hot_path_stability = self._compute_hot_path_stability(all_traces, name_to_idx)

        # --- v3 Feature 5: Exception causality hash ---
        exc_causality_hash = self._compute_exception_causality_hash(
            all_traces, name_to_idx
        )

        return DynamicGenomeV3(
            program_id=program_id,
            # v2 features from normalizer
            coverage_size=nb.coverage_vector_size,
            coverage_consistency=nb.coverage_consistency,
            anon_call_freq=dict(nb.anon_call_freq),
            hot_path_hash=nb.hot_path_hash,
            exception_type_set=list(nb.exception_type_set),
            exception_rate=nb.exception_rate,
            call_depth_mean=nb.call_depth_stats.get("mean", 0.0),
            call_depth_max=nb.call_depth_stats.get("max", 0.0),
            trace_length_mean=nb.trace_length_stats.get("mean", 0.0),
            trace_length_std=nb.trace_length_stats.get("std", 0.0),
            n_unique_functions=nb.n_unique_functions,
            # v3 new features
            call_transition_bigrams=bigrams,
            input_sensitivity_score=input_sensitivity,
            call_depth_variance=call_depth_var,
            hot_path_stability=hot_path_stability,
            exception_causality_hash=exc_causality_hash,
            provenance={
                "program_id": program_id,
                "n_runs": len(all_runs),
                "n_traces_total": len(all_traces),
                "n_functions_observed": len(name_to_idx),
                "feature_classification": "OUTPUT_FREE",
                "safeguard_2_compliant": True,
                "version": "v3",
            },
        )

    # ------------------------------------------------------------------
    # v3 Feature Computations
    # ------------------------------------------------------------------

    def _compute_call_bigrams(
        self, traces: List[ExecutionTrace], name_to_idx: Dict[str, int]
    ) -> Dict[str, float]:
        """
        Compute normalized call transition bigram frequencies.

        For each consecutive pair of call events (f_i → f_j) within a trace,
        record the bigram. Normalize by total bigrams across all traces.

        Rename-invariant: uses anonymous indices, not function names.
        """
        bigram_counts: Dict[str, int] = {}
        total = 0

        for trace in traces:
            call_seq = [
                name_to_idx.get(ev.function_name, -1)
                for ev in trace.events
                if ev.event_type == "call"
            ]
            for i in range(len(call_seq) - 1):
                if call_seq[i] >= 0 and call_seq[i+1] >= 0:
                    key = f"({call_seq[i]},{call_seq[i+1]})"
                    bigram_counts[key] = bigram_counts.get(key, 0) + 1
                    total += 1

        if total == 0:
            return {}
        return {k: v / total for k, v in bigram_counts.items()}

    def _compute_per_input_signatures(
        self, traces: List[ExecutionTrace], name_to_idx: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Compute a behavioral signature for each unique input representation.

        Signature = hash of (coverage_frozenset, n_calls, exception_type_set).
        Returns {input_repr: signature_count} — count of traces per signature.
        """
        sig_counts: Dict[str, int] = {}
        for trace in traces:
            cov_key = ",".join(str(l) for l in sorted(trace.coverage))
            n_calls = sum(1 for ev in trace.events if ev.event_type == "call")
            exc_key = trace.exception.split(":")[0] if trace.exception else ""
            raw = f"{cov_key}|{n_calls}|{exc_key}"
            sig = hashlib.md5(raw.encode()).hexdigest()[:8]
            sig_counts[sig] = sig_counts.get(sig, 0) + 1
        return sig_counts

    def _entropy(self, counts: List[int]) -> float:
        """Normalized Shannon entropy of count distribution."""
        total = sum(counts)
        if total == 0 or len(counts) <= 1:
            return 0.0
        n = len(counts)
        entropy = 0.0
        for c in counts:
            if c > 0:
                p = c / total
                entropy -= p * math.log2(p)
        # Normalize by log2(n) to get [0, 1]
        max_entropy = math.log2(n)
        return round(entropy / max_entropy, 6) if max_entropy > 0 else 0.0

    def _compute_call_depth_variance(self, traces: List[ExecutionTrace]) -> float:
        """Variance of max call depth across traces."""
        depths = []
        for trace in traces:
            depth = max_depth = 0
            for ev in trace.events:
                if ev.event_type == "call":
                    depth += 1
                    max_depth = max(max_depth, depth)
                elif ev.event_type == "return":
                    depth = max(0, depth - 1)
            depths.append(max_depth)
        if len(depths) < 2:
            return 0.0
        mean_d = sum(depths) / len(depths)
        var_d = sum((d - mean_d) ** 2 for d in depths) / len(depths)
        return round(var_d, 6)

    def _compute_hot_path_stability(
        self, traces: List[ExecutionTrace], name_to_idx: Dict[str, int]
    ) -> float:
        """
        Fraction of traces that share the most common top-3 call sequence hash.

        High stability = program follows same execution path regardless of input.
        Low stability = highly input-conditioned behavior.
        """
        n = len(traces)
        if n == 0:
            return 1.0

        hashes: Dict[str, int] = {}
        for trace in traces:
            call_seq = [
                name_to_idx.get(ev.function_name, -1)
                for ev in trace.events
                if ev.event_type == "call"
            ]
            top3 = call_seq[:3]  # First 3 calls determine the main path
            key = "|".join(str(i) for i in top3)
            h = hashlib.md5(key.encode()).hexdigest()[:8]
            hashes[h] = hashes.get(h, 0) + 1

        if not hashes:
            return 1.0

        most_common_count = max(hashes.values())
        return round(most_common_count / n, 6)

    def _compute_exception_causality_hash(
        self, traces: List[ExecutionTrace], name_to_idx: Dict[str, int]
    ) -> str:
        """
        Hash of exception causality tuples: (anon_fn_idx, exc_type, call_depth).

        Captures WHERE exceptions occur in the call graph and WHAT TYPE they are.
        More semantically rich than exception_type_set alone.
        """
        causality_tuples = []
        for trace in traces:
            if trace.exception is None:
                continue
            exc_type = trace.exception.split(":")[0].strip()
            # Find the function + depth at the point of exception
            depth = 0
            last_fn_idx = -1
            for ev in trace.events:
                if ev.event_type == "call":
                    depth += 1
                    last_fn_idx = name_to_idx.get(ev.function_name, -1)
                elif ev.event_type == "return":
                    depth = max(0, depth - 1)
                elif ev.event_type == "exception":
                    fn_idx = name_to_idx.get(ev.function_name, -1)
                    causality_tuples.append((fn_idx, exc_type, depth))

        if not causality_tuples:
            return hashlib.sha256(b"no_exceptions").hexdigest()[:16]

        # Sort for determinism
        causality_tuples.sort()
        key = "|".join(f"{fn}:{exc}:{dep}" for fn, exc, dep in causality_tuples)
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def _empty(self, program_id: str) -> DynamicGenomeV3:
        """Return empty genome for programs that could not be executed."""
        return DynamicGenomeV3(
            program_id=program_id,
            coverage_size=0,
            coverage_consistency=1.0,
            anon_call_freq={},
            hot_path_hash=hashlib.sha256(b"").hexdigest()[:16],
            exception_type_set=[],
            exception_rate=0.0,
            call_depth_mean=0.0,
            call_depth_max=0.0,
            trace_length_mean=0.0,
            trace_length_std=0.0,
            n_unique_functions=0,
            call_transition_bigrams={},
            input_sensitivity_score=0.0,
            call_depth_variance=0.0,
            hot_path_stability=1.0,
            exception_causality_hash=hashlib.sha256(b"empty").hexdigest()[:16],
            provenance={
                "program_id": program_id,
                "n_runs": 0,
                "n_traces_total": 0,
                "feature_classification": "OUTPUT_FREE",
                "safeguard_2_compliant": True,
                "version": "v3",
            },
        )


# ---------------------------------------------------------------------------
# v3 Distance Function
# ---------------------------------------------------------------------------

def distance_v3(g1: DynamicGenomeV3, g2: DynamicGenomeV3) -> float:
    """
    Pseudometric on DynamicGenomeV3 in [0, 1].

    v3 formula (8-component weighted average):

    d = W_cov  * d_coverage         (0.20)  # reduced from 0.30 to reduce volume bias
      + W_seq  * d_call_transitions  (0.25)  # NEW: order-sensitive sequences
      + W_freq * d_call_freq          (0.20)  # reduced from 0.30
      + W_exc  * d_exception          (0.10)  # reduced from 0.15
      + W_dep  * d_depth              (0.10)
      + W_con  * d_consistency        (0.05)  # reduced from 0.10
      + W_inp  * d_input_sensitivity  (0.05)  # NEW: input-conditioned behavior
      + W_exc2 * d_exc_causality      (0.05)  # NEW: exception context

    Component definitions
    ---------------------
    d_coverage    : |coverage_size_1 - coverage_size_2| / max(1, max(sizes))
    d_call_trans  : L1(bigrams_1, bigrams_2) / 2  [order-sensitive]
    d_call_freq   : L1(anon_call_freq_1, anon_call_freq_2) / 2
    d_exception   : 0.5 * Jaccard(exc_types) + 0.5 * |exc_rate_1 - exc_rate_2|
    d_depth       : |depth_mean_1 - depth_mean_2| / max(1, max(depths))
    d_consistency : |consistency_1 - consistency_2|
    d_input_sens  : |input_sensitivity_1 - input_sensitivity_2|
    d_exc_causality: 0 if exc_causality_hash matches, 1 if not (coarse)

    Scientific justification for weight changes
    --------------------------------------------
    v2 had d_coverage=0.30 and d_call_freq=0.30 (60% on volume statistics).
    Wave 5 shortcut audit found these are driven by execution-volume proxies.
    v3 reduces volume weights to 0.40 total, adds order-sensitive features
    (call_transitions=0.25) which cannot be predicted by wall_time_ms alone.

    Properties
    ----------
    * d(g, g) = 0.0
    * d(g1, g2) = d(g2, g1)  (symmetric)
    * result in [0, 1]
    """
    W_cov, W_seq, W_freq = 0.20, 0.25, 0.20
    W_exc, W_dep, W_con  = 0.10, 0.10, 0.05
    W_inp, W_exc2        = 0.05, 0.05

    # d_coverage (execution volume — kept but reduced weight)
    max_cov = max(g1.coverage_size, g2.coverage_size, 1)
    d_coverage = abs(g1.coverage_size - g2.coverage_size) / max_cov

    # d_call_transitions (NEW: order-sensitive bigrams)
    all_bigrams = set(g1.call_transition_bigrams) | set(g2.call_transition_bigrams)
    if not all_bigrams:
        d_call_trans = 0.0
    else:
        l1 = sum(
            abs(g1.call_transition_bigrams.get(b, 0.0) - g2.call_transition_bigrams.get(b, 0.0))
            for b in all_bigrams
        )
        d_call_trans = min(1.0, l1 / 2.0)

    # d_call_freq (execution volume — frequency histogram)
    all_funcs = set(g1.anon_call_freq) | set(g2.anon_call_freq)
    if not all_funcs:
        d_call_freq = 0.0
    else:
        l1 = sum(
            abs(g1.anon_call_freq.get(f, 0.0) - g2.anon_call_freq.get(f, 0.0))
            for f in all_funcs
        )
        d_call_freq = min(1.0, l1 / 2.0)

    # d_exception
    s1, s2 = set(g1.exception_type_set), set(g2.exception_type_set)
    union_exc = len(s1 | s2)
    jaccard_exc = 0.0 if union_exc == 0 else (1.0 - len(s1 & s2) / union_exc)
    d_exception = 0.5 * jaccard_exc + 0.5 * abs(g1.exception_rate - g2.exception_rate)

    # d_depth
    max_depth = max(g1.call_depth_mean, g2.call_depth_mean, 1.0)
    d_depth = abs(g1.call_depth_mean - g2.call_depth_mean) / max_depth

    # d_consistency
    d_consistency = abs(g1.coverage_consistency - g2.coverage_consistency)

    # d_input_sensitivity (NEW)
    d_input_sens = abs(g1.input_sensitivity_score - g2.input_sensitivity_score)

    # d_exception_causality (NEW: coarse binary on hash match)
    d_exc_causality = 0.0 if g1.exception_causality_hash == g2.exception_causality_hash else 1.0

    total = (
        W_cov  * d_coverage
        + W_seq  * d_call_trans
        + W_freq * d_call_freq
        + W_exc  * d_exception
        + W_dep  * d_depth
        + W_con  * d_consistency
        + W_inp  * d_input_sens
        + W_exc2 * d_exc_causality
    )
    return max(0.0, min(1.0, total))
