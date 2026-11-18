# V7-B changelog: Phase 1 to Phase 2

Branch `research/v7b-final-validation`. Commit hashes are from `git log --oneline`. Everything is local, macOS only and exploratory.

## Phase 1 (V7-B build and first exploratory results)
- `18bac42f` core verdict engine, evidence log, CLI (54 tests). `c0e833de` isolated child-process runner (macOS), security audit. `6ef6a675` benchmark inventory and independence audit. `f8c81bba` literature review and novelty assessment. `caa0012e` K1/K2 feasibility spike (K1 not met). `d939c83b` baselines B1-B5 on development pairs. `0cfbbfcc` statistical analysis plan and scripts. `700532b8` fix NO_RUN not blocking `NO_DIVERGENCE_OBSERVED` (red-team B-1). `d3dc0506` independent red-team review. `ec962eec` post-fix rerun (3 verdicts changed). `a55b7770` manuscript draft (never compiled). `34884636` readiness report. `94f2d391` README rewrite, REPRODUCIBILITY, datasets README. `846db4de` macOS `killpg` guard.
- Phase 1 closure: `543e2cd3`, `3f140af2` (legacy README-splice target disabled), `27765f5d` (Makefile venv default, docs check), `02ed478e`, `e1d7fc2e`.

## Phase 2 (implementation, specification closure, local experiments)
| Commit | Change |
|---|---|
| `1206312e` | `--help` of `k1_spike.py` and `sbgv7.baselines.run` exits 0 without work; unknown or missing command exits 2 |
| `865bfaea` | conformance audit and reconciled R1 design documents with index |
| `8f11d3aa` | D-01: dict-subclass and `__slots__` canonicalisation; D-02: HMAC-authenticated result frame on a dedicated pipe, real tamper signal (`unsafe_program`); 48 regression tests |
| `cc56e029` | lossy `SAME` is not evidence; docstring-only changes recognised; invalid-input binding is not a `SAME`; evidence package with sources and inputs; `python -m sbgv7 verify` |
| `c1b6ccb8` | literature review extended (185 rows), related-work chapter, novelty reclassification |
| `f2aa9143` | requirements traceability matrix, final specification decisions, K1/K5 decision, mandatory backlog |
| `5efcef74` | MB-01..MB-16: huge ints compared exactly, fd-1 output folded in, source-path normalisation, explicit invariants, replay/alt runs checked, child hash seed actually pinned (`-I` replaced by `-s -P -B` plus an environment allowlist), required-versus-advisory isolation properties, no-overwrite and identity policy, Merkle `run_set_root`, constant config keys, CLI exit codes (compare 0/1/2/3; verify 0/1/2/4), V6 digest; 276 passed, 1 skipped in `tests/v7` |
| `a6afa639` | local experiment rerun matrix (plan only) |
| `aea4202c` | E1 K2 determinism re-measurement report (414/414 verified); E3-E7 pre-registration and drivers |
| `0b957d4f` | recomputed traceability (135 rules: 78/30/7/14/2/4) and reconciliation of earlier counts; single risk register |
| `ee4749bc` | novelty reassessment (`research/literature/NOVELTY_REASSESSMENT_PHASE2.md`); risk register wording fix |
| `debc4396` | E3-E7 executed and verified; consolidated experimental analysis; compact summaries in `results/v7b_phase2_summary/` (raw archived outside git) |

## Behavioural changes that alter old numbers
Old-engine figures (`results/postfix`, `results/processed`, `research/evaluation/*`, the manuscript tables) are historical; they must not be cited for the current engine.
- Child interpreter profile `-I` to `-s -P -B` with `PYTHONHASHSEED=0` really in effect (before: random hash seed per child).
- Conservative `unmodelled_change` rule: 54 pairs moved to `INSUFFICIENT`; abstention 0.360 to 0.473 with unchanged detection (0.708) and false assurance (0.123).
- 63 of 312 driven verdicts changed versus the old engine; `DIVERGENT_OBSERVABLE` unchanged at 84.
- `pair_id` now covers repeat, sufficiency and policy ids (budget excluded); `NO_RUN` carries a reason; CPU budget charges parent CPU.

## Documentation changes in this documentation pass
README, REPRODUCIBILITY and datasets README updated for Phase 2; new guides: `PHASE2_REPRODUCTION_GUIDE.md`, `EXPERIMENT_PROTOCOL.md`, `DATASET_PROVENANCE.md`, `FAILURE_MATRIX.md`, `VERDICT_INTERPRETATION.md`, `DOCUMENTATION_RECONCILIATION_INDEX.md`; stale statements in `docs/architecture/V7B_IMPLEMENTATION.md` corrected. No code, test or result was changed.
