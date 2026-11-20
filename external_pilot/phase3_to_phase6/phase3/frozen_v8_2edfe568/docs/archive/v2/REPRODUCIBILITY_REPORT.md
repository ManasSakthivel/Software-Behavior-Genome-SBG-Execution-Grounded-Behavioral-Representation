# SBG V2 — Reproducibility Report

*Agent N: Reproducibility Audit — generated from source inspection*

---

## 1. Environment Requirements

| Requirement | Value |
|---|---|
| Python | >= 3.9 |
| External dependencies | **NONE** — stdlib only |
| OS | Linux / macOS (Windows untested) |
| RAM | ~256 MB for full baseline sweep |
| Disk | ~50 MB (code + artifacts) |
| Estimated wall time | ~15–30 min for full pipeline on a modern laptop |

All computation uses pure Python standard library. No `pip install` is required.

---

## 2. Random Seeds

All sources of randomness are seeded deterministically:

| Seed usage | Value | Location |
|---|---|---|
| Global / split assignment | 42 | `artifacts/final/FINAL_REPRODUCIBILITY_MANIFEST.json` |
| Bootstrap CI (F1, AUROC) | 42 | `baselines/common.py` → `random.Random(42)` |
| Permutation test | 42 | `artifacts/final/FINAL_REPRODUCIBILITY_MANIFEST.json` |
| SandboxRunner per-run seed | 42 | `baselines/v2/b07_dynamic_v2.py` → `_runner.run(..., seed=42)` |
| All REGISTRY.yaml experiments | 42 | `experiments/REGISTRY.yaml` (each entry: `seed: 42`) |

Bootstrap uses 1 000 resamples with `random.Random(42)` in [`baselines/common.py`](../../baselines/common.py).

---

## 3. Exact Reproduction Commands

### 3.1 Regenerate benchmark corpus

```bash
cd /path/to/SBG
python3 benchmark/scripts/generate_benchmark.py
python3 benchmark/scripts/validate_benchmark.py
```

Expected output from `validate_benchmark.py`:
- 0 base-program leakage across splits
- Diversity score ≥ 0.85
- Pair counts: Train 2 278 | Dev 615 | Val 540 | Test 744

### 3.2 Reproduce Phase 3 baselines (B01–B08)

```bash
python3 baselines/run_all_baselines.py
```

Or individually:

```bash
python3 baselines/b01_token.py        # EXP-B01: Token TF-IDF
python3 baselines/b02_ast.py          # EXP-B02: AST similarity   ← best baseline
python3 baselines/b03_cfg.py          # EXP-B03: CFG structure
python3 baselines/b04_dependency.py   # EXP-B04: Dependency approx
python3 baselines/b05_embedding.py    # EXP-B05: Embedding fallback (subword TF-IDF)
python3 baselines/b06_dynamic.py      # EXP-B06: Dynamic trace
python3 baselines/b07_static_sbg.py   # EXP-B07: Static SBG
python3 baselines/b08_full_sbg.py     # EXP-B08: Full SBG
```

### 3.3 Reproduce Phase 4 experiments (E1–E12)

```bash
python3 experiments/phase4/e1_equivalence_detection.py
python3 experiments/phase4/e2_mutation_detection.py
python3 experiments/phase4/run_phase4_gate.py
```

All 12 experiment scripts live in `experiments/phase4/`.

### 3.4 Reproduce V2 dynamic baseline (B07-v2)

```bash
python3 baselines/v2/b07_dynamic_v2.py
```

> ⚠ **SAFEGUARD-6 VIOLATION** — see Section 5.

### 3.5 Run test suite

```bash
python3 -m pytest sbg/ benchmark/ground_truth/ -v
```

Expected: 653 tests, all pass.

### 3.6 Run reproducibility audit

```bash
python3 experiments/v2/reproducibility_check.py
```

Writes `artifacts/v2/REPRODUCIBILITY_AUDIT.json`.

### 3.7 Generate final artifacts

```bash
python3 phase7/generate_final_artifacts.py
```

---

## 4. Expected Output Metrics (±0.001 tolerance)

### Primary headline results

| Experiment | Metric | Expected value | Tolerance |
|---|---|---|---|
| EXP-B02 (AST) | Test AUROC | 0.5528 | ±0.001 |
| EXP-B02 (AST) | Test F1 | 0.6595 | ±0.001 |
| EXP-B08 (Full SBG) | Test AUROC | 0.4237 | ±0.001 |
| EXP-B08 (Full SBG) | Test F1 | 0.6595 | ±0.001 |
| EXP-B07 (Static SBG) | Test AUROC | 0.3491 | ±0.001 |
| EXP-B01 (Token) | Test AUROC | 0.4043 | ±0.001 |
| EXP-B03 (CFG) | Test AUROC | 0.4613 | ±0.001 |
| EXP-B04 (Dep) | Test AUROC | 0.3993 | ±0.001 |
| EXP-B05 (Embed) | Test AUROC | 0.3694 | ±0.001 |
| EXP-B06 (Dynamic) | Test AUROC | 0.5046 | ±0.001 |

### Key structural-semantic inversion values

| Measure | Expected | Source |
|---|---|---|
| SP transforms mean SBG similarity (SP-1) | 0.84 | README.md |
| SC mutations mean SBG similarity (SC-3) | 1.00 | README.md |
| SC mutations near-identical fraction | 99.18% | README.md |

### Bootstrap CI (B02, B08)

| Baseline | AUROC 95% CI lower | AUROC 95% CI upper |
|---|---|---|
| B02 AST | 0.509 | 0.594 |
| B08 Full SBG | 0.375 | 0.472 |

CIs are computed with `random.Random(42)`, 1 000 resamples.
They may differ by ≤ 0.002 on different Python patch versions due to `random` PRNG implementation details.

---

## 5. Known Violations and Non-Reproducible Aspects

### 5.1 ⚠ SAFEGUARD-6 VIOLATION — `b07_dynamic_v2.py` n_runs=1

**File:** [`baselines/v2/b07_dynamic_v2.py`](../../baselines/v2/b07_dynamic_v2.py) line 132

```python
result = _runner.run(program_id, fn_to_trace, inputs_to_use, n_runs=1, seed=42)
```

**Requirement:** SAFEGUARD-6 requires `n_runs >= 5` for a valid noise floor estimate.
`SandboxRunner.run()` defaults to `n_runs=5` and explicitly documents this in its docstring.

**Impact:**
- With `n_runs=1`, `_compute_noise_floor()` computes std over a single sample → std = 0.0 for all features.
- `non_deterministic_flags` will always be `[]` regardless of actual program non-determinism.
- Noise floor check is vacuous: SAFEGUARD-6 cannot fire, making the safeguard inoperative for B07-v2 results.
- Any reported noise floor stats in `artifacts/v2/B07/` cannot be trusted.

**Remediation (out of scope for this audit):** Change the call to `n_runs=5`.

### 5.2 Timing-dependent non-reproducibility

Dynamic tracing uses a 5-second timeout per trace (`SandboxRunner` / v1 `Tracer`).
On slower hardware, programs near the timeout boundary may flip between completing and
timing out, producing different `timeout_fraction` values and different genome features.

**Affected:** `EXP-B06` (Dynamic Trace), `EXP-B08` (Full SBG dynamic dims), `b07_dynamic_v2.py`.

### 5.3 Java cross-language validation (Phase 5) — manual only

Java programs in Phase 5 cannot be executed in this environment.
Cross-language results (`artifacts/phase5/cross_language_results.json`) are validated
by manual inspection only (n=15 pairs).

**Impact:** H4 (language-agnostic) remains NOT EVALUABLE computationally.

### 5.4 B05 Embedding baseline is a fallback

B05 uses subword n-gram TF-IDF because `torch`/`transformers` are unavailable.
A true CodeBERT comparison would require:
```bash
pip install torch transformers
python3 baselines/b05_embedding.py  # would then use real CodeBERT
```
Results with CodeBERT would differ from the reported AUROC=0.3694.

### 5.5 Artifact hash prefixes (16-hex) vs full SHA-256

`FINAL_REPRODUCIBILITY_MANIFEST.json` stores 16-character SHA-256 prefixes.
The audit script (`reproducibility_check.py`) verifies that freshly computed SHA-256
hashes start with the declared prefix. Full collision probability is negligible (2^−64).

---

## 6. Artifact Hash Manifest

The following files have declared SHA-256 prefixes in
[`artifacts/final/FINAL_REPRODUCIBILITY_MANIFEST.json`](../../artifacts/final/FINAL_REPRODUCIBILITY_MANIFEST.json):

| Artifact | Declared SHA-256 prefix |
|---|---|
| `artifacts/research/PHASE_0_GATE.json` | `c5e33166a2b6432d` |
| `artifacts/research/PHASE_1_GATE.json` | `407f8927d954efc1` |
| `artifacts/research/PHASE_2_GATE.json` | `f88bebd7e02020a6` |
| `artifacts/research/PHASE_3_GATE.json` | `4d78fa6ea25731d8` |
| `artifacts/research/PHASE_4_GATE.json` | `8e8f414753ce7ef1` |
| `artifacts/research/PHASE_5_GATE.json` | `7a0697655340128d` |
| `artifacts/research/PHASE_6_GATE.json` | `6652ba86dfade918` |
| `artifacts/phase3/B02/results_test.json` | `6d87c16bb958343b` |
| `artifacts/phase3/B08/results_test.json` | `efe00bff25e73747` |
| `artifacts/phase4/E1/results.json` | `e0fa9acca567a11d` |
| `artifacts/phase4/E2/results.json` | `ce5f300269ff36ee` |
| `artifacts/phase4/E6/results.json` | `b5c8cb99cc68a0b4` |
| `artifacts/phase4/E7/results.json` | `c76c591015128b70` |
| `artifacts/phase4/E12/results.json` | `69149bcc9c3cb16b` |
| `docs/CLAIMS_REGISTRY.yaml` | `946d8d3f7f2e299c` |

Run `python3 experiments/v2/reproducibility_check.py` to verify all hashes live.

---

## 7. Anti-Reproducibility Pattern Scan

Scan performed across: `baselines/`, `sbg/`, `experiments/`, `benchmark/scripts/`

| Pattern | Hits in source | Notes |
|---|---|---|
| `MOCK_RESULT` | 0 | Clean |
| `FAKE_RESULT` | 0 | Clean |
| `HARDCODED_RESULT` | 0 | Clean |
| `PLACEHOLDER` | 0 | Clean |
| `READY_FOR_LINUX` | 0 | Clean |
| `PENDING` | 300+ | **All in benchmark domain data** (`OrderState.PENDING`) — not code flags |
| `TODO` / `FIXME` | 0 | Clean (in source, not benchmark data) |

No synthetic or hardcoded results were found in the source or experiment code.

---

## 8. Dependency Specification

```
Python >= 3.9
Standard library only:
  ast, hashlib, json, math, pathlib, random, re, sys, time,
  collections, dataclasses, importlib, inspect, io, types, typing
```

No `requirements.txt` or `pyproject.toml` is needed.
Reproducibility is fully achieved with a clean Python 3.9+ installation.

---

## 9. Computation Time Estimates

| Step | Estimated time | Notes |
|---|---|---|
| `generate_benchmark.py` | < 1 min | Pure AST transforms |
| `validate_benchmark.py` | < 30 s | File checks |
| `baselines/b01_token.py` | ~2 min | Token similarity on 1 359 pairs |
| `baselines/b02_ast.py` | ~30 min | AST edit distance — 37.9 ms/pair |
| `baselines/b03_cfg.py` | ~3 min | CFG structure |
| `baselines/b04_dependency.py` | ~3 min | Use-def approx |
| `baselines/b05_embedding.py` | ~3 min | Subword TF-IDF |
| `baselines/b06_dynamic.py` | ~15 min | Dynamic trace with 5 s timeout |
| `baselines/b07_static_sbg.py` | ~5 min | Static SBG, 3.75 ms/pair |
| `baselines/b08_full_sbg.py` | ~20 min | Full SBG + dynamic dims |
| `experiments/phase4/` (all) | ~10 min | Statistical analysis |
| Test suite | ~2 min | 653 tests |
| **Total** | **~90 min** | Serial execution |

---

*Made with IBM Bob*
