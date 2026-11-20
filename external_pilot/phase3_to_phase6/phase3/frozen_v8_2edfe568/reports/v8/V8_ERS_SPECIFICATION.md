# V8 Evidence Response Signature (ERS) specification

Status: development specification, `sbgv8/ers.py`. No empirical claims.

## Definition
For a record E, a predictor f (protocol: `predict_risk(rec) -> [0,1]`, `decide(rec) -> (verdict, risk)`) and a perturbation T_j from `perturb.PERTURBATION_MATRIX`:

    Delta_j = risk_f(T_j(E)) - risk_f(E)

The `ERS` dataclass stores perturbation id and parameters, original and perturbed profile, risks, decisions, coverage (act_frac, branch_cov_min, chan_complete) before/after, provenance and integrity status, expected and observed response, `passed` (True/False/None), tolerance and the `PerturbationRecord`. ERS needs only the predictor interface, not the CEC policy; `ActivationStubPredictor` (risk = 1 - act_frac, V7-B-style decision) is the reference stub. `ers_vector` returns `ers_<pid>_delta` for use as calibrator inputs (0.0 where not applicable). `schema.ERS_FEATURES` should be set to `[f"ers_{p}_delta" for p in PERTURBATIONS]` by the owner of schema.py.

## The properties (verdict NDO = NO_DIVERGENCE_OBSERVED, INS = INSUFFICIENT)
| Pid | Property | Pass condition | Tolerance |
|---|---|---|---|
| P1 | relevant-evidence sensitivity | Delta >= -tol, or verdict INS | tol = 1e-6 |
| P2 | irrelevant-evidence invariance | abs(Delta) <= tol and verdict unchanged | 0.02 |
| P3 | duplicate-evidence invariance | abs(Delta) <= tol and verdict unchanged | 0.02 |
| P4 | observation-loss sensitivity | Delta >= -tol, or verdict INS | 1e-6 |
| P5 | reproducibility-degradation sensitivity | Delta >= -tol, or verdict INS | 1e-6 |
| P6 | divergence responsiveness | verdict DIVERGENT_OBSERVABLE, or Delta > 0, or verdict INS (no monotonicity imposed) | none |
| P7 | provenance sensitivity | Delta >= -tol, or verdict INS | 1e-6 |
| P8 | integrity rejection | perturbed integrity_ok = 0 and verdict INS | exact |
| P9 | environment sensitivity | Delta >= -tol, or verdict INS | 1e-6 |

## Applicability and abstention
`passed = None` (reason recorded) when: the perturbation is not applicable to the record (P1 no sole-reacher input; P2 no clean SAME input; P3/P5/P7 no suitable inputs; P4 channel not captured by any input; P6 already divergent; P8/P9 already violated), or, for P1/P4/P5/P7/P9, the original verdict is already DIVERGENT_OBSERVABLE (assurance risk is not defined there). Abstention (perturbed verdict INS) counts as a pass for P1/P4/P5/P6/P7/P9 and is the required response for P8.

## What ERS does not show
- It is an evidence-perturbation response: what the predictor would output given E', not a counterfactual about the programs. No causal claim about program behaviour.
- Post-hoc P2 and P6 use synthetic recorded inputs; passing says nothing about discovery power or about real execution behaviour (see V8_PERTURBATION_CONTROL_MATRIX.md).
- Passing the properties is necessary, not sufficient, for calibration validity (P7 of the design is empirical and needs held-out projects). A predictor can pass all of them and still be miscalibrated.
- A stub that abstains always passes the monotone properties; abstention rates must be reported next to pass rates.
- Response features may be redundant with profile features (e.g. P1 and mu_min); whether they add information is the empirical RQ3.

## Finding from the first development-data run (recorded, not hidden)
Running the ERS control matrix with the actual fitted model on 312 development records first produced **84 P8 failures** (`results/v8_dev_summary/ers_matrix_initial_P8_84_failures/`): all 84 were witnessed DIVERGENT_OBSERVABLE pairs. When the record's integrity flag was set to false, the decision function still returned DIVERGENT_OBSERVABLE, because V7-B's `decide` gives witness precedence and the record-level integrity flag was not part of it. Resolution (a V8 policy rule, V7-B untouched): `calibrate.Model.decide` returns INSUFFICIENT (risk 1.0) for any record whose integrity check failed, for every verdict class. The matrix was then re-run (`results/v8_dev_summary/ers_matrix_real_model/`): P8 312/312 pass. This is a policy rule, so the P8 pass reflects that rule; the independent evidence for evidence-integrity handling remains the trust forgery suite, which shows two attacks still succeed (see V8_SECURITY_AND_TRUST_REPORT.md).
Applicability on the development data (pass/fail/N-A of 312): P1 16/0/296 (relevant deletion applies only where a single input is the sole reacher), P2 227/0/85, P3 262/0/50, P4 178/0/134, P5 176/0/136, P6 228/0/84, P7 178/0/134, P8 312/0/0, P9 228/0/84. P2, P5, P6 are the post-hoc recorded-evidence variants; the real-execution variants need the collector and were not run. Passing means "behaved as pre-declared", not that the model is accurate.

## Addendum 2026-11-18 (Mac hardening, agent E; append-only)
Full detail: `reports/v8/mac/V8_MAC_PERTURBATION_VALIDATION.md`; data `results/v8_mac_perturb/`.
- Evidence class: every perturbation is now labelled (`perturb.EVIDENCE_CLASS`): (a) recorded-evidence transformation, (b) re-execution with changed conditions, (c) independently acquired evidence. All post-hoc variants are class (a); none is an execution intervention. Only P2 (b), P5 (b) and P6 (c, outcome-conditioned) have real-execution analogues, implemented in `experiments/v8/run_real_exec_perturbations.py` (30 development pairs, macOS).
- N/A is never a pass. Pass rate is pass/(pass+fail) over APPLICABLE cases with the denominator printed. 312 development records, nine properties: stub 1805/1805 applicable (N/A 1003 of 2808), fitted model 1805/1805 (1003), V7-B recorded gate 1579/1805 (fails P6 71, P8 155; it is a stored verdict, so it cannot respond to a perturbed record), V7-B recomputed 1721/1805 (P8 84: witness precedence over the tamper flag).
- The fitted dev model keeps only `mu_min`; its P2/P3/P4/P6/P7/P9 deltas are exactly 0. Those passes are "no wrong-direction response", not sensitivity. An unfitted all-feature `calibrate.Model` fails P2 on 109/227 (quantity features count irrelevant inputs) and, in real execution, credits identical repeated runs (`n_rep`) in 30/30 pairs.
- P3 invariance holds for copies flagged `duplicate_of`; unflagged copies raise `n_same`/`n_rep`.
- Correction to "Applicability" above: the stub's P8 now also requires the integrity gate (`ActivationStubPredictor.decide` returns INSUFFICIENT when `integrity_ok` is false).
- Named variant P1b (least-multiplicity covered unit deletion) added without replacing P1; P1: 54 applicable of 312, 38 of them originally DIVERGENT (N/A), 16 evaluated; P1b: 93 evaluated.
