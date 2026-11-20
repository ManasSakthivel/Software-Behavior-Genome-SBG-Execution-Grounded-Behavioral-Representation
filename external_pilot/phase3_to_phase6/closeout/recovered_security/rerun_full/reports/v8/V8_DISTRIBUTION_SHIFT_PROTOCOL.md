# V8 distribution-shift protocol (project-family shift experiment; design only, DEFERRED on current data)

Extends 06 RQ4. Code: `sbgv8/splits.py` (`family_shift_feasibility`, `family_shift_split`, `assert_no_leakage(families=True)`). Project-held-out splitting (06) tests generalisation to new projects; this experiment asks the harder question of generalisation to new kinds of projects.

## Design
1. Family grouping uses only label-independent information (source collection, project domain, ecosystem, size band, test-style) fixed and recorded as a rule id before labels are opened. The development manifest uses rule `arm_prefix_v1`. A family never uses the label, verdict, or anything derived from system output.
2. Train and calibrate on some families (project-aware development/calibration split inside them), evaluate on whole held-out families, rotating which family is held out (leave-one-family-out when there are enough families; otherwise a pre-declared subset).
3. Report within-family (project-held-out inside a family) versus cross-family results side by side, same metrics as 06: selective risk at matched coverage, Brier, log loss, calibration slope and intercept with project-clustered intervals.
4. Calibration degradation: slope, intercept and ECE change from within- to cross-family, with intervals, plus the shift in issued coverage at a fixed threshold. Report whether the pre-declared threshold tau still meets alpha_pre.
5. Features failing under shift: per-feature coefficient and partial-dependence stability across held-out families, the feature-distribution shift (e.g. standardised mean difference of each of the 15 features between train and held-out families), and the ablation of each feature group (`schema.FEATURE_SETS`) under shift. A feature is reported as shift-fragile if dropping it improves cross-family log loss or if its coefficient sign flips.
6. No distribution-free claim: nothing here supports a guarantee under arbitrary shift. Conformal-style guarantees need exchangeability (04 sec. 6), which family shift violates by construction; results are empirical with intervals, for the families tested.

## Deferral rule (feasibility check)
`family_shift_feasibility` requires at least 3 families, each with >= 5 projects, >= 20 labelled pairs and both outcome classes, and no family above 60% of labelled pairs. Otherwise the experiment is DEFERRED and the report states why; no cross-family number is produced or implied.

## Feasibility on the development manifest (computed, not assumed)
Verdict: **DEFERRED: data lacks family diversity.** Families under `arm_prefix_v1`: quixbugs (1 project, 113 labelled pairs, 29 divergent), synthetic (101 pseudo-projects, 145 labelled, 77 divergent), bugsinpy (12 projects, 0 labelled). Only synthetic qualifies; need 3. Further, even a split on these would measure generator-to-benchmark difference on design-exposed data, not distribution shift across real projects. The experiment is therefore a Phase 3 item that needs the external dataset (07) built with family diversity in mind (at least 3 families, ideally 5, each with >= 10 projects). `family_shift_split` is tested on synthetic fixtures only.

## Threats
Family definitions are a researcher choice and can be gamed; fix and register them first. Few families means wide intervals and strong dependence on which family is held out; report every rotation, not the best. Family and project size confound; stratify and report.
