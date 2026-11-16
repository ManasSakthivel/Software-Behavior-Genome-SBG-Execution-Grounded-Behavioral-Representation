# TRANSFER_EXCLUSIONS

Everything below exists on the source Mac but was NOT transferred. Original paths are relative to `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/IEEE_ACCESS_PRE_SUBMISSION/` unless prefixed `SBG/` (relative to `.../SBG-FINALREVIEW/`). Nothing was altered or deleted at the source. Bulk copies are listed per directory; individually withheld files are listed one by one.

Always skipped as non-evidence: `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.DS_Store`, virtualenvs, `.git`.

## A. Withheld because redistribution permission is unclear, or because of personal information (owner decision needed)

| Rule | Original path(s) | Files | Bytes | Reason |
|---|---|---:|---:|---|
| X04 | `WP_D_EXTERNAL_VALIDATION/raw/WPD-D1_compat/unit_copies/` | 447 | 417495 | Byte copies of vendored BugsInPy/QuixBugs units (upstream licences incl. GPL-3.0 ansible units). Already tracked in the public SBG repo under external/; sha256 listings in raw/WPD-D1_compat/data/ ARE transferred |
| X03 | `WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/_venv_tools/` | 837 | 14677688 | Private virtualenv (python-minifier, libcst); environment, not evidence |
| X03 | `WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/data/` | 20707 | 28789114 | Third-party datasets downloaded for feasibility probes (HumanEvalPack, Refactory, SeqCoBench, EquiBench, ...); licences UNVERIFIED (see WPD-D3 FEASIBILITY.md); sha256 manifest P99_sha256_manifest.txt IS transferred |
| X08 | `results/raw/literature/dblp/changeguard.json`, `results/raw/literature/dblp/kessel_atkinson_search.json` | 2 | 14978 | Captured anti-bot challenge HTML page (not data) containing a third-party individual's e-mail address (personal information) |
| X02 | `results/raw/literature/pdf/` | 30 | 39450667 | Third-party copyrighted publisher/arXiv PDFs (30 files); redistribution permission not established. Bibliographic metadata (crossref/openalex/arxiv/gh) IS transferred. |
| X02 | `results/raw/literature/text/` | 30 | 3089827 | Plain-text extractions of the copyrighted PDFs; same redistribution concern |

## B. Withheld as bulk reproducible copies / environments / non-document files (no new evidence lost)

| Rule | Original path(s) | Files | Bytes | Reason |
|---|---|---:|---:|---|
| X05 | `WP_D_EXTERNAL_VALIDATION/raw/WPD-D2_repro/runs/` | 145218 | 860035914 | Per-run full copies of the SBG tree (~214 MB each x 9). Only files that differ from / are absent in SBG/ (i.e. the re-run outputs) are transferred; identical copied source files are excluded |
| X05 | `WP_D_EXTERNAL_VALIDATION/raw/WPD-D2_repro/sbg_copy/` | 16137 | 95772529 | Full copy of the SBG tree used by D2. Only files that differ from / are absent in SBG/ are transferred |
| X09 | `WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/_venv_tools/bin/python`, `WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/_venv_tools/bin/python3`, `WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/_venv_tools/bin/python3.13` | 3 | 0 | Symbolic link (not copied) |
| X01 | `reproduction/clean_checkout/` | 15038 | 79091121 | Complete copy of the SBG source tree (made by A2 for clean-checkout reproduction); reproducible from the SBG repo, ~116 MB, no new evidence |
| X01 | `reproduction/clean_checkout_ci/` | 15038 | 79091113 | Complete copy of the SBG source tree (CI emulation); reproducible, no new evidence |
| X01 | `reproduction/clean_checkout_py39/` | 15038 | 79091113 | Complete copy of the SBG source tree (py3.9 run); reproducible, no new evidence |
| X01 | `reproduction/scratch/` | 15040 | 79095330 | Scratch copy of the SBG source tree; reproducible, no new evidence |
| X11 | `results/raw/EXP-A4-002/` | 9 | 20773367 | FAST-TRANSFER scope cut: predecessor A4 features (SUPERSEDED by EXP-A4C-001 per EXPERIMENT_RECOVERY_AND_REGISTRY.md). Not transferred in this pass |
| X11 | `results/raw/EXP-A4-003/` | 3328 | 17236729 | FAST-TRANSFER scope cut: predecessor A4 independent-input batteries (SUPERSEDED by EXP-A4C-001/indep). Not transferred in this pass |
| X11 | `results/raw/EXP-A4C-001/features/` | 176 | 21363887 | FAST-TRANSFER scope cut: A4C per-pair feature files (47 MB, inputs to predictions; predictions themselves ARE transferred). Not transferred in this pass |
| X10 | `results/raw/trace_cache/` | 3450 | 6665989 | FAST-TRANSFER scope cut: shared trace caches (15 MB, regenerable with experiments/common/dump_traces.py; math_gray_code missing in v9c_train). Not transferred in this pass |
| X06 | `SBG/artifacts/paper_evidence/ (non-document files)` | 53 | 2983700 | SBG repo evidence files other than documents (already tracked in the public repo, or not manuscript documents); only .md/.txt/.bib/.tex/.cff transferred from this directory |

Note on X03: only downloaded third-party datasets and the private virtualenv are excluded; probe scripts/outputs and `P99_sha256_manifest.txt` ARE transferred.
Note on X05: the D2 `runs/*` and `sbg_copy/` trees are full copies of the SBG source; only files that differ from, or are absent in, the read-only `SBG/` tree (i.e. the re-run outputs) were transferred, decided by byte comparison.
Note on X06: from `SBG/artifacts/paper_evidence`, `SBG/docs/*`, `SBG/reports/remediation` only text documents were transferred; the remaining files are already tracked in the public SBG repo.

## C. Individually withheld files (X02, X07, X08, X09)

| Rule | Original path | Bytes |
|---|---|---:|
| X09 | `WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/_venv_tools/bin/python` | 0 |
| X09 | `WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/_venv_tools/bin/python3` | 0 |
| X09 | `WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/_venv_tools/bin/python3.13` | 0 |
| X08 | `results/raw/literature/dblp/changeguard.json` | 7489 |
| X08 | `results/raw/literature/dblp/kessel_atkinson_search.json` | 7489 |
| X02 | `results/raw/literature/pdf/allamanis_probegen.pdf` | 840794 |
| X02 | `results/raw/literature/pdf/bugsinpy_arxiv.pdf` | 496852 |
| X02 | `results/raw/literature/pdf/cetbench.pdf` | 1193531 |
| X02 | `results/raw/literature/pdf/changeguard.pdf` | 823189 |
| X02 | `results/raw/literature/pdf/codeexecutor.pdf` | 662412 |
| X02 | `results/raw/literature/pdf/codenet.pdf` | 546453 |
| X02 | `results/raw/literature/pdf/danglot_dci.pdf` | 435912 |
| X02 | `results/raw/literature/pdf/envtrace.pdf` | 2946035 |
| X02 | `results/raw/literature/pdf/equibench.pdf` | 518334 |
| X02 | `results/raw/literature/pdf/fu_menzies.pdf` | 1234178 |
| X02 | `results/raw/literature/pdf/gdse_equiv.pdf` | 330847 |
| X02 | `results/raw/literature/pdf/impact_not_invalidation.pdf` | 355870 |
| X02 | `results/raw/literature/pdf/invariant_diffs.pdf` | 254783 |
| X02 | `results/raw/literature/pdf/kessel_codesearch_jss2024.pdf` | 2002150 |
| X02 | `results/raw/literature/pdf/kessel_dissertation_2023.pdf` | 4747715 |
| X02 | `results/raw/literature/pdf/kessel_fse2026_runtime_history.pdf` | 481325 |
| X02 | `results/raw/literature/pdf/kessel_openscience_jss2024.pdf` | 2073457 |
| X02 | `results/raw/literature/pdf/krinke_2025.pdf` | 952989 |
| X02 | `results/raw/literature/pdf/mokav.pdf` | 1935684 |
| X02 | `results/raw/literature/pdf/next_ni.pdf` | 1637298 |
| X02 | `results/raw/literature/pdf/numericaldiff.pdf` | 573339 |
| X02 | `results/raw/literature/pdf/ojdanic.pdf` | 3233705 |
| X02 | `results/raw/literature/pdf/output_equiv_oracles_miss.pdf` | 1048623 |
| X02 | `results/raw/literature/pdf/patchguru.pdf` | 2476412 |
| X02 | `results/raw/literature/pdf/piech_embed.pdf` | 847355 |
| X02 | `results/raw/literature/pdf/semadiff.pdf` | 500042 |
| X02 | `results/raw/literature/pdf/testora.pdf` | 696821 |
| X02 | `results/raw/literature/pdf/traced.pdf` | 2692479 |
| X02 | `results/raw/literature/pdf/wang_singh_su_dynamic_embedding.pdf` | 596706 |
| X02 | `results/raw/literature/pdf/wang_su_blended.pdf` | 2315377 |
| X02 | `results/raw/literature/text/allamanis_probegen.txt` | 62733 |
| X02 | `results/raw/literature/text/bugsinpy_arxiv.txt` | 31567 |
| X02 | `results/raw/literature/text/cetbench.txt` | 91567 |
| X02 | `results/raw/literature/text/changeguard.txt` | 81269 |
| X02 | `results/raw/literature/text/codeexecutor.txt` | 57997 |
| X02 | `results/raw/literature/text/codenet.txt` | 70808 |
| X02 | `results/raw/literature/text/danglot_dci.txt` | 97506 |
| X02 | `results/raw/literature/text/envtrace.txt` | 108515 |
| X02 | `results/raw/literature/text/equibench.txt` | 56256 |
| X02 | `results/raw/literature/text/fu_menzies.txt` | 74766 |
| X02 | `results/raw/literature/text/gdse_equiv.txt` | 49597 |
| X02 | `results/raw/literature/text/impact_not_invalidation.txt` | 43444 |
| X02 | `results/raw/literature/text/invariant_diffs.txt` | 72153 |
| X02 | `results/raw/literature/text/kessel_codesearch_jss2024.txt` | 170199 |
| X02 | `results/raw/literature/text/kessel_dissertation_2023.txt` | 722868 |
| X02 | `results/raw/literature/text/kessel_fse2026_runtime_history.txt` | 35463 |
| X02 | `results/raw/literature/text/kessel_openscience_jss2024.txt` | 134278 |
| X02 | `results/raw/literature/text/krinke_2025.txt` | 166337 |
| X02 | `results/raw/literature/text/mokav.txt` | 89834 |
| X02 | `results/raw/literature/text/next_ni.txt` | 112298 |
| X02 | `results/raw/literature/text/numericaldiff.txt` | 80700 |
| X02 | `results/raw/literature/text/ojdanic.txt` | 144908 |
| X02 | `results/raw/literature/text/output_equiv_oracles_miss.txt` | 83944 |
| X02 | `results/raw/literature/text/patchguru.txt` | 70940 |
| X02 | `results/raw/literature/text/piech_embed.txt` | 46353 |
| X02 | `results/raw/literature/text/semadiff.txt` | 63260 |
| X02 | `results/raw/literature/text/testora.txt` | 80452 |
| X02 | `results/raw/literature/text/traced.txt` | 74948 |
| X02 | `results/raw/literature/text/wang_singh_su_dynamic_embedding.txt` | 41296 |
| X02 | `results/raw/literature/text/wang_su_blended.txt` | 73571 |

X03/X04 individual file lists (hundreds of files) are in `exclusions.json` in the source-Mac work directory (`/Users/manassakthivel/Desktop/SBG-TRANSFER-WORK/`) and follow from the directory rule; SHA-256 listing for X04 is under `IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D1_compat/data/` and for X03 in `IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/P99_sha256_manifest.txt`.

## D. Reviewed and kept (not excluded), recorded for transparency

| Item | Decision |
|---|---|
| Absolute path `/Users/manassakthivel/...` (local macOS user name) in many logs/scripts/reports | Kept unmodified (evidence files must not be altered). Low-sensitivity identifier; already present in the public SBG repo (e.g. `cobol_inventory.py`). |
| `reviewer@example.org` in literature scripts | Placeholder address, kept |
| `api_key` strings in OpenAlex JSON | Field names in API responses, no secret values, kept |
| `Authorization: Bearer token123` in a copied test fixture (`bugsinpy_evaluation.py`) | Fake fixture string, kept |
| `git@github.com` strings in GitHub API metadata (`results/raw/literature/gh/`) | Public repository clone URLs, kept |
| `ibm.com` URLs in a Crossref reference list | Bibliographic citations of public web pages, kept |
| 3 saved HTML pages (arXiv abstract, PMLR abstract, a Cloudflare challenge page) in `results/raw/literature/` | Public pages used as literature evidence; kept; delete if you prefer |
| 37 `.pkl` files (frozen A4 models, features) | Own artefacts; kept. Pickle files execute code when loaded: load only in a trusted environment |
| QuixBugs Java sources / LICENSE (MIT) under `SBG_repo_docs/paper/.../_ws/` | Upstream MIT-licensed, licence file kept; the same corpus is vendored in the public SBG repo |
| COBOL/IBM check | Only `agent_7` (names of local client/employer-looking source trees) was withheld (X07). Other COBOL documents (`COBOL_CORPUS_INVENTORY.md`, `COBOL_EVALUATION_REPORT.md`, `cobol_inventory.py`) are already tracked in the public SBG repo; no `.cbl`/`.cpy` source files are transferred. |
| Automated scan | Regex scan of every staged file (gzip decompressed): private keys, AWS/GitHub/Slack/Google/OpenAI-style tokens, JWTs, bearer headers, `password/api_key/secret =` assignments, credentialed URLs, e-mail addresses, IBM/confidentiality markers. No credentials found. Raw results: `security_scan.json` in the source-Mac work directory. |

## E. Withheld by the commit-time secret scanner (IBM Vault Radar "Block Secrets" pre-commit hook; NOT bypassed)

The managed pre-commit hook blocked the first commit attempt with 43 "Secret assignment (medium)" findings, all in three frozen population files. Inspection of the flagged byte offsets shows numeric score fields (e.g. `"..._fraction": 0.0, "call_count": 0.98, "static_token": 0.1169...`), i.e. almost certainly false positives, but the hook was not bypassed (no breakglass, no `--no-verify`) and the files were not re-encoded to evade it. They were removed from the package instead:

| Original path (under `IEEE_ACCESS_PRE_SUBMISSION/`) | Bytes | SHA-256 (original) |
|---|---:|---|
| `configs/populations/v9c_dev.json` | 332298 | `4b8ff238566567b97824074472fa94e19189cbb55c3d56109d013809ff1c6fe4` |
| `configs/populations/v9c_train.json` | 1197504 | `3f252a9ad96bd620d81434f8aec94f4538124ecd76b92167a4a835ade54ce83a` |
| `configs/populations/v9c_val.json` | 307966 | `5e2e2e1ab3546a7271cf0f9bdeba1779ff090ca217f3e5764a862656b1310a8e` |

`v10_test.json` and `SUMMARY.json` (which carries all four hashes) ARE included. To obtain the three files: copy them from the source Mac (e.g. AirDrop), or raise the false-positive ticket / use the Block Secrets breakglass yourself, then verify against the SHA-256 values above. They are the frozen V9c populations: the V9c-val/dev/train pair rows with frozen SBG scores.
