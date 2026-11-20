# Raw execution evidence index
New file; linked from `../README.md`. Status: **present** (inspected), **referenced-absent** (cited by a document but not found), **absent**.

| Evidence | Location | Status | Notes |
|---|---|---|---|
| QuixBugs upstream files | `external/quixbugs/` (commit `4257f44b…`) | present | Resolves upstream |
| BugsInPy units + manifest | `external/bugsinpy/` (55 units; manifest 501 bugs, 51 eligible) | present | Catalogue commit resolves |
| V8 dev records | `datasets/v8/dev_records.jsonl` | present | 312 records |
| V6 phase-2 raw runs (QuixBugs, BugsInPy units, per-run `evidence.jsonl`, `verdict.json`, `stderr.txt`) | `../SBG-V6-phase2-raw-archive/p2_e*.tar.gz`, 7 archives, `SHA256SUMS.txt` verified OK | present (outside repo) | Real executions of dev subjects. Their link to the V8 dev records has not been verified. Not extracted |
| Earlier per-pair feature CSVs | `reports/external_validation/*_pairs.csv`, `SBG_*_RESULTS.csv` | present | Feature values only, no raw traces |
| Bugs.jar/Codeflaws raw traces | none | absent | Only `*_TRACE_DIAGNOSTICS.csv` summaries |
| Earlier BugsInPy pair file `pairs_bugsinpy_output_free_v7.jsonl`, `bugsinpy_purge_rescore.json` | cited path `../SBG/artifacts/...` | referenced-absent | |
| QuixBugs harness inputs | cited path `IEEE_ACCESS_PRE_SUBMISSION/.../quixbugs` | referenced-absent | |
| Original Linux VM `/root/sbg_sprint` | this machine | **absent** (`/root` does not exist) | Not recoverable here |
| Podman images/container logs | anywhere searched | absent | |
| Five-dataset sources/builds | none | n/a | Generated cases; see `../external_validation_audit/` |
