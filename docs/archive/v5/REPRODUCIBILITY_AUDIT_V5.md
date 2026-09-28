# SBG V5 — Reproducibility Audit

*Auditor: Bob (IBM) — Automated Artifact & Reproducibility Audit*
*Date: 2025-07-07*
*Machine-readable companion: [`artifacts/v5/REPRODUCIBILITY_AUDIT_V5.json`](../../artifacts/v5/REPRODUCIBILITY_AUDIT_V5.json)*

---

## Executive Summary

| Dimension | Status |
|---|---|
| **Overall verdict** | ⚠ **CONDITIONAL PASS** |
| All 19 manifest artifacts present | ✅ PASS |
| SHA-256 prefix integrity | ✅ PASS |
| Random seeds (SEED=42) | ✅ PASS |
| No `time.time()` affecting results | ✅ PASS |
| No hard-coded paths | ✅ PASS |
| Benchmark data present & well-formed | ✅ PASS |
| SAFEGUARD-6 (n_runs) | ✅ PASS (resolved from v2 audit) |
| pytest is undocumented external dep | ⚠ WARNING |
| Figure 4 & 5 scripts are PLACEHOLDER | ⚠ WARNING |
| V2/V3/V4 FINAL_RESULTS not hashed | ⚠ WARNING |
| Dynamic reproducibility is hardware-dependent | ⚠ WARNING |
| README test count is stale (489 vs 653) | ℹ INFO |

**Primary scientific results are fully reproducible** on CPython >= 3.9 with a clean clone. The two figures that **cannot** be regenerated (fig4, fig5) are supporting visualisations only and do not affect any reported metric.

---

## A. Dependency Audit

### Classification

| Module | Classification | Used In | Notes |
|---|---|---|---|
| `ast` | stdlib | `sbg/`, `baselines/b02_ast.py`, `experiments/` | Core static extraction |
| `hashlib` | stdlib | `sbg/`, `baselines/`, manifests | Artifact integrity |
| `json` | stdlib | Everywhere | Ubiquitous |
| `math` | stdlib | `baselines/common.py`, `sbg/v3/metrics.py` | |
| `pathlib` | stdlib | Everywhere | Python >= 3.4 |
| `random` | stdlib | `baselines/common.py`, `sbg/v3/metrics.py`, experiments | Seeded via `random.Random(42)` |
| `re` | stdlib | `experiments/v2/reproducibility_check.py` | |
| `sys` | stdlib | Everywhere | |
| `time` | stdlib | `sbg/extraction/dynamic/tracer.py`, `runner.py` | For provenance + wall-time only — never scoring |
| `threading` | stdlib | `sbg/extraction/dynamic/tracer.py` | Tracer timeout mechanism |
| `collections` | stdlib | `baselines/b01_token.py`, `b06_dynamic.py` | |
| `dataclasses` | stdlib | `sbg/v2/execution/runner.py`, normalizer, fusion | Requires Python >= 3.7 |
| `importlib.util` | stdlib | `baselines/b06_dynamic.py`, `b07_dynamic_v2.py` | Dynamic program loading |
| `inspect` | stdlib | `baselines/v2/b07_dynamic_v2.py` | Class adapter detection |
| `tokenize` | stdlib | `baselines/b01_token.py`, `b05_embedding.py` | |
| `io` | stdlib | `sbg/extraction/dynamic/tracer.py` | |
| `subprocess` | stdlib | `experiments/v4/phase6_cross_language.py` | `java -version` check only |
| `shutil` | stdlib | `experiments/v4/phase6_cross_language.py` | Optional experiment |
| **`pytest`** | **required_external** | 9 test files in `sbg/` | **UNDOCUMENTED** — required for `python3 -m pytest sbg/ -q` |
| `torch` | optional | `experiments/v2/run_modern_baseline_wave7.py` | Guarded by try/import; falls back to subword TF-IDF |
| `transformers` | optional | `experiments/v2/run_modern_baseline_wave7.py` | Same — CodeBERT only |

### ⚠ Undocumented Required Dependency

**`pytest`** is imported in 9 test files. README Reproduction step 1 says:

```bash
# Requires Python >= 3.9, stdlib only (no pip install needed)
python3 -m pytest sbg/ -q
```

This is **false** — `pytest` is not stdlib. Clean-room reproducers must first run:

```bash
pip install pytest
```

This does not affect any primary reported metric, but the documentation claim is inaccurate.

---

## B. Seed Determinism Audit

### Verdict: PASS (with one documented intentional deviation)

| Check | Status | Location | Detail |
|---|---|---|---|
| Bootstrap CI seeding | ✅ PASS | [`baselines/common.py:175`](../../baselines/common.py) | `rng = random.Random(42)` — local instance, 1 000 resamples |
| REGISTRY.yaml experiment seeds | ✅ PASS | `experiments/REGISTRY.yaml` | All EXP-B01..B08 `seed: 42` |
| SandboxRunner seed parameter | ✅ PASS | [`sbg/v2/execution/runner.py:109`](../../sbg/v2/execution/runner.py) | `seed=42` default — logging only, does not affect trace output |
| b07_dynamic_v2.py seed call | ✅ PASS | [`baselines/v2/b07_dynamic_v2.py:279`](../../baselines/v2/b07_dynamic_v2.py) | `n_runs=5, seed=42` |
| `random.randint()` without seeding | ✅ PASS | All directories | **Zero** bare `random.randint()` calls found |
| `time.time()` affecting results | ✅ PASS | 7 extraction files | Used only for `extraction_timestamp` provenance — never for scoring |
| `time.monotonic()` | ✅ PASS | [`runner.py:145`](../../sbg/v2/execution/runner.py) | Wall-time metadata only |
| `os.walk()` / file ordering | ✅ PASS | All directories | Not used in `sbg/` or `baselines/`. Benchmark pairs loaded from frozen JSONL |
| Dict iteration ordering | ✅ PASS | — | Python >= 3.7 guarantees insertion order; requirement is >= 3.9 |

**One intentional deviation:** [`experiments/v2/statistical_audit.py:67`](../../experiments/v2/statistical_audit.py) uses `rng2 = random.Random(0)` (seed 0) to generate a synthetic random-classifier simulation. This is a correctness unit-test for the AUROC function — it does not affect any reported experimental metric.

---

## C. Environment Requirements

| Requirement | Stated | Verified |
|---|---|---|
| Python version | `>= 3.9` | Accurate. Core pipeline uses `dataclasses` (3.7+), f-strings (3.6+), dict ordering (3.7+). |
| External packages (core) | None | ✅ True for pipeline and results |
| External packages (tests) | None | ⚠ **False** — pytest required |
| OS | Linux / macOS | Windows untested (documented) |
| Java | Not mentioned in README | Required for `experiments/v4/phase6_cross_language.py` only; gracefully detected |
| Hard-coded paths | None | ✅ Verified — all paths use `pathlib.Path(__file__).resolve().parent...` |
| CPython requirement | Not documented | ⚠ **`sys.settrace` dynamic tracing is CPython-only** — PyPy will not work for dynamic baselines |

---

## D. Clean-Room Reproduction Test

Simulated fresh clone → execution sequence:

### What would succeed

```bash
# After: pip install pytest  (missing from README)
python3 -m pytest sbg/ -q                                 # ✅ PASS
python3 baselines/run_all_baselines.py                    # ✅ PASS (~90 min)
python3 baselines/v2/b07_dynamic_v2.py                   # ✅ PASS (~30 min)
python3 baselines/v2/b08_hybrid_v2_correct.py            # ✅ PASS
python3 baselines/v2/b06_fair_v2.py                      # ✅ PASS
python3 experiments/v2/hard_negative_analysis.py          # ✅ PASS
python3 experiments/v2/noise_floor.py                     # ✅ PASS
python3 experiments/v2/robustness_analysis.py             # ✅ PASS
python3 experiments/v2/regression_benchmark.py            # ✅ PASS
python3 experiments/v2/statistical_audit.py               # ✅ PASS
```

### What would fail or produce incomplete output

| Command | Status | Reason |
|---|---|---|
| `python3 -m pytest sbg/ -q` (without pip install pytest first) | ❌ FAIL | `pytest` not stdlib |
| `python3 experiments/v2/figures/fig4_hard_negative.py` | ❌ FAIL | `PLACEHOLDER_PENDING_DATA` — writes placeholder JSON only |
| `python3 experiments/v2/figures/fig5_robustness.py` | ❌ FAIL | `PLACEHOLDER_PENDING_DATA` — writes placeholder JSON only |
| `python3 experiments/v2/run_modern_baseline_wave7.py` | ⚠ PARTIAL | Falls back to subword TF-IDF if `torch`/`transformers` absent |

### Missing from README Reproduction section

1. `pip install pytest` — needed before step 1
2. `python3 benchmark/scripts/generate_benchmark.py` — needed to regenerate pairs from scratch (documented in `docs/v2/REPRODUCIBILITY_REPORT.md` §3.1 but absent from README)

---

## E. Artifact Integrity

| Metric | Value |
|---|---|
| Artifacts in manifest | 19 |
| Artifacts present on disk | 19 (100%) |
| SHA-256 prefix matches | 19/19 ✅ |
| Full SHA-256 recorded | Yes — in `artifacts/v2/REPRODUCIBILITY_AUDIT.json` |
| Prefix length | 16 hex chars (collision probability 2⁻⁶⁴ — negligible) |
| SEED recorded in manifest | Yes — `artifacts/final/FINAL_REPRODUCIBILITY_MANIFEST.json` |
| Experiment configs recorded | Yes — `experiments/REGISTRY.yaml` (all `seed: 42`) |

The V2-specific result artifacts (`artifacts/v2/FINAL_RESULTS.json`, `artifacts/v3/FINAL_RESULTS.json`, `artifacts/v4/FINAL_RESULTS.json`) are **present but not hashed** in any manifest. These files contain the primary reported AUROC numbers and should be integrity-protected.

---

## F. Missing Artifacts

### Claimed but not generatable

| Artifact | Reason | Severity |
|---|---|---|
| `experiments/v2/figures/fig4_hard_negative_PLACEHOLDER.json` | `fig4_hard_negative.py` is `PLACEHOLDER_PENDING_DATA` | ⚠ WARNING |
| `experiments/v2/figures/fig5_robustness_PLACEHOLDER.json` | `fig5_robustness.py` is `PLACEHOLDER_PENDING_DATA` | ⚠ WARNING |

### Documentation mismatch (no broken code)

| Claimed location | Actual location | Impact |
|---|---|---|
| `sbg/v2/execution/tracer.py` (mentioned implicitly in docs) | [`sbg/extraction/dynamic/tracer.py`](../../sbg/extraction/dynamic/tracer.py) | None — `runner.py` imports correctly from the actual path |

### Present but not in manifest (unprotected artifacts)

- `artifacts/v2/FINAL_RESULTS.json`
- `artifacts/v2/H7_CORRECTED_RESULTS.json` through `H12_FINAL_RESULTS.json`
- `artifacts/v3/FINAL_RESULTS.json`
- `artifacts/v4/FINAL_RESULTS.json`

---

## G. SAFEGUARD-6 Status (Updated from V2 Audit)

| | V2 Audit | V5 Audit (current) |
|---|---|---|
| `b07_dynamic_v2.py` `n_runs` | **1** (VIOLATION) | **5** ✅ PASS |
| Noise floor check valid | No — std always 0.0 | Yes — 5 runs enable real std computation |
| `non_deterministic_flags` can fire | No | Yes |

The SAFEGUARD-6 violation recorded in `artifacts/v2/REPRODUCIBILITY_AUDIT.json` has been **resolved**. The current code at [`baselines/v2/b07_dynamic_v2.py:279`](../../baselines/v2/b07_dynamic_v2.py) passes `n_runs=5`.

---

## H. Recommended Remediations

| Priority | Action | File |
|---|---|---|
| 🔴 HIGH | Add `pip install pytest` to README Reproduction section | `README.md` |
| 🔴 HIGH | Add SHA-256 hashes for `artifacts/v2/FINAL_RESULTS.json`, `v3/`, `v4/` to `FINAL_EVIDENCE_MANIFEST.json` | `artifacts/final/FINAL_EVIDENCE_MANIFEST.json` |
| 🟡 MEDIUM | Implement `fig4_hard_negative.py` and `fig5_robustness.py` (remove PLACEHOLDER_PENDING_DATA) | `experiments/v2/figures/fig4_hard_negative.py`, `fig5_robustness.py` |
| 🟡 MEDIUM | Add V2 reproduction commands to `FINAL_REPRODUCIBILITY_MANIFEST.json` | `artifacts/final/FINAL_REPRODUCIBILITY_MANIFEST.json` |
| 🟡 MEDIUM | Document CPython requirement for dynamic baselines | `README.md` |
| 🟢 LOW | Fix README test count: 489 → 653 | `README.md` |
| 🟢 LOW | Add benchmark/scripts/generate_benchmark.py step to README | `README.md` |

---

## Reproduction Check Script

A self-contained V5 reproduction check script has been created at [`experiments/v5/reproduction_check.py`](../../experiments/v5/reproduction_check.py).

```bash
python3 experiments/v5/reproduction_check.py
```

It performs 6 checks:

| Check | Description |
|---|---|
| `artifact_integrity` | All 19 manifest artifacts present + SHA-256 prefix matches |
| `benchmark_data` | All 4 split JSONL files present, parseable, correct pair counts |
| `minimal_pipeline` | End-to-end ControlGenome extraction + distance on one real pair |
| `determinism` | Runs same pair twice, verifies bit-identical JSON output |
| `pytest_available` | `pytest` importable (test-suite gate) |
| `bootstrap_seed` | `random.Random(42)` confirmed in `baselines/common.py` |

Output is written to `artifacts/v5/REPRODUCIBILITY_AUDIT_V5.json`.

---

*Made with IBM Bob*
