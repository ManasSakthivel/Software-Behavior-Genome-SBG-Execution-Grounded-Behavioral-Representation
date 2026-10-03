# Makefile for SBG — Software Behavior Genome
#
# Targets are grouped by what they actually do, because the previous `reproduce`
# target only compared hashes of committed artifacts and was described as
# reproducing the result. Verification and reproduction are now separate.

PYTHON ?= python3

.PHONY: help test quickstart verify-artifacts audit manifest tables readme \
        figures check check-reproduction reproduce-fast reproduce-v5 reproduce-output-free reproduce-all \
        benchmark-v6 clean setup verify-v7-invariance v7-train v7-fit v7-test \
        reproduce-v7 quixbugs bugsinpy java reproduce-real reproduce-external gate

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
	@echo ""
	@echo "  PHASE 2 — see docs/current/PHASE2_HANDOFF.md before running any of these"
	@echo "  make setup              create .venv on CPython 3.13 from requirements-lock.txt"
	@echo "  make verify-v7-invariance  v7 leaves every v6 selection unchanged"
	@echo "  make reproduce-v7       v7-train, v7-fit, v7-test (dev and tau* are frozen)"
	@echo "  make reproduce-real     QuixBugs + BugsInPy under output_free_v7"
	@echo "  make reproduce-external reproduce-real + Java"
	@echo "  make gate               evidence-driven Stanford gate -> STANFORD_GATE.json"

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

# ---------------------------------------------------------------------------
# Phase 2 (docs/current/PHASE2_PREREGISTRATION.md, docs/current/PHASE2_HANDOFF.md)
# The dev run and tau* are frozen and have no target on purpose: re-running dev
# would re-derive a threshold that later stages already depend on.
# ---------------------------------------------------------------------------

V7 = output_free_v7
V6DATA = benchmark/datasets/v6
AUDIT_V7 = artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7.json

setup:
	python3.13 -m venv .venv
	.venv/bin/python -m pip install -r requirements-lock.txt

verify-v7-invariance:
	$(PYTHON) experiments/final/verify_v6_unchanged.py

v7-train:
	$(PYTHON) experiments/final/run_main_evaluation.py --split train --protocol $(V7) --dataset-dir $(V6DATA) --tag v6train
	$(PYTHON) experiments/final/static_baselines.py --pairs artifacts/final/pairs_v6train_$(V7).jsonl --dataset $(V6DATA)

v7-fit:
	$(PYTHON) experiments/final/fit_weights.py fit

v7-test:
	$(PYTHON) experiments/final/run_main_evaluation.py --split test --protocol $(V7) --dataset-dir $(V6DATA) --tag v6test
	$(PYTHON) experiments/final/static_baselines.py --pairs artifacts/final/pairs_v6test_$(V7).jsonl --dataset $(V6DATA)
	$(PYTHON) experiments/final/fit_weights.py score
	$(PYTHON) experiments/final/analyse_results.py --split test --protocol $(V7) --tag v6test --audit $(AUDIT_V7) --family prereg_v7
	$(PYTHON) experiments/final/fit_weights.py test

reproduce-v7: v7-train v7-fit v7-test

quixbugs:
	$(PYTHON) experiments/final/external_quixbugs.py score --protocol $(V7)
	$(PYTHON) experiments/final/external_quixbugs.py analyse --protocol $(V7)

bugsinpy:
	$(PYTHON) experiments/final/external_bugsinpy.py score --protocol $(V7)

java:
	$(PYTHON) experiments/final/external_java.py run
	$(PYTHON) experiments/final/external_java.py finalize

reproduce-real: quixbugs bugsinpy

reproduce-external: reproduce-real java

gate:
	$(PYTHON) experiments/final/stanford_gate.py

reproduce-all: reproduce-fast reproduce-v5 reproduce-output-free verify-artifacts

clean:
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '*.pyc' -delete
