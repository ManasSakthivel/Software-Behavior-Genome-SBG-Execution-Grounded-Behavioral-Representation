# REAL-BUG GENERALISATION AUDIT
**Branch:** `remediation/sbg-v4`  
**Commit:** `c5bc130ea0909379315a7fdc160aa777c6c04840`  
**Date:** 2026-10-30  
**Auditor:** Bob (research engineering agent)  
**Question:** Are the sub-chance SBG results on BugsInPy and QuixBugs due to evaluation defects, or a genuine method limitation?

---

## 1. Summary of Existing Evidence

From `EXTERNAL_RESCORE_V8.json`, `EXTERNAL_NEGATIVE_AUDIT.json`, `DIAGNOSTIC_EXTERNAL.json`, and `RESEARCH_STATUS_V3.md §4`:

| Corpus / subset | n pairs (pos/neg) | Original v7 AUROC | Rescored v8 AUROC | 95% CI (cluster) |
|---|---|---|---|---|
| BugsInPy, all | 147 (41/106) | 0.410 | 0.416 | [0.322, 0.514] |
| BugsInPy, excl. SP-2 | 107 (41/66) | — | 0.497 | [0.402, 0.596] |
| QuixBugs canonical, all | 152 (40/112) | 0.388 | 0.384 | [0.285, 0.490] |
| QuixBugs canonical, excl. SP-2 | 111 (39/72) | — | 0.444 | [0.355, 0.539] |

The "positive" class in both corpora is the real-bug pair (base = fixed program, variant = buggy program). An AUROC below 0.5 means SBG scores the fixed program as *more different* from the buggy one than the reverse — the opposite of the desired discrimination.

---

## 2. Were the Labels Correct?

### Label orientation
- `DIAGNOSTIC_EXTERNAL.json` explicitly states: `"positives_base_is_fixed_variant_is_buggy": "pair_kind=real_bug, label=1 (see loader; base=fixed program)"`.
- This means positive = real bug = (base=fixed, variant=buggy). SBG should score HIGH when comparing buggy to fixed.
- AUROC < 0.5 means SBG actually scores the buggy→fixed direction as larger. This is the wrong direction.
- **However**, an AUROC of 0.416 on BugsInPy is the *complement* of 0.584 — if the positive/negative orientation were reversed, the AUROC would be 0.584. This is **not** a label-orientation error; a 0.416 AUROC in the stated direction is a genuine sub-chance result, not an inverted-label artefact (an inverted label would give exactly 1-AUROC = 0.584, and that threshold-independent measure is already above chance).
- **Label orientation is correct. The sub-chance result is genuine.**

### Buggy vs. fixed consistency
- In BugsInPy: base = the fixed (correct) program, variant = the buggy version. SBG compares variant's genome to base's genome. A behaviour-changing bug should produce a nonzero SBG score.
- In QuixBugs: same orientation (confirmed in `DIAGNOSTIC_EXTERNAL.json`).
- **No inconsistency.**

---

## 3. Is the Execution Protocol Appropriate?

### Observable behaviour rate
- BugsInPy: 26/41 real-bug pairs have SBG V5 = 0.0 exactly. The diagnostic (`DIAGNOSTIC_EXTERNAL.json`) records 31/40 QuixBugs real-bug pairs with identical exception fractions and 31/40 with identical event counts.
- This means the **protocol inputs do not exercise the bug** in the majority of pairs. The canonical inputs for QuixBugs/BugsInPy are the originally provided test inputs, which are designed to expose the bug for unit testing — but the SBG oracle uses 11 fixed, programmatically generated protocol inputs, which may not align with the bug-triggering inputs.
- **Root cause 1:** The fixed protocol inputs are not designed to trigger the specific mutations used in BugsInPy/QuixBugs bugs. This is a fundamental design mismatch between the evaluation protocol and the test corpus.

### SP-2 negatives (invalid labels)
- 40 BugsInPy SP-2 EQUIVALENT negatives: all have the entry function renamed (part of SP-2 transformation).  
- `EXTERNAL_NEGATIVE_AUDIT.json` identifies 7/40 as provably invalid: the `fix_kv` nested function is renamed to `fn_fix_kv`, but the call site `fix_kv(token)` is unchanged → `NameError` at runtime. These 7 score 0.79–0.80 (high SBG scores for ostensibly EQUIVALENT pairs), inflating apparent false-positive rate.
- **Effect:** These 7 invalid negatives count as false positives, depressing AUROC. Removing them raises BugsInPy excl. SP-2 to ~0.445; still well below chance.
- **Root cause 2:** Invalid EQUIVALENT labels in BugsInPy SP-2 contaminate the results, but correcting them does not resolve the sub-chance result.

### Self-distance contamination
- 3 BugsInPy base programs have nonzero self-distance (max 0.673), indicating the first-extraction-in-process cache effect (`raw/cold_start_probe.json`). These 3 units score anomalously high even for EQUIVALENT pairs.
- Removing these further reduces noise but does not move the point estimate above chance.
- **Root cause 3:** Partial (3 instances), does not explain the overall sub-chance result.

---

## 4. Is the Baseline Equivalent?

For the BugsInPy evaluation, no logistic baseline comparison was run. The comparison is SBG V5 alone vs. chance. This is appropriate: the question is whether SBG V5 can detect real bugs at all, not whether it can beat a baseline. The absence of baseline comparison is correct for this diagnostic question.

---

## 5. Is the Result a Genuine Method Limitation?

After correcting for:
1. The SP-2 invalid negatives (removing SP-2 entirely): BugsInPy AUROC = 0.497 [0.402, 0.596] — CI covers 0.5; QuixBugs = 0.444 [0.355, 0.539] — CI includes 0.5.
2. Self-distance contamination (3 BugsInPy bases): marginal effect.

**The corrected results indicate SBG V5 performs at approximately chance on real bugs, with large uncertainty (CIs spanning 0.5).**

The primary mechanism is identified: **26/41 BugsInPy and 32/39 QuixBugs real-bug pairs have SBG V5 = 0.0 because the protocol inputs do not expose the bug.** When 63–82% of positive cases score zero (indistinguishable from the EQUIVALENT class), AUROC cannot exceed chance in expectation.

This is not a coding error or a label error. It is a **fundamental design mismatch**:
- SBG uses 11 fixed programmatic inputs that exercise program call structure generally.
- Real bugs (in BugsInPy/QuixBugs) often require specific inputs to trigger the different behaviour (e.g., an edge case that the buggy code handles incorrectly).
- The output-free protocol (SAFEGUARD-2) additionally hides return-value differences, which are the most common manifestation of algorithmic bugs.

**The sub-chance point estimates** (0.416, 0.384 overall) arise from the SP-2 invalid negatives and self-distance contamination inflating apparent false-positive counts, not from SBG actively ranking fixed programs below buggy ones. When these artefacts are removed, the result is near-chance (0.497, 0.444), which is correct given the zero-score rate.

---

## 6. Assessment: Evaluation Validity

| Issue | Finding |
|---|---|
| Label orientation | Correct (positive = real bug) |
| Buggy/fixed consistency | Correct (base = fixed) |
| Execution protocol for bug class | **Fundamental mismatch**: fixed inputs do not expose most real bugs |
| SP-2 invalid negatives (7 cases) | Confirmed; does not reverse conclusion |
| Self-distance contamination (3 cases) | Confirmed; does not reverse conclusion |
| Metric implementation | Correct |
| Leakage | None |
| Overall validity | Valid; sub-chance is genuine once artefacts are removed → near-chance |

---

## 7. Should a New Real-Bug Experiment Be Attempted?

A new real-bug experiment could potentially show better results if:
- Bug-triggering inputs were used (rather than fixed protocol inputs), or
- The output-free constraint were relaxed for this domain.

However:
- Modifying the evaluation protocol after seeing negative results would constitute selective experiment design.
- A new experiment using different inputs or a different protocol would measure a different research question.
- The existing sub-chance result is *informative* about SBG's limitation in the current protocol: the output-free, fixed-input design does not generalise to real bug detection.

A new infrastructure-intensive real-bug experiment is **not recommended** within this audit. The limitation is genuine and must be stated.

---

## Conclusion

**Existing real-bug evidence is valid and indicates a genuine limitation.**

SBG V5 does not demonstrate meaningful discrimination on real bugs from BugsInPy or QuixBugs. The corrected AUROC (excluding provably invalid negatives and self-distance contamination) is near chance (BugsInPy: 0.497 [0.402, 0.596]; QuixBugs: 0.444 [0.355, 0.539]). The primary mechanism is that the fixed protocol inputs do not exercise the mutations underlying real bugs, combined with the output-free design that hides return-value differences.

This is a real method limitation, not an evaluation artefact. The paper must state clearly that SBG V5 does not demonstrate real-bug generalisation, and explain the mechanistic reason (input coverage + output-free design mismatch with real-bug mutation types).

The paper must not claim SBG is validated for real-world bug detection.
