# Independent Red-Team Review of V7-B (branch research/v7b-final-validation)

Reviewer stance: hostile, did not build this. Read-only except this file. Everything below was either re-run by me or is flagged "read only".

## 0. What I verified myself

- `.venv/bin/python -m pytest tests/v7 -q`: **74 passed, 1 skipped** (the skip is the RLIMIT_AS test, unenforceable on macOS). Note the isolation audit still quotes "11 passed, 1 skipped", which is stale.
- Spot-checked numbers against `results/processed/`: K1 report (27/31 QuixBugs DIVERGENT, 4 INSUFFICIENT; BugsInPy units 6/16/24/9 not-driven; synthetic S2 32 / S1 13; 321 invocations) matches `k1_spike_summary.json` exactly. Baseline report (B1 29/31, 54/78 CHANGED, 17/72 EQUIVALENT; B1 CPU ~151 s, B1+rep ~543 s) matches `baselines_per_pair.jsonl`. One drift: B3 total CPU is 1424 s in the data against "about 1407 s" in the report (minor). The 321-row vs 312-row files differ only by the 9 NOT_DRIVEN class units (explained).
- CLI on a trivial pair (`x+1` vs `x+2`; `x+1` vs `1+x`): returned DIVERGENT_OBSERVABLE with a witness id, and NO_DIVERGENCE_OBSERVED S2, respectively. It works. The S2 verdict came from **two inputs**.
- Equivalence verdict: `Verdict()` in `records.py` asserts value is in a closed enum, and `decide.py` returns only DIVERGENT_OBSERVABLE, INSUFFICIENT or NO_DIVERGENCE_OBSERVED. grep finds "SAME" only as a per-input outcome, never as a pair verdict. **An equivalence verdict cannot be emitted by the code.** That is a naming guarantee, not a semantic one (see Q5, Q11).
- Reachability of NO_DIVERGENCE_OBSERVED with incomplete evidence: **yes, I reproduced it** (finding B-1 below).

## 1. What is new?

Honest answer: the integration and the discipline, not any primitive. The only thing I would call new is a replayable evidence contract (hash-chained records, closed verdict enum, structural impossibility of an "equivalent" outcome) wrapped around cross-version differential execution, with a recorded changed-region activation record that gates the "no difference" verdict. The repo's own novelty assessment concedes this (C1-C4 are "Partially novel", C2 is the "weakest", C5 is "Unsupported"). I agree with it and would not upgrade anything.

## 2. What already exists (research/literature/RESEARCH_GAP_AND_NOVELTY_ASSESSMENT.md)

- Witnesses: Beyer et al. verification witnesses; Shadow symbolic execution and Mokav emit replayable differing inputs (C1).
- Sufficiency = changed-code coverage: Hilton 2018 patch coverage, DiffTestGen union coverage of modified code, Cleverest, dynamic impact analysis papers saying results hold only for observed executions (C2).
- Abstain/unknown: DiffKemp "undetermined", regression-verification, reject option (Chow 1970, Geifman 2017) (C3).
- Repeat-to-filter-flaky: iDFlakies, DeFlaker, etc. (C4).
- Closest competitors 2024-26: Testora, DiffTestGen, Mokav, Cleverest. None was run as a baseline (baseline report, "Not implemented").
- Caveat on the assessment itself: it rests mostly on abstracts, by one reviewer. Its absence claims are not proofs.

## 3. Could conventional differential testing do the same? B1 vs B1+rep differ on 2 pairs

Largely yes, on the evidence we have. I traced the two pairs (`baselines_per_pair.jsonl` joined to `k1_spike_per_pair.jsonl`):

1. `synthetic/train__graph_center_finder__sp-11_s1` (labelled EQUIVALENT): B1 DIVERGE, B1+rep NO_DIFF. V7 says INSUFFICIENT(nondeterministic).
2. `bugsinpy_units/black__21__black_py__dump_to_file` (REAL_BUGFIX): B1 DIVERGE, B1+rep NO_DIFF. V7 says INSUFFICIENT(nondeterministic).

What this implies:
- The entire marginal effect of V7's replay/determinism machinery, over 311 pairs driven in both, is **2 pairs, both nondeterminism filters that plain "run it 3 times" also gets**. B1+rep is the null model for V7 minus sufficiency, and it differs from B1 on 0.6% of pairs. The replay/control-alternation apparatus (r_replay=5, k_alt=3) shows no measurable value on this data. Note k_alt is excluded from B1+rep, but no V7 witness was demoted to ENV_SENSITIVE in the data I saw, so I cannot show k_alt earns anything.
- V7 is not a detection gain. V7 DIVERGENT_OBSERVABLE count is 83 over the 321 pairs. B1 DIVERGE is 139 (29+7+71+32). The report says "V7 witnesses never missed by B1". Most B1 extras are renamed-entry artefacts that V7 refuses (`unsupported_signature`, 49 pairs), i.e. V7 is cleaner there but only because the V7 engine lacks rename support, and the result is a refusal rather than a finding.
- V7 costs about 3x B1 CPU (455 child-only vs ~151) and B1+rep about 543 for the same protection.
- The one place V7 does something B1+rep cannot is the sufficiency gate (next question).

## 4. Does sufficiency add measurable value?

**No evidence that it does; some evidence that it does not discriminate.** No pair has an independent ground truth, so FAR, the claimed headline metric, is not computable on anything produced so far.

The only proxy available is the synthetic arm (labels from the transformer, "CHANGED" vs "EQUIVALENT", explicitly not adjudicated; K1 finding 3 shows labels are wrong in at least 2 cases). Among pairs where B1 reports NO_DIFF (n=79 CHANGED+EQUIVALENT in the synthetic arm, 24 CHANGED):

| V7 outcome on B1-NO_DIFF synthetic pairs | CHANGED | EQUIVALENT | share CHANGED |
|---|---|---|---|
| NO_DIV S2 | 8 | 24 | 25% |
| NO_DIV S1 | 5 | 8 | 38% |
| INSUFFICIENT | 11 | 23 | 32% |

If sufficiency carried signal, S2 should be markedly purer in EQUIVALENT than INSUFFICIENT. It is not (25% vs 32% changed; wrong direction for S1). Small n and noisy labels mean this is not proof either way, but it is the only data, and it is not supportive. In BugsInPy units (real fixes with synthetic battery inputs), V7 returned 16 NO_DIVERGENCE_OBSERVED (15 at S2) on pairs that are, by construction, real bug fixes: 16 of 46 driven pairs got a "no difference" verdict where a difference exists. That is a 35% rate of potentially false assurance at S2, with labels that are real (the bug fix does change behaviour on some input), though the battery inputs may not reach it.

Second problem: sufficiency is **line coverage of changed lines plus 80% branch direction coverage**, with no dependence on input count or diversity. My two-input example earned S2. `s2_all_channels_instrumented` is a hardcoded `True` in `decide.py`. Third: S3 is disabled and S1/S2 thresholds (0.80) are admitted UNVALIDATED defaults. The "calibration claims" (miss-rate caps S1 0.35, S2 0.20) have not been tested.

The 40% INSUFFICIENT rate in several arms comes mostly from engine gaps (renames 49, generators, class units), not from a meaningful sufficiency judgement. Counting those as "honest abstention" would be misleading.

## 5. Are verdicts operational?

Mostly yes as software. The enum is closed, reason codes are ranked, records are content-addressed and hash-chained, reruns are deterministic (0 diffs on all 139 re-run pairs). Semantically weak in three ways:
- NO_DIVERGENCE_OBSERVED is operationally "the harness saw nothing", not an assurance, and the S-levels have no calibration.
- Spec reason codes never produced: `ambiguous_entry`, `unmodelled_change`, `unsafe_program` (except trace tamper), `blind_spot_dominant`; so the INSUFFICIENT vocabulary is partly aspirational.
- Level S2 appears to a user as a quality grade though it is uncalibrated.

## 6. Is evidence grounded?

Partly. Each verdict resolves to run/observation records; I verified the chain exists (the tests and `records.trace`), not independently re-derived. Gaps: no Merkle tree (flat hash), no event-stream storage, dependency byte-identity check covers the source file only, control alternation virtualises only `random.seed` and `time`, `os.write(1)` and subprocess output bypass capture, and every macOS record carries `policy_below_minimum=true` (spec says such runs are synthetic/benchmark-only grade). Isolation does not confine reads and a `setsid()` child escapes the group kill (audit, "known gaps").

## 7. Is the benchmark independent?

No, and the repo says so. Every pair used is burned or developer-owned (QuixBugs, BugsInPy, v8/v10 synthetic scored by V5/V6). The BugsInPy "units" run on a synthetic battery, not the project tests. QuixBugs counted as 1 project; K1 (>=100 runnable pairs, >=8 projects, project-level runs) is **NOT MET**, and the K1 report says so. No sealed holdout exists; the independence audit declares everything non-pristine. The baseline B4 threshold and B5 threshold were tuned on development material; B5 is a lookup of V6 scores on different inputs and covers 237 of 321 pairs. Truth-team labels, kappa and the leakage audit do not exist yet (K5).

## 8. Is it powered?

No. No confirmatory sample exists. The protocol's own simulation says 40 projects / 160 pairs gives **63% power at +10pp and 22% at +5pp** (central case). The K5 gate (>=60 projects, >=250 independent divergent pairs) is not approached; the real-pair count so far is 12 BugsInPy projects (units) plus one QuixBugs "project". With fewer than about 15 projects the SAP itself says CIs undercover and the study stays exploratory. The headline claim (+10pp over same-budget differential testing) is also in tension with section 3: on current data the sufficiency-free baseline B1+rep tracks V7 on every detection outcome.

## 9. Does it generalise?

Nothing supports it. Python top-level functions with JSON-representable args, macOS sandbox-exec only, single machine, CPython 3.13 only. Not supported: classes/methods (8 BugsInPy class units not driven), tuples/sets/objects as inputs, declared renames, generators (flatten, kheapsort run no body, K1 finding 1), multi-file projects, third-party repos. Network/file/stateful programs only via declared side effects. No cross-language claim is available (Java needs a different tool). LLM-era baselines not tested.

## 10. Are the conclusions supported?

The repo's own "Not claimed" lists are honest and consistent with the data. The conclusions that are supported: the tool builds, runs, is deterministic, never crashed on 321 invocations, and refuses to say "equivalent". Not supported: any statement that sufficiency or replay improves outcomes, any FAR/detection rate, any "better than differential testing". I note the README still carries V5/V6-era headline claims (AUROC 0.897, "Supported" rows) that are not about V7-B and use developer-authored benchmarks; they must not be conflated with V7-B.

## 11. Would an IEEE Access reviewer reject?

Yes, as a *validation* paper; likely accept-with-major-revision at best as a *design + feasibility* paper (and IEEE Access is lenient on that). Reasons a reviewer would give:
1. No independent ground truth, no sealed holdout, K1 failed; a system of "what was not observed" is evaluated only on burned data.
2. The central novelty (sufficiency) has no measured value, the null baseline (B1+rep) matches, and the one contrast (2 pairs) is solved by repetition.
3. Prior art (Shadow, DiffTestGen, Testora, Mokav, DiffKemp, patch-coverage) not run as baselines; "we found none" claims rest on abstracts.
4. Sufficiency is coverage with unvalidated thresholds (a known contested proxy: Inozemtseva & Holmes; Just 2014).
5. Platform below the spec's own minimum isolation grade; no Linux/container path.
6. Underpowered by own analysis.
7. 16/46 real-fix pairs received "NO_DIVERGENCE_OBSERVED" on a synthetic battery, undermining the abstention narrative.

## Issues by severity

### Blocking
- **B-1: NO_DIVERGENCE_OBSERVED is reachable with an incomplete input.** `decide._blockers` maps outcomes CONFIRMED_DIFF, UNCONFIRMED_DIFF, ENV_SENSITIVE_DIFF, QUARANTINED, LIMIT_ASYMMETRIC to blockers, but **NO_RUN has no entry** (decide.py, code map). I reproduced: `inputs=[SAME, NO_RUN]` with all changed units hit returns `('NO_DIVERGENCE_OBSERVED','S2',None)`. `runner.process_input` emits NO_RUN when both sides hit a resource limit, or on a harness/import failure *per call*. The import-failure path adds a `stat` blocker separately, but the both-sides-timeout path adds none. So an input that timed out on both versions is silently dropped from the verdict. This contradicts the module's own "missing records are blockers" claim. It is a one-line fix plus a regression test, but it breaks the central safety property and must be fixed before any result is reported.
- **B-2: No evidence sufficiency adds value, and no ground truth exists to test FAR.** Section 4. The paper's core claim is untested.
- **B-3: K1 not met; no independent benchmark.** Section 7.

### Major
- M-1: B1+rep differs from B1 on 2 pairs; V7 machinery adds ~0 over cheap repetition (section 3).
- M-2: S2 can be obtained from 2 inputs; levels ignore input count/diversity; `s2_all_channels_instrumented` is hardcoded True.
- M-3: 16/46 real-fix BugsInPy units get NO_DIVERGENCE_OBSERVED (15 at S2). With battery inputs not designed for the bug this is the expected failure mode and S2 does not stop it.
- M-4: Closest competitors (Testora, DiffTestGen, Mokav, Shadow, DiffKemp) not run; B3 is a minimal mutation loop, not a fuzzer; B2/B5 cover part of the pairs.
- M-5: Engine coverage gaps drive INSUFFICIENT (renames 49, generators, class units 8), inflating "abstention" without semantic meaning, and making V7 vs B1 comparison unfair in both directions.
- M-6: macOS-only, `policy_below_minimum=true` on every record; reads unconfined; `setsid` escape untested.
- M-7: Underpowered per own simulation (63% at +10pp for 40 projects).

### Moderate
- Mo-1: Synthetic EQUIVALENT labels are "equivalent under looser equality" (2 witnesses on EQUIVALENT-labelled pairs; 8 unadjudicated).
- Mo-2: Budget exhaustion is a blocker only if changed units remain unhit; stopping at the budget with unrun inputs but covered lines still yields NO_DIV (stop_reason recorded but not gating).
- Mo-3: Empty changed region (`r_empty`) yields vacuous activation and can still reach NO_DIV (spec-sanctioned, not stratified in code).
- Mo-4: Control alternation virtualises only `random.seed` and `time`; uuid/os.urandom/env unvirtualised, so ENV_SENSITIVE detection is partial.
- Mo-5: B4 and B5 thresholds fitted on dev material; B5 not input- or budget-matched; V7 parent-CPU overhead unmeasured ("lower bound").
- Mo-6: Output and tamper: `os.write(1)`/subprocess output bypass capture.

### Minor
- Mi-1: Stale numbers in docs (isolation audit "11 passed"; B3 CPU 1407 vs 1424).
- Mi-2: README carries V5/V6-era headline claims on the same page as V7-B framing.
- Mi-3: Branch coverage counts only POP_JUMP_IF/FOR_ITER/SEND with a conservative denominator (can under- and over-state).
- Mi-4: No LaTeX toolchain here; manuscript not compiled or reviewed by me.

## Claims the manuscript and README must NOT make

1. Any statement that V7-B (or its sufficiency level) *reduces false assurance*, improves detection, or beats differential testing / any named published tool.
2. Any "equivalent", "same", "safe", "verified", "no bug" reading of NO_DIVERGENCE_OBSERVED, and any probability/confidence attached to S1/S2.
3. That S1/S2 thresholds are calibrated or that "S2 means 80% of changed branches' directions are validated as behaviourally safe".
4. That the K1 or K2 gates pass, or that real-project feasibility is shown (K1 NOT MET; BugsInPy runs are units on synthetic inputs).
5. That replay (r_replay=5, k_alt=3) or the environment-sensitivity check adds value over B1+rep (2 pairs, both plain flakiness).
6. That QuixBugs/BugsInPy/v8/v10 results are evidence; they are smoke/development only.
7. "First", "novel" or "state of the art" for witnesses, sufficiency, abstention, or flaky-aware comparison.
8. Any cross-platform, cross-language, or "isolated execution of untrusted code" claim (macOS sandbox-exec, below spec minimum).
9. That 100% determinism or zero crashes shows correctness; it shows the harness is stable on 321 development pairs.
10. That INSUFFICIENT rate is evidence of honest abstention: it is dominated by unimplemented engine features.
11. Reusing V5/V6 AUROC claims as V7-B results.

## Recommended readiness verdict

**B. Publishable only as a design/feasibility/negative-result report; not ready as a validation paper.** Required before any submission framed as validation (would move it toward a C-to-A path): fix B-1 and add the regression test; produce independent labelled real pairs (K5) with a kappa-checked truth team; measure FAR of V7-B vs B1+rep on them; run at least one external baseline (Testora/DiffTestGen/Mokav-class) or drop competitive claims; implement renames/generators/class units so INSUFFICIENT means something. If the author wants to claim sufficiency as a contribution, the FAR comparison against B1+rep is the decisive experiment, and my reading of current data predicts it will show no gain. If forced to choose among A (ready), B (feasibility/design paper only), C (not ready, stop/pivot): **B**, with the honest alternative that the claim should be reframed as an evidence-contract for differential testing rather than a sufficiency advance.
