# WPD-D3 — PROBE LOG (what was actually executed)

Scope: feasibility only. **No SBG scoring was run. V10-test / V9c-val were never touched. SBG repo was only read** (the one Python import of
`SBG/experiments/final/protocol.py` is a read-only `importlib` load of a pure-`ast`/`typing` module with `PYTHONDONTWRITEBYTECODE=1`; its sha256 is recorded in
`probes/P04_static_refactory.json` → `protocol_sha256`).
All probe scripts/outputs: `probes/` (this directory). sha256 of every script/output: `probes/P99_sha256_manifest.txt`.
Interpreter for execution probes: `venvs/py313/bin/python` (CPython 3.13.5), `PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1`, subprocess per program, 1 s/call alarm, 2 s import alarm, 40 s hard cap, `stdin=/dev/null`, throw-away cwd.

## Environment checks (shell one-liners, not scripted)
| Check | Result |
|---|---|
| Network (`curl --max-time 8`), 2026-11-14 ≈20:40 IST | github.com 200, pypi.org 200, huggingface.co 200 |
| Disk | 476 GiB free |
| pip cache (`~/Library/Caches/pip`) | only unrelated wheels (red_black_tree_mod, numpy 1.26.4-cp314, safe_pysha3, neo4j) |
| HF cache (`~/.cache/huggingface/hub`) | only `microsoft/codebert-base` |
| `venvs/py313`, `venvs/py39` | pytest/pluggy/pygments/iniconfig/packaging only (no mutmut / cosmic-ray / MutPy / datasets / pyarrow) |
| `/usr/bin/python3` 3.9.6 | has hypothesis, pytest*, no mutation tools |
| `/opt/homebrew` python 3.11 / 3.14 | stdlib incl. `Lib/test` (519 entries, 26 MB for 3.11); pytest(+asyncio) on 3.11 |
| Dataset directories in workspace | only `SBG/external/{bugsinpy,quixbugs,quixbugs_java}` (+ SBG artifacts); no HumanEval/MBPP/CodeNet/Defects4J copies |

## Probes
| ID | Script | What it did | Executed dataset code? | Network | Output |
|---|---|---|---|---|---|
| P01 | `P01_metadata_fetch.py` | GitHub API / HF API / PyPI JSON metadata (licence, size, language, files) for ~30 repos, 16 HF datasets, 16 PyPI packages | no | yes (metadata only) | `P01_metadata.json` (fetched 2026-11-14T15:13Z). Some GitHub names guessed by D3 returned 404 (ManySStuBs4J/ManySStuBs4J, TypeBugs/TypeBugs, ExpertiseModel/Defects4Py, Jungfrau-ai/debugbench, Spirals-Team/defects4j-dissection, cqse/refactoring-oracle, tdurieux/RefactoringMiner) → those are **UNVERIFIED**, not "non-existent". Rows for `nlp-uoregon/trankit` and `FSoft-AI4Code/CodeCapybara` are accidental noise (ignore). |
| P02 / P02b | `P02_arxiv_abstracts.py` | arXiv API titles + abstracts for BugSwarm, OctoPack(HumanEvalPack), ManySStuBs4J, CodeNet, BugLab(PyPIBugs), AlphaCode, CodeXGLUE, MBPP, GitBug-Java, DebugBench, SeqCoBench (2408.11081) | no | yes | `P02_arxiv.json`, `P02b_seqcobench_arxiv.json` |
| P03 | `P03_download_small.py` | Downloaded Refactory `data.zip` (1,921,407 B), HumanEvalPack-python via HF datasets-server (164 rows, 474,439 B merged) | no | yes | `data/P03_downloads.json` (sha256s) |
| (inline) | `curl` | SeqCoBench train/valid/test CSVs (3,529,690 / 1,349,739 / 2,198,009 B), EquiBench OJ_A/OJ_V/OJ_VA `pairs.jsonl` (2,121,041 / 2,143,143 / 1,850,278 B) | no | yes | `data/seqcobench_*.csv`, `data/P10_seqcobench_sha256.txt`, `data/equibench/*.jsonl` |
| P04 | `P04_static_eligibility.py` | **Static** (`ast`) SBG entry-selection/eligibility on Refactory (4,225+5 programs) and HumanEvalPack (164×2) using SBG's frozen rule | no | no | `P04_static_refactory.json`, `P04_static_humanevalpack.json` |
| P05 | `P05_worker.py`, `P05_run.py` | Ran each HumanEvalPack canonical+buggy (328) and Refactory reference/correct/wrong (4,393) program on **SBG's frozen entry rule + 11-input battery**, recorded outcome signature (return repr[:300], exception type, stdout[:200], post-call argument repr[:300]). **No trace features, no distance, no SBG score.** First launch was killed after HEP finished (HEP file kept); relaunched for Refactory only (`fail/` subfolder not run, see FEASIBILITY §11). | yes (dataset code, sandboxed subprocess) | no | `P05_hep_outcomes.json`, `P05_refactory_outcomes.json`, `P05_run.log` |
| P06 | `P06_analyze_hep.py` | HEP battery-observability | no | no | `P06_hep_observability.json` |
| P07 / P07b | `P07_minify_probe.py`, `P07b_minify_behaviour.py` | Installed `python-minifier 3.4.0` + `libcst 1.9.0` into **D3-private venv** `probes/_venv_tools` (27 MB); minified 164 canonical solutions with annotations preserved; checked outcome equality on battery | yes (164 variants) | yes (pip) | `P07_minify.json`, `P07b_minify_behaviour.json`, `data/hep_min/` |
| P08 | `P08_stdlib_scan.py` | **Static** scan of local CPython 3.11 Lib for self-contained public functions | no | no | `P08_stdlib_scan.json` |
| P09 | `P09_analyze_refactory.py` | Refactory battery-observability / label recovery | no | no | `P09_refactory_observability.json` |
| P10 / P10b | `P10_seqco_prepare.py`, `P10_seqco_run.py` | SeqCoBench: write sources, split/leakage audit, edit sizes (static); then battery run of 1,134 originals + 14,572 transformed (15,706 programs, 178 s) | yes | no | `P10_seqco_static.json`, `P10_seqco_outcomes.jsonl`, `data/seqco_rows.jsonl` |
| P11 | `P11_hep_editsize.py` | Static edit-size confound for HEP CH vs minifier-EQ | no | no | `P11_hep_editsize.json` |
| P12 | `P12_equibench_static.py` | Static eligibility + stdin usage on EquiBench OJ pairs | no | no | `P12_equibench_static.json` |
| P13 | `P13_analyze_seqco.py` | SeqCoBench label reliability / observability / stratum yield | no | no | `P13_seqco_observability.json` |
| P14 | `P14_seqco_static_shortcut.py` | Label-only static shortcut AUROCs (token-bag, AST-bag, edit size) on validated SeqCoBench pairs; cluster bootstrap B=1000 seed 42 (descriptive) | no | no | `P14_seqco_static_shortcut.json` |
| P15 | `P15_overlap_check.py` | Exact function-level AST overlap of SeqCoBench originals / HEP canonical / Refactory references against 14,257 SBG `.py` files (read-only) | no | no | `P15_overlap.json` |
| P16 | `P16_seqco_prior_crosscheck.py` | Re-derived prior in-repo SeqCoBench counts (zero-exception originals, e=2 programs/pairs) with D3's oracle; compared to Agent 3 report | yes (SeqCoBench programs, from P10 outcomes) | no | `P16_seqco_prior_crosscheck.json` |

Total new downloads ≈ 19.5 MB of data + pip wheels (python-minifier, libcst and pip deps; well below the 50 MB cap). **Not downloaded (size/justification):** CodeContests 7.6 GB, CodeNet 7.8 GB, APPS 1.4 GB, CPython repo 0.9 GB, Defects4J ~150 MB (+checkouts); none feeds the feasibility check beyond what proxies (EquiBench OJ) already show.

## Known limitations of the probes (read before citing any number)
1. Outcomes were recorded **once per program** (no 5-run determinism check as in `output_free_v8`). A frozen experiment must re-run twice and drop non-deterministic programs (log them).
2. Outcome comparison uses exception **type** (not message), `repr()` truncated at 300 chars, stdout truncated at 200 chars. SBG's own label definition (output/exception/stdout/argument-mutation) is approximated, not reproduced bit-for-bit.
3. Entry selection is SBG's own `select_entry_output_free`; the 11 inputs are SBG's own `synthesise_inputs` (zip of per-family batteries). Class-tier driving (`output_free_v7` class fallback) was **not** exercised.
4. Observability counts are properties of (program pair, fixed battery) and say nothing about SBG's score.
5. Python 3.13.5 only. Programs that need `typing` features beyond 3.13 or `from __future__` oddities were not specially handled; `import_fail` rows are kept and counted.
6. `SBG/.pytest_cache/v/cache/{nodeids,lastfailed}` carry a modification time newer than 18:00 today. D3 never ran pytest; this was caused by another session/agent and is flagged for the orchestrator's EXP-ORCH-006 tree check.
