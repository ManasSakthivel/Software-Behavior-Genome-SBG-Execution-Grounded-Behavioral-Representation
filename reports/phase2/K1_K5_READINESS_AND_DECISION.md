# K1 and K5: readiness and decision (Phase 2)

Branch `research/v7b-final-validation`, HEAD `cc56e029`. Documentation and read-only analysis. This file states what the frozen spec requires, what the development data does and does not show, what can and cannot be decided in Phase 2, and what remains blocked. **It does not declare K1 triggered or cleared, and it does not attempt K5.** Nothing here claims equivalence of any pair, a detection rate, or that any threshold is correct.

## 1. What the frozen spec requires for K1

`reports/final/V7B_FROZEN_SPEC.md` s12:

> "K1 real-pair feasibility (>=100 runnable pairs, >=8 projects): fail STOP."

s13 (authorised scope, the only scope under which K1 is evaluated):

> "(1) build the isolation runner and pass I1-I7 on a Linux container host (Docker was down in P0); (2) a 2-3 week feasibility spike on about 30 candidate projects (build success, drivable fraction, input-representation coverage, determinism, replay activation); (3) evaluate K1 and K2. No K3+ work until K2 passes; any gate failure follows section 12 without renegotiation."

`reconciled/SBG_V7_VALIDATION_AND_ACCEPTANCE_GATES.R1.md` B.0 (single K table, D9) fixes the measurable test:

> "Count of runnable real pairs: both versions import and execute at least one input to completion under the P1 isolation runner, scope has a drivable signature, no network/GPU/interactive need" ... Fixture: "DEV-N real-regression pilot mining (not V5/V6 generators, not sealed sets); timing: end of the feasibility pilot, before G1 closes" ... Threshold: ">= 100 runnable real pairs from >= 8 independent projects" ... Failure response: "STOP" ... Reproducibility: "Mining script and candidate list hashed; deterministic ordering; independent rerun reproduces the count; excluded-units ledger attached".

`reconciled/SBG_V7_IMPLEMENTATION_ROADMAP.R1.md` row 3.4: K1 is "project-level under D10 isolation", **Phase 3, not started**; K1 and K2 are exit conditions of G1, and containment (zero escapes) is a hard G1 sub-gate. FS s10: "Third-party repositories run only under Linux container isolation; macOS runs are synthetic/benchmark-only, flagged `policy_below_minimum`."

Elements of the K1 definition, each of which must be met by a real evaluation: (a) fixture is a DEV-N real-regression pilot, not generators or sealed sets; (b) executed under the P1 isolation runner (Linux container, I1-I7 passing); (c) project-level scope with a drivable signature; (d) >= 100 pairs and >= 8 independent projects; (e) hashed mining script, deterministic ordering, independent rerun, excluded-units ledger.

## 2. What the development data shows

Source: `research/evaluation/K1_K2_FEASIBILITY_REPORT.md` (Phase 1 spike on macOS, `sbgv7` at the then-current engine; superseded numbers in its last section).

| Quantity | Value | Counts toward K1 as defined? |
|---|---|---|
| QuixBugs buggy/fixed | 31 pairs, 30 runnable, counted as 1 project | Not project-level; one benchmark, one repository; burned set |
| BugsInPy extracted single-file units | 55 pairs, 44 runnable, 12 projects | Not project-level runs; synthetic-battery inputs, not project tests; burned set |
| Total real pairs available to the spike | 86 | - |
| Runnable real pairs | **74** | below 100 |
| Projects with project-level runs | **0** of >= 8 | below 8 |
| Synthetic v8/v10 and QuixBugs-negative pairs | 150 + 85 | excluded by definition (generators) |

Answers to the question asked:

1. **Is there a shortfall independent of the Linux requirement?** Partly. Even with every generous reading (units counted as pairs, QuixBugs as one project, synthetic inputs accepted), the existing real-pair inventory the spike could draw on is 86 pairs, so no re-count of that inventory can reach 100; and its "13 projects" are 1 benchmark plus 12 unit extractions, with **no** project-level execution (0 of >= 8). Those facts do not depend on Linux. But they describe an inventory that was never the K1 fixture: K1 is measured on a DEV-N pilot whose mining (about 30 candidate projects) has not been done. A shortfall of the existing inventory against a threshold defined on a different, not-yet-collected fixture is a risk indicator, not a K1 failure.
2. **Is the 74 stable?** No. The spike ran before commits `8f11d3aa` and `cc56e029`. Those fixes change which pairs end in `no_inputs` or `unobservable_outcome` (lossy/degenerate `SAME` no longer counts; both-side binding failures are `NO_RUN`), which are inside or at the edge of the spike's own "runnable" definition (it excluded import_error, unsupported_signature, alignment_failed, tool_error, sandbox_failure, no_inputs). The count could only fall or stay; it was not re-run here (a re-run is local synthetic/benchmark execution and is not part of this documentation task).
3. **The spec does not define "runnable" beyond the K table text** ("import and execute at least one input to completion under the P1 isolation runner ... drivable signature, no network/GPU/interactive"). The spike's operational definition is a reasonable reading; under the K table it additionally requires the P1 (Linux) runner, which the spike did not use.

## 3. Can the formal K1 STOP be evaluated in Phase 2?

**Decision: no. K1 is neither triggered nor cleared by Phase 2.** Reasoning:

- The STOP is defined as failure of K1 on the fixture and runner named in s13 and the K table. Three of its five defining elements cannot be satisfied in Phase 2: (b) the P1 isolation runner (Linux container passing I1-I7; the macOS runner is below the minimum policy by FS s10); (c) project-level execution, which FS s10 forbids outside Linux containers for third-party repositories; (e) the mining script and candidate list, which do not exist, so no "independent rerun reproduces the count" is possible.
- The repository itself records the same conclusion: roadmap R1 row 3.4 "not an evaluation of K1 as defined", OI-21, U2 of `PHASE_2_RECONCILIATION_INDEX.md`.
- To declare K1 **cleared** would need >= 100 qualifying pairs: impossible with the 86-pair inventory. To declare it **triggered** (STOP, which ends the programme with a negative-result report) on this data would apply a gate to a fixture the gate does not name, using an engine state that has since changed, on a runner below minimum policy; that would be an unrequired, irreversible step. The required evidence is absent in both directions.
- What Phase 2 can truthfully state: "On the existing development inventory K1 would not be met (74 runnable of at most 86 real pairs; 0 project-level runs). K1 as defined has not been evaluated."

**Programme decision (UD-5 in `FINAL_SPECIFICATION_DECISIONS.md`).**

| Option | Consequence |
|---|---|
| A. Leave K1 open; authorise the Phase 3 spike (Linux isolation first, then about 30 candidate projects) and evaluate K1 there (recommended) | matches FS s13; Phase 3 is not started and needs explicit authorisation; risk: effort spent before a possible STOP |
| B. Declare K1 failed on existing data and STOP now | literal reading of "fail STOP"; ends the programme on non-fixture evidence |
| C. Amend K1 so the existing inventory passes | not recommended: FS s13 says "without renegotiation", and thresholds change only through the development split, not to avoid a stop |

A cheap, honest risk-reducing step inside the Phase 2 boundary (not done here): estimate on paper how many post-T0 candidate projects with drivable regression tests exist (feasibility of mining is already flagged as an open risk, CHANGELOG U-1), without executing any third-party code.

## 4. What stays blocked pending Phase 3

| Blocked item | Blocking dependency |
|---|---|
| K1 evaluation and the STOP decision | Linux container runner passing I1-I7; mining of about 30 candidate projects; hashed mining script and ledger |
| K2 (determinism >= 70 %, replay+crude activation >= 35 %) | K1 pairs under D10 isolation; the spike's K2 figures are indicative only |
| K3 (explorer activation >= 60 % and +15 points) | the explorer (absent), K2 pass |
| K4 (FAR vs like-for-like comparators at matched coverage >= 0.60) | comparators, explorer or V7-B' fallback, K3 outcome, development set |
| K5, sealed-holdout unseal, G5-G7 | section 5; independent benchmark and adjudication |
| Any claim about real-project performance, third-party execution, zero-escape containment, calibration of S1/S2/S3 miss rates | Linux hostile fixtures; calibration data |
| Re-measuring the Phase 1 spike numbers on the fixed engine | optional local step; needed before any figure from it is quoted as a current engine property (the three-pair post-fix note covers only the NO_RUN fix) |

What Phase 2 may still do locally and is listed in `MANDATORY_IMPLEMENTATION_BACKLOG.md`: close the false-assurance defects (MB-01, MB-02, MB-03, MB-05), which would otherwise contaminate whatever K2/K1 data is collected later.

## 5. K5 (preserved, not attempted in Phase 2)

K5 is preserved exactly as frozen (FS s11/s12 and GATES R1 B.0):

> K5: ">= 60 independent projects (clusters), >= 250 independent-lineage divergent pairs, >= 20 mixed-class projects; adjudication kappa >= 0.7 with the CI rule of EP 3.5; leakage audit clean (zero cross-split duplicate groups; shortcut and diff-shape probes <= 0.65 or matched subset declared; no label-correlated input path)". Failure response: "DOWNGRADE: no confirmatory evaluation; exploratory report only". Placement: exit of G5, before G6; unseal is one shot after K5 and G5-G7. (FS s12: "K5 power-sized benchmark, kappa, clean leakage audit before any unseal: fail means no confirmatory evaluation (exploratory report only).")

The planning target in EP R1 s3.2 is >= 80 projects and >= 320 pairs (80 % power at +10 pp, multiplicity-adjusted); 60/250 is the hard floor (unresolved open item O11). Feasibility of mining 60-80 fresh post-T0 projects is not demonstrated.

### 5.1 Phase 3 validation protocol (exact sequence)

1. **Prerequisites.** K1 and K2 passed (or their failure responses executed), Linux containment gate passed, G0 closed (EP, GATES and SPEC hashed; custodian appointed; T0 declared; power analysis re-run with DEV-N estimates and sample targets amended pre-seal).
2. **Corpus H-R.** Python projects not in BugsInPy, QuixBugs or V5/V6 base programs; project-disjointness verified by repository URL, package name and source-hash overlap; only commits dated after T0 and after the last day any V7 development data was collected; project list frozen by hash before commits are examined. Divergent pairs: (parent, fix) commits where a regression test added by the fix fails on the parent and passes on the fix, scope = the touched function/class set with a drivable signature. Controls: behaviour-preserving (parent, child) commits with the full suite passing on both. Exclusions fixed before mining with a ledger: network/external service, GPU/hardware, interactive input, undrivable signature (counted, not dropped).
3. **Counts.** >= 60 independent projects, >= 250 independent-lineage divergent pairs, >= 20 projects contributing both classes; computed by a hashed script from the manifest.
4. **Truth and adjudication.** Truth harness built by the custodian side with a separate capture path (evidence tiers T0-T3; any harness-found witness is conclusive for divergence); two blind adjudicators A1, A2 with a versioned hashed rubric, a third blind adjudicator A3 for disagreements, pre-resolution votes kept; `label_original` immutable and `label_final` adjudicated.
5. **Agreement.** Pilot on >= 60 DEV-N items; for the collapsed three-class scheme (divergent / no-output-difference / insufficient) on a >= 100-item double-rated sample (all items if fewer): kappa >= 0.80 with CI lower bound >= 0.70 per EP 3.5; K5's gate floor is kappa >= 0.7 (D9). Report PABAK and specific agreement. Label-noise audit of the no-output-difference class (fatal above about 2 % in the pilot); class-5 share > 15 % of a source flags the source.
6. **Leakage audit (all must be clean).** Zero cross-split duplicate groups and zero source-hash overlap; generator-fingerprint probe and edit-size/diff-shape probe AUROC <= 0.65 or the matched subset declared primary; leave-project-out folds (>= 8) on DEV-N and H-R; label-independence of inputs and a label-shuffle negative control (outputs byte-identical when labels are withheld); results hold under `repr` normalisation; LLM-involved components disclosed with identifier and cutoff.
7. **Commitments.** Hash-committed manifests; labels frozen at sealing; custodian signs counts, kappa ledger and the hashed audit report.
8. **Outcome rule.** All of the above met: confirmatory evaluation may proceed (still subject to G5-G7 and K4). Any one failed: DOWNGRADE (no unseal; exploratory report with confidence intervals only; stated in advance).

### 5.2 Evidence the engine must supply for K5 (what Phase 2 can prepare, not produce)
The engine side can only be exercised after K1/K2/K3/K4 and the Linux gate; its prerequisites from this review are: no known false-assurance path (backlog MB-01, MB-02, MB-03, MB-05), a pinned control profile so determinism rates are meaningful (MB-07), a verified evidence chain per pair (`sbgv7 verify` exits 0), and label-free operation (D11).

### 5.3 Explicit statement
**Phase 2 does not attempt K5.** No holdout was constructed, opened, mined, adjudicated or scored; no leakage audit was run; no kappa was computed; no unseal occurred or was prepared. K5 remains a Phase 3 gate, not started, not authorised by this document.
