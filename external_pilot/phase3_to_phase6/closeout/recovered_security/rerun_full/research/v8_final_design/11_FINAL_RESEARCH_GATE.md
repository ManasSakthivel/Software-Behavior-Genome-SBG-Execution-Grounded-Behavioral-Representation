# 11 Final research gate

| Gate | Decision | Condition |
|---|---|---|
| Research direction | CLOSED | CEC narrowed as in 00; no further direction sprints |
| Offline implementation M1-M4 on recorded development data | GO | new package `sbgv8/`; V7-B, results and artifacts untouched; no external execution; no confirmatory claims |
| Registration drafting (06) | GO | freeze requires explicit sign-off before any Phase 3 label exists |
| Phase 3 (Linux/Docker V8-A, dataset, adjudication, holdout) | NO-GO until the user explicitly authorises Phase 3 | standing project constraint |
| Publication | CONDITIONAL | one of the fallbacks in 10 is always available; submission requires the checklist |
| Novelty claims | restricted | only the surviving distinctions in 00; "first" prohibited |
| Calibration guarantee claims | prohibited | empirical calibration with cluster CIs only; CRC secondary under stated assumptions |
Risks that could stop the programme: kappa < 0.7; fewer than about 100 issued NDO verdicts; D2 infeasible and no response-feature gain; V8-A cannot be validated. None of these invalidates publication under F1-F5.

## Final adversarial review of this deliverable (done before closing)
Found and fixed: (1) the power statement in 06 contradicted the sample-size arithmetic in 07 (a 5pp difference is underpowered at K5 scale; both files now say so); (2) source line references in 03 corrected to `decide.py:72`, `runner.py:317` and `runner.py:333-335`; (3) the brief's title for the 2026 selective conformal paper does not match the paper found (Bai & Jin, arXiv 2603.24704): recorded in the register and bib; (4) bibliography rebuilt after a malformed copy (19 balanced entries, no duplicates).
Checked: no sbgv7 code implements slicing, influence or provenance (grep, 0 hits); no phrase claims "first", equivalence, tamper-proof or a guarantee on conditional risk; every guarantee statement lists assumptions; abstention is never counted as improvement without matched coverage; confidence scores are not called probabilities until calibrated.
Not verified (limits of this review): Geifman & El-Yaniv, the two 2025/2026 selective-conformal preprints, Dunn et al. and the conservative-Bayesian papers were seen at abstract/snippet level; ORION was not re-found by search; the STVR 2013 checked-coverage extension and Inozemtseva & Holmes were not read; BESTEST was read in part; no systematic search on calibration under distribution shift or on benchmark contamination was completed; all DOIs outside the 5 newly checked papers rely on the repo's Crossref verification of 2026-11-17. Sample-size figures are arithmetic on assumed inputs (design effects, discordance), not data.
