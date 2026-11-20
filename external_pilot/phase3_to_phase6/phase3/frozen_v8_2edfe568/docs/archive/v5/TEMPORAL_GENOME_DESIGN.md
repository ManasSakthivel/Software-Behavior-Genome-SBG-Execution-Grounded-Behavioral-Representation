# Temporal Behavioral Genome v5 — Design Document

**File:** `sbg/v5/temporal_genome_v5.py`  
**Version:** v5  
**Classification:** OUTPUT_FREE / SAFEGUARD-2 compliant  
**Dependencies:** Python stdlib only (`collections`, `hashlib`, `math`, `itertools`)

---

## 1. Motivation

The V3 genome introduced call-transition bigrams — consecutive (i→j) call pairs — to
capture *order-sensitive* behavior.  This was a significant improvement over V2's pure
frequency histograms, but bigrams are limited to length-2 windows and cannot encode
longer sequential patterns, repeated-structure (loop) behavior, or the causal relationship
between function invocations across a trace.

V5 adds five new feature families (g_τ) that extend the V3 bigram foundation:

| Family | Feature | What it captures |
|--------|---------|-----------------|
| F1 | Call trigrams + entropy | 3-call sequential patterns; diversity of call ordering |
| F2 | Exception transition triples | Where, which, and what follows exceptions |
| F3 | Causal precedence chains | Which functions consistently precede others |
| F4 | Phase diversity | Behavioral diversity in setup / main / teardown phases |
| F5 | Loop profiles | Mean contiguous run lengths; loop regularity |

---

## 2. Dataclass: `TemporalGenomeV5`

```python
@dataclass
class TemporalGenomeV5:
    program_id: str

    # F1: Call N-grams
    call_trigrams: Dict[str, float]        # "(i,j,k)" → normalized frequency
    bigram_entropy: float                   # normalized Shannon entropy of bigrams
    trigram_entropy: float                  # normalized Shannon entropy of trigrams

    # F2: Exception transitions
    exception_transition_triples: List[str] # sorted "(pre_idx,exc_type,post_idx)"
    exception_recovery_rate: float          # fraction of exceptions followed by normal call

    # F3: Causal chains
    causal_precedence_set: List[str]        # sorted "(i,j)" where i precedes j in >50%
    causal_entropy: float                   # mean binary entropy of causal ordering probs

    # F4: Phase diversity
    phase_diversity_vector: List[float]     # [setup_div, main_div, teardown_div]

    # F5: Loop profiles
    loop_mean_run_length: Dict[str, float]  # str(anon_idx) → mean contiguous run length
    loop_early_exit_score: float            # coefficient of variation of run lengths

    provenance: Dict
```

---

## 3. Feature Family Designs

### F1 — Call N-grams

**Bigrams** (inherited from V3): consecutive call pairs (i, j) normalized by total.

**Trigrams** (new): consecutive call triples (i, j, k) normalized by total trigrams.

```
call_seq = [0, 1, 2, 0, 1, 2]
trigrams: (0,1,2) × 2 → {(0,1,2): 1.0}   (only one type → trigram_entropy = 0)
```

**Entropy**: normalized Shannon entropy H / log₂(n) ∈ [0, 1].  
- `bigram_entropy = 0` ↔ only one call transition type (perfectly regular).  
- `bigram_entropy = 1` ↔ all bigram types equally frequent (maximally variable).

**Rename invariance**: all keys use integer indices (first-call order). Functions with
different names but the same call structure produce identical trigram dictionaries.

---

### F2 — Exception Transition Triples

For each exception event, record the tuple:
```
(pre_call_idx, exception_type_string, post_call_idx)
```
where:
- `pre_call_idx` = anonymous index of the most recent `call` event before the exception
- `exception_type_string` = raw `function_name` of the exception event (class name, rename-invariant)
- `post_call_idx` = anonymous index of the next `call` event after the exception (-1 if none)

**Recovery rate** = fraction of exception events followed by a `call` (not another exception).

**Rename invariance**: exception type strings are class names (e.g., `ValueError`), not
function names — they are intrinsically rename-invariant.

---

### F3 — Causal Precedence Chains

For every ordered pair of distinct function indices (i, j):
- Count `n_ij` = number of times index i appears before index j in the call sequence.
- Count `n_ji` = number of times index j appears before index i.
- `p_ij = n_ij / (n_ij + n_ji)`

If `p_ij > 0.5`, add `"(i,j)"` to `causal_precedence_set`.

**Causal entropy** = mean binary entropy h(p_ij) over all pairs, where  
`h(p) = -p·log₂(p) - (1−p)·log₂(1−p)`.  
A value near 0 means all orderings are deterministic; near 1 means all orderings are random.

**Key property**: using a shared `name_to_idx`, `A→B` and `B→A` sequences produce
different causal sets, as demonstrated by Test 5.

---

### F4 — Phase Diversity

The call sequence is divided into three equal-length phases:
```
setup    = call_seq[:n//3]
main     = call_seq[n//3 : 2n//3]
teardown = call_seq[2n//3:]
```

For each phase, compute normalized Shannon entropy of the function-index frequency
distribution within that phase.

`phase_diversity_vector = [setup_div, main_div, teardown_div]` ∈ [0, 1]³

A program with a fixed initializer followed by a varied main loop followed by a single
cleanup call would yield `[0.0, high, 0.0]`.

**Invariant**: each element ≤ 1.0, so sum ≤ 3.0 (and ≤ 1.0 for most typical programs).

---

### F5 — Loop Profiles

A contiguous run of the same function index in the call sequence is treated as a "loop body".

For each function index, collect all contiguous run lengths and compute the mean:
```
call_seq = [0, 0, 0, 1, 0, 0]
runs[0] = [3, 2]  →  mean_run_length["0"] = 2.5
runs[1] = [1]     →  mean_run_length["1"] = 1.0
```

**Loop early exit score** = coefficient of variation (CV = σ/μ) of ALL run lengths across
all functions.  High CV → irregular loops (early exits, variable iteration count).
CV = 0 → all runs have identical length (perfectly regular loop structure).

---

## 4. Extraction API

```python
def extract(
    events: List[dict],
    name_to_idx: Optional[Dict[str, int]] = None,
    program_id: str = "unknown",
) -> TemporalGenomeV5:
```

**Input**: flat list of event dicts with keys `event_type`, `function_name`, `depth`.

**Anonymization**: if `name_to_idx` is not provided, it is built from first-call order
across the input event list. Providing a pre-built map enables cross-program comparison
with a shared index space (required for meaningful causal comparison).

**Output**: `TemporalGenomeV5` with canonicalization applied.

---

## 5. Distance Function

```python
def distance(g1: TemporalGenomeV5, g2: TemporalGenomeV5) -> float:
```

Seven-component weighted mean in [0, 1]:

| Component | Weight | Sub-distance formula |
|-----------|--------|---------------------|
| `d_trigrams` | 0.20 | L1(trigram dicts) / 2 |
| `d_entropy` | 0.10 | 0.5·\|H_bi₁−H_bi₂\| + 0.5·\|H_tri₁−H_tri₂\| |
| `d_exc_transitions` | 0.10 | Jaccard distance on triple sets |
| `d_exc_recovery` | 0.15 | \|recovery_rate₁ − recovery_rate₂\| |
| `d_causal` | 0.15 | Jaccard distance on causal_precedence_sets |
| `d_phase` | 0.10 | L1(phase vectors) / 2 |
| `d_loop` | 0.20 | 0.5·d_run_length + 0.5·\|CV₁−CV₂\|/max_CV |

**Formal properties**:
- `distance(g, g) = 0.0` — reflexivity
- `distance(g1, g2) = distance(g2, g1)` — symmetry (all sub-distances are symmetric)
- `result ∈ [0, 1]` — bounded

---

## 6. Canonicalization

```python
def canonicalize(g: TemporalGenomeV5) -> TemporalGenomeV5:
```

Steps applied before returning from `extract()` and available standalone:
1. Sort all dict keys lexicographically.
2. Round all float values to 6 decimal places.
3. Sort all list fields.
4. Clamp float fields to [0, 1] where semantically appropriate.

---

## 7. Design Invariants

| Invariant | Mechanism |
|-----------|-----------|
| Rename-invariant (SP-2) | All dict keys are integer indices from first-call order |
| Output-free (SAFEGUARD-2) | Only `event_type`, `function_name`, `depth` consumed |
| Exception type invariance | Exception type strings are class names, not function names |
| Deterministic | `canonicalize` applied at extraction; floats rounded to 6 dp |
| Self-distance zero | All sub-distances are reflexive by construction |
| Symmetric | All sub-distances use absolute differences, min/max, or Jaccard |

---

## 8. Relationship to Earlier Versions

```
V2 DynamicGenome     — volume statistics: coverage, call_freq, exception_rate
V3 DynamicGenomeV3   — adds bigrams, input_sensitivity, depth_variance
V5 TemporalGenomeV5  — adds trigrams, exception transitions, causal chains,
                        phase diversity, loop profiles
```

V5 is **standalone** (no dependency on V2/V3 normalizer). It accepts a simple
`List[dict]` event format and performs its own anonymization. This makes it usable
without the full `ExecutionTrace` infrastructure.

---

## 9. Test Coverage

Ten unit tests in `if __name__ == '__main__':`:

| # | Property tested |
|---|----------------|
| 1 | `distance(g, g) == 0.0` |
| 2 | `distance(g1, g2) == distance(g2, g1)` |
| 3 | `distance ∈ [0, 1]` |
| 4 | Identical call structure under different function names → same trigrams |
| 5 | Swapped call order (shared index map) → different causal_precedence_set |
| 6 | Single repeated call → `loop_mean_run_length > 1` |
| 7 | Exception event → non-empty `exception_transition_triples` |
| 8 | Single bigram type → `bigram_entropy == 0.0` |
| 9 | `phase_diversity_vector` has 3 elements, sum ≤ 1.0 |
| 10 | 5-call sequence → exactly 3 trigrams with correct keys and frequencies |

Run: `python3 sbg/v5/temporal_genome_v5.py`
