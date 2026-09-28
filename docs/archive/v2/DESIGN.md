# SBG V2 — Architecture Design

**Date:** 2025-07-07  
**Status:** Pre-implementation design specification

---

## Core Principles

1. **V1 is FROZEN** — no modifications to `sbg/`, `baselines/`, `benchmark/corpus/`, `experiments/phase4/`, `artifacts/research/`
2. **Output-free features only** — SAFEGUARD-2 enforced at extraction time
3. **Composable with v1** — v2 imports v1 components (especially Tracer), does not replace them
4. **Determinism** — all extractions reproducible given same inputs and seed
5. **Provenance** — every genome carries evidence of extraction method and inputs used
6. **Rename-invariant features** — no function names used in distance computation
7. **Line-number-invariant features** — no absolute line numbers in distance computation

---

## Directory Structure

```
sbg/v2/
├── __init__.py
├── execution/
│   ├── __init__.py
│   ├── runner.py          # SandboxRunner — composes v1 Tracer; noise-floor (SAFEGUARD-6)
│   ├── normalizer.py      # TraceNormalizer — anonymized, rename-invariant features
│   ├── genome.py          # DynamicGenome + DynamicGenomeExtractor + distance()
│   └── tests/
│       ├── __init__.py
│       ├── test_runner.py
│       ├── test_normalizer.py
│       └── test_genome.py
└── hybrid/
    ├── __init__.py
    ├── fusion.py          # HybridGenome dataclass + fuse()
    └── distance.py        # hybrid_distance() — weighted combination

baselines/v2/
├── __init__.py
├── b07_dynamic_v2.py      # Dynamic-only baseline (H7)
└── b08_hybrid_sbg_v2.py   # Hybrid SBG baseline (H8, H9, H12)

experiments/v2/
├── __init__.py
├── e1_dynamic_discrimination.py    # H7
├── e2_inversion_reduction.py       # H9
├── e3_hybrid_vs_dynamic.py         # H8
├── e4_refactoring_robustness.py    # H10
├── e5_hard_negative_analysis.py    # SC-3/SC-11 SAFEGUARD-4
└── run_all_experiments.py

docs/v2/
├── HYPOTHESES_V2.md       # SAFEGUARD-1
├── FEATURE_ORACLE.md      # SAFEGUARD-2
├── THREATS_V2.md
├── DESIGN.md              # (this file)
├── PHASE_0_BASELINE_AUDIT.md
└── agents/

artifacts/v2/
├── PHASE_0_GATE.json
├── PREREGISTRATION_MANIFEST.json
├── B07/                   # B07 results
└── B08/                   # B08 results
```

---

## Key Design Decisions

### D1: Output-Free Dynamic Features Only

All SBG genome features are execution STRUCTURE. DynamicGenomeExtractor never accesses
`trace.return_value` or `trace.stdout` content. Only exception class names (not messages) allowed.

### D2: Rename-Invariant Normalization

Functions are anonymized by first-call order before any frequency computation.
Call frequency histogram is keyed by integer index (0, 1, 2...), not function name.
This makes SP-2 (rename) produce identical normalized signatures.

### D3: Relative Coverage

Coverage consistency (Jaccard ratio) is used instead of absolute line numbers.
This makes coverage features robust to SP-8 (extract function adds lines) and similar transforms.

### D4: Noise Floor Measurement (SAFEGUARD-6)

SandboxRunner runs each program ≥5 times. Intra-version feature variance is computed.
Features where std/mean > 0.10 across runs are flagged as non-deterministic.

### D5: Hybrid Fusion Weights (pre-registered)

Default fusion weights: static=0.4, dynamic=0.6. These are pre-registered in HYPOTHESES_V2.md.
Alpha sweep on DEV split is allowed for H8 ablation, but final test evaluation uses pre-registered weights.

---

## Integration with V1

V2 imports from v1 (unchanged):
- `from sbg.extraction.dynamic.tracer import Tracer, ExecutionTrace`
- `from baselines.common import load_pairs, compute_auroc, compute_metrics`
- Test pairs: `benchmark/datasets/pairs_test.jsonl` — FROZEN
