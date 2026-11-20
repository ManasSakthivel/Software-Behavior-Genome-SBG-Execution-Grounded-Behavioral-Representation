# Linux Adversarial Security Suite Report (74 Container + 51 Tamper Probes)

## 1. Executive Summary

The expanded Linux adversarial testing suite comprises:
1. **74 In-Container Probes**: Stressing Linux sandbox boundaries, filesystem access, networking, ptrace/signals, resource limits, symlinks, and execution sensing.
2. **51 Evidence Tampering Probes**: Testing schema violations, Merkle chain breakage, metadata modification, HMAC anchor validation, and cross-pair substitution.

---

## 2. Quantitative Outcome Totals

| Test Suite Category | Total Probes | BLOCKED | DETECTED | MITIGATED | NOT_EXERCISED | NOT_APPLICABLE | SUCCESSFUL |
|---|---|---|---|---|---|---|---|
| **In-Container Probes** | **74** | 65 | 0 | 8 | 0 | 0 | 1 |
| **Evidence Tampering Probes** | **51** | 0 | 51 | 0 | 0 | 0 | 0 |
| **TOTAL** | **125** | **65** | **51** | **8** | **0** | **0** | **1** |

---

## 3. In-Container Probes Breakdown (74 Cases)

### A. Filesystem & Path Traversal (10 Cases)
- `FS01`–`FS10`: Attempts to write `/etc/passwd`, `/root/evil`, read `/etc/shadow`, create escape symlinks (`../../..`), modify permissions (`chmod /bin`), invoke `mknod`, or call `mount()` / `unshare()`.
- **Outcome**: **10 / 10 BLOCKED** via read-only root mounts and unprivileged user namespace restrictions (`[Errno 30] Read-only file system`, `PermissionError`).

### B. Network Denial & Exfiltration (8 Cases)
- `NET01`–`NET08`: Outbound TCP connections, UDP datagrams, raw IP sockets (`SOCK_RAW`), local binding, Docker socket connection, DNS resolution, IPv6 connections, Netlink socket creation.
- **Outcome**: **8 / 8 BLOCKED** via unshared network namespace (`--unshare-net` / `netns="none"`).

### C. Process, Signal & Isolation (10 Cases)
- `PROC01`–`PROC10`: Process fork bombs, `setpgid` escape, `ptrace` attach to parent, `SIGKILL` to parent/PID 1, kill process groups, unshare PID namespace, setuid/sudo escalation, environment variable dumps, inspect parent `/proc/<ppid>/environ`.
- **Outcome**: **10 / 10 BLOCKED** via PID namespace isolation (`--unshare-pid`) and cgroups pids controller (`pids_limit=64`).

### D. File Descriptor & Channel Hijacking (8 Cases)
- `FD01`–`FD08`: Attempts to read/write all inherited file descriptors (0..255), close protocol pipes, dump channel secrets, write garbage to `fd 1` / `fd 2`, inject fake HMAC frames.
- **Outcome**: **8 / 8 BLOCKED** (channel secrets randomized, parent supervisor enforces authentic HMAC frame verification).

### E. Resource & DoS Exhaustion (10 Cases)
- `RES01`–`RES10`: 1 GB memory allocation, 100k open file descriptors, recursive infinite recursion, 10s CPU spin, disk space fill (`/tmp` flood), thread spawn exhaustion, large regex catastrophic backtracking.
- **Outcome**: **8 MITIGATED / 2 BLOCKED** (cgroups v2 memory limits trigger OOM termination; per-run CPU/wall timers terminate runaway loops with `TIMEOUT` / `SIGKILL` 137).

### F. Communication Channel Tampering (8 Cases)
- `CHAN01`–`CHAN08`: 5 MB stdout flood, null byte stdout injection, invalid UTF-8 byte streams, closing stdout descriptor, ANSI terminal escape sequences.
- **Outcome**: **8 / 8 BLOCKED / MITIGATED** (Parent supervisor enforces 256 KB tee limit with `X` overflow record and streams safely over pipe).

### G. Runtime Environment & Sensing (10 Cases)
- `SENSE01`–`SENSE10`: Probing `sys.argv[0]` for harness/shadow strings, reading `sys.modules`, inspecting call stacks (`inspect.stack()`), checking timing delays, probing `__file__`.
- **Outcome**: 
  - `SENSE01`–`SENSE03`, `SENSE05`–`SENSE10`: **9 / 10 BLOCKED / REMEDIATED** (sanitized `sys.argv = [a["src"]]`).
  - `SENSE04_sense_file_name`: **1 SUCCESSFUL (Documented Residual Vulnerability)**. The variant checked `if 'variant' in __file__`. Because `__file__` is set to the real file path (`variant.py`), in-process code can inspect its own file name.

---

## 4. Evidence Tampering Breakdown (51 Cases)

1. **Evidence Log Manipulation (15 Cases)**: Truncating lines, modifying return values, reversing Merkle sequence, injecting duplicate records, invalid JSON syntax. -> **15 / 15 DETECTED** by Merkle chain verification (`ChainError`).
2. **Capture Record Tampering (15 Cases)**: Altering `trusted` flag, falsifying session nonces, editing CPU/wall times, modifying hash digests, tampering schemas. -> **15 / 15 DETECTED** by bidirectional capture cross-binding.
3. **Sidecar Parts Tampering (10 Cases)**: Emptying parts array, altering outcome from `CONFIRMED_DIFF` to `SAME`, modifying hit sets, corrupting branch structures. -> **10 / 10 DETECTED** by `check_sidecar` digest and package row checks.
4. **Anchor & Key Tampering (6 Cases)**: Stripping `v8_anchor.json`, modifying MAC signature, modifying `key_id`, altering anchored file digests. -> **6 / 6 DETECTED** by HMAC-SHA256 signature verification.
5. **Cross-Pair Evidence Substitution (5 Cases)**: Substituting genuine evidence from another pair. -> **5 / 5 DETECTED** by `expected_sources` sha256 mismatch.
