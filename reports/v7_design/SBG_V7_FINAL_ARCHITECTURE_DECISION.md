# SBG V7 Final Architecture Decision

## 1. Recommendation
Build the architecture in the Master Plan (§3, reconciled decisions §2): immutable evidence fabric + sandboxed tiered capture + adaptive changed-region-directed exploration + alignment + first-divergence witnesses + explicit sufficiency + four-way verdict. Python only, first.

## 2. Why this beats the alternatives (see COMPETING_ARCHITECTURES)
- It fixes what actually failed. V6's losses were driven by unobservable pairs and return-blindness; differential output comparison already reached 0.976 on activated QuixBugs pairs and 0.995 on v10, so the missing piece is exploration/activation plus honest abstention, not a better scorer.
- Graph-only (a) and invariant-only (d) cannot produce a replayable witness; the learned scorer (e) is V6 again and inherits the generator/edit-size shortcuts; the transition system (b) is kept as an optional view because an abstract transition is not a witness.
- **Honest caveat:** pure same-budget differential testing (f) tied the selected design at 19/24 in the authors' scoring (wins if cost/risk are weighted double). The composite is a bet, not a demonstrated improvement; those scores are judgment, not measurement.

## 3. Retain / discard from V5/V6
Retain: freeze/manifest/hash discipline, from-raw reproduction check, program-cluster bootstrap and permutation statistics, abstention-first policy and status taxonomy (ACTIVATED/NOT_ACTIVATED/UNKNOWN), audit scripts, all negative findings, the tracer's event semantics as `v6_compat`. Preserve untouched: tag `v6-holdout-complete`, holdout artifacts, reports.
Discard: 10-feature distance scorer and LR/GBM fusion as the core; output-free-only channel; the E columns as predictors; mutation-generator-derived labels as ground truth; SP-8/SP-11 generators (retained only as documented defect cases); the in-process thread sandbox for claims; AUROC as the headline metric.

## 4. Strongest defensible novelty hypothesis (a hypothesis, not a finding)
Primitives (differential testing, directed fuzzing, shadow/regression analysis, coverage-linked impact) exist. The only candidate contribution is: **at equal CPU budget, a sufficiency-gated verdict that never equates "no observed difference" with equivalence, plus internal-state divergence witnesses, yields fewer false assurances at a given coverage than output-only differential testing and coverage-guided differential fuzzing, on independently adjudicated, project-disjoint real regressions.** Two tiers: V7-A if internal-state divergence adds measurable information; V7-B (narrower, still legitimate) if only sufficiency-aware witness-based differential testing wins.

## 5. Strongest argument against
It may reduce to existing differential testing + coverage tools; the added value of internal-state divergence is unproven and, with ~150 divergent real pairs, the planned +3pp internal-state test is underpowered ("inconclusive" is a likely outcome). Real-bug ground truth is scarce and costly to adjudicate, the independent holdouts (H-R, H-M) may be infeasible at the stated size, V5/V6 benchmarks cannot serve as pristine evidence, and ~51 engineer-weeks (~32 calendar weeks critical path, range 22-48) is spent before the central question is answered.

## 6. Most serious remaining risks
(1) Benchmark construction and adjudication feasibility (kill K1/K5). (2) Activation on real projects may stay low even with exploration (K3: need >= 60% activation and +15 points over replay). (3) Isolation rebuild and nondeterminism control cost more than estimated. (4) Threshold and power judgment calls. (5) Contamination: any design choice informed by V6 failure lists further contaminates those sets (R-26). Full list: `SBG_V7_RISK_REGISTER.md` (38 risks, stop conditions).

## 7. Implementation order (from the roadmap)
P0 governance, schema, immutable store, benchmark-construction start and holdout hash-commit -> P1 capture hardening (isolation, determinism, completeness, replay; activation census) -> baseline harness frozen -> P2 static context + alignment -> P3 divergence, sufficiency, verdict on independent controlled suites -> P4 adaptive exploration -> **K4 checkpoint: does the core thesis beat output-differential at equal budget?** -> P5 state abstraction/invariants and P6 impact only if K4 passes -> P7 adjudicated benchmark finalised -> P8 one-shot sealed-holdout evaluation -> P9 optional prediction and formal tier.

## 8. Evidence required to declare success
Gates G0-G8 passed with numeric thresholds frozen beforehand; on the sealed project-disjoint holdout (>= ~150 adjudicated divergent pairs, >= 40 projects, kappa >= 0.7): lower confidence bound of the false-assurance reduction versus same-budget differential testing above 0 at coverage >= 0.60, replay-confirmed witness validity 100%, all 14 validation-matrix rows passing, clean leakage audit. V7-A additionally needs a significant internal-state gain on masked-divergence truth. Not sufficient: results on V5/V6 benchmarks, AUROC alone, or completed experiments without a pre-declared win. NO-GO triggers are in `VALIDATION_AND_ACCEPTANCE_GATES.md`.

## 9. GO / REVISE / NO-GO
**REVISE, with a conditional GO limited to P0-P1 plus benchmark construction.**
- Not a full GO: the design documents were written in parallel and are not cross-checked (§5 of the Master Plan), thresholds are untuned, references are not fully verified, and the central bet is untested.
- Conditional GO for P0/P1 is justified because they are cheap, are required by every alternative (including the differential-testing fallback), and produce the activation census and feasibility numbers (K1, K2) that decide whether to continue.
- Stop or pivot to a narrower "sufficiency-aware differential testing" (V7-B) if K3 or K4 fail; stop entirely if K1 or K5 fail.
