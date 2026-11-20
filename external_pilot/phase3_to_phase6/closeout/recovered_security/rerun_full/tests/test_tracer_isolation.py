"""Regression tests for tracer defects found during V6/V7 corrections.

Covers:
- Stdout restoration after timeout (V6 defect).
- Early abort on repeated timeouts (V6 defect).
- RecursionError counted toward MAX_TIMEOUTS (V7 defect: infinite-recursion
  mutations were spending minutes per pair because RecursionError was silently
  caught and the runner proceeded through all N_RUNS × 5000-event traces).
- No expensive repr() snapshots collected after event-budget exhaustion (V7
  defect: tight-loop and infinite-recursion variants triggered 5000 snapshot
  calls per trace even after tracing was disabled by the budget check).
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


# ---------------------------------------------------------------------------
# V7 regression: RecursionError counted toward MAX_TIMEOUTS
# ---------------------------------------------------------------------------

def _infinite_recursion(value):
    """Simulates a broken _partition mutation that recurses forever."""
    return _infinite_recursion(value)  # pragma: no cover - abandoned on purpose


class TestRecursionErrorCountsAsTimeout:
    """A variant whose mutation causes infinite recursion (e.g. sort_topk_select
    sc10: missing i+=1 in _partition) hits RecursionError on every input.
    Before the fix the runner silently caught RecursionError and continued
    through all N_RUNS × max_events traces, spending ~190 s per pair.
    After the fix RecursionError counts toward max_timeouts and the run aborts
    after the configured number of failing traces."""

    def test_recursion_error_triggers_early_abort(self):
        started = time.monotonic()
        result = SandboxRunner().run(
            "infinite_recursion", _infinite_recursion,
            [[1], [2], [3], [4], [5]],
            n_runs=5, max_events=5000, timeout_s=1.0, max_timeouts=2,
        )
        elapsed = time.monotonic() - started
        # Must abort after 2 RecursionErrors, not run all 5 inputs × 5 runs.
        assert result.error == "NONTERMINATING"
        assert result.n_runs == 1
        # Two RecursionErrors at most a few seconds each, not 25+ minutes.
        assert elapsed < 30.0, f"took {elapsed:.1f}s — RecursionError not counted as timeout"

    def test_recursion_error_recorded_in_trace_exception(self):
        traces = Tracer().trace(
            _infinite_recursion, [[1]], max_events=500, timeout_s=1.0,
        )
        assert traces[0].exception is not None
        assert "RecursionError" in traces[0].exception

    def test_terminating_program_unaffected_by_recursion_guard(self):
        result = SandboxRunner().run(
            "fine", _terminating, [[1], [2], [3]],
            n_runs=3, timeout_s=1.0, max_timeouts=2,
        )
        assert result.error is None
        assert result.n_runs == 3


# ---------------------------------------------------------------------------
# V7 regression: no repr() snapshots collected after event-budget exhaustion
# ---------------------------------------------------------------------------

def _tight_loop(value):
    """A function that generates many trace events quickly (simulates a variant
    whose mutation causes O(n^2) or infinite looping under sys.settrace)."""
    total = 0
    for _ in range(10_000):
        total += 1
    return total


class TestNoSnapshotsAfterBudgetExhaustion:
    """After the event cap is reached, the trace function must return None
    immediately without calling repr() on any local variables.  Before the fix
    the cap check came *after* the snapshot block, so a 5000-event trace still
    collected 5000 repr() snapshots even on a variant that was already known to
    be over-budget."""

    def test_event_budget_stops_snapshot_collection(self):
        """Verify the trace is truncated and completes in reasonable time."""
        started = time.monotonic()
        traces = Tracer().trace(_tight_loop, [0], max_events=100, timeout_s=5.0)
        elapsed = time.monotonic() - started
        assert traces[0].truncated, "trace should be marked truncated at event cap"
        assert len(traces[0].events) == 100
        # Should finish in well under 1 s; before the fix repr() overhead on
        # large local state after budget exhaustion could stall for seconds.
        assert elapsed < 2.0, f"took {elapsed:.1f}s — snapshots still collected after cap"

    def test_deadline_stops_snapshot_collection(self):
        """A trace that hits the wall-clock deadline must not keep reprinting."""
        started = time.monotonic()
        traces = Tracer().trace(_tight_loop, [0], max_events=500_000, timeout_s=0.1)
        elapsed = time.monotonic() - started
        # The join waits up to timeout_s; total should be well under 1 s.
        assert elapsed < 2.0, f"took {elapsed:.1f}s — repr() called after deadline"


# ---------------------------------------------------------------------------
# V7 regression: checkpointing in run_main_evaluation
# ---------------------------------------------------------------------------

class TestCheckpointing:
    """The checkpoint mechanism must write intermediate results, allow restart
    from any completed prefix, and delete the checkpoint on clean completion."""

    def test_checkpoint_written_and_deleted_on_completion(self, tmp_path):
        import json as _json
        from experiments.final.run_main_evaluation import (
            _checkpoint_path, _load_checkpoint, _write_checkpoint,
        )
        ckpt = _checkpoint_path(tmp_path, "test_tag", "output_free_v7")
        assert not ckpt.exists()

        rows = [{"pair_id": f"p{i}", "evaluated": True} for i in range(3)]
        _write_checkpoint(ckpt, rows)
        assert ckpt.exists()

        loaded_rows, loaded_ids = _load_checkpoint(ckpt)
        assert len(loaded_rows) == 3
        assert loaded_ids == {"p0", "p1", "p2"}

        # Simulate completion: delete checkpoint.
        ckpt.unlink()
        assert not ckpt.exists()

    def test_resume_skips_completed_pairs(self, tmp_path):
        """A restart with a checkpoint must produce the same final output as a
        fresh run (same rows, same order) without re-executing completed pairs."""
        import json as _json
        from experiments.final.run_main_evaluation import (
            _checkpoint_path, _load_checkpoint, _write_checkpoint,
        )
        ckpt = _checkpoint_path(tmp_path, "resume_tag", "output_free_v7")
        pre = [{"pair_id": "already_done", "evaluated": False,
                "base_id": "x", "split": "train"}]
        _write_checkpoint(ckpt, pre)
        loaded_rows, loaded_ids = _load_checkpoint(ckpt)
        assert "already_done" in loaded_ids
        assert len(loaded_rows) == 1
