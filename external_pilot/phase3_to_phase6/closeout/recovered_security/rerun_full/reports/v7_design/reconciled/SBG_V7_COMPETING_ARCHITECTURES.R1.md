Reconciled version R1 of SBG_V7_COMPETING_ARCHITECTURES.md; original preserved at reports/v7_design/_original_archive/

# SBG V7 Competing Central Architectures, R1

Authority: `reports/final/V7B_FROZEN_SPEC.md` > `P0_BINDING_DECISIONS.md`. This file keeps the original analysis of alternatives (a)-(f) (sections 1-9 and the evidence tags [SPINE] [LIT] [HYP-En] [JUDGEMENT] of the original are unchanged and remain valid as design analysis) and reconciles only what the P0 decisions, the frozen spec, the as-built implementation and the red-team review changed. All scores remain [JUDGEMENT]; no measurement was added by this document.

## 1. The alternatives (unchanged)

(a) multi-view code/behaviour graph with graph comparison; (b) labelled transition system over abstracted states; (c) structured event log with aligned-trace diff (the hybrid spine); (d) invariant-set comparison (Daikon style); (e) learned embedding/GNN scorer (V6-like); (f) pure differential testing with coverage-guided fuzzing. Original unweighted totals /24: (a) 13, (b) 10, (c) 17, (d) 8, (e) 10, (f) 19, selected composite (f)+(c)+(a as static context) 19. Weight sensitivity (original): witness and localisation x2 gives composite 25 vs (f) 23; cost and risk x2 gives (f) 25 vs composite 23. The choice was and remains a bet to be resolved by experiment, not by the table.

## 2. What changed

| # | Change | Reason | CM / decision |
|---|---|---|---|
| 1 | The "selected composite" is replaced by **V7-B**: (f) differential execution with replay-confirmed witnesses, plus the sufficiency/evidence contract of (c) restricted to observed channels, plus (a) only as static context (`ChangedRegions`, `SourceMapping`). The aligned-trace internal-state channel of (c), the LTS (b) and invariants (d) leave the core | D5, D6: E optional, V7-A a gated pilot; internal-only divergence is not a verdict | M-02, V-02; D2, D5, D6 |
| 2 | The collapse rule is now concrete: if K4 fails, PIVOT to V7-B' (sufficiency-aware differential testing, no explorer/impact/state, no novelty claim beyond the evaluation protocol); if V7-B' is no better than B1, STOP. This replaces "if E1 shows no benefit of (c)'s internal channels" | E1 depended on internal labels that cannot be defined independently (RT Q3) | K-01, K-02; D9 |
| 3 | Role of (f): it is the baseline family and the first stage. Baselines must be like-for-like (same diff-derived information, or V7 also run diff-blind; same abstention rule; one FAR definition) | information asymmetry between V7 and baselines | X-05; D7, D11 |
| 4 | Role of (e): optional J, off by default, never touches a verdict, own sealed holdout | unchanged in role; margin disputes (X-12) are not decided here | X-12 |
| 5 | Role of (a), (b), (d): (a) static context only; (b) and (d) optional views for the V7-A pilot only | no replayable witness from an abstract transition or invariant set | D5 |
| 6 | Original challenge 5 (monotone sufficiency scalar for convenience) is withdrawn: no scalar sufficiency is computed; S-levels are a conjunction of floors (FS s6) | four incompatible S definitions; plateau rewards weak explorers | S-01; D3 |
| 7 | Original challenge 6 (cheap bounded-equivalence tier by exhaustive enumeration) is kept only as the separately named formal claim `BOUNDED_EQUIVALENCE_PROVEN` with its stated domain, outside the verdict set and never required | D1; FS s2 | V-04 |
| 8 | Original challenge 4 (anchors restricted to context, not compared payload): kept; because the observed-channel verdict is alignment-free, G affects only the optional locus | circularity | EV-06 |

## 3. Post-Phase-1 evidence relevant to the choice (cited, not re-derived)

From `INDEPENDENT_RED_TEAM_REVIEW.md` and `FINAL_RESEARCH_READINESS_REPORT.md`: on 321 development pairs (non-pristine, exploratory) V7-B detection was 0.708 vs B1 0.774 and B3 0.81; false assurance 0.123 vs 0.226, largely through abstention; B1+rep differs from B1 on 2 of 311 pairs; V7-B cost about 3x B1 CPU on child-only accounting; the sufficiency level did not separate synthetic labels. This is consistent with the original ordering (f) >= composite on raw score and keeps the bet unresolved. Published tools that overlap (Shadow SE, DiffKemp, Testora, DiffTestGen, Mokav, Cleverest, DiffSpec) were not run as baselines; B2 covers QuixBugs only, B3 is a minimal mutation loop, B5 is a lookup of V6 scores on different inputs. Any competitive claim is therefore unavailable (R48, R50).

## 4. Open or unchanged

- Scores remain judgement; E7 (tracing overhead, storage, alignment on real traces) remains unmeasured on real traces. The as-built tracer uses `sys.monitoring` line/branch capture; overhead was measured only as child CPU lower bound.
- Language scope: Python only; "language-neutral" scores are about the architecture, not demonstrated tooling. Java/C carry no claim (R34).
- Literature in the original was cited from memory; use `P0_LITERATURE_VERIFICATION.md` and `research/literature/` (158 rows: 7 full text, 89 abstract, 62 metadata).
