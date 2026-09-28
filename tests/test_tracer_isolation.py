"""Regression tests for two tracer defects found during the V6 correction.

Both are about what happens *after* a traced program fails to terminate.
"""
from __future__ import annotations

import sys
import time

from sbg.extraction.dynamic.tracer import Tracer
from sbg.v2.execution.runner import SandboxRunner


def _terminating(value):
    return sum(value or [])


def _hangs_on_nine(value):
    if value and value[0] == 9:
        while True:                       # pragma: no cover - abandoned on purpose
            pass
    return sum(value or [])


class TestStdoutIsRestoredAfterTimeout:
    """The worker replaces the process-global sys.stdout to capture the traced
    program's output. A worker abandoned on timeout never reaches its restore,
    so every later write by the host vanished into a dead thread's StringIO --
    which silently swallowed the evaluation harness's own progress logging and
    made a running job look hung."""

    def test_stdout_survives_a_timeout(self):
        original = sys.stdout
        Tracer().trace(_hangs_on_nine, [[9]], max_events=500, timeout_s=0.3)
        assert sys.stdout is original

    def test_stdout_survives_a_normal_trace(self):
        original = sys.stdout
        Tracer().trace(_terminating, [[1, 2, 3]], max_events=500, timeout_s=1.0)
        assert sys.stdout is original

    def test_print_after_timeout_reaches_the_host(self, capsys):
        Tracer().trace(_hangs_on_nine, [[9]], max_events=500, timeout_s=0.3)
        print("host output after a timeout")
        assert "host output after a timeout" in capsys.readouterr().out


class TestNonterminationEarlyAbort:
    """Each timed-out trace leaves behind a worker thread that cannot be killed.
    Without an early abort, a mutant that loops forever leaves one per input per
    run, and they compete for the GIL with every program traced afterwards."""

    def test_aborts_after_the_configured_number_of_timeouts(self):
        started = time.monotonic()
        result = SandboxRunner().run(
            "hangs", _hangs_on_nine, [[9], [9], [9], [9], [9]],
            n_runs=5, timeout_s=0.3, max_timeouts=2)
        elapsed = time.monotonic() - started
        assert result.error == "NONTERMINATING"
        assert result.n_runs == 1
        # Two timeouts at 0.3 s, not 25. Generous bound for a loaded machine.
        assert elapsed < 5.0

    def test_terminating_program_is_unaffected(self):
        result = SandboxRunner().run(
            "fine", _terminating, [[1], [2], [3]],
            n_runs=3, timeout_s=1.0, max_timeouts=2)
        assert result.error is None
        assert result.n_runs == 3
        assert all(len(run) == 3 for run in result.traces)

    def test_default_behaviour_is_unchanged(self):
        # max_timeouts=None must leave the published protocol exactly as it was.
        result = SandboxRunner().run(
            "fine", _terminating, [[1], [2]], n_runs=2)
        assert result.error is None
        assert result.n_runs == 2


class TestConfigurableTimeout:
    def test_timeout_is_respected(self):
        started = time.monotonic()
        traces = Tracer().trace(_hangs_on_nine, [[9]], max_events=500, timeout_s=0.3)
        elapsed = time.monotonic() - started
        assert elapsed < 3.0
        assert traces[0].exception.startswith("TimeoutError")
        assert "0.3" in traces[0].exception

    def test_omitting_the_timeout_keeps_the_module_default(self):
        traces = Tracer().trace(_terminating, [[1]], max_events=500)
        assert traces[0].exception is None
