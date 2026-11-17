# Reproducibility

Short guide; the full protocol is `research/reproducibility/REPRODUCIBILITY_PROTOCOL.md`.

Scope: everything here regenerates **exploratory development** results on 321 non-pristine pairs. It cannot regenerate any confirmatory or held-out result because none exists.

Requirements: macOS (isolation uses `sandbox-exec`), CPython 3.13 in `.venv`, numpy, scipy, pandas, matplotlib, pytest.

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt numpy scipy pandas matplotlib

scripts/run_evaluation.sh --dry-run   # preflight + print stages, executes nothing
scripts/run_evaluation.sh --quick     # tests + QuixBugs-only pipeline into results/repro/quick_<time>/
scripts/run_evaluation.sh --full      # all 321 pairs, all baselines; long; into results/repro/full_<time>/
```

The script stops with a non-zero exit on the first failing stage. It never writes into the committed `results/processed`, `results/statistics`, `results/figures` or `results/postfix`.

Compare a `--full` run with the committed post-fix files (`results/postfix/`; `results/processed/` is the superseded pre-fix run): `results/postfix/processed/k1_spike_summary.json` (verdict counts, exact match expected), `baselines_per_pair_final.jsonl` there, `results/postfix/statistics/*.json` (CIs match for the same seed and library versions). `--quick` output is a pipeline smoke test and is not comparable with committed results.

Committed result files (the only source for numbers quoted in the README): `results/postfix/` (current), `results/processed/`, `results/statistics/`, `results/figures/` (pre-fix), narrative in `research/evaluation/EXPLORATORY_RESULTS.md`.

Datasets: `datasets/README.md`. Seeds, determinism evidence, tolerances and known hazards: the protocol file.
