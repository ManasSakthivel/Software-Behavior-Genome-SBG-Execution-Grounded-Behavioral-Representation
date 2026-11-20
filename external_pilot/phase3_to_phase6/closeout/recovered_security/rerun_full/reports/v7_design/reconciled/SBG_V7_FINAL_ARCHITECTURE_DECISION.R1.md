Reconciled version R1 of SBG_V7_FINAL_ARCHITECTURE_DECISION.md; original preserved at reports/v7_design/_original_archive/

# SBG V7 Final Architecture Decision, R1

Authority: `reports/final/V7B_FROZEN_SPEC.md` > `P0_BINDING_DECISIONS.md` (D1-D11). Evidence base added since the original: `reports/final/P0_FINAL_RECONCILIATION_REPORT.md`, `INDEPENDENT_RED_TEAM_REVIEW.md`, `FINAL_RESEARCH_READINESS_REPORT.md`, `PHASE_1_FINAL_CLOSURE_REPORT.md`, `research/literature/RESEARCH_GAP_AND_NOVELTY_ASSESSMENT.md`. Nothing here is a new result.

## 1. Decision

**V7-B is the primary architecture** (D6; FS s1): sufficiency-aware, witness-based differential comparison with adaptive exploration as a gated extension, three verdicts, evidence contract, no equivalence verdict. **V7-A** (internal-state divergence, module E) is an optional gated pilot (<= 12 weeks, effect of interest +10pp, authored suites with independent truth), attempted only after V7-B shows headroom and not authorised now. **Full V7** (explorer plus internal-only divergence plus impact as claimed components) is not justified by the evidence (readiness report, "V7 vs V7-B"). The original recommendation text "four-way verdict", "internal-state divergence witnesses" and "state abstraction core" is withdrawn (CM V-01, V-02, M-02).

## 2. Why V7-B beats the alternatives (see `SBG_V7_COMPETING_ARCHITECTURES.R1.md`)

Unchanged in substance: V6's losses came from unobservable pairs and return-blindness, so the missing pieces are controlled observation and honest abstention rather than a better scorer. Graph-only, invariant-only and learned alternatives cannot yield a replayable witness. The honest caveat stands and is now stronger: pure same-budget differential testing tied the composite on the authors' judgement score (19/24 each), and the independent red team found that, on the development data, repeated differential testing (B1+rep) differs from plain B1 on 2 of 311 driven pairs and tracks V7-B on every detection outcome. The V7-B choice is a bet resolved by K4 (FAR at matched decided coverage against like-for-like comparators), not a demonstrated improvement.

## 3. Retain / discard from V5/V6

Unchanged from the original (retain freeze/manifest/hash discipline, cluster bootstrap, abstention-first policy, audit scripts, all negative findings, tracer event semantics as `v6_compat`; discard the 10-feature scorer as core, output-free-only channel, E columns as predictors, generator-derived labels as truth, SP-8/SP-11 generators except as documented defect cases, the in-process thread sandbox for claims, AUROC as headline). Tag `v6-holdout-complete` and V5/V6 artefacts stay untouched. README V5/V6-era headline claims (AUROC 0.897 etc.) must not be conflated with V7-B results (red team Mi-2).

## 4. Minimal novelty claim (restated from `RESEARCH_GAP_AND_NOVELTY_ASSESSMENT.md`)

Standing: "found none" within a limited, single-reviewer, mostly abstract-level search; not an absence proof; **no "first", "novel" or "state of the art" wording is warranted for any item**.

| Claim | Classification | Surviving statement |
|---|---|---|
| C1 witness representation | Partially novel (not novel as a concept) | One schema carrying observation context (what was exercised, environment, seeds) for both difference and no-difference outcomes, replayable by a third party. Prior art: verification witnesses (Beyer et al.), Shadow, Mokav replayable differing inputs |
| C2 explicit sufficiency | Partially novel; weakest | Sufficiency as a recorded, per-claim, replayable field that gates the verdict. Prior art: patch coverage (Hilton 2018), DiffTestGen union coverage of modified code, Cleverest, dynamic-impact-analysis caveats. Coverage as sufficiency is itself contestable (Inozemtseva and Holmes; Just 2014) |
| C3 evidence-grounded insufficient outcome | Partially novel; "abstain" itself is not novel | Grounds of abstention are observation evidence recorded with the witness. Prior art: DiffKemp "undetermined", reject option (Chow 1970, Geifman 2017). Must never be worded as equivalence |
| C4 reproducibility-aware comparison | Partially novel; unassessable at depth | Folding nondeterminism evidence into the cross-version verdict. Repeat-to-filter-flaky is standard (iDFlakies, DeFlaker) |
| C5 empirical evidence | Unsupported | Must come from SBG's own independent runs; none exist |

The defensible contribution today is the integration: one replayable contract carrying witness, sufficiency record and an evidence-grounded insufficient outcome under nondeterminism checks, with an implementation whose closed enum makes an equivalence verdict unrepresentable (a naming guarantee, not a semantic one; red team s0, Q5, Q11). The closest competitors for behaviour-difference discovery (Testora, DiffTestGen, Mokav, Cleverest, DiffSpec) were not run as baselines.

## 5. Strongest argument against (updated)

V7-B may reduce to differential testing plus coverage reporting: on development data B1+rep matches V7-B detection-wise, sufficiency did not separate synthetic labels (changed share 25% under NO_DIVERGENCE_OBSERVED S2 vs 32% under INSUFFICIENT), 16 of 46 driven BugsInPy real-fix units received NO_DIVERGENCE_OBSERVED (15 at S2) on synthetic battery inputs, and a large part of the INSUFFICIENT rate comes from unimplemented engine features, not from a sufficiency judgement (renames 49, generators, class units). No pair has independent ground truth, so false-assurance rate is not computable from anything produced so far; the exploratory paired false-assurance gain had a lower CI bound of +4.3pp, below the +10pp effect of interest. Real-bug ground truth is scarce; underpowered per the P0 simulation (63% power at +10pp with 40 projects). These figures are from the cited reports; they were not re-derived here.

## 6. Most serious remaining risks

See `SBG_V7_RISK_REGISTER.R1.md` (R01-R38 retained, R39-R54 added). Top five: (1) no independent benchmark or adjudication capacity (K1 not met on development data, K5 not approached); (2) isolation below the spec minimum and untested on Linux/containers (blocks K2 and any third-party execution); (3) sufficiency has no measured value and uncalibrated thresholds (R03, R39-R41); (4) activation on real projects may stay low (K2/K3); (5) contamination: all existing data are burned or developer-owned (R27, R28).

## 7. Implementation order (reconciled; see `SBG_V7_IMPLEMENTATION_ROADMAP.R1.md`)

Phase 1 (done): V7-B core, development spike and baselines, red-team review. Phase 2 (this document set): reconciliation and conformance audit, documentation only. Phase 3 (**not started, not authorised**): Linux container isolation passing I1-I7, feasibility spike on about 30 candidate projects, K1 and K2; no K3+ work until K2 passes; K4, K5 and any sealed evaluation only per FS s12.

## 8. Evidence required to declare success

Unchanged in structure and now defined only by `SBG_V7_VALIDATION_AND_ACCEPTANCE_GATES.R1.md` section C (the original FINAL s8 numbers, ">= ~150 divergent pairs, >= 40 projects", are superseded by the K5 floor: >= 60 projects, >= 250 independent divergent pairs, >= 20 mixed-class projects, kappa >= 0.7, clean leakage audit; CM X-02, X-10). Not sufficient: results on V5/V6 benchmarks, AUROC alone, or completed experiments without a pre-declared win.

## 9. GO / REVISE / NO-GO (reconciled)

- P0 decision of record: **GO_P1, scoped** (FS s13). Not REVISE_P0 (the missing reconciled documents were debt, not inputs to P1; this R1 set closes that debt, O13) and not STOP (no gate had failed).
- Post-Phase-1 reading (readiness report): **verdict B**, promising as a design/feasibility contribution, not ready as a validation paper. This document records that and does not upgrade it.
- Recommendation for Phase 3 (a recommendation, not an authorisation): proceed only with the FS s13 scoped work (Linux container isolation, feasibility spike, K1/K2), under explicit PI authorisation. K1 evaluation as intended requires project-level runs under D10 isolation and has not been performed; the "K1 NOT MET" statement in the Phase 1 reports refers to development data only (74 runnable real pairs, 1 true project plus 44 extracted units on synthetic inputs). Whether that already triggers the K1 STOP of D9 is an unreconciled programme decision (OI-21), not decided here.
- Responses are fixed by FS s12: K1 STOP; K2 one redesign of B then STOP; K3 PIVOT (replay plus structure-aware exploration, no directed-exploration claim); K4 PIVOT to V7-B' and STOP if V7-B' is no better than B1; K5 no confirmatory evaluation. The original "stop entirely if K1 or K5 fail" is superseded for K5 (DOWNGRADE) (CM K-01).
