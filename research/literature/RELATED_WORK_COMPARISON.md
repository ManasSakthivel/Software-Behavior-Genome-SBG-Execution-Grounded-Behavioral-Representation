# Related Work Comparison (capability table and method cards)

Updated 2026-11-17 (pass 2). Published findings are kept separate from SBG's own (unpublished, development-grade) experimental findings; the latter appear only in Section 4 and are labelled as such. This is a targeted review, not a systematic review and not PRISMA.

## 0. Access levels (strict) and how to read them

- **FULL TEXT (own read)**: I read the extracted text of the paper body myself (Evans & Savoia, 4 pp., Internet Archive copy of the authors' PDF; Shadow ICSE 2016; DiffKemp ICST 2021; plus the P0-pass full texts: Felsing 2014, Daikon 2001, Law & Rothermel 2003, Orso 2004, Chianti tech report). Shadow and DiffKemp were re-read in selected sections only (see `access_note` in the matrix).
- **FULL TEXT (tool-mediated)**, marked with a dagger in tables: the arXiv HTML text was processed by a summarising fetch tool; I did not see the raw text. Roughly the first 100,000 characters were covered (Testora 100k/115.8k, Mokav 100k/109.4k, Cleverest about 100k/109k, DiffTestGen 100k/100.2k, PatchGuru 100k/115.7k, ORION 100k/104k, Tian 100k/104k; DiffSpec, Prefactory and SemaDiff as processed). Numbers below are as that processing reported them; "silence" for these papers means silence in the processed text. They are the most useful 2024-26 sources but are weaker evidence for "the paper does not do X" than an own read.
- **ABSTRACT / METADATA**: as in the matrix. ACM DL returned HTTP 403 for every DOI (including an ACM CC BY PDF link for Shadow TOSEM).

Counts in `EVIDENCE_MATRIX.csv` (185 rows): FULL TEXT 20 (8 own read, 12 tool-mediated), ABSTRACT 89, METADATA 76.

## 1. Capability definitions

(A) executes both versions on common inputs/tests; (B) produces a re-runnable witness artefact; (C) measures and reports how much of the change was exercised; (D) has an explicit inconclusive/insufficient outcome (not just binary); (E) handles nondeterminism/flakiness in the comparison; (F) evaluated on real code changes; (G) the "no difference" result is conditioned on (C) (a gate).

Labels: **Supported** = stated in the source at the access level shown. **Partially supported** = a related mechanism is stated, not the full capability. **Not supported** = the text defines its outcome/feature space without it, or states it as a limit. **Not evaluated** = silent in the text read (not evidence of absence). **Unknown** = access too low to judge. "(static)" in a cell means the work does not execute programs, so the capability does not apply.

## 2. Capability table

| Work [access] | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| Evans & Savoia 2007 [FT] | Supported | Partially supported (generated test sets for regressed/progressed behaviour) | Partially supported (coverage changes observed in the study; no per-verdict record) | Partially supported (states that an empty difference set is ambiguous; defines no outcome) | Not evaluated | Partially supported (one project, JTopas, 3 versions, 38 seeded faults) | Not supported |
| Shadow ICSE 2016 [FT] | Supported | Partially supported (divergent inputs replayed natively; code-level divergences reported; no exchange format) | Partially supported (seeded from regression tests touching the patch; reports divergences and % replayed) | Not supported (outcomes are divergences and output differences) | Not supported (non-determinism in replay and classification stated as a limitation) | Supported (18 CoREBench patches) | Not supported |
| Shadow TOSEM 2018 [AB] | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |
| Rutledge & Orso ICST 2022 [MD] | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |
| Jin, Orso, Xie ICST 2010 [MD] | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |
| DiffKemp ICST 2021 [FT] / TOSEM 2026 [AB] | Not supported (static) | Partially supported (localises the C symbol behind a difference) | Not supported (static) | Partially supported (equal / non-equal / could not be determined; third class mostly missing definitions) | Not supported (static) | Supported (RHEL KABI over 7 releases; 42 refactoring commits; musl) | Not supported |
| Regression verification, Felsing 2014 [FT] | Not supported (proof) | Not evaluated | Not supported (proof) | Not evaluated | Not supported (proof) | Partially supported (benchmarks of 16-53 LOC) | Not supported |
| Dynamic impact: Law & Rothermel 2003, Orso 2004 [FT] | Not supported as a verdict tool (impact sets from traces) | Partially supported (whole-path traces) | Partially supported (authors state estimates hold relative to observed runs) | Not supported (impact sets, no abstain outcome, P0) | Not evaluated | Partially supported (small subjects) | Not supported |
| Chianti [AB; tech report FT] | Not supported (static) | Not evaluated | Not supported (potentially affected tests only) | Not evaluated | Not supported (static) | Supported (Daikon CVS data) | Not supported |
| Daikon [FT] | Partially supported (invariants per version, diffable) | Partially supported (invariants as artefacts) | Partially supported (authors: accuracy depends on test quality) | Not supported | Not evaluated | Partially supported (one 563-line C program) | Not supported |
| Verification Witnesses [AB] | Not supported (verification) | Supported (exchangeable, independently validated) | Not evaluated | Not evaluated | Not evaluated | Not evaluated | Not evaluated |
| Mokav (Etemadi 2025) [FT†] | Supported | Supported (DET as a unit test asserting different outputs) | Not evaluated | Not supported (success or "max iterations reached") | Partially supported (main experiment repeated five times for LLM variance; no program-nondeterminism handling) | Partially supported (QuixBugs, Codeforces submissions; not repository changes) | Not supported |
| Testora (Pradel 2026) [FT†] | Supported | Partially supported (test, both outputs, explanation for "unintended") | Partially supported (diff coverage measured, RQ2; not required) | Not supported (binary; filtered tests dropped silently) | Supported (re-execution of differences; classifier asks "deterministic") | Supported (4 projects, 525 checked PRs) | Not supported |
| DiffSpec (Rao 2025) [FT†] | Supported (across implementations of one spec) | Partially supported (tests) | Not supported (authors chose not to use code coverage) | Not supported (per-test PASS/FAIL/SKIP/ERROR/CRASH) | Not evaluated | Partially supported (eBPF, Wasm implementations; not versions) | Not supported |
| Cleverest (Liu 2026) [FT†] | Supported | Partially supported (test inputs) | Supported (GCOV "commit reached" measured; as generation feedback) | Partially supported (ordinal outcome distinguishes "commit reached, no output change" from "not reached") | Partially supported (10 repeated runs; authors report no observed flakiness) | Supported (72 commits, 8 programs) | Partially supported (reaching qualifies the "no change" result, but as feedback) |
| DiffTestGen (Hu 2026, preprint) [FT†] | Supported | Partially supported (tests) | Supported (union coverage of changed lines, reported per dataset) | Not supported (PR without difference is "not detected") | Supported (each test re-run on both versions; discarded if either run differs) | Supported (463 PRs) | Not supported (coverage drives generation, not the verdict) |
| PatchGuru (Le-Cong 2026, preprint) [FT†] | Supported | Partially supported (comparison program with runtime assertions + report) | Not evaluated (no changed-line coverage; mutation score instead) | Not supported (empty report does not separate "consistent" from "budget exhausted") | Not evaluated | Supported (400 PRs) | Not supported |
| ORION (Fu 2026, preprint) [FT†] | Supported | Partially supported (cases with tests and outputs) | Partially supported (coverage over oracle items, not lines) | Partially supported (infrastructure-failure-only PRs flagged for human review) | Partially supported (isolated environments; infrastructure noise filtered; no reruns) | Supported (154-PR benchmark; 1,459 PRs) | Not supported |
| Prefactory (Bouzenia 2026, preprint) [FT†] | Supported (original vs rewritten function) | Partially supported (failing inputs/outputs) | Not evaluated | Partially supported (pass / fail / inconclusive, where inconclusive = script cannot run reliably) | Not evaluated | Supported (100 developer refactorings, 61 projects) | Not supported |
| SemaDiff (Ayub 2026, preprint) [FT†] | Supported | Partially supported (tests) | Partially supported (coverage measured in evaluation) | Not supported (binary; failures counted as errors) | Not evaluated | Supported (183 labelled commits) | Not supported |
| Hilton 2018 [AB]; Bailey & Cadar 2025 [AB]; Covrig 2014 [MD] | Not evaluated | Not evaluated | Partially supported (patch coverage studied) | Not evaluated | Unknown | Supported (47 projects / 7,816 builds; nine C/C++ projects, 78 years) | Not evaluated |
| Flaky tests: iDFlakies, DeFlaker, Luo, Parry, FlakyLens [AB/MD] | Not evaluated | Not evaluated | Not evaluated | Not evaluated | Supported (flakiness is the subject) | Supported (per abstracts) | Not evaluated |
| Abstention: Geifman 2017, Hendrickx 2024, Spiess 2025, Jeong 2025 [AB] | Not supported (not about program versions) | Not supported | Not supported | Partially supported (abstain on model confidence; Jeong adds test-based checks of generated code) | Not evaluated | Supported (ML benchmarks) | Not supported |
| EquiBench 2025 [AB]; Tian et al. ISSTA 2024 [FT†] | Not supported (equivalence judged by a model) | Not supported | Not supported | Not supported (binary equivalence) | Not evaluated | Partially supported (benchmarks; Tian: 3,302 Java mutant pairs) | Not supported |

Every cell rests on the cited work's accessed text. No cell reports a capability of any tool I ran (none was run). "Not evaluated" must not be quoted as proof of absence. Rows marked † are weaker evidence than an own full-text read.

## 3. Method cards (comparison set)

"Inference" marks my reasoning, not an author claim. Published limitations are only those stated in the sources.

### 3.1 Evans & Savoia 2007, ESEC/FSE (FULL TEXT, own read)
- Problem: regression testing as practised is unsound because of inconsistent test repair/addition, so changes go undetected.
- Method: use an automated characterisation test generator on both S and S'; run each suite on both versions; partition tests into preserved, regressed (TS minus TS') and progressed (TS' minus TS).
- Inputs: two versions, an automated test generator (Agitator-based, JUnit Factory).
- Output: sets of tests per behaviour category; the authors say categories are only as strong as the generated tests are reliable (Howden).
- Evaluation: JTopas (SIR), three versions of 852/842/2,287 executable lines, 38 seeded faults; 21%, 34%, 21% more behaviour changes than regression testing alone. Authors' threats: the three "subjects" are related versions of one parser; seeded faults only; single generator.
- Strengths: clear two-suite cross-version formulation; explicit about the empty-difference ambiguity.
- Limitations (authors): preliminary; inadequate tests are an obvious risk: if TDifferent is empty "the result is ambiguous: it could mean the two systems are identical, or that TS and TS' are inadequate"; assertion masking hides later assertions in a JUnit test.
- Relation to SBG: the earliest source I read that states the exact ambiguity SBG's outcome targets. It is a stated threat, not an outcome, record or gate.
- SBG distinct (inference): making that ambiguity a typed, recorded, replayable outcome with grounds.

### 3.2 Shadow symbolic execution: Palikareva, Kuchta, Cadar ICSE 2016 (FULL TEXT, own read of key sections); Kuchta, Palikareva, Cadar TOSEM 2018 (ABSTRACT); Cadar & Palikareva ICSE-NIER 2014 (METADATA)
- Problem: tests written to cover a patch often exercise the same behaviour in old and new code (abstract); generate inputs that exercise the new behaviour.
- Method: old and new versions merged with hand-written `change()` annotations and run in lockstep in KLEE; at divergent branches generate a test and run a bounded symbolic phase; divergent inputs replayed natively on both versions with cross-version checks.
- Inputs: C source of both versions with annotations; a regression suite touching the patch.
- Output: code-level divergences (and % replayed), observed output differences classified expected vs regression bug (using fix revisions plus a manual sanity check).
- Evaluation: CoREBench Coreutils, 18 patches (P0: 2 excluded for infrastructure reasons); median 1,020 s / 1,962 s / 7,213 s per phase; exposes some regressions and two unrecorded bugs.
- Strengths: reaches changed behaviour by constraint solving; reports code-level divergence even without an output difference; native replay.
- Limitations (authors): manual annotations; missed bugs needing file-permission, floating-point or symbolic-directory modelling; short timeouts; depends on starting inputs; output differences only; refactorings: any difference is a bug; too many divergent inputs; replay below 100% for some patches; non-determinism in replay and in the automatic classification.
- Relation to SBG: the strongest published cross-version tester; shares "run both versions and replay a witness". Its stated finding that patch-covering tests may not exercise new behaviour is a published caution against coverage-only sufficiency.
- SBG distinct (inference): no input generation (so no claim to match Shadow's reach); a recorded sufficiency and an explicit insufficient outcome, which the text read does not define.

### 3.3 DiffKemp: Malik & Vojnar ICST 2021 (FULL TEXT, own read of method and Table II); Malik, Vojnar, Necas TOSEM 2026 (ABSTRACT)
- Problem: automatically check semantic equivalence between versions of very large C projects (Linux kernel KABI stability).
- Method: LLVM IR; light-weight transformations and pattern matching plus synchronisation-point comparison; static only. TOSEM abstract adds global-variable semantics via specialised slicing.
- Inputs: both versions compiled to LLVM IR; selected functions/symbols.
- Output: equal / non-equal / could not be determined (typically missing definitions); locates the C symbol causing a difference. The authors treat non-equal as possibly a false non-equality, i.e. "not proven equal".
- Evaluation: RHEL KABI over 7 releases (Table II: e.g. 739 KABI functions: 608 equal, 125 non-equal, 6 undetermined; 471: 360/86/25; 7-14 minutes per pair), 42 refactoring commits, musl (P0); manual inspection of non-equal found at most a few unchanged-semantics functions.
- Strengths: scales; conservative verdict direction; localisation.
- Limitations: static and C only; cannot establish equivalence of heavily refactored code (P0 reading); the undetermined class reflects analysability, not observation.
- Relation to SBG: strongest prior art for a non-binary conservative verdict; complementary (static proof direction vs dynamic observation).
- SBG distinct (inference): outcome grounded in what executions exercised and recorded, replayable by a third party.

### 3.4 Mokav: Etemadi, Mohammadi, Su, Monperrus; JSS 2025 (FULL TEXT, tool-mediated)
- Problem: find a difference-exposing test (DET) for two programs P and Q.
- Method: iterative LLM loop with execution feedback; first DET stops the run.
- Inputs: P, Q and an example test on which they agree (Python, <= 2,500 tokens per version; primitive/list inputs).
- Output: a unit test asserting different outputs, or a "maximum iterations" failure message.
- Evaluation: 32 QuixBugs pairs and 1,535 Codeforces-derived pairs (C4DET); Pynguin and DPP baselines; final success 100% (32/32) and 81.7% (1,255/1,535) vs Pynguin 4.9% and DPP 37.3% on C4DET.
- Strengths: large gain on its datasets; self-contained DET.
- Limitations (authors): possible leakage; temperature-1 randomness; Python only; length cap; weak at precise mathematics; safety of running generated tests.
- Relation to SBG: competitor on witness discovery; potential baseline.
- SBG distinct (inference): Mokav has no record of what a failed search exercised.

### 3.5 Testora: Pradel, ICSE 2026 (FULL TEXT, tool-mediated)
- Problem: all behavioural differences are reported by regression test generation although most changes are intended.
- Method: LLM test generation from a PR, differential execution in Docker, re-execution to validate, five-question LLM classification against PR intent.
- Inputs: PR text, diff and messages; Python projects.
- Output: "unintended" with test, outputs and explanation, or "intended"; no inconclusive class in the processed text.
- Evaluation: keras, marshmallow, pandas, scipy; 525 checked PRs, 100 with differences, 19 regressions and 11 coincidental fixes; classifier on 164 labelled entries: precision 55%, recall 67%, F1 60% (default); no tool baseline.
- Strengths: developer-confirmed real regressions (11 of 13 reported confirmed); cheap; explicit nondeterminism checks.
- Limitations (authors): unit-testable APIs; complex diffs; four Python projects; LLM variance; single-researcher labels.
- Relation to SBG: closest LLM tool for real changes; corrects the earlier "nondeterminism not evaluated".
- SBG distinct (inference): Testora asks "intended or not", SBG asks "was the change exercised enough to say anything about no-difference".

### 3.6 DiffSpec: Rao et al. (arXiv, FULL TEXT, tool-mediated)
- Problem/method: spec-driven differential testing of implementations (eBPF runtimes, Wasm validators) with LLM prompt chaining.
- Inputs: NL spec, implementation code, human tests, bug reports.
- Output: per-test outcome classes; "differentiating" need not be a bug.
- Evaluation: eBPF 1,901 differentiating tests (69.4% valid), 4 confirmed bugs in a 200-test sample; Wasm 299 differentiating tests, 2 confirmed bugs; fuzzers as baselines.
- Limitations (authors): not every difference is a bug; LLM expected values may be wrong; no code coverage; single runs.
- Relation: different setting (implementations, not versions). SBG distinct (inference): none claimed here.

### 3.7 Cleverest: Liu, Lee, Losiouk, Boehme, PACMSE FSE 2026 (FULL TEXT, tool-mediated)
- Problem: just-in-time regression tests for programs with structured inputs and no oracle.
- Method: zero-shot feedback-directed LLM loop; execution analyser with ASan, output comparison and GCOV "commit reached"; ordinal feedback (bug triggered, output changed, commit reached, none).
- Inputs: commit message/diff, format name, command line; before/after binaries.
- Output: test inputs and the ordinal result per commit.
- Evaluation: 72 commits (36+36), 8 programs, 10 runs; WAFLGo baseline (24 h); reproduced 11/24 vs 8/24, found 7/26 vs 10/26; ClevFuzz 20/26 and 18/24. (v1 on arXiv covered 22 commits per a search result.)
- Limitations (processed text): ASan-based oracle; depends on input format/LLM/message; weak on PDF and Z3.
- Relation: the ordinal score already separates "reached, no change" from "not reached": a published precedent for part of C2/C3 semantics, used for generation feedback rather than as a verdict.
- SBG distinct (inference): carrying the distinction into a verdict and a record.

### 3.8 DiffTestGen: Hu, Cadar, Pradel (arXiv 17 Jul 2026; FULL TEXT, tool-mediated)
- Problem/method: change-directed LLM tests via call-graph entry-point discovery and a union-coverage feedback loop (covered changed lines in old plus new over all changed lines).
- Output: tests exposing differences (different error type, one side errors, different outputs after normalisation); no-difference PRs are simply not counted.
- Evaluation: 463 PRs; on Testora's 439 PRs 79.7% with 92.7% union coverage vs Testora 77.1%; ChaCo 28 vs 21. The abstract's 78.2%/90.7% is not reconciled in the processed text.
- Flaky handling: each test re-run on both versions; discarded if either result differs from the first run.
- Limitations (authors): LLM non-determinism; invisible differences; LLM classifier; Python only; four projects.
- Relation: the closest published two-version measure of change coverage. Preprint, no venue stated.
- SBG distinct (inference): sufficiency as verdict gate and record, not generation feedback.

### 3.9 PatchGuru: Le-Cong et al. (arXiv Feb/Jul 2026; FULL TEXT, tool-mediated)
- Method: infer executable "patch oracles" (assertions in comparison programs over pre/post versions), enhance, self-review.
- Output: warning only after self-review; otherwise an empty report which the text read does not split into "consistent" and "budget exhausted".
- Evaluation: 400 PRs; 39 warnings, 24 true positives, precision 0.62 vs Testora 0.32 (authors' numbers); mutation score 0.70 vs 0.58 for developer tests.
- Limitations (authors): Python; single-function PRs; one LLM; manual analysis; 15 false positives.
- SBG distinct (inference): an explicit distinction for the silent case.

### 3.10 ORION: Fu et al. (arXiv Oct 2026; FULL TEXT, tool-mediated)
- Method: intent and impact regions, per-function oracles, oracle-guided test generation, pre/post execution with rules then an LLM check.
- Output: regression-inducing or clean; infrastructure-failure-only PRs flagged for human review.
- Evaluation: 154 PRs (77/77), baselines Testora, PatchGuru, direct LLM, Codex, Claude Code; F1 0.6125 vs Testora 0.3243 (authors' numbers); 1,459 PRs, 8 maintainer-confirmed bugs.
- Limitations (authors): setup failures; LLM oracle dependence; non-determinism; small benchmark; training-data exposure.
- SBG distinct (inference): typed, replayable insufficiency rather than a human-review flag.

### 3.11 Prefactory: Bouzenia & Pradel (arXiv Jul 2026; FULL TEXT, tool-mediated)
- Differential test outcomes: pass (no generated input reveals a difference), fail, inconclusive (script cannot run reliably); a pass is "evidence on the generated inputs, not proof of equivalence".
- Evaluation: 100 refactorings from 61 projects, 49 passing differential tests, 40 validated; Codex CLI 22 validated.
- Relation: the most direct published three-way outcome in execution-based version comparison. Its inconclusive covers harness failure, not unexercised change.
- SBG distinct (inference): grounds beyond harness failure.

### 3.12 SemaDiff: Ayub et al. (arXiv Jul 2026; FULL TEXT, tool-mediated)
- Method/output: LLM-generated dependent code and tests run on both versions; "preserving" only if all agree; binary.
- Evaluation: 183 labelled Java commits (text and Table I disagree on the 95/88 split); precision 100%, recall 58.89%, accuracy 75.95%; direct LLM prompting without tests has higher accuracy.
- Limitation (authors): recall about 59%; exposing a change is harder than confirming none.
- Relation: its "preserving" output is an assurance based on generated tests only.

### 3.13 Supporting methods (shorter)
- Regression verification (Godlin & Strichman 2009/2013 [AB]; Felsing et al. 2014 [FT]): proves equivalence for small programs (benchmarks of 16-53 LOC, integer-only); SBG must not imitate the "equivalent" wording.
- Dynamic impact analysis (Law & Rothermel 2003; Orso et al. 2004 [FT]): impact estimates are relative to observed executions and "not safe"; impact sets, no verdict.
- Chianti [tech report FT]: static call-graph affected tests; Daikon [FT]: likely invariants whose accuracy depends on test quality.
- Verification witnesses (Beyer et al. [AB]): exchangeable, independently validated witnesses, in verification.
- Flaky tests (iDFlakies, DeFlaker, Luo 2014, Parry 2021, FlakyLens 2025): flakiness detection and classification per test [AB/MD].
- Abstention (Chow 1970; Geifman & El-Yaniv 2017; Hendrickx 2024; Jeong 2025; Sharma & David 2025) [AB/MD]: on model confidence or test-based checks of generated code.
- Equivalence classification (EquiBench [AB]; Tian et al. ISSTA 2024 [FT†]): Tian et al. note that equivalence is undecidable; best F1 86.58% (fine-tuned UniXCoder) on 3,302 Java mutant pairs.
- Observability and adequacy: Voas PIE 1992 [snippet-level], Schuler & Zeller checked coverage 2011/2013 [snippet-level], Inozemtseva & Holmes 2014 [MD], Just et al. 2014 [AB]: coverage is an imperfect proxy for effect or checking.
- Studies of generated tests: Haroon et al. 2026 [FT†] (tests regenerated under semantic-altering changes often track original behaviour), Charoosaei et al. 2026 [FT†] (8.4-16.9% of generated tests "fault-enforcing": they encode faulty behaviour).

## 4. SBG's own status (not literature; development-grade, unpublished)

Taken from repository reports (`reports/final/INDEPENDENT_RED_TEAM_REVIEW.md`); these are SBG experimental findings, not published results, and none is confirmatory.

| Capability | SBG V7-B status (internal) |
|---|---|
| A, B | Implemented for Python top-level functions; hash-chained replayable records; closed verdict enum without an equivalence value |
| C, G | Sufficiency = changed-line coverage plus 80% branch-direction coverage (UNVALIDATED thresholds); red team: obtainable from two inputs |
| D | INSUFFICIENT outcome exists; red team: the observed rate is dominated by engine gaps (renames 49, generators, class units) |
| E | Replay r=5 and control alternation; red team: over 311 pairs the replay machinery differs from a "repeat three times" baseline on 2 pairs |
| F | K1 NOT MET (no independent real-project benchmark); real-fix BugsInPy units: 16 of 46 driven pairs got a no-divergence verdict on a synthetic battery |
| Blocking defect at review time | NO_RUN did not block a no-divergence verdict (B-1); status of the fix not verified here |

No claim of empirical superiority over any work in Section 2 is made or supported by anything in this review.
