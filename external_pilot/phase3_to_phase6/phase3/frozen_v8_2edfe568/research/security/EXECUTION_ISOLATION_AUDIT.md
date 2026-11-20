# V7 Execution Isolation Audit

Scope: `sbgv7/isolation.py` (implements P0 binding decision D10). Verified on: macOS (Darwin 25.6), CPython 3.13.15 (`.venv`), one machine, one run of `.venv/bin/python -m pytest tests/v7` (11 passed, 1 skipped, ~4 s). Linux and Docker were NOT tested (Docker daemon not running).

Design: each run is a fresh child (`python -I -B sbgv7/_child.py`), `start_new_session` (own process group), scrubbed env, workdir = temp dir. The child applies rlimits and aborts (exit 97, reported as CRASH) if one cannot be applied. Parent: wall timeout, group RSS watchdog, output cap, `killpg(SIGKILL)` after every run with ESRCH verification. On macOS the child is wrapped in `sandbox-exec -f sbgv7/sandbox_darwin.sb`. `capabilities()` probes each control once per process and reports ACTIVE or UNAVAILABLE; `run_*` with `sandbox=True` returns `SANDBOX_UNAVAILABLE` instead of running unconfined.

## Observed status per property (this machine)

| Property | Observed | Evidence (test) |
|---|---|---|
| Fresh process per run / `os._exit` does not kill host | ENFORCED | `test_os_exit_does_not_kill_host`: status CRASH, rc 7, host alive |
| Wall-clock timeout kills spinning code | ENFORCED | `test_spin_wall_timeout`: TIMEOUT < 3 s for a 1 s limit, cleanup verified |
| Process-group kill, no survivors | ENFORCED | `test_child_process_survival`: orphan `sleep 30` detected, killed, `kill(pid,0)` -> ESRCH; ps check clean |
| RLIMIT_CPU | ENFORCED | `test_cpu_rlimit`: SIGXCPU at 1 s CPU (status RESOURCE) |
| RLIMIT_NOFILE, RLIMIT_FSIZE | ENFORCED (capability probe only: opens/writes beyond cap fail) | `capabilities()` |
| RLIMIT_AS | NOT ENFORCED (macOS rejects setrlimit: "current limit exceeds maximum limit"). Reported UNAVAILABLE, test skipped | `capabilities()`, skipped test |
| RLIMIT_NPROC | NOT ENFORCED (not applied; per-user count on macOS, enforcement unverified). Reported UNAVAILABLE | `capabilities()` |
| Memory cap (compensating) | ENFORCED by parent RSS polling (100 ms), NOT a hard limit: 180 MB alloc with a 100 MB cap was killed, RESOURCE/rss_watchdog. A fast allocator can overshoot between polls | `test_memory_limit_200mb_or_less` |
| Output cap | ENFORCED: infinite stdout stopped at cap, truncated flag set, RESOURCE/output_cap | `test_output_cap` |
| Network denial (sandbox-exec) | ENFORCED: connect to 127.0.0.1:1 gives EPERM under sandbox; control without sandbox gives ECONNREFUSED | `test_network_denied` |
| Write confinement (sandbox-exec) | ENFORCED: write to a sibling temp dir denied, write inside workdir allowed; control without sandbox succeeds | `test_write_outside_denied` |
| SANDBOX_UNAVAILABLE explicit, no silent degrade | ENFORCED (simulated by patching the capability report) | `test_sandbox_unavailable_is_explicit` |
| Structured result (status, exit/signal, capped stdout/stderr, wall, CPU, peak RSS) | PRESENT. Peak RSS is max(watchdog samples, `ru_maxrss`); `ru_maxrss` may include pre-exec parent pages | `test_ok_and_callable` |

## Known gaps

- Reads are not confined (profile is `allow default`; only writes and network are denied). Secrets readable by the user are readable by the child.
- A child that calls `setsid()` leaves the process group and escapes the group kill (not tested).
- `sandbox-exec` is deprecated by Apple; it works on this OS version but may disappear.
- The tracer-evasion issue (R8d, `sys.settrace(None)`) is not addressed by this module; it only provides the process boundary.
- Fork bombs, real-network targets and writes outside temp were deliberately not probed.
- Linux (`RLIMIT_AS`, cgroups, seccomp, `--network none`) and Docker: not implemented, not tested.
