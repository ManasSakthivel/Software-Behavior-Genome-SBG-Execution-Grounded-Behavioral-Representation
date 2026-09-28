# SBG V2 — Phase 0 Baseline Audit

**Date:** 2025-07-07  
**Status:** CONDITIONAL PASS — proceed to pre-registration (SAFEGUARD-1) immediately  

---

## Executive Summary

Phase 0 for SBG v2 deployed 8 parallel agents to audit the v1 codebase, verify all reported metrics, identify risks for dynamic execution, and design the v2 architecture. All agent outputs are saved in `docs/v2/agents/`.

The central finding: SBG v1 discovered a **structural-semantic inversion** — semantics-changing mutations (off-by-one, operator swap) score *higher* static similarity than semantics-preserving refactoring. This is a genuine, undocumented scientific finding. V2 investigates whether execution-derived behavioral evidence overcomes this inversion.

---

## V1 Results — All Verified by Agent 0B

| Metric | Value | Source |
|--------|-------|--------|
| SBG AUROC | 0.4237 | artifacts/phase3/B08/results_test.json |
| Best baseline AUROC (B02 AST) | 0.5528 | artifacts/phase3/B02/results_test.json |
| Structural-semantic inversion delta | +0.0335 | artifacts/phase4/E1/results.json |
| SC near-identical fraction | 99.18% | artifacts/phase4/E2/results.json |
| McNemar p-value (B08 vs B02) | 1.0 | artifacts/phase4/E6/results.json |
| E3 permutation p (variance test) | 1.0 | artifacts/phase4/E3/results.json |
| B06 dynamic trace AUROC | 0.5046 | artifacts/phase3/B06/results_test.json |
| H1–H6 verdict | NOT SUPPORTED / INSUFFICIENT | Final report |

---

## Agent Outputs Summary

| Agent | Status | Key Finding |
|-------|--------|-------------|
| 0A — Repo Map | ✅ COMPLETE | 64 programs, 3577 pairs, all v1 files frozen |
| 0B — Baseline Audit | ✅ COMPLETE | All v1 metrics independently verified |
| 0C — Leakage Audit | ✅ COMPLETE | 6 leakage risks; R4 (determinism) HIGH severity |
| 0D — Statistical Audit | ✅ COMPLETE | Holm-Bonferroni across H1–H12 family (n=12) |
| 0E — Prior Art Audit | ✅ COMPLETE | Missing: Jiang & Su 2009, Chen 1998 metamorphic testing |
| 0F — Adversarial Review | ✅ COMPLETE | 3 P0 risks identified; all mitigable |
| 0G — Architecture | ✅ COMPLETE | 60/64 programs safe for execution; v2 dir structure |
| 0H — Benchmark Audit | ✅ COMPLETE | SP-8 divergence bug; SC-3/SC-11 hard negatives |

---

## V2 Research Question

> Can execution-derived behavioral evidence (dynamic signatures: call patterns, branch coverage, exception behavior) overcome the structural-semantic inversion documented in SBG v1?

---

## Three P0 Risks — Must Resolve Before Experiments

| Risk | Description | Resolution |
|------|-------------|------------|
| AV1 | H7–H12 designed after seeing v1 negative results | SAFEGUARD-1: pre-register before any dynamic execution |
| AV2 | Output comparison trivially encodes ground truth | SAFEGUARD-2: classify all features as output-free vs output-proximate |
| AV3 | Output-proximate features = differential testing in disguise | SAFEGUARD-2: architectural separation of genome vs differential-testing baseline |

---

## Seven Safeguards

| ID | Description | Status |
|----|-------------|--------|
| SAFEGUARD-1 | Pre-register H7–H12 in git before any execution | **REQUIRED IMMEDIATELY** |
| SAFEGUARD-2 | Classify all v2 features as output-free vs output-proximate | Required before experiments |
| SAFEGUARD-3 | V2 uses inputs independent from v1's 5 canonical inputs | Designed in |
| SAFEGUARD-4 | Report AUROC separately for SC-3/SC-11 hard negatives | Required in evaluation |
| SAFEGUARD-5 | Re-run B06 with v2 input protocol | Required before claiming improvement |
| SAFEGUARD-6 | Run extraction ≥5× per program; exclude noisy features | Required in extraction phase |
| SAFEGUARD-7 | Holm-Bonferroni across H1–H12 (n=12) | Specified in statistical protocol |

---

## Novelty Assessment

SBG v2 is **conditionally novel** if:
1. The structural-semantic inversion is named and quantified as the central organizing finding
2. V2 dynamic features are genuinely output-free (not differential testing in disguise)
3. Prior art citations are augmented (add Jiang & Su 2009, Chen 1998, McKeeman 1998)
4. Negative results are reported with equal prominence

The structural-semantic inversion is not documented, named, or quantified in prior literature. This is the primary scientific contribution.

---

## Phase 0 Gate: CONDITIONAL PASS

**Passes:** All 8 agent outputs present; v1 metrics verified; architecture designed; risks identified.

**Conditions:**
1. SAFEGUARD-1 must be completed (git commit of H7–H12) before any dynamic execution
2. SAFEGUARD-2 feature oracle audit must classify all features before experiments

**Immediate next step:** Write `docs/v2/HYPOTHESES_V2.md` and commit to git.
