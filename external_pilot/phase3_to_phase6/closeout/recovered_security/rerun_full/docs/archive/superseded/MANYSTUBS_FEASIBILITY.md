# SBG — ManySStuBs4J Feasibility Analysis
## Assessment of Large-Scale Java Single-Statement Bug Corpus

**Created:** 2025  
**Sprint:** A+ Multi-Corpus External Validity Sprint  
**Status:** Feasibility analysis complete  
**Decision:** Excluded from primary evaluation; documented for completeness

---

## Dataset Description

ManySStuBs4J (Many Simple Stupid Bugs in Java) is a corpus of single-statement
bug fixes mined from GitHub Java projects using pattern matching on git diffs.

Two versions exist:
- **100-project corpus:** 10,231 single-statement bug fixes from 100 Java projects
- **1000-project corpus:** 153,652 single-statement bug fixes from 1,000 Java projects

Source: Karampatsis and Sutton, "How Often Do Single-Statement Bugs Occur? 
The ManySStuBs4J Dataset," MSR 2020.

---

## Assessment Against Inclusion Criteria

| Criterion | Status | Detail |
|-----------|--------|--------|
| Provenance is credible | ✓ Yes | Peer-reviewed (MSR 2020), institutionally maintained |
| Program versions available | ✓ Yes | Git commit pairs (buggy + fixed) |
| Execution is reproducible | ⚠ Partial | Requires per-project Maven/Gradle builds |
| Labels are defensible | ⚠ Partial | Mining-based; not all patterns are genuine bugs |
| Output-free compatible | ⚠ Requires Java adapter | Same barrier as Defects4J |
| Independent reproduction | ✓ Yes | Public dataset, well-documented |

---

## Bug Label Reliability Assessment

### Mining Methodology

ManySStuBs4J labels are produced by:
1. Pattern-matching on git diffs for 10 specific single-statement change patterns
2. Filtering for commits mentioning "fix", "bug", "error", etc. (heuristic)
3. Checking that the diff is a single-statement change

### Reliability Concerns

**False positives in labels:**

The mining approach introduces ambiguity at multiple levels:

1. **Refactoring vs. bug fix**: A single-statement change that uses the word "fix" in
   the commit message may be a style refactoring, not a correctness bug. The mining
   heuristic cannot distinguish these cases.

2. **Pattern specificity**: The 10 defined patterns (e.g., "Change Binary Operator",
   "Change Operand") are structural patterns, not semantic bug patterns. A change that
   matches "Change Binary Operator" might be an intentional feature change, not a bug fix.

3. **Context dependency**: Whether a single-statement change is a "bug" depends on the
   program's specification, which is not available in the dataset.

4. **Severity spectrum**: Some SStuBs represent genuine critical bugs; others may be
   cosmetic preference changes. The dataset does not distinguish.

### Estimated False Positive Rate in Labels

Based on analysis in the original paper and subsequent SE research:
- The authors estimate ~40-60% of mined patterns are "genuine" bugs
- The remainder are style changes, feature additions, or non-bug fixes
- No ground-truth validation against bug reports was performed in the original paper

For EEP evaluation, a 40-60% label false positive rate would severely compromise
the validity of any detection rate metric: we would be measuring detection of a
mixture of bugs and non-bugs, making the results uninterpretable.

---

## Java Language Barrier

ManySStuBs4J is Java-only. The same Java adaptation requirements from
[`docs/DEFECTS4J_FEASIBILITY.md`](DEFECTS4J_FEASIBILITY.md) apply:
- Java trace instrumentation required
- Output-free audit required on Java programs
- JUnit input extraction required
- Cross-language calibration required

---

## Scale vs. Interpretability Trade-off

The 1000-project corpus with 153,652 bugs offers:
- **Large scale advantage:** Statistical significance at any plausible detection rate
- **Project diversity advantage:** 1,000 independent projects

But this is offset by:
- **Label ambiguity:** 40-60% of "bugs" may not be genuine correctness defects
- **Language barrier:** Java only
- **Execution complexity:** 1,000 projects each requiring separate build environments
- **Interpretation problem:** What does "detected 45% of ManySStuBs4J bugs" mean if
  45% of the labels are non-bugs? The signal would be uninterpretable without further
  label validation.

---

## What ManySStuBs4J Would Be Appropriate For

Despite the above limitations, ManySStuBs4J could legitimately be used for:

1. **Large-scale robustness analysis** — after label validation on a random sample
2. **Project diversity claims** — demonstrating EEP works across diverse Java ecosystems
3. **Category-specific analysis** — reporting results per SStuB pattern category

If used, the following must be disclosed:
- N bugs in corpus
- N bugs evaluated
- N bugs excluded (with reasons)
- Estimated false positive rate in labels
- Per-pattern-category results (not just aggregate)
- Comparison against a label-validated subset

---

## Decision

**ManySStuBs4J is excluded from the primary empirical evaluation** because:

1. **Java language barrier** — same as Defects4J; Java adapter not yet validated
2. **Label ambiguity** — 40-60% label false positive rate makes detection rates uninterpretable
3. **No test infrastructure** — reproducible execution requires per-project Maven/Gradle builds
4. **Interpretation problem** — aggregate results over ambiguous labels would not constitute
   credible evidence

**Not excluded because of unfavorable numbers** — no numbers have been computed.
Exclusion is entirely on methodological grounds.

---

## Recommendation

ManySStuBs4J at the 100-project scale (after label validation and after Java adapter
completion) could provide strong evidence for:
- Project diversity at scale
- Bug category breakdown at large N
- Comparison with existing Java bug detection tools

This is appropriate for a **follow-up paper** or **extended evaluation** after the
current work establishes the foundational EEP result on Python corpora.

---

*ManySStuBs4J: Karampatsis and Sutton, "How Often Do Single-Statement Bugs Occur?  
The ManySStuBs4J Dataset," MSR 2020. https://arxiv.org/abs/2004.13653*
