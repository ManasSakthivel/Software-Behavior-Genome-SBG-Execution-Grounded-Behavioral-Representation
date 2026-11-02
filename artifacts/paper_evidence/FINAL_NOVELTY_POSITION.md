# Final novelty position (FINAL SPRINT, Part 2C/2E)

Companion documents: `RELATED_WORK_COMPARISON.md` (sources, depth of reading, matrix),
`CLAIM_TO_EVIDENCE_MATRIX.md`, `INCREMENTAL_CONTRIBUTION_ANALYSIS.md`.

## 1. Closest prior methods

1. **Kessel & Atkinson, SCAM 2019** (DOI **10.1109/SCAM.2019.00030**) — dynamic behaviour comparison (behaviour sampling)
   for judging functional equivalence. **Abstract only; full text closed access.**
2. **Danglot, Monperrus, Rudametkin, Baudry, EMSE 2020** (DOI 10.1007/s10664-019-09794-7; arXiv:1902.08482) — DCI:
   detect behavioural change of commits via test amplification. **Abstract and introduction read.**
3. Differential testing / behavioural regression testing / differential symbolic execution: Evans & Savoia 2007,
   Jin–Orso–Xie 2010, Person et al. 2008. **Metadata only.**
4. Behaviour sampling (Podgurski & Pierce 1992) and random-testing equivalence mining (Jiang & Su 2009). **Metadata only.**

## 2. Verified distinctions (and what is *not* distinction)

Verified from sources actually read (K abstract; D abstract + intro):

* D produces *test cases that distinguish versions* using existing unit tests on Java projects; SBG produces a *continuous
  trace distance* on Python programs with no test suite. (Verified for D; for K the abstract does not describe the
  response representation.)
* K studies how many stimuli are needed to recognise non-equivalence (≥ 39 random tests for ~85 % recognition; coverage-
  based generation needs fewer). SBG does **not** study input sufficiency; it uses a fixed battery.
* Neither K's abstract nor D's abstract/introduction reports a baseline comparison against edit size, or the
  edit-size/label coupling in a synthetic transformation benchmark.

**Not distinctions** (must not be argued as novelty): "dynamic" analysis; use of execution traces; comparison of two
versions; a larger evaluation; more rigorous statistics.

## 3. Unresolved overlaps

* **Kessel & Atkinson full text.** Which behavioural representation they compare (raw outputs? traces? coverage?),
  how labels were obtained, and whether they control for confounds is **unknown**. Until read, any sentence of the form
  "unlike Kessel & Atkinson, SBG …" beyond "SBG does not study stimulus count and uses a structured trace
  representation" is unsupported.
* The differential-testing family (metadata only).
* The wider literature on trace/program similarity, regression test selection and change-impact analysis was **not
  surveyed systematically** in this sprint.

## 4. Three-level contribution analysis

| Level | Candidate statement | Support | Assessment |
|---|---|---|---|
| **1 — Method** | "A trace-derived, rename-invariant, output-free representation (call-level + temporal + abstract state-transition) whose distance separates behaviour-changing from behaviour-preserving transformations." | Works vs edit size (V10 0.897 vs 0.616). **No established gain over execution statistics** computed from the same traces (H4 null; LOPO +0.010 n.s.). The state component is the strongest piece (V9c-val 0.762; V10 0.917). V6 not better than V5. Prior dynamic comparison exists (K, D, E, B, S). | **Weak-to-modest.** Defensible only as "a representation", not as an algorithmic advance over cheap trace statistics. |
| **2 — Evaluation** | "A size-aware, oracle-validated, preregistered evaluation design: identification of an edit-size/label confound (V8: reversed-edit AUROC 0.876), a composed pairing that removes most of it (edit AUROC 0.616), dynamic-oracle label validation, Holm-corrected paired program-cluster bootstrap, and a strong-baseline (edit + execution statistics) test." | Strongly documented in-repo (`LABEL_GENERATION_AUDIT.json`, `DIAGNOSTIC_EDIT_SIZE.json`, `EVALUATION_PLAN_V9.md`, V10 frozen results). Novelty relative to literature **only relative to sources read** (K, D, KR, Y abstracts). | **Strongest defensible contribution.** |
| **3 — Empirical finding** | "On controlled Python transformation pairs, edit size is a poor predictor of behavioural change once the confound is removed; execution statistics derived from the same traces account for most of the discriminative signal, and a richer trace representation (SBG) does not demonstrably add to them; value-only changes are invisible to output-free traces." | H2/H3 supported; H4 null on two datasets; LOPO and 2×2 analyses; SC-6 blind spot (73.9 %). | **Defensible and honest**, but modest in scope (synthetic, same-author programs). |

**Chosen position:** lead with **Level 2 (evaluation methodology)** supported by **Level 3 (the empirical finding,
including the null)**, and present Level 1 as a *modest, secondary* contribution ("we instantiate and evaluate such a
representation"). Do not present the paper as an algorithmic breakthrough.

## 5. Proposed one-paragraph novelty argument

> Dynamic comparison of program versions is an established idea, from behaviour sampling and differential testing to
> test-amplification-based detection of behavioural change in commits. We do not claim to introduce it. We study a
> specific, under-examined question: when a trace-derived behavioural distance separates behaviour-changing from
> behaviour-preserving source transformations, how much of that separation is simply explained by the size of the edit,
> and how much by cheaper execution statistics computed from the same traces? We show that a naive transformation-family
> benchmark can be solved by edit size alone (reversed-edit AUROC 0.876), give a composed pairing design with
> dynamic-oracle-validated labels that largely removes this confound, and evaluate a structured, rename-invariant,
> output-free trace representation (SBG) under preregistered, multiplicity-corrected tests. SBG separates the two classes
> far better than edit size (AUROC 0.897 vs 0.616 on 19 held-out programs generated by the same author and procedure),
> but we find no statistically established gain over execution statistics from the same traces, and a systematic blind spot
> for changes that alter values without altering control flow or local state.

## 6. Contribution bullets (paper-ready)

1. **A size-aware evaluation design** for behaviour-change detection: we identify an edit-size/label confound in
   transformation-family benchmarks (an edit-size-only predictor reaches AUROC 0.876 in reverse on V8) and give a
   composed pairing with dynamic-oracle-validated labels that reduces forward edit-size AUROC to 0.616 on held-out data.
2. **A trace-derived, rename-invariant, output-free behavioural representation (SBG)** combining call-level, temporal and
   abstract state-transition components, evaluated with preregistered, Holm-corrected, program-clustered paired tests.
3. **Evidence that the representation carries behavioural signal beyond edit size** (V10 AUROC 0.897 [0.863, 0.922];
   +0.254 AUROC over edit alone; 0.875 when edit size is exactly matched), on programs unseen during development.
4. **A strong-baseline negative result:** adding SBG to edit size and execution statistics gives no statistically
   established gain (V10 +0.006, 95 % CI [−0.069, +0.068]; V9c-val +0.021 [−0.005, +0.048]); with an in-distribution refit,
   execution statistics alone reach 0.885 vs SBG 0.897 (exploratory).
5. **A characterised failure profile:** value-only mutations (SC-6) are invisible by construction (73.9 % of SC-6 changed
   pairs score exactly 0), and the representation does not transfer to real-bug corpora (BugsInPy 0.497, QuixBugs 0.444
   after excluding the SP-2 negatives).

## 7. Claims that must not be made

* SBG (or dynamic behaviour comparison) is "the first", "novel framework", "unique approach", or "first-of-its-kind".
* SBG adds predictive value beyond edit size **plus** execution statistics; or that the H4 result "trends" toward it;
  or that the null proves equivalence/redundancy.
* SBG detects real bugs or real regressions; SBG is "validated for practical use"; developer-productivity statements.
* V10 is independently authored or demonstrates generalisation to independent software (it is a held-out split from the
  same author and generation procedure).
* V6 is better than V5 (H5 Holm p = 0.090; Δ ≈ 0.003).
* Equivalence labels are universal semantic equivalence (they are equivalence on protocol inputs).
* Anything about COBOL or other languages (tracer is Python-only; the COBOL corpus provided no evaluation).
* Novelty relative to Kessel & Atkinson beyond the verified abstract-level distinctions.

## 8. Citations still requiring full-text verification

| Citation | Status |
|---|---|
| Kessel & Atkinson 2019 (10.1109/SCAM.2019.00030) | **Full text not obtained** (closed access). **Must be read before submission** to confirm the distinction in §2 and fill the "not verified" cells of the matrix. |
| Podgurski & Pierce 1992; Jiang & Su 2009; Jin et al. 2010; Person et al. 2008; Evans & Savoia 2007 | Metadata verified; methods not read — read before making any method-level comparative claim. |
| Just et al. 2014; Ojdanić et al. 2023 | Metadata verified; findings not read — read before using them to *explain* the real-bug null. |
| TRACED (Ding et al. 2024) | Metadata verified; earlier abstract-level notes only. |
| EquiBench (Wei et al., arXiv:2502.12466) | Metadata/author list verified; **venue unverified**; earlier audit's venue and title were inaccurate. |
| Yu et al. 2022 (10.1145/3502852) | Metadata verified; content not read. |

Corrected in this sprint: the earlier repo documents cite Kessel & Atkinson as 10.1109/SCAM.2019.00019, which resolves to
Harrand et al., *The Strengths and Behavioral Quirks of Java Bytecode Decompilers*. The correct DOI is 10.1109/SCAM.2019.00030.

## 9. Assessment

**Defensible, as a modest evaluation-methodology-plus-empirical-finding paper; not defensible as an algorithmic novelty
paper.** The Level-2 contribution rests on in-repo evidence that is strong and reproducible, but its *novelty* is
established only against the sources actually read here; the remaining risk is concentrated in (i) the unread Kessel &
Atkinson full text and (ii) the unsurveyed differential-testing / change-impact literature. If either shows that
size-aware, oracle-validated comparison of dynamic behavioural representations has been done, the contribution reduces
to the empirical finding (Level 3). That residual uncertainty is stated, not resolved.
