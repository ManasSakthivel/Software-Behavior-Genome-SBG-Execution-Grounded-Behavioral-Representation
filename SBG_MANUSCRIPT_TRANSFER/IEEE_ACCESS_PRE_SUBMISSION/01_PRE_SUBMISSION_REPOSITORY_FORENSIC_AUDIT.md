# 01 — Pre-Submission Repository Forensic Audit (Agent A2)

Repo: `SBG/` at HEAD `3425693` ("fix(ci): restore Python compatibility and deterministic reproduction checks", 2026-11-05), branch `remediation/sbg-v4`. Read-only.
Registry: `logs/registry/A2_repo.jsonl` (`EXP-A2-001 … 018`). Companion report: `09_REPRODUCIBILITY_AND_ARTIFACT_FREEZE_AUDIT.md`. Paths are relative to `PKG/` unless prefixed `SBG/`.

---

## 0. Verdict

The repository is internally consistent, its tests pass, CI is green at HEAD, and the headline scored files reproduce exactly on CPython 3.13.5. It is **not** yet submission-clean, for these reasons:

1. The headline V10 and V9c results cannot be reached from the documented reproduction path (README, `REPRODUCTION.md`, Makefile). **Major.**
2. "Frozen before scoring" is self-attested: freeze, scored pairs, evaluation and dataset share one commit (`c5bc130`). **Major.**
3. Results hold only on CPython 3.13.x. 3.9.6, 3.11.15 and 3.14.5 give different scores and flip rankings. **Major.**
4. Several Makefile targets and scripts overwrite committed artifacts in place without a guard. **Major.**
5. Four untracked v8-dev files are needed by `zero_score_population.py` and `EXPERIMENT_MANIFEST.json`. **Major.**
6. Provenance of the 121 "authored" corpus programs does not name an author or tool, and the project shows an AI-agent workflow. This is an ethics and disclosure risk. **Major (disclosure).**

Contradicted prior-audit claims: "CI red" (CI is green at HEAD) and "7 vs 10 consistency checks still open" (fixed in `9bed2f0`; one stale file remains).

| Item | Result |
|---|---|
| Diff 93ef3f3 → 3425693 | 3 files, +54/−10; **no frozen artifact, source module or reported number touched** (§2) |
| pytest, clean checkout, py313 | **807 passed, 0 failed, 0 skipped, 3 warnings** (EXP-A2-004) |
| `verify_trace_v4.py` | 35/35, but mostly a document-string check (EXP-A2-005) |
| `consistency_check.py` | **10/10** (C1–C10) (EXP-A2-005) |
| Frozen hashes | 533/536 match, 3 explained (EXP-A2-001) |
| V10 / V9c-val recompute | 644/644 and 436/436 bit-identical (EXP-A2-007/008) |
| Silent-fallback frequency | **0** on V10, V9c-val, V9c-dev, V9c-train (EXP-A2-003) |

---

## 1. Inventory (EXP-A2-014 data in `results/raw/repro/ls_files_by_top.txt`, `ls_files_by_dir2.txt`)

* 15,038 tracked files, of which 14,275 are `.py`. REPO is 208 MB; `.git` is 29 MB. 50 commits, all authored by Manas Sakthivel; 3 carry Claude co-author trailers (Haiku 4.5 ×2, Opus 5 ×1).
* Tracked files by top-level directory:

| Directory | Files | Notes |
|---|---|---|
| `benchmark` | 13,606 | `datasets` 12,749; `v5` 279; `corpus` 187; `v3` 182; `regression` 151; `transformations` 21; `scripts` 18 |
| `external` | 589 | `bugsinpy` 257; `quixbugs` 246; `quixbugs_java` 86 |
| `artifacts` | 329 | `paper_evidence` 96; `final` 71; `v2` 55; `phase3` 29; `v5` 21 |
| `docs` | 156 | `archive` 112; `current` 20 |
| `experiments` | 147 | `final` 68; `v2` 25; `phase4` 15; `v4` 10; `external` 10 |
| `sbg` | 59 | `extraction` 19; `v2` 17; `v5` 5; `v3` 5; `v6` 2; `repair` 3 |
| `reports` | 40 | `remediation` 40 |
| `phase5` | 31 | cross-language |
| `results` | 28 | |
| `baselines` | 19 | |
| `tests` | 18 | |
| root and others | 15 | |

* **Untracked** (`git status`): `artifacts/final/pairs_dev_output_free_v8.jsonl`, `pairs_v8dev_output_free_v8.jsonl`, `programs_dev_output_free_v8.json`, `programs_v8dev_output_free_v8.json`; `paper/` (17 MB, contains `_ws` full-code copies of the repo); `reports/sprint2/`.
  * The four v8-dev files are read by `experiments/final/zero_score_population.py:24-25` and listed in `EXPERIMENT_MANIFEST.json`. They are superseded by the tracked `v8devrescore` files, so the zero-score population table is not regenerable from a fresh clone (D4).
  * Neither the headline V10 nor V9c-val results depend on untracked files: the clean-checkout pytest and recompute needed none.
* Local branches: `main`, `remediation/ieee-access-audit`, `remediation/sbg-v2`, `remediation/sbg-v3`, `remediation/sbg-v4` (HEAD), `independent-audit/ieee-access-2026-10`. Remote `origin` = GitHub `ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation`. `origin/remediation/sbg-v4` equals HEAD.
* A gitignored `SBG/.pytest_cache/v/cache/{lastfailed,nodeids}` (mtime 14 Nov 18:34) exists. It lists `benchmark/v5/hard_negatives/...` tests. It was not created by A2 (all A2 pytest runs used `-p no:cacheprovider` on copies). It is ignored by git and was excluded from the BEFORE hash.
* 27 tracked files contain the absolute path `/Users/manassakthivel` (for example `EXPERIMENT_MANIFEST_V4.json`, `experiments/.../cobol_inventory.py:69`). `cobol_inventory.py` reads `/Users/manassakthivel/Desktop/COBOLSRC`, outside the repo.

---

## 2. What changed between 93ef3f3 and 3425693

`git diff --stat 93ef3f3 3425693` (read-only): **3 files, +54/−10.**

| File | Change | Effect on results |
|---|---|---|
| `.github/workflows/ci.yml` | py3.9 jobs pinned to `ubuntu-22.04` | None (CI infrastructure) |
| `docs/current/REPRODUCTION.md` | 2 lines: documents that `--strict` tolerates one difference, the `threshold_provenance` key | None |
| `experiments/final/check_reproduction.py` | adds `STRICT_IGNORED_KEYS` and `strict_differences()` | None on any frozen artifact; changes the strictness rule of the reproduction check. `check_reproduction.py` is not hash-pinned. |

No file in `artifacts/final/`, `artifacts/paper_evidence/`, `sbg/`, `benchmark/` or any pinned script changed. All reported numbers are therefore unaffected by the move to 3425693. Hash verification at 3425693 matches 533/536 (the same 3 disclosed mismatches as before).

**CI status.** GitHub Actions (public API read): run #9 (workflow_dispatch) success; run #10 (pull_request) success, all 5 jobs green (tests py3.9, tests py3.13, scientific-integrity, fast-experiments py3.9, fast-experiments py3.13); run #11 (push to main, merge `f3e40db`, tree `6f89be5` = tree of `3425693`) success. The prior audit's "CI red" is true for the older commit it examined, not for HEAD. `ci.yml` triggers on push to main/master, pull_request and workflow_dispatch.

---

## 3. Architecture, from the code

### 3.1 Headline path (V10 and V9c-val)

```
program file → experiments/final/extraction.py::extract_program(.., "output_free_v8")
   → _extract_v8 → entry_policy.select_entry_structural   (class_driver only if no function entry)
   → sbg/v2/execution/runner.py::SandboxRunner.run          (N_RUNS=5, MAX_EVENTS=5000,
                                                              trace timeout 1.0 s, program budget 60 s, MAX_TIMEOUTS=2)
   → sbg/extraction/dynamic/tracer.py::Tracer                (sys.settrace in a daemon worker thread)
   → genome layers: sbg/v3/genome.py (d_V3), sbg/v5/temporal_genome_v5.py (temporal), sbg/v5/state_transition_genome.py (state)
   → extraction.score_pair = 0.50·d_V3 + 0.25·d_temporal + 0.25·d_state
   → experiments/final/score_v6_experimental.py writes pairs_v10_test_v6exp.jsonl (also V6 state variant)
```

Pair-evaluation scripts: `experiments/final/evaluate_v10.py`, `evaluate_v9.py`, `evaluate_v8.py`.

### 3.2 What is recorded per trace (`sbg/extraction/dynamic/tracer.py`)

* `TraceEvent` (line 38): `event_type` (call/return/exception/line), `function_name`, `lineno`, `local_vars_snapshot` (repr of locals, capped at 100 characters), `timestamp_ns`.
* `ExecutionTrace` (line 53): `program_id`, `input_repr`, `events`, `return_value`, `exception`, `stdout`, `execution_time_ms`, `coverage` (set of line numbers), `truncated` (True when `MAX_EVENTS` was hit).
* `ExecutionGenome` (line 396): coverage vector, function-call counts, instruction-type histogram, hot-path signature (SHA-256 prefix of the top-5 functions), trace-length statistics, truncated fraction, provenance (includes an extraction timestamp).
* Scores do not use `timestamp_ns`, `execution_time_ms` or the extraction timestamp.

### 3.3 Component weights

* Overall: **0.50·d_V3 + 0.25·d_temporal + 0.25·d_state** (`extraction.score_pair`, ≈ line 483). Weights are fixed, not fitted (`fit_weights.py`, `WEIGHT_FITTING.json`).
* `distance_v3` (8 components): coverage 0.20, bigrams 0.25, call frequency 0.20, exception 0.10, depth 0.10, consistency 0.05, input sensitivity 0.05, exception-causality hash 0.05.
* Temporal (7 sub-weights): 0.20, 0.10, 0.10, 0.15, 0.15, 0.10, 0.20.
* State: frequency-weighted Jaccard over state-transition features. V6 variant: `sbg/v6/state_transition_genome_v6.py`.

### 3.4 Fallbacks

In `extraction.score_pair`:
* A `None` or failed temporal or state layer is replaced by `d_V3`.
* If `v5_full` is false, the whole V5 score becomes `d_V3`.
* `extract_temporal` and state extraction are wrapped in `try/except → None`.
* `v5_full` is stored in each scored row, so the fallback is auditable after the fact.

In legacy `sbg/v5/distance_v5.py`: silent 0.5, `d_V3` and 0.0 fallbacks for missing layers. This module is **not** on the headline path.

**Measured frequency (EXP-A2-003; `results/raw/repro/fallback_rates_frozen.json`, `fallback_files_recompute.json`):**

| Population | Evaluated pairs | `v5_full=1.0` | Fallbacks fired |
|---|---|---|---|
| V10 | 638 | 638 | 0 |
| V9c-val | 432 | 432 | 0 |
| V9c-dev | 464 | 464 | 0 |
| V9c-train | 1,650 | 1,650 | 0 |

In the recompute, all 660/660 V10 and 445/445 V9c-val files that ran produced both a temporal and a state layer. The unevaluated pairs are explicit failures: V10 has 3 nonterminating; V9c-val has 1 nonterminating and 1 import_error. Files with traces truncated at `MAX_EVENTS`: V10 29/660, V9c-val 40/445.

### 3.5 Exact-zero scores (counts from the frozen files)

| Population | Exact-zero `sbg_v5` among primary pairs |
|---|---|
| V10 | 221/638 = 34.64% (63.6% of equivalent, 5.64% of changed) |
| V9c-val | 160/432 = 37.04% |
| V9c-dev | 158/464 |
| V9c-train | 628/1,650 |

### 3.6 Determinism

* Deterministic: the scores. On 3.13.5 they were bit-identical across hash seeds 0, 1 and 12 random draws, cwd, `re.purge()` state, and up to 84 competing processes (EXP-A2-009).
* Event-sequence digests of the 5 runs are identical in all 663 V10 files. Locals-snapshot digests differ in 267/663 files because reprs contain memory addresses; scores do not use them.
* Nondeterminism sources: (1) CPython minor version (dominant; companion report §6); (2) memory addresses in snapshot reprs; (3) wall-clock timeouts (1 s per trace, 60 s per program), not triggered in any measured condition; (4) the tracer's daemon thread: after the deadline, tracing stops silently while the function continues running, with no flag in the output (**D6**, mechanism exists, not triggered); (5) `SEED=42` is logged but seeds no RNG.
* `sbg/v2/execution/runner.py` (on the headline path) is not hash-pinned in any freeze file.

### 3.7 Headline-path code vs legacy or dead code

| On the headline path | Legacy / not on the path |
|---|---|
| `experiments/final/{extraction,protocol,entry_policy,class_driver,score_v6_experimental,evaluate_v8,evaluate_v9,evaluate_v10,run_chunked}.py` | `sbg/v2/hybrid`, `sbg/repair` |
| `sbg/extraction/dynamic/tracer.py`, `sbg/v2/execution/runner.py` | `sbg/v5/distance_v5.py` (used by baseline `b07_dynamic_v5`, `experiments/external/*`, `phase1_output_leakage_gate`) |
| `sbg/v3/genome.py`, `sbg/v5/{temporal_genome_v5,state_transition_genome}.py`, `sbg/v6/state_transition_genome_v6.py` | `baselines/*` (comparators are computed by `experiments/final/static_baselines.py`, which is pinned) |
| `sbg/statistics.py` | `phase5`, `experiments/{v2,v4,v5,phase4,strengthening,repair,external}`, `docs/archive` |

The dead/legacy set is several thousand files (most of `benchmark/datasets`, `docs/archive`, `artifacts/{v2,phase3,v4}`), which makes the repository hard to audit. A reviewer-facing README map of "what is on the headline path" is missing.

---

## 4. Frozen artifacts and traceability (summary; details in report 09)

* 536 pins checked, 533 match, 3 mismatches, all disclosed in V8 amendments (report 09 §1).
* `FREEZE_V10.variants_tree_sha256` could not be reproduced (algorithm undocumented). The 25 per-file pins and the byte-identical dataset regeneration (EXP-A2-012) cover the same files.
* 34 reported claims traced to artifact, line, script and command; 24 of 34 scripts are hash-pinned; 10 are not (report 09 §3).
* BugsInPy 0.497 vs 0.410, and QuixBugs 0.444 vs 0.388, are different populations, not contradictions.

---

## 5. Environment, CI and Makefile

| Item | Value |
|---|---|
| Machine | macOS 26.6.2, Apple M4 Max, 14 cores, 36 GB |
| Python | canonical `venvs/py313` 3.13.5; `venvs/py39` 3.9.6; `/opt/homebrew/bin/python3.11` 3.11.15; `python3.14` 3.14.5 |
| `.python-version` | `3.13` |
| Declared 3.13.15 | `requirements-lock.txt`, `external/bugsinpy/manifest.json`, `docs/current/PYTHON_VERSIONS.md`, `docs/current/REPRODUCTION.md`. The freeze files and the venv say 3.13.5. Results reproduced on 3.13.5. **Minor (documentation).** |
| Tracer limits | `N_RUNS=5`, `MAX_EVENTS=5000`, trace timeout 1.0 s, program budget 60 s, `MAX_TIMEOUTS=2`, `SEED=42` (logging only) |
| CI | `.github/workflows/ci.yml`: tests py3.9 and py3.13, scientific-integrity, fast-experiments py3.9 and py3.13. Green on #9, #10, #11. |

**Makefile overwrite risks** (none run in REPO):
* `reproduce-fast`, `check-reproduction`, `check_reproduction.py` overwrite `artifacts/final/HARD_NEGATIVE_V5_RESULTS.json` and `REGRESSION_V5_RESULTS.json` in place.
* `tables`, `figures`, `readme`, `verify-artifacts`, `check` rewrite docs, README and manifests.
* `reproduce-v5`, `reproduce-output-free`, `v7-*` overwrite `artifacts/final/pairs_*`.
* There is no Makefile target for V8, V9 or V10 headline reproduction.
* In REPO, the two V5 result files have a Nov 7 mtime (with the macOS `@` xattr) but content equal to HEAD. Someone ran the check there and the files were later restored.

---

## 6. Prior-audit cross-check (`SBG_CURRENT_STATE_FORENSIC_AUDIT_2026-11-04.md`)

| Prior-audit claim | A2 result | Evidence |
|---|---|---|
| 807 tests pass | **Confirmed** (807 passed, 0 failed, 0 skipped, 3 warnings, 399 s) | EXP-A2-004 |
| 10/10 consistency | **Confirmed** | EXP-A2-005 |
| 25/25 FREEZE_V10 and 18/18 EXPERIMENT_MANIFEST_V4 hashes | **Confirmed** | EXP-A2-001 |
| Silent-fallback frequency unverified | **Measured: 0** on all evaluated populations | EXP-A2-003 |
| Zero rates 37.04% and 34.6% | **Confirmed as counts** (160/432, 221/638) | EXP-A2-003 |
| CI red | **Contradicted**: CI green at 3425693 (runs #9, #10, #11) | GitHub API |
| 7 vs 10 consistency checks still open | **Contradicted**: fixed in `9bed2f0` (2026-10-30); one stale file remains | EXP-A2-013 |

---

## 7. The 7-vs-10 consistency-check discrepancy (EXP-A2-013)

**Authoritative statement:** `experiments/final/consistency_check.py` `CHECKS` has **10 entries (C1–C10)** and **all 10 pass** on a clean checkout of 3425693 (`reproduction/consistency_check.log`):

| ID | Check | Result |
|---|---|---|
| C1 | generated tables match their artifacts | PASS |
| C2 | benchmark manifest is internally consistent | PASS |
| C3 | result denominators agree with the sets | PASS |
| C4 | documents cite only MEASURED artifacts | PASS |
| C5 | no retired claim appears in a current document | PASS |
| C6 | no output-reading result is attributed to SBG | PASS |
| C7 | output-free protocol traces no self-test driver | PASS |
| C8 | README results block matches the generated tables | PASS |
| C9 | frozen inputs are unchanged (prereg, benchmark, threshold, corpora) | PASS |
| C10 | gate verdict is recomputed from artifacts and quoted exactly | PASS |

History (`git log -S`):
* `docs/current/REPRODUCTION.md` said "C1–C7 / 7/7" at `9a9104f` (2026-09-28). Changed to "C1–C10 / 10/10" in `9bed2f0` (2026-10-30). HEAD line 107: "10/10".
* **Still stale:** `artifacts/paper_evidence/FINAL_PREMANUSCRIPT_RELEASE_CHECK.md` (lines ≈ 167, 172, 176, 185, 195) still describes the gap as open and lists it as a required fix, while its own §8 (≈ line 208) says it is resolved. It contradicts itself.
* **Historical and correct at the time (not patched):** `FINAL_STANFORD_READINESS_REPORT.md` "8 checks" (lines 115, 290, 351); `docs/archive/superseded_gate/*` "8/8".
* **Separate thing:** the "7/7 safeguard gates" are `experiments/strengthening/phase1_output_leakage_gate.py`. They are cited in `phase13_reproduction.py:196`, `phase14_adversarial_review.py` and `results/phase14/ADVERSARIAL_REVIEWS.json`. They are unrelated to `consistency_check.py`.
* `README.md` line 90 "516 tests" sits in a withdrawn-claims table; the current count is 807.

Proposed patch: `reproduction/proposed_doc_fixes.patch` (edits only `FINAL_PREMANUSCRIPT_RELEASE_CHECK.md`; `git apply --check -p2` passes). Not applied.

---

## 8. Licensing, provenance and ethics

| Item | Finding |
|---|---|
| Repository licence | MIT (`LICENSE`); `CITATION.cff` also MIT |
| `external/quixbugs`, `external/quixbugs_java` | Pinned commit `4257f44b…`; MIT (James Koppel); LICENSE files present |
| `external/bugsinpy` | Catalogue pinned at `11c5f1ee…`. 256 units copied verbatim under upstream licences, per-file hashes pinned in `freeze_bugsinpy.json` (256/256 match). Upstream licences include **GPL-3.0 (ansible)**, NOASSERTION (matplotlib, tqdm), MIT, BSD-3, Apache-2.0, Unlicense. |
| `benchmark/corpus/fresh_programs/` | 121 `.py` files, all headed `# provenance: authored` and `# license: original`. The author or tool is not named. All were added in one commit, `b54ea99` (2026-10-28). |
| V10 programs | 19 programs, 644 variants, generated by `benchmark/scripts/generate_v10_independent.py` (regenerates byte-identically, EXP-A2-012). "Independent" means unseen, not independent of the author: they are algorithmic siblings of development programs and were excluded from V8 only by a token-Jaccard of 0.101–0.146 (above a 0.10 threshold). `FREEZE_V10` and the generator docstring disclose this. |

Concerns:
1. **Possible undisclosed LLM authorship (Major, disclosure).** `reports/remediation/agent_e_fresh_dataset.md` plans a "provenance record (author or tool)" and a "human derivation review". `09_CLAUDE_HANDOFF.md` and the `agent_a…g` reports show an AI-agent workflow, and 3 commits carry Claude co-author trailers. The corpus header "authored / original" does not say who or what authored it. If any dev, V9 or V10 program was written or mutated by the same LLM that designed the method, that is a generator-bias risk and must be stated in the paper.
2. **GPL-3.0 code inside an MIT repository (Minor-to-Major, licence).** ansible units are copied verbatim. Either document them as separately licensed third-party material, remove them, or keep them only as downloaded-on-demand data.
3. **Same-author siblings (Minor, disclosed).** V10 independence is limited to unseen programs (see above).
4. **Third-party data and personal paths (Minor).** 27 tracked files embed `/Users/manassakthivel`.

---

## 9. Defects (severity-rated)

| ID | Severity | Defect | Evidence |
|---|---|---|---|
| D1 | **Major** | Headline V10/V9c reproduction is undocumented and unreachable from README, `REPRODUCTION.md` and Makefile; `grep` finds no mention of `evaluate_v10`, `score_v6_experimental` or `FREEZE_V10` | report 09 §9.1; `reproduction/REPRODUCE.md` supplies the path |
| D2 | **Major** | Freeze ordering is self-attested: FREEZE_V10, scored pairs, evaluation and dataset are in one commit `c5bc130` | `results/raw/repro/git_history_audit.md` |
| D3 | **Major** | In-place overwrite scripts and Makefile targets with no guard (section 5) | `Makefile`, `check_reproduction.py` |
| D4 | **Major** | 4 untracked v8-dev files are inputs to `zero_score_population.py:24-25` and `EXPERIMENT_MANIFEST.json`; the table is not regenerable from a clone | `git status` |
| D5 | **Major** | Scores exact only on 3.13.x; 3.9.6/3.11.15/3.14.5 differ; macOS 3.9.6 aborts on fatal recursion in the tracer | EXP-A2-009/010/011/017 |
| D6 | **Major** | Tracer truncation after the deadline is silent (no flag); mechanism not triggered even at 84× load; `MAX_EVENTS` truncation affects 29/660 V10 and 40/445 V9c-val files | `tracer.py`, EXP-A2-003 |
| D7 | Major (disclosure) | Corpus provenance does not name author or tool; AI-agent workflow evident | §8 |
| D8 | Minor | `FREEZE_V10.variants_tree_sha256` cannot be reproduced | EXP-A2-001 |
| D9 | Minor | `3.13.15` in four documents vs 3.13.5 actually used | §5 |
| D10 | Minor | `docs/CLAIMS_REGISTRY.yaml` drifted since August manifests (size 12,828 → 23,119) | EXP-A2-001 |
| D11 | Minor | GPL-3.0 ansible code in an MIT repo | §8 |
| D12 | Minor | 27 tracked files with absolute user paths; `cobol_inventory.py` reads an external directory | grep |
| D13 | Minor | `verify_trace_v4.py` (35/35) is mostly vacuous (hard-coded True, string checks) | EXP-A2-005 |
| D14 | Minor | `FINAL_PREMANUSCRIPT_RELEASE_CHECK.md` contradicts itself on the 7-vs-10 gap | §7 |
| D15 | Minor | `PHASE2_FREEZE.json` timestamp (2026-09-28) predates its commit | git log |
| D16 | Minor | About 10 reporting scripts, and `sbg/v2/execution/runner.py`, are not hash-pinned (report 09 §3) | EXP-A2-014 |
| D17 | Minor | `paper/` is an untracked 17 MB duplicate-code workspace | `git status` |
| D18 | Minor | 3 test warnings (1 `PytestRemovedIn10Warning`; 2 `SyntaxWarning` in `graph_cycle_detect_dfs__sc1_s0_p0.py:37`) | EXP-A2-004 |
| D19 | Minor | `HARD_NEGATIVE_V5_RESULTS.json` `threshold_provenance` free text is not reproducible; disclosed in `REPRODUCTION.md` and tolerated by `--strict` | `check_reproduction.py` |
| D20 | Minor | `FREEZE_V8.base_programs_tree_sha256` is computed over `fresh_programs`, so the key name is misleading; 8 of 100 V8 per-program hashes are stale (disclosed) | EXP-A2-001 |
| D21 | Minor | `README.md` line 90 "516 tests" is stale (807 now), though in a withdrawn-claims table | §7 |
| D22 | Minor | Stray `.pytest_cache` in REPO, listing `benchmark/v5/hard_negatives` tests; gitignored | §1 |

No critical defect was found: no result number was changed, no frozen pin was silently altered, and no headline score failed to reproduce.

---

## 10. What failed, could not be done, and how to continue

| Item | Status | Continuation |
|---|---|---|
| Orchestrator trace dump (`experiments/common/dump_traces.py`) | Stalled at 3/19 V10 and 0 V9c-val programs when polled at the start and end of the audit | `python reproduction/crosscheck_orch_trace_cache.py` after it completes. A2's own full recompute covers all programs (EXP-A2-007/008). |
| `FREEZE_V10.variants_tree_sha256` | Not reproduced | Obtain the author's hashing code |
| py39 pytest | Interpreter abort (SIGABRT) at `TestRecursionErrorCountsAsTimeout::test_recursion_error_triggers_early_abort` (macOS 3.9.6 only) | Run with `--deselect` on that test, on a copy |
| py39 V10 recompute | `math_fib_matrix` aborts the interpreter; 18/19 programs scored | informational |
| CI emulation `git commit` step | Blocked by a global secret-scanner hook (false positive on "seed"); not bypassed | Used `diff -r` against a pristine archive instead |
| Full-population recompute on 3.11/3.14 | Subset only | `reproduction/recompute_scores.py run --python <interp> --design v10 --split test` |
| Statistics re-derivation | Out of A2's scope | Agent A3 |

---

## 11. Supported / unsupported / contradicted

**Supported**
* Tests, consistency checks and CI at HEAD (807 passed; 10/10; green).
* 533/536 pins match; all mismatches are disclosed; FREEZE_V9 and FREEZE_V10 pins unchanged since their commits.
* V10 and V9c-val scored files reproduce bit-exactly on CPython 3.13.5, and the V10 dataset regenerates byte-identically.
* The diff 93ef3f3 → 3425693 touches no frozen artifact or result.

**Unsupported**
* A git-enforced "frozen before scoring" statement for V10.
* Reproduction on any interpreter other than 3.13.x.
* Reproduction of the headline by following the README.
* 35/35 as independent trace verification.
* "authored / original" as a statement of who wrote the corpus.

**Contradicted**
* "CI red" at HEAD.
* "7 vs 10 open" in `FINAL_PREMANUSCRIPT_RELEASE_CHECK.md` (contradicted by its own §8 and by HEAD `REPRODUCTION.md`).
* "3.13.15" as the interpreter (the venv and freeze files say 3.13.5).

---

## 12. Tree integrity (EXP-A2-016 and final check)

Final re-hash of the REPO working tree against `logs/sbg_tree_sha256_BEFORE.txt` (16,137 entries; excluding `.git`, `__pycache__`, `.pyc`, `.DS_Store`), EXP-A2-018: **0 changed, 0 missing.** There are 5 extra files, all in the gitignored `SBG/.pytest_cache/` (mtime 14 Nov 18:34:25). A2 ran pytest only on copies with `-p no:cacheprovider`, so this cache is not attributed to A2 (some other process ran pytest inside REPO). `git status` is unchanged and HEAD is still `3425693`. `logs/sbg_tree_sha256_BEFORE.txt` was not regenerated.
