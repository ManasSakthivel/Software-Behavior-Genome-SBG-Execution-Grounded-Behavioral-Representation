# K1/K2 feasibility spike for sbgv7 (DEVELOPMENT / EXPLORATORY)

Date 2026-11-17. Branch research/v7b-final-validation. Every dataset used here is non-pristine (QuixBugs and BugsInPy are burned; v8/v10 synthetic pairs were scored by V5/V6). Nothing below is an independent result, a detection rate, or evidence for or against any claim. No thresholds were tuned. Per-pair values come from the engine; labels were not given to it.

Scripts: `experiments/v7b/k1_spike.py` (run, then summarize). Raw: `results/raw/k1_spike/<arm>/<run1|run2>/<pair>/` (evidence.jsonl, verdict.json, inputs, cfg). Processed: `results/processed/k1_spike_per_pair.jsonl`, `results/processed/k1_spike_summary.json`. Engine invoked only through `python -m sbgv7 compare` (sandbox-exec child per run), OMP_NUM_THREADS=1, 4 workers. No stray processes remain.

## Setup and deviations
- Platform: macOS, CPython 3.13.15 (also 3.12/3.11/3.9 present via uv; no BugsInPy-era interpreters or project repos). Docker CLI present, daemon down; sbgv7 has no Linux-container path. Every record carries `policy_below_minimum=true`, so all runs are benchmark-only grade per spec section 10.
- Config: spec defaults except per-run limits cpu 2 s / wall 5 s (spec `fast_cpu_s`); the default 10/20 s made one infinite-loop pair cost 60 s. Budget 60 CPU-s per pair, at most 12 inputs per pair.
- Inputs: QuixBugs from `json_testcases` (args only; expected outputs not used). Synthetic and BugsInPy-unit inputs come from the existing label-free `entry_policy.select_entry_structural` battery (tuples cast to lists). Entry name is the base entry for both sides (declared renames are not implemented in the engine).

## Arms
| Arm | Pairs | Notes |
|---|---|---|
| quixbugs (buggy vs fixed, declared inputs) | 31 | all 31 declared-eligible of 40 programs; 9 have Node/object inputs |
| quixbugs_neg (fixed vs SP variant, synthetic label EQUIVALENT) | 85 | only the 31 eligible programs |
| synthetic (v8+v10, <=1 EQUIVALENT + 1 CHANGED per base program, seed fixed) | 150 | 101 base programs |
| bugsinpy_units (extracted single-file units, synthetic battery inputs, NOT project runs) | 55 | 12 projects; 8 class units and 1 unsynthesisable not driven |

## K1 measurables
Spec text: K1 = >=100 runnable pairs from >=8 projects (fail = STOP). The spec does not define "runnable"; I use: both versions imported, entry resolved, at least one input executed (verdict not import_error / unsupported_signature / alignment_failed / tool_error / sandbox_failure / no_inputs). The spec's unit of independence is the project (benchmark protocol section 2; K5 counts projects). QuixBugs is 40 small independent programs from one benchmark and one repository: I count it as ONE project (a generous reading would count programs, but the protocol collapses by project/lineage). Synthetic pairs are not real pairs and do not count toward K1.

| Real-pair source | Pairs | Runnable | Projects (runnable) |
|---|---|---|---|
| QuixBugs buggy/fixed | 31 | 30 | 1 |
| BugsInPy extracted units (synthetic inputs; not a project-level run) | 55 | 44 | 12 |
| Total | 86 | 74 | 13 (1 + 12) |

Statement: **K1 is NOT MET on existing data** (74 runnable real pairs < 100 even with BugsInPy units counted, and those units are not project-level runs, run on synthetic rather than project-test inputs; counting QuixBugs as one project, project-level runs number 0 of the >=8 needed). **K1 as intended (real projects driven by their own tests) CANNOT BE ASSESSED on this machine**: no Linux container isolation (daemon down, not implemented), spec forbids running third-party repos outside Linux isolation, project repos and their period-correct interpreters/dependencies are not present, and I did not install or clone anything. This is data/infra-limited, not evidence about the engine's ability on projects.

## Verdict, sufficiency and reasons (run1)
| Arm | DIVERGENT | NO_DIV S2 / S1 | INSUFFICIENT | Not driven |
|---|---|---|---|---|
| quixbugs (31) | 27 | 0 / 0 | 4 | 0 |
| quixbugs_neg (85) | 1 | 47 / 3 | 34 | 0 |
| synthetic (150) | 50 | 32 / 13 | 55 | 0 |
| bugsinpy_units (55) | 6 | 15 / 1 | 24 | 9 |

INSUFFICIENT fraction and primary reasons: quixbugs 13% (resource_limit 2: bitcount and sqrt loop forever in the buggy version, one-sided limit; changed_region_not_activated 2: flatten and kheapsort are generator functions, see findings). quixbugs_neg 40% (unsupported_signature 31: SP-2 renamed the entry, engine has no declared-rename support; changed_region_not_activated 3). synthetic 37% (changed_region_not_activated 34, unsupported_signature 18 [renamed entries], resource_limit 2, nondeterministic 1). bugsinpy_units 44% of all, 24 of 46 driven (changed_region_not_activated 21, nondeterministic 1 [black dump_to_file], import_error 1, unobservable_outcome 1); activation failures here mean the synthetic battery did not reach the changed lines, expected for inputs not written for the bug.

## K2 measurables (indicative only: K2 is defined on K1 pairs under D10 isolation, which is not satisfied)
- Determinism-confirmed (no quarantined/nondeterministic input): quixbugs 100%, bugsinpy_units 98%, synthetic 99%, quixbugs_neg 100%. Spec floor 70%.
- Crude activation (witness found, or all changed units hit): quixbugs 90%, bugsinpy_units 33% (15 of 46 driven; below the 35% floor on its own), synthetic 65%, quixbugs_neg 60%. Pooled real pairs (QuixBugs + BugsInPy units): about 56% (43 of 77). The 35% floor is "replay+crude activation"; I did not implement the replay baseline, so this is the engine's own activation, not the K2 quantity.
- Determinism of the engine itself: whole-pair rerun with identical inputs gave identical verdict, level, reason codes and witness id for all 31 QuixBugs pairs, 46 BugsInPy-unit pairs, 25 quixbugs_neg and 37 synthetic pairs (0 differences).
- Wall time per pair (4 workers in parallel): median 2.2 s (quixbugs), 3.7 s (bugsinpy_units), 3.5 s (synthetic); worst 20 s (infinite-loop pairs hitting per-run wall limit).

## Engine crashes
None: all 321 invocations produced a verdict (exit 0); no `ENGINE_NO_VERDICT`, no tracebacks. No engine fix and no new regression test were made or needed.

## Findings worth acting on (not crashes)
1. Generator entries: a generator function's return value is a generator object that the harness compares without consuming, so the body never runs and changed lines are unhit (QuixBugs flatten, kheapsort: all inputs SAME, then `changed_region_not_activated`). The engine fails safe (INSUFFICIENT), but it needs a harness declaration (materialise generators) before generator programs can yield witnesses.
2. Renamed entries (SP-2) are 31 of 85 quixbugs_neg and 18 of 150 synthetic INSUFFICIENT: `unsupported_signature(entry_missing)`. Declared-rename support is unimplemented (documented gap), so this strata cannot be scored until it exists.
3. Boundary strictness: levenshtein SP-6 labelled EQUIVALENT yields a confirmed witness because the rewrite returns `bool` where the original returns `int` (type tag is identity by spec). A second labelled-EQUIVALENT synthetic pair (test__math_count_set_bits__sp-11_s2) also gets a witness. Neither was adjudicated; they show the synthetic EQUIVALENT label is "equivalent under looser equality", not "no observable difference" under the V7 boundary.

## Confusion tables (DEVELOPMENT/EXPLORATORY; labels as given; not tuned; not a performance claim)
QuixBugs buggy-vs-fixed (expected: DIVERGENT on witness inputs; I did not separately verify that each program's declared inputs contain a witness, so INSUFFICIENT rows are not misses by definition):
| Label | DIVERGENT | NO_DIV | INSUFFICIENT |
|---|---|---|---|
| BUGGY_VS_FIXED (31) | 27 | 0 | 4 |

Synthetic, labels as given (v8/v10 EXPLORATORY; CHANGED includes semantic-change transforms whose divergence may fall outside the sampled inputs):
| Label | DIVERGENT | NO_DIV S1 | NO_DIV S2 | INSUFFICIENT |
|---|---|---|---|---|
| CHANGED (78) | 49 | 5 | 8 | 16 |
| EQUIVALENT (72) | 1 | 8 | 24 | 39 |
Together with quixbugs_neg (EQUIVALENT-labelled): DIVERGENT 1, S1 3, S2 47, INSUFFICIENT 34 of 85. All NO_DIVERGENCE_OBSERVED values mean only "no difference seen on the explored inputs"; 13 of 78 CHANGED-labelled synthetic pairs received NO_DIVERGENCE_OBSERVED, which illustrates why it is not an equivalence verdict.
BugsInPy extracted units (REAL_BUGFIX, synthetic-battery inputs): 6 DIVERGENT, 16 NO_DIV (15 S2, 1 S1), 24 INSUFFICIENT, 9 not driven. Divergence here shows a difference on a synthetic input, not that the real regression was reproduced.

## Limits of this spike
Single machine and platform below minimum isolation; at most 12 inputs per pair; no exploration beyond given inputs; no replay/structure baselines (so K2 activation and K3 untested); sample of synthetic pairs is one stratified draw (seed 20261117); counts above are from `k1_spike_summary.json` and may be recomputed with `k1_spike.py summarize`.

## Superseded numbers (post-fix rerun, commit 700532b8; see POSTFIX_RERUN_NOTE.md)
Original text above is preserved. After the NO_RUN fix only the quixbugs_neg arm changed (3 pairs: knapsack sp-1, knapsack sp-3, levenshtein sp-3, NO_DIV S2 -> INSUFFICIENT resource_limit): quixbugs_neg row 1 / 47 S2 / 3 S1 / 34 INSUFFICIENT -> 1 / 44 / 3 / 37; INSUFFICIENT fraction 40% -> 43.5% with added reason resource_limit 3; combined line "S2 47, INSUFFICIENT 34 of 85" -> "S2 44, INSUFFICIENT 37 of 85". Other arms, K1 (not met) and K2 conclusions, and determinism for quixbugs/bugsinpy_units/quixbugs_neg are unchanged; synthetic determinism was not re-run post-fix.
