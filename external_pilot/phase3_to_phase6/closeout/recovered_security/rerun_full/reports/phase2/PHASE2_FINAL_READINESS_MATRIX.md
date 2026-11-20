# Phase 2 final readiness matrix

Status at the end of Phase 2 (local macOS, exploratory, non-pristine development data). Source: `PHASE2_CONSOLIDATED_EXPERIMENTAL_ANALYSIS.md`, `PHASE2_FINAL_RED_TEAM_REVIEW.md` (verdict: READY WITH DOCUMENTED LIMITATIONS; 0 blocking, 5 major, 9 minor). Categories: PASS / PASS WITH LIMITATIONS / BLOCKED / DEFERRED TO PHASE 3.

| Area | Status | Basis and limitation |
|---|---|---|
| Implementation (MB-01..MB-16, D-01..D-09) | PASS WITH LIMITATIONS | 286 passed, 1 skipped (`tests/v7 tests/v6`); 16/16 mutants killed; 12 of 13 red-team probes behave per spec. Limits: program under test can forge its own verdict (same-process result channel, documented), `datetime.now` not virtualised, `random._urandom` private attribute, no domain separation in the Merkle root, pair id depends on policy |
| Specification conformance | PASS WITH LIMITATIONS | 135 rules: 78 Conforming, 30 Partially, 7 Deviating, 14 Not implemented, 2 Unverifiable, 4 Deferred; red-team spot check 15 of 15 rows hold (1 loose line citation). UD-2 and UD-5 open |
| Evidence verification (E7) | PASS WITH LIMITATIONS | 828/828 verify; 42/42 corruption cases as pre-registered. Hash chain is tamper-evident only against non-rechaining edits; no trust anchor; deleted `verdict.json` not detected |
| E1 determinism | PASS WITH LIMITATIONS | Supported weakly (1 vs 2 pairs); confounded; hash order untested |
| E2 hash-order sensitivity | DEFERRED TO PHASE 3 | not run by decision; needs a diagnostic seed switch |
| E3 vs baselines | PASS WITH LIMITATIONS | numbers independently recomputed; false-assurance reduction is abstention only; detection possibly lower; precision of no-difference verdicts not better (13/61 vs 24/130); false-alarm figure is an artefact; SP-2 sensitivity not run; label validity limits (synthetic labels) |
| E4 ablations | PASS WITH LIMITATIONS | variants applied; no verdict change; cannot show component value |
| E5 floor sensitivity | PASS WITH LIMITATIONS | stable by construction (floor only relabels S1/S2) |
| E6 runtime | PASS WITH LIMITATIONS | ~1.6x B1, ~1.02x B1+rep; load-flagged, battery |
| Literature and novelty | PASS WITH LIMITATIONS | conservative wording; abstract/metadata-only for most sources; bib items flagged (malik2026diffkemp, year keys, 11 unverified rows) |
| Manuscript | PASS WITH LIMITATIONS | complete content, checks pass; **not compiled** (no LaTeX), not IEEE-ready claimed; numerical check is internal consistency |
| Documentation and reproduction | PASS WITH LIMITATIONS | validator passes; frozen spec W3 wording and some historical docs retain old text (banners added); `run_evaluation.sh --full` legacy test stage impractical |
| Raw-data preservation | PASS | archives outside git with sha256 (verified by red team); compact summaries tracked; historical results untouched |
| OS-level isolation (Linux/Docker, K1) | DEFERRED TO PHASE 3 | not claimed |
| K5 adjudicated benchmark, independent holdout | DEFERRED TO PHASE 3 | not started |
| Comparison with published tools | DEFERRED TO PHASE 3 | not run |
| Trust anchor for evidence log | DEFERRED TO PHASE 3 | |
| Confirmatory / generalisation claims | BLOCKED (by design) | no pristine data |

Overall: **Phase 2 complete with documented limitations. Not ready for confirmatory claims; ready to begin independent validation (Phase 3) on explicit user authorisation.**
