# V5 Prior Art Additions — Piech 2015 & Sumner 2011

**Date:** 2025-07-09  
**Status:** Added to docs/research/PRIOR_ART_MATRIX.md (entries [41] and [42])

## Summary

The V5 novelty audit identified two critical missing prior art works that must be
cited and differentiated before any publication submission.

---

## 1. Piech et al. (ICML 2015)

**Why critical:** Most direct architectural analog to SBG's core pipeline.
Both use: execution traces → feature vector → similarity/distance.

**Differentiation:**
- Piech: supervised (LSTM trained on labels) vs SBG: unsupervised distance
- Piech: cross-program clustering vs SBG: cross-version comparison  
- Piech: uses output values (feedback signal) vs SBG: output-free (SAFEGUARD-2)
- Piech: learned similarity (no formal guarantees) vs SBG: formal pseudometric
- Piech: variable names in trace vs SBG: rename-invariant anonymization

**Strength of differentiation:** STRONG — the output-free design and unsupervised
nature are genuine architectural differences, not just application differences.

---

## 2. Sumner et al. (ICST 2011)

**Why critical:** Most direct prior art for the regression detection claim.
Sumner also targets behavioral change detection between program versions.

**Differentiation:**
- Sumner: lossless trace comparison vs SBG: lossy 8-dim compression
- Sumner: C/LLVM only vs SBG: designed for multi-language
- Sumner: binary verdict vs SBG: graded distance in [0,1]
- Sumner: O(trace_length) space vs SBG: O(1) per genome
- Sumner: requires aligned execution environments vs SBG: portable

**Strength of differentiation:** STRONG — the lossy vs lossless trade-off is
a genuine architectural distinction with different scaling properties.

---

## Impact on Novelty Verdict

With these two citations properly included and differentiated:
- Novelty remains: INCREMENTALLY_NOVEL
- The core contribution is the LOSSY, PORTABLE, MULTI-LANGUAGE behavioral genome
  as a design point between lossless comparison (Sumner) and supervised embedding (Piech)
- The benchmark (3,577 pairs) and the honest negative results remain novel contributions

## Action Items

- [x] Added to docs/research/PRIOR_ART_MATRIX.md as entries [41] and [42]
- [ ] Update paper abstract to acknowledge Piech and Sumner
- [ ] Add explicit comparison paragraph in Related Work section
- [ ] Ensure differentiation arguments are in the paper body
