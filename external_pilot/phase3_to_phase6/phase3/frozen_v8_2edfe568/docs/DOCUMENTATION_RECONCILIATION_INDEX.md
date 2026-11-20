# Documentation reconciliation index (test counts, security, determinism, novelty, results)

Reference state: HEAD `debc4396`; code and tests identical to `5efcef74`. Current facts used as the yardstick:
- Tests: `tests/v7` alone 276 passed, 1 skipped (277 tests; recorded at `5efcef74`, sources unchanged since); `tests/v7` + `tests/v6` 286 passed, 1 skipped (E3 run); full `pytest tests -q` never completed.
- Phase 2 numbers: E3 false assurance 0.123 versus 0.226, detection 0.708 versus 0.774, abstention 0.473 (older engine: 0.360).
- Security: result-channel protocol correctness only; no OS-isolation claim; evidence log not tamper-proof; trust anchor is Phase 3.
- Determinism: hash seed fixed (hash-order untested), `datetime.now` not virtualised, not completely deterministic.
- Novelty: no "first", "novel" or "state of the art" claim; see `research/literature/NOVELTY_REASSESSMENT_PHASE2.md` (commit `ee4749bc`).

Status values: **current** (agrees with the yardstick), **fixed** (stale text corrected in this pass), **superseded** (historical; kept unchanged, must not be cited for the current engine), **stale: owner** (needs an edit by the named owner outside this documentation pass).

## A. Documents owned by this pass
| File | Issue found | Status |
|---|---|---|
| `README.md` | counts "76 collected", "85 passed"; abstention 0.360 as current; "Merkle tree" and `unmodelled_change` listed as never built or produced; `--full` described as routine; no Phase 2 section | fixed |
| `REPRODUCIBILITY.md` | pointed `--full` at the slow legacy pytest stage; no Phase 2 workflow | fixed |
| `datasets/README.md` | no pair-level provenance, no denominators | fixed (links to `docs/DATASET_PROVENANCE.md`) |
| `docs/architecture/V7B_IMPLEMENTATION.md` | "261 passed" test line; `unmodelled_change` listed as never produced; header exit codes omitted 1 | fixed |
| new: `PHASE2_REPRODUCTION_GUIDE.md`, `EXPERIMENT_PROTOCOL.md`, `DATASET_PROVENANCE.md`, `FAILURE_MATRIX.md`, `VERDICT_INTERPRETATION.md`, `CHANGELOG_V7B.md` | - | current |

## B. V7-B documents not owned by this pass
| File | Statement | Status / owner |
|---|---|---|
| `docs/architecture/V7B_RESULT_PROTOCOL.md`, `V7B_RISK_REGISTER.md`, `V7B_BACKLOG_STATUS.md` | security and determinism wording (explicit non-claims; guard test `test_v7b_docs_do_not_claim_tamper_proof`) | current; backlog status line quoting an older suite count: stale, owner: architecture docs |
| `reports/phase2/PHASE2_CONSOLIDATED_EXPERIMENTAL_ANALYSIS.md`, `E1_K2_DETERMINISM_REMEASUREMENT.md`, `E3_E7_PROTOCOLS.md`, `LOCAL_EXPERIMENT_RERUN_MATRIX.md`, `FINAL_SPECIFICATION_DECISIONS.md`, `PHASE2_TRACEABILITY_RECONCILIATION.md`, `K1_K5_READINESS_AND_DECISION.md` | experiments, decisions, counts | current (owner: lead) |
| `reports/phase2/MANDATORY_IMPLEMENTATION_BACKLOG.md` | "168 passed, 1 skipped" as the standing baseline | superseded (historical baseline before MB items); note OI-19 |
| `reports/phase2/PHASE_2_SPEC_CONFORMANCE_AUDIT.md` | "5 files, 92 tests (91 passed, 1 skipped)"; lists drift in README | superseded by `PHASE2_TRACEABILITY_RECONCILIATION.md` |
| `reports/phase2/FINAL_V7B_REQUIREMENTS_TRACEABILITY_MATRIX.md`, `PHASE_2_SPEC_CONFORMANCE_AUDIT.md` | row W3 "Witness immutable" / "immutable by chain" | stale: owner lead; should read "append-only chain, forgeable by its writer" (already so in the matrix row text; audit row W3 still says "immutable") |
| `reports/final/V7B_FROZEN_SPEC.md` | `Witness` described as immutable (line about the Witness record) | stale: owner lead (frozen file: annotate, do not rewrite) |
| `reports/final/INDEPENDENT_RED_TEAM_REVIEW.md` | "74 passed, 1 skipped" | superseded (historical review of the Phase 1 build) |
| `reports/final/FINAL_RESEARCH_READINESS_REPORT.md`, `FINAL_CLAIMS_AND_EVIDENCE_MATRIX.md`, `PHASE_1_*REPORT.md`, `EXECUTION_LOG.md` | "75 passed", Phase 1 claims and counts, old-engine numbers | superseded; owner lead: add a one-line banner pointing to the Phase 2 analysis |
| `research/evaluation/EXPLORATORY_RESULTS.md`, `POSTFIX_RERUN_NOTE.md`, `K1_K2_FEASIBILITY_REPORT.md`, `BASELINE_IMPLEMENTATION_AND_FAIRNESS.md` | old-engine numbers (abstention 0.360, K2 determinism with random hash seed) | superseded; owner research: add a banner "old engine; see Phase 2" |
| `research/security/EXECUTION_ISOLATION_AUDIT.md`, `THREAT_MODEL.md` | "11 passed"; isolation described before D-02 and MB-06/07 | stale: owner research/security (add Phase 2 status; keep non-claims) |
| `research/reproducibility/REPRODUCIBILITY_PROTOCOL.md` | `--full` as the full-run recipe; test counts; hash-seed statement (`-I` ignored the seed) | stale: owner research |
| `research/literature/RESEARCH_GAP_AND_NOVELTY_ASSESSMENT.md`, `NOVELTY_REASSESSMENT_PHASE2.md` | novelty positioning | assessment current in the Phase 2 file; Phase 1 file superseded by it (owner research) |
| `research/benchmarks/*` | dataset inventory and audit | current for non-pristine status; `DATASET_PROVENANCE.csv` is the independent-data log (empty of acquisitions) |

## C. Paper (owner: paper; outside this pass)
| File | Issue | Status |
|---|---|---|
| `paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/sections/definitions.tex` line 10 | "An immutable record..." for the Witness; the log is not tamper-proof | stale: owner paper; wording: "an append-only, content-addressed record" |
| `paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/figures/evidence_witness_model.dot` line 5 | label "derived; immutable" | stale: owner paper |
| `sections/execution.tex` | child is `python -I`; "74 passed, 1 skipped" | stale: owner paper (current profile `-s -P -B`, hash seed pinned; counts above) |
| `sections/results.tex`, `tables/*.tex`, `tables/SOURCES.json`, `scripts/make_tables.py` | old-engine headline numbers (abstention 0.360, pre-fix and post-fix tables) | superseded by Phase 2 numbers; owner paper must regenerate or label as historical |
| `sections/limitations.tex`, `tables/capability.tex`, `tables/not_evaluated.tex` | lists `unmodelled_change` and Merkle as unbuilt | stale: owner paper |
| `sections/introduction.tex`, `related_work.tex`, `conclusion.tex` | novelty and contribution wording | review against `NOVELTY_REASSESSMENT_PHASE2.md`; owner paper |

## D. Pre-V7-B documents (V1-V6 era; not V7-B claims)
`docs/README_pre_v7b.md`, `docs/CLAIMS_REGISTRY.yaml`, `docs/SBG_BOB_HANDOFF.md`, `docs/SBG_BOB_FINAL_HANDOFF_REPORT.md`, `docs/VERSION_MAP.md`, `docs/current/*` (including `REPRODUCTION.md`: 807 and 738 passed), `docs/research/*` (novelty analysis, prior art, threats), `reports/recovery_programme/*`, `reports/remediation/*` (738, 657, 807 passed), `reports/sprint2/*`, `reports/v6_*`, `reports/v7_design/*`, `paper/empirical_sprint_2026-11-04/*`, `paper/final_empirical_readiness_2026-11-05/*`: **superseded / historical**. They concern V5/V6 or the V7 design package, contain numbers (AUROC, test counts, "determinism", "novel", "state-of-the-art" language) that are not V7-B results, and are not edited. `reports/v7_design/**` describe "immutable event log" designs that V7-B did not build. Do not cite any of them for the current engine; owner lead may add a pointer banner to the index files.

## E. Outside-scope files that still need an owner action (summary)
1. Paper: `definitions.tex:10` and `figures/evidence_witness_model.dot:5` ("immutable"), `execution.tex` (`-I`, 74 passed), results and tables (old-engine numbers), limitations and capability tables.
2. `reports/final/V7B_FROZEN_SPEC.md` and `PHASE_2_SPEC_CONFORMANCE_AUDIT.md` W3 wording.
3. `research/evaluation/*`, `research/reproducibility/REPRODUCIBILITY_PROTOCOL.md`, `research/security/*`: banners and Phase 2 status.
4. `Makefile` legacy targets `readme` and `verify-artifacts` still reference README markers that no longer exist (README section 18).
5. `CITATION.cff` predates V7-B (no DOI, version, or date).
6. `scripts/run_evaluation.sh`: `--full` still begins with the legacy full `pytest tests`; a variant that substitutes `tests/v7 tests/v6` (as the E3 run did) is an owner decision for the scripts owner.
