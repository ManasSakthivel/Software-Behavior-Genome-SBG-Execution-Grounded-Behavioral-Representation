# 10A — Adversarial Review (Reviewer 2), Existing Evidence Only

**Status:** first pass. No GO / CONDITIONAL GO / NO-GO decision is issued. A4 (head-to-head) and A5 (ablation, return-value, external) were not complete and are not used. Every verdict below can move once they report; see §6 and `WPF_OPEN_REVIEW_QUESTIONS.md`.
**Scope:** SBG repo HEAD `3425693` (read-only), PKG audits `01`, `03`, `07`, `09`, and the four independent reviewer memos in `_reviewer_notes/`.
**Date:** 2026-11-14.

## 0. Method and evidence discipline

Four independent reviewers worked in isolated contexts: **A** novelty, **B** statistical claims, **C** methodological validity, **D** publication positioning. I then re-checked the highest-impact facts myself (§7 of `02_…FIRST_PASS.md`). Every finding is tagged:

- **[FULL-TEXT]** — the repo's literature record says the full paper was read.
- **[ABSTRACT-ONLY]** / **[METADATA-ONLY]** — shallower reading.
- **[DIRECT-EXPERIMENT]** — a number produced by running code on data (A2/A3, or a reviewer's recomputation, flagged as unreplicated).
- **[QUALITATIVE]** — reasoned comparison, no experiment.
- **[UNVERIFIED]** — no file supports it.

Two distinctions the manuscript must keep:
1. **Literature comparison is not experimental comparison.** No competitor was run against SBG on held-out data. Every "SBG vs. prior work" statement today is QUALITATIVE.
2. **Depth of reading differs by paper.** 8 of 96 works were read in full, 10 partially, 66 abstract-only, 12 metadata-only. Prior-art claims inherit the weakest depth involved.

## 1. Reviewer's summary of the submission

SBG is a Python-only, `sys.settrace`-based, output-free (by protocol) representation of program behaviour. It combines call topology, call bigrams, exception structure, temporal features and an abstract state-transition genome. A fixed-weight distance (V5) scores pairs of program versions. Evaluation uses synthetic pairs: mutation operators for CHANGED and rewrites for EQUIVALENT, labelled by an output oracle on 11 synthesised inputs. The headline is AUROC 0.897 on a 19-program held-out set (V10), against 0.616 for edit size. The authors also report an inconclusive incremental-value test (H4), a state component that outscores the composite, at-or-below-chance results on real-bug corpora, and a documented blind spot for value-only edits.

## 2. Overall assessment (not a decision)

The arithmetic is sound: A3 reproduced 522 quantities with max |Δ| = 0, and A2 reproduced the scored files bit-exactly on CPython 3.13.5. The problem is what the numbers measure and what is built on them. As currently evidenced:

- the **novelty** of the representation is weak and partly unresolved;
- the **hypothesis tests that were confirmed (H1–H3) are the least informative**, and the informative one (H4) is inconclusive;
- the **benchmark's labels are tied to the same inputs the method sees**, and its held-out set is not independent of the development procedure;
- the **claims that would make this practically useful** (real bugs, value-only edits, output-free) are untested, negative, or limited;
- the **results are version-specific** to CPython 3.13.x.

A paper that states these plainly could be a sound methods/negative-result contribution. A paper that presents SBG as a validated representation or bug detector would, in my reading, not survive review. That is a statement about the evidence, not a prediction of editorial outcome.

## 3. The ten most serious reviewer objections

Severity: **FATAL** = invalidates a headline claim as currently worded; **MAJOR** = would likely force revision or rejection if unaddressed; **MODERATE** = needs repair or disclosure.

### O1. "The task is label-tautological; the headline measures prediction of a pre-selected output difference." — FATAL for any same-input comparison; MAJOR for the headline
**Objection.** V10 keeps a CHANGED pair only if `oracle(mutant) != oracle(base)` on SBG's own 11 inputs, and an EQUIVALENT pair only if outputs match on all of them (`generate_v10_independent.py:136-137,154`; I read it). An output-reading method on those inputs gets AUROC 1.0 by definition. SBG's 0.897 therefore says only that a trace difference correlates with an output difference that was pre-selected to exist. CHANGED pairs not visible on the 11 inputs are excluded by construction.
**Evidence status.** [DIRECT-EXPERIMENT: A3 confirmed 319/319 and 322/322.] The tautology is by design.
**Evidence required to resolve.**
- A4/A5: output-differential baseline on an **independent** input battery (labels from battery A, competitor on battery B, no overlap with the 11 protocol inputs, verified by A4D), reported as a ceiling and not as a competitor.
- A label-source analysis: how many CHANGED pairs would remain if labelled from a *different* battery (fraction of pairs whose label flips).
- Explicit scoping in the abstract: "predicts observable output change on a fixed battery", not "behavioural equivalence".

### O2. "SBG is not novel: it recombines established execution features, and the one possibly new component overlaps value spectra." — MAJOR
**Objection.** Call frequencies, bigrams, exception structure, rename-invariance and fixed-weight distances are established (path/branch/profile spectra, birthmarks, DyCLINK, ChangeGuard) [ABSTRACT-ONLY for most; ChangeGuard FULL-TEXT]. The temporal bundle shows no gain over execution statistics. The state-transition genome overlaps value spectra (Xie & Notkin 2005), ADABU, Daikon, Collector-Sahab [ABSTRACT-ONLY for all]. The closest same-task competitor, ChangeGuard (FSE'25, Python, P 77.1%/R 69.5% on 224 commits), does not appear anywhere in the SBG repo (I grep-confirmed).
**Evidence status.** The prior-art depth for SBG's own *features* is the shallowest in the corpus: bibliography group A (behaviour sampling, spectra, differential testing, Daikon, ADABU) has **zero** full-text reads. The novelty verdict is therefore uncertain in both directions.
**Evidence required to resolve.**
- Full-text reads of Xie & Notkin 2005, ADABU, Kessel & Atkinson 2019, Invariant Diffs (downloaded but never bibliographed), and one JIT defect-prediction change-size baseline (Kamei/Nagappan).
- A feature-by-feature novelty table with the evidence tag per cell.
- Ablation (A5E) showing which components carry the signal.
- Either drop novelty claims entirely, or restrict them to "evaluation methodology".

### O3. "Kessel & Atkinson (2019), the closest prior work, was never read." — MAJOR (credibility), not decisive on its own
**Objection.** The full text was unobtainable (IEEE paywalled, no open copy). The repo's K&A statements rest on the abstract, the author's 2023 thesis (partial) and two JSS-2024 papers. Two older repo files still carry a wrong DOI and K&A property claims that `03` calls unsupported. A reviewer who knows K&A will test every sentence about it.
**What is and is not known.** [ABSTRACT-ONLY] K&A compare dynamic behaviour for functional-equivalence judgement by sampling tests (about 4 random tests recognised ~85% non-equivalence initially; the larger study needed ≥ 39 random, fewer with coverage-based generation). [UNVERIFIED] their representation, labels, metrics, baselines, datasets and whether they address size confounds. Thesis-level "stimulus-response matrix of serialised responses" [FULL-TEXT partial] describes an output-reading framework, but is not the SCAM study.
**Evidence required to resolve.**
- Obtain the paper (institutional IEEE access or an author request; the A1 notes name the contact route). Re-do the K&A row of `03` §B.
- Until then: strike all "unlike K&A…" sentences; use only "K&A address test-count sufficiency for output-based equivalence judgement (abstract); SBG does not read outputs by protocol".
- Correct the wrong DOI in `RELATED_WORK_NOVELTY_AUDIT.md:52` and `NOVELTY_CLAIM_TO_EVIDENCE.md:52-56`.
- Any K&A-style baseline must be labelled ADAPTED from abstract + thesis.

### O4. "H4 — the only test of incremental value — is inconclusive, and the null framing is also overstated." — MAJOR
**Objection.** V10 ΔAUROC +0.0063, 95% CI [−0.069, +0.068], p = 0.81; V9c-val +0.021 [−0.005, +0.048]. MDE ≈ 0.10 (Reviewer B re-derived it), equivalence margin ≈ ±0.06, power at Δ = 0.02 is 8.6%. Effective sample is about 19 programs (design effect ≈ 5). H4 compares against a combiner trained on V9c-train, so it partly measures combiner transfer failure (V10 M_EX+V5 0.797 < V5 alone 0.897; in-distribution LOPO refit of execution statistics reaches 0.885 vs V5 0.897, +0.012 n.s.). Meanwhile ΔAUPRC is positive in both sets (V10 +0.050 [+0.004, +0.092], uncorrected p = 0.036; V9c-val +0.072). It was not pre-declared and survives Holm only by counting a favourable number of looks.
**Consequence.** Neither "no incremental value" nor "adds value" is supportable. A "null result" paper would be mis-described, because the data are *indeterminate*.
**Evidence required to resolve.**
- Pre-registered power analysis and ≈ 40–60 additional truly held-out programs (the repo's own estimate; ≈ 410 programs for 80% power at Δ = 0.02 on V10).
- In-distribution refit execution-statistics baseline as the primary comparator.
- Equivalence-test (TOST) wording with the ±0.06 margin.
- Component ablation (A5E) to determine what, if anything, V5 adds.

### O5. "The state genome alone beats the full composite, so the distance is not the contribution, and the state genome may read return values through locals." — MAJOR (potentially FATAL for 'output-free')
**Objection.** `sbg_state` AUROC 0.9171 vs `sbg_v5` 0.8968 on V10 (Δ +0.020, program-cluster CI ≈ [+0.007, +0.039], p ≈ 0.002 uncorrected). It is post-hoc, outside the Holm family, and does **not** replicate on V9c-val (+0.011 [−0.024, +0.040]). Per-program sign test p = 0.096. The 3.9-vs-3.13 interpreter shift (≈ 0.03) is as large.
The tracer snapshots `repr(frame.f_locals)` at every event including `return` (`tracer.py:364-384`; I read it). The state genome consumes those snapshots. When a result is held in a local and returned by name, the output is in the trace. Reviewer C's crude regex found a bare-local `return` in 10/19 V10 programs [DIRECT-EXPERIMENT by a reviewer, unreplicated by me]. The earlier "published" protocol already leaked the self-test's `AssertionError` once, which the project itself called an output comparison. So "output-free" is a *protocol* property, not an information-theoretic one.
**Mitigation.** SC-6 (return-expression mutation) is invisible, so the leak is not total.
**Evidence required to resolve.**
- A5E/A5F: reimplementation of the state abstraction verified bit-equal to the frozen one, then variants (a) dropping return-event snapshots, (b) args-only, (c) shuffled-locals null. Report all three whatever they show.
- A paired cluster test for state − V5 with ablation-family multiplicity declared, and replication on a withheld set under a new freeze.
- Until done: "output-free" only with the qualifier "return values and prints are not read; frame-local snapshots are".

### O6. "The held-out set is not independent of the development procedure." — MAJOR
**Objection.** All 19 V10 programs were first rejected from V8 by the project's own novelty rule (token-Jaccard 0.101–0.146 > 0.10 vs a corpus sibling) and then relabelled held-out (`generate_v10_independent.py:5-9`; `FREEZE_V10.json:44`). 16/19 still exceed 0.10 token-Jaccard to a V8/V9c program (max 0.225; A3). V10 reuses the same SC/SP families, composer, mutator, transformer and oracle; only the base programs differ. The corpus author is unnamed; three commits carry AI co-author trailers; whether the method and corpus authors coincide is [UNVERIFIED]. The benchmark was redesigned after the V8 negative result (reversed edit beat SBG, 0.876 vs 0.694), and V10 inspected edit-size statistics pre-freeze. "Frozen before scoring" rests on self-reported timestamps in one commit. The README concedes "same author and generation procedure".
**Consequence.** Generalisation is across programs only (LOPO V5 range 0.892–0.906), not across transformation families, authors, styles or input batteries.
**Evidence required to resolve.**
- Programs or version pairs from an independent source (human-authored, or real refactoring commits), with labels validated on an independent battery.
- Disclosure of corpus authorship and any LLM involvement; release history of when V9c-val scores were first opened relative to V10 generation.
- External timestamping of the next freeze (signed tag or archive DOI).
- Report V8-test (negative), V9c-val (noisy) and V10 together, with the V8 → V9 → V10 iteration history. Use "held-out programs", never "independent".

### O7. "Edit-size confounding is not controlled at the pair level." — MAJOR
**Objection.** Inside matched sets the CHANGED member has the larger edit in 292/319 (292 of 294 non-tied). Edit matched-set concordance is 0.955 [0.934, 0.972] vs V5 0.931 [0.897, 0.957]; difference +0.0235 [−0.011, +0.062] on V10, so they are not distinguishable. On V9c-val edit 0.924 vs V5 0.806 (marginal CIs separate; paired CI [UNVERIFIED]). The 0.875 / 0.735 exact-stratified AUROCs have no CIs and edit is 0.5 by construction in those strata. V8-test shows edit alone can win (0.876 vs 0.694).
**Consequence.** "Size-matched" holds for pooled AUROC only, and H3 is a between-pair effect. The repo's own matrix concedes the confound is "not fully removed (92% of V10 sets)".
**Evidence required to resolve.**
- Within-matched-set paired comparison with CIs on all populations; stratified AUROCs with cluster CIs.
- A benchmark design in which the edit-size difference within a set is not nearly deterministic (e.g. matched on token delta both ways), or a regression/partial-AUROC analysis conditioning on edit size and set.
- Wording: "outperforms edit size in pooled and size-stratified AUROC; does not outperform it in within-pair ranking".

### O8. "No evidence of real-world transfer; the decisive limitation is architectural." — MAJOR
**Objection.** BugsInPy 0.497 / 0.410 and QuixBugs 0.444 / 0.388 are different pipelines (SP-2-excluded post hoc vs committed), with CIs spanning 0.5 or sitting barely below it. Normal-approximation two-sided p-values for "below chance" are roughly .035, .09, .95, .044, .027, .23 (Reviewer B, derived, uncorrected). The real finding is that V5 = 0 on 26/41 BugsInPy and 32/39 QuixBugs bug pairs, and the negatives are synthetic rewrites, not real versions. The SC-6 result (17/23 invisible, exact CI ≈ [0.52, 0.90], 18 programs) is a protocol choice, not a tracer limit: `settrace` exposes the return value, but reading it would make SBG the label oracle (see O1). A committed declared-inputs QuixBugs regime shows 8/24 evaluated pairs at exactly 0 despite differing outputs (Reviewer C, unreplicated by me; 16 of 40 pairs excluded).
**Evidence required to resolve.**
- A5G: recompute BugsInPy/QuixBugs from raw scored files (reuse EXP-A3-007), report all six configurations plus the declared-inputs regime *with every exclusion*, coverage-of-buggy-path check, and Python-version effect.
- One pre-registered, ≤ 2 h, independent-source mutation experiment (config + sha256 before scoring; run once; exploratory).
- A5F: SC-6 classification of the 6 non-zero pairs and the zero-score causes (architectural vs bug vs protocol), with the exploratory return-value variant on dev only. Confirmatory evaluation requires a fresh withheld set and new freeze (V10 is burned for any variant designed after seeing it).
- Replace "below chance" with "no evidence of discrimination".

### O9. "AUROC is an artefact of benchmark composition and a tie-heavy score." — MAJOR
**Objection.** 63.6% of EQUIVALENT V10 pairs score exactly 0 (203/319), concentrated in rename/format families (SP-1 45/48, SP-2 52/53, SP-4 52/55, SP-6 49/52). Within-family V5 AUROC is 0.98–1.00 on SP-1/4/6 but 0.836 on SP-2 (edit 0.875), 0.774 on SP-5, and 0.611 on SP-8 extract-method (edit 0.606, n = 18). Hard families {3,5,8,11,12} give 0.836 against 0.952 for {1,2,4,6} [Reviewer C, exploratory, unreplicated]. The frozen Youden threshold is 7.955e-05, the smallest non-zero step, so precision/recall are a restatement of the zero-score rate (65.4% flagged, sens 0.944, FPR 0.364). Prevalence is 50% by construction. 84 AST-identical groups (212 rows) inflate the set; de-duplicated AUROC is 0.8843 [0.846, 0.912].
**Evidence required to resolve.**
- Pre-declared stratified table by SP and SC family with cluster CIs and tie handling (AUROC with explicit tie convention, plus AUPRC).
- De-duplicated primary analysis.
- Prevalence-sensitivity (1:5, 1:10) for precision, and a threshold-free practitioner metric.
- Report the families where SBG is indistinguishable from edit size (SP-8) as findings.

### O10. "Reproducibility is version-bound and the freeze is self-attested; the artefact has licence, provenance and citation defects." — MODERATE to MAJOR
**Objection.** Results are bit-exact on CPython 3.13.x only. On 3.9: 299/613 V10 pairs differ, 3,837/93,942 cross-label orderings flip (4.1%), pooled AUROC 0.8947 → 0.9226 (V9c-val +0.029). This shift is larger than the H4 and H5 estimates and comparable to state − V5; bootstrap CIs condition on fixed scores and exclude it. The cause is not isolated. Further: `FREEZE_V10.variants_tree_sha256` cannot be reproduced; the "35/35 trace check" is mostly string checks; the headline evaluation path is undocumented in README/Makefile; 18 GPL-3.0 ansible units sit in an MIT repo; ≥ 8 wrong citations (including a non-existent "Sumner ICST 2011"); corpus authorship undisclosed; `math_gray_code` trace failure (rc −9 after 1057 s) is uninvestigated. On the positive side: 807 tests pass, 10/10 consistency checks, 533/536 hashes match.
**Evidence required to resolve.**
- A5G version-sensitivity run (3.9/3.11/3.14) on full populations with AUROC impact and cause (line events, repr, frame details); state "CPython 3.13.x" at claim level.
- A single documented command for the headline path; correct README/Makefile; delete or explain the 35/35 check.
- Resolve licence (remove or relicense GPL material), citation audit, authorship/AI disclosure, archived DOI.
- WP-E: root cause of `math_gray_code` and EXP-ORCH-006 re-hash of the SBG tree against the 16,137-file baseline.

## 4. Other findings (not in the top ten)

- **V9c-val labels (MAJOR).** 16/216 EQUIVALENT pairs change output; 67/216 CHANGED (31%) are unobservable. The repo's static validity audit reports 0, which is contradicted by dynamic evidence. The same pattern exists in V9c-train, where thresholds and the combiner were fitted. The clean-subset V5 gain (0.751 → 0.849) selects on output and is an upper bound. V9c-val is called "confirmatory" in repo documents; I rate it **weak**.
- **Internal contradictions in the repo's own documents** (Reviewer D, in-file): "H4 fails in both independent evaluations" vs the same file's statement that V10 is not independent; "additional experiments needed: No"; "ready for manuscript drafting"; README body still headlines older V6-era numbers while its update block cites V10.
- **Practical significance.** Synthetic pairs only; no human or real-refactoring study; input synthesis needs typed signatures; cost studied only on toy programs (five repeated runs are redundant for deterministic code: event digests identical in 663/663); no memory cap.
- **Structural baselines straw man.** AST/token baselines are anti-informative on a benchmark whose EQUIVALENT class is rewritten source, so beating them is expected.
- **Language scope.** Python only. "Language-agnostic" in `docs/research/NOVELTY_ANALYSIS.md` is unsupported; SLACC already claims cross-language dynamic clone detection.

## 5. Claim ledger (existing evidence)

| Claim | Verdict | Note |
|---|---|---|
| H1: V5 AUROC > 0.5 | SUPPORTED, low bar | Label is selected for observability (O1). |
| H2/H3: V5 beats pooled edit size | SUPPORTED (pooled); not at pair level | O7. |
| H4: gain over edit + execution statistics | NOT ESTABLISHED (inconclusive) | O4. |
| H5/H6 (V6) | H5 not confirmed after Holm (.090); H6 inconclusive | Immaterial to positioning. |
| State 0.917 > V5 0.8968 | WEAK (post-hoc, not replicated) | O5. |
| BugsInPy/QuixBugs "at or below chance" | "No evidence above chance" supported; "below chance" not | O8. |
| 17/23 SC-6 pairs invisible | SUPPORTED (descriptive); WEAK as a rate | O8. |
| V10 "independent" | UNSUPPORTED | O6. |
| "Output-free" (unqualified) | UNVERIFIED / possibly contradicted | O5. |
| "Size-matched" (unqualified) | CONTRADICTED at pair level | O7. |
| "Frozen before scoring" (V10) | NOT ESTABLISHED (self-attested) | O6. |
| Any "SBG is novel / first" | UNSUPPORTED / CONTRADICTED | O2. |
| Any "unlike K&A…" | UNVERIFIED | O3. |
| Cross-language | UNTESTABLE | – |

## 6. How this review would be updated

| Pending result | Which objection changes |
|---|---|
| A4C/A4D held-out competitor predictions, independence check of the independent battery | O1, O2, O9 (and practical significance) |
| A5E ablation + state-vs-V5 paired test + leakage variants | O2, O4, O5 |
| A5F SC-6 classification and return-value variant | O5, O8 |
| A5G external, version-sensitivity, independence assessment | O6, O8, O10 |
| K&A, Xie & Notkin, ADABU full text | O2, O3 |
| WP-E final tree re-hash and `math_gray_code` root cause | O10 |

Nothing in this file should be read as a verdict on the paper's eventual merit. It is a statement of the best case a sceptical reviewer can currently make from existing evidence, and of what would answer each point.

## 7. Limits of this review

- I did not re-run any experiment myself. A3's 522 reproduced quantities are taken as established. Reviewer B re-derived some numbers (MDE, design effects, jackknife) and Reviewer C computed zero-score and SP-family AUROCs from frozen population/trace-cache files. I treat those as reviewer-derived and unreplicated.
- Literature claims inherit the repo's own reading depth; I read no external papers apart from the IEEE Access pages Reviewer D retrieved.
- IEEE Access: the fetched pages state the "original, technically correct" criterion and list "Negative Result" and "Methods" manuscript types. The "soundness over novelty" and data-availability mandates were not on the pages retrieved, so I treat them as [UNVERIFIED general knowledge]. The suitability risk is therefore a judgement: desk reject low–moderate (disclosure, licence, length); reject after review moderate–high if framed as a new representation or practical tool, moderate if framed as a methods/negative-result paper with every caveat above.
- Held-out predictions in `results/raw/EXP-A4C-*` were not read, per the non-citable status in `CURRENT_EXECUTION_STATUS.md`.
