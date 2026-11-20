# Review R1: Software Testing and Differential / Regression Testing

**Manuscript:** "How Far Can a No-Divergence Verdict Be Trusted? False-Assurance Risk, Evidence Response Signatures, and a Pilot Study in Differential Regression Testing" (IEEE Access submission, SBG V8)
**Reviewer expertise:** software testing, differential and regression testing, test adequacy, mutation analysis
**Basis of review:** static reading of `main.tex`, all `sections/*.tex` and `tables/*.tex` in include order, figure filenames, `CLAIM_EVIDENCE_REGISTER.md`, `NUMERICAL_CLAIM_AUDIT.md`, `audit/*`, and the repository source (`sbgv8/`, `experiments/v8/`, `scripts/`, `datasets/v8/dev_records.jsonl`, `research/v8_final_design/`). Nothing was executed except read-only counting over the saved development records file to check reported denominators.

---

## Summary

The paper treats a differential-testing "no divergence observed" (NDO) verdict as a selective prediction. It defines a false-assurance risk relative to an observation boundary and an adjudication budget. It proposes a change-conditioned evidence profile with a calibrated, abstaining, integrity-first decision procedure (CEC), and an "Evidence Response Signature" (ERS): eight label-free properties checked by ten post-hoc perturbations of evidence records. A pilot on 312 Python development pairs (synthetic, QuixBugs, BugsInPy; 258 with construction labels) reports a plain-differential-testing false-assurance rate of 0.169. The predecessor gate abstained heavily without lowering that rate, and the richer profile did not beat coverage-only calibration (+1.6 pp, 95% CI −6.6 to +16.3). The paper is unusually candid about its limits. However, the headline empirical number depends on vacuous pairs and on unverified generator labels, the main chance reference is drawn from the wrong pool, the novelty positioning misses the classic literature on estimating failure probability after failure-free testing, and the one positive empirical result (ERS found a defect) is narrow.

## Strengths

1. **Honest negative-result reporting.** Non-significance is not read as equivalence (`design.tex:200`, `discussion.tex:13`, Table `tab:interp`). An MDE/power analysis is reported (`results.tex:88`). The sign instability across seeds is disclosed (`results.tex:86`). A flawed internal artifact is explicitly excluded (`results.tex:144–154`). This is rarer than it should be.
2. **Matched-coverage comparison against random abstention** (Prop. 3, `problem.tex:130–135`; `discussion.tex:6`) is the right methodological lesson for any abstaining test oracle or LLM-based equivalence filter, and the paper states it clearly.
3. **The ERS definition is precise and transcribed from code.** The N/A and abstention-credit accounting (`ers.tex:14–26`, Remark `rem:vacuous`) prevents vacuous passes from being counted silently. The "Resp." column in Table `tab:ers` usefully exposes which passes are vacuous for the fitted model.
4. **The threat model is concrete,** and outcome categories separate blocked / detected-only / no effect / successful (`trust.tex:38–39`, Table `tab:security`). Open channels are admitted (SENSE04b, `results.tex:14`).
5. **Traceability** of numbers to machine-readable sources is far better than typical. The `audit/stats_summary.json` denominators match the paper (I recounted B1 = 183 NDO / 31 FA, B3 = 61 / 13 from `dev_records.jsonl`).

## Major concerns

### M1. The headline B1 risk (0.169) and the B6 chance reference include 49 pairs on which no input was executed
*Evidence.* `sbgv8/baselines.py:29` defines B1 as `DIV if has_witness(rec) else NDO`. In `datasets/v8/dev_records.jsonl`, 50 records have an empty `inputs` list; 49 of them are labelled. All 49 carry the blocker `unsupported_signature`, which the protocol notes describe as SP-2 renamed entry points. They split into 31 QuixBugs negatives, 15 synthetic Y=0 and 3 synthetic Y=1. B1 issues NDO on all 49, so they make up 27% of B1's 183 "no difference" verdicts. A practitioner's harness that cannot call the entry point reports an error, not a pass. Excluding them gives B1 risk = 28/134 = **0.209**, not 0.169. That moves the abstract's headline (`abstract.tex:1`; `introduction.tex:42`; `results.tex:56`) and recasts the "gate abstained on two thirds without lowering the risk" claim (`results.tex:57`; `discussion.tex:6`). Of the 122 gate abstentions, 49 are on pairs where nothing ran. The statement "312 executed development pairs" (`abstract.tex:1`) and "All 312 runs completed with exit status 0" (`design.tex:72`) are technically true but misleading.

The same pool feeds B6 (`baselines.py:48–56`: `pool = [r.y for r in lab if not has_witness(r)]`), so the "random abstention" reference of 0.169 is also deflated.
*Fix.* Define B1 to return INS (or a separate "not executed" outcome) when no input executed. Recompute B1, B2, B6 and the worst-case figures. Report both versions in a sensitivity row. **No new experiments; re-analysis only.**

### M2. The chance reference for the matched-coverage contrast is drawn from the wrong population
*Evidence.* At c* the soft-policy models rank and issue 61 of the **85 soft-eligible** pairs (`design.tex:26`; `results.tex:76`). B6 instead samples 61 from the **183 B1-issuable** pairs (`design.tex:163`; `baselines.py:48–56`). These populations have different base rates. Recounting from `dev_records.jsonl` with the v8.0 soft blocker set (`sbgv8/policy.py:13`), the 85 eligible labelled pairs contain 24 with Y=1, a base rate of **0.282**. Random selection within the eligible set therefore has expected risk 0.282, against which B8 (0.213) and B7 (0.230) look *better* than chance and B9 (0.292) looks *at* chance. The paper's reading "B8 … lies 4.4 points above random abstention … not better than chance" (`results.tex:76`; Table `tab:stats` row B6−B8) conflates the eligibility filter with ranking quality. Prop. 3 itself is stated for random abstention *within the issued set S* (`problem.tex:131`), which supports the within-eligible reference.
*Fix.* Report two chance references: (a) random within the policy-eligible set, for ranking quality, and (b) random within executed B1-issuable pairs, for the end-to-end procedure. Re-state RQ4 accordingly. **No new experiments.**

### M3. "False assurance" is operationalised with unverified generator labels, which brings back the equivalent-mutant problem, and suspect labels were excluded in an outcome-dependent way
*Evidence.* For synthetic pairs, Y is "the generator's record of whether the injected change alters behaviour on the declared domain" (`problem.tex:169`). The repository's own dataset notes say "Divergence may lie outside the sampled inputs" and that the Y=0 synthetic pairs are "equivalent under looser equality", which differs from the strict channels compared under the boundary. All 13 B3 false assurances and 29 of 31 B1 false assurances are synthetic Y=1 pairs (`design.tex:109`; recount). Many of them have full activation and 11 SAME inputs, for example `synthetic:dev__math_collatz_length__sc4_s0_p0` and `synthetic:train__sort_pigeonhole_sort__sc1_s0_p0`. These are exactly the cases where an equivalent or practically unrevealable mutant is a live alternative explanation. Mutation-testing work treats this as a first-order threat (Budd & Angluin 1982; Madeyski et al., TSE 2014; Papadakis et al., TCE, ICSE 2015), and none of it is cited. Moreover, `scripts/build_dev_pairs_csv.py:23–25` marks whole transformation families (SP-8, SP-11, and "levenshtein SP-6") as `SUSPECT_LABEL` and excludes them (`experiments/v8/dev_collect.py:14`). One excluded pair, `quixbugs_neg:levenshtein__sp-6_s0`, is a "behaviour-preserving by construction" negative that produced a DIV verdict, so it is a label error detected *by the evidence*. Excluding labels because the system disagreed with them biases risk estimates. The exclusion of 6 pairs is not mentioned in the manuscript: the corpus table reports "Unlab." without separating suspect from unlabelled (`design.tex:90–95`).
*Fix.* (i) For every Y=1 NDO pair (31 under B1), produce a concrete witness input in the declared domain, by bounded-exhaustive search, symbolic execution or manual construction. A pair without a witness should be reclassified as unresolved, which the paper's own worst/optimistic-case machinery already supports (`problem.tex:113`). This is about 31 small programs, so it is cheap. (ii) Disclose the 6 SUSPECT_LABEL exclusions, the rule, and when it was fixed, and report risks with them included. (iii) Discuss the equivalent-mutant literature. **(i) needs a small new adjudication effort, not new pipeline runs.**

### M4. The QuixBugs arm is near-degenerate for the estimand yet dominates the cluster bootstrap
*Evidence.* QuixBugs positives are labelled DIV *only if* the benchmark's tests distinguish the versions; otherwise they are UNLABELLED (`scripts/build_dev_pairs_csv.py:15–19`). The same inputs drive the evidence (`problem.tex:169`; `design.tex:110`). QuixBugs negatives are all Y=0. As a result, the 113-pair QuixBugs cluster contributes 0 NDO false assurances under B3 and 2 under B1 (both resource-limit cases: `quixbugs:bitcount`, `quixbugs:sqrt`). It is nevertheless 43.8% of labels and a single bootstrap draw (`design.tex:78`). It inflates the denominators and the Y=0 pool while adding essentially no information about ranking false assurances. Calling these subjects "benchmarks" in the abstract overstates what they test.
*Fix.* Report all RQ3/RQ4 numbers with and without the QuixBugs cluster. Relabel QuixBugs positives with inputs that are disjoint from the evidence battery, or drop the arm from label-dependent RQs. **Re-analysis; relabelling needs new executions.**

### M5. "Plain differential testing" is a weak, non-representative baseline, and the conclusions about differential testing do not follow
*Evidence.* B1 uses the V7-B declared battery: at most 12 inputs per pair (`approach.tex:210`). The most common counts in the records are 11 (124 pairs), 0 (50) and 2 (34). There is no generated or property-based input campaign, no coverage-guided generation, no change-directed generation (DiffGen/BERT/shadow symbolic execution, which are cited at `background.tex:6`) and no LLM test generator (Testora, cited). The conclusion "Roughly one in six 'no difference' outcomes concealed a labelled behavioural change" (`results.tex:56`) and "Empty difference sets carry substantial false-assurance risk" (`discussion.tex:4`) are therefore claims about an ~11-input hand battery, not about differential regression testing as practised. For BugsInPy, the units run on "synthetic-battery inputs; regression not reproduced" (`build_dev_pairs_csv.py:20–21`). The claim that "real-project changes thus pose the sufficiency problem more often" (`results.tex:143`) is more plausibly an artifact of feeding a generic battery to extracted project functions.
*Fix.* Add at least one realistic input generator per pair: Hypothesis-based random generation with a fixed budget, or a change-directed generator. Report how B1 risk falls with input budget, which also gives Prop. 2 an empirical instance, since the budget is the variable it is about. Rephrase B1 as "declared-battery differential testing". **New experiments needed.**

### M6. The obvious testing-literature competitors to the evidence profile were not evaluated
*Evidence.* The paper argues that the profile turns execution–infection–propagation knowledge into features (`background.tex:19`). Yet its "influence" feature is an admitted reachability proxy (`approach.tex:139, 152`). The only learned comparators are coverage logistic models (B7) and ablations (`design.tex:158–167`), and the fitted model "retains essentially one feature (`mu_min`)" (`tables/tab_ers.tex:27`). The natural testing baselines are cheap on programs this small:
- (a) change-localised mutation score, i.e. the share of mutants of P′ within U_c killed by the battery, in the style of diff-based mutation testing at Google (Petrović & Ivanković, ICSE-SEIP 2018);
- (b) checked coverage or dynamic-slice-based oracle reach of U_c (Schuler & Zeller, cited);
- (c) a PIE-style propagation estimate.

Any of these could test whether "sufficiency" signals predict false assurance, which is the paper's core hypothesis. Without them, the negative RQ4 result says little about evidence-based estimation in general, only about this profile.
*Fix.* Add (a) as baseline B10. It needs only mutant generation on the changed lines plus re-running the existing battery. **New experiments needed (small).**

### M7. Novelty positioning omits the directly relevant literature on estimating failure probability after failure-free testing, and on per-change risk prediction
*Evidence.* The gap statement (`background.tex:19, 34–40`) claims that no prior work attaches a conditional probability of error to a passing observation. This overlooks several bodies of work:
- Miller et al., "Estimating the probability of failure when testing reveals no failures" (TSE 1992);
- Hamlet's probable correctness;
- Voas & Miller's testability, and Bertolino & Strigini (TSE 1996), who combine PIE-style testability with failure-free testing to obtain a posterior probability of correctness, which is the per-verdict analogue for one version;
- Littlewood & Wright on conservative claims after failure-free operation;
- Böhme's STADS (TOSEM 2018) and residual-risk estimation (Böhme, Liyanage, Wüstholz, FSE 2021), which estimate the probability that further testing would reveal a discovery after a campaign found none. This is the closest statistical analogue of the paper's estimand R.
- Just-in-time defect prediction (Kamei et al., TSE 2013) is a per-change risk estimate from change features and is an obvious comparator for "risk per change pair".
- For ERS, CheckList (Ribeiro et al., ACL 2020) defines invariance (INV), directional (DIR) and minimum-functionality (MFT) tests, which are the same three classes as ERS's invariances, monotone requirements and prescribed outcomes (`ers.tex:7–11`). Metamorphic testing of ML classifiers (Xie et al., JSS 2011) is also absent.

`voas1992pie` is cited only as a per-location score (`background.tex:17`; Table `tab:positioning`). None of the works above is in `references.bib` (76 entries checked).
*Fix.* Add these works, recast C1 as an adaptation of residual-risk / testability-based reliability estimation to version pairs, and recast ERS as INV/DIR/MFT behavioural testing applied to a verdict-risk estimator. **No experiments.**

### M8. The formal results are close to definitional and are presented as contributions
*Evidence.*
- Prop. 2 (`problem.tex:115–122`) assumes adjudication "monotone" in exactly the sense needed: an input found under (Ω, B) that separates under Ω′ is found under (Ω′, B′). The proof is then immediate.
- Prop. 3 (`problem.tex:130–133`) is the textbook expectation of a hypergeometric sample mean.
- Prop. 4(ii) (`problem.tex:161–164`) says that an estimator can be modified off-support without changing on-support metrics.
- Prop. 1 (`problem.tex:89–92`) restates that untrusted input must not drive a decision.

All four are correct, but the abstract's "Three results follow" (`abstract.tex:1`) and contribution C1 (`introduction.tex:61`) overstate them.

There is also an implementation gap for Prop. 1. The validator returns `trusted = None` for a "legacy" directory with no V8 artefacts (`sbgv8/evidence_schema.py:145–149, 207`; `approach.tex:98`). `None` maps to ι=1 (`sbgv8/adapter.py:97`). `require_anchor` defaults to `False` (`adapter.py:60`), and the anchor is not checked when no V8 artefacts and no anchor file exist (`evidence_schema.py:204`). A keyless writer (A2) who deletes `v8_parts.json`, `v8_capture.json` and `v8_anchor.json` and re-chains `evidence.jsonl` would therefore appear to pass validation. That is a downgrade attack, and it contradicts "fail-safe integrity against keyless post-hoc writers" (`results.tex:28`) unless `require_anchor` is mandatory. Table `tab:threats` labels "Strip or alter the anchor" as **Blocked** (`trust.tex:57`).

Separately, `experiments/v8/dev_collect.py:50` calls `load_record` without an anchor key. The 312 development records lack the `capture`/`anchor`/`untrusted` metadata that the current adapter writes, so the evaluated corpus appears to have been collected *without* independent capture or anchoring. "Every development record passed integrity validation" (`approach.tex:152`) thus refers to a weaker validator than the one described in Section VII.
*Fix.* Downgrade the propositions to "observations" or merge them into the text. Make `require_anchor` default to true whenever a key is configured, and test the strip-all-artefacts downgrade. State which validator produced ι for the 312 records. **Small code change plus one security re-run.**

### M9. "Pre-registered" is overstated, and pre-declared analyses are missing
*Evidence.* The paper says the plan was "fixed before evaluation" (`design.tex:203`) and refers to a "pre-registered three-test family" (`design.tex:197`). The protocol `research/v8_final_design/06_EXPERIMENTAL_PROTOCOL.md` was committed on 2026-11-18 (commit `e8ca1c12`), the same date as the development collection directory `v8_dev_20261118_195446` (`tables/…`, `reproducibility.tex:17`). It is titled "to be frozen and time-stamped before any Phase 3 label is seen" (line 1). It says development data "may be used for debugging only; they are design-exposed" (line 20) and requires a third-party timestamp (line 20), which the paper concedes was not obtained (`reproducibility.tex:66`). The protocol also pre-declares analyses the paper omits (line 18): the secondary c* grid {0.20, 0.30, 0.40} (line 7), BCa intervals, leave-one-project-out, analysis without hard negatives, and "no pair silently dropped", which conflicts with the 6 SUSPECT_LABEL exclusions and the 9 missing BugsInPy records (`design.tex:76`).
*Fix.* Call H1a–H3 "hypotheses declared in the design protocol, applied to design-exposed data", and drop "pre-registered". Report the pre-declared secondary c* grid and the sensitivity analyses, or justify omitting them. **Re-analysis only.**

### M10. The positive ERS result is thinner than presented
*Evidence.* Of the ten perturbations, several give no information about the deployed model:
- P8 passes "by construction" (`tables/tab_ers.tex:22`; `ers.tex` Table `tab:ersprops` row 7);
- P3 tests flagged duplicates that the profile already filters;
- P4, P7 and P9 are vacuous for the fitted model (Resp. 0; `results.tex:47–49`);
- P1 applies to 16 records.

The "real defect" was found in an *unfitted all-feature probe* that is never used to issue verdicts (`tables/tab_ers.tex:27`). The defect is that count features included inputs that reach no changed unit (`approach.tex:154`), which a code review of a feature whose name says "change-conditioned" should also catch. The real-execution corroboration is 5 of 7 applicable pairs, run from a dirty tree, with run directories absent (`ers.tex:106`; `reproducibility.tex:22`). The "V7-B recorded" column fails P6/P8 because a replayed stored verdict cannot react to anything (`results.tex:45`), which is a strawman rather than a finding. Tolerances δ=0.02 and ε=1e−6 are not justified, and no sensitivity analysis is given.
*Fix.* Evaluate ERS against seeded estimator defects in a mutation-analysis style: inject known estimator bugs (sign flips, counting irrelevant inputs, ignoring channels, ignoring integrity) and report the detection rate per property and the false-alarm rate on correct estimators. This would turn one anecdote into a measured capability. Add tolerance sensitivity. **New (cheap, label-free) experiments.**

## Minor concerns

1. `reproducibility.tex:41` cites `FINAL_CLAIM_EVIDENCE_REGISTER.md`, which does not exist in the manuscript directory; only `CLAIM_EVIDENCE_REGISTER.md` exists.
2. Internal project vocabulary in the body text: "V7-B", "eighth iteration of the Software Behavior Genome", branch names, commit hashes, "mac-hardening branch" (`results.tex:80, 82, 87`; `reproducibility.tex:4`). Move these to the artifact appendix.
3. Contribution C6, "Evidence audit … exclusion of a label-derived artifact" (`introduction.tex:66`), and RQ5 are project hygiene, not research contributions. The five-dataset discussion (`results.tex:144–154`; `introduction.tex:46`) can shrink to one sentence.
4. Table `tab:corpus` (`design.tex:90–95`) should separate SUSPECT_LABEL (6) from UNLABELLED (48).
5. `tab_ablation.tex:16`: the B6 row has no CI, while every other rule row has one.
6. Strict-policy rows in Table `tab:ablation` (`tab_ablation.tex:25–30`) are identical by construction and take space. Collapse them into a footnote.
7. The B2 definition (`design.tex:159`) is identical to B1 on every pair here. Say why it is kept.
8. The fitted model retains essentially one feature, yet Table `tab:profile` presents 15 features, three of them constant (`approach.tex:145–147, 152`). Report the fitted coefficients.
9. The matched-coverage algorithm divides by k (weighted target), not by the issued weight (`design.tex:189`). Confirm these coincide when eligibility is short.
10. The reliability diagram uses 5 bins of about 17 pairs (`results.tex:131`), which is too few to support any calibration statement. Consider dropping it.
11. Calling the 74 Linux runs "isolation probes" when 65 ended undecided in about 0.2 s (`results.tex:22`) suggests a harness failure. Investigate it or remove the row from Table `tab:security`.
12. Author affiliation and biography are placeholders (`main.tex:38, 68`).
13. Titles in the form of a question are discouraged by some IEEE Access editors. Consider a declarative title.
14. Definition of witness (`problem.tex:44`): "reproduced on re-execution" makes DIV depend on the determinism repeats. State how many repeats, and the treatment of LIMIT_ASYMMETRIC (22 inputs) and NO_RUN (6).

## Scores (1–10)

| Criterion | Score | Justification |
|---|---|---|
| Novelty | 4 | The reformulation is useful, but residual-risk / testability-based correctness estimation and INV/DIR/MFT behavioural testing already cover most of it, and they are uncited (M7). |
| Technical contribution | 4 | A solid engineering prototype, but the propositions are near-definitional and the predictive component did not work (M8, RQ4). |
| Literature coverage | 5 | Broad on differential testing, adequacy and selective prediction; misses Miller/Bertolino–Strigini/Böhme, JIT defect prediction, the equivalent-mutant literature and CheckList. |
| Experimental design | 4 | Matched coverage and grouped CV are good, but vacuous zero-input pairs, the wrong chance pool, a weak B1 and missing mutation/checked-coverage competitors undermine RQ3/RQ4 (M1, M2, M5, M6). |
| Statistical validity | 6 | Careful cluster bootstrap, Holm and MDE, and honest non-equivalence framing; weakened by outcome-dependent label exclusion and overstated pre-registration (M3, M9). |
| Benchmark breadth | 2 | Small synthetic Python functions plus QuixBugs whose labels share the evidence inputs; BugsInPy unlabelled; one language; nothing held out. |
| Reproducibility | 5 | Analysis is regenerable from saved records, but per-run logs and real-execution run dirs are absent, the fix sits on an unmerged branch, the cited register file is missing, and the dev corpus predates the described trust pipeline. |
| Writing | 6 | Clear and precise, with exemplary hedging, but dense with internal project jargon and self-audit material that belongs in an appendix. |
| Figures and tables | 6 | Informative and traceable, but too many (14+ tables for a pilot); strict-policy and five-dataset content is redundant. |
| Overall readiness | 3 | The headline number needs recomputation and the labels need verification before the empirical claims stand. |

## Recommendation

**Major revision.** The conceptual framing (no-divergence as a selective prediction, matched-coverage comparison against random abstention, label-free conformance checks for verdict-risk estimators) is worthwhile, and the reporting is honest. But the headline empirical results rest on:
- (i) 49 zero-input pairs counted as "no difference" (M1);
- (ii) an inappropriate chance pool that reverses the reading of RQ4 (M2);
- (iii) unverified mutant-style labels with an undisclosed outcome-dependent exclusion (M3);
- (iv) a battery-limited B1 that does not represent differential testing (M5).

M1, M2, M7, M8 (text) and M9 can be fixed without new experiments. M3(i) needs only a manual witness search over 31 pairs. M5, M6 and M10 need modest new experiments on the existing corpus. Without at least M1–M3 and M7, I would not support publication.
