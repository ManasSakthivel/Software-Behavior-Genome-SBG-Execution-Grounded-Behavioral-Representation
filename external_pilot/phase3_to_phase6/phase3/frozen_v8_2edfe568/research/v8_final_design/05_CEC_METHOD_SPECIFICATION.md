# 05 CEC method specification (design only; nothing here is implemented)

Working name: Counterfactual Evidence Calibration (CEC), formally "calibration of false-assurance risk with evidence-perturbation responses". "Counterfactual" is limited to the evidence package (04, section 5).

## 1. Evidence dimensions (phi)
No composite weights. Each is reported separately; the model uses a pre-declared subset (tier 1, <= 5 predictors, see section 4).
| # | Dimension | Definition | Observable inputs | Failure modes | Depends on | In V7-B? |
|---|---|---|---|---|---|---|
| D1 | Change activation and multiplicity | a = |U_hit|/|U_chg| over deterministic clean SAME inputs; b = branch-direction coverage on changed lines; mu_u = number of behaviourally distinct inputs reaching changed unit u; mu_min = min_u mu_u | recorded hits/branches per input | AST diff mis-maps continuation lines (Phase 2: 54 pairs `unmodelled_change`) | D4, D3 | a, b yes; mu no (recorded per-input hits make it computable) |
| D2 | Observable influence | iota = fraction of changed units u with at least one input x whose recorded observation depends on execution of u. Candidate measurements: dynamic dependence from changed-line definitions to observation values (backward slice from observation values, in the spirit of checked coverage) or a cheaper data-flow approximation | execution trace (needs harness extension) | implicit flows, aliasing, C extensions, cost | D1, D3 | **No** (new, research risk) |
| D3 | Observation completeness | kappa = fraction of declared channels with effective non-lossy capture over inputs; lossy/degenerate SAME rate | observation records | channel exists but program emits nothing there (degenerate SAME) | none | partial (lossy flag; channel instrumentation hard-coded True) |
| D4 | Reproducibility | share of inputs deterministic-confirmed; replay and alternate-run agreement; quarantined count | run records | hash order and wall clock outside controls | none | yes |
| D5 | Effective input diversity | n_eff = number of distinct observation fingerprints; n_eff_prov = same after collapsing inputs of one provenance class | observations, provenance | fingerprint collisions; coarse canonicalisation | D6 | no |
| D6 | Provenance and dependence | per-input provenance class (declared test, generator seed class, LLM prompt family, developer test, label-derived); rule: label-derived inputs are not eligible as NDO evidence | input metadata | provenance mis-recorded | none | no |
| D7 | Environment consistency | all runs share one environment digest; differences flagged | env digest | undeclared host state | none | partial |
| D8 | Evidence integrity | verification passed; tamper flag; collector trust level (V8-A) | log verification | in-process forgery (red-team M-4) | V8-A | partial |

## 2. Intervention operators on E
| Op | Name | What changes | Fixed | Execution? | Expected response | Falsified if |
|---|---|---|---|---|---|---|
| T_del | Relevant-evidence deletion | remove the inputs that are sole reachers of changed unit u (or of an observation channel value) | everything else | no (recompute `finalize` on recorded parts) | s_theta non-decreasing; verdict may become INSUFFICIENT | s_theta decreases after deletion for a large share of pairs |
| T_dup | Duplicate augmentation | repeat recorded inputs/observations k times | E otherwise | no | phi unchanged (n_eff, mu_min unchanged); s_theta unchanged | s_theta changes by more than a tolerance |
| T_irr | Irrelevant augmentation | add inputs that execute only unchanged code | E | yes (new runs, V7-B engine) | activation, mu, iota unchanged; s_theta unchanged | s_theta decreases materially |
| T_mask | Observation masking | drop channel(s) from recorded observations and recompute | E | no | kappa decreases; s_theta non-decreasing; if the witness channel is masked the pair can flip DIV -> NDO (a controlled missed divergence) | s_theta decreases after masking |
| T_bud | Reproducibility-budget perturbation | vary r_det, r_replay, k_alt | inputs | yes | witness status stable on witnessed pairs; flaky pairs change | verdicts of witnessed pairs not stable |
| T_aug | Independent discriminating-input augmentation | add independently obtained inputs that hit changed behaviour | E | yes | if a difference exists the verdict becomes DIV (not "higher confidence"); otherwise phi improves | a divergence-revealing input fails to change the verdict |
Quantity versus information: T_dup and T_irr test that evidence QUANTITY is not credited as INFORMATION. T_del and T_mask are post-hoc ablations (no new observation); T_irr, T_bud, T_aug are real execution interventions.
Warning on T_mask: masking a witness channel creates labelled missed divergences, but they are synthetic and do not follow the natural error distribution. They are used for property tests only, never for fitting or threshold choice.
Response profile rho(E) = (Delta s_theta under T_del per unit, under T_mask per channel, ...). Whether rho adds predictive information beyond phi is the empirical hypothesis (RQ3); deletion response is a function of the same recorded evidence and could be redundant with mu_min, which is why baseline 9 (CEC without response features) exists.

## 3. Pre-declared response properties
P1 irrelevant-evidence invariance (T_irr); P2 duplicate-evidence invariance (T_dup); P3 relevant-evidence sensitivity (T_del, label-free direction check; labelled check: pairs whose deletion raises s_theta should have higher observed false assurance); P4 observation-loss sensitivity (T_mask); P5 divergence responsiveness (T_aug); P6 provenance sensitivity (label-derived and same-generator inputs must not raise s_theta); P7 calibration validity (empirical, held-out projects). P1, P2, P4 are deterministic unit tests needing no labels; P3 direction, P5 and P6 need controlled fixtures; P7 needs labelled independent data. P3, P5 do not require monotone increase of confidence when a divergence appears: the correct response is the verdict DIV.

## 4. Calibration method
Recommendation: a transparent hybrid, simplest first.
1. Tier-1 model: L2-penalised logistic regression with monotone sign constraints on at most 5 pre-declared predictors (a, mu_min, iota or kappa, reproducibility share, n_eff_prov). Rationale: false assurances among issued NDO will be tens, so about 1 predictor per 10 events limits k.
2. Recalibration on a separate project fold: isotonic regression only if the fold has at least a few hundred scored pairs, otherwise Platt-style intercept/slope.
3. Threshold tau on the calibration projects: the largest coverage whose upper project-cluster-bootstrap confidence bound on R is at most alpha_pre (pre-declared, 0.10 and 0.15 as the two reported targets).
4. Secondary, exploratory: conformal risk control for the joint risk J with exchangeable project units, third disjoint split, bound reported only with assumptions A-EX of 04. No guarantee language in the abstract or conclusions.
Not used: deep learning (insufficient independent data), generalised additive models beyond a pre-declared monotone spline for one predictor, post-hoc feature search on test projects.
Issues handled: project-level split (no project in two folds); grouped k-fold with nested threshold selection; leakage control through feature pre-registration and a frozen holdout; class imbalance through reporting selective risk, not accuracy; selection bias because R conditions on A=1 (estimated only on eligible pairs, with c reported); dependence within projects via cluster bootstrap with at least 60 clusters, otherwise wild/cluster permutation and wide intervals; dist. shift: only held-out-project generalisation is evaluated, no shift-robust claim.
Finite-sample guarantee: not available for R under the available design; empirical calibration with cluster CIs is the primary claim.
Metrics: Brier score; log loss; calibration intercept and slope (logistic recalibration); reliability diagram; ECE reported with binning sensitivity and never alone; selective risk at fixed coverage; coverage at predeclared risk; all with project-clustered CIs.
