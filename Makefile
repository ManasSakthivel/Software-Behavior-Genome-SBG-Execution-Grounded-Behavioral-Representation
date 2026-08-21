# Makefile for SBG — Software Behavior Genome
# Convenience targets. All commands are just thin wrappers around the underlying scripts.

.PHONY: test test-fast reproduce quickstart lint help

# Run the full test suite (516 tests, ~25 seconds)
test:
	python3 -m pytest sbg/ -q

# Run tests but stop at first failure (useful during development)
test-fast:
	python3 -m pytest sbg/ -q -x

# Verify reproducibility (6 checks, instant)
reproduce:
	python3 experiments/v5/reproduction_check.py

# Run the V3 reference result on the test set (~20 min)
run-v3:
	python3 baselines/v3/b07_dynamic_v3.py

# Run the V5 integrated pipeline on the test set (~30 min)
run-v5:
	python3 baselines/v5/b07_dynamic_v5.py

# Run the hard-negative oracle (instant)
hard-negatives:
	python3 benchmark/v5/hard_negatives/oracle.py

# Run the regression detection experiment (instant)
regression:
	python3 experiments/v5/regression_evaluator.py

# Run the quickstart example (compares a few program pairs, instant)
quickstart:
	python3 examples/quickstart.py

help:
	@echo "Available targets:"
	@echo "  make test          — run full test suite (516 tests)"
	@echo "  make test-fast     — run tests, stop on first failure"
	@echo "  make reproduce     — verify reproducibility (6/6 checks)"
	@echo "  make run-v3        — reproduce V3 result (AUROC=0.540, ~20 min)"
	@echo "  make run-v5        — reproduce V5 result (AUROC=0.551, ~30 min)"
	@echo "  make hard-negatives — run hard-negative oracle (instant)"
	@echo "  make regression    — run regression detection experiment (instant)"
	@echo "  make quickstart    — quick smoke test (instant)"
