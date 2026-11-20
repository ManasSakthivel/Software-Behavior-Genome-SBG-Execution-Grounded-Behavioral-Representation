# Reproducibility

Short guide; the full protocol is `research/reproducibility/REPRODUCIBILITY_PROTOCOL.md`.

Scope: everything here regenerates **exploratory development** results on 321 non-pristine pairs. It cannot regenerate any confirmatory or held-out result because none exists.

Requirements: macOS (isolation uses `sandbox-exec`), CPython 3.13 in `.venv`, numpy, scipy, pandas, matplotlib, pytest.

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt numpy scipy pandas matplotlib

scripts/run_evaluation.sh --dry-run   # preflight + print stages, executes nothing
scripts/run_evaluation.sh --quick     # tests/v7 + tests/v6 + QuixBugs-only pipeline into results/repro/quick_<time>/
scripts/run_evaluation.sh --full      # all 321 pairs; FIRST stage is the legacy `pytest tests -q`, which did not finish in >77 CPU-min (see Phase 2 below)
```

The script stops with a non-zero exit on the first failing stage. It never writes into the committed `results/processed`, `results/statistics`, `results/figures` or `results/postfix`.

**The committed `results/postfix/` files are the OLD engine (before Phase 2) and are not the reference for the current engine.** The current reference is `results/v7b_phase2_summary/`. For historical comparison only, a `--full` run can be compared with the post-fix files (`results/postfix/`; `results/processed/` is the superseded pre-fix run): `results/postfix/processed/k1_spike_summary.json` (verdict counts, exact match expected), `baselines_per_pair_final.jsonl` there, `results/postfix/statistics/*.json` (CIs match for the same seed and library versions). `--quick` output is a pipeline smoke test and is not comparable with committed results.

Committed result files (the only source for numbers quoted in the README): `results/postfix/` (current), `results/processed/`, `results/statistics/`, `results/figures/` (pre-fix), narrative in `research/evaluation/EXPLORATORY_RESULTS.md`.

Datasets: `datasets/README.md`. Seeds, determinism evidence, tolerances and known hazards: the protocol file.

## Phase 2 (current engine, local, exploratory)
Use [`docs/PHASE2_REPRODUCTION_GUIDE.md`](docs/PHASE2_REPRODUCTION_GUIDE.md) (commands for E1 and E3-E7, new output directories only, expected headline numbers) and [`docs/EXPERIMENT_PROTOCOL.md`](docs/EXPERIMENT_PROTOCOL.md) (summary of the pre-registration). Key points:
- Do not run `scripts/run_evaluation.sh --full` unmodified: its legacy `pytest tests -q` stage was killed after more than 77 CPU-minutes without finishing. E3 was run as the same stages with the tests stage replaced by `pytest tests/v7 tests/v6` (recorded in `results/v7b_phase2_summary/p2_e3_20261118_092700/E3_COMMANDS.sh`).
- Test counts, with the suite named: `tests/v7` alone 276 passed, 1 skipped (277 tests, recorded at `5efcef74`, sources unchanged at HEAD); `tests/v7` + `tests/v6` 286 passed, 1 skipped (E3 run); all of `tests/` never completed.
- Reproduction is by verdict counts and the consistency rule (at most 3 of 321 pairs differing between same-engine runs), not byte equality. Witness ids can depend on timing near resource limits; the child hash seed is fixed at 0 (hash-order sensitivity untested); `datetime.now` is not virtualised; macOS only.
- Verify evidence with `python -m sbgv7 verify DIR` (exit 0 verified, 1 mismatch, 2 unreadable, 4 omitted by size cap). It re-derives verdicts from recorded facts and executes nothing; the log is not tamper-proof.
- Compact results: `results/v7b_phase2_summary/`. Raw evidence archives (not in git): `~/Desktop/SBG-V6-phase2-raw-archive/`, sha256 in `results/v7b_phase2_summary/RAW_ARCHIVE_SHA256SUMS.txt`.
- Documentation check: `.venv/bin/python scripts/check_docs_v7b.py` (or `make verify-docs-v7b`).
- Not reproducible here, deferred to Phase 3: Linux/Docker isolation, K1, K5, independent holdout, comparison with published tools, hash-order E2, trust anchor.
