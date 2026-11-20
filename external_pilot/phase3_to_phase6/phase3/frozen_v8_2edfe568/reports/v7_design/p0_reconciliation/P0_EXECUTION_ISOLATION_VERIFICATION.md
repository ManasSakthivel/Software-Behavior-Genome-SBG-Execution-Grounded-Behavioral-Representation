# P0 Execution Isolation Verification (experimental)

Date: 2026-11-17. Branch: feature/sbg-v7-p0-reconciliation. No V5/V6 files modified.

## Test environment (what was actually run)

- Docker: Docker.app is installed, but `docker info` fails: "failed to connect to the docker API at unix:///Users/manassakthivel/.docker/run/docker.sock ... no such file". The daemon was not running and I did not start it. No container probes were run. Docker-based design is UNTESTED here.
- Fallback used: host probes, each in its own child process (own session and process group), run from a temp dir, with an external hard wall-clock kill (20-60 s) and `ulimit -t 120`. `ulimit -v 4000000` was attempted, but it has no effect on macOS (see R4). Env was scrubbed to PATH plus probe vars and `python -I` was used. After the runs, `ps` showed no stray probe or `sleep 2` processes. The only `sleep` seen belongs to another agent's wait loop.
- Interpreters: system CPython 3.9.6 and the repo `.venv` CPython 3.13.15 (the canonical interpreter per `requirements-lock.txt`). Results were identical unless stated.
- Real API used in every probe: `SandboxRunner().run("probe", func, inputs, n_runs=1, timeout_s=T)`, which calls `Tracer.trace`, `_trace_one`, `_WorkerThread` (daemon thread plus `sys.settrace`).
- Harness: `reports/v7_design/p0_reconciliation/isolation_tests/probe.py` (one probe per process) and `run_all.py` (driver). Reproduce with `PY=$PWD/.venv/bin/python python3 reports/v7_design/p0_reconciliation/isolation_tests/run_all.py [pid spin leak rlimit child net fs malformed osexit]`.

## Verified findings

| # | Requirement | Existing implementation | Verification method | Observed result | Evidence | Required remediation |
|---|---|---|---|---|---|---|
| R1 | Traced program runs in a separate process | `_WorkerThread(daemon=True)` in the host process (tracer.py:255-273) | probe `pid` through the runner; compare pid/ppid inside func vs host | REFUTED. Same pid, non-main thread | `{"pid": 88719, "ppid": 88696, "thread": "Thread-1", "main": false, "host_pid": 88719}` | Run each program in a child process (subprocess or multiprocessing, spawn) |
| R2 | Wall-clock timeout actually stops the program | `worker.join(timeout)`; the worker is abandoned. The trace fn only does `settrace(None)` at the deadline and does not raise | probe `spin`: `while True: pass`, `timeout_s=1.0` | PARTIAL. The call returns on time (1.01 s with TimeoutError), but the thread keeps running. The CPU burn continues | `returned_after_s 1.02`; `threads_after ["MainThread","Thread-1"]`; CPU in 2 s idle after return = `2.01` s (about 100% of a core plus GIL contention) | Kill the process (SIGKILL on the process group), not the thread. A thread cannot be killed |
| R3 | No leakage across repeated timeouts | None. Each timeout leaves a spinning daemon thread | probe `leak`: 20 sequential 0.2 s spins | REFUTED. Threads and CPU grow monotonically, and the runs get slower | runs/threads/cpu_s: `(1,2,0.22) (5,6,1.23) (10,11,3.16) (20,21,7.81)`; wall 7.67 s for 20 x 0.2 s (about 1.9x) | Per-trace process isolation. `max_timeouts` only bounds the leak and does not remove it |
| R4 | CPU and memory limits | None set by the repo. The only guard is `max_events` and the timeout | probe `rlimit` inside func | REFUTED. `RLIMIT_AS`, `DATA`, `FSIZE` are inf. `NPROC` is 8000. `RLIMIT_CPU` was 120 only because my driver set it. `sys.getrecursionlimit()` is 1000. `ulimit -v` is a silent no-op on macOS | `"RLIMIT_AS": ["inf","inf"], "RLIMIT_CPU":[120,120] (driver-set)` | Set RLIMIT_CPU, RLIMIT_FSIZE and RLIMIT_NPROC in the child (macOS). Add RLIMIT_AS on Linux, or a cgroup/container `--memory`. macOS has no working memory rlimit for Python, so use a polling RSS watchdog in the parent. Not tested for memory (a >200 MB allocation was disallowed) |
| R5 | Child processes die with the run | None | probe `child`: func does `subprocess.Popen(["sleep","2"])` | REFUTED. The child outlives the runner call and is reparented | `alive_after_runner_returned: true`, `ps: 88934 88933 00:00 sleep 2` after the runner returned (exc `[null]`, i.e. no error reported) | New session or process group per run and `killpg` on exit. On Linux add `PR_SET_PDEATHSIG` or a PID namespace |
| R6 | Network denied | None. Failure is only environmental | probe `net`: connect 127.0.0.1:1 and `getaddrinfo("sbg-probe-nonexistent.invalid")` | NOT DENIED BY DESIGN. Closed-port connect got a normal ECONNREFUSED and the DNS lookup got a normal gaierror. Both calls are permitted syscalls that happen to fail. A live local service would be reachable. I tested no real hosts | `ConnectionRefusedError: [Errno 61]`; `gaierror: [Errno 8]` | Enforce denial: `docker --network none`, or a sandbox-exec profile `(deny network*)` (tested below) |
| R7 | Filesystem confinement | None. The process runs with full user privileges | probe `fs` | REFUTED. Read of `/etc/hosts` succeeded (213 bytes). Write to the cwd and to a temp path succeeded. The env was visible. (Writes were only to temp dirs, and each file was removed.) By inference, any user-writable path is writable; I did not write outside temp | `read_etc_hosts_bytes 213, write_cwd OK, write_tmp OK, env_keys_visible 12` | Read-only repo mount, tmpfs scratch, or a sandbox-exec file-write deny. Scrub the env |
| R8a | Ordinary exception is captured | try/except Exception in the worker | probe `malformed ValueError` | CONFIRMED | `exc "ValueError: boom", n_events 4` | none |
| R8b | Runaway recursion handled | Relies on the recursion limit (1000) plus worker stack | probe `malformed recursion` | INTERPRETER-DEPENDENT. On 3.13 it gives RecursionError and a trace of 1990 events. On the system 3.9.6 the whole host process aborted: `Fatal Python error: _Py_CheckRecursiveCall: Cannot recover from stack overflow` (rc -6) | 3.13: `{"exc":"RecursionError: maximum recursion depth exceeded","n_events":1990}`; 3.9: rc=-6, no result | Process isolation so a C-stack crash kills only the child. Pin and enforce 3.13 |
| R8c | BaseException (SystemExit, KeyboardInterrupt, GeneratorExit) handled | The worker catches only `Exception`. The thread dies and the result queue stays empty | probes `malformed SystemExit/KeyboardInterrupt/GeneratorExit` | PARTIAL. The host survives, but the failure is misreported as a timeout after 0.0 s. KeyboardInterrupt and GeneratorExit also print a traceback to stderr. No trace is recorded | `"exc":"TimeoutError: execution exceeded 1.0 s","wall_s":0.0` | Catch BaseException in the worker and report its real type. Process isolation handles this by exit code |
| R8d | Tracer cannot be evaded | None. The trace fn is a normal `sys.settrace` hook that the program can replace | probes `evade_settrace_None` and `evade_settrace_noop` (func calls `sys.settrace(None)` or installs a no-op hook, then loops 50 times) | REFUTED. Evasion works silently: no error, and `ret=1225` (correct). Events dropped to 2-3 against 50+ iterations. The event feature is silently undercounted, and nothing flags it | `{"exc":null,"n_events":2,"ret":1225}` | Out-of-process tracing (`sys.monitoring` on 3.12+, or an external tracer) or integrity checks (compare the hook identity after the run, flag the trace as tampered). Treat the corpus as non-adversarial unless this is fixed |
| R8e | `os._exit` in the program does not kill the host | None | probe `osexit` | REFUTED. The host process died with the program's exit code, and "HOST_ALIVE_AFTER" never printed | rc=7; output only `HOST_ALIVE_BEFORE` | Process isolation. Treat child exit code as the result |
| R9 | Stdout isolation | Process-global `sys.stdout` swap restored by the host after join | (not re-probed; covered by `tests/test_tracer_isolation.py`, which I read but did not run for this report) | Not independently verified. By code reading: a race with other host threads remains because `sys.stdout` is process-global | n/a | Subprocess pipes |

## Sandbox candidates actually tested

| Option | Tested? | Result |
|---|---|---|
| `docker run --network none --memory --pids-limit --read-only` | NO. The Docker daemon was not running and I did not start it | Feasible on Linux and on macOS arm64 with Docker Desktop (it runs a Linux arm64 VM), but unverified here |
| macOS `sandbox-exec` with `(allow default)(deny network*)(deny file-write* (require-not (subpath TMP)))`, running the `.venv` Python 3.13 | YES | Network denied: `net: PermissionError [Errno 1] Operation not permitted`. Write inside TMP: `write OK ok.txt`. Write outside TMP (`~/sbg_iso_denied_probe.txt`): `PermissionError`, and the file does not exist afterwards. `sandbox-exec` is deprecated by Apple but functional on Darwin 25.6 |
| rlimits via `resource.setrlimit` in a child (`preexec_fn`) | Partial. I observed that inherited `RLIMIT_CPU` is visible in the traced func (120 set by the driver). Enforcement (a SIGXCPU kill) was not exercised | CPU/FSIZE/NPROC are settable on macOS. `RLIMIT_AS` is not enforced on macOS (`ulimit -v` accepted silently, getrlimit still inf) |
| `RLIMIT_AS` / cgroups / `unshare -n` / seccomp on Linux | NO (host is macOS) | Standard Linux mechanisms; untested |

## Recommended V7 isolation design

1. Process per (program, input-set), spawned with `subprocess.Popen([python3.13, -I, worker.py], start_new_session=True)` (not fork, since threads are present). Communicate via a pipe or JSON file. No shared interpreter state, so R1, R3, R5 (via `killpg`), R8b-e are resolved by construction.
2. Parent enforces a hard wall timeout with `os.killpg(pid, SIGKILL)` plus a polling RSS watchdog (macOS) or `RLIMIT_AS`/cgroup (Linux).
3. In the child, before `exec` of the traced code: `setrlimit` for CPU (e.g. 2x the timeout), FSIZE (0 or small), NPROC, NOFILE, CORE=0. Scrub env. Scratch cwd in tempdir.
4. Network and filesystem containment (choose by platform):
   - Linux/CI: `docker run --network none --memory 256m --pids-limit 64 --read-only --tmpfs /tmp --cap-drop ALL -v repo:/repo:ro` with a pinned python image (UNTESTED here).
   - macOS dev: `sandbox-exec -f profile.sb` wrapping the child (TESTED: network and out-of-temp writes denied). Also apply this to the Docker VM path where applicable.
5. Failure semantics: record child exit code and signal as failure kinds (`killed_wall`, `killed_mem`, `crashed`, `exit_called`, `base_exception`); never fold them into "TimeoutError". Fix R8c's misclassification in the same change.
6. Tamper detection for R8d: since in-process tracing can be overridden, either use out-of-process tracing or flag traces whose event counts collapse with no exception. Without this, V7 claims of "isolated and faithful tracing" must be restricted to non-adversarial corpora.
7. Pin CPython 3.13 and refuse 3.9 (R8b abort).

## What could not be tested safely

- Docker-based isolation (the daemon was not running; I did not start it).
- A memory-exhaustion limit (a >200 MB allocation was disallowed). I only observed that no limit is set.
- Fork bombs, real network targets, writes outside temp dirs (disallowed).
- Linux-specific controls (cgroups, seccomp, `RLIMIT_AS` enforcement, `PDEATHSIG`).
- `RLIMIT_CPU` enforcement (SIGXCPU) and `tests/test_tracer_isolation.py` (read, not run). `experiments/final/extraction.py` and `sbgv6/observe.py` were read: both call the same `_runner`, so they inherit all of the above. `observe.py` monkey-patches `X._runner` with a recorder.
