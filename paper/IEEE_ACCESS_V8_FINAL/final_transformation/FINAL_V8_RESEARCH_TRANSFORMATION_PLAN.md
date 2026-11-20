# SBG V8 final research-readiness transformation: plan
New file; linked from `../README.md`. Written before any manuscript change or experiment. Parts 3 (partly), 4-12 are **not yet executed**; this plan and the Part 2 audit are.

## A. Actual state of the research
- A formally argued methodology paper (estimand, integrity-first decision, ERS conformance, propositions) with a **312-pair development-only** evaluation: central comparison B7−B8 +1.6 pp [−6.6, +16.3], MDE ≈ 16 pp, n_eff ≈ 41. Honest negative result on predictive value.
- **No held-out external evidence exists.** Neither the five-dataset run nor the earlier workstream qualifies (below). No independent adjudication has been done.
- The manuscript already says this (RQ5, Table 11, conclusion); the audits confirm those statements and found no claim that needs retraction.

## B. Verified external execution evidence
None. Verified building blocks only: upstream QuixBugs (`4257f44b`) and BugsInPy (`11c5f1ee`, sample commits) exist and are checked into `external/`; V6 phase-2 raw run archives (7, checksums OK) hold real executions of QuixBugs and BugsInPy units, but those are development subjects.

## C. Invalid, uncertain, partially supported
| Item | Status |
|---|---|
| Five-dataset run (250) | Generated stand-ins; label-derived outcomes; 2,250 ERS cells not 2,500; no Podman/Java evidence; export not blind → pipeline demonstration only |
| Earlier QuixBugs / BugsInPy | Real code, partial execution; development/tuned; V5 method; per-case results partly absent |
| Earlier Bugs.jar / Codeflaws | Hand-written stand-ins; unresolvable tag (Bugs.jar) |
| `/root/sbg_sprint` VM | Absent on this machine (`/root` missing); not recoverable |
| Phase-2 archive ↔ V8 dev linkage | Unverified; archive not extracted |

## D. Development/external overlap
Five-dataset: 0 identifier overlap, but not real. Earlier workstream: 31/40 QuixBugs programs and 43/51 BugsInPy bugs are V8 dev data; 17 cases `UNCERTAIN`; source-fingerprint check not done (could be done for the local QuixBugs/BugsInPy sources). Registry: `EXTERNAL_CASE_EVIDENCE_REGISTRY.json`.

## E. Claims requiring correction (none applied yet)
1. Any repository document claiming "real-world", "Podman-isolated", "100% reproducible" or "2,500 trials" for the five-dataset run (reports under `reports/v8/independent-validation/`) must be annotated as superseded; manuscript text already excludes it.
2. `reports/external_validation/` manifest wording ("Valid Cross-Language … Benchmark", "100% Passing") should be annotated, not deleted.
3. README/REPRODUCIBILITY: add the audit pointers (done for README; REPRODUCIBILITY pending).
4. Open manuscript items: P1–P9 vs "properties 1–8"; placeholder affiliation/biography; length.

## F. Additional experiments genuinely necessary
Exactly one, because no existing evidence can address the gap (no held-out real data):
**E-REAL**: freeze V8 (code hash, thresholds, predictions) and run it on real checkouts of 150-300 pairs at authentic commits, chosen from BugsInPy bugs not in V8 dev (≥ 8 unused eligible now; need more projects), plus Defects4J/Bugs.jar with a JVM tracer if available; Linux container with logged digests; original tests recorded; predeclared inclusion/exclusion; two-reviewer blind adjudication of NDO verdicts (protocol in `../external_validation_audit/`).
- Gap: external validity and false-assurance risk on real code. Why existing evidence can't: it is development or generated. Effort: high (JVM tracer, environments, reviewer time ≈ 45 min × 2 per NDO case). Statistical value: with ~300 pairs and ~100 issued NDO verdicts the MDE falls from ≈ 16 pp to roughly 12 pp; still modest, so claim *estimation*, not superiority. Threats: project clustering, reviewer disagreement, trace-tool coverage, selection into buildable projects.
Optional cheap step, no new execution: hash-based source-fingerprint overlap of `external/` units vs dev inputs; verify the phase-2 archive ↔ dev linkage.

## G. Manuscript changes required (after approval)
Only those that follow from audited evidence: fix the property labelling; replace placeholder affiliation/biography with facts you supply; shorten by moving audit material to supplements; add pre/postconditions to the 6 algorithms; align abstract/intro/conclusion with the evidence class table. No result or claim is strengthened.

## H. Reproducibility engineering
Demonstrated: statistical reproduction macOS↔Linux to 1e-9 on identical records. Not demonstrated: raw dev collection from checkout, container isolation, five-dataset execution. Work: one-command `make reproduce` for the statistics and figures (feasible now), pinned environment manifests (`pip freeze`, OS facts from this machine only), checksum manifest of `external/`, explicit "not reproducible from this repo" list. Do not claim Podman or cross-platform execution beyond what is evidenced.

## I. Prioritised roadmap
1. (done) five-dataset audit; Part 2 audit; this plan.
2. Verify phase-2 archive ↔ dev linkage and compute source-fingerprint overlap (read-only).
3. Statistical recomputation audit (Part 7) from `dev_records.jsonl` and saved outputs; scripts in `STATISTICAL_ANALYSIS_SCRIPTS/`.
4. Proof audit and novelty/related-work matrix (Part 8).
5. Reproducibility package (Part 9).
6. Manuscript editorial fixes (Part 10), rebuild PDF, run `check_manuscript.py`.
7. Internal reviews, labelled **simulated** (Part 11); the earlier R1-R5 never ran.
8. Scorecard (Part 12). Decide on E-REAL with you.

## J. Is 9+/10 achievable with existing evidence?
**No.** Experimental design, benchmark breadth/external validity and statistical validity (together 35% of the weight) are bounded by development-only data and an underpowered central contrast; no editing can raise them without new real-execution evidence and adjudication, and unverified external evidence must cap the score. Provisional, unvalidated estimate of the achievable ceiling from the work in items 2-7: roughly 6-6.5 overall (benchmark breadth stays ≈ 2-3; reproducibility ≈ 7-8; writing/figures ≈ 8). Reaching 9 needs E-REAL with real adjudication, and even then a result like the current one (no predictive gain) would keep novelty/contribution scores below 9. I will not raise a score without evidence.

## Needed from you
- Decision on E-REAL (new experiment, real checkouts, reviewers). Without it the ceiling above stands.
- Real affiliation/biography text.
- Whether the repo may be pushed/committed (nothing committed so far).
