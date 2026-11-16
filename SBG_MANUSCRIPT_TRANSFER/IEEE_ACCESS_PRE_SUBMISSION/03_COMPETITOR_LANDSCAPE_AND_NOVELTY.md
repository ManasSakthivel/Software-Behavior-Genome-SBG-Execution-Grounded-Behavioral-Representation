# 03 — COMPETITOR LANDSCAPE AND NOVELTY ASSESSMENT (Agent A1, literature / novelty / prior-work)

*Status: COMPLETED 2026-11-14 (system date, IST). Registry: `PKG/logs/registry/A1_lit.jsonl` (EXP-A1-001 … EXP-A1-007). Repo commit audited: `3425693b432bb774b10db1cf3185eae1a7eef095` (REPO read-only; nothing written to it).
Raw evidence: `PKG/results/raw/literature/` (fetch log with UTC timestamps: `fetchlog.jsonl`; bibliography records: `bibliography_verified.json`, `crossref_verified.jsonl`, `crossref/`, `openalex/`, `arxiv/`, `dblp/`, `pdf/`, `text/`; early brief for A4: `EARLY_COMPETITOR_BRIEF.md`).*
*Everything below is derived from primary-source records fetched in this session. Where I could only read an abstract, the access level says so. Nothing from the in-repo literature files was trusted without re-verification.*

---

## 0. VERDICT SUMMARY (read this first)

| # | Finding | Confidence / basis |
|---|---|---|
| V1 | **No "first" claim for SBG is defensible.** Pairwise dynamic comparison of two program versions to judge changed/equivalent behaviour is an old, crowded line (behaviour sampling 1992; value spectra 2005; BERT 2010; Kessel & Atkinson 2019; DCI 2020) and has **direct 2025-26 same-task competitors in Python**: **ChangeGuard** (FSE 2025, Python function pairs, execution-based, 224 annotated commits, P 77.1 %/R 69.5 %), Testora (ICSE 2026), SemaDiff, PatchGuru (2026). | HIGH (ChangeGuard, DCI, Testora, Mokav full text read) |
| V2 | **Kessel & Atkinson (SCAM 2019): access level = ABSTRACT-ONLY.** Full text is not available from any legitimate open source (IEEE paywalled; Unpaywall `is_oa=false`; MADOC record 53324 has no PDF; S2/OpenAlex "closed"). I read the author's open 2023 PhD thesis and three open MADOC papers for framework-level context only. **Every repo statement of the form "K&A do not report AUROC / use manual labels / are compared against formal verification" is unsupported by anything I could read.** | HIGH (access attempts logged §H) |
| V3 | **SBG's representation components are ESTABLISHED or INCREMENTAL, not strong novelty:** call-frequency/call-order k-grams (birthmarks 2004-2009), exception sets (differential testing), abstract-value state transitions (≈ value spectra / ADABU / Daikon-style state abstraction), fixed-weight sums of L1/Jaccard terms. The "output-free" idea is itself established (path/value spectra, birthmarks, DyCLINK). The one component with an unresolved overlap I could not close is Xie & Notkin's value spectra (abstract-only access). | MEDIUM-HIGH |
| V4 | **The defensible contributions remain evaluation-methodological** (edit-size/label confound diagnosis + composed size-matched benchmark + oracle-validated labels + cluster-level statistics + incremental-value test vs. execution statistics). Each is INCREMENTAL, not STRONG: benchmark-artefact/trivial-baseline critiques exist in adjacent areas (Yu 2022 linear identifier model for BigCloneBench; Krinke 2025; Allamanis 2019; Fu & Menzies 2017), and "label = output differs on sampled inputs" is the standard mutation-kill criterion. No paper I found diagnoses an *edit-size/label* confound for behaviour-change benchmarks — but my search is bounded (§F) and a "first" claim is still unverifiable. | MEDIUM |
| V5 | **Label-tautology warning for head-to-head work.** SBG's CHANGED label is defined by output differences on the protocol's 11 inputs. Any output-reading baseline (K&A, ChangeGuard comparator, BERT/differential testing, DCI-style) evaluated on the *same* 11 inputs reproduces the label by construction (AUROC≈1 is a definition, not a result). A fair output-reading baseline needs independent inputs. | HIGH (follows from PROTOCOL §2) |
| V6 | **"Output-free" is a protocol claim, not an information-theoretic one.** `sbg/extraction/dynamic/tracer.py` L366-372 snapshots `repr()` of *all frame locals* (capped at 100 chars) at every traced event incl. `return`; the state genome (`state_transition_genome.py`) abstracts these. Locals frequently hold the computed result. Leakage of output information through locals is therefore **plausible and untested by me** → flagged REQUIRES ADDITIONAL INVESTIGATION (for the leakage/ablation agents). | MEDIUM (code read, not experimentally tested) |
| V7 | **Repo literature material is materially unreliable** (§E): ≥8 wrong/unfindable/mismatched citations in `PRIOR_ART_MATRIX.md`, a non-existent "Sumner et al. ICST 2011" entry, mischaracterised Piech 2015, wrong K&A DOI still present in two bodies, wrong EquiBench/QuixBugs metadata, and "first/novel" statements in `docs/research/NOVELTY_ANALYSIS.md` and `RESEARCH_QUESTION.md` that are contradicted by verified prior work. The current `artifacts/paper_evidence/*` position documents are appropriately conservative. | HIGH |
| V8 | **Corrections to the task brief** (verified): ARDiff is **ESEC/FSE 2020** (DOI 10.1145/3368089.3409757), not ICSE 2020; "Sumner et al., *Comparative analysis of software behavioral traces*, ICST 2011" **does not exist** in Crossref/DBLP (the real 2011 paper is *Selecting peers for execution comparison*, ISSTA 2011); "Ding et al., *Learning Executable Semantics for Software Engineering*" **NOT-FOUND** (nearest: TRACED, ICSE 2024); ChangeGuard **exists** (Gröninger, Souza, Pradel, FSE 2025). | HIGH |
| V9 | **Name collision:** no software-engineering work titled/phrased "software behavior genome" appeared in 3 OpenAlex phrasing variants (2005-2026). Negative result under a bounded search. | LOW-MEDIUM |

### Claim-by-claim novelty ratings (details in §D)

| SBG claim | Rating |
|---|---|
| Call topology (anonymised call-frequency / coverage features) | ESTABLISHED TECHNIQUE |
| Call-order bigrams (and trigrams) | ESTABLISHED TECHNIQUE |
| Exception structure (type set, rate, causality hash) | ESTABLISHED TECHNIQUE |
| Temporal features (n-gram/entropy/phase/loop/causal pairs) | INCREMENTAL NOVELTY |
| Abstracted state-transition genome | UNRESOLVED OVERLAP (value spectra, ADABU, Daikon, Collector-Sahab, NumericalDiff) |
| Output-free design | ESTABLISHED TECHNIQUE (idea) / REQUIRES ADDITIONAL INVESTIGATION (strictness, V6) |
| Rename-invariance by first-call-order anonymisation | ESTABLISHED TECHNIQUE |
| Fixed-weight distance (0.50/0.25/0.25) | ESTABLISHED TECHNIQUE |
| Edit-size-confound evaluation methodology | INCREMENTAL NOVELTY |
| Composed size-matched benchmark | INCREMENTAL NOVELTY |
| Oracle-validated labels (kill-by-sampled-inputs) | ESTABLISHED TECHNIQUE |
| Program-level cluster statistics (cluster bootstrap, LOPO, Holm) | ESTABLISHED TECHNIQUE (general statistics; not literature-searched for SE specifics) |
| Incremental-value-over-execution-statistics analysis | INCREMENTAL NOVELTY |
| Pairwise CHANGED/EQUIVALENT *task* | UNRESOLVED OVERLAP (ChangeGuard, Testora, SemaDiff, K&A) |
| "Longitudinal behavioural genome / versioned record" (docs/research S2) | CONTRADICTED by Kessel FSE 2026 (vision paper, same idea) — not in current paper claims |

### A/B/C/D head-to-head classification (for A4; reasons in §C)

| Approach | Class |
|---|---|
| Static/lexical/bytecode baselines (edit size, TCE-style bytecode equality, identifier linear model à la Yu 2022) | **A** |
| Execution statistics (coverage/trace-length) baseline; k-gram call-sequence Jaccard (Myles/Wang/Schuler birthmark algorithms) | **A** (algorithm) / B (task) |
| Output-sampling comparator (K&A / behaviour sampling / BERT / Evans-Savoia / ChangeGuard-comparator) | **B** (independent inputs required; same-input version = tautological ceiling) |
| Value/path spectra comparison (Xie & Notkin; Harrold; Reps) | **B** |
| Trace-alignment distance (Sumner & Zhang-style; NumericalDiff-style LCS) | **B** |
| DCI (Danglot) | **C** faithful; B-analogue = amplified-test differential outcome |
| DyCLINK / code relatives | **C** |
| ChangeGuard faithful (LExecutor neural value injection) | **D/C** (needs neural model); comparator-only version = B |
| Neural execution models (TRACED, Wang-Singh-Su, blended, CodeExecutor, NExT) | **D** (qualitative **C**) |
| LLM test-gen/judging (Testora, Mokav, ProbeGen, SemaDiff, PatchGuru), EquiBench | **D** |
| Symbolic/verification (ARDiff, SymDiff, regression verification, DiSE, shadow SE, Churchill) | **D** (qualitative **C**) |

---

## 1. EVIDENCE TABLE (experiments run by A1)

| EXP-ID | What | Output files (under `PKG/results/raw/literature/`) | Status |
|---|---|---|---|
| EXP-A1-001 | Umbrella: literature/novelty investigation | all | COMPLETED |
| EXP-A1-002 | Bibliographic verification vs Crossref / arXiv API / DBLP (browser session) / OpenAlex / S2 (≥96 records) | `bibliography_verified.json`, `bibliography_table.md`, `crossref_verified.jsonl`, `crossref/*.json`, `arxiv/*.xml`, `dblp/dblp_browser_session_2026-11-14.json`, `openalex_abstracts.jsonl`, `s2_meta.jsonl` | COMPLETED |
| EXP-A1-003 | Full-text acquisition attempts for Kessel & Atkinson 2019 (+ thesis, follow-ups) | `pdf/kessel_*`, `text/kessel_*`, `openalex/unpaywall_kessel_atkinson.json`, `openalex/kessel_atkinson_refs_resolved.json`, `crossref/kessel_atkinson_links.json` | COMPLETED — K&A full text NOT obtainable |
| EXP-A1-004 | Forward-citation queries (OpenAlex `cites:`) for K&A, DCI, Xie&Notkin, BERT, Evans&Savoia, Sumner&Zhang, Jiang&Su, TRACED, ChangeGuard, EquiBench | `openalex/fwd_*.json` | COMPLETED |
| EXP-A1-005 | Keyword searches (11 queries) | `openalex/search_kw1..kw11.json` | COMPLETED |
| EXP-A1-006 | Repo audit: originality claims + citation correctness (grep + Crossref re-verification) | `crossref/*repo*`, this file §E | COMPLETED |
| EXP-A1-007 | Competitor full-text reading → `EARLY_COMPETITOR_BRIEF.md` (for A4) | `EARLY_COMPETITOR_BRIEF.md`, `text/*.txt` | COMPLETED (brief delivered early) |

---

## A. VERIFIED BIBLIOGRAPHY (access-level annotated)

**Rules.** An entry appears only if its title/authors/venue/year/identifier were read from a primary record (Crossref, arXiv API, DBLP, or MADOC record) in this session. *Access* = what **I** read: `FULL-TEXT-READ` (whole paper read; for arXiv items the arXiv version), `FULL-TEXT-READ (partial)` (open full text obtained and the relevant sections read, not the whole), `ABSTRACT-ONLY` (abstract read from OpenAlex/arXiv/S2; for some, an open PDF exists but I did not read it), `METADATA-ONLY` (bibliographic record only). `NOT-FOUND` items are in §A.2. Source column = the primary record used for the bibliographic fields (OpenAlex/S2 supplied abstracts and citation counts only).

Counts (from `bibliography_verified.json`): ABSTRACT-ONLY: 66; METADATA-ONLY: 12; FULL-TEXT-READ: 8; FULL-TEXT-READ (partial): 10; total 96.

### A.1 Verified works (B01 … )

| ID | Authors (year) | Title | Venue | Identifier | Primary source | Access | Notes |
|---|---|---|---|---|---|---|---|
| B01 | Kessel et al. (2019) | On the Efficacy of Dynamic Behavior Comparison for Judging Functional Equivalence | 2019 19th International Working Conference on Source Co | `10.1109/scam.2019.00030` | Crossref | **ABSTRACT-ONLY** | Abstract via OpenAlex/S2/MADOC record; IEEE paywalled; MADOC record 53324 has NO PDF; S2/OpenAlex closed-access. 36 reference list resolved via OpenAlex. K&A protocol details NOT read. |
| B02 | Podgurski et al. (1992) | Behavior sampling | Proceedings of the 14th international conference on Sof | `10.1145/143062.143152` | Crossref | **ABSTRACT-ONLY** | Behaviour sampling origin (ICSE 1992). OpenAlex abstract. |
| B03 | Podgurski et al. (1993) | Retrieving reusable software by sampling behavior | ACM Transactions on Software Engineering and Methodolog | `10.1145/152388.152392` | Crossref | **ABSTRACT-ONLY** | TOSEM 1993. OpenAlex abstract. |
| B04 | Xie et al. (2005) | Checking inside the black box: regression testing by comparing value spectra | IEEE Transactions on Software Engineering | `10.1109/tse.2005.107` | Crossref | **ABSTRACT-ONLY** | Value spectra; OpenAlex abstract. Paywalled. |
| B05 | Jin et al. (2010) | Automated Behavioral Regression Testing | 2010 Third International Conference on Software Testing | `10.1109/icst.2010.64` | Crossref | **ABSTRACT-ONLY** | BERT; abstract only; method described secondhand in DCI §7.2 (text read). |
| B06 | Evans et al. (2007) | Differential testing | The 6th Joint Meeting on European software engineering  | `10.1145/1295014.1295038` | Crossref | **ABSTRACT-ONLY** | ESEC/FSE 2007 Companion; DBLP title "Differential testing: a new approach to change detection". Abstract only. |
| B07 | Sumner et al. (2013) | Comparative causality: Explaining the differences between executions | 2013 35th International Conference on Software Engineer | `10.1109/icse.2013.6606573` | Crossref | **ABSTRACT-ONLY** | Execution comparison/ causality; abstract only. |
| B08 | Sumner et al. (2011) | Selecting peers for execution comparison | Proceedings of the 2011 International Symposium on Soft | `10.1145/2001420.2001458` | Crossref | **METADATA-ONLY** | The ONLY Sumner 2011 execution-comparison paper found (ISSTA 2011); verified Crossref + DBLP (conf/issta/SumnerBZ11). Repo's "Sumner ICST 2011 Comparative analysis of software behavioral traces" NOT FOUND (DBLP+Crossref). No abstract retrieved. |
| B09 | Person et al. (2008) | Differential symbolic execution | Proceedings of the 16th ACM SIGSOFT International Sympo | `10.1145/1453101.1453131` | Crossref | **ABSTRACT-ONLY** | Differential symbolic execution FSE 2008; abstract only. |
| B10 | Reps et al. (1997) | The use of program profiling for software maintenance with applications to the year 2000 problem | ACM SIGSOFT Software Engineering Notes | `10.1145/267896.267925` | Crossref | **ABSTRACT-ONLY** | Path-profile spectra / Y2K (ESEC/FSE 1997 per SIGSOFT SEN record); abstract only. |
| B11 | Harrold et al. (2000) | An empirical investigation of the relationship between spectra differences and regression faults | Software Testing, Verification and Reliability | `10.1002/1099-1689(200009)10:3<171::aid-stvr209>3.0.co;2-j` | Crossref | **ABSTRACT-ONLY** | Spectra differences vs regression faults (STVR 2000); abstract only. |
| B12 | Harrold et al. (1998) | An empirical investigation of program spectra | ACM SIGPLAN Notices | `10.1145/277633.277647` | Crossref | **METADATA-ONLY** | "An empirical investigation of program spectra" (PASTE 1998); no abstract retrieved. |
| B13 | Ernst et al. (2001) | Dynamically discovering likely program invariants to support program evolution | IEEE Transactions on Software Engineering | `10.1109/32.908957` | Crossref | **ABSTRACT-ONLY** | Daikon invariants for evolution (TSE 2001); abstract only. (ICSE-1999 conference version 10.1145/302405.302467 also Crossref-verified.) |
| B14 | Dallmeier et al. (2006) | Mining object behavior with ADABU | Proceedings of the 2006 international workshop on Dynam | `10.1145/1138912.1138918` | Crossref | **ABSTRACT-ONLY** | ADABU object-behaviour models (WODA 2006); abstract only. |
| B15 | McKeeman (1998) | Differential Testing for Software | Digital Technical Journal | `(no DOI; DBLP journals/dtj/McKeeman98)` | DBLP (browser session) | **METADATA-ONLY** | Primary source: DBLP record only; paper not located/read. |
| B16 | Orso et al. (2002) | Gamma system | Proceedings of the 2002 ACM SIGSOFT international sympo | `10.1145/566172.566182` | Crossref | **ABSTRACT-ONLY** | Gamma system (ISSTA 2002, field-data deployment); abstract only. Peripheral. |
| B17 | Danglot et al. (2019) | An Approach and Benchmark to Detect Behavioral Changes of Commits in Continuous Integration | Empirical Software Engineering 25 (2020) | `10.1007/s10664-019-09794-7` | arXiv API | **FULL-TEXT-READ** | arXiv v3 full text read (§§1-7). Crossref DOI verified separately. |
| B18 | Etemadi et al. (2023) | Augmenting Diffs With Runtime Information | IEEE Transactions on Software Engineering | `10.1109/tse.2023.3324258` | Crossref | **ABSTRACT-ONLY** | Collector-Sahab: runtime-state diff augmentation of code diffs (Java, Defects4J). OpenAlex abstract; arXiv 2212.11077 exists but not read. |
| B19 | Du et al. (2026) | Revealing Regressions: A Comparative Study of State-Capture Strategies in Validating Program Behavior | Proceedings of the ACM on Software Engineering | `10.1145/3797107` | Crossref | **ABSTRACT-ONLY** | State-capture strategies for regression oracles; abstract only. |
| B20 | Badihi et al. (2023) | Responsibility in Context: On Applicability of Slicing in Semantic Regression Analysis | 2023 IEEE/ACM 45th International Conference on Software | `10.1109/icse48619.2023.00057` | Crossref | **ABSTRACT-ONLY** | Slicing for semantic regression analysis; abstract only. |
| B21 | Morita et al. (2024) | TraceJIT: Evaluating the Impact of Behavioral Code Change on Just-In-Time Defect Prediction | 2024 IEEE International Conference on Software Analysis | `10.1109/saner60148.2024.00065` | Crossref | **ABSTRACT-ONLY** | Behavioural code change impact on JIT defect prediction; abstract only. |
| B22 | Silva et al. (2024) | Detecting semantic conflicts with unit tests | Journal of Systems and Software | `10.1016/j.jss.2024.112070` | Crossref | **ABSTRACT-ONLY** | Semantic conflict detection via unit tests; abstract only. |
| B23 | Cheng et al. (2026) | BCaLLM: Call Graph-Guided Python Breaking Change Detection with Large Language Models | Proceedings of the ACM on Software Engineering | `10.1145/3832195` | Crossref | **ABSTRACT-ONLY** | Python breaking-change detection via call graph + LLM (PyBCEval); abstract only. |
| B24 | Gröninger et al. (2025) | ChangeGuard: Validating Code Changes via Pairwise Learning-Guided Execution | Proceedings of the ACM on Software Engineering | `10.1145/3715760` | Crossref | **FULL-TEXT-READ** | Closest contemporary task-level competitor; full text read (arXiv 2410.16092v2) and repo metadata (github.com/sola-st/ChangeGuard). |
| B25 | Pradel (2026) | Testora: Using Natural Language Intent to Detect Behavioral Regressions | Proceedings of the 2026 IEEE/ACM 48th International Con | `10.1145/3744916.3764527` | Crossref | **FULL-TEXT-READ** | arXiv 2503.18597v3 read; code github.com/michaelpradel/testora (MIT). |
| B26 | Etemadi et al. (2025) | Mokav: Execution-driven differential testing with LLMs | Journal of Systems and Software | `10.1016/j.jss.2025.112571` | Crossref | **FULL-TEXT-READ** | arXiv 2406.10375v2 read. |
| B27 | Allamanis et al. (2025) | Disproving Program Equivalence with LLMs | arXiv preprint | `arXiv:2502.18473` | arXiv API | **FULL-TEXT-READ** | arXiv 2502.18473 read ("ProbeGen"-style differential testing with LLM probes). |
| B28 | Ayub et al. (2026) | SemaDiff: Identifying Semantic-Changing Commits with Generated Code and Tests | arXiv preprint | `arXiv:2607.13111` | arXiv API | **FULL-TEXT-READ (partial)** | arXiv 2607.13111 (2026; unreviewed preprint): abstract/intro/eval read. |
| B29 | Le-Cong et al. (2026) | PatchGuru: Patch Oracle Inference from Natural Language Artifacts | arXiv preprint | `arXiv:2602.05270` | arXiv API | **ABSTRACT-ONLY** | arXiv 2602.05270 (2026): abstract read; PDF downloaded, not read in full. |
| B30 | Anand (2026) | Impact Is Not Invalidation: Ask About the Claim, Not the Diff | arXiv preprint | `arXiv:2609.25130` | arXiv API | **ABSTRACT-ONLY** | arXiv 2609.25130 (single-author, unreviewed): abstract read. |
| B31 | Kachroo et al. (2026) | Functionally Equivalent or Not? Graph-Grounded Differential Surrogate Execution for Code Equivalence | arXiv preprint (stated accepted: NeurIPS 2026 workshop) | `arXiv:2610.04371` | arXiv API | **ABSTRACT-ONLY** | arXiv 2610.04371 FEAgent: LLM-"surrogate" differential execution; abstract read. |
| B32 | Chen et al. (2026) | NumericalDiff: Numerical Program Differencing via Value-Based Trace Alignment and Intervention | arXiv preprint | `arXiv:2611.11213` | arXiv API | **ABSTRACT-ONLY** | arXiv 2611.11213 (2026-11-08): value-based trace alignment for numerical programs; abstract read. Unreviewed. |
| B33 | Le et al. (2026) | TestWeaver: Execution-aware, Feedback-driven Regression Testing Generation with Large Language Models | Proceedings of the 2026 IEEE/ACM 48th International Con | `10.1145/3744916.3787805` | Crossref | **ABSTRACT-ONLY** | Execution-aware regression test generation with LLMs; abstract only. |
| B34 | Ding et al. (2024) | TRACED: Execution-aware Pre-training for Source Code | Proceedings of the IEEE/ACM 46th International Conferen | `10.1145/3597503.3608140` | Crossref | **FULL-TEXT-READ (partial)** | Ding et al. ICSE 2024; arXiv 2306.07487 read (method + evaluation). |
| B35 | Liu et al. (2023) | Code Execution with Pre-trained Language Models | Findings of the Association for Computational Linguisti | `10.18653/v1/2023.findings-acl.308` | Crossref | **FULL-TEXT-READ (partial)** | Liu et al. Findings ACL 2023; arXiv 2305.05383 text extracted; method/eval skimmed. |
| B36 | Ni et al. (2024) | NExT: Teaching Large Language Models to Reason about Code Execution | arXiv preprint (venue not stated in arXiv record) | `arXiv:2404.14662` | arXiv API | **FULL-TEXT-READ (partial)** | Ni et al. 2024; text extracted; skimmed. |
| B37 | Wang et al. (2017) | Dynamic Neural Program Embedding for Program Repair | arXiv preprint (v4); arXiv record gives no venue | `arXiv:1711.07163` | arXiv API | **FULL-TEXT-READ** | Wang, Singh, Su; code github.com/keowang/dynamic-program-embedding. Text read. |
| B38 | Wang et al. (2020) | Blended, precise semantic program embeddings | Proceedings of the 41st ACM SIGPLAN Conference on Progr | `10.1145/3385412.3385999` | Crossref | **FULL-TEXT-READ (partial)** | PLDI 2020; arXiv 1907.02136 text extracted, skimmed. |
| B39 | Piech et al. (2015) | Learning Program Embeddings to Propagate Feedback on Student Code | ICML 2015 (PMLR v37; arXiv comment + PMLR page title ve | `arXiv:1505.05969` | arXiv API | **ABSTRACT-ONLY** | Abstract: linear map embedded-precondition→embedded-postcondition; NOT an LSTM (contradicts repo PRIOR_ART_MATRIX [41]). |
| B40 | Pei et al. (2023) | Learning Approximate Execution Semantics From Traces for Binary Function Similarity | IEEE Transactions on Software Engineering | `10.1109/tse.2022.3231621` | Crossref | **ABSTRACT-ONLY** | Trex (TSE 2023): micro-trace execution semantics for BINARY similarity; abstract only. Peripheral. |
| B41 | Mammadov et al. (2026) | Neural Program Modeling Learning Program-Specific Models that Predict Execution Features from Input Features a | ACM Transactions on Software Engineering and Methodolog | `10.1145/3845620` | Crossref | **ABSTRACT-ONLY** | Neural program modeling (predict traces/coverage); abstract only. Peripheral. |
| B42 | Jiang et al. (2009) | Automatic mining of functionally equivalent code fragments via random testing | Proceedings of the eighteenth international symposium o | `10.1145/1572272.1572283` | Crossref | **ABSTRACT-ONLY** | Random-test I/O functional equivalence mining (ISSTA 2009); abstract only. |
| B43 | Elva et al. (2012) | Semantic clone detection using method IOE-behavior | 2012 6th International Workshop on Software Clones (IWS | `10.1109/iwsc.2012.6227874` | Crossref | **ABSTRACT-ONLY** | IOE-behaviour semantic clones (IWSC 2012); abstract only. |
| B44 | Su et al. (2016) | Code relatives: detecting similarly behaving software | Proceedings of the 2016 24th ACM SIGSOFT International  | `10.1145/2950290.2950321` | Crossref | **ABSTRACT-ONLY** | Code relatives (FSE 2016); abstract only. |
| B45 | Su et al. (2016) | Challenges in Behavioral Code Clone Detection | 2016 IEEE 23rd International Conference on Software Ana | `10.1109/saner.2016.75` | Crossref | **ABSTRACT-ONLY** | Challenges in behavioral code clone detection (SANER 2016); abstract only. |
| B46 | Mathew et al. (2020) | SLACC | Proceedings of the ACM/IEEE 42nd International Conferen | `10.1145/3377811.3380407` | Crossref | **ABSTRACT-ONLY** | SLACC (ICSE 2020); arXiv 2002.03039 exists (not read); abstract read. |
| B47 | Suzuki et al. (2017) | An Exploratory Study of Functional Redundancy in Code Repositories | 2017 IEEE 17th International Working Conference on Sour | `10.1109/scam.2017.21` | Crossref | **ABSTRACT-ONLY** | Functional redundancy study (SCAM 2017); abstract only. |
| B48 | Myles et al. (2004) | Detecting Software Theft via Whole Program Path Birthmarks | Lecture Notes in Computer Science | `10.1007/978-3-540-30144-8_34` | Crossref | **METADATA-ONLY** | WPP birthmarks (LNCS 2004): no abstract retrieved. |
| B49 | Myles et al. (2005) | K-gram based software birthmarks | Proceedings of the 2005 ACM symposium on Applied comput | `10.1145/1066677.1066753` | Crossref | **ABSTRACT-ONLY** | K-gram birthmarks (SAC 2005); abstract only. |
| B50 | Wang et al. (2009) | Detecting Software Theft via System Call Based Birthmarks | 2009 Annual Computer Security Applications Conference | `10.1109/acsac.2009.24` | Crossref | **ABSTRACT-ONLY** | System-call birthmarks (ACSAC 2009); abstract only. |
| B51 | Schuler et al. (2007) | A dynamic birthmark for java | Proceedings of the twenty-second IEEE/ACM international | `10.1145/1321631.1321672` | Crossref | **ABSTRACT-ONLY** | Dynamic birthmark for Java (ASE 2007); abstract only. |
| B52 | Badihi et al. (2020) | ARDiff: scaling program equivalence checking via iterative abstraction and refinement of common code | Proceedings of the 28th ACM Joint Meeting on European S | `10.1145/3368089.3409757` | Crossref | **ABSTRACT-ONLY** | ARDiff is ESEC/FSE 2020 (NOT ICSE 2020 as stated in task prompt); abstract only. |
| B53 | Lahiri et al. (2012) | SYMDIFF: A Language-Agnostic Semantic Diff Tool for Imperative Programs | Lecture Notes in Computer Science | `10.1007/978-3-642-31424-7_54` | Crossref | **METADATA-ONLY** | SymDiff (CAV 2012); no abstract retrieved. |
| B54 | Godlin et al. (2012) | Regression verification: proving the equivalence of similar programs | Software Testing, Verification and Reliability | `10.1002/stvr.1472` | Crossref | **ABSTRACT-ONLY** | Regression verification (STVR 2012 journal version; DAC 2009 version 10.1145/1629911.1630034 not separately verified). |
| B55 | Lahiri et al. (2013) | Differential assertion checking | Proceedings of the 2013 9th Joint Meeting on Foundation | `10.1145/2491411.2491452` | Crossref | **ABSTRACT-ONLY** | Differential assertion checking (ESEC/FSE 2013); abstract only. |
| B56 | Person et al. (2011) | Directed incremental symbolic execution | ACM SIGPLAN Notices | `10.1145/1993316.1993558` | Crossref | **ABSTRACT-ONLY** | Directed incremental symbolic execution (PLDI 2011, SIGPLAN Notices 46); abstract only. |
| B57 | Kuchta et al. (2018) | Shadow Symbolic Execution for Testing Software Patches | ACM Transactions on Software Engineering and Methodolog | `10.1145/3208952` | Crossref | **ABSTRACT-ONLY** | Shadow symbolic execution (TOSEM 2018); abstract only. |
| B58 | Partush et al. (2014) | Abstract semantic differencing via speculative correlation | Proceedings of the 2014 ACM International Conference on | `10.1145/2660193.2660245` | Crossref | **ABSTRACT-ONLY** | Abstract semantic differencing (OOPSLA 2014); abstract only. |
| B59 | Churchill et al. (2019) | Semantic program alignment for equivalence checking | Proceedings of the 40th ACM SIGPLAN Conference on Progr | `10.1145/3314221.3314596` | Crossref | **ABSTRACT-ONLY** | Semantic program alignment (PLDI 2019); abstract only. |
| B60 | Sarker et al. (2025) | Hybrid Equivalence/Non-Equivalence Testing | 2025 IEEE Conference on Software Testing, Verification  | `10.1109/icst62969.2025.10988990` | Crossref | **ABSTRACT-ONLY** | Hybrid equivalence/non-equivalence testing (ICST 2025); abstract only. |
| B61 | Liang et al. (2025) | Unified and Split Symbolic Execution for Exposing Semantic Differences | ACM Transactions on Software Engineering and Methodolog | `10.1145/3705299` | Crossref | **ABSTRACT-ONLY** | Unified/split symbolic execution (TOSEM 2025); abstract only. |
| B62 | Wei et al. (2025) | EquiBench: Benchmarking Large Language Models’ Reasoning about Program Semantics via Equivalence Checking | Proceedings of the 2025 Conference on Empirical Methods | `10.18653/v1/2025.emnlp-main.1718` | Crossref | **FULL-TEXT-READ** | EMNLP 2025 main (DOI 10.18653/v1/2025.emnlp-main.1718); arXiv 2502.12466v3 read; code github.com/Anjiang-Wei/EquiBench. |
| B63 | Oza et al. (2025) | LLMs are Brittle to Simple Code Transformations: Introducing CETBench - A Benchmark for Code-Equivalence Check | Findings of ACL 2026 | `10.18653/v1/2026.findings-acl.2070` | arXiv API | **ABSTRACT-ONLY** | CETBench; arXiv abstract; venue per arXiv journal_ref. |
| B64 | Tandon et al. (2026) | Re-evaluating Detection of Equivalent Mutants using LLMs: We Should Properly Measure How Far We Are | Proceedings of the ACM on Software Engineering | `10.1145/3832250` | Crossref | **ABSTRACT-ONLY** | LLM equivalent-mutant detection re-evaluation (PACMSE 2026); abstract only. |
| B65 | Yu et al. (2022) | Assessing and Improving an Evaluation Dataset for Detecting Semantic Code Clones via Deep Learning | ACM Transactions on Software Engineering and Methodolog | `10.1145/3502852` | Crossref | **ABSTRACT-ONLY** | Yu et al. TOSEM 2022 (BigCloneBench label quality); abstract only. |
| B66 | Krinke et al. (2025) | How the Misuse of a Dataset Harmed Semantic Clone Detection | Empirical Software Engineering (accepted per arXiv comm | `arXiv:2505.04311` | arXiv API | **ABSTRACT-ONLY** | Krinke & Ragkhitwetsagul: BigCloneBench WT3/T4 mislabelled (93.9%); arXiv abstract read. |
| B67 | Just et al. (2014) | Are mutants a valid substitute for real faults in software testing? | Proceedings of the 22nd ACM SIGSOFT International Sympo | `10.1145/2635868.2635929` | Crossref | **ABSTRACT-ONLY** | Mutants vs real faults (FSE 2014); abstract only. |
| B68 | Ojdanic et al. (2023) | Mutation Testing in Evolving Systems: Studying the Relevance of Mutants to Code Evolution | ACM Transactions on Software Engineering and Methodolog | `10.1145/3530786` | Crossref | **FULL-TEXT-READ (partial)** | Commit-relevant mutants (TOSEM 2023); arXiv 2112.14566 text extracted; abstract+design excerpt read. |
| B69 | Papadakis et al. (2015) | Trivial Compiler Equivalence: A Large Scale Empirical Study of a Simple, Fast and Effective Equivalent Mutant  | 2015 IEEE/ACM 37th IEEE International Conference on Sof | `10.1109/icse.2015.103` | Crossref | **ABSTRACT-ONLY** | Trivial Compiler Equivalence (ICSE 2015); abstract only. |
| B70 | Kintis et al. (2018) | Detecting Trivial Mutant Equivalences via Compiler Optimisations | IEEE Transactions on Software Engineering | `10.1109/tse.2017.2684805` | Crossref | **ABSTRACT-ONLY** | Detecting trivial mutant equivalences via compiler optimisations (TSE 2018); abstract only. |
| B71 | Chekam et al. (2017) | An Empirical Study on Mutation, Statement and Branch Coverage Fault Revelation That Avoids the Unreliable Clea | 2017 IEEE/ACM 39th International Conference on Software | `10.1109/icse.2017.61` | Crossref | **ABSTRACT-ONLY** | Chekam et al. ICSE 2017; abstract only. |
| B72 | Fu et al. (2017) | Easy over hard: a case study on deep learning | Proceedings of the 2017 11th Joint Meeting on Foundatio | `10.1145/3106237.3106256` | Crossref | **FULL-TEXT-READ (partial)** | Easy over Hard (FSE 2017); arXiv 1703.00133 abstract + intro read; a "simpler baseline vs DL" precedent only (not an edit-size-confound study). |
| B73 | Chakraborty et al. (2022) | Deep Learning Based Vulnerability Detection: Are We There Yet? | IEEE Transactions on Software Engineering | `10.1109/tse.2021.3087402` | Crossref | **ABSTRACT-ONLY** | DL vulnerability detection "are we there yet" (TSE 2022); abstract only (dataset realism). |
| B74 | Croft et al. (2023) | Data Quality for Software Vulnerability Datasets | 2023 IEEE/ACM 45th International Conference on Software | `10.1109/icse48619.2023.00022` | Crossref | **ABSTRACT-ONLY** | Data quality for vulnerability datasets (ICSE 2023); abstract only. |
| B75 | Allamanis (2019) | The adverse effects of code duplication in machine learning models of code | Proceedings of the 2019 ACM SIGPLAN International Sympo | `10.1145/3359591.3359735` | Crossref | **ABSTRACT-ONLY** | Adverse effects of code duplication (Onward! 2019); abstract only. |
| B76 | Geirhos et al. (2020) | Shortcut learning in deep neural networks | Nature Machine Intelligence | `10.1038/s42256-020-00257-z` | Crossref | **METADATA-ONLY** | Shortcut learning in DNNs (Nat. Mach. Intell. 2020); no abstract retrieved. |
| B77 | Rabin et al. (2021) | On the generalizability of Neural Program Models with respect to semantic-preserving program transformations | Information and Software Technology | `10.1016/j.infsof.2021.106552` | Crossref | **METADATA-ONLY** | Generalizability of neural program models under semantic-preserving transformations (IST 2021); no abstract retrieved. |
| B78 | Kamei et al. (2013) | A large-scale empirical study of just-in-time quality assurance | IEEE Transactions on Software Engineering | `10.1109/tse.2012.70` | Crossref | **ABSTRACT-ONLY** | JIT quality assurance (TSE 2013): change-level defect prediction from change metrics; abstract (first ~900 chars) read; that change SIZE is a strong predictor is NOT verified from the retrieved text (needs full-text check). |
| B79 | Nagappan et al. (2005) | Use of relative code churn measures to predict system defect density | Proceedings of the 27th international conference on Sof | `10.1145/1062455.1062514` | Crossref | **METADATA-ONLY** | Relative code churn measures vs defect density (ICSE 2005; title-level only; finding not verified here). |
| B80 | Widyasari et al. (2020) | BugsInPy: a database of existing bugs in Python programs to enable controlled testing and debugging studies | Proceedings of the 28th ACM Joint Meeting on European S | `10.1145/3368089.3417943` | Crossref | **ABSTRACT-ONLY** | BugsInPy (ESEC/FSE 2020); arXiv 2401.15481 text extracted (not read in depth). |
| B81 | Lin et al. (2017) | QuixBugs: a multi-lingual program repair benchmark set based on the quixey challenge | Proceedings Companion of the 2017 ACM SIGPLAN Internati | `10.1145/3135932.3135941` | Crossref | **ABSTRACT-ONLY** | QuixBugs = Lin, Koppel, Chen, Solar-Lezama (SPLASH-Companion 2017) -- repo had wrong authors/venue. |
| B82 | Just et al. (2014) | Defects4J: a database of existing faults to enable controlled testing studies for Java programs | Proceedings of the 2014 International Symposium on Soft | `10.1145/2610384.2628055` | Crossref | **ABSTRACT-ONLY** | Defects4J (ISSTA 2014). |
| B83 | Svajlenko et al. (2014) | Towards a Big Data Curated Benchmark of Inter-project Code Clones | 2014 IEEE International Conference on Software Maintena | `10.1109/icsme.2014.77` | Crossref | **ABSTRACT-ONLY** | BigCloneBench (ICSME 2014). |
| B84 | Puri et al. (2021) | CodeNet: A Large-Scale AI for Code Dataset for Learning a Diversity of Coding Tasks | NeurIPS 2021 Datasets & Benchmarks (venue not in arXiv  | `arXiv:2105.12655` | arXiv API | **ABSTRACT-ONLY** | CodeNet; arXiv abstract. |
| B85 | Li et al. (2022) | Competition-level code generation with AlphaCode | Science | `10.1126/science.abq1158` | Crossref | **ABSTRACT-ONLY** | AlphaCode / CodeContests (Science 2022). |
| B86 | Kessel (2023) | LASSO – an observatorium for the dynamic selection, analysis and comparison of software | PhD thesis, University of Mannheim | `MADOC 64107 (no DOI); URL madoc.bib.uni-mannheim.de` | MADOC record (browser session) | **FULL-TEXT-READ (partial)** | Open PDF downloaded; §§3.4.1, 9.1-9.2, 11.2, 16.1-16.2 read. Thesis-level (NOT the SCAM 2019 protocol). |
| B87 | Kessel et al. (2024) | Code search engines for the next generation | Journal of Systems and Software | `10.1016/j.jss.2024.112065` | Crossref | **FULL-TEXT-READ (partial)** | CC-BY MADOC copy; read for equivalence/behaviour-comparison passages. |
| B88 | Kessel et al. (2024) | Promoting open science in test-driven software experiments | Journal of Systems and Software | `10.1016/j.jss.2024.111971` | Crossref | **FULL-TEXT-READ (partial)** | CC-BY MADOC copy; skimmed. |
| B89 | Kessel (2026) | Treating Run-time Execution History as a First-Class Citizen: Co-Versioning Run-time Behavior alongside Code | Proceedings of the 34th ACM International Conference on | `10.1145/3803437.3805589` | Crossref | **FULL-TEXT-READ** | FSE Companion 2026 (5 pp.) vision paper: co-versioning run-time behaviour; read in full. |
| B90 | Kessel et al. (2022) | Diversity-driven unit test generation | Journal of Systems and Software | `10.1016/j.jss.2022.111442` | Crossref | **METADATA-ONLY** | Diversity-driven unit test generation (JSS 2022); metadata only. |
| B91 | Kessel et al. (2019) | Automatically Curated Data Sets | 2019 19th International Working Conference on Source Co | `10.1109/scam.2019.00015` | Crossref | **ABSTRACT-ONLY** | Automatically Curated Data Sets (SCAM 2019); abstract only. |
| B92 | Kessel et al. (2025) | Morescient GAI for Software Engineering | ACM Transactions on Software Engineering and Methodolog | `10.1145/3709354` | Crossref | **ABSTRACT-ONLY** | Morescient GAI (TOSEM 2025; arXiv 2406.04710); abstract only. |
| B93 | Harrand et al. (2019) | The Strengths and Behavioral Quirks of Java Bytecode Decompilers | 2019 19th International Working Conference on Source Co | `10.1109/scam.2019.00019` | Crossref | **ABSTRACT-ONLY** | DOI-collision witness: 10.1109/SCAM.2019.00019 is Harrand et al., NOT Kessel & Atkinson (repo error). |
| B94 | Arnaoty et al. (2024) | OneSpace: Detecting cross-language clones by learning a common embedding space | Journal of Systems and Software | `10.1016/j.jss.2023.111911` | Crossref | **METADATA-ONLY** | Citer of K&A (OpenAlex forward-citation list); metadata only. |
| B95 | Leone et al. (2022) | Towards Overcoming Type Limitations in Semantic Clone Detection | 2022 IEEE 16th International Workshop on Software Clone | `10.1109/iwsc55060.2022.00013` | Crossref | **METADATA-ONLY** | Leone & Takada IWSC 2022; citer of K&A; metadata only. |
| B96 | Su et al. (2016) | Identifying functionally similar code in complex codebases | 2016 IEEE 24th International Conference on Program Comp | `10.1109/icpc.2016.7503720` | Crossref | **METADATA-ONLY** | Identifying functionally similar code in complex codebases (ICPC 2016); metadata only. |


### A.2 NOT-FOUND / UNVERIFIED (deliberately kept OUT of the verified table)

| Item (as named in task or repo) | Result | Evidence |
|---|---|---|
| "Sumner et al., *Comparative analysis of software behavioral traces*, ICST 2011" (repo `PRIOR_ART_MATRIX` [42]; task prompt) | **NOT-FOUND** | Crossref bibliographic query top hits: *Precise Calling Context Encoding* (TSE 2012, 10.1109/tse.2011.70; Sumner, Zheng, Weeratunge, Zhang), *Selecting peers for execution comparison* (ISSTA 2011, 10.1145/2001420.2001458), *Comparative causality* (ICSE 2013). DBLP (browser session): title query returns **0 hits**; Sumner 2011 = `conf/issta/SumnerBZ11`. File `dblp/dblp_browser_session_2026-11-14.json`. |
| "Ding et al., *Learning Executable Semantics for Software Engineering*" | **NOT-FOUND** | arXiv title/author queries (`arxiv/search_ding_exec1.xml`, `search_ding_exec2.xml`) return only unrelated papers; Crossref query returns unrelated items. Nearest verified: TRACED (Ding, Steenhoek, Pei, Kaiser, Le, Ray; ICSE 2024). |
| SABER — "Identifying SimilAr BEhavioR for program comprehension" (Sridhar, Qiao, Kaiser) | **UNVERIFIED** (appears only in OpenAlex/S2 citer lists of K&A; no DOI; Crossref has no record; arXiv search empty) | `openalex/fwd_kessel_atkinson.json`, `arxiv/search_saber.xml` |
| AgentExecutor, Treefix (ICSE 2025), RippleGUItester, Condor (TSE 2025), "False Proximity: Frozen Code Embeddings Invert Similarity on Behaviourally Divergent Mutant Pairs" (Research Square preprint 2026) | **UNVERIFIED** here (listed only by OpenAlex forward-citation/keyword output; not independently confirmed against Crossref/arXiv). The last one is potentially relevant (embedding similarity vs behavioural divergence of mutants) and should be checked by the manuscript author. | `openalex/fwd_traced.json`, `fwd_changeguard.json` |
| EquiBench title in repo ("Understanding …", "NeurIPS 2025 Workshop", 5 authors) | **WRONG** — verified: *EquiBench: Benchmarking Large Language Models' Reasoning about Program Semantics via Equivalence Checking*, 11 authors, **EMNLP 2025 main**, DOI 10.18653/v1/2025.emnlp-main.1718 (Crossref), arXiv 2502.12466v3 | B62 |
| Repo's DOI `10.1109/SCAM.2019.00019` for K&A | **WRONG** — that DOI = Harrand et al., *The Strengths and Behavioral Quirks of Java Bytecode Decompilers* (B93). Correct K&A DOI `10.1109/SCAM.2019.00030` (B01). |
| Piech 2015 as "supervised LSTM over variable-state traces" (repo [41]) | **CONTRADICTED by abstract**: "encode programs as a linear mapping from an embedded precondition space to an embedded postcondition space" (ICML 2015). Full text not read. | B39 |
| Venue claims not stated by the primary record: Wang–Singh–Su (often cited as ICLR 2018), NExT (ICML 2024), CodeNet (NeurIPS 2021 D&B) | **Not confirmed** from the retrieved records; cited as arXiv/preprints unless the manuscript author confirms. | B36, B37, B84 |
| McKeeman 1998 full text | not located; DBLP metadata only | B15 |

---

## B. TECHNICAL COMPARISON OF THE CLOSEST APPROACHES vs SBG

Legend: **Out?** = does the method read program *outputs* (return value / stdout / test-pass-fail)? Access: FT = full text read; FTp = partial; AB = abstract only. "per DCI" = secondhand description inside DCI §7.2 (FT), not the original. Facts not obtainable at my access level are marked UNVERIFIED.

| Approach (access) | Unit of comparison | What is recorded from execution | Distance / decision rule | Labels / datasets | Evaluation / metrics | Out? | Inputs | Language | Released code / benchmark |
|---|---|---|---|---|---|---|---|---|---|
| **SBG (repo; read via code + docs)** | pair of versions of one program; entry function/class driven | `sys.settrace` events call/return/exception/line + `repr(locals)` (≤100 chars). V3: anonymised call-frequency, call-transition bigrams, coverage size, exception type set/rate/(fn,exc,depth) hash, depth/length stats. Temporal: call trigrams, exception transitions, causal pairs, phase Shannon diversity, loop run-lengths. State: abstract-value transition tuples (func_idx, pre_state, event, post_state) | `0.50·d_V3 + 0.25·d_temporal + 0.25·d_state`; d_V3 = fixed-weight mean of 8 L1/Jaccard/abs-diff terms (`sbg/v3/genome.py` L441-); score ranks pairs CHANGED vs EQUIVALENT | composed benchmark: SP transformations ⇒ EQUIVALENT, SC mutations ⇒ CHANGED; label = outputs differ on 11 synthesised inputs (oracle-validated); V10: 19 Python programs; BugsInPy/QuixBugs real-bug sets | AUROC, program-cluster bootstrap, Holm; edit-size baseline AUROC 0.616 vs SBG 0.897 (repo figures, not re-run by A1) | No (return/stdout not read) **but locals' reprs are** (V6) | synthesised from annotations; 11 per program | Python | repo |
| **Kessel & Atkinson 2019** (AB; thesis/JSS-2024/FSE-2026 FTp for framework context) | pairs/sets of candidate implementations of the same functionality | *Thesis-level:* "actuations" = serialised response values per stimulus in a stimulus-response matrix. SCAM protocol itself: UNVERIFIED | judged functionally equivalent iff responses identical on all sampled stimuli; thesis §11.2: output-string distance matrices for graded similarity | abstract: "original experiment" (4 tests ≈85 %) vs "larger study"; datasets UNVERIFIED | abstract: % non-equivalence recognised vs #tests (random ≥39; coverage-based far fewer). AUROC/ranking: UNVERIFIED | **Yes** | random vs coverage-based generated tests (abstract) | Java (thesis/LASSO; SCAM-specific UNVERIFIED) | LASSO platform (thesis says open; not verified by me) |
| **Behaviour sampling / I-O semantic clones**: Podgurski & Pierce 1992/93; Jiang & Su 2009; Elva & Leavens 2012; Suzuki 2017; SLACC 2020 (all AB) | code fragments / methods | responses (outputs; Elva & Leavens also params and pre/post heap state "IOE-behavior"; SLACC: I/O behaviour across Java & Python) | identical (or clustered) I/O on sampled inputs ⇒ functionally equivalent | clone/redundancy mining corpora (e.g., 68 SourceForge Java projects for Suzuki) | precision of mined clusters; no change-detection ranking | **Yes** | random / amplified inputs | Java, Python (SLACC) | varied; not verified |
| **Evans & Savoia 2007** (AB) | system versions | outcomes of test suites generated for both versions | differential contrast of two suites on both versions | n/a (abstract) | UNVERIFIED | Yes (test outcomes) | tests for both versions | UNVERIFIED | UNVERIFIED |
| **BERT, Jin–Orso–Xie 2010** (AB; per DCI) | changed classes between versions | return values & object state values from generated tests (Randoop) on both versions | report of all differing values; human review | small artificial project (~60 % of generated inputs reveal seeded diff); Joda-Time 54 version pairs → 36 differences, 1 real regression (secondhand) | counts | **Yes** | Randoop-generated | Java | Eclipse plugin; availability UNVERIFIED |
| **DCI, Danglot et al. EMSE 2020** (FT) | commit (pre/post) | amplified-test pass/fail on both versions (DSpot) | behavioural change ⇔ amplified test passes pre, fails post | 60 commits, 6 Java projects, hand-checked | detected 25/60 (SBAMPL, RQ1 answer; the §RQ1 text also says 28/60 — internal inconsistency in the paper), 9/60 (AAMPL); applicable to 15.29 % of commits; no AUROC | **Yes** (assertions) | DSpot amplification of existing tests | Java/Maven | github.com/STAMP-project/dspot (LGPL-3.0), dspot-experiments |
| **ChangeGuard, Gröninger–Souza–Pradel FSE 2025** (FT) | Python function old/new (commit-level) | args, return value, stdout/stderr, external-call log, intentional exceptions under learning-guided execution (LExecutor injects neural-predicted values) | any difference ⇒ semantics-changing; no difference after k=300 executions ⇒ "likely preserving"; else inconclusive | 224 manually annotated commits from 10 Python projects + 3 automated-refactoring datasets | precision 77.1 %, recall 69.5 % (regression tests: recall 7.6 %); no AUROC, no edit-size control | **Yes** | neural value injection (LExecutor) | Python | github.com/sola-st/ChangeGuard (MIT, last push 2025-05-21), LExecutor (MIT) |
| **Xie & Notkin 2005** (AB) | old/new version of a program | value spectra (internal state values at function boundaries) and path spectra | spectra differences ⇒ deviation-propagation call tree; heuristics locate deviation roots | 8 C programs | detection of deviations "even when outputs are the same"; root-location accuracy | internal values yes; final outputs not required | existing test inputs | C | UNVERIFIED |
| **Harrold et al. 1998/2000; Reps et al. 1997** (AB) | program runs | program spectra (path/branch/profile counts) | spectra differences correlate with regression faults | UNVERIFIED | UNVERIFIED | No (internal) | tests | C-family | n/a |
| **Sumner & Zhang 2013 / Sumner 2011** (AB) | two executions | trace + state; state replacement for causality; peer selection for execution comparison | alignment + causal inference (debugging, not a scorer) | UNVERIFIED | debugging precision/efficiency | internal state | given runs | Java/C (UNVERIFIED) | UNVERIFIED |
| **Dynamic birthmarks** Myles & Collberg 2004/05; Wang et al. 2009; Schuler et al. 2007 (AB) | program pair (suspected theft) | whole-program-path / instruction k-grams; system-call short sequences; API-call usage (Java) | set/sequence similarity over k-grams; resilience to obfuscation/compiler differences by design | UNVERIFIED | credibility & resilience | No | runs | Win/Java/Linux | UNVERIFIED |
| **DyCLINK / code relatives, Su et al. FSE 2016** (AB) | code fragments | instruction-level traces → dynamic dependence graphs | subgraph matching | 422+ M instructions across codebases (abstract) | UNVERIFIED | No (internal) | sample executions | Java | UNVERIFIED |
| **Wang–Singh–Su 2017 / Wang–Su 2020** (FT / FTp) | program (repair / classification) | variable-value traces; blended symbolic+concrete traces | learned embedding | student/benchmark programs | repair/classification accuracy | internal values | tests | C# (2017) / C# + Python via Roslyn/IronPython (2020) | github.com/keowang/dynamic-program-embedding |
| **TRACED / CodeExecutor / NExT** (FTp) | code snippet | executed-trace supervision (variable values, coverage, branches) used to pre-train/finetune LLMs | learned | CodeNet-style, clone/vuln tasks (TRACED) | task accuracy | trace values | existing inputs | Python/Java | public models (not verified for each) |
| **Testora / Mokav / ProbeGen / SemaDiff / PatchGuru** (FT/FT/FT/FTp/AB) | PR/commit/function pair | tests generated by LLM; outputs of old/new | differences + (Testora) LLM intent classification; Mokav: difference-exposing test search | Testora: PRs of Python projects (19 regressions found); Mokav: 1535 Codeforces Python pairs + 32 QuixBugs pairs; PatchGuru: 400 PRs | bugs found / DET success rate | **Yes** | LLM-generated | Python (Java for SemaDiff per abstract: UNVERIFIED) | Testora MIT (pushed 2026-03-12) |
| **EquiBench** (FT) | program pair | none (LLM judges source) | binary equivalence over *all* inputs | 2400 pairs, 4 languages, 6 categories | accuracy (19 LLMs) | n/a | n/a | C, CUDA, Python, x86-64 (4 langs per abstract) | github.com/Anjiang-Wei/EquiBench (Apache-2.0) |
| **ARDiff / SymDiff / regression verification / DiSE / shadow SE** (AB) | program pair | none (static/symbolic) | prove equivalence or generate witness | EQBench, ARDiff benchmarks etc. | proved/disproved counts, time | no | symbolic | Java/C/Boogie | varied; not verified |
| **Kessel FSE 2026 vision** (FT) | version history | behavioural fingerprints: I/O values + call sequences + side effects + performance (proposal; Python prototype on dateutil) | semantic diff via fingerprint comparison (proposal) | none (vision) | none | partly (I/O values) | n/a | Python | UNVERIFIED |

---

## C. HEAD-TO-HEAD COMPARABILITY CLASSIFICATION (A/B/C/D) — for Agent A4

Class legend: **A** directly comparable and faithfully implementable on SBG's trace cache/inputs; **B** adaptable with documented assumptions; **C** qualitative comparison only; **D** not comparable.
Constraints used: shared trace cache holds run-0 traces of the 11 label-defining inputs (PROTOCOL §3); no numpy/scipy/sklearn/torch; no network LLM access assumed.

| Approach | Class | Technical justification | Faithfulness caveat to report |
|---|---|---|---|
| Edit-size / lexical / identifier-linear baselines (Yu 2022 style), AST/bytecode-distance, TCE-style bytecode equality | **A** | Computable from sources only; algorithm trivially specified; same pairs, same labels | TCE (Papadakis 2015) targets equivalent *mutants* by compiled-binary identity; Python analogue = normalised `dis` bytecode equality — label as "TCE-analogue" |
| Execution-statistics baseline (coverage count, trace length, event counts) | **A** | Fully specified by the trace schema; no hidden hyper-parameters | repo already has `M_EX`; check it is the strong version |
| k-gram call-sequence Jaccard / set-containment (Myles & Collberg 2005, Wang 2009, Schuler 2007) | **A** (algorithm) / **B** (task) | Algorithm is a plain set similarity over call n-grams; but birthmarks are designed to be *invariant* to semantics-preserving changes for plagiarism detection, not to rank change; adaptation = score = 1−Jaccard | ≈ SBG's own V3 bigram term; expect near-identical behaviour (not an independent baseline) |
| Output-sampling comparator (K&A behaviour sampling; Evans & Savoia; BERT; ChangeGuard comparator; DCI-analogue) | **B** | Decision rule is simple (any response differs ⇒ non-equivalent; or fraction of differing inputs), but **on the 11 label-defining inputs it reproduces the label (tautology)**. Needs *independent inputs* (new executions with a different generator/seed) or a reduced-k protocol | K&A SCAM protocol not read (AB). Thesis-level description only. Never describe the baseline as "Kessel & Atkinson's method as published" |
| Value-spectra / path-spectra comparison (Xie & Notkin; Harrold; Reps) | **B** | Python port: record (function, entry args / exit values) tuples (value spectra) or per-function path/branch counts (path spectra) and compare sets/counts between versions; ranking by Jaccard or count of differing spectrum elements. This is the closest *output-free-ish* prior art and the most informative adaptation | Original is C and used as a debugging aid with deviation-propagation call tree; scoring rule is an adaptation; abstract-only access |
| Trace-alignment (LCS / edit distance on call-event sequences; Sumner-style; NumericalDiff-style) | **B** | Adapt as normalised LCS distance over anonymised call sequences per input, averaged; cheap | Original is causal-inference/debugging; the scorer is an adaptation |
| DCI (Danglot) | **C** | Needs DSpot test amplification on Java/Maven projects; no Python implementation; label = amplified test failing post-commit | A-priori adaptation "generate assertion-bearing tests on old version, replay on new" collapses to the output-sampling comparator (B above) |
| DyCLINK / code relatives | **C** | Instruction-level dynamic dependence graph + subgraph matching, Java instrumentation; no Python implementation; code availability unverified | Could approximate with call-level dependence; do not call it DyCLINK |
| ChangeGuard (faithful) | **D**; comparator-only **B** | Faithful version requires LExecutor's neural value injection (torch/CodeT5) to execute without real inputs; **comparator-only variant** (same decision rule on real inputs) is B | Closest same-task competitor — must be discussed qualitatively even if not run; report P/R as published (77.1 %/69.5 %; different dataset) — not comparable numbers |
| Neural execution models: TRACED, Wang–Singh–Su, blended embeddings, CodeExecutor, NExT | **D** (qualitative **C**) | Require pre-trained/fine-tuned neural models, torch/GPU; none was designed for pairwise change/equivalence scoring; label supervision differs | At most a clearly labelled non-neural bag-of-trace-tokens proxy (class C/B-weak), never named after those papers |
| LLM judges/test generators: Testora, Mokav, ProbeGen, SemaDiff, PatchGuru, EquiBench | **D** | Need LLM access; Testora/PatchGuru consume NL PR text SBG never sees; EquiBench labels are *all-input* equivalence on C/CUDA/x86 etc.; Mokav searches for difference-exposing inputs (output-reading) | Qualitative discussion; Mokav-type "search for a DET" is the independent-inputs analogue of the B comparator |
| Symbolic / verification: ARDiff, SymDiff, regression verification, DiSE, shadow SE, Churchill, Hybrid equiv testing, Unified/Split SE | **D** (qualitative **C**) | Prove/disprove equivalence for Java/C/Boogie subjects; produce proofs/witnesses, not graded scores; no Python tool re-implemented in the allowed stack | Cite as the "sound but non-scalable" pole; do not claim SBG supersedes them |
| Static ML code embeddings (code2vec/CodeBERT) | **D** | not in my verified set; require pretrained weights | out of scope for A1 verification |

Priority list for A4 (my recommendation, ordered by informativeness): (1) edit-size & lexical baselines (A); (2) execution-statistics (A); (3) value/path-spectra Python port (B); (4) trace-alignment LCS (B); (5) output-sampling comparator **on independent inputs**, with the same-input run reported only as a labelled "privileged-information ceiling" (B); (6) call-k-gram Jaccard (A/B).

---

## D. NOVELTY ASSESSMENT OF EACH SBG CLAIM

Scale: STRONG NOVELTY / INCREMENTAL NOVELTY / ESTABLISHED TECHNIQUE / UNRESOLVED OVERLAP / REQUIRES ADDITIONAL INVESTIGATION. Bxx = bibliography ID in §A.1. "Access" qualifies what the rating can rely on.

| # | SBG claim | Rating | Evidence for the rating | Limit of the evidence |
|---|---|---|---|---|
| 1 | **Call topology** (anonymised call-frequency histogram, coverage size, depth/length statistics) | **ESTABLISHED TECHNIQUE** | Path/branch/profile spectra comparison across versions (Reps 1997 B10, Harrold 1998/2000 B11-B12, Xie & Notkin 2005 B04); whole-program-path and API-call birthmarks (B48-B51); execution statistics are the baseline in DCI-type work | abstract-only for all |
| 2 | **Call-order bigrams / trigrams** | **ESTABLISHED TECHNIQUE** | K-gram birthmarks over instruction sequences (Myles & Collberg 2005, B49: "credibility and resilience to semantics-preserving transformations"); system-call short-sequence birthmarks (Wang 2009 B50); API-call sequences (Schuler 2007 B51); DyCLINK (B44) | abstract-only |
| 3 | **Exception structure** (type set, rate, (fn,exc,depth) hash, exception transitions) | **ESTABLISHED TECHNIQUE** | Differential testing treats exceptions as observable behaviour (ChangeGuard compares "intentional exceptions", FT; BERT/K&A compare responses incl. exceptions: AB). The *causality hash* is a minor variant | structural (non-output) use of exceptions as features not exhaustively searched |
| 4 | **Temporal features** (trigrams, phase diversity entropy, loop run-lengths, causal pairs) | **INCREMENTAL NOVELTY** | Sequence n-grams and entropies are standard; I found no prior *pairwise version-change scorer* using this specific bundle, but the repo's own incremental-value test shows it adds nothing over execution statistics (H4 null per repo docs). Novelty of a feature bundle without demonstrated utility is weak | Search-bounded (§F); repo H4 result not re-run by A1 |
| 5 | **Abstracted state-transition genome** (abstract value domains + (func, pre, event, post) tuples) | **UNRESOLVED OVERLAP** | Overlaps value spectra (Xie & Notkin 2005 B04: internal values per function), ADABU (B14: abstract state machines of mutators/inspectors), Daikon (B13), Collector-Sahab (B18: state diff between old/new), Revealing Regressions (B19: state-capture strategies), NumericalDiff (B32: value-based trace alignment independent of variable names), Wang–Singh–Su (B37: variable-value traces). The specific *abstract-domain bucketing + transition-tuple graph + frequency-weighted Jaccard* was not found in a prior version-pair scorer, but full texts of B04/B13/B14 were not read | cannot close without reading Xie & Notkin and ADABU full text |
| 6 | **Output-free design** | **ESTABLISHED TECHNIQUE** (idea); strictness **REQUIRES ADDITIONAL INVESTIGATION** | Xie & Notkin: deviations exposed "even when program outputs are the same" (B04); path spectra and birthmarks and DyCLINK ignore outputs by design. Contrast class (K&A, ChangeGuard, BERT, DCI, Mokav, Testora) *does* read outputs. But SBG snapshots `repr(locals)` at return events (tracer L366-372) so the claim is a protocol statement; information leakage via locals untested | leakage not tested by A1 |
| 7 | **Rename-invariance** (first-call-order anonymisation) | **ESTABLISHED TECHNIQUE** | Birthmarks are designed for resilience to renaming/obfuscation (B49, B51 "obfuscators"); NumericalDiff alignment "independent of variable names" (B32); instruction-level DyCLINK is name-free (B44). Implementation detail only | abstract-only |
| 8 | **Fixed-weight distance** (0.50/0.25/0.25; inner V3 weights fixed) | **ESTABLISHED TECHNIQUE** | Weighted sum of L1/Jaccard/absolute-difference terms; weights hand-set (repo has `fit_weights.py` — A5/A-other should check whether weights were tuned on test data). The in-repo "formal pseudometric" language in `docs/research` describes a *different* 8-dimension JSD/Wasserstein/GED design not implemented in V5 | A1 did not execute the code |
| 9 | **Edit-size-confound evaluation methodology** | **INCREMENTAL NOVELTY** | Precedents for exposing trivial/lexical shortcuts: Yu et al. TOSEM 2022 (B65: "undesirable-by-design" linear identifier model matches deep models on BigCloneBench), Krinke & Ragkhitwetsagul 2025 (B66: 93.9 % of WT3/T4 pairs mislabelled), Allamanis 2019 (B75), Chakraborty 2022 (B73), Geirhos 2020 (B76), Fu & Menzies 2017 (B72). Change-size as strong baseline in change-level prediction: JIT defect prediction (Kamei B78/Nagappan–Ball B79; *size-is-strong* finding not verified here). I found **no** paper that names/quantifies an edit-size↔label confound for *behaviour-change* benchmarks built by SP transformations vs mutations — but absence in a bounded search ≠ novelty proof | adjacent areas (JIT defect prediction, mutation-size, program-repair patch size, metamorphic testing) only touched |
| 10 | **Composed size-matched benchmark** | **INCREMENTAL NOVELTY** | Matched/counterfactual pairing is standard experimental design; combining SP transformations and mutations on the same rewrite is a specific construction not found in the verified works (DCI uses real commits; EquiBench uses compiler/superoptimiser; CETBench uses random transformation sequences, B63). Still same-author, 19 programs (repo) | benchmark internals not audited by A1 |
| 11 | **Oracle-validated labels** | **ESTABLISHED TECHNIQUE** | Label "changed ⇔ outputs differ on sampled inputs" is the mutation-analysis *kill* criterion; equivalent-mutant problem and trivial-compiler/ML approximations (Papadakis 2015 B69, Kintis 2018 B70, Chekam 2017 B71), mutants-vs-real-faults validity (Just 2014 B67, Ojdanić 2023 B68). "Equivalent" labels from 11 inputs are only *sample-equivalent*, not semantic equivalence (EquiBench requires all-input) | — |
| 12 | **Program-level cluster statistics** (cluster bootstrap, LOPO, Holm) | **ESTABLISHED TECHNIQUE** (general statistics) | Standard methodology; I did **not** search SE-specific prior use — treat as "not a contribution" | no SE literature searched |
| 13 | **Incremental-value-over-execution-statistics analysis** (nested/LOPO test vs strong simple baseline) | **INCREMENTAL NOVELTY** | Strong-simple-baseline culture (Fu & Menzies B72) and ablation precedents; applying it to execution-genome vs execution-statistics is specific. The *result* is a null (repo), so the novelty is methodological | repo numbers not re-run by A1 |
| 14 | **The task**: ranking version pairs CHANGED vs EQUIVALENT by an unsupervised execution score | **UNRESOLVED OVERLAP** | Same-task competitors: ChangeGuard (B24, Python, FT), Testora (B25), SemaDiff (B28), PatchGuru (B29), K&A (B01), DCI (B17). Their mechanism reads outputs; SBG does not, and reports AUROC/edit-size control, which none of the FT-read competitors does | K&A SCAM protocol unread — K&A could already report ranking metrics |
| 15 | *(docs/research S2)* **Longitudinal/versioned behaviour genome** | **CONTRADICTED** (if ever claimed) | Kessel FSE 2026 (B89, FT) proposes co-versioning run-time behaviour with code, Behavioral Archive, semantic diff via behavioural fingerprints (vision, Python prototype). Not in current paper claims | — |
| 16 | *(docs/research)* **cross-language behavioural equivalence without shared IR** | **CONTRADICTED / ESTABLISHED** (if ever claimed) | SLACC (B46, ICSE 2020; abstract read): dynamic I/O-behaviour clone detection across Java and Python, "first to perform clone detection across languages that lack a common underlying representation"; OneSpace (B94). SBG evaluates Python only | — |

---

## E. REPO AUDIT — UNSUPPORTED ORIGINALITY CLAIMS AND WRONG CITATIONS

### E.1 Originality language (grep over `docs/`, `artifacts/paper_evidence/`, `README.md`; patterns: first/novel/no prior work/never/unique/only/unprecedented/to our knowledge)

| File:line | Text (abridged) | Assessment |
|---|---|---|
| `docs/research/NOVELTY_ANALYSIS.md:286` | "…No prior work claims or demonstrates a test-suite-free, language-agnostic, execution-behavioral regression oracle with formal pseudometric properties. **This should be the first sentence of any SBG abstract.**" | **CONTRADICTED**: ChangeGuard/Testora/PatchGuru (execution-based, test-suite-free-ish, Python) exist; "language-agnostic" never evaluated (Python only); "formal pseudometric" ≠ implemented V5 distance (weighted L1/Jaccard sum) |
| `NOVELTY_ANALYSIS.md:132,270,300-314,352-361`; `RESEARCH_QUESTION.md:37-53,87` | "first runtime-behavior-based evidence for cross-language equivalence"; "first formal normalised multi-dimensional behavioural distance"; S1/S2 "survive all attacks / most clearly novel" | **UNSUPPORTED/CONTRADICTED**: SLACC (cross-language dynamic, ICSE 2020), Kessel FSE 2026 (versioned behaviour), birthmarks; the design described (8 dims, JSD/Wasserstein/GED) is not the evaluated V5 |
| `docs/research/PRIOR_ART_MATRIX.md:628,634` (CG-1, CG-3) | "No prior work builds a versioned behavioral genome…", "…supply-chain artifact" | Unsupported (no systematic search; Kessel 2026 counter-example) |
| `PRIOR_ART_MATRIX.md:700,719` | "Why SBG is still novel vs Piech / vs Sumner" | Built on mischaracterised Piech and a non-existent Sumner paper (see E.2) |
| `PRIOR_ART_MATRIX.md:748 ff` (footer) | "All citations are to real published works" | **FALSE** (E.2) |
| `docs/archive/v5/NOVELTY_AUDIT_V5.md:204` | "the first systematic benchmark for behavioral change detection with 3577 labeled pairs" | Unsupported; DCI (60 commits), ChangeGuard (224 + 3 sets), Mokav (1535 pairs) exist; archived |
| `docs/archive/superseded/literature_novelty_audit.md:256,295,332,335` | "No prior work applies output-free dynamic behavioural comparison to BugsInPy pairs"; "No prior work combines output-free + execution-grounded + version comparison"; "No prior work compares Python–Java behaviours on same scale" | Unsupported/contradicted for the second (Xie & Notkin spectra, birthmarks, DyCLINK; SLACC for cross-language); archived |
| `docs/archive/v2/NOVELTY_AUDIT_V2.md:114-118,173`; `agents/0E_prior_art_audit.json:158,238` | "inversion phenomenon absent from all 40 surveyed works"; "genuinely novel empirical observation" | Search was over the repo's own 40-work matrix (unreliable); not a literature-wide statement; JIT-defect/clone-benchmark shortcut literature (§F) not consulted |
| `artifacts/paper_evidence/RELATED_WORK_NOVELTY_AUDIT.md:126` | "The confound mechanism is novel in this specific domain … has not been explicitly named, quantified, or remediated in the literature found." | Phrased as bounded ("literature found") — **acceptable if kept bounded**; K&A and DCI evaluation sections were not read, so "literature found" excludes them |
| `RELATED_WORK_NOVELTY_AUDIT.md:52` and `NOVELTY_CLAIM_TO_EVIDENCE.md:54` | cite K&A with **wrong DOI `10.1109/SCAM.2019.00019`** in the body (banners elsewhere correct it) and assert K&A properties (AUROC-style not reported, manual labels, baselines vs formal verification) | **UNSUPPORTED** — K&A full text never read (log says abstract only; I confirm abstract-only). Strike these cells or mark "unverified" |
| `FINAL_NOVELTY_POSITION.md`, `CLAIM_TO_EVIDENCE_MATRIX.md:32`, `MANUSCRIPT_CLAIMS_CHECKLIST.md`, `FINAL_MANUSCRIPT_BLUEPRINT.md:11,35,109` | prohibitions on "first/novel/unique"; novelty "only relative to sources read" | **Appropriate**; keep. Note FINAL_NOVELTY_POSITION relies on K&A/DCI/Kessel abstracts — compare against §B |
| `FINAL_IEEE_ACCESS_READINESS.md:108` | "The contribution is novel in the specific combination described." | Mild; supportable only as INCREMENTAL (§D 9-13) |

### E.2 Wrong / unverifiable / mismatched citations in the repo (re-verified against Crossref/DBLP/arXiv; raw in `crossref/`, `dblp/`)

| Repo location | Repo says | Verified fact | Verdict |
|---|---|---|---|
| `RELATED_WORK_NOVELTY_AUDIT.md:52`, `NOVELTY_CLAIM_TO_EVIDENCE.md:54` | K&A DOI `10.1109/SCAM.2019.00019` | = Harrand et al. decompilers paper; K&A = `…00030` | WRONG (still in body) |
| `PRIOR_ART_MATRIX` [42] | "Sumner, N., Zheng, Y., Bhansali, S., Zhang, X. *Comparative analysis of software behavioral traces.* ICST 2011. Also *Precise Calling Context Encoding*, IEEE TOSEM"; claims lossless traces, heap state, 6 C programs | No such ICST 2011 paper (DBLP 0 hits); *Precise Calling Context Encoding* is **TSE 2012** (ICSE 2010 version) by Sumner, Zheng, Weeratunge, Zhang — "Bhansali" not an author; the 2011 execution-comparison paper is *Selecting peers for execution comparison* (ISSTA 2011) | NON-EXISTENT/CONFLATED; all described properties unverified |
| [41] Piech 2015 | "execution trace features → LSTM", "supervised", "uses outputs" | abstract: linear map embedded precondition → embedded postcondition (ICML 2015, PMLR v37) | MISCHARACTERISED (abstract-level) |
| [17] | "Churchill, Sharma, Bastien, Aiken. *Sound Loop Summarization and Regression Verification.* PLDI 2019" | not found; nearby: *Semantic program alignment for equivalence checking* (Churchill, Padon, Sharma, Aiken; PLDI 2019; B59) | UNFINDABLE (repo already flags) |
| [33] | "Buch & Trivedi … SANER 2019" | title is Siow et al. SANER 2022 | WRONG (flagged by repo) |
| [39] | "DeFreez … Path-Based Function Embeddings, FSE 2018" | two records: ICSE-2018 Companion 10.1145/3183440.3195042 and FSE 2018 10.1145/3236024.3236059 (different titles) | CONFLATED (flagged) |
| [36] | heading "Meng et al. — BinaryDiff" | citation is Ding, Fung, Charland (S&P 2019) | heading wrong (flagged) |
| [5] | heading "TTAnalyze" but cited paper is *Scalable, Behavior-Based Malware Clustering* NDSS 2009; `NOVELTY_ANALYSIS.md:24` says "(NDSS 2009, TTAnalyze)" | internal heading/citation mismatch; NDSS paper not in Crossref (not independently verified here) | INCONSISTENT (unverified) |
| [12] | heading "Gabel & Su — Scalable Code Clone Detection" | cited paper = *A study of the uniqueness of source code* (FSE 2010; 10.1145/1882291.1882315) | heading/citation MISMATCH |
| [24] | heading "Nilsson & Offutt — Regression Test Selection"; cites "Nilsson, Offutt, Mellin, *Test Case Minimization for Mutation Testing of Feature Models*" + Rothermel & Harrold TSE 1996 | Rothermel & Harrold 10.1109/32.536955 verified; the Nilsson–Offutt–Mellin title not found (their Crossref records are about timeliness testing) | UNFINDABLE/MISMATCH |
| [25] | heading "Kim et al. — Automatic Test Amplification"; cites Kim et al. *Data Scientists in Software Teams* and Baudry et al. ISSTA 2014 | neither is a test-amplification paper (Baudry 2014 = *Tailored source code transformations to synthesize computationally diverse program variants*, 10.1145/2610384.2610415); real test-amplification works (DSpot, DCI, Danglot) are absent | MISMATCH (misleading) |
| [26] | "Cioroaica, Chren, Buhnova. *Behavioral Regression Testing in Component-based Systems.* SEAA 2018" | not found in Crossref | UNVERIFIED |
| [29] | "Coles et al. *PIT* … ICST 2016" | verified: *PIT: a practical mutation testing tool for Java (demo)*, **ISSTA 2016** (10.1145/2931037.2948707) | WRONG VENUE |
| EquiBench / QuixBugs entries (`RELATED_WORK_COMPARISON`, access log) | "NeurIPS 2025 Workshop", 5 authors, "Understanding…"; QuixBugs authors/venue wrong | EquiBench = EMNLP 2025 main, 11 authors; QuixBugs = Lin, Koppel, Chen, Solar-Lezama, SPLASH Companion 2017 | WRONG |
| `LITERATURE_ACCESS_LOG` (BERT) | "Joda-Time, 54 version pairs" attributed to BERT evaluation | consistent with DCI §7.2 (secondhand); also "small artificial project ~60 %" not mentioned | partial (secondhand only) |
| PRIOR_ART_MATRIX footer | "all citations are to real published works" | false for at least [17], [33], [39], [42], [24], [25] | FALSE |

---

## F. MISSING-LITERATURE RISKS (things a reviewer is likely to know that the repo does not cite or I could not read)

1. **ChangeGuard (FSE 2025)** — same task, same language, execution-based; must be cited and positioned (output-reading vs output-free; precision/recall vs AUROC; no edit-size control). *Not in the repo's prior-art matrix at all.*
2. **Testora, Mokav (Python, 2025-26)**, SemaDiff, PatchGuru — LLM-based change-behaviour judgement; reviewers in 2026 will ask why not compared (answer: different information, different oracle; classes D).
3. **Xie & Notkin value/path spectra and Harrold/Reps spectra** — the direct prior art for output-free version comparison; the repo cites none of Xie & Notkin's TSE paper in its comparison tables beyond metadata. Full text must be read before any "differs from value spectra" sentence is written.
4. **Software birthmarks** (Myles & Collberg, Wang, Schuler) and **DyCLINK / code relatives** — prior art for call-sequence k-grams and name-invariant behaviour signatures.
5. **K&A 2019 full text** — unread; any sentence about what K&A "do not do" is unsafe. Contact the authors (Kessel, Atkinson; MADOC contact) or obtain via institutional access.
6. **SLACC and other cross-language dynamic clone work** — contradicts any cross-language "first".
7. **Benchmark-validity literature beyond clone detection**: JIT defect prediction (change-size/churn baselines; I verified only the titles of Kamei 2013 and Nagappan–Ball 2005), mutant-size/subsumption studies, program-repair patch-size studies, metamorphic-testing literature, data-leakage/duplication (Allamanis 2019). The "edit-size confound is new" claim is exposed here.
8. **Equivalent-mutant detection via LLMs** (Tandon et al. 2026, B64; EquiBench) — reviewers may ask whether "equivalent" labels are sound; SBG's labels are *sample-equivalent* only.
9. **Statistical-methodology precedents** in SE (cluster bootstrap, multiple-comparison control) — not searched by A1; not a contribution but needs references if described as a method.
10. **Possible name collision / term "genome"**: bounded OpenAlex search found nothing in SE; not exhaustive.
11. **DBLP/Google-Scholar-level coverage**: DBLP rate-limited after ~14 queries; Semantic Scholar rate-limited; Google Scholar not queried (blocked for scripts). Systematic gaps are therefore possible for 2024-26 preprints not yet in OpenAlex.

---

## G. WHAT TO CITE, AND REVIEWER-RISK LIST

### G.1 Minimum "what to cite" (verified works; ID → role)

| Role | Cite |
|---|---|
| Behaviour sampling / I-O equivalence | Podgurski & Pierce 1992/93 (B02/B03); **Kessel & Atkinson 2019 (B01, abstract-level statements only)**; Jiang & Su 2009 (B42); Elva & Leavens 2012 (B43); SLACC (B46) |
| Differential/regression behaviour comparison | Evans & Savoia 2007 (B06); BERT (B05); **Xie & Notkin 2005 (B04)**; Harrold (B11/B12); Reps (B10); DCI (B17); Collector-Sahab (B18) |
| Same-task recent competitors | **ChangeGuard (B24)**, Testora (B25), Mokav (B26), SemaDiff (B28), PatchGuru (B29), Kessel FSE 2026 (B89) |
| Execution traces in learned models | TRACED (B34), CodeExecutor (B35), NExT (B36), Wang–Singh–Su (B37), Wang–Su (B38) |
| Birthmarks / dynamic similarity | Myles & Collberg (B48/B49), Wang 2009 (B50), Schuler 2007 (B51), Code relatives (B44) |
| Symbolic equivalence (contrast) | ARDiff (B52; **FSE 2020**), SymDiff (B53), Regression verification (B54), DiSE (B56), Shadow SE (B57), Person DSE (B09) |
| LLM equivalence benchmarks | EquiBench (B62; EMNLP 2025), CETBench (B63) |
| Benchmark validity / shortcuts | Yu 2022 (B65), Krinke & Ragkhitwetsagul 2025 (B66), Allamanis 2019 (B75), Fu & Menzies 2017 (B72), Just 2014 (B67), Papadakis TCE (B69), Ojdanić 2023 (B68) |
| Real-bug benchmarks | BugsInPy (B80), QuixBugs (B81; correct authors), Defects4J (B82) |

### G.2 Reviewer-risk list (ordered by likely severity)

| # | Risk | Why | Mitigation (from literature side only) |
|---|---|---|---|
| R1 | "ChangeGuard already does this in Python" | verified same task/language, 2025 | position: output-free vs output-reading; report AUROC + edit-size control which ChangeGuard lacks; do NOT claim first |
| R2 | "Output-free" is not really output-free | locals' `repr` includes results (tracer L366-372) | ablate: remove/obfuscate local snapshots at return events; report AUROC without state genome |
| R3 | Label tautology / circular validation | label defined by 11 sampled outputs; EQUIVALENT = sample-equivalent only | use independent inputs for labels vs for baselines; state "sample-equivalence" explicitly; cite EquiBench for all-input contrast |
| R4 | K&A not read | any K&A comparison sentence is unverifiable | obtain full text via authors/institution; until then cite only the abstract-level facts |
| R5 | Value spectra (Xie & Notkin) overlap with state genome | internal-value version-comparison since 2005 | read B04 full text; frame state genome as abstraction/ranking variant |
| R6 | Same-author, 19-program benchmark; real-bug transfer fails (0.497/0.444 per repo) | external validity | disclose; do not claim generality (repo already does) |
| R7 | "Fixed weights" look ad hoc | 0.50/0.25/0.25, inner weights | show sensitivity analysis / no-tuning-on-test statement (other agents) |
| R8 | Benchmark-confound novelty overclaim | JIT-defect size baselines, Yu 2022, Krinke 2025 | cite and phrase as "we show this specific confound in behaviour-change benchmarks" without "first" |
| R9 | Stale design docs contradict code | `docs/research` describes different 8-dimension design | do not cite `docs/research` as the method description |
| R10 | Preprint-only citations of 2026 work (SemaDiff, Impact Is Not Invalidation, NumericalDiff, FEAgent) | unreviewed | mark as preprints; keep to peripheral discussion |

---

## H. KESSEL & ATKINSON — ACCESS LOG AND WHAT CAN/CANNOT BE SAID

| Attempt | Result |
|---|---|
| Crossref (10.1109/SCAM.2019.00030) | metadata OK (SCAM 2019, pp. 193–203); only link = IEEE similarity-checking URL (not readable) |
| IEEE Xplore doc 8930875 | paywalled; abstract visible only |
| Unpaywall API | `is_oa=false`, `oa_status=closed`, no `oa_locations` (`openalex/unpaywall_kessel_atkinson.json`) |
| OpenAlex / Semantic Scholar | closed access; 7 (OpenAlex) / 10 (S2) citers; 36 references resolved (`openalex/kessel_atkinson_refs_resolved.json`) |
| MADOC (Mannheim) record 53324, via headed browser to pass the Anubis gate | metadata only; **no PDF attached** |
| CORE search | HTTP 403 for scripts |
| Author pages / guessed PDF URLs | 404 |
| Open adjacent copies obtained | Kessel PhD thesis 2023 (MADOC 64107), JSS 2024 ×2 (CC-BY), FSE 2026 vision paper |
| arXiv | no arXiv version of the SCAM paper |

**Resulting access level: ABSTRACT-ONLY.** Abstract-level facts I can state: K&A study behaviour sampling for functional-equivalence judgement; an earlier experiment suggested 4 random tests give ≈85 % recognition of non-equivalence; their larger study finds ≥39 random tests needed, and far fewer when tests are coverage-based. Their reference list (36 items) contains Podgurski & Pierce, Code Conjurer, CodeGenie, Reiss, Carzaniga's cross-checking oracles, Stolee & Elbaum, EvoSuite, Barr et al.; I did **not** see Xie & Notkin/BERT among them in the resolved list. Everything else about the SCAM protocol (datasets, labels, metrics, input generation) is **UNVERIFIED**. Framework-level information (response-value matrices, output-string distances, formal-equivalence dismissal) comes from the author's later thesis and is *not* evidence about the SCAM study's evaluation.

**Continuation commands (if access is obtained):**
`python3 PKG/results/raw/literature/pdf2txt.py <kessel_atkinson.pdf> PKG/results/raw/literature/text/kessel_atkinson_scam2019.txt` then read §III-V for: stimulus generation, ground truth for "non-equivalent", metric definition, whether any ranking/AUROC is reported, whether baselines include formal verification.

---

## I. NEWER WORK (2023-2026) FOUND VIA FORWARD CITATIONS AND KEYWORD SEARCHES

Forward-citation counts (OpenAlex `cites:`; files `openalex/fwd_*.json`): Xie & Notkin 61; BERT 97; Evans & Savoia 37; DCI 13; TRACED 55; ChangeGuard 12; Sumner & Zhang 2013 28; Jiang & Su 2009 174; EquiBench 31; K&A 7 (S2: 10).

| Work (ID) | Why it matters to SBG | Access |
|---|---|---|
| ChangeGuard, FSE 2025 (B24) | same task, Python, execution-based | FT |
| Testora, ICSE 2026 (B25); PatchGuru 2026 (B29); SemaDiff 2026 (B28); Mokav JSS 2025 (B26); ProbeGen 2025 (B27) | LLM-driven behavioural-change/equivalence judgement | FT / FTp / AB |
| Kessel FSE 2026 (B89) | versioned run-time behaviour + behavioural fingerprints; same research group as K&A | FT |
| NumericalDiff 2026-11 (B32) | trace alignment independent of variable names; value-based | AB |
| Collector-Sahab TSE 2023 (B18); Revealing Regressions 2026 (B19); Responsibility in Context ICSE 2023 (B20) | runtime-state differences between versions | AB |
| TraceJIT SANER 2024 (B21); BCaLLM 2026 (B23) | behavioural-change impact / Python breaking-change detection | AB |
| EquiBench EMNLP 2025 (B62), CETBench ACL-Findings 2026 (B63), Tandon et al. 2026 (B64) | equivalence benchmarks / label soundness | FT / AB |
| Hybrid Equivalence/Non-Equivalence Testing ICST 2025 (B60); Unified & Split SE TOSEM 2025 (B61); Semantic-conflict detection JSS 2024 (B22) | symbolic/hybrid equivalence and semantic-conflict detection | AB |
| "Impact Is Not Invalidation" 2026-09 (B30); FEAgent 2026-10 (B31) | LLM behaviour-preservation judgement; surrogate execution | AB |

Keyword searches run (OpenAlex, from-year 2018 unless noted): "behavioral change detection execution traces program versions"; "semantic equivalence checking dynamic execution traces Python programs"; "regression detection execution trace similarity"; "semantic diff dynamic analysis behavioral difference two program versions"; "differential testing LLM program equivalence non-equivalence detection"; "behavioral fingerprint program version execution profile comparison"; "software behavior genome" (2005+); "behavioral genome program execution" (2005+); "program genome software DNA similarity" (2005+); "edit size confound code change classification trivial baseline"; "execution trace abstract state transition graph program comparison" (2012+). **No result matched SBG's combination (call/temporal/state genome + fixed-weight distance + edit-size-controlled benchmark).** This is a bounded negative result (§F item 11).

---

## J. CLAIMS SUPPORTED / UNSUPPORTED / CONTRADICTED (literature side)

| Claim (source) | Status |
|---|---|
| "SBG is first/novel/unique" (docs/research, archive) | **UNSUPPORTED** (and CONTRADICTED for the specific variants in §E.1) |
| "Dynamic comparison for equivalence/change is not new" (FINAL_NOVELTY_POSITION, NOVELTY_CLAIM_TO_EVIDENCE) | **SUPPORTED** (behaviour sampling 1992 … ChangeGuard 2025) |
| Strongest contribution = evaluation methodology | **PARTLY SUPPORTED**: methodology is INCREMENTAL; "first" unverifiable |
| K&A properties asserted in RELATED_WORK_NOVELTY_AUDIT | **UNSUPPORTED** (full text unread) |
| "SBG representation is weak-novelty" (audit I.3) | **SUPPORTED** (§D 1-8) |
| "Output-free" as differentiator | **SUPPORTED as contrast with output-reading approaches; CONTRADICTED as novelty** (value/path spectra, birthmarks); strictness **UNTESTED** (V6) |
| "All citations are to real published works" (PRIOR_ART_MATRIX) | **CONTRADICTED** (§E.2) |
| Task prompt: "ARDiff ICSE 2020"; "Sumner ICST 2011" | **CONTRADICTED** by primary records |

---

## K. WHAT FAILED / COULD NOT BE DONE / CONTINUATION COMMANDS

| Item | Why | How to continue |
|---|---|---|
| K&A SCAM 2019 full text | closed; no legitimate open copy | email the authors (Marcus Kessel, Colin Atkinson, Univ. Mannheim) or use institutional IEEE access; then run `pdf2txt.py` (see §H) |
| Full texts of Xie & Notkin 2005, BERT, Evans & Savoia, Person 2008, Sumner & Zhang, Jiang & Su, Podgurski & Pierce, birthmark papers, Just 2014, Yu 2022, Defects4J, BugsInPy | publisher-paywalled/closed; arXiv versions absent (BugsInPy arXiv 2401.15481 text extracted but not read in depth) | institutional access; author homepages (guessed URLs failed); then update access levels in `build_bib.py` and re-run `python3 PKG/results/raw/literature/build_bib.py` |
| DBLP API for scripts | Anubis proof-of-work (HTTP 202) — used headed browser; rate-limited after ~14 queries | re-run remaining title queries (SABER, Tamada 2004 dynamic birthmark, Su 2016, Ding) later |
| Semantic Scholar API | intermittent HTTP 429 | retry with longer sleeps; `python3 s2_meta.py DOI:...` |
| Google Scholar / Scopus / Web of Science | not queried (blocked/paywalled) | manual check by the manuscript author for forward citations of K&A/ChangeGuard |
| SE-specific statistical-methodology precedents; JIT-defect "size baseline" evidence; mutant-size confounds | out of A1 time-box | targeted search + read Kamei 2013, Nagappan & Ball 2005 full text |
| Experimental testing of SBG "output-free" leakage (V6) | out of A1 scope (literature agent; repo read-only) | ablation by the experimental agents |
| Code availability for K&A/LASSO, BERT, Xie & Notkin, DyCLINK | not verified | check LASSO/GitHub/author pages |
| EquiBench / Wang–Singh–Su / NExT / CodeNet venue strings | primary records lacked venue | confirm via ACL Anthology / ICLR / ICML proceedings |

*Registered experiments, outputs and exclusions are mirrored in `PKG/logs/registry/A1_lit.jsonl`.*
