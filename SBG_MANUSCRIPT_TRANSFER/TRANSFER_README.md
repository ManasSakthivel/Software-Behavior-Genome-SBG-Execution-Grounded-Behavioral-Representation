# TRANSFER_README — SBG November manuscript-evidence package (FAST TRANSFER, essential subset)

Transferred 2026-11-16 from the Mac where the November 2026 SBG work was done. Source trees were only READ (copied byte-for-byte; no file content changed). The original `SBG/` source was not touched (re-hash of its 16,137 BEFORE-listed files: 0 differences; no file newer than the BEFORE manifest).

**Being transferred is NOT verification.** Nothing here has been independently re-verified by this transfer. Reports such as `05`/`05b` ("VERIFIED PASS", "CONFIRMED") are the originating agents' own statements; WP-D (external validation) found several earlier claims to be contradicted (see `IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/08C_EXTERNAL_VALIDATION.md`).

## What was checked in this transfer
- Every copied file was compared (SHA-256 + size) with its source at copy time: see `SHA256SUMS.txt` (one line per transferred evidence file; paths relative to this directory). Check on the new Mac: `cd SBG_MANUSCRIPT_TRANSFER && shasum -a 256 -c SHA256SUMS.txt`.
  The 4 generated documents (`FILE_INVENTORY.md`, `SHA256SUMS.txt`, `TRANSFER_EXCLUSIONS.md`, `TRANSFER_README.md`) are not listed in it.
- Pre-existing manifests are preserved as transferred (e.g. `WP_E_MATH_GRAY_CODE/MANIFEST.sha256`, `WP_LITERATURE_FOLLOWUP/MANIFEST.sha256`, `WP_C_ABLATIONS/configs/WPC_RV_PREDECLARATION.sha256`, `WP_D_.../probes/P99_sha256_manifest.txt`, `logs/sbg_tree_sha256_BEFORE.txt`). They were not regenerated.
- Automated regex scan of all staged files (gzip decompressed): no private keys, cloud/GitHub/Slack/Google/OpenAI-style tokens, JWTs, credentialed URLs or `password=`-style secrets. Remaining hits are placeholders/field names/fake fixtures (listed in `TRANSFER_EXCLUSIONS.md` §D). The local macOS user name `manassakthivel` appears inside absolute paths in many logs/scripts (kept unmodified).
- COBOL/IBM check: the report that names local client/employer-looking mainframe source trees (`paper/empirical_sprint_2026-11-04/agent_7/`) was WITHHELD. No `.cbl/.cpy` source is included. No other IBM-proprietary material was found, but this was a pattern scan, not a legal review.

## Directory structure
| Directory | Content |
|---|---|
| `IEEE_ACCESS_PRE_SUBMISSION/` | The November evidence package, original relative layout |
| `SBG_repo_docs/` | Selected documents from the read-only `SBG/` repo (original relative paths): `artifacts/paper_evidence/*.md` (claim matrix, novelty position, readiness, sprint report, blueprint, ...), `reports/` (sprint2 + remediation incl. `FINAL_RESEARCH_READINESS_REPORT.md`), `docs/archive/v2/FEATURE_ORACLE.md`, selected `docs/current/*.md`, 2 files from `paper/final_empirical_readiness_2026-11-05/` |
| `workspace_root_docs/` | Workspace-level audit/plan (2026-11-04) and `reports/sprint2` copy |
| `FILE_INVENTORY.md`, `SHA256SUMS.txt`, `TRANSFER_EXCLUSIONS.md`, `LITERATURE_EXCLUDED_LIST.md`, this file | Transfer metadata |

## Workstreams (all under `IEEE_ACCESS_PRE_SUBMISSION/`)
| Workstream | Where | Key files |
|---|---|---|
| WP-C ablations / return-value | `WP_C_ABLATIONS/` | `08A_ABLATION_RESULTS.md`, `08B_RETURN_VALUE_ARCHITECTURAL_ANALYSIS.md`, `WPC_EXPERIMENT_REGISTRY.md`, `raw/EXP-WPC-001..006`, `tables/`, `configs/` (incl. pre-declaration + sha256), `scripts/`, `logs/` (incl. failed first attempts) |
| WP-D external validation | `WP_D_EXTERNAL_VALIDATION/` | `08C_EXTERNAL_VALIDATION.md`, `08D_DATASET_COMPATIBILITY_AND_LIMITATIONS.md`, `WPD_EXPERIMENT_REGISTRY.md`, `WPD_registry.jsonl`, `REPRODUCTION_INSTRUCTIONS.md`, `raw/WPD-D1..D4`, `scripts/`, `logs/` |
| WP-E math_gray_code | `WP_E_MATH_GRAY_CODE/` | `MATH_GRAY_CODE_FAILURE_ANALYSIS.md`, `diagnostic_probe_results.json`, `micro_probe_threads.py`, `run_full_diagnostic.py`, `probe_math_gray_code.py`, `reproduction_commands.sh`, `MANIFEST.sha256` |
| A4 baselines & evaluation | top-level `04_`, `05_`, `05b_`, `06_*.md`, `EXPERIMENT_RECOVERY_AND_REGISTRY.md`; `WP_A_B_COMPARATIVE_BENCHMARK/`; `experiments/competitor_baselines/`; `experiments/statistical_verification/a4d/`; `results/raw/EXP-A4*`; `results/tables/EXP-A4C-*`; `logs/registry/A4C.jsonl, A4D.jsonl` | frozen config `results/raw/EXP-A4C-002/frozen_config.json` (SHA `f52bfaee96f501fc19198de2a585dcfc500e0ae21e13f2dec0d3d670251e7bdb`), predictions `results/raw/EXP-A4C-003/predictions/{v10_test,v9c_val,v9c_dev,v9c_train}/`, evals `EXP-A4C-004/`, incremental/sensitivity `EXP-A4C-005/`, verification `EXP-A4D-005/` |
| A1/A2/A3 audits | `01_`, `03_`, `07_`, `09_*.md`, `reproduction/` (scripts, logs, REPRODUCE.md), `results/raw/EXP-A3-*`, `results/raw/repro/`, `experiments/statistical_verification/` | |
| WP-F review, literature | `WP_F_ADVERSARIAL_REVIEW/`, `WP_LITERATURE_FOLLOWUP/`, `results/raw/literature/` (metadata only) | |
| Governance | `configs/` (PROTOCOL, ADDENDUM, frozen populations), `HANDOFF/`, `experiments/common/`, `logs/` | |

## A4: what was actually completed (from file evidence at transfer time, not from reports)
- Held-out prediction files EXIST for `v10_test` (214 method files × 638 rows) and `v9c_val` (212 × 432), plus `v9c_dev` (212 × 464) and `v9c_train` (212 × 1610); each folder also holds `_population_info.json`. Checked by counting rows in the files.
- `EXP-A4C-002/frozen_config.json` and `models.pkl` have mtime 2026-11-14 20:19:17; `v10_test`/`v9c_val` prediction files have mtime 21:45:32–21:45:39 (dev/train 20:20:38). So the held-out scoring files post-date the freeze file by file-time. Whether labels were unseen before the freeze is a claim of the A4 reports, not proven by file times alone.
- `EXP-A4C-001..005` and `EXP-A4D-002..005` are registered COMPLETED in `logs/registry/A4C.jsonl, A4D.jsonl`. `EXP-A4R-001` exists (`VERIFIED_BASELINES.json`).
- Wave-2 competitors (`competitors_new/`, `EXP-A4B-001`, `WP_A_B_.../raw/EXP-A4R-002..006`) were run on v9c dev/train only (development/exploratory); they were NOT scored on held-out data.
- v9c_train has 45/46 programs (1610 of 1650 pairs): `math_gray_code` trace failure was DIAGNOSED by WP-E (thread leak on a runaway-loop mutant), but this transfer does not show a regenerated trace cache for it.

## Missing, excluded or incomplete (critical)
- **Withheld by the secret-scanner hook (false positives, not bypassed): `configs/populations/v9c_dev.json`, `v9c_train.json`, `v9c_val.json`** (frozen V9c population rows + scores). Hashes and instructions: `TRANSFER_EXCLUSIONS.md` §E. `v10_test.json` and `SUMMARY.json` are present. Many analyses that need V9c pair labels (e.g. `eval_lib.load_population`) cannot run on the new Mac until these three are copied over; the per-method prediction files (`EXP-A4C-003/predictions/*`) already carry labels.
- NOT FOUND on the source Mac: `references.bib` (no `.bib` or `.tex` at all, i.e. no LaTeX manuscript or draft), `IEEE_ACCESS_READINESS_AUDIT.md` (closest: `SBG_repo_docs/artifacts/paper_evidence/FINAL_IEEE_ACCESS_READINESS.md`), `ARTIFACT_MANIFEST_FINAL.md`, `00_EXECUTIVE_SUMMARY`, `02_SCIENTIFIC_CONTRIBUTION...` (only first-pass `WP_F_.../02_..._FIRST_PASS.md`), merged `08_ROBUSTNESS_ABLATION_AND_EXTERNAL_VALIDATION.md`, `10_ADVERSARIAL_REVIEWER_2_REPORT` (only `WP_F_.../10A_...`), `11_`, `12_`. Registries `A4R.jsonl`, `A4B.jsonl`, `AI.jsonl`, `A5*.jsonl` do not exist in `logs/registry/` (WPC/WPD registries are in their own directories).
- `FEATURE_ORACLE.md`: only the archived v2 version (`SBG_repo_docs/docs/archive/v2/FEATURE_ORACLE.md`) exists. `CLAIM_TO_EVIDENCE_MATRIX.md`, `FINAL_NOVELTY_POSITION.md`, `FINAL_SPRINT_REPORT.md`, `FINAL_RESEARCH_READINESS_REPORT.md` exist in `SBG_repo_docs/` — these are older epochs (Oct–early Nov 2026), predate the November 14 package, and must not be combined with it without provenance.
- Withheld in this FAST pass (see `TRANSFER_EXCLUSIONS.md`): shared trace caches `results/raw/trace_cache/` (15 MB; regenerable with `experiments/common/dump_traces.py`), A4C feature files `EXP-A4C-001/features/` (47 MB; predictions are included, their inputs are not), superseded predecessor outputs `EXP-A4-002/`, `EXP-A4-003/`, all literature PDFs/text (30 each; list in `LITERATURE_EXCLUDED_LIST.md`), D3 downloaded third-party datasets (licences unverified; sha256 manifest included), D1 vendored-unit copies (already in the public SBG repo), D2 full SBG copies (only re-run outputs differing from SBG were kept), `reproduction/clean_checkout*` and `scratch` (full SBG copies), 2 files containing a third-party e-mail address, the COBOL `agent_7` report.
- Excluded not for size but for permission/personal-data reasons (owner decision): `agent_7` COBOL material, third-party datasets (X03), literature PDFs (X02), dblp challenge pages (X08).
- Incomplete / exploratory (from WP registries): WP-D — D2 reproduction subagent never wrote `REPRO_REPORT.md` (`raw/WPD-D2_repro/D2_STATUS.md`); SeqCoBench replication `WPD-X1` is PLANNED, NOT EXECUTED; no dataset qualified as a valid independent evaluation; BugsInPy/QuixBugs are exploratory only. WP-C — state/return-value variants are exploratory modified-SBG experiments, never evaluated on V10; tracer event-cap/timeout/input-subset sensitivity NOT DONE. A4 — see above. WP-F — first pass only.

## Provenance issues to keep in mind
1. Epochs: `IEEE_ACCESS_PRE_SUBMISSION/` = 2026-11-14 package on repo commit `3425693b432bb774b10db1cf3185eae1a7eef095` (branch `remediation/sbg-v4`). `SBG_repo_docs/` = older sprint documents (Oct 2026 – 5 Nov 2026), some from untracked `paper/` and `reports/sprint2`. Headline numbers there (e.g. earlier external AUROCs) are not interchangeable.
2. Population sizes: V10 638/19, V9c-val 432/11, V9c-dev 464/13, V9c-train 1610/45 (1650/46 before the `math_gray_code` exclusion).
3. External AUROCs 0.497 (BugsInPy) and 0.444 (QuixBugs) reproduce only after a POST-HOC exclusion of SP-2 negatives; pre-registered values are 0.410 / 0.388 (WP-D `08C`).
4. Absolute paths in scripts/logs point to `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/...`; reproduction on another Mac needs path edits. Reproduction needs Python 3.13.x (results bit-identical only on 3.13) and the SBG repo at the stated commit — not included here (it is the repo this branch lives in; check out branch `remediation/sbg-v4`).
5. 37 `.pkl` files (frozen A4 models) execute code when unpickled; load only in a trusted environment.

## Important reproduction commands (copied from the package; not re-run by this transfer)
```
export PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1
PY=<python3.13>; PKG=<path to IEEE_ACCESS_PRE_SUBMISSION>; cd $PKG
# A4 evaluation (see 06_COMPARATIVE_BENCHMARK_REPRODUCTION.md): experiments/competitor_baselines/run/{run_all,eval_all}.py ; verification: experiments/statistical_verification/a4d/exp_a4d_005_verify_predictions.py
# A3 external AUROC recompute (cheapest check of 0.497/0.444 from stored scored files): $PY experiments/statistical_verification/recompute_external_auroc.py   (needs SBG/artifacts/final/pairs_*.jsonl)
# WP-D: WP_D_EXTERNAL_VALIDATION/REPRODUCTION_INSTRUCTIONS.md ; WP-E: WP_E_MATH_GRAY_CODE/reproduction_commands.sh ; WP-C: WP_C_ABLATIONS/scripts/ + WPC_EXPERIMENT_REGISTRY.md
```
