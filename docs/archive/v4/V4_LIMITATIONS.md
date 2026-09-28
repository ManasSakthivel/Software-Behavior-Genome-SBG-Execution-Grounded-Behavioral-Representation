# SBG V4 Limitations

**Version:** v4 (Flagship Sprint)
**Status:** EVIDENCE FROZEN

---

## Critical Limitations (P0)

### L1: Execution-Volume Domination
SBG V3 (AUROC=0.540) is beaten by exception_fraction alone (AUROC=0.567).
The behavioral representation is dominated by execution-volume proxies.
Any paper making claims about "behavioral" information must address this.

**Root cause:** SBG's genome components (coverage, call frequency, exception rate)
are all monotone functions of execution volume. The v3 additions (call bigrams,
input sensitivity) did not break this dominance.

**Mitigation:** Re-design around state-transition invariants and input-output
behavior (accepting SAFEGUARD-2 relaxation).

### L2: SP-2 Partial Invariance Failure
Function rename (SP-2) gives mean_sim=0.587 instead of ~1.0.
A semantics-preserving transformation is not recognized as equivalent.

**Root cause:** Call bigrams use anonymization by first-call ORDER, not by
semantic role. A renamed function gets a different anonymous index if the rename
changes the load order.

**Mitigation:** Use stable content-hashing for function identity (not first-call order).

### L3: SC-3 Constant Mutation Blindness
Only 7.5% of integer constant mutations detected (SC-3 detection rate).
Programs with mutated constants (e.g., loop bound 5 → 6) appear identical to SBG.

**Root cause:** Small constant changes typically don't change coverage or call
frequency on the current canonical input set. The affected code path may execute
the same functions in the same order, differing only in a loop count or threshold.

**Mitigation:** Use inputs that specifically trigger the changed constant
(e.g., inputs near the threshold value). Currently canonical inputs are fixed.

### L4: Cross-Formulation Inversion
Cross-formulation AUROC=0.225 — equivalent algorithm implementations score
MORE similar than semantically changed (buggy) implementations on this micro-test.

**Root cause:** Buggy variants with output reversal still execute the same
functions in similar order/frequency, so SBG measures low distance.
The behavioral genome does not capture output semantics (SAFEGUARD-2).

**Mitigation:** Either relax SAFEGUARD-2 (compare outputs directly) or use
input-conditioned state-transition invariants.

### L5: Corpus Size Insufficient for Generalization
13 test programs → HIGH per-program AUROC variance (range [0.424, 0.686]).
DEV AUROC=0.488, VAL AUROC=0.512, TEST AUROC=0.546 — TEST is the highest split.
This suggests the 13-program test AUROC may be a favorable fluctuation.

**Mitigation:** Expand test set to ≥50 programs. Infrastructure exists (64 total).

---

## Important Limitations (P1)

### L6: No Java Execution
H11 (cross-language) remains INSUFFICIENT_EVIDENCE.
Java binary (JDK17) is available, but no Java tracing infrastructure was built.
This would require ~10-15 engineering days (Java instrumentation API, JVM bytecode tracer).

### L7: No Real Regression Corpus
BugsInPy not available. Track B (8 embedded pairs) is N too small for conclusions.
The regression accuracy of 0.50 is based on 8 hand-crafted pairs.

### L8: Label Validity
Oracle agreement rate 69.6% — approximately 30% of test labels are either:
(a) unverifiable with 16 oracle inputs, OR
(b) genuinely incorrect due to benchmark construction issues.

### L9: Statistical Power
At n=744 pairs, 80% power requires AUROC effect ~0.15.
Observed effect ~0.046 → significantly underpowered.

### L10: v3 Features Don't Help
Call bigrams (delta=+0.002), input sensitivity (delta=+0.001), exception causality
(delta=-0.001) collectively do not improve AUROC by the preregistered criterion (0.01).
The representational additions are null results.

---

## Minor Limitations (P2)

1. No environment containerization (requires Python 3.11, specific path)
2. Single canonical input set (11 inputs) may not trigger all behavioral differences
3. conc_producer_consumer excluded (threading non-determinism)
4. sys.settrace misses C-extension calls
5. Memory and CPU metrics unavailable
6. All programs are single-file, algorithmic — no module boundary effects
7. Cross-language: only Python evaluated
