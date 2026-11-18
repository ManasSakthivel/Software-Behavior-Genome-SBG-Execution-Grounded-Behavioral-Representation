# Phase 2 consolidated experimental analysis (local, exploratory)

Campaign date 2026-11-18, implementation `5efcef74` (the `sbgv7/` and `tests/` sources are byte-identical in every later commit: `a6afa639` for E1, `ee4749bc` for E3-E6 per their RUN_RECORDs), macOS 26.7 / Apple M4 Pro (arm64), CPython 3.13.15, `PYTHONHASHSEED=0` in every child. All data are the existing 321 development pairs (31 QuixBugs, 85 QuixBugs-neg, 150 synthetic, 55 BugsInPy units; 9 not driven; 258 pairs enter the primary denominators after excluding 57 UNLABELLED and 6 SUSPECT_LABEL). **Non-pristine data, no independent holdout: every result below is exploratory.** Nothing here supports independent generalisation, confirmation, OS-isolation, tamper-proof evidence or complete determinism. E2 (hash-order sensitivity) was deliberately not run and remains untested.
Pre-registration: `E3_E7_PROTOCOLS.md` and `LOCAL_EXPERIMENT_RERUN_MATRIX.md` (committed before E3 ran). Compact outputs: `results/v7b_phase2_summary/`; raw evidence archives (sha256 in `RAW_ARCHIVE_SHA256SUMS.txt`) outside the repository.

## 1. Experiment summary
| Exp | Objective | Dataset / config | Result (headline) | Verification | Limitations |
|---|---|---|---|---|---|
| E1 | K2: QUARANTINED rate not higher after hash-seed/env fix | 312 driven pairs, old (`-I`, random seed) vs new engine | **Supported (weak)**: 1 vs 2 pairs; 1 vs 3 of 3,044 inputs; p(increase)=1.0 | 414/414 `verify` verified | confounded (other MB fixes), tiny counts, no seed variation |
| E3 | Detection / false assurance / abstention vs baselines | 258 labelled pairs, B1, B1+rep, B3, B4 | FA 0.123 vs 0.226; detection 0.708 vs 0.774; abstention 0.473; **FA reduction entirely abstention** | V7-B verdicts identical to E1 run1 (321/321) | non-pristine; +10pp rule not met |
| E4 | Component ablations V1-V5 | same pairs, 5 variants | **No verdict change** from any ablation except one reason code | V0 equals E3 on 320/321 strict (1 witness id) | data has almost no nondeterminism; cannot show component value |
| E5 | S2 floor 0.6/0.8/0.9 | same pairs | verdict values identical; S2 share 71/55/43 | monotone check passed | floor only relabels S1/S2 |
| E6 | Runtime cost | 40-pair subset, 5 reps, two runs | V0 ~1.6x B1 (wall; CPU 1.7x); ~1.02x B1+rep | 0 failed jobs | load above limit, battery power |
| E7 | Verify every verdict; corruption suite | 828 directories; 42 corruption cases | 828/828 verified; 42/42 as expected | by construction | verify recomputes recorded facts, executes nothing |

## 2. E1: K2 determinism re-measurement
See `E1_K2_DETERMINISM_REMEASUREMENT.md`. Pre-registered rule outcome SUPPORTED; the child profile changed from `-I` (random hash seed regardless of the parent environment) to `-s -P -B` with an allowlisted environment that pins `PYTHONHASHSEED=0`, together with other engine changes, so the comparison is old engine versus current engine, not a clean seed effect. Counts: 1 of 312 pairs quarantined versus 2; 1 of 3,044 inputs versus 3. The one pair that left quarantine (`graph_center_finder__sp-11_s1`) is consistent with set-order dependence, untested. One pair (`black__21__black_py__dump_to_file`) is quarantined in both and is not a hash-seed effect. Run1 versus run2: 102 of 102 identical.

## 3. E3: detection, false assurance, abstention (n = 106 divergent, 152 non-observed-difference, 258 total)
Project-level cluster bootstrap (78 and 69 projects), 10,000 resamples, seed 42; sign-flip primary test; exact McNemar sensitivity; Holm over 4 comparisons x 2 primary outcomes.
| System | False assurance | Detection | Abstention | False alarm |
|---|---|---|---|---|
| B1 | 24/106 = 0.226 [0.119, 0.392] | 82/106 = 0.774 [0.609, 0.881] | 0/258 | 46/152 = 0.303 |
| B1+rep | identical to B1 (0 discordant pairs) | identical | 0 | 0.303 |
| B3 | 20/106 = 0.189 [0.097, 0.337] | 86/106 = 0.811 [0.663, 0.904] | 0 | 0.309 |
| B4 (edit size) | 0.991 | 0.009 | 0 | 0.007 |
| V7-B | 13/106 = 0.123 [0.054, 0.236] | 75/106 = 0.708 [0.545, 0.816] | 122/258 = 0.473 [0.353, 0.524] | 0/152 |

V7-B minus B1 (paired, 106 divergent pairs): false assurance -10.4pp, 95% CI [-20.5, -4.3], 0 V7-B-only versus 11 B1-only, sign-flip p = 0.0010, exact McNemar p = 0.0010, Holm p = 0.0059; **the +10pp effect-of-interest rule is not met** (lower bound -4.3pp), so the wording is "reduced by about 10pp, not shown to reach 10pp". Detection: -6.6pp [-11.5, -2.6], 0 versus 7, sign-flip p = 0.031, **Holm p = 0.156, not significant after correction**; reported as a possible loss, not an established harm. Abstention +47.3pp (122 versus 0; Holm p = 3e-4; this is by design). False alarm 0 versus 0.303. All p-values are descriptive: pairs cluster by project (largest cluster 29 pairs), several labels are synthetic, and the data are non-pristine, so they are not evidence of generalisation. B3 versus B1 is not significant (sign-flip p = 0.125 for both false assurance and detection, Holm 0.5). `statistics/power_actual.json` is a design-property simulation, not post-hoc power at the observed effect.
**Is the false-assurance reduction explained by abstention? Yes, entirely, on this data.** Of the 24 divergent pairs that B1 (and B1+rep) wrongly pass, V7-B returns INSUFFICIENT for 11 and NO_DIVERGENCE_OBSERVED for 13; it detects none that B1 misses (0 test-only). On the 88 divergent pairs where V7-B does not abstain, V7-B detects 75 and misses 13, and B1 detects the same 75 and misses the same 13. The pre-registered attribution statistic is 11 of 11 (cluster bootstrap interval degenerate at [1, 1] because all 11 recovered cases are INSUFFICIENT; with n = 11 this is not a precise estimate). V7-B's advantage is therefore calibrated abstention, not extra detection. Risk-coverage (decided NO_DIVERGENCE verdicts): coverage 0.527 for any level (the 0.096 'risk' is 13/136 and mixes 75 detections with 61 NO_DIVERGENCE verdicts; the error rate of NO_DIVERGENCE verdicts is 13/61 = 0.213 for V7-B versus 24/130 = 0.185 for B1, so the gate gives fewer, not more reliable, no-difference calls; abstention is selective: 11/24 B1 false assurances versus 7/82 B1 detections became INSUFFICIENT, Fisher one-sided p about 1e-4); at S2 or higher coverage 0.465, risk 0.067; the S3 row of the risk-coverage table (coverage 0.291, 75 decided, risk 0) contains only witnessed divergences, because S3 is refused by configuration and no NO_DIVERGENCE_OBSERVED verdict is issued at that level.
Derived (not executed) sufficiency-gate counterfactual: relabelling every INSUFFICIENT as NO_DIVERGENCE_OBSERVED would raise false assurance from 13 to 31 of 106 (0.293); relabelling only gate-attributable reasons gives 24 of 106 (0.226, equal to B1): the gate is what lowers false assurance.
**Change relative to the earlier (post-fix) run.** Detection and false assurance did not change (0.708, 0.123), baselines are identical, but abstention rose from 0.360 to 0.473 because 54 pairs now return `INSUFFICIENT(unmodelled_change)` (changed lines without executable code, in the cases inspected continuation lines of multi-line statements such as regex literals or list-literal elements, which the previous engine ignored). This is the ratified conservative rule (A-U1) and it is unrefined: continuation lines of an executable statement are not mapped to the statement. Part of the abstention may be noise of that rule; refining it is a design decision not taken here (UD-2 remains open).

## 4. E4: ablations
Variants (config deltas via `python -m sbgv7 compare`): V1 `r_det=1`, V2 `r_replay=1`, V3 `k_alt=0`, V4 all three, V5 `FOLD_FD1=False`. All variants executed (run records: V0 13,764; V1 5,930; V3 13,250; V4 4,746). **No variant changes the verdict value or level on any of the 321 pairs**; detection, false assurance, abstention and false alarm are identical (all paired p = 1.0, no discordant pairs). The only observable difference is one reason code: `black__21__black_py__dump_to_file` moves from `nondeterministic` to `flaky_witness` under V1 and V4 (both INSUFFICIENT). Witness ids change under V2-V4 because the replay set is part of the witness (84 pairs). Interpretation limits: the dataset contains almost no intermittent or control-sensitive behaviour (E1: 1 of 312 pairs), so confirmation machinery has nothing to filter; this experiment can show a cost (V4 uses about 65% fewer runs for the same verdicts here) but cannot show the value of the components, and component importance must not be inferred. Hash-order sensitivity is untested.
**Run-to-run anomaly.** One pair (`quixbugs/longest_common_subsequence`) has a different witness id in E4-V0 than in E1 and E3: input i3 sits at the 2 s CPU limit and hit it on one side in one run (LIMIT_ASYMMETRIC), so a later input became the witness. The verdict (DIVERGENT_OBSERVABLE) is unchanged, but witness identity is timing-dependent for inputs near a resource limit. Strict-key consistency: E1 vs E3 321/321; E3 vs E4-V0 320/321 (within the pre-registered tolerance of 3).

## 5. E5: S2 branch-coverage floor
Floors 0.6, 0.8, 0.9, run separately. Verdict values identical at all floors (0 flips of value). NO_DIVERGENCE_OBSERVED/S2 count: 71, 55, 43 of 71 (S1: 0, 16, 28), monotone as pre-registered. Detection (0.708), false assurance (0.123) and abstention (0.473) are identical at all floors, and so are the comparisons with B1: the pre-registered "headline stable" criterion holds. The floor does not change whether a verdict is issued, only the S1/S2 label, so stability is a property of the decision rule, not evidence that 0.8 is well chosen. No threshold was selected retrospectively.

## 6. E6: runtime
Fixed 40-pair subset (seed 20261118; quotas 8/8/16/8), 5 repetitions, sequential, fresh process per job; Apple M4 Pro, 14 cores, 48 GiB; **on battery power**. Both runs were flagged by the pre-registered load rule (run 1 load average 4.81 at start, 1.65 at end; the repeat 1.44 at start, 2.24 at end; transient spikes to 62 and 13 from other applications); 0 failed jobs; both runs are reported.
| | Run 1 | Run 2 |
|---|---|---|
| V0 median wall per pair (s) | 2.075 | 2.067 |
| B1 median wall (s) | 1.310 | 1.308 |
| V0/B1 wall, median ratio [95% CI] | 1.595 [1.584, 1.742] | 1.598 [1.586, 1.736] |
| V0/B1 CPU | 1.718 [1.706, 1.844] | 1.716 [1.706, 1.836] |
| V0/B1+rep wall | 1.018 [1.014, 1.072] | 1.018 [1.015, 1.071] |
| median CV across 5 reps (V0 wall) | 0.48% | 0.65% |
V0 costs more than B1 (the CI excludes 1) and about as much as B1+rep. Peak RSS (tree maximum measured by the driver): median about 26 MiB (V0) and 28 MiB (B1), maximum about 700 MiB for one pair. Wall times from the E3 baselines stage (reported 20,880 s, apparently a machine suspend) are not used. Per-run RSS is not logged by the engine.

## 7. E7: verification
`python -m sbgv7 verify` returned exit 0 for all 828 evidence directories (E3 and E1, run1 and run2), covering DIVERGENT_OBSERVABLE, NO_DIVERGENCE_OBSERVED/S1 and /S2, and INSUFFICIENT with every reason produced (E1 counts: changed_region_not_activated 56, import_error 2, nondeterministic 2, resource_limit 6, unmodelled_change 70, unobservable_outcome 16, unsupported_signature 58; divergent 117, S1 17, S2 70, counted over run1 and run2). Corruption suite on copies: 42 of 42 as pre-registered (byte flip, truncation, record deletion, missing package, broken chain, edited verdict.json, deleted log exit 2, simulated size-cap omission exit 4, no-rechain control exit 1). The documented limitations behave as predicted and are not detected: a writer who edits unverified fields (run timings, run status/detail) and recomputes the chain and `log_head` produces a log that verifies, and a deleted `verdict.json` is not detected. `verify` recomputes recorded facts and executes nothing, so it does not detect a lie in a recorded observation. The plaintext hash chain is not tamper-proof; a trust anchor (pinned `log_head` or signature held outside the log) is Phase 3.

## 8. Statistical status of findings
- Statistically supported (descriptive, clustered, exploratory): V7-B has lower false assurance than B1 on these data (Holm p = 0.0059, effect 10.4pp, +10pp rule not met) (false alarm 0/152 versus 46/152 is an artefact, see below); the false-assurance reduction is fully attributable to abstention (11 of 11) and to B1's lack of a sufficiency gate.
- Descriptive: detection 0.708 versus 0.774 (not significant after Holm); abstention 0.473; runtime ratios 1.6x and 1.02x; E5 stability; E4 invariance.
- Exploratory: attribution to specific mechanisms (unmodelled_change, set-order dependence).
- Inconclusive: any effect of the hash-seed change on determinism (1 versus 2 pairs); component value (no nondeterminism in the data).
- Unsupported: independent generalisation, any superiority claim beyond these 258 non-pristine pairs, comparisons with published tools (not run), OS-isolation, tamper-proof evidence, complete determinism, hash-order robustness.
Multiple comparisons: Holm within each pre-registered family (E3: 8 tests; E4 and E5 their own families); no p-value here is a claim of significance across the campaign.

## 9. Protocol deviations and anomalies (disclosed)
1. E3: the first attempt via `run_evaluation.sh --full` was killed after 77 CPU-minutes in the legacy `pytest tests -q` stage (unrelated V5/V6 tests); a second attempt aborted at the test stage on a docs-wording guard that my new risk register tripped (fixed); the reported E3 run replaces that stage with `pytest tests/v7 tests/v6` (286 passed, 1 skipped) and runs all other stages as in `--full`. Failed attempts are recorded in `RUN_RECORD.md` files; no data was produced by them.
2. E6 was flagged by the load rule, repeated once, both reported; machine on battery power.
3. The E3 baselines stage wall time is a suspend artefact and is not used.
4. E1's verify log column recorded the pipeline exit status; the `"verified": true` field is the authority (414/414); E7 re-verified with real exit codes (828/828).
5. Raw evidence is archived outside git (sha256 listed); compact outputs are tracked in `results/v7b_phase2_summary/`.
6. No implementation code was changed during the experiments; historical results and `artifacts/` are unchanged.

## 10. Remaining Phase 3 requirements
Linux/Docker isolation verification, K1 real-pair feasibility (>= 100 runnable real pairs, >= 8 projects) and K5 (>= 60 projects, >= 250 adjudicated divergent pairs, kappa >= 0.7), independent benchmark collection and holdout, comparison with published tools under a fair design, hash-order sensitivity (E2) and seed variation, a trust anchor for the evidence log, refinement of `unmodelled_change` (UD-2), and re-measurement of K1/K2 on validated isolation.

## 11. Post-review corrections (independent red-team review, see PHASE2_FINAL_RED_TEAM_REVIEW.md)
- False alarm 0/152 versus 46/152 is not a finding: all 46 B1 false alarms are `renamed_entry_SP-2` pairs (B1 treats a missing entry as a difference); V7-B abstains on all 48 such pairs. The pre-declared sensitivity excluding these pairs (E3_E7_PROTOCOLS.md) was **not run**: a protocol deviation, recorded here; on the other 104 negatives B1 has 0 false alarms and V7-B abstains on 56.
- Detection loss versus B1: CI [-11.5, -2.6] excludes zero although Holm p = 0.156; reported as a possible loss.
- All 24 B1 false assurances are synthetic generator labels and QuixBugs detection uses the declared tests that also supply inputs (near circular): false assurance is partly 'generator said changed, sampled inputs showed nothing'. No coverage-matched or coverage-gated baseline was run.
- The risk column of the risk-coverage table mixes detections and no-difference calls; the S3 row contains only witnessed divergences.
- The numerical-claim check in the manuscript folder is an internal consistency check (it rereads the same tracked CSVs), not independent verification.
