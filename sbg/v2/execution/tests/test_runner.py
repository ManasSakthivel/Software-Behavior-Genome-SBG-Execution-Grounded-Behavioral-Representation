"""Unit tests for SandboxRunner."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent.parent.parent))

import pytest
from sbg.v2.execution.runner import SandboxRunner, SandboxResult


def _simple_sort(inp):
    if isinstance(inp, list):
        return sorted(inp)
    return inp


def _always_raises(inp):
    raise ValueError("test error")


def test_sandbox_runner_basic():
    runner = SandboxRunner()
    result = runner.run("test_sort", _simple_sort, [[3, 1, 2], [5, 4]], n_runs=2)
    assert isinstance(result, SandboxResult)
    assert result.n_runs == 2
    assert len(result.traces) == 2
    assert result.program_id == "test_sort"


def test_sandbox_runner_noise_floor():
    runner = SandboxRunner()
    result = runner.run("test_sort", _simple_sort, [[3, 1, 2]], n_runs=5)
    # Deterministic function should have near-zero noise
    assert result.noise_floor_stats["coverage_size_std"] < 1.0


def test_sandbox_runner_exception():
    runner = SandboxRunner()
    result = runner.run("test_exc", _always_raises, [1, 2], n_runs=1)
    assert result.timeout_fraction == 0.0
    # Exceptions should be recorded, not crash the runner
    for run_traces in result.traces:
        for trace in run_traces:
            assert trace.exception is not None


def test_sandbox_runner_empty_inputs():
    runner = SandboxRunner()
    result = runner.run("test_empty", _simple_sort, [], n_runs=1)
    assert result.n_runs == 1
    assert all(len(r) == 0 for r in result.traces)
