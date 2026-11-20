# Second-round scientific revision

Manuscript: `main.tex` → `main.pdf`, 27 pages: 20 tables, 15 figures, 6 algorithms, 70 cited references. Branch `research/v8-linux-validation`; round 1 is commit `df612db0`. Nothing in this revision is committed or pushed. This document is new; it is linked from `README.md` and `FINAL_MANUSCRIPT_AUDIT.md`.

## 0. Constraints honoured

- **No experiment was run.** No benchmark, validation run, security probe, ERS perturbation, statistical pipeline or held-out scoring was executed, and no prediction, label, exclusion, manifest, execution record or historical manuscript was modified.
- **What was run.** Only the following executed in round 2:
  - `scripts/make_figures.py`, which draws diagrams and re-plots existing JSON;
  - `scripts/make_stat_figures.py`, which re-plots `audit/stats_summary.json`; the regenerated `tables/tab_ablation.tex` is byte-identical;
  - pdfLaTeX / BibTeX;
  - `scripts/check_manuscript.py`;
  - read-only inspection: `git ls-tree`, `diff` and JSON reads.
- **Files deleted.** Only files inside this directory were removed: `scripts/make_diagrams.py`, `figures/fig_pipeline.pdf` and the bib entry `rezaalipour2024empirical`. All three remain in `df612db0`.
- **Data-derived values.** Every number new to round 2 is listed, with its source, at the end of `NUMERICAL_CLAIM_AUDIT.md`.

## 1. Parts of the brief that could not be followed as written

### 1.1 Part VI: "five-dataset benchmark coverage"

The brief describes the five-dataset suite (Defects4J, BugsInPy, Bears, BugSwarm, Bugs.jar; 250 pairs, 200/50) as genuine benchmark coverage and asks for it to be presented as such. The existing, verified audit (`audit/DATASET_VERIFICATION_REPORT.md`, re-read in round 2) shows the opposite:
- the 250 records come from 12 hand-written templates;
- the commit identifiers are SHA-1 digests of literal strings;
- none of the 180 Java records was compiled or run;
- per-input outcomes are assigned from labels (`executor.pair_to_evidence_record`);
- `integrity_ok` and the Linux environment identifier are hard-coded;
- the activation-stub predictor was used;
- 6 records are duplicates.

Presenting the artifact as benchmark execution would break the brief's own rules: "never fabricate evidence", "do not claim independent correctness validation where the ground truth is based on dataset labels", and "do not invent per-dataset metrics". The revision therefore:
- separates four evidence categories (A–D) and marks category A, multi-dataset benchmark execution, as **not performed**;
- adds Table 11, which lists literature-reported sizes next to what the artifact contains under each benchmark's name, reports **no per-dataset metric**, and gives the evidential status of each row;
- shows the artifact hatched and grey in Fig. 8(c), labelled "excluded";
- adds RQ5, whose answer states that no external multi-dataset benchmark evaluation exists.

The benchmark-breadth score cannot rise until real benchmark checkouts are executed. That would be a new experiment, which the brief prohibits.

### 1.2 "Counterfactual Evidence Calibration"

The brief expands CEC as "Counterfactual Evidence Calibration". The repository's specification (`reports/v8/V8_ERS_SPECIFICATION.md:29`) states that ERS is "not a counterfactual about the programs", and the method conditions on recorded evidence. The paper keeps its round-1 name, **change-conditioned evidence calibration**, because calling it counterfactual would imply causal identification that the method does not provide.

### 1.3 "Statistical uncertainty" and "MDE"

The brief asks for improved statistics. No statistic was recomputed. Table 17 assembles the contrasts that already existed in `audit/stats_summary.json`: effect, 95% CI, one-sided p, Holm-adjusted p and valid-resample share. The B6 contrast was read from the saved Linux run. Power and MDE figures are the round-1 values.

## 2. Corrections to round 1 found during this revision

| # | Round-1 statement | Correction | Evidence |
|---|---|---|---|
| K1 | "A separate real-execution script for P2, P5 and P6 exists, but no raw output from it is in the replication package." | `results/v8_mac_perturb/realexec_matrix.json` (720 per-trial rows, 30 pairs, macOS, pre-fix, dirty tree at `01fdaf09`) **is** on this branch; only the per-run evidence directories are absent. It is now reported as exploratory corroboration. | File listing; per-trial rows read in round 2 |
| K2 | "Abstaining on three quarters of the B1 verdicts" | 122 of 183, two thirds | 183 − 61 |
| K3 | (Implicit) cross-platform evidence was limited to the statistics | The pre-fix post-hoc ERS matrices on macOS (`results/v8_mac_perturb/`) and Linux are identical (empty `diff`) | `diff` in round 2 |
| K4 | Conclusion: "…and has at least one open evaluation-awareness channel" (ungrammatical) | Rewritten | `sections/conclusion.tex` |
| K5 | Six bib entries became uncited in the rewrite | Restored with one scoped sentence each in stream A (regression test selection, property-based testing, regression verification) | `check_manuscript.py`: 70 cited, 0 uncited |

## 3. What changed, by review dimension

`REVIEW_SCORE_IMPROVEMENT_REGISTER.md` gives the per-dimension detail. In summary:

- **Novelty.**
  - A 15-work, 11-column positioning table (Table 2).
  - A defensible novelty statement with no "first" or "novel" claims.
  - Two new conceptual results: Proposition 1, that random abstention preserves expected risk, and Remark 2, that an always-abstaining procedure conforms trivially.
  - `NOVELTY_AND_PRIOR_WORK_ANALYSIS.md`.
- **Technical contribution.**
  - A system model (§III) with a notation table and eight definitions.
  - Remark 1, which formally separates NDO from PROGRAM_EQUIVALENCE.
  - Six algorithms checked line by line against the code. Two corrections were made during that check: the chain verification belongs to the adapter, not `validate_dir`; and integrity is checked before the witness.
  - A component responsibility table, a lifecycle figure, and an ERS property specification table with intent, transformation, pass and fail conditions, implementation, evidence and limitation for each property.
  - A perturbation table with post-hoc and execution-level modes.
- **Literature.**
  - Streams A–H, each with a critical synthesis, and the synthesis matrix (Table 3).
  - Every cell checked against the register's "Must NOT be cited for" column; all 70 references cited.
- **Experimental design.**
  - RQ1–RQ5, each with objective, data, unit, metrics, comparators, analysis and limitation (Table 10).
  - The evidence-category framework, a baseline table, and the matched-coverage algorithm.
- **Statistics.**
  - A full contrast table (Table 17), with valid shares and the strict-policy degeneracy explained.
  - Worst-case risks, and an explicit statement that non-significance is never read as equivalence and that no equivalence margin was pre-registered.
- **Benchmarks.** Presented accurately (§1.1); no change in substance is possible.
- **Reproducibility.**
  - A claim register with ID, statement, section, value, source, artifact, branch or commit, reproduction key, status, limitation and evidence class (RAW, DER, CALC, CONC or SIM).
  - An artifact-mapping table (Table 20) and a traceability figure (Fig. 15).
  - A record of which steps round 2 did and did not re-run.
- **Writing.**
  - The abstract was rewritten to cover problem, gap, method, scope, findings, negative result and limitations (237 words).
  - The introduction was restructured as problem, gap, approach, findings and non-claims.
  - Results are organised by RQ, each ending with an explicit answer.
  - Limitations are stated once per RQ and in the threats table.
- **Figures and tables.**
  - 15 vector figures in one style (`scripts/figstyle.py`) and 20 tables.
  - Each item is mapped in `FIGURE_AND_TABLE_CATALOG.md`.

## 4. Red-team review (round 2)

**Method.** The author of the revision ran this review in the same session, taking five reviewer perspectives in turn. It was not performed by an independent party and should be read as a **simulated** review (class SIM in the claim register), not as evidence. A genuinely independent review would be stronger.

### 4.1 Reviewer 1: software testing

- **Positive.**
  - The estimand is well posed, and Fig. 1 makes the problem concrete.
  - B1 is the right practice baseline.
  - The finding that the predecessor gate cut false assurances from 31 to 13 only by issuing fewer verdicts is useful to the community.
- **Concerns.**
  - Programs are single Python functions with declared inputs.
  - The QuixBugs label and evidence share inputs.
  - There is no comparison with an actual regression-test generator on the same changes.
  - The influence feature is a reachability proxy.
- **Asks.**
  - An adjudicated corpus of real project changes.
  - Checked-coverage or dependence features.
  - Generated tests as an evidence source.

### 4.2 Reviewer 2: empirical software engineering

- **Positive.**
  - Unusually transparent: the exclusion of a label-derived artifact, an evidence-category framework, a claim register, and RQ answers that say "not demonstrated".
- **Concerns.**
  - The whole quantitative evaluation is development data with construction labels, examined during design.
  - One cluster holds 43.8% of the labels, and 46 real-project units are unlabelled.
  - Under construct-validity rules, RQ3 and RQ4 measure agreement with generator and test labels, not false assurance.
  - Benchmark breadth is effectively one external benchmark (QuixBugs).
- **Asks.** Execute the adjudication protocol, and pre-register a held-out corpus.

### 4.3 Reviewer 3: program analysis

- **Positive.**
  - Remark 1 is precise.
  - The integrity-first ordering is argued, and its cost is stated.
  - The algorithms match the code.
  - The threat model is honest about detection versus prevention.
- **Concerns.**
  - The trust architecture is in-process for the tee, and SENSE04b is open.
  - Linux isolation is network unsharing plus a read-only root, with no namespaces or seccomp.
  - O is fixed to four channels, and environment-dependent divergence is not studied.
- **Asks.** Out-of-process capture, anonymised file names, and a Linux re-run with metadata.

### 4.4 Reviewer 4: ML and calibration

- **Positive.**
  - Matched coverage against random abstention, with Proposition 1, is exactly the right comparison.
  - Cluster bootstrap, Holm adjustment, valid-share reporting, no equivalence claims, and an MDE analysis.
  - The strict-policy degeneracy is explained rather than hidden.
- **Concerns.**
  - n = 61 issued verdicts, with an effective n of about 41.
  - Slopes of −1.83 and 0.30 show that the models are not usefully calibrated.
  - The fitted model collapses to one feature.
  - The placebo result is unadjusted.
  - The matched-coverage operating point is transductive.
- **Verdict.** The statistics are now well reported. The study simply lacks the sample to answer RQ4.

### 4.5 Reviewer 5: IEEE Access associate editor

- **Fit.** In scope; the formal and methodological content is substantial.
- **Clarity.** Good. Twenty-seven pages is long but acceptable for Access.
- **Ethics and integrity.** Exemplary disclosure.
- **Main risk.** Reviewers will ask why a method paper whose central predictive hypothesis is not supported, evaluated without adjudicated labels or external benchmarks, should be published now. The defensible framing is a methodology and negative-results paper: an estimand, a conformance protocol that demonstrably caught a defect, an evaluation protocol, and a sized confirmatory study.
- **Expected outcome.** Major revision, or reject-and-resubmit, depending on the reviewers' tolerance for development-only evidence.

### 4.6 Specific assessments requested by the brief

| Question | Assessment |
|---|---|
| Will reviewers recognise five-dataset benchmark coverage? | **No, and they should not.** The paper states that no external multi-dataset benchmark was executed, and it shows the artifact as excluded. A reviewer who checks the repository would find the template generator; presenting it as coverage would be a research-integrity failure. |
| Is the macOS/Linux presentation accurate? | Yes. Table 18 and Fig. 14 distinguish executed outputs, partial outputs (no host metadata, run directories absent, undecided runs) and report-only claims. The cross-platform result is stated as *analysis* reproducibility on identical records, not cross-platform collection. |
| Is novelty clear against the closest work? | Yes, as an integration claim. SemaDiff (dataset-level agreement accuracy), selective classification (the estimand), and checked coverage plus metamorphic testing (the perturbation idea) are each credited, and the delta is stated cell by cell in Table 2. |
| Is the formal method complete? | Mostly. The estimand, verdicts, integrity, eligibility, matched coverage and perturbation response are all defined; Proposition 1 and Remarks 1–2 are stated; there are 6 algorithms. Missing: a formal model of the observation channels' canonicalisation, and any statistical guarantee for the threshold rule. Neither is claimed. |
| Are the figures publication-quality? | Yes: vector output, one style, restrained palette, each traceable to a script. Caveat: Tables 2 and 3 use `\tiny` and will be dense in print. |
| Is the negative result interpreted correctly? | Yes: "not demonstrated", "inconclusive", MDE ≈ 16 pp, no equivalence claim, the sign instability across seeds reported, and the placebo flagged as weak and unadjusted. |
| Are all claims supported? | Within this review, yes. Every number traces to `NUMERICAL_CLAIM_AUDIT.md`. Two statements were softened during the review: "detects estimator defects" became "can detect … found one", and "reproduced exactly" became "to 1e-9". |

## 5. Final decision

### A. Areas substantially improved

- Formal system model and algorithms (technical contribution).
- Literature synthesis and positioning.
- Statistical reporting.
- Reproducibility and traceability.
- Figures and tables.
- The structure of the experimental design (RQ1–RQ5, evidence categories).
- Honesty of the benchmark presentation.

### B. Areas still weak

- Empirical strength: development data only, construction labels, n = 61 issued verdicts.
- Benchmark breadth: one external benchmark executed (QuixBugs).
- Predictive value of CEC and ERS: not demonstrated.
- Linux security evidence: partial and pre-fix.
- One open sensing channel.

### C. Editorial weaknesses that can still be fixed

- Tables 2 and 3 are dense at `\tiny`. Consider moving them to an appendix or supplementary file.
- Some content is duplicated: Table 18 and Fig. 14 overlap, as do Table 14 and Fig. 9.
- Three overfull boxes of at most 6.5 pt.
- Author metadata placeholders (affiliation, e-mail, biography, ORCID).
- Twenty-seven pages; shortening §VIII-A would help.

### D. Intrinsic limitations

- NDO is observation-conditioned by definition. Risk is relative to (O, B, C) and cannot certify equivalence.
- Post-hoc perturbations test estimators, not programs.
- A trust architecture that runs in the evaluated process cannot prevent in-process forgery, only detect it.

### E. Weaknesses that require future experiments (not authorised here)

- Executing the blinded two-adjudicator protocol on an external corpus of several hundred to over a thousand issued NDO verdicts, with an externally timestamped prediction lock.
- Executing real benchmark checkouts (Defects4J, BugsInPy, etc.) through the collector.
- Merging the profile fix and re-evaluating.
- A Linux security re-run after remediation, with host metadata and a diagnosis of the 65 undecided probes.
- Closing SENSE04b.
- Real-execution ERS analogues at scale, with run directories retained.

### F. Final scorecard

Scores are on a 1–10 scale. The revised scores are simulated reviewer judgments.

| Dimension | Round 1 | Round 2 | Main reason |
|---|---|---|---|
| Novelty | 6 | 7 | The delta is now precise against 15 works. Proposition 1, Remark 2 and integrity-first ordering add conceptual content. The integration claim is modest by design. |
| Technical contribution | 5 | 7 | Formal model, definitions, 6 code-checked algorithms and a full ERS specification. Empirical effectiveness is unchanged (negative). |
| Literature coverage | 7 | 8 | Eight streams with critical synthesis; positioning and synthesis tables; all references verified and cited. |
| Experimental design | 4 | 5 | Clear RQ design and evidence categories. Still development-only data with construction labels; cannot rise further without new data. |
| Statistical validity | 6 | 7 | Complete contrast reporting, multiplicity, valid shares, worst-case risk, MDE, no equivalence claim. Sample size is a design limit. |
| Benchmark breadth | 2 | 2 | Unchanged in substance; now presented accurately. Raising it requires executing benchmarks. |
| Reproducibility | 6 | 7 | Claim register, artifact map, traceability figure, script per figure. Some raw run directories are absent (dev collection logs, real-execution runs, Linux metadata). |
| Writing | 8 | 8 | Better structure and explicit RQ answers; longer. |
| Figures and tables | 6 | 8 | 15 consistent vector figures and 20 tables; some tables dense. |
| Overall readiness | 4 | 5 | A coherent methodology and negative-results paper, but the central empirical question remains open. |

### G. Recommendation

**Submit only as a methodology and negative-results paper, and expect major revision.** The manuscript is now internally consistent, fully traceable and honest. Its scientific weight rests on three things:
1. the estimand and the matched-coverage protocol, including the demonstration that a sufficiency gate abstained without improving the false-assurance rate;
2. the ERS conformance protocol, which found a real defect and confirmed it under execution;
3. a transparent, sized negative result.

Higher readiness requires the experiments in §E, above all independent adjudication and execution of real external benchmarks. No amount of manuscript work can substitute for them.
