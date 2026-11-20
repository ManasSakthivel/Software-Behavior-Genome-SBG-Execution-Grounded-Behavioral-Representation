# Review R2: Empirical Software Engineering

**Manuscript:** "SBG V8": false-assurance risk of no-divergence verdicts in differential regression testing (IEEE Access submission, `paper/IEEE_ACCESS_V8_FINAL/`)
**Reviewer expertise:** empirical SE study design, validity, benchmark methodology, negative results
**Materials examined:** `main.tex`, all of `sections/` and `tables/` in include order, `CLAIM_EVIDENCE_REGISTER.md`, `NUMERICAL_CLAIM_AUDIT.md`, `audit/DATASET_VERIFICATION_REPORT.md`, `audit/STATISTICAL_AUDIT_REPORT.md`, `audit/oof_seed0.json`, and `datasets/v8/dev_records.jsonl` / `DEV_MANIFEST.jsonl`. I used read-only Python counts over the records and OOF file. I did not re-run any pipeline.

---

## 1. Summary

The paper treats a "no divergence observed" (NDO) verdict from differential regression testing as a selective prediction. It defines a false-assurance risk relative to an observation boundary and an adjudication budget, and proves four short propositions: boundary monotonicity, integrity-must-gate, random abstention preserves risk, and conformance is independent of accuracy. It then presents SBG V8, which has four parts: a change-conditioned evidence profile, a sign-constrained calibrated abstaining model (CEC), an integrity-first trust gate, and an "Evidence Response Signature" (ERS). ERS is a set of eight properties checked by post-hoc evidence perturbations.

The empirical part is a pilot on 312 development pairs: 150 synthetic, 116 QuixBugs-derived and 46 BugsInPy function units. Only 258 pairs carry construction labels. The headline numbers are:

- plain differential testing (B1) has a false-assurance risk of 0.169;
- the predecessor gate (B3) has 0.213 at one third of B1's coverage;
- CEC is not shown to beat coverage-only calibration at matched coverage (+1.6 pp, CI −6.6 to +16.3, MDE ≈ 16 pp);
- ERS found one profile defect.

A security evaluation and an "evidence-scope" RQ5 complete the paper. RQ5 documents why a project-internal "five-dataset" artifact is excluded.

The authors are unusually candid. Non-claims, threats, design controls and artifact provenance are all disclosed in detail. My concerns are not about hidden weaknesses. They are that (a) some headline numbers have construct problems the paper does not disclose, (b) several comparisons are confounded by the candidate pool rather than by the method, and (c) the benchmark component is thinner than its presentation suggests.

---

## 2. Strengths

1. **Clear estimand and honest scoping.** The NDO ≠ equivalence remark is explicit (`problem.tex:83-85`). Boundary and budget relativity is made formal (Prop. 2, `problem.tex:117-122`). The non-claims list (`introduction.tex:71-80`) is a model for the field.
2. **Matched coverage against random abstention.** Prop. 3 (`problem.tex:130-135`) and its use in RQ3 address a real and common flaw in abstaining-tool evaluations. The point that "the gate abstained on two thirds without lowering the rate" (`results.tex:57,62`) is methodologically valuable.
3. **Negative result reported properly.** It comes with an MDE/power analysis (`results.tex:88`), an interpretation table separating "no evidence of improvement", "evidence of no improvement" and "equivalence" (`discussion.tex:13-32`), Holm adjustment, and per-seed sign instability.
4. **Self-audit of a flawed internal artifact.** The five-dataset artifact is excluded with specific reasons (`results.tex:144-154`; `audit/DATASET_VERIFICATION_REPORT.md` §§1, 4). This is good scientific practice.
5. **Traceability.** The register and artifact table (`reproducibility.tex:6-31`) make every number auditable. My spot checks matched: B1 183/31, B3 61/13, B4 141/17, B5 144/18, soft-eligible 85 (24 positive) and the arm/label counts in Table `tab:corpus` all agree with `dev_records.jsonl` and `oof_seed0.json`.
6. **ERS as a label-free conformance test.** The idea of metamorphic-style relations on the *estimator's evidence* is sound. Accounting for N/A trials and abstention credit separately (`ers.tex:14-26`) avoids vacuous passes.

---

## 3. Major concerns

### M1. The headline B1 risk (0.169) includes vacuous "verdicts" with no executed input

**Evidence.**
- In `dev_records.jsonl`, 49 of the 183 labelled B1 NDO verdicts come from records with **zero** input records. All carry the blocker `unsupported_signature`: 31 QuixBugs negatives and 18 synthetic pairs. 46 of these 49 are Y=0.
- B1 is defined as "NDO unless a witness exists" (`design.tex:158`), so an unexecuted pair counts as an "all inputs agree" pass.
- Restricting B1 to pairs with at least one `SAME` input gives 27/133 = **0.203**, not 0.169.
- The paper never mentions zero-input records. `design.tex:72` reports only "1,976 input records" over 312 runs.

**Why it matters.** No practitioner's differential-testing pipeline reports "no difference" when the harness could not call the function. That is an error or skip. The 0.169 figure in the abstract, the introduction (`introduction.tex:42`), the discussion ("one in six", `discussion.tex:4`) and the conclusion is diluted by non-observations that are overwhelmingly Y=0. This is a construct-validity problem for the practice baseline. It also distorts the B1-vs-B3 comparison behind "abstention is not reliability": part of what B3 "abstains" on is these non-runs.

**Fix.**
- Redefine B1 to require at least one executed comparable input, or report both variants.
- Add a row to `tab:corpus` for zero-input or unsupported-signature records.
- Re-state the headline.

No new experiments are needed. This is a recount from existing records.

### M2. The synthetic construction labels may contain many equivalent mutants, and the paper does not discuss this

**Evidence.**
- 29 of the 31 B1 false assurances and all 13 B3 false assurances are synthetic (`design.tex:109`; recount from records).
- Synthetic Y=1 pairs all come from semantics-changing operators (`sc*` in the pair id). Y=0 pairs all come from semantics-preserving operators (`sp*`).
- The misses are concentrated by operator:
  - SC-4 accounts for 12 of 29 synthetic B1 misses and 8 of 13 B3 misses;
  - per the repository's `benchmark/transformations/mutations/mutator.py:310-330`, SC-4 is `BoundaryConditionMutator`, which "remove[s] a guard/boundary check" by replacing its body with `pass`;
  - removing a redundant guard is a textbook source of equivalent mutants.
- The same file's module docstring (`mutator.py:21-27`) records that on the project's *original* benchmark "135 of 336 CHANGED-labelled test pairs (40%) carry a mutation that is unreachable … and the CHANGED label is false."
- The paper describes Y as "the generator's record of whether the injected change alters behaviour on the declared domain" (`problem.tex:169`). It neither states that this was verified nor discusses equivalent-mutant contamination.
- The threats table says only that risks "may be biased in either direction" (`threats.tex:15`).
- 6 pairs were dropped as `SUSPECT_LABEL` (records' `meta.truth_raw`). The criterion is not described. Three of them were V7-B DIV verdicts on EQUIVALENT-labelled pairs.

**Why it matters.** If a material fraction of the 29 synthetic "misses" are equivalent mutants, the false-assurance risk is overstated, perhaps substantially. Every RQ3/RQ4 contrast is then driven by label noise concentrated in one operator. Operator is also an unmodelled cluster: the bootstrap clusters by program (`design.tex:78`), not by operator.

**Fix.**
- State which mutator version generated the Phase-2 pairs and whether site restriction was applied.
- Describe the SUSPECT_LABEL criterion and show that it is outcome-independent.
- Manually adjudicate the 31 B1 misses, which is a small and feasible set, using the paper's own two-adjudicator protocol. Report how many are confirmed divergences.
- Report risk by operator.

This needs human adjudication of about 31 pairs, which is modest. It needs no new pipeline execution.

### M3. The candidate pool confounds the matched-coverage contrasts, and the B6 "chance" reference is the wrong comparator for CEC

**Evidence.**
- B6 is defined as random abstention among the **183 B1-issuable pairs** (`design.tex:163`). Its expected risk is 0.169 (`tab_ablation.tex:16`).
- The calibrated models can issue only among the **85 soft-eligible pairs**. These have 24 positives, a base rate of **0.282** (`oof_seed0.json`; also `audit/STATISTICAL_AUDIT_REPORT.md:44`).
- The soft eligibility filter therefore *raises* the risk of the pool by about 11 pp before any model ranks anything. One reason: the blocker `unmodelled_change` occurs only on Y=0 pairs (43 of 43; recount), and the soft policy excludes it.
- "B6 − B8 = −4.4, not better than chance" (`results.tex:76`, `tab:stats` row 3) therefore mixes a pool effect with a ranking effect. Against random abstention *within the eligible pool* (expected 0.282), B8's 0.213 would be about 7 pp better.
- With 85 eligible and 61 to issue, every model can withhold only 24 pairs. The primary contrast B7 − B8 = +1.6 pp is exactly **one false assurance out of 61** (14 vs 13). The paper never states this unit-level magnitude.
- QuixBugs is a single cluster and occupies all of fold 0 (113 pairs, 24 eligible, 0 positives; `oof_seed0.json`). So a large share of every model's issued set is a fixed block of Y=0 QuixBugs negatives, and the ranking signal comes from about 61 eligible synthetic pairs.
- The paper says ranking is within each outer fold (`design.tex:175`), but fold 0's quota (about 26.7) exceeds its 24 eligible pairs. How this is handled is not explained.

**Fix.**
- Add a within-pool random-abstention reference (B6′) for each eligibility policy.
- Report effects in pairs as well as pp.
- Explain how the per-fold quota is handled when it exceeds the eligible count.
- State that the strict-policy analysis is degenerate by construction (`results.tex:78`) and move it out of the main tables.

This is analysis only, with no new experiments.

### M4. A simple coverage rule dominates every proposed model, and the paper calls it "suggestive only"

**Evidence.** B4 (full activation plus branch floor) issues 141 verdicts at risk 0.121, and B5 issues 144 at 0.125 (`tab_ablation.tex:14-15`). Both have higher coverage *and* lower risk than B3 (61 at 0.213) and than every calibrated model (61 at 0.213–0.295). The paper dismisses the ordering as "suggestive only" (`results.tex:62`) and does not compare B4 against random abstention at B4's own coverage.

**Why it matters.** This is the only operating point in the study where abstention looks informative (0.121 < 0.169). It directly qualifies the "Abstention is not reliability" message (`discussion.tex:6`). It also suggests that the restrictive eligibility policy, not the evidence profile, is what limits CEC.

**Fix.**
- Report B4 and B5 vs random abstention at their coverage, with cluster-bootstrap CIs.
- Evaluate CEC on the B1-issuable pool, with no eligibility filter, at c = 141/258, and compare it with B4.

This uses existing records and the existing statistics code. It is a re-analysis, not a new data collection.

### M5. The benchmark arms are presented as broader than they are

**Evidence.**
- **QuixBugs.** The 31 buggy/fixed pairs contribute **zero** NDO verdicts (27 DIV, 2 INS, 2 unlabelled; `tab:corpus`, `design.tex:91`). They therefore contribute nothing to any risk numerator. The 85 "QuixBugs negatives" are project-generated semantics-preserving variants, not QuixBugs data, and 31 of them have zero inputs (M1). Effectively, the QuixBugs arm adds 84 Y=0 denominators in one cluster, which holds 43.8% of the labels (`design.tex:78`). It is not a benchmark evaluation of false assurance. The paper also does not say why only 31 of QuixBugs' 40 Python programs were used.
- **BugsInPy.**
  - The 46 units are function-level extractions run on "declared" inputs (all inputs carry `provenance: declared`), not on the projects' test suites. They are therefore not "real-project changes" in the usual sense (`results.tex:143`).
  - youtube-dl supplies 17 of the 46 units (37%), so cluster dominance recurs here.
  - The units are unlabelled (`design.tex:76`), yet BugsInPy bugs come with fail-to-pass tests, and a bug-fix commit is behaviour-changing at least on its triggering test.
  - The 8 NDO verdicts that V7-B issued on BugsInPy units (`results.tex:143`) are therefore *candidate false assurances on real code*. They are the most externally relevant data in the paper, and they go unanalysed.
  - The 70% vs 47% abstention comparison (`results.tex:143`) is unadjusted and confounded by input source.
  - 9 of 55 extractions failed silently (`design.tex:76`).
- **Evaluation landscape table** (`design.tex:45-69`). Rows B–E (real-execution analogue, cross-platform analysis of the *same* records, attack suites, the unit test suite) are listed as "evaluation settings" next to the corpus. Calling these "five executed evaluation settings" (`results.tex:143,165`) inflates the apparent breadth. Only row A produces evidence on program changes, and within it only the synthetic arm carries information about false assurance.
- **Synthetic splits.** Synthetic pair ids carry Phase-2 `train/val/test/dev` prefixes (for example 56 `test__` pairs). Phase-2 test partitions were pooled into development without comment. This matters for exposure (M6).

**Fix.**
- Re-describe the landscape. Separate "evidence on program changes" (A) from "system validation" (C–E).
- Report how many risk-informative pairs each arm contributes.
- Label the 8 BugsInPy NDO units by inspecting the BugsInPy trigger tests. This is a small manual task. Running the tests would be new execution.
- Report per-project counts for BugsInPy.
- Explain the QuixBugs program selection and the Phase-2 split pooling.

Mostly no new experiments. Labelling BugsInPy by running tests would require execution.

### M6. Development exposure and a "pre-registered" framing that the record does not support

**Evidence.**
- The paper calls H1a–H4 "pre-registered" and the analysis plan "fixed before evaluation" (`design.tex:197,203`). It also states that the corpus "was examined repeatedly during design" (`design.tex:111`) and that two method changes followed results on the same records (`threats.tex:18,28`).
- No external timestamp exists for any plan or lock (`audit/DATASET_VERIFICATION_REPORT.md:166`).
- The ERS feature set and the integrity-first ordering were tuned on these 312 records. The profile fix was evaluated on the same records that revealed the defect (`approach.tex:154`; `results.tex:41`).

**Why it matters.** "Pre-registered" has a specific meaning in empirical SE: time-stamped and public before data access. Using the term here invites readers to treat the results as confirmatory. The negative result is somewhat robust to this, since exposure would bias toward SBG. The positive claims (the ERS defect detection and the trust gate's 312/312) are not.

**Fix.** Replace "pre-registered" with "internally specified analysis plan (not externally registered; data previously examined)" throughout. This is text only.

### M7. The evidence for RQ2 (ERS as a defect detector) is one anecdote on an author-built probe

**Evidence.**
- The single detected defect was found on an *unfitted, hand-signed* "all-feature probe" (`tab_ers.tex:27`). The fitted model passed P2 throughout because it uses essentially one feature (`results.tex:41`).
- The abstract says the signature "exposed a profile defect invisible to aggregate metrics". It is invisible to aggregate metrics because no evaluated predictor was affected by it.
- P8 passes 312/312 "by construction" (`tab:ersprops`, row 7).
- For the fitted model, P4, P7 and P9 are vacuous (`results.tex:49`), because the corresponding features were constant (`approach.tex:152`).
- The real-execution analogue could apply P2 to 7 of 30 pairs and P6 to 1. Its supplementary cohort was selected using labels (`ers.tex:106`), even though row B of `tab:benchmarks` says "label-free".
- `audit/DATASET_VERIFICATION_REPORT.md` §5.2 says the defect was "found by P2 on 9 dev records", while the paper says 109/227. Please reconcile.

**Why it matters.** "ERS detects estimator defects" is the paper's "most transferable result" (`discussion.tex:8`). Its support is n = 1, and no comparison is made with cheaper alternatives such as unit tests on feature definitions or code review.

**Fix.** Run a seeded-fault study on the estimator. Inject k ≥ 20 realistic defects into `profile.py`, `calibrate.py` and the decision code. Report ERS detection rate vs aggregate-metric change vs the existing unit tests. This is a new experiment, but it is cheap: post-hoc only, with no program execution. Also soften the abstract.

### M8. The scope of the paper is diluted by the security material and RQ5

**Evidence.** The paper is 29 pages with 23 tables and 12 figures. RQ5 is not a research question about the phenomenon. It is a provenance audit of the authors' own artifacts (`design.tex:9`; `results.tex:142-165`). The security evaluation (RQ1) uses author-written attacks with one platform re-run (`tab_security.tex`), and 65 of 74 Linux probes are undecided (`results.tex:22`).

**Why it matters.** For an empirical SE reader, the contribution is the estimand plus the negative pilot. The excluded artifact does not need a research question, a figure panel (`fig:landscape`(c)) and a landscape row. Prominent discussion of a template-generated artifact with fabricated SHAs (`audit/DATASET_VERIFICATION_REPORT.md` §1) may raise questions at the editorial level, for example whether earlier reports citing it were disseminated. A short disclosure paragraph serves transparency better.

**Fix.**
- Fold RQ5 into a "Data provenance" subsection plus one sentence in Threats.
- Move the bulk of the security tables to a supplement.
- Remove the five-dataset panel from Fig. `fig:landscape`.

Text and structure only.

---

## 4. Minor concerns

1. **Rounding.** `introduction.tex:43` says the gate "abstained on two thirds … (0.213)", but 122/183 = 0.667 refers to B1 verdicts, not abstentions overall. Phrase this consistently with `results.tex:57`.
2. **Cluster counts.** `tab:corpus` lists 101 synthetic clusters, but only 100 synthetic programs carry labels (one program has only unlabelled pairs). The footnote "101 labelled projects" (`tab_ablation.tex:34`) is 100 synthetic plus 1 QuixBugs. Clarify.
3. **Input generation.** The input-generation procedure for each arm is never described: who declares the inputs, how many, and whether the generator saw the change. Yet `n≤12` and multiplicity are central features. Add a paragraph.
4. **Two policies.** `tab_ablation.tex` presents the strict-policy block with CIs that the caption calls "not reliable". Drop it to a footnote.
5. **Calibration.** A calibration slope of −1.83 for B7 (inverted ordering) on 85 pairs suggests that the coverage-only model is mis-specified or overfit. Show the fitted coefficients.
6. **Placebo test.** The permutation placebo (`results.tex:80`) is on a different branch, with 100 permutations and unadjusted p. Either report it with the same rigour as the rest or drop it.
7. **Prop. 4 proof.** Prop. 4(ii) (`problem.tex:162-164`) holds for any off-support test, not only ERS, so it is close to trivial. Present it as a remark.
8. **Influence feature.** `obs_react` is called an "influence" feature, but it is reachability (`approach.tex:152`). Rename it to avoid construct confusion.
9. **Collection platform.** The platform is unrecorded for all 312 records (`results.tex:163`), yet `tab:benchmarks` lists "one env. id". State that the collection environment cannot be identified.
10. **Literature.** Equivalent-mutant literature (for example Madeyski et al., TSE 2014; Papadakis et al., ICSE 2015 "Trivial Compiler Equivalence") is missing. It is directly relevant to M2.
11. **Preprints.** Several key comparators are 2026 preprints (SemaDiff, FEAgent, EquiBench). Comparisons with them are conceptual only, which is acceptable, but mark them as such in the main text, not only in the table caption.
12. **Cost table.** `tab:cost` says the CEC threshold uses B = 1,000, while the matched-risk intervals use 10,000 and the B6 contrast uses 2,000. Unify or justify.

---

## 5. Scores (1–10)

| Criterion | Score | Justification |
|---|---:|---|
| Novelty | 5 | Reframing NDO as selective risk and ERS-on-evidence is a fresh synthesis, though each ingredient is established, as the authors acknowledge. |
| Technical contribution | 5 | The formalism is clean but its propositions are short. The CEC predictive contribution is not demonstrated, and the trust gate is engineering. |
| Literature coverage | 7 | Broad and well-organised across eight streams. Equivalent-mutant and label-noise literature is missing. |
| Experimental design | 3 | Construction labels with likely equivalent-mutant noise, a B1 diluted by zero-input pairs, pool-confounded chance references, design-exposed data and no held-out set. |
| Statistical validity | 6 | Cluster bootstrap, Holm, MDE and non-equivalence language are good. Comparator pools and the per-fold quota handling are flawed or unexplained, and "pre-registered" is overstated. |
| Benchmark breadth | 2 | Effectively one informative arm (synthetic). QuixBugs contributes no risk numerator, BugsInPy is unlabelled, the language is Python only, and no held-out data exists. |
| Reproducibility | 6 | Analysis-level reproducibility and traceability are excellent. Collection logs are absent, the real-execution analogue ran on a dirty tree, and the profile fix is unmerged. |
| Writing | 6 | Precise and candid but very dense: 29 pages, 23 tables, and heavy self-referential audit material. |
| Figures and tables | 5 | Thorough, but too many. Some are degenerate (strict block) or decorative (landscape panel for the excluded artifact, conceptual figures). |
| Overall readiness | 3 | The core headline number needs recounting (M1) and label validation (M2) before it can stand. The paper's own scope is a pilot. |

---

## 6. Recommendation

**Major revision.** It is borderline reject in its current form.

The conceptual contribution and the honest negative reporting are worth publishing. However, the empirical anchor of the paper, "one in six empty difference sets conceals a behavioural change", rests on (i) a practice baseline that counts unexecuted pairs as passes (M1) and (ii) unverified mutant labels concentrated in an operator class prone to equivalent mutants (M2). Both can be fixed with existing data plus a small manual adjudication of about 31 pairs, which the authors' own protocol already supports. M3 and M4 are re-analyses with existing code and could change the interpretation of "abstention is not reliability". M5–M8 require reframing rather than new data, except for the optional seeded-fault study in M7.

I would support acceptance as a methodology-plus-pilot negative-results paper once M1–M5 are resolved and the claims are scoped accordingly.
