# NEXT SESSION ASSIGNMENTS (independent Bob sessions; each session reads MASTER_HANDOFF_PROMPT.md first)

Launch rule: run the liveness check (MASTER_HANDOFF_PROMPT §7) first. Sessions C, D, E(partial), F(partial) are safe now. A and B only if the originating session's A4R/A4B/A4C/A4D have gone quiet (>10 min no writes) — otherwise poll.

## Session C — A5E + A5F: ablation, state-genome dominance, return-value (START NOW)
Own: `experiments/ablations/`, `08a_ABLATION_REPORT.md`, `08b_RETURN_VALUE_REPORT.md`, `EXP-A5E-*`, `EXP-A5F-*`, registries `A5E.jsonl`,`A5F.jsonl`.
1. 11 ablation variants (full; state only; call-topology only; bigrams only; exception only; temporal only; minus each) by recomputing the frozen distance from frozen components (import SBG read-only); verify full == frozen sbg_v5 bit-exactly first; AUROC+cluster CI+AUPRC+P/R/F1 (train Youden)+paired Δ vs full (Holm over 10) on v10_test and v9c_val (context: dev/train); per-program, matched concordance, edit strata; family declared exploratory.
2. State 0.917 vs full 0.897: paired cluster Δ test; per-sc_type; component redundancy; **leakage test** of the "output-free" claim: reimplement state abstraction (verify == frozen sbg_state), then variants dropping return-event snapshots / keeping args only / shuffled-locals null (A1 hypothesis: tracer snapshots locals incl. at return).
3. SC-6: verify 17/23 invisible on V10 (+val analogue), classify zero-score causes, architectural vs bug vs protocol; exploratory SBG+return-value variant on v9c_dev ONLY; state requirement for confirmatory evaluation (fresh withheld set, new freeze) — V10 burned for any variant designed after seeing it.
4. Sensitivity: tracer event-cap (MAX_EVENTS), timeout, input subset (e.g. 5/11 inputs) — bounded subsets via `dump_traces.py --worker` into own dir.
Done marker: `results/raw/EXP-A5E-DONE`, `EXP-A5F-DONE`.

## Session D — A5G: external validation (START NOW)
Own: `experiments/external_validation/`, `08c_EXTERNAL_VALIDATION_REPORT.md`, `EXP-A5G-*`, `A5G.jsonl`.
Recompute BugsInPy 0.497/0.410 and QuixBugs 0.444/0.388 from raw scored pair files (A3 already did: `experiments/statistical_verification/recompute_external_auroc.py`, EXP-A3-007 — reuse, don't redo); explain populations; coverage-of-buggy-path check; SBG vs state/coverage/edit baselines on external pairs; Python-version AUROC effect (use A2 raw outputs `results/raw/repro/`); size/category stratification; independence assessment; ONE pre-registered independent-source mutation experiment (≤2 h, config+sha256 before scoring, run once, exploratory); Java/cross-language status (no demonstrated generalisation expected — verify). No manufactured validation.

## Session A — A4R + A4B continuation (WAIT unless originating agents quiet)
Own: `EXPERIMENT_RECOVERY_AND_REGISTRY.md`, `logs/registry/INDEX.md`, `recovery/`, `competitors_new/`, `EXP-A4R-*`, `EXP-A4B-*`.
A4R: classify EXP-A4-002..004 and A4B/A4C partials (VERIFIED COMPLETE / PARTIAL / INTERRUPTED / INVALID / UNKNOWN); answer the held-out-label-before-freeze question; unit tests; publish `EXP-A4R-001/VERIFIED_BASELINES.json`; build INDEX.md. A4B: finish 8 modules → `.READY` files; independent-input differential executors; classes C/D justification in `competitors_new/README.md`.

## Session B — A4C + A4D continuation (WAIT for Session A `.READY`, or originating agents)
Own: `run/`, `05_*`, `06_*`, `05b_*`, `a4d/`, `EXP-A4C-*`, `EXP-A4D-*`.
A4C: held-out prediction run once on frozen config (`EXP-A4C-002/frozen_config.json`), eval matrix, runtime/memory, incremental-value matrix, strata; write 05/06. A4D: verify predictions (pair-id sets, labels, orientation, thresholds), recompute all metrics with own code, SBG-vs-baseline verdicts with MDE caveats, check independent battery independence (no overlap with protocol 11 inputs), different-combiner robustness; write 05b; publish `A4D_READY`.

## Session E — AI: artifact integrity (math_gray_code NOW; final re-hash LAST)
Own: `reproduction/final/`, `ARTIFACT_MANIFEST_FINAL.md`, `EXP-AI-*`. Now: `math_gray_code` root cause (bounded, RSS watchdog), Makefile destructive-target inventory (A2 has one — reuse), validate new experiment configs. Last: EXP-ORCH-006 (`shasum` tree vs BEFORE file, investigate every diff, no restore), hashes of all new prediction files, final manifest + one-command reproduction check.

## Session F — A6 + AJ (first pass NOW, final update LAST)
Own: `10_*`, `02_*`, `11_*`. Pass 1 now on existing evidence (01, 03, 07, 09 + prior audit): Reviewers A (novelty), B (methodology), C (practical significance): major/minor objections, missing experiments, unsupported claims, rejection risks, remediation. `02`: what SBG demonstrates / does not; supported / unsupported / contradicted claims; best research question + contribution statement (current evidence favours: evaluation-methodology + empirical negative/null on incremental value; NOT "validated representation / bug detector / cross-language"). Pass 2 after WP-A/B/C/D: update with real comparative/ablation/external results; write `11` (list likely reviewer objections ↔ evidence needed).

## Orchestrator session (final)
After WP A–F: merge `08a/b/c` → `08_ROBUSTNESS_ABLATION_AND_EXTERNAL_VALIDATION.md`; write `00_EXECUTIVE_SUMMARY.md`, `12_FINAL_GO_NO_GO_DECISION.md` with the 7-gate scorecard (PASS/CONDITIONAL/BLOCKED), final user report (items 1–15 of the resume directive).

## Dependency graph
C, D, E(math_gray_code), F(pass 1) → independent, start now.  A → B (held-out competitor runs).  A,B,C,D → F(pass 2) → E(final re-hash) → Orchestrator.
