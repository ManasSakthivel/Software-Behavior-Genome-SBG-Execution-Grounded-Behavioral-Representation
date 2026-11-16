# 02 — Scientific Contribution and Positioning (WP-F, FIRST PASS)

Status: **first pass on existing evidence only.** A4 (head-to-head) and A5 (ablation, return-value, external) results did not exist when this was written and are not used. No GO / NO-GO is issued here.
Date: 2026-11-14. Author role: WP-F adversarial reviewer. PKG = `IEEE_ACCESS_PRE_SUBMISSION`.
Supporting independent memos (same directory, `_reviewer_notes/`): `REVIEWER_A_NOVELTY.md`, `REVIEWER_B_STATISTICS.md`, `REVIEWER_C_METHODOLOGY.md`, `REVIEWER_D_POSITIONING.md`.

## 0. Evidence-level vocabulary (used throughout)

| Tag | Meaning |
|---|---|
| **FULL-TEXT** | The repo's own record (`03`, §B bibliography) says the full paper was read. Usually the arXiv version. |
| **ABSTRACT-ONLY** | Only an abstract was read. No claim about methods, labels, metrics or baselines can rest on it. |
| **METADATA-ONLY** | Only a bibliographic record. |
| **DIRECT-EXPERIMENT** | A number produced by running code on data, in this repo's audits (A2/A3) or by me. |
| **QUALITATIVE** | A reasoned comparison. No experiment exists. |
| **UNVERIFIED** | Not supportable from any file I could read. |

Literature depth for the 96 works in `03` (Reviewer A recounted `results/raw/literature/bibliography_verified.json`; matches `03` L79): **8 full-text, 10 partial full-text, 66 abstract-only, 12 metadata-only.** So 81% of the corpus is abstract- or metadata-only. The works closest to SBG's *representation* (value and path spectra, birthmarks, DyCLINK, ADABU, Daikon; bibliography group A) have **zero** full-text reads. The works closest to its *task* (ChangeGuard, Testora, DCI) were read in full. The novelty verdict on the representation is therefore the least well supported part of the literature analysis.

**No direct experimental comparison with any competitor exists.** Everything said below about prior work is FULL-TEXT, ABSTRACT-ONLY or QUALITATIVE. Head-to-head benchmarking (A4) is BLOCKED/in progress and nothing from it is citable. A dev-split observation in `CURRENT_EXECUTION_STATUS.md` §3 is explicitly marked non-citable, and I did not use it.

## 1. Research question and hypotheses — as they stand

### 1.1 What the project asks
The repo's own best framing (`FINAL_MANUSCRIPT_BLUEPRINT`, relayed by Reviewer D) is: *how much does a trace-derived behavioural representation add once edit size is controlled and a strong execution-statistics baseline is present?* That is a meaningful question. The evidence answers it only partly.

### 1.2 Hypothesis formulation problems
- The protocol files do **not** define H1–H6. Their definitions live in `SBG/artifacts/final/FREEZE_V10.json` (`hypotheses`) and `V9_VAL_EVALUATION.json`. A reviewer reading `PKG/configs/PROTOCOL.md` cannot see them. [Reviewer B §1]
- **H1** (AUROC of V5 > 0.5) is a near-trivial bar. The label is "output differs on the 11 protocol inputs", and the V10 generator keeps a CHANGED pair only if `oracle(mutant) != oracle(base)` on at least one input. I confirmed this in `benchmark/scripts/generate_v10_independent.py:136-137,154`. Above-chance discrimination of a label that was selected for observability is expected, not informative.
- **H2/H3** compare against *pooled* edit size. Inside matched sets the CHANGED variant has the larger edit in 292/319 sets (292 of 294 non-tied), and edit-size matched-set concordance (0.955) is not distinguishable from V5's (0.931) on V10 (difference +0.0235, CI [−0.011, +0.062]). On V9c-val edit concordance is higher (0.924 vs 0.806; paired CI unreported). "Size-matched" is therefore true only of the pooled distribution. [Reviewer B §4]
- **H4** (adding V5 to edit + execution statistics) is the only hypothesis that bears on contribution. It is inconclusive (§3).
- **H5/H6** are labelled EXPERIMENTAL V6 contrasts and add nothing to the positioning (§3).

## 2. What SBG demonstrates, and what it does not

### 2.1 Demonstrated (within stated limits)
| # | Claim | Evidence | Level |
|---|---|---|---|
| D1 | Scores reproduce bit-exactly (522 quantities, max \|Δ\| = 0) on CPython 3.13.5 | `07`, `09` | DIRECT-EXPERIMENT (A2/A3) |
| D2 | V5 AUROC 0.8968 [0.8629, 0.9216] on V10 (638 pairs, 19 programs), vs forward edit-size 0.616 | `07` §2 | DIRECT-EXPERIMENT |
| D3 | On a transformation-family benchmark, edit size alone can solve the task (V8-test: reversed edit 0.876 vs SBG 0.694) | `07` §2, `SBG/STATUS.md` | DIRECT-EXPERIMENT |
| D4 | V10 labels are clean (319/319 CHANGED differ, 322/322 EQUIVALENT identical on the protocol inputs) | `07` §4.5 | DIRECT-EXPERIMENT, but see label tautology |
| D5 | A characterised blind spot: value-only (SC-6) mutations | `V10_INDEPENDENT_EVALUATION.json:699-703` | DIRECT-EXPERIMENT |

### 2.2 Not demonstrated
| # | Not shown | Why |
|---|---|---|
| N1 | Gain over edit + execution statistics | H4 inconclusive, MDE ≈ 0.10 |
| N2 | Real-bug transfer | BugsInPy 0.497/0.410, QuixBugs 0.444/0.388; CIs span 0.5 or sit just below it; most positives score exactly 0 |
| N3 | Independence of V10 | Same generator, transformation families, oracle and author as development; 16/19 programs > 0.10 token-Jaccard to a V8/V9c program (max 0.225); freeze is self-attested |
| N4 | Genuine "output-free" behaviour | The tracer snapshots `repr(frame.f_locals)` at every event including `return` (`sbg/extraction/dynamic/tracer.py:364-384`, which I read). Leakage through locals is untested |
| N5 | Superiority or inferiority to any output-reading method | Not run on an independent battery; same-input comparison is label-tautological |
| N6 | Cross-language capability | Python `sys.settrace` only |
| N7 | Practical value | Synthetic pairs, 50% prevalence by construction, no human or real-refactoring evidence |
| N8 | Version-robustness | Scores shift (+0.028 pooled AUROC) on CPython 3.9; this is larger than H4 and H5 and comparable to state − V5 |

## 3. The five critical findings

### 3.1 H4 is inconclusive — but not a clean null
- V10: ΔAUROC +0.0063, 95% CI [−0.069, +0.068], p = 0.81. V9c-val: +0.021 [−0.005, +0.048], p = 0.117. [`07`; EXP-A3-003]
- MDE ≈ 0.100 on V10 (Reviewer B re-derived 2.8 × 0.0357 = 0.100). Equivalence margin the data support ≈ ±0.06. Power at a true Δ of 0.02 is 8.6%.
- Effective n for H4 is about 19 programs (design effect ≈ 5, ≈ 128 pair-equivalents), not 638.
- ΔAUPRC is positive in both sets (V10 +0.050 [+0.004, +0.092], uncorrected p = 0.036; V9c-val +0.072 [+0.042, +0.106]). It was not pre-declared, so it is hypothesis-generating only.
- H4 compares against a combiner trained on V9c-train. V10 M_EX+V5 (0.797) is below V5 alone (0.897), so H4 partly measures combiner transfer failure. The in-distribution LOPO refit of execution statistics reaches 0.885, against V5 0.897 (+0.012, not significant).
- **Defensible wording:** "We could not determine whether SBG adds AUROC beyond edit size plus execution statistics. The study can detect only effects ≥ ~0.10 and cannot exclude gains or losses of ~0.07." **Not** "no incremental value" and **not** "adds value beyond execution statistics". "Null result" overstates it, because the AUPRC signal points the other way.

### 3.2 State genome 0.917 vs full V5 0.8968
- V10: `sbg_state` 0.9171 [0.893, 0.938] vs `sbg_v5` 0.8968. Difference +0.020; program-cluster CI approximately [+0.007, +0.039]; uncorrected p ≈ 0.002. I confirmed the state rows in `EXP-A3-003_v10_test_resampling_unit_comparison.csv`.
- It is **not** in the pre-declared Holm family and not in the repo's own result JSON. Only A3's "(extra)" contrast contains it. It was found by post-hoc comparison among V3 / temporal / state / V5 / V6 on V10.
- It does **not** replicate on V9c-val (+0.011, CI [−0.024, +0.040]). Per-program: V5 < state in 13, > in 5, 1 tie (sign p = 0.096). Leave-one-program-out Δ stays +0.017…+0.024 [Reviewer B, derived].
- The 3.9-vs-3.13 interpreter shift (≈ 0.03) is the same size as this difference.
- Mechanistic concern: the state genome is the component that ingests value snapshots, and the locals channel is untested (N4). A bare-local `return` appears in 10 of the 19 V10 programs by a crude grep (Reviewer C, [MY-COMPUTATION], unreplicated by me). The hypothesis that the state genome's lead comes from locals at return events is **untested**. It is consistent with the data but not demonstrated.
- **Positioning consequence:** the fixed-weight composite is not shown to be better than one of its own components. Ablation (A5E) is required before "representation" can be a claim.

### 3.3 BugsInPy and QuixBugs at or below chance
- Point estimates 0.38–0.50 across six configurations. 95% CIs span 0.29–0.60. The "0.497" and "0.444" figures need a post-hoc SP-2 exclusion (7/40 invalid negatives). All-pairs values are 0.41–0.42 and 0.38–0.39. They are different pipelines, not repeat estimates of one quantity.
- Normal-approximation p-values for "below chance" (Reviewer B, derived): roughly .035, .09, .95, .044, .027, .23. So "below chance" is borderline in 3 of 6, absent in the SP-2-excluded numbers, and uncorrected.
- 26/41 BugsInPy and 32/39 QuixBugs real-bug pairs score exactly 0. The result is chiefly "SBG is blind to these bugs on the protocol inputs", not evidence of anti-correlation.
- The negatives are synthetic SP rewrites of the fixed program, not independent real version pairs.
- A committed declared-inputs QuixBugs regime (`artifacts/final/pairs_quixbugs_declared_output_free_v7.jsonl`) shows 8/24 evaluated real-bug pairs at exactly 0 despite differing outputs (pooled AUROC ~0.70, not cluster-bootstrapped; 16 of 40 pairs excluded; Reviewer C [MY-COMPUTATION], I did not re-run it). It is not reported in the existing audit.
- **Wording:** "no evidence that SBG discriminates real bugs from equivalent rewrites under the frozen protocol". Not "SBG performs below chance".

### 3.4 SC-6: 17/23 changed pairs invisible
- Verified source: `V10_INDEPENDENT_EVALUATION.json:699-703` gives `changed_zero_rate_by_sc_family["SC-6"] = {n: 23, sbg_v5: 0.7391}`. 0.7391 = 17/23. Reviewer B recounted 17/23 from `configs/populations/v10_test.json`; exact 95% CI ≈ [0.52, 0.90]; 23 pairs from 18 programs.
- "Invisible" means `sbg_v5 == 0.0` exactly, with V3, temporal and state all zero. It does not mean undetectable in principle.
- Reviewer C's trace comparison (unreplicated by me): for all 17 the (event type, function, line) streams equal the matched EQUIVALENT partner's. Raw locals are identical in 7/17 and collapsed by the abstraction in the other 10. Returns differ on 3–11 of 11 inputs.
- Cause: a protocol choice (SAFEGUARD-2, return values unread), not a tracer limit. `settrace` hands the return value to the callback (`tracer.py:336`).
- **Central tension for the paper:** reading return values would make SBG the label oracle (circular on this benchmark). Not reading them makes it blind to value-only edits. Either the title/abstract must carry this limitation, or SBG's scope must be stated as "structure-visible behaviour change". The value-only class is also where output differential testing, the cheapest practitioner tool, is strongest.

### 3.5 Validation programs may not be independent of the development procedure
Treat this as **probable** rather than possible, on the repo's own record:
- All 19 V10 programs were first rejected from V8 by the project's own novelty rule (token-Jaccard 0.101–0.146 > 0.10 against a corpus sibling), then repackaged as held-out (`generate_v10_independent.py:5-9`; `FREEZE_V10.json:44`). Reviewer C verified this in file.
- V10 reuses the V8/V9 `SC_TYPES`/`SP_TYPES`, composer, mutator, transformer and oracle. Only the base program differs. Thresholds and weights were fixed on the same transformation families.
- Corpus authorship is unnamed (`provenance: authored`, `license: original`), 121 programs were added in one commit whose message says "NOT research-ready", and AI co-author trailers exist on three commits (`01` §1). Who or what wrote the programs is UNVERIFIED. If an LLM that also designed SBG wrote them, shared-generator bias applies and disclosure is required.
- The benchmark was redesigned after negative results (V8 test: reversed edit beat SBG) in the sequence V8 → V9 → V10, over about two days. The V10 freeze discloses that edit AUROC 0.616 and mean edit sizes were inspected before the freeze. Whether V9c-val scores had been opened before V10 generation is UNVERIFIED.
- "Frozen before scoring" for V10 rests on self-reported `written_at` in a single commit (c5bc130).
- The README concedes "same author and generation procedure … not independently authored software" (`README.md:33-34`). The manuscript should say "held-out programs", never "independent".

## 4. Novelty

### 4.1 Closest prior work, Kessel & Atkinson (2019)
- **Evidence level: ABSTRACT-ONLY.** IEEE is paywalled, Unpaywall `is_oa=false`, MADOC record 53324 has no PDF, and there is no arXiv copy. [`03` V2, §H]
- What the abstract supports: a behaviour-sampling study of functional-equivalence judgement (about 4 random tests recognised ~85% of non-equivalence in an earlier experiment; the larger study needed ≥ 39 random tests, far fewer with coverage-based generation).
- What the repo read instead: Kessel's 2023 PhD thesis (partial), two JSS-2024 papers (partial), an FSE-2026 vision paper (full). These are framework-level context, **not** the SCAM 2019 protocol. The `03` table mixes thesis details into the K&A row, which invites misreading.
- **Therefore no statement of the form "K&A do not report AUROC / use manual labels / lack a size baseline / compare against formal verification" is supportable.** Two paper-evidence files (`RELATED_WORK_NOVELTY_AUDIT.md:52`, `NOVELTY_CLAIM_TO_EVIDENCE.md:52-56`) still carry the wrong DOI `10.1109/SCAM.2019.00019` (that is Harrand et al.; the correct DOI is `.00030`) and, per `03`, assert K&A properties. Reviewer A confirmed the DOI in both files.
- What can be said: K&A are prior art for "compare dynamic behaviour of two implementations to judge equivalence", an output/response-sampling family member. [ABSTRACT-ONLY + QUALITATIVE]
- Same research group: Kessel (FSE 2026, full-text read) proposes versioned run-time behaviour with behavioural fingerprints (I/O values, call sequences). That contradicts any "longitudinal behavioural genome" claim.

### 4.2 Closest same-task competitors
| Work | Depth | Note |
|---|---|---|
| ChangeGuard (FSE 2025) | FULL-TEXT (arXiv v2) | Python function-pair, execution-based, 224 annotated commits, P 77.1% / R 69.5%. **No mention anywhere in `SBG/`** (my grep: no match). Not directly comparable (needs LExecutor neural injection; class D). |
| Testora (ICSE 2026) | FULL-TEXT (arXiv v3) | Uses PR natural language SBG never sees. |
| DCI | FULL-TEXT | Repo docs still say "abstract and introduction read". |
| SemaDiff | Partial full-text per `03`; FULL-TEXT per `EARLY_COMPETITOR_BRIEF.md` | **Records disagree.** Unreviewed 2026 preprint. |
| PatchGuru | ABSTRACT-ONLY per `03`; FULL-TEXT per the brief | **Records disagree.** |
| Xie & Notkin (value spectra, 2005) | ABSTRACT-ONLY | Closest prior art for the state genome and "output-free" idea. |

### 4.3 Is SBG novel, or a combination of existing execution-derived features?
Feature by feature (Reviewer A; `03` §D):
| SBG component | Verdict | Evidence level |
|---|---|---|
| Call-frequency topology, coverage size | ESTABLISHED (path/branch/profile spectra, birthmarks) | ABSTRACT-ONLY |
| Call-order bigrams | ESTABLISHED (k-gram, API-call, system-call birthmarks, DyCLINK) | ABSTRACT-ONLY |
| Exception structure | ESTABLISHED / minor variant (not exhaustively searched) | ChangeGuard FULL-TEXT; others ABSTRACT-ONLY |
| Rename-invariance by first-call anonymisation | ESTABLISHED (implementation detail) | ABSTRACT-ONLY |
| Fixed-weight L1/Jaccard sum | ESTABLISHED; hand-set weights invite a "tuned?" challenge | UNVERIFIED |
| Temporal bundle | Weak: no demonstrated gain over execution statistics (LOPO +0.010 n.s.; V10 +0.006) | QUALITATIVE + DIRECT |
| Abstract state-transition genome | **UNRESOLVED OVERLAP** with value spectra (Xie & Notkin), ADABU, Daikon, Collector-Sahab. It is the repo's "strongest piece" and the least cleared against prior art | ABSTRACT-ONLY (B04, B13, B14, B18, B19, B32) |
| CHANGED/EQUIVALENT ranking task | Not novel as a task | Mixed |

**Assessment:** on the evidence available, SBG is **primarily a recombination of established execution-derived features** with a small, unproven novelty risk concentrated in the state genome. A reviewer holding Xie & Notkin would likely see the state genome as a re-abstraction of value spectra unless the paper shows otherwise. This is a QUALITATIVE judgement from abstract-level reading. It could move in either direction once Xie & Notkin, ADABU, and Kessel & Atkinson are read in full. I do not claim it is proven.

### 4.4 Claims on novelty
- **Indefensible:** any "first / novel / unique"; "cross-language"; "versioned/longitudinal genome"; any "unlike K&A…"; unqualified "output-free"; "all citations are real" (≥ 8 wrong citations, including a non-existent "Sumner ICST 2011").
- **Weak:** representation as an algorithmic contribution; temporal bundle; the task framing.
- **Defensible only in bounded form (INCREMENTAL, "in the literature found"):** edit-size/label-confound diagnosis with a composed benchmark; oracle-checked labels (a rigour feature equal to the mutation-kill criterion); honest strong-baseline null. "No precedent" is UNVERIFIED outside clone-detection benchmarks. JIT defect-prediction size baselines (Kamei, Nagappan) were never verified.
- Coverage gaps: `invariant_diffs.txt`, `envtrace.txt`, `output_equiv_oracles_miss.txt` were downloaded but never entered the bibliography. The search was bounded (no Google Scholar, DBLP rate-limited). The corpus is recency-heavy (21/96 from 2025–26).

## 5. Internal validity, external validity, generalisation

**Internal (Reviewer C):**
- *Label tautology (MAJOR; FATAL for same-input output-reading comparisons).* Any output-reading baseline on the 11 protocol inputs scores AUROC 1.0 by construction. A fair comparison needs labels from battery A and competitors on battery B.
- *"Output-free" locals channel (MAJOR; potentially FATAL for the word).* Untested.
- *V10 independence (MAJOR)* — §3.5.
- *V9c-val labels (MAJOR).* 16/216 EQUIVALENT pairs change output; 67/216 (31%) CHANGED are unobservable. The repo's static audit reports 0 unobservable pairs, which is contradicted by dynamic evidence. The same defect pattern exists in V9c-train, where thresholds and the combiner were fitted. The clean-subset gain (0.751 → 0.849) selects on output and is an upper bound.
- *Pseudo-replication.* 84 AST-identical groups; V5 0.8968 → 0.8843 [0.846, 0.912] de-duplicated.
- *AUROC depends on benchmark composition (Reviewer C, own computation, exploratory).* 63.6% of EQUIVALENT V10 pairs score exactly 0 (rename/format families). V5 within-family: SP-1/4/6 0.98–1.00, SP-2 0.836 (edit 0.875), SP-5 0.774, SP-8 extract-method 0.611 (edit 0.606; n = 18). Hard families {3,5,8,11,12}: 0.836 vs easy {1,2,4,6}: 0.952. The 0.897 is carried partly by rename/format invariance, a property any normalised trace comparison has. Many cells are small.
- *Statistics.* Percentile bootstrap with 19 clusters, coverage untested; seed-sensitivity ±0.002–0.004; p = 0.001 is a floor.

**External:** synthetic single-file Python exercises; 14 mechanical mutation operators; scope selection removes stateful class-based programs; real-bug pairs at or near chance; no human study.

**Generalisation:** across programs — some support (LOPO V5 range 0.892–0.906); across transformation families, authors/styles, input batteries, interpreters, languages, tasks — none or negative.

**Practical significance:** frozen threshold (7.955e-05, the smallest non-zero step) flags 65.4% of pairs (sens 0.944, FPR 0.364). The decisive practitioner baseline, output differential testing on the same inputs, was not run, and cannot be fairly run on this benchmark. The repo's own proposed workflow says "run a cheap output comparison in parallel". Cheap execution statistics from the same traces are about as good (LOPO +0.012 n.s.).

**Reproducibility:** bit-exact on CPython 3.13.x only (3.9: 3,837/93,942 orderings flip, pooled AUROC +0.028); `FREEZE_V10.variants_tree_sha256` unreproducible; the "35/35 trace check" is mostly a string check; headline evaluation path undocumented in README/Makefile; GPL-3.0 ansible code (18 units) inside an MIT repo; `math_gray_code` trace failure uninvestigated. Strong points: 807 tests pass, 10/10 consistency checks, 533/536 hashes match.

## 6. Candidate contribution statements, ranked by defensibility

| Rank | Positioning | Status |
|---|---|---|
| 1 | **Evaluation-methodology contribution:** trace-based change scoring evaluated with edit-size diagnosis, oracle-checked labels, program-cluster statistics and a power analysis; plus the H4 "could not determine" result | Defensible, INCREMENTAL novelty, "in the literature found" only. Risk: the confound is partly self-inflicted (a benchmark the authors built and then corrected). |
| 2 | **Negative/null result (IEEE Access "Negative Result" type)** | Defensible only if H4 is stated as *inconclusive* (not "no value"), with equivalence bounds, and if real-bug and SC-6 limits are included. Needs a rigorous, meaningful question. |
| 3 | Exploratory triage/review-effort observation | Supporting only (post-hoc, 50% prevalence by construction). |
| 4 | "Validated representation" | **Not defensible** on current evidence. |
| 5 | "Bug/regression detector" | **Contradicted** by external results. |
| 6 | "Cross-language" | **Untestable** now. |
| 7 | "Output-free genome beats output-reading differential testing" | **Untested**, and structurally untestable on same-input labels. |

Titles/abstract terms to avoid: novel, first, framework, validated, detects bugs, independent evaluation, size-matched/controlled (unqualified), output-free (unqualified), semantic equivalence, cross-language, formal pseudometric, practical/productivity, state of the art. "Genome" implies a longitudinal/biological analogy that Kessel (FSE 2026) already occupies.

**Current best research question:** *Once edit size and cheap execution statistics are controlled, does a trace-derived structural representation add measurable ability to rank behaviour-changing over behaviour-preserving edits, and how much of the apparent gain is explained by benchmark construction?* **Current best answer from existing evidence:** it outperforms pooled edit size on same-author synthetic pairs; whether it adds anything beyond execution statistics is unresolved; there is no real-bug transfer; and the leakage and value-only limits are unresolved.

## 7. Spot checks I made myself (versus relying on sub-reviewers)
| Check | Result |
|---|---|
| `tracer.py:364-384` snapshots `repr(f_locals)` for every traced event incl. `return`; harness frames skipped | Confirmed by reading the file |
| `generate_v10_independent.py:136-137,154` accept rule (EQ: oracle equal; CH: mutant oracle ≠ base and composed oracle = mutant oracle) | Confirmed |
| `V10_INDEPENDENT_EVALUATION.json` SC-6 `0.7391` | Confirmed (lines 699-702) |
| `sbg_state` rows in EXP-A3-003 resampling CSV (cluster Δ CI lower ≈ +0.0069, upper ≈ +0.0387) | Confirmed |
| ChangeGuard/Testora absent from `SBG/` | Confirmed (grep, no matches) |
| K&A abstract-only; DOI errors | Confirmed in `03` (V2, B01, B93, L291) |
| Items **not** re-run by me: Reviewer C's zero-score, SP-family AUROCs, locals-grep counts, declared-inputs QuixBugs numbers; Reviewer B's design-effect and jackknife figures | Reviewer-derived; flagged as such |

## 8. Pass-2 plan
When A4 (A4C/A4D) and A5 (E/F/G) have finished, revisit this file against the actual results. Specifically: ablation/leakage (§3.2, §3.4, N4), independent-battery output-reading baseline (N5), Python-version effect (N8), external pre-registered run (§3.3). Do not update from non-citable dev-split observations.
