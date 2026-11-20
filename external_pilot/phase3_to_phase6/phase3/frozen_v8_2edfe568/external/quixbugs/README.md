# QuixBugs (Python), vendored subset

This is an external real-program corpus for the SBG Phase 2 evaluation. See
`docs/current/PHASE2_PREREGISTRATION.md` §6.

| | |
|---|---|
| Upstream | https://github.com/jkoppel/QuixBugs |
| Commit | `4257f44b0ff1181dedaedee6a447e133219fcebf` (2022-08-29, "Merge pull request #52 from h4iku/add-manual-run") |
| License | MIT, Copyright 2017-2019 James Koppel (see `LICENSE`) |
| Vendored | `python_programs/` (buggy), `correct_python_programs/` (fixed) and `json_testcases/`, copied byte-for-byte from that commit |

The programs were written for the Quixey Challenge and curated by the QuixBugs
authors. None of them was written for SBG, and none was used to develop SBG.

Each subject program has exactly one real bug. That bug is the positive pair
(fixed against buggy). The negatives are made from the fixed program with the
repository's own semantics-preserving transformers, and are stored under
`variants/`.

Only the **input** half of each `json_testcases` line is ever used. Expected
outputs are discarded when the file is loaded
(`experiments/final/external_quixbugs.py:load_declared_inputs`).

`manifest.json` lists every file: eligibility, exclusion reason, interface and
split (`external_test` for all programs). The manifest and the negatives were
hashed into `artifacts/final/freeze_quixbugs.json` before any pair was scored.
