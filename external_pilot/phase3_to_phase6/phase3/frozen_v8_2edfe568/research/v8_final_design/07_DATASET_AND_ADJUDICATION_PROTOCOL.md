# 07 Dataset and adjudication protocol (Phase 3; nothing here is executed or authorised yet)

## Why the Phase 2 data cannot be the test set
321 development pairs (31 QuixBugs, 85 QuixBugs negatives, 150 synthetic, 55 BugsInPy units): 57 unlabelled and 6 suspect in E3, 24 of 24 B1 false assurances were synthetic generator labels, QuixBugs labels derive from declared tests that also supply the inputs, and the pairs were examined repeatedly during design. They are development data. Use: debugging, fixtures for property tests P1-P6 and pipeline checks only.

## Target dataset
- Projects: at least 60 independent open-source Python projects (feasibility minimum, retained from K5) and a recommendation of at least 80 if the sample-size section below applies; maximum 8 pairs per project to limit clustering (design effect).
- Pairs: version pairs from real commits with a declared entry point and input specification.
 - Divergent: at least 250 (K5 minimum).
 - Non-divergent controls: at least 350, of which at least 100 hard negatives (behaviour-preserving refactors, performance changes, fixes on paths outside the declared scope, near-miss changes).
- Splits by project: development pool, calibration pool, final holdout of at least 20 projects (and at least 200 pairs) untouched until the pre-registration is frozen and scored once.
- Evidence generation: inputs supplied to the system come from declared tests and generator classes with recorded provenance; adjudication inputs are separate and never reused as system evidence.
## Adjudication
- Two independent adjudicators per pair, blind to all system verdicts; third adjudicator for disagreements. Cohen's kappa at least 0.7 on a double-labelled sample covering at least 30% of the pairs (all divergent pairs double-labelled). Kappa below 0.7 triggers protocol revision before any scoring.
- Y=1 requires an executed, repeated, determinism-controlled observable difference (04). Y=0 requires adjudication budget b exhausted (fixed per pair: e.g. N independent generators and a time cap, pre-declared) and reviewer agreement that the change is not behaviour-altering within scope. Unresolved pairs are Y=bottom and reported.
- The adjudication tool chain must differ from the system's evidence generators (different generators and seeds), otherwise Y=0 would only restate the system's own blind spots. Residual dependence is stated as a threat.
## Sample-size analysis (script: `scripts/sample_size_calc.py`; arithmetic on assumed inputs, not data)
Quantity of interest: R among issued NDO verdicts. Issued NDO verdicts needed for a 95% Wilson half-width h, inflated by a design effect 1+(m-1)rho:
| R | h | issued NDO, iid | DEFF m=3, rho=0.15 | DEFF m=5, rho=0.30 |
|---|---|---|---|---|
| 0.10 | 0.05 | 141 | 184 | 311 |
| 0.20 | 0.05 | 245 | 319 | 539 |
| 0.20 | 0.07 | 124 | 162 | 273 |
Coverage converts verdicts to pairs: issuing NDO on 25% to 40% of pairs, 150 issued verdicts need 375 to 600 pairs, 250 need 625 to 1,000. Phase 2 development coverage was 61 of 258 (0.24) for V7-B.
Paired comparison at matched coverage (80% power, alpha 0.05): detecting a 8pp risk difference needs about 121 to 243 matched issued pairs (175 to 353 with clustering) depending on the discordant share; a 5pp difference needs about 312 to 626 (452 to 908).
**Finding: the K5 targets (60 projects, 250 divergent pairs) are adequate for a feasibility and risk-coverage study but not for narrow calibration intervals or for confirming a 5pp matched-coverage difference.** With 250 divergent plus 350 non-divergent pairs (600 total) and issuance 0.25 to 0.4 the study yields about 150 to 240 issued NDO verdicts, enough for a half-width near 0.07 at R about 0.2 only if clustering is mild. The false-assurance events themselves (R about 0.2 means about 30 to 50 events) also cap the model at about 3 to 5 predictors.
Recommendation: target at least 600 adjudicated pairs from at least 60 (preferably 80) projects; pre-declare that primary inference uses grouped cross-validation over the whole non-holdout pool with cluster bootstrap, and that the holdout (at least 200 pairs, about 50 to 80 issued NDO) is a one-shot confirmation reported with its realised interval and MDE. At this scale the minimum detectable matched-coverage risk difference is about 8-10pp, so the 5pp practical threshold of H2 is underpowered (06). Do not claim generalisation from 60 projects or 250 divergent pairs.
If infeasible: (a) fewer than 400 pairs or fewer than 60 projects: report a pilot, estimate risk-coverage curves and intervals, make no calibration or H2 claim; (b) if adjudication kappa < 0.7: stop and revise labels; (c) if issued NDO verdicts < 100: report that the system rarely issues NDO and the claim reduces to abstention behaviour.
## Leakage and contamination controls
Project-level splits; no commit-message or issue text in features; dedupe near-identical projects/forks; record whether projects are in public benchmarks or in LLM-training-exposed corpora; adjudicators blind to verdicts; adjudication inputs sealed from system evidence; feature set frozen before labels are opened.
