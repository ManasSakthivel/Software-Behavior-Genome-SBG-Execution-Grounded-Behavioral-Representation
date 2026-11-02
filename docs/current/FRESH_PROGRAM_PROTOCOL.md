# Fresh-Program Collection Protocol
## Software Behavior Genome (SBG) — B02/B12 Specification

**Date:** 2026-10-26  
**Branch:** `remediation/sbg-v2`  
**Status:** SPECIFICATION COMPLETE — programs not yet written  
**This document must be frozen (hashed into FREEZE_V8.json) before any test data is generated.**

---

## 1. Why fresh programs are required

All 64 existing programs (benchmark/corpus, QuixBugs, BugsInPy, regression corpus) have been used in development — their per-pair scores have been committed and analysed. Using any of them in the confirmatory test set would mean the test set is contaminated. The confirmatory test set must consist entirely of programs that:

1. Have never been scored under any SBG protocol.
2. Were not used to choose the entry-point policy, thresholds, weights, or baselines.
3. Were not used to investigate the edit-size confound or any other methodological question.

---

## 2. Target population

**Independent Python programs at the function level** suitable for execution-grounded behavioral analysis. A program is in-scope if:

- It is a standalone Python module with at least one non-trivial, synthesisable function.
- It computes a deterministic, functional transformation of its inputs (i.e., given the same inputs, returns the same result across runs).
- It can be executed in Python 3.13 without external dependencies beyond the standard library.
- It is short enough to be evaluated within the tracer's event budget.
- Its primary function(s) can be called with inputs from the fixed battery (integers, floats, strings, booleans, lists, dicts, None — see `protocol.BATTERIES`).

---

## 3. Inclusion criteria (all must be satisfied)

1. **Single-function structure preferred:** the program has one clearly identifiable root function (the main computation). Multi-API programs are accepted only if `select_entry_structural` unambiguously selects one entry (i.e., it does not raise `AmbiguousEntryPoint`). Record the selected entry in the program manifest.
2. **Synthesisable parameters:** all required parameters of the selected entry function have battery-supported type annotations (`int`, `float`, `str`, `bool`, `list`, `dict`, `Optional[T]` where T is supported, `None`).
3. **Deterministic execution:** the program produces identical output for identical inputs across repeated calls. Programs involving randomness, threading, I/O, time, or network are excluded.
4. **Standard-library only:** no third-party imports. `import math`, `import collections`, `import itertools`, etc. are permitted.
5. **Non-trivial:** the function must contain at least one conditional branch and at least one loop or recursive call. Trivial one-liners are excluded.
6. **Novelty:** Jaccard token-overlap score ≤ 0.10 with every program in the existing benchmark (`benchmark/corpus/base_programs/`), the QuixBugs Python corpus, the BugsInPy corpus, and the regression programs.
7. **Provenance documented:** origin (authored, adapted, or public domain), license (if adapted), and any modifications documented in the program manifest.

---

## 4. Exclusion criteria

Any program is excluded if:

- It raises any exception on any of the standard battery inputs at the entry function.
- `select_entry_structural` raises `NoEntryPoint`, `AmbiguousEntryPoint`, or `UnsupportedSignature`.
- `data_integrity.py --strict` flags any pair generated from it.
- Jaccard overlap > 0.10 with any known program.
- It imports a third-party library.
- It is non-deterministic (randomness, time, I/O).
- Its output is a mutable side-effect with no return value (these produce empty traces).
- Its execution produces fewer than 5 distinct events in any trace (insufficient signal).

**Exclusion records:** Every excluded program and the reason for exclusion must be recorded in the dataset manifest. Do not count excluded programs toward the ≥50 total.

---

## 5. Independence unit

The independence unit is the **base program** — one Python module. Multiple pairs derived from the same base program are correlated and must be treated as one cluster for statistical analysis. Fresh programs and existing programs must not overlap at the program level.

Programs from the same source repository, tutorial series, or algorithm textbook chapter may be structurally similar. If two fresh programs share a data structure or algorithm concept and have Jaccard overlap > 0.10, only one is included. Record the overlap check result for every candidate.

---

## 6. Sample size

**Target: ≥20 evaluable programs in the held-out test set** (programs for which at least one pair is evaluated under `output_free_v8`). Under `STATISTICAL_PROTOCOL.md` §3, cluster bootstrap inference is unreliable for $k < 15$ program clusters. To provide adequate statistical power for cluster bootstrap confidence intervals without risking the $k < 15$ exploratory penalty, the test split must contain $\ge 20$ independent base programs.

To achieve $\ge 20$ evaluable test programs alongside adequately sized training (~45–50 programs for weight fitting), development (~15 programs for threshold derivation and model selection), and validation (~10 programs) sets, the total fresh corpus requires **≥100 written candidate programs** yielding **≥80–100 eligible programs**.

**Power analysis:** Run `benchmark/scripts/power_analysis.py` on the dev split per-program AUROC data before freezing. If the estimated power is < 80% for a ΔAUROC of 0.10 (the minimum meaningful effect), increase the program count. Do not freeze until adequate power is confirmed.

---

## 7. Development/test separation

The fresh programs must be assigned to train, dev, val, and test splits **before any evaluation is run**. The assignment algorithm is:

1. Stratify by category: sort programs by category (sort, string, math, graph, ds, other).
2. Assign splits 50/15/10/25 (train/dev/val/test) by category-stratified random assignment with seed 42.
3. Programs in the test split must never be scored, visualised, or used for any tuning decision until the protocol freeze is committed.
4. The split assignment is committed with the dataset manifest. It cannot be changed after any development data has been seen.

---

## 8. Label validation

All transformation-generated variants must pass the following checks before any pair is scored:

1. **Static syntax check:** `ast.parse()` succeeds.
2. **Compile check:** `compile()` succeeds (catches SP-3 scope errors).
3. **SP-2 reference check:** `data_integrity.py --strict` must exit 0 (0 dangling method references).
4. **Execution check for EQUIVALENT pairs:** run base and variant on all standard battery inputs; assert they return identical results. Any EQUIVALENT pair that fails execution must be flagged and excluded from the dataset.
5. **SC pair sanity:** a CHANGED pair must differ in output on at least one battery input (the mutation must be reachable). If no battery input witnesses the change, flag the pair as a potential hard-negative; include it in the dataset but label it `hard_negative=true`.

---

## 9. Transformation coverage

Each fresh program should receive all SP transformations (SP-1 through SP-12) and all SC mutations (SC-1 through SC-13) where applicable. The minimum per-program pair count is:
- ≥5 EQUIVALENT pairs (at least 5 distinct SP transformations succeed)
- ≥5 CHANGED pairs (at least 5 distinct SC mutations succeed)

Programs that produce fewer than 5 pairs in either class are excluded. Record the reason (no applicable mutation sites, no synthesisable parameters, etc.).

**SP-1 and SP-2: use `max_names=1`.** See `docs/current/EDIT_SIZE_REDESIGN.md`.

---

## 10. Transformation family balance

Across the full fresh dataset, each transformation type should have at least 10 pairs. This is a soft target; record actual counts in the manifest. If a transformation type has < 5 pairs, do not use it as the basis for per-family AUROC claims.

---

## 11. Dataset manifest

The dataset manifest (`benchmark/datasets/v7/manifest.json`) must contain:

```json
{
  "version": "v7",
  "generated_at": "<ISO-8601 timestamp>",
  "generator_commit": "<git SHA>",
  "generator_script": "benchmark/scripts/generate_v7_dataset.py",
  "sp1_max_names": 1,
  "sp2_max_names": 1,
  "n_programs": <count>,
  "n_programs_per_split": {"train": N, "dev": N, "val": N, "test": N},
  "n_pairs": <count>,
  "class_balance": {"EQUIVALENT": N, "CHANGED": N},
  "programs": {
    "<program_id>": {
      "split": "train|dev|val|test",
      "category": "<category>",
      "source": "<origin>",
      "license": "<license or 'authored'>",
      "entry_function": "<selected entry>",
      "entry_status": "ok|NoEntryPoint|AmbiguousEntryPoint|UnsupportedSignature",
      "n_equivalent_pairs": N,
      "n_changed_pairs": N,
      "jaccard_max_vs_known": <float>,
      "provenance_note": "<brief note>"
    }
  },
  "excluded_programs": [
    {"id": "<id>", "reason": "<exclusion reason>"}
  ],
  "sha256": {
    "pairs_train": "<sha256>",
    "pairs_dev": "<sha256>",
    "pairs_val": "<sha256>",
    "pairs_test": "<sha256>",
    "variants_tree_hash": "<sha256>"
  }
}
```

---

## 12. Freeze point

The fresh-program collection protocol is frozen when:

1. All programs are written with provenance documentation.
2. Jaccard overlap checks pass.
3. `generate_v7_dataset.py` has been run and `data_integrity.py --strict` exits 0.
4. Power analysis has been run on dev data and confirms ≥80% power.
5. τ* has been derived on the dev split under `output_free_v8`.
6. The manifest SHA-256 values are recorded.
7. **`FREEZE_V8.json` (complete, not template) is committed** before any test-split pair is evaluated.

The test split becomes off-limits the moment any development data is seen (step 4 above). If the power analysis fails, add more programs and re-run steps 1–6.

---

## 13. Sources for fresh programs

From `docs/current/FRESH_PROGRAM_SOURCES.md`, the following source families are identified:

| Source family | Type | Approximate programs available | Notes |
|---|---|---|---|
| Rosetta Code (CC0/MIT-compatible) | Algorithm implementations | ~30 | Screen for Python 3.13 compatibility; no stdlib |
| Exercism Python core exercises | Algorithm/data | ~20 | Adapt solutions; MIT license |
| LeetCode problems (authored solutions) | Algorithm | ~15 | Must be authored, not copied |
| Classic CS textbook algorithms | Algorithm | ~15 | Knuth, CLRS, Sedgewick; author from spec |
| Project Euler solutions (authored) | Math/number theory | ~10 | Author from spec; avoid IO-heavy problems |
| Cryptography primitives | Math | ~5 | Simple block cipher components, hash functions |
| Custom authored programs | Any | Unlimited | Primary source; no license concerns |

Preferred: author programs from scratch using algorithm specifications. This provides the strongest independence guarantee.

---

## 14. Progress tracking

| Phase | Status | Completion criterion |
|---|---|---|
| Protocol specification (this document) | ✅ COMPLETE | Specification frozen before any programs written |
| Decision D1 (max_names=1) | ✅ DECIDED | Documented in EDIT_SIZE_REDESIGN.md |
| Decision D2 (Option 1 primary) | ✅ DECIDED | Documented in CLASS_DRIVER_POLICY.md |
| Fresh programs written | ❌ 0/≥50 | ≥50 programs passing all inclusion criteria |
| Jaccard overlap screen | ❌ Not run | All programs pass Jaccard ≤ 0.10 |
| Dataset generation | ❌ Not run | generate_v7_dataset.py → data_integrity.py --strict exits 0 |
| Power analysis | ❌ Not run | ≥80% power at ΔAUROC=0.10 |
| Dev threshold derivation | ❌ Not run | τ* committed |
| Protocol freeze (FREEZE_V8.json) | ❌ Not created | FREEZE_V8.json committed before test scoring |
| Test evaluation | ❌ Not run | One run of make v7-train v7-fit v7-test |
