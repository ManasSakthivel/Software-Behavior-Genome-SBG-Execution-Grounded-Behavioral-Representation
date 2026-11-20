# V8 Mac: eligibility-pool policy review (DEVELOPMENT DATA, EXPLORATORY, NOT INDEPENDENT VALIDATION)

Run: `results/v8_mac_reanalysis_20261118_210512/` (policies `v8.0`, `v8.1`; 312 records, 258 y-known, 101 projects; records md5 `07e57a80...`). Code: `sbgv8/policy.py`, `calibrate.is_eligible`.

## 1. What the two blockers mean operationally (from the V7-B code)
Both codes are emitted at one place, `sbgv7/decide.py::_blockers` (last block): when `changed_units - hit_units` is non-empty, i.e. at least one changed executable (side, line) was never executed by a deterministic-confirmed, non-lossy SAME input, the blocker is `budget_exhausted_s0` if the run stopped because the input budget was used up (`Evidence.budget_exhausted`, set in `sbgv7/runner.py::finalize` for stop in {budget, budget_mid_input}; `budget_mid_input` additionally appends a `budget_exhausted_s0` static blocker), otherwise `changed_region_not_activated`. Both have RANK 9 (weakest) but ANY blocker makes `decide` return `INSUFFICIENT` and `sufficiency` return level S0. They are therefore INSUFFICIENT reasons by V7-B's declared semantics, not graded features: the V7-B contract is "NO_DIVERGENCE_OBSERVED only if every changed unit was exercised by a SAME input".
- changed_region_not_activated: the supplied/generated inputs never reached part of the changed code. Missing evidence: any observation of base-vs-variant behaviour on that code. "No divergence observed" there is vacuous for the unexecuted part.
- budget_exhausted_s0: same missing evidence, but the cause is the tool stopping early (more inputs might have reached it); the evidence gap is a tool/budget limit, not a statement about the inputs.
Data fact (dev records): 24 labelled pairs are eligible under v8.0 only because of the soft rule, all `synthetic`, all with V7-B verdict INSUFFICIENT; 5 of the 24 have act_frac = 0.0 (no changed unit executed at all), the mean unhit fraction is 0.55, and none carries `budget_exhausted_s0` (that code does not occur in the dev data; the review of it is from code semantics only).

## 2. Is an NDO defensible when changed units were never executed?
No. A verdict of "no divergence observed" for a pair whose changed lines were never run states nothing about those lines; V7-B refuses it by construction (INSUFFICIENT), and V8's role is to calibrate confidence in V7-B-issued NDOs, not to override V7-B's refusals. A calibrated risk estimate cannot repair it: the activation shortfall is already the information the model would use, so "issue NDO if the modelled risk is low" re-introduces by a threshold what V7-B excludes by a rule. Therefore these pairs must cause ABSTENTION (hard blockers).

## 3. Policies
| name | rule | eligible labelled | Y=1 among eligible |
|---|---|---|---|
| v8.0 (A, historical default, kept reproducible) | the two codes are soft; every other blocker hard | 85 | 24 (0.282) |
| v8.0s (legacy `STRICT_BLOCKERS`) | every recorded blocker hard | 61 | 13 (0.213) |
| **v8.1 (B, PRIMARY)** | eligible iff V7-B-style decision on the record is NO_DIVERGENCE_OBSERVED (no recorded blocker AND no re-derived unhit changed unit) | 61 | 13 (0.213) |
**Selection of the primary policy is by declared semantics (section 2), made before looking at which policy scores better.** v8.0 was a documented design shortcut (comment in `calibrate.py`: keep coverage a graded feature); v8.1 corrects it as a NEW named version, so every v8.0 result stays reproducible (`results/v8_mac_reanalysis_*/v8.0/seed0` reproduces `results/v8_dev_eval_20261118_200754/seed0` exactly on all system metrics; test `test_policy.py`). On this data v8.1 == v8.0s == exactly the set of pairs where V7-B itself issues NDO (61 pairs, 13 false assurances, risk 0.213, coverage 0.236).

## 4. Effect on coverage and on estimated false-assurance risk (computed)
- Soft-blocked pairs are risky: 11 of 24 have Y=1 (0.458) vs 0.213 for the 61 V7-B-NDO pairs. Admitting them raises the eligible-pool risk from 0.213 to 0.282.
- Coverage ceiling: v8.0 can issue NDO on up to 85/258 = 0.329 of labelled pairs; v8.1 up to 61/258 = 0.236 = V7-B's own coverage. Under v8.1 calibration can only abstain further, never extend coverage beyond V7-B.
- In practice v8.0's frozen target-coverage rule (section "frozen" in the matched-coverage review) issued NDO on only 2 of these 24 pairs for CEC-without-ERS (1 false assurance), because the model learns to rank them as riskiest; coverage-only calibration (b7) issued 79 pairs, 18 of them soft-blocked with 9 false assurances (pooled realised coverage 0.306 vs the 0.236 target), i.e. under v8.0 the coverage-only baseline is the system that most often issues NDO on never-activated code, and 9 of the 11 soft-pool Y=1 pairs reach the user as NDO.
- Selective risk at the V7-B coverage (matched-rank diagnostic): v8.0 b7 0.230, b9 0.292, b8 0.213; v8.1 all three 0.213 (identical 61 pairs). Differences under v8.0 are not resolvable (all paired 95% CIs include 0) and under v8.1 are exactly 0 by construction.
- The v8.0 headline "coverage-only calibration beats nothing" and the v8.1 outcome "all models tie at the gate coverage" are therefore the same fact seen through two pools; v8.0's apparent room to differentiate models came from the 24 soft-blocked pairs.

## 5. Consequences under the strict policy (v8.1)
- `act_frac` and `obs_react` are CONSTANT (=1.0) among eligible pairs (slope diagnostics: `constant_features_among_eligible`); the model code zeroes dead features. Coverage-only calibration (b7) therefore reduces to `branch_cov_min` alone (3 distinct values 0.75/0.857/1.0 among the 61 eligible pairs; 59 of 61 >= 0.8), essentially an intercept: it cannot rank, and its matched-coverage and frozen results tie with the V7-B gate. The coverage-only baseline is not a competent comparator here; it is a constant predictor. The claim "CEC beats coverage-only calibration" is then trivially the claim "CEC ranks V7-B's NDO pairs better than a constant", which is a weaker and different statement than the original RQ2, and it is carried only by multiplicity (`mu_min`, `n_same`) and, possibly, ERS.
- Equivalently, the coverage hypothesis (H1a) is untestable under v8.1 on this data: coverage varies only through the activation screen that V7-B already applies.
- Eligible pool shrinks to 61 pairs / 34 projects (24 are `quixbugs_neg`, one project, Y=0 by generator construction) so statistical resolution falls further (V7-B-gate power report: ICC 0.61, DEFF 1.48, effective n 41, crude MDE 16.5 pp, pilot/exploratory).
- Under v8.1, nothing in the nested-threshold evidence (0 coverage at alpha 0.10/0.15) changes: honest bootstrap upper bounds still issue nothing.

## 6. Recommendation
Use v8.1 as the primary eligibility policy for all V8 statements; report v8.0 as a labelled sensitivity analysis that answers a different question ("may calibration override V7-B's activation refusal?", answered: it should not, and the data show that doing so adds risk, 0.458 in that sub-pool). Both result sets are preserved. This is a development-data review: no claim here is independent validation.
