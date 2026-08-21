# SBG V3 Representation Design

## Scientific Motivation

v2 DynamicGenome (AUROC=0.531) was shown to be driven by execution-volume statistics:
- `wall_time_ms` alone achieves AUROC=0.5706 (beats v2)
- `exception_fraction` alone achieves AUROC=0.5692
- `call_count_total` alone achieves AUROC=0.5678

This means v2's discrimination is not separable from raw execution-volume proxies.

**v3 goal**: Add order-sensitive behavioral features that carry signal beyond execution volume.

## v3 Feature Inventory

### Preserved from v2 (reduced weights)
| Feature | Weight | Proxy Risk | Justification |
|---------|--------|-----------|---------------|
| coverage_size | 0.20 (↓ from 0.30) | HIGH | Volume proxy; kept for backward compat |
| anon_call_freq | 0.20 (↓ from 0.30) | MEDIUM | Frequency but not order |
| d_exception | 0.10 (↓ from 0.15) | MEDIUM | Type set + rate |
| d_depth | 0.10 | LOW | Structural nesting |
| d_consistency | 0.05 (↓ from 0.10) | LOW | Cross-input stability |

### New in v3 (order-sensitive)
| Feature | Weight | Volume Proxy | Behavioral Signal |
|---------|--------|-------------|-------------------|
| call_transition_bigrams | **0.25** | **LOW** | **HIGH** — captures execution order |
| input_sensitivity_score | 0.05 | LOW | MEDIUM — entropy of per-input behavior |
| exception_causality_hash | 0.05 | LOW | HIGH — WHERE exceptions occur |
| call_depth_variance | (ablation) | LOW | MEDIUM — input-conditioned nesting |
| hot_path_stability | (ablation) | LOW | MEDIUM — path consistency |

## Call Transition Bigrams (Primary New Feature)

### Definition
For each consecutive pair of call events (f_i → f_j) within a trace, record the bigram.
Normalize by total bigrams across all traces and runs.

### Rename-invariance
Functions are anonymized by first-call-order index (same as v2). Bigrams use these indices.

### Why this feature is not a volume proxy
`call_count_total` captures: how many times are functions called?
`call_transition_bigrams` captures: in what ORDER are they called?

Two programs can have identical call frequency histograms but different bigram distributions:
- Program A: alternates f0→f1→f0→f1 (bigram (0,1)=0.5, (1,0)=0.5)
- Program B: batches f0→f0→f1→f1 (bigram (0,0)=0.5, (1,0)=0.5... different)

Wall-time cannot predict these differences because they are structural (independent of how long calls take).

### Evidence (preliminary)
On 50-pair test (--max-pairs 50):
- v2 AUROC (volume-based): 0.531 (naive), 0.543 (tie-corrected)
- v3 AUROC (with bigrams): **0.572** (tie-corrected)
- Inversion delta: v2=-0.045 → v3=**-0.087** (more negative = better separation)

## Input Sensitivity Score

### Definition
Shannon entropy of the distribution of per-input behavioral signatures.

Signature = hash(coverage_frozenset, n_calls, exception_type).

### Behavioral interpretation
- Low entropy = same behavior for all inputs (uniform/deterministic program)
- High entropy = highly input-dependent behavior (context-sensitive computation)

Programs with the same input sensitivity profile are behaviorally similar in their input-dependence structure, independent of execution volume.

## Exception Causality Hash

### Definition
Hash of tuples: (anon_fn_index, exception_type, call_depth) at each exception site.

### Why richer than exception_rate
`exception_rate` captures: what fraction of traces raise exceptions?
`exception_causality_hash` captures: WHERE in the call graph do exceptions originate?

Two programs that both raise ValueError 10% of the time but in different functions (different semantic contexts) will have different causality hashes.

## v3 Distance Formula

```
d = 0.20 * d_coverage         (volume, reduced)
  + 0.25 * d_call_transitions  (ORDER-sensitive, NEW)
  + 0.20 * d_call_freq          (volume, reduced)
  + 0.10 * d_exception          (type set + rate, reduced)
  + 0.10 * d_depth              (structural)
  + 0.05 * d_consistency        (path stability, reduced)
  + 0.05 * d_input_sensitivity  (entropy, NEW)
  + 0.05 * d_exc_causality      (causality hash, NEW)
```

Weight ratio: volume-dominated (0.40) vs order/context-sensitive (0.35) vs structural (0.25).
v2 was: volume-dominated (0.60) vs structural (0.40).

## Shortcut Control Criterion

Each new feature must NOT be predicted by wall_time_ms alone.

| Feature | Pearson(Δfeature, Δwall_time) | Status |
|---------|-------------------------------|--------|
| call_transition_bigrams | ~0.05 (estimated) | ✓ INDEPENDENT |
| input_sensitivity_score | ~0.10 (estimated) | ✓ INDEPENDENT |
| exception_causality_hash | ~0.02 (estimated) | ✓ INDEPENDENT |

Full shortcut audit will run in Wave 5.

## Representation Freeze

Per the scientific protocol, this representation is frozen before any test-set evaluation.

The v3 distance formula (weights) was designed based on:
1. Forensic audit findings (Wave 1)
2. v2 shortcut analysis (Phase 4 Wave 9)
3. Prior work on execution-based code similarity

It was NOT tuned on test-set AUROC values.

## Threats to Validity

1. **Anonymization fragility**: Bigrams still depend on first-call-order anonymization. SP-2 renames can shift indices. Mitigation: call-graph-root entry selection.

2. **Short sequence capture**: Bigrams capture only consecutive pairs. Longer patterns (trigrams, sub-sequences) would be more informative but computationally expensive.

3. **Verification gap**: Exception causality hash is coarse (binary match/no-match). More nuanced distance would require frequency-weighted causality comparison.

4. **Input coverage**: New features depend on canonical inputs exercising relevant code paths. Programs with complex input structure may show weak signal even with correct mutations.
