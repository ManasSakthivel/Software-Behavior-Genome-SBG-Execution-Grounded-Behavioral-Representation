# 03 V7-B capability and gap audit (for V8)

Basis: HEAD `8bd7d9da` (branch `research/v7b-final-validation`), sources read in this sprint: `sbgv7/decide.py`, `runner.py` (`finalize`, `_static_branches`), `config.py`, `harness.py` (branch/line monitors), `records.py`, plus `reports/phase2/PHASE2_CONSOLIDATED_EXPERIMENTAL_ANALYSIS.md` and `PHASE2_FINAL_RED_TEAM_REVIEW.md`. V7-B stays the historical baseline; V8 is additive (new package, V7-B files untouched).

## Capability inventory
| Capability | What it actually measures | Where | Evidence recorded | Assumptions | Cannot measure | V8 use |
|---|---|---|---|---|---|---|
| Changed-region activation | Fraction of changed executable lines (per side) hit by deterministic, clean, non-lossy SAME inputs | `runner.finalize` (hit_units, units_total); `decide._blockers` | SufficiencyRecord `units_hit/units_total/unhit` | Changed lines from AST diff; docstring/non-executable lines -> `unmodelled_change` | Whether the activated code influences any recorded observation | Reuse as D1 |
| Branch-direction coverage on changed lines | `min(2,|directions seen|)/2` per static branch instruction on changed lines, per side (`runner.py:333-335`) | `runner.finalize`, `harness.on_branch` | `branch_cov` per side | sys.monitoring BRANCH events, Python 3.12+ | Coverage of unchanged code; path/condition combinations | Reuse as D1; floor 0.8 is an unvalidated default |
| Fixed sufficiency gate S1/S2 | S1: no blockers; S2: S1 and branch_cov >= floor both sides, non-lossy SAME, channels instrumented (`decide.sufficiency`) | `decide.py:65-75` | floors dict | `s2_all_channels_instrumented` is a hard-coded `True` (decide.py:72) | Anything probabilistic; it only labels S1/S2 and never changes whether NDO is issued (verdict is NDO iff no witness and no blocker) | S1/S2 become baseline 3; NOT a calibrated risk |
| Reproducibility (determinism, replay, alt) | `r_det` repeats, `r_replay` fresh runs per side, `k_alt` RNG/time/urandom-shifted controls; QUARANTINED/flaky -> INSUFFICIENT | `runner.py` | Run records | Hash seed fixed; `datetime.now` not virtualised | Hash-order sensitivity; wall-clock dependence | Reuse as D4 |
| Observation / lossy detection | Lossy or degenerate SAME is not evidence (A-L1) | `finalize`, harness canonicalisation | `lossy` flag | Canonicaliser covers value kinds | Which channels a program could have observed but did not | Partial D3 |
| Witness confirmation | CONFIRMED_DIFF needs repeat, replay and alternate confirmation | `runner`, `decide` | Witness records | As above | Independent re-derivation of the observation by a trusted collector | Reuse |
| Evidence log + verify | Hash-chained log; `verify` recomputes verdict from recorded facts, executes nothing | `records.py`, `verify.py` | evidence.jsonl | Log written by the same process tree as the program under test | Tamper-proofness; red-team probe forged a verdict from inside the program | V8-A replaces collection (Phase 3) |
| Budget / limits | CPU/wall caps, budget stop | `config.py`, `runner.py` | stop_reason | Local macOS sandbox | Linux isolation | Reuse |

## Not present in V7-B (searched `sbgv7/`, `docs/`, `reports/phase2/`)
- Checked/behavioural influence (no dynamic slicing or dependence tracking: `grep` finds no slice/influence code).
- Evidence provenance and independence (inputs carry no provenance class; label-derived inputs are not distinguished).
- Input diversity / effective number of distinct behaviours.
- Any probability, calibration, or risk estimate (`decide` returns discrete values only).
- Intervention operators (deletion, duplication, masking). `finalize` is pure (runner.py:317 "Pure: everything after the runs"), which makes post-hoc evidence perturbation implementable without re-execution.
- Per-input recorded hits exist (`parts=[(InputEv, hits, branches)]`), so multiplicity of coverage per changed unit is computable from recorded data.

## Fixed gate vs calibrated risk vs guarantee vs equivalence
1. Fixed rule gate (V7-B): deterministic thresholds; says nothing about error frequency.
2. Calibrated risk estimate (V8 target): a model whose predicted false-assurance probability agrees with observed frequencies on held-out projects.
3. Statistical guarantee: a bound with stated assumptions (exchangeability, monotone loss, marginal expectation) which a convenience benchmark may not satisfy.
4. Equivalence proof: not available and never claimed (no equivalence verdict exists).

## Phase 2 evidence that motivates V8 (development data; hypothesis-generating only)
Using E3 outputs (258 labelled pairs, project-clustered; red-team recomputed): wrong share among issued NDO verdicts is 13/61 = 0.213 for V7-B versus 24/130 = 0.185 for B1; by level S1 5/16, S2 8/45. The false-assurance reduction versus B1 was entirely abstention (11 of 11). V7-B's abstention is selective (11/24 B1 false assurances vs 7/82 detections abstained, Fisher p ~ 1e-4), so the evidence profile carries some information, but the fixed gate did not make NDO verdicts more reliable. These are exactly the observations CEC is designed to test; they come from design-exposed data and cannot support a V8 claim.

## Reuse map
Reuse unchanged: `finalize` pure core, `decide`, records, verify, config. Modify (additively, in a new package): harness extension for influence capture, recorded-evidence loader. Unsuitable for V8: the hard-coded `s2_all_channels_instrumented`, the single-number floor, in-process evidence collection.
