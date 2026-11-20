# V8 adjudication protocol (implementation-level; Phase 3 execution NOT authorised)

Consistent with `research/v8_final_design/04` (sec. 2) and `07`. Code: `sbgv8/adjudication.py`; templates: `datasets/v8/adjudication_templates/`. Nothing here has been run on real pairs; no adjudicator exists yet and none is simulated except in clearly synthetic test fixtures.

## 1. Estimand and outcome classes
Per pair the final outcome is one of: `confirmed_divergence` (Y=1), `no_divergence_found_within_budget` (Y=0), `unresolved` (Y=bottom). Y=0 means "no divergence found by the protocol within budget b, and two reviewers judge the change not behaviour-altering within scope". It is not equivalence, so R_adj is a lower bound on R_true when adjudication power is below 1 (04 sec. 2). This is reported with every estimate.
- Y=1 needs an executed input x in the declared domain with a repeated, determinism-controlled observable difference in the observation boundary O.
- Y=0 needs the pre-declared budget exhausted AND reviewer agreement as above.

## 2. Blinding (enforced in code, not by promise)
- `AdjudicationCase` has exactly four fields: pair id, observation boundary, budget, evidence reviewed. There is no field for model scores, ERS outputs, baseline predictions or verdicts; any such key (matched by name, at any nesting depth) raises `BlindingViolation` (tested).
- Adjudicators receive the diff, entry point, O, b and adjudication-only inputs. They never receive commit message or issue text unless 07 lists it, and never any system output.
- Residual blinding risk that code cannot remove: an adjudicator may recognise a public project or a bug; recorded as a threat. An adjudicator who has seen a system output declares it and the case is reassigned.
- Independence of tool chain: adjudication generators and seeds differ from the system's evidence generators (07). Residual dependence is stated as a threat.

## 3. Workflow
1. Case registration: observation boundary O and budget b are frozen (hash recorded; `budget_hash` is copied into every decision).
2. Two primary adjudicators, distinct, decide independently, each recording outcome, free-text rationale (required), timestamp. Decisions are never edited.
3. Agreement: identical outcomes are final. A primary disagreement (including unresolved vs a definite outcome) goes to a third adjudicator, distinct from both, who decides; the third decision is final. Disagreement without a third decision stays `unresolved` (`pending_third`).
4. Budget freeze: `Workflow.set_budget` raises `BudgetFrozen` once any decision exists for the case; before that, each change is logged.
5. All-divergent double labelling: every pair with any primary `confirmed_divergence` is double-labelled; at least 30% of all pairs are double-labelled (07). The code reports the double-labelled fraction; the all-divergent condition must be checked by the study lead.

## 4. Audit trail
Append-only JSONL; each event stores seq, timestamp, type, payload, previous hash, and sha256 of the canonical event. `verify_chain` detects edits, insertions or reordering of events. **It is tamper-evident only**: someone with write access to the whole file can recompute every hash; there is no signature, no trusted time source and no external anchor. For publication the final chain head hash should be placed in a third-party time-stamped registration (06).

## 5. Agreement statistics
Cohen's kappa over the three outcome classes between the two primaries, with confusion matrix. Gate: kappa >= 0.7 on at least 30% double-labelled coverage; below it, protocol revision before any scoring (07). Hand-checked in tests (e.g. po=0.7, pe=0.5 gives 0.4). Degenerate marginals (pe = 1: both raters used one identical category) make kappa undefined; the code returns `None` with a note and the report must show raw agreement; no smoothing or imputed value. Kappa is also unstable with strongly skewed prevalence, so the confusion matrix and raw agreement are always reported with it; kappa with a confidence interval is a Phase 3 analysis choice to pre-register.

## 6. From outcomes to Y and the estimand variants
`y_from_adjudication` maps confirmed -> 1, none found -> 0, unresolved -> None (default `drop`). `estimand_variants` returns three pre-declared variants:
| variant | unresolved becomes | meaning |
|---|---|---|
| `drop` (primary) | excluded, counted and reported | changes numerator and denominator of R |
| `worst_case_divergence` | Y=1 | every unresolved pair counted as a false assurance if issued NDO (06 sensitivity) |
| `non_divergence` | Y=0 | optimistic bound |
The number of unresolved pairs is always reported. If unresolved pairs are a large share, conclusions are stated as an interval between variants, not as the `drop` point estimate.

## 7. Never done
No adjudicator, decision, kappa or label is fabricated; test fixtures are synthetic and labelled so. The system's verdicts must not be consulted at any step. Real adjudication is a Phase 3 action (see `V8_PHASE3_AUTHORISATION_PACKAGE.md`).
