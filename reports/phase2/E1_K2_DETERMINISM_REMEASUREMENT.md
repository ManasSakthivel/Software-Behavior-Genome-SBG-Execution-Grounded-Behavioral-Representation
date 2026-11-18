# E1: K2 determinism re-measurement (Phase 2 local, exploratory)

Run date 2026-11-18. Engine commit `a6afa639` (implementation `5efcef74`). Output: `results/repro/p2_e1_20261118_074906/` (gitignored `results/repro/`; raw evidence preserved, nothing under `results/raw|processed|postfix` or `artifacts/` was touched).

## 1. Objective and pre-registered hypothesis
Hypothesis (fixed in `LOCAL_EXPERIMENT_RERUN_MATRIX.md`, and the decision rule in `scripts/e1_analyze.py`, BEFORE the run): **the QUARANTINED rate does not rise after the corrected child environment and hash-seed configuration.**
Decision rule: primary metric = pair-level "at least one QUARANTINED input" on pairs driven in both runs; NOT SUPPORTED if new-only discordant pairs significantly exceed old-only (one-sided exact McNemar-form test, alpha 0.05); SUPPORTED if the new count <= old count and that test is not significant; INCONCLUSIVE otherwise. Pairs share projects, so the p-value is descriptive only.

## 2. Protocol and command
`K1_RAW=results/repro/p2_e1_20261118_074906/raw K1_PROC=results/repro/p2_e1_20261118_074906/proc .venv/bin/python experiments/v7b/k1_spike.py run` (defaults: four arms, `--rerun 25`, 4 workers, per-run limits cpu 2 s / wall 5 s as in the original spike). Then `k1_spike.py summarize` (same environment variables), `scripts/e1_analyze.py <new proc> results/postfix/processed <out.json>`, and `python -m sbgv7 verify` on every evidence directory. Comparison source: the post-fix rerun `results/postfix/processed/k1_spike_per_pair.jsonl` (read-only). Dataset: the 321 development pairs (31 QuixBugs, 85 QuixBugs-neg, 150 synthetic, 55 BugsInPy units; non-pristine), 312 driven and 9 not driven in both runs.

## 3. Environment and configuration difference
Python 3.13.15, macOS 26.7 (25G229), arm64; full record in `RUN_RECORD.md`. New child profile: `python -s -P -B`, environment allowlist with `PYTHONHASHSEED=0` actually reaching the child. **The old engine (post-fix rerun, commit 700532b8) ran the child with `-I`, which ignores `PYTHONHASHSEED`, so the hash seed was random per child**, although the spike set it in the parent environment. The two runs differ in more than the hash seed (MB-01 hex integers, MB-02 fd-1 capture, MB-05 replay/alt blocking, D-05 docstring/unmodelled handling, D-06 binding, lossy-SAME rule, MB-09 ids, MB-11 budget). Old and new figures are therefore NOT direct measurements of the seed effect; the comparison is "old engine vs current engine".

## 4. Results (denominators explicit)
| Measure | Old (post-fix rerun) | New | Denominator |
|---|---|---|---|
| Pairs with at least one QUARANTINED input | 2 | 1 | 312 driven pairs |
| QUARANTINED inputs | 3 | 1 | 3,044 inputs of those pairs |
| Discordant pairs (new-only / old-only) | | 0 / 1 | exact one-sided p(increase) = 1.0; two-sided p = 1.0 |
| Determinism-confirmed fraction, synthetic arm | 0.993 | 1.000 | 150 pairs |
| Determinism-confirmed, other arms (BugsInPy / QuixBugs / neg) | 0.978 / 1.0 / 1.0 | 0.978 / 1.0 / 1.0 | 46 driven / 31 / 85 |
| Whole-pair rerun identity (run1 vs run2) | 102 of 102 | 102 of 102 | QuixBugs 31, BugsInPy 46, neg 25; synthetic not re-run in either (the `--rerun 25` budget is consumed by the neg arm) |

QUARANTINED pairs: new `black__21__black_py__dump_to_file` (1 input; also quarantined in the old run, so it persists and is not related to the hash seed); old only `train__graph_center_finder__sp-11_s1` (2 of 11 inputs quarantined, INSUFFICIENT/nondeterministic), now NO_DIVERGENCE_OBSERVED/S2 with 0 quarantined. That pair is consistent with set-order dependence removed by the fixed seed (a plausible reading, untested: E2 is deferred).
Engine failures: none (`ENGINE_NO_VERDICT` 0). Not driven: 9 in both runs (same pairs).

## 5. Verdict distribution (312 common driven pairs) and an unexpected finding
| Verdict | Old | New |
|---|---|---|
| DIVERGENT_OBSERVABLE | 84 | 84 |
| NO_DIVERGENCE_OBSERVED/S2 | 91 | 55 |
| NO_DIVERGENCE_OBSERVED/S1 | 17 | 16 |
| INSUFFICIENT | 120 | 157 |

**63 of 312 verdicts changed; DIVERGENT_OBSERVABLE is unchanged at 84.** Transitions: 37 NDO/S2 -> INSUFFICIENT(unmodelled_change); 14 INSUFFICIENT(changed_region_not_activated) -> INSUFFICIENT(unmodelled_change); 7 changed_region_not_activated -> INSUFFICIENT(unobservable_outcome); 3 resource_limit -> unmodelled_change; 1 NDO/S1 -> INSUFFICIENT(changed_region_not_activated); 1 INSUFFICIENT(nondeterministic) -> NDO/S2. By arm the 54 `unmodelled_change` pairs split QuixBugs-neg 27, synthetic 17, BugsInPy 10.
Inspection of the evidence packages for three of them shows changed lines inside multi-line statements: a regex string literal in a `re.sub(r'''...''')` (youtube_dl `js_to_json`) and a list-literal element (`"skew",` in a pandas allow-list). The previous engine dropped such lines and issued NDO/S2, arguably a false assurance; the ratified A-U1 rule (changed lines without executable code are `unmodelled_change`, conservative) now abstains. The caveat that continuation lines of an executable statement are not mapped to the statement was recorded before the run (`MB_SECOND_STAGE_REVIEW.md`). The other transition classes were not individually inspected. This is a verdict-distribution change of the engine, not a hash-seed effect, and it matters for E3: abstention rises by 37 pairs (11.9% of driven pairs) and any false-assurance reduction must be examined against that. No code was changed.

## 6. Interpretation of the hypothesis
By the pre-registered rule the hypothesis is **SUPPORTED**: the QUARANTINED pair count did not rise (1 vs 2) and the one-sided test for an increase has p = 1.0. The evidence is weak: counts of 1 versus 2 pairs (1 versus 3 inputs of 3,044) cannot support a claim of reduction, the design is underpowered for effects this small, pairs are clustered by project, and the comparison is confounded with the other engine changes. No rise was observed. Within these limits the corrected hash-seed handling did not increase quarantine.

## 7. Limitations and anomalies
- Single machine and run; two runs per pair for 102 pairs only; the synthetic arm has no determinism rerun in either run.
- Hash-order sensitivity across seeds is untested (E2 deferred, Decision A); a fixed seed removes that variation by construction and does not show it is harmless.
- The old run used a random per-child seed, so its two QUARANTINED pairs are one draw of a random process.
- Wall-clock-dependent programs can still produce false witnesses (Decision B, `datetime.now` not virtualised).
- K2 is defined on K1 pairs under validated isolation, which is Phase 3; this measures the local exploratory engine only. No OS-isolation or tamper-proof claim is made.

## 8. Verification
`python -m sbgv7 verify` on all 414 evidence directories (312 run1, 102 run2): 414 report `"verified": true`, 0 failures (`verify_results.tsv`). The exit-code column of that file records the last command of the pipeline, not the verify exit code, so the verified field is the authority. `summarize.out` and `e1_analysis.json` agree with the raw per-pair file (counts above recomputed from it). `git status` shows no change under `results/` or `artifacts/` and no implementation file changed.

## 9. Reproduction
Check out `a6afa639`, create `.venv` per README, run the commands in section 2 into a fresh `K1_RAW`/`K1_PROC` pair of directories, then `python scripts/e1_analyze.py <proc> results/postfix/processed out.json`. Wall time about 16 minutes.

## 10. Conclusion
**Hypothesis SUPPORTED (weakly; underpowered and confounded).** This is a local exploratory measurement. It is not a confirmation that the engine is deterministic, and it does not extend to independent data or Linux.
