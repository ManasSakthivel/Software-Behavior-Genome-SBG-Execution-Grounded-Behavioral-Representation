# Makefile for SBG — Software Behavior Genome
#
# Targets are grouped by what they actually do, because the previous `reproduce`
# target only compared hashes of committed artifacts and was described as
# reproducing the result. Verification and reproduction are now separate.

PYTHON ?= python3

.PHONY: help test quickstart verify-artifacts audit manifest tables readme \
        figures check check-reproduction reproduce-fast reproduce-v5 reproduce-output-free reproduce-all \
        benchmark-v6 clean

help:
	@echo "Software Behavior Genome — make targets"
	@echo ""
	@echo "  make test             run the full test suite"
	@echo "  make quickstart       smoke test: compare a few program pairs (instant)"
	@echo ""
	@echo "  VERIFY — checks committed artifacts without re-running experiments"
	@echo "  make audit            static benchmark + output-free audits (~20 s)"
	@echo "  make manifest         rebuild benchmark/benchmark_manifest.json (~5 s)"
	@echo "  make tables           regenerate docs/generated/ from the artifacts"
	@echo "  make figures          regenerate docs/figures/ from the artifacts"
	@echo "  make readme           splice the generated results into README.md"
	@echo "  make verify-artifacts audit + manifest + tables + consistency gate"
	@echo "  make check            verify-artifacts + the integrity tests"
	@echo ""
	@echo "  REPRODUCE — re-executes experiments and overwrites the artifacts"
	@echo "  make reproduce-fast   hard negatives + regression corpus (~1 min)"
	@echo "  make check-reproduction  re-run those and compare against the artifacts"
	@echo "  make reproduce-v5     main benchmark, published protocol (~26 min)"
	@echo "  make reproduce-all    every experiment (~60 min)"
	@echo "  make benchmark-v6     regenerate the corrected benchmark (~3 min)"

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

test:
	$(PYTHON) -m pytest sbg/ tests/ -q

quickstart:
	$(PYTHON) examples/quickstart.py

# ---------------------------------------------------------------------------
# Verification — no experiment is executed, nothing is measured
# ---------------------------------------------------------------------------

audit:
	$(PYTHON) benchmark/scripts/observability_audit.py
	$(PYTHON) experiments/final/output_oracle_leak_audit.py

manifest:
	$(PYTHON) benchmark/scripts/build_manifest.py
	$(PYTHON) experiments/final/artifact_provenance.py

tables:
	$(PYTHON) experiments/final/make_tables.py

figures:
	$(PYTHON) experiments/final/make_figures.py

readme: tables
	$(PYTHON) experiments/final/assemble_readme.py

verify-artifacts: audit manifest tables figures readme
	$(PYTHON) experiments/final/consistency_check.py

check: verify-artifacts
	$(PYTHON) -m pytest tests/test_integrity.py -q

# ---------------------------------------------------------------------------
# Reproduction — experiments are re-executed and artifacts overwritten
# ---------------------------------------------------------------------------

reproduce-fast:
	$(PYTHON) experiments/final/hard_negative_evaluation.py
	$(PYTHON) experiments/final/regression_evaluation.py

check-reproduction:
	$(PYTHON) experiments/final/check_reproduction.py

reproduce-v5:
	$(PYTHON) experiments/final/run_main_evaluation.py --split test --protocol published
	$(PYTHON) experiments/final/analyse_results.py --split test --protocol published

reproduce-output-free:
	$(PYTHON) experiments/final/run_main_evaluation.py --split test --protocol output_free_v6
	$(PYTHON) experiments/final/analyse_results.py --split test --protocol output_free_v6

benchmark-v6:
	$(PYTHON) benchmark/scripts/generate_benchmark_v6.py
	$(PYTHON) benchmark/scripts/observability_audit.py benchmark/datasets/v6 \
		artifacts/final/BENCHMARK_VALIDITY_AUDIT_V6.json

reproduce-all: reproduce-fast reproduce-v5 reproduce-output-free verify-artifacts

clean:
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '*.pyc' -delete
