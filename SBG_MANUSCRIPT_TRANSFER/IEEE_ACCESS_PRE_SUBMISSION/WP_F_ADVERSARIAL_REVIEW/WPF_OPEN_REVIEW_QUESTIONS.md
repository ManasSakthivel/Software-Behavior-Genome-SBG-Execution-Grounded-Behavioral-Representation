# WP-F Open Review Questions

Status: first pass (existing evidence). Questions that A4/A5/WP-E results or additional reading must answer before WP-F can write its second-pass review. **No GO / NO-GO is implied.**
Date: 2026-11-14. Cross-references: `10A_ADVERSARIAL_REVIEW_EXISTING_EVIDENCE.md` (O1–O10), `02_SCIENTIFIC_CONTRIBUTION_AND_POSITIONING_FIRST_PASS.md`.

Column "Blocks" = the review item that stays open until the question is answered. "Owner" = work package expected to produce the evidence, per `HANDOFF/NEXT_SESSION_ASSIGNMENTS.md`.

## A. Comparative evidence (A4: WP-A/WP-B)

| ID | Question | Why it matters | Needed evidence | Owner | Blocks |
|---|---|---|---|---|---|
| Q-A1 | Is the "independent-input" output-reading battery truly independent of the 11 protocol inputs and of label construction? | Without independence any comparison with output-reading methods is tautological. | A4D overlap check (inputs, generator, seed, no label access), written verdict | A4D | O1 |
| Q-A2 | Were any held-out labels joined to predictions before the frozen config (`EXP-A4C-002/frozen_config.json`)? Did the predecessor A4 (cancelled 20:04, `stages_eval.py` edited 20:04:50 after freeze at 20:02:54) ever see held-out metrics? | Pre-registration integrity for every comparative claim. | A4R classification (`EXP-A4R-001/VERIFIED_BASELINES.json`) and mtime audit | A4R | O1, O6 |
| Q-A3 | What are the held-out AUROC/AUPRC, with cluster CIs, for each competitor class (static, execution-statistics, spectra, birthmark, trace alignment, output-differencing) versus V5 on v10_test and v9c_val? | Replaces every QUALITATIVE comparison with DIRECT-EXPERIMENT. | A4C held-out run once on the frozen config; A4D recomputation with its own code | A4C/A4D | O2, O9 |
| Q-A4 | Does SBG add anything over the best independent competitor, with MDE stated? | The incremental-value claim. | A4D paired cluster tests, MDE per contrast | A4D | O2, O4 |
| Q-A5 | Which competitors are ADAPTED (K&A from abstract + thesis; ChangeGuard class D) vs faithfully reimplemented? | Prevents "outperforms ChangeGuard" claims on a non-ChangeGuard baseline. | `competitors_new/README.md` class justifications | A4B | O2, O3 |
| Q-A6 | Was any UNVERIFIED predecessor module used on held-out data by A4C? | Protocol risk logged in `BLOCKED_AND_FAILED_WORK.md` item 4. | A4R/A4C reconciliation | A4R/A4C | O1 |

## B. Ablation, state-genome dominance, return-value leakage (A5E/A5F: WP-C)

| ID | Question | Why it matters | Needed evidence | Owner | Blocks |
|---|---|---|---|---|---|
| Q-B1 | Does a reimplemented frozen distance reproduce `sbg_v5` bit-exactly? | Precondition for any ablation. | Bit-equality check before variants | WP-C | O5 |
| Q-B2 | Which components carry the AUROC: state only, topology only, bigrams only, exceptions only, temporal only, leave-one-out? Paired Δ vs full, Holm over the declared family. | Decides "representation" vs "one component" and answers whether the composite is justified. | A5E on v10_test, v9c_val (context dev/train), per-program, matched concordance, edit strata | WP-C | O2, O5 |
| Q-B3 | Is state (0.9171) > V5 (0.8968) on V10 robust (paired cluster test, per-sc_type), and does it replicate on a withheld set? | It is post hoc, uncorrected, not replicated on V9c-val (+0.011). | A5E paired test; a fresh withheld set under a new freeze | WP-C | O5 |
| Q-B4 | **Does the state genome's performance depend on return-event locals snapshots?** Variants: drop return snapshots; args only; shuffled-locals null. | Decides whether "output-free" can appear in a title/abstract. | A5E/F leakage variants, reported whatever they show | WP-C | O5 |
| Q-B5 | Of the 10/19 V10 programs with a bare-local `return`, is performance different from the other 9? | Reviewer C's crude regex is suggestive only. | Per-program split in A5E | WP-C | O5 |
| Q-B6 | What exactly makes the 17 SC-6 pairs score 0 (identical event streams: 17/17 per Reviewer C), and why do 6 of 23 not? Is the V9c-val analogue similar? | Distinguishes architecture vs bug vs protocol. | A5F classification, V10 plus val analogue | WP-C | O8 |
| Q-B7 | Would an exploratory SBG + return-value variant (dev only) restore SC-6 and what does it do to the label tautology? | The central tension of the paper. | A5F on v9c_dev only; statement that confirmation needs a fresh withheld set | WP-C | O1, O8 |
| Q-B8 | How sensitive are scores to `MAX_EVENTS`, per-trace timeout and an input subset (e.g. 5 of 11)? | Hidden free parameters in a frozen protocol. | A5E sensitivity runs via `dump_traces.py --worker` in own dir | WP-C | O9, O10 |

## C. External validity and robustness (A5G: WP-D)

| ID | Question | Why it matters | Needed evidence | Owner | Blocks |
|---|---|---|---|---|---|
| Q-C1 | Do raw scored files reproduce BugsInPy 0.497/0.410 and QuixBugs 0.444/0.388 (reuse EXP-A3-007)? Are the all-pairs and SP-2-excluded numbers both reported with every exclusion? | Two pipelines are quoted as one result. | A5G recompute, six configurations plus declared-inputs regime | WP-D | O8 |
| Q-C2 | For real-bug pairs, does the buggy path get executed under the protocol inputs (coverage-of-buggy-path)? Why do 26/41 and 32/39 pairs score exactly 0? | Distinguishes "input did not expose bug" from "representation is blind". | Coverage-of-buggy-path check; declared-inputs regime (8/24 zero per Reviewer C) | WP-D | O8 |
| Q-C3 | How do SBG, state-only, coverage and edit baselines compare on external pairs? | Whether any external signal exists beyond edit/coverage. | A5G baseline comparison on the same pairs | WP-D | O8 |
| Q-C4 | What is the AUROC effect of Python version (3.9/3.11/3.14) on full V10/V9c-val? What is the cause? | The shift (+0.028 on 3.9) exceeds H4 and H5. | A5G run from `results/raw/repro/` raw outputs; mechanism isolation if feasible | WP-D | O10 |
| Q-C5 | What is the result of one pre-registered independent-source mutation experiment (config + sha256 before scoring, run once)? | The only available partial test of generalisation off the development generator. | A5G pre-registration file with hash, then single run | WP-D | O6, O8 |
| Q-C6 | Is there any Java or cross-language evidence beyond "unusable/unverified"? | Prevents accidental generality claims. | A5G status statement; expected: none | WP-D | O2, O8 |
| Q-C7 | Are BugsInPy/QuixBugs negatives independent of the generator (they are SP rewrites of the fixed program)? | The "real bug" positives are real, the negatives are not. | A5G independence assessment | WP-D | O6, O8 |

## D. Statistics and benchmark validity (existing data; WP-C/WP-D or an A3 follow-up)

| ID | Question | Why it matters | Needed evidence | Owner | Blocks |
|---|---|---|---|---|---|
| Q-D1 | Are the 19-cluster percentile bootstrap CIs well calibrated? | Coverage was never tested (07 §8). | Simulation or alternative (cluster-t, wild, exact permutation) comparison | stats follow-up | O4, O5 |
| Q-D2 | What is the paired CI for edit − V5 matched-set concordance on V9c-val? CIs for exact-edit-stratified AUROC (0.875/0.735), tercile AUROCs, de-duplicated deltas? | Needed to say anything about edit-size control. | Recompute from existing scores with program-cluster resampling | stats follow-up | O7 |
| Q-D3 | How many post-hoc contrasts were computed in total? | Multiplicity is not logged in one place (Reviewer B). | A single exploratory-contrast register | stats follow-up | O4, O5 |
| Q-D4 | Does V5 retain its advantage over edit size when conditioned on within-set edit difference (regression/partial-AUROC)? | Pooled AUROC hides a near-deterministic within-set edit signal (292/294). | Conditioned analysis, cluster CIs | stats follow-up | O7 |
| Q-D5 | What is V5's stratified AUROC by SP/SC family with cluster CIs, with ties handled explicitly (63.6% of EQUIVALENT = 0)? | Reviewer C's table is exploratory, unreplicated, with n = 3–18 cells. | Pre-declared stratified table | WP-C | O9 |
| Q-D6 | Is the H4 combiner-transfer failure (V10 M_EX+V5 0.797 < V5 0.897) the reason H4 is flat? Do in-distribution refits change H4? | H4 may measure combiner transfer, not information. | H4 recomputed with in-distribution execution-statistics baseline | stats follow-up | O4 |
| Q-D7 | Is the `REAL_BUG_GENERALISATION_AUDIT.md` "~0.445" figure coherent? | Reviewer B could not reconcile it with 0.497. | Trace the number to a file or retract | WP-D | O8 |
| Q-D8 | What are label-error rates in V8-test, V9c-train and V9c-dev? | Thresholds and the combiner were fit on V9c-train; V8 labels were never audited. | Dynamic label audit, no label edits | WP-C or A3 follow-up | O6, O9 |

## E. Literature and positioning (independent of A4/A5)

| ID | Question | Why it matters | Needed evidence | Owner | Blocks |
|---|---|---|---|---|---|
| Q-E1 | What do K&A (2019) actually do (representation, labels, metrics, baselines, datasets, size confounds)? | Closest prior work; currently ABSTRACT-ONLY. | Full text via institutional access or author request | literature owner | O2, O3 |
| Q-E2 | Does Xie & Notkin (value spectra, 2005) subsume the state genome? Same for ADABU and Invariant Diffs? | The only possibly novel component. | Full-text reads; written overlap analysis | literature owner | O2 |
| Q-E3 | Is there precedent for the edit-size-confound diagnosis in JIT defect prediction (Kamei, Nagappan) and in ML-for-code benchmark critiques? | "In the literature found" must be true. | Full-text reads of those papers | literature owner | O2 |
| Q-E4 | Are `03` and `EARLY_COMPETITOR_BRIEF.md` consistent about SemaDiff and PatchGuru reading depth? | Records disagree (partial vs full; abstract-only vs full). | A1 reconciliation, one canonical depth per paper | literature owner | O2, O3 |
| Q-E5 | Can ChangeGuard (class D) be approximated faithfully enough for any comparison, or only discussed qualitatively? | Closest same-task competitor, uncited in SBG repo. | A4B class justification; otherwise explicit "qualitative comparison only" | A4B | O2 |
| Q-E6 | Does IEEE Access, at the time of submission, require data availability and judge soundness over novelty? | Reviewer D could verify only the "original, technically correct" criterion and manuscript types. | Re-read of current author guidelines at submission time | WP-F/orchestrator | positioning |
| Q-E7 | Who or what authored the 121 corpus programs, and was the corpus produced by the same system that designed SBG? | Shared-generator bias and AI-use disclosure. | Authorship statement from the repository owner; commit/tool provenance | repository owner | O6, O10 |
| Q-E8 | When were V9c-val scores first opened relative to V10 generation (b54ea99 → 8386eb5 → c5bc130)? | Forking-path risk after the V8 negative result. | Session/log evidence, or explicit non-verifiable disclosure | repository owner | O6 |

## F. Artefact and reproducibility (WP-E)

| ID | Question | Why it matters | Needed evidence | Owner | Blocks |
|---|---|---|---|---|---|
| Q-F1 | Is `SBG/` unchanged after the A4 wave (EXP-ORCH-006 re-hash vs the 16,137-file baseline)? | Read-only integrity of the evaluated artefact. | `shasum` diff, every difference investigated | WP-E | O10 |
| Q-F2 | Root cause of `math_gray_code` failing rc = −9 after 1057 s? | v9c_train trace cache is 45/46; Reviewer C's mechanism (2^100 loop, no memory cap) is INFERRED only. | Bounded subprocess with RSS watchdog | WP-E | O10 |
| Q-F3 | Can `FREEZE_V10.variants_tree_sha256` be reproduced, and is the headline path (`evaluate_v10`, `score_v6_experimental`, `FREEZE_V10`) documented in one command? | A reviewer will try. | Algorithm recovery or removal; a single documented command | WP-E | O10 |
| Q-F4 | Can the GPL-3.0 ansible content be removed or relicensed, and the ≥ 8 citation errors corrected before any text reuse? | Desk-reject and credibility risk. | Licence resolution; citation audit | repository owner | O10 |
| Q-F5 | What does the "35/35 trace check" verify? | It is mostly string/hard-coded checking, so citing it is misleading. | Remove or replace by A2's 644/644 + 436/436 recompute | WP-E | O10 |

## G. Procedure for the second pass

1. When A4D publishes `A4D_READY` and `05b` exists, and `08a/b/c` and `EXP-A5E/F-DONE` exist, re-read them cold.
2. Re-assess O1–O10 one by one; record "resolved / reduced / unchanged / worsened" with the specific file and number.
3. Add any new objection arising from A4/A5 results, including adverse ones (e.g. a simple baseline matching or beating V5 on independent inputs). Do not drop negatives.
4. Only then, and only if the orchestrator asks, issue a recommendation. This first pass issues none.

## H. Facts to keep out of the manuscript until resolved

- Any "unlike K&A…" or "K&A do not…" sentence (Q-E1).
- "Output-free" without the locals qualifier (Q-B4).
- "Independent" for V10 (Q-C5, Q-E7, Q-E8).
- "Size-matched/controlled" without the within-set caveat (Q-D2, Q-D4).
- "Below chance" for external corpora (Q-C1).
- "No incremental value" or "adds value" for H4 (Q-D6, A4/A5).
- "Frozen before scoring" without "self-attested" (Q-E8).
- Any number from `results/raw/EXP-A4C-*` before A4D verification.
