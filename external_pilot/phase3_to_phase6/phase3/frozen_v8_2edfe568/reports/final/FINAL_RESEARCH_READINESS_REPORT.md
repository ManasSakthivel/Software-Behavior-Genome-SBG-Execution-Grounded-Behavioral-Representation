> **Phase 2 update (2026-11-18):** superseded where it conflicts by `reports/phase2/PHASE2_FINAL_READINESS_MATRIX.md` and `PHASE2_CONSOLIDATED_EXPERIMENTAL_ANALYSIS.md`. Numbers below that predate the Phase 2 engine are historical; no confirmatory claim is made.

# Final research-readiness report: SBG V7-B (branch research/v7b-final-validation)

**Verdict: B. Promising as a design/feasibility contribution; NOT ready for submission as a validation paper.** Date 2026-11-17.

## Executive summary
V7-B (witness-based, sufficiency-aware differential comparison with three verdicts `DIVERGENT_OBSERVABLE`, `INSUFFICIENT(reason)`, `NO_DIVERGENCE_OBSERVED(S1|S2)`, no equivalence verdict) is implemented and unit-tested (`tests/v7`: 75 passed, 1 skipped). It has been run only on existing, non-pristine development data. No independent held-out evaluation exists, the K1 gate is not met, and the exploratory results do not show an advantage of sufficiency-aware reporting over plain differential testing beyond moving some outcomes to INSUFFICIENT.

## Research question and contribution (defensible wording)
Whether explicit observation sufficiency, replay-confirmed witnesses and an insufficient-evidence outcome make differential analysis of software changes more reliable and traceable. Defensible contribution today: a precisely specified verdict/evidence contract with a tested implementation and an honest negative-result record. Not claimed: novelty of abstention (prior work exists), detection superiority, generalisation, equivalence.

## Status by area (labels per rules)
| Area | Status |
|---|---|
| Frozen spec, P0 reconciliation (`reports/final/V7B_FROZEN_SPEC.md`) | Implemented as documents; 4 R1 design drafts + schema/roadmap/risk R1s incomplete (debt logged) |
| Core engine `sbgv7/` (S1/S2, witnesses, hash-chained log, CLI) | Implemented and verified by unit tests; B-1 bug found by red team and fixed |
| Isolation | macOS child process + sandbox-exec verified; RLIMIT_AS/NPROC not enforced; memory cap soft; Linux/Docker NOT tested (daemon down) |
| S3, explorer, module E (internal-only), input generation | Designed but not implemented |
| Baselines B1, B1+rep, B2 (QuixBugs only), B3 (minimal), B4 | Implemented and run on dev pairs; B5 partial/not fair; Shadow SE, DiffKemp, LLM tools NOT compared |
| Independent benchmark | Not evaluated: no pristine data; K1 not met (74 runnable real pairs, 1 true project + 44 units on synthetic inputs); 60 projects/250 divergent pairs not attainable from existing Python sets |
| Statistics | Plan and code tested on synthetic data; applied only exploratorily (K=78 clusters, one cluster of 113 pairs; CIs weak); power at +5pp <= 0.27, +10pp unreachable |
| Literature | 158 rows: 7 full text, 89 abstract, 62 metadata; absence claims weak |
| Manuscript | Draft written, never compiled (no LaTeX); checker passes (cites, refs, 270 table numbers); prose numbers not machine-checked |
| README/reproducibility | Rewritten; quick-start commands run; `--quick` run 165 s; `--full` not run; full legacy `tests/` not completed |

## Main exploratory results (dev, non-pristine, post-fix; `research/evaluation/EXPLORATORY_RESULTS.md`)
Detection V7-B 0.708 vs B1 0.774, B3 0.81; false assurance V7-B 0.123 vs B1 0.226; abstention 0.360; V7-B false alarms 0.000, but B1's false alarms are all SP-2 renamed-entry harness artefacts. B1+rep differs from B1 on 2 of 311 pairs. Sufficiency did not separate labels on synthetic pairs (CHANGED 25% under S2 vs 32% under INSUFFICIENT). Paired false-assurance gain Holm p=0.006 but lower CI bound +4.3pp < +10pp rule. RQ4 generalisation, ablations, sensitivity, RQ5 beyond a CPU lower bound: NOT EVALUATED.

## Blocking / major issues before submission
1. No independent held-out data (K5: >=60 projects, >=250 independent divergent pairs, kappa>=0.7). Needs a new mining campaign with Linux container execution.
2. K1 unmet; no project-level runs of third-party repos (needs Linux isolation, period interpreters).
3. No evidence sufficiency adds value; needs matched-coverage comparison on independent data.
4. Fair comparison with published tools and 2024-26 LLM differential-testing work (Testora, Mokav, DiffTestGen, Cleverest, DiffSpec) not done.
5. Entry-function limits (renames, generators), JSON-only inputs, no input generation.
6. Flaky tests: os.killpg PermissionError guarded in isolation.py (3 clean runs; not a proof); stray-process test still depends on no concurrent runs.
7. Raw results (~160 MB) committed to git; consider moving out.

## Novelty (see research/literature/RESEARCH_GAP_AND_NOVELTY_ASSESSMENT.md)
Four of five contribution claims partially novel; empirical-evidence claim unsupported until independent experiments exist.

## V7 vs V7-B
V7-B only is justified; full V7 (explorer, internal-only divergence) is not.

## Reproduce
`.venv/bin/python -m pytest tests/v7 -q`; `scripts/run_evaluation.sh --quick`; `.venv/bin/python paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/scripts/check_manuscript.py`. See REPRODUCIBILITY.md.

Phase 1 closure: see `PHASE_1_FINAL_CLOSURE_REPORT.md` (note: the "~160 MB in history" figure in this report is uncompressed working-tree size; the repository pack is 48.61 MiB).
