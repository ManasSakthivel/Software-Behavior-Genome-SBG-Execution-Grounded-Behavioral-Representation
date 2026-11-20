# Podman Container Isolation & Boundary Verification Report (Phase 1 & 2)

## 1. Executive Summary

This report documents the container isolation architecture, configuration, and verification tests on the Linux validation environment (`9.30.57.225`). All workloads are executed under unprivileged rootless Podman / Bubblewrap sandboxes enforcing strict read-only root filesystems, unshared network namespaces, private PID namespaces, and cgroups v2 resource accounting.

---

## 2. Podman Isolation Configuration

```ini
[engine]
cgroup_manager = "systemd"
runtime = "crun"
events_logger = "file"
network_cmd_path = "/usr/bin/slirp4netns"

[containers]
netns = "none"
userns = "auto"
pids_limit = 64
ulimits = [
  "cpu=5:10",
  "as=1073741824:1073741824",
  "nproc=32:32",
  "nofile=1024:1024"
]
```

---

## 3. Boundary & Policy Enforcement Checks

### A. Non-Privileged Execution
- Container workloads run strictly as unprivileged user `alex` (UID `1001`).
- No `--privileged`, `--cap-add=ALL`, or host namespace flags (`--net=host`, `--pid=host`, `--ipc=host`) are permitted.

### B. Filesystem Mount Hardening
- Root filesystem is mounted read-only (`--read-only` in Podman, `--ro-bind / /` in bwrap).
- Temporary scratch space is isolated to an in-memory `tmpfs` under `/tmp/sbgv8_work/` with `noexec,nosuid,nodev` flags.
- **Forbidden Mounts**: The supervisor verifies that `/root`, `/home`, `~/.ssh`, `~/.gitconfig`, Docker/Podman control sockets (`/run/podman/podman.sock`), and host environment variables (specifically `$SBGV8_ANCHOR_KEY`) are NEVER mounted or passed to evaluated child containers.

### C. Network Denial
- Evaluated workloads run with `--network=none` or `--unshare-net`.
- Inbound and outbound connections, raw sockets (`SOCK_RAW`), Netlink control sockets (`AF_NETLINK`), and DNS resolutions are blocked by kernel namespace isolation.

---

## 4. Verification Test Matrix

| Test Probe ID | Category | Target Subsystem | Expected Enforcement | Observed Result | Status |
|---|---|---|---|---|---|
| **ISO-01** | Filesystem | Host root write | EROFS | `[Errno 30] Read-only file system` | **PASSED (BLOCKED)** |
| **ISO-02** | Filesystem | Host secret access | EACCES / ENOENT | File not found or unreadable | **PASSED (BLOCKED)** |
| **ISO-03** | Network | TCP outbound connect | ENETUNREACH / ECONNREFUSED | Connection refused | **PASSED (BLOCKED)** |
| **ISO-04** | Network | DNS resolution | EAI_NONAME | Resolution failed | **PASSED (BLOCKED)** |
| **ISO-05** | Privilege | Setuid / sudo attempt | EPERM | Operation not permitted | **PASSED (BLOCKED)** |
| **ISO-06** | Process | Parent signal / ptrace | EPERM / ESRCH | Process not found | **PASSED (BLOCKED)** |
| **ISO-07** | Resource | Memory flood (> 1 GB) | OOM Kill | Container killed / `SIGKILL` | **PASSED (MITIGATED)** |
| **ISO-08** | Resource | CPU infinite loop | CPU timeout | Process killed after 5s cpu / 10s wall | **PASSED (MITIGATED)** |
| **ISO-09** | Process | Fork bomb | EAGAIN | Process table limits enforced | **PASSED (BLOCKED)** |
| **ISO-10** | Teardown | Process residue | Zero orphans | Supervisor verified empty cgroup | **PASSED (VERIFIED)** |
