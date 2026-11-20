# Security recovery report (Decision 3: macOS security counts 3/15/5/2)

Date: 2026-11-20. Scope: read-only search of the source repository, then a re-execution of the producing script in a scratch copy. No file in `~/Desktop/SBG-V8-LINUX` was modified, and no file under `phase3/` was touched.

## Result

**Recovered and verified.** The evidence file exists and the manuscript counts reproduce exactly from it.

- Manuscript claim (`sections/results.tex`, line 10): "Of 25 attacks and probes, 3 were blocked, 15 detected, 5 had no effect and 2 succeeded."
- Source file: `paper/IEEE_ACCESS_V8_FINAL/audit/security_rerun_darwin.json` in `~/Desktop/SBG-V8-LINUX`, tracked in commit `df612db0`.
- Recount from the file: **blocked 3, detected 15, no effect 5, succeeded 2; total 25.** Matches.
- Re-execution on macOS at the frozen commit: outcomes and verdicts are identical to the original file (only the timestamp and duration differ). The recount is the same.

An earlier note in the working summary said this file was "absent". That was wrong. The file was present; the earlier check looked at the wrong path.

## How the 25 are formed

The file has 27 rows. Two are excluded from the count as controls, which matches the manuscript's "25 attacks and probes":

| Set | Rows | Included in the 25 |
|---|---|---|
| `forgery_suite` | 21 | 20 (excludes `H00_honest_control`) |
| `sensing_probes` | 6 | 5 (excludes `SENSE07_benign_control`) |

Outcome categories, from the `outcome` field, by prefix:

| Category | Count | Entries |
|---|---|---|
| blocked (`BLOCKED by engine`) | 3 | A03, A04, A05 |
| detected (`DETECTED by …`) | 15 | A01, A02, A07, A08, A16, A17, P01–P07, P09, SENSE04c |
| no effect (`NO EFFECT …`) | 5 | A06, A07c, SENSE04, SENSE04d, SENSE01 |
| succeeded (`SUCCEEDS (open)…`) | 2 | P08, SENSE04b |

The two successes match the manuscript text (P08, the out-of-scope key-holder forgery, and SENSE04b, the code-object filename probe). The A17 entry is detected, not succeeded, which matches the manuscript's description of it as "denial of a true divergence".

## Provenance

- Producing script: `paper/IEEE_ACCESS_V8_FINAL/scripts/audit_security_rerun.py`, added in `df612db0`. It calls `trust.forgery_suite()` and six sensing probes through the real collector, then writes `audit/security_rerun_<platform>.json`.
- The code it runs is frozen. The `sbgv8/` tree hash is `8728842f129fe5ba493b6592ab4fa2304333407a` at `2edfe568`, at HEAD, and at `df612db0`.
- Run metadata in the original file: `platform=darwin`, `host=macOS-26.7-arm64-arm-64bit-Mach-O`, `python=3.13.15`, `utc=2026-11-19T17:03:13Z`, `duration_s=8.6`. Capability states: `network_denial`, `write_confinement`, `rlimit_cpu`, `rlimit_nofile`, `rlimit_fsize`, `rss_watchdog`, `process_group_kill` ACTIVE; `rlimit_as` and `rlimit_nproc` UNAVAILABLE.

## Re-execution

- Scratch copy: `closeout/recovered_security/rerun_full/` (full `git archive` of commit `2edfe568`, plus the producer script from `df612db0`).
- Command: `venv313/bin/python -I paper/IEEE_ACCESS_V8_FINAL/scripts/audit_security_rerun.py`
- Exit code: 0 (`closeout/recovered_security/rerun_full_exit.txt`). Log: `closeout/recovered_security/rerun_full_stdout.log`.
- Output: `closeout/recovered_security/security_rerun_darwin.recomputed.json`.
- Comparison with the original, excluding `meta.utc` and `meta.duration_s`: **identical**.

Two earlier attempts failed and are recorded here so the trail is complete:
1. Script run from a partial archive (`sbgv8 sbgv7 sbg` only): `ModuleNotFoundError: sbgv6`. The archive was incomplete; no result was produced. `closeout/recovered_security/rerun_stdout.log` and `rerun_run2/` are from this attempt and are not evidence.
2. Script run from `2edfe568` without the `df612db0` script: the script is absent at that commit. Not evidence.

## Limitations (stated, not removed)

- Single run per file on one host, as in the original. The sensing and forgery outcomes are not repeated across runs, so run-to-run variability is not measured.
- The file records the platform as darwin only. Nothing in the file speaks to Linux or Docker isolation, which the project itself lists as not reproduced.
- The manuscript's reproducibility table (`sections/reproducibility.tex`, line 23) cites commit `07ecd5b7` in its commit column. That column records the code commit the audit ran against. `07ecd5b7` has the same `sbgv8/` tree as `2edfe568`, so the citation is accurate for the code. The artifact file itself was first committed in `df612db0`. No change was made to the table.
- The security claims concern in-process harness forgery and result-channel attacks against this implementation. They are not an external validation and are not confirmatory evidence for the SBG methodology.

## Decision

Counts retained: **3 / 15 / 5 / 2 (of 25)**, labelled as a single-run audit at the frozen commit on macOS. No count is removed. The reproducibility-table commit reference is accurate as written and was left unchanged.
