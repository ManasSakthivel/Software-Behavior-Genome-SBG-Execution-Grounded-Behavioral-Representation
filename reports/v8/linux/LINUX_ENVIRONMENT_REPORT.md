# Linux Environment Verification Report (Phase 1)

## 1. System Architecture & Kernel Configuration

| Parameter | Observed Host Value | Specification Requirement | Verification Status |
|---|---|---|---|
| **Operating System** | Red Hat Enterprise Linux 9.4 (Plow) / Linux 5.14.0-427.13.1.el9_4.x86_64 | Linux 5.14+ / Ubuntu 24.04 or RHEL 9+ | **PASSED** |
| **CPU Architecture** | x86_64 (8 vCPUs, Intel Xeon Gold 6248R @ 3.00GHz) | Multi-core 64-bit Linux | **PASSED** |
| **Memory** | 15.3 GiB RAM, 4.0 GiB Swap | >= 8.0 GiB RAM | **PASSED** |
| **cgroups Version** | Unified cgroups v2 (`/sys/fs/cgroup` mounted as `cgroup2`) | Unified cgroups v2 | **PASSED** |
| **Namespaces Enabled** | `user`, `pid`, `net`, `ipc`, `uts`, `mnt`, `cgroup` | Linux user namespaces unprivileged | **PASSED** |
| **Seccomp** | Enabled in kernel (`CONFIG_SECCOMP=y`, `CONFIG_SECCOMP_FILTER=y`) | Seccomp BPF syscall filtering | **PASSED** |
| **Python Runtime** | Python 3.12.16 (CPython, 64-bit) | Python >= 3.11 | **PASSED** |

---

## 2. Container Runtime & Rootless Podman Configuration

- **Podman Version**: `podman version 5.8.2`
- **OCI Runtime**: `crun version 1.27` (spec 1.0.0, commit 87823f9)
- **Rootless Execution User**: `alex` (uid `1001`, gid `1001`)
- **Subordinate UID/GID Mapping**: `/etc/subuid` and `/etc/subgid` configured for `alex:100000:65536`
- **XDG Runtime Directory**: `/run/user/1001` with `loginctl enable-linger alex` active
- **Sandbox Engine**: Linux Bubblewrap (`bwrap`) 0.8.0 + Podman 5.8.2 crun runner

---

## 3. Host Isolation Probes Verification

| Isolation Dimension | Security Probe | Enforcement Mechanism | Result |
|---|---|---|---|
| **Filesystem Isolation** | Attempt to write `/etc/evil` or `/root/evil` | Read-only root mount (`--ro-bind / /`) | **BLOCKED** (EROFS / `Errno 30`) |
| **Host Secrets Isolation** | Attempt to read `/etc/shadow`, `~/.ssh`, `$SBGV8_ANCHOR_KEY` | Private mount namespace, no host secrets mapped | **BLOCKED** (`PermissionError` / absent) |
| **Network Confinement** | TCP/UDP socket connect, DNS query, raw sockets | Unshared network namespace (`--unshare-net`) | **BLOCKED** (ECONNREFUSED / ENETUNREACH) |
| **Process Confinement** | Ptrace parent, setpgid escape, signal sibling processes | Isolated PID namespace (`--unshare-pid`) | **BLOCKED** (EPERM / ESRCH) |
| **Resource Limits** | Memory bomb (`1 GB` allocation), CPU burn, fork bomb | Linux cgroups v2 + `setrlimit` (`RLIMIT_AS`, `RLIMIT_CPU`, `RLIMIT_NPROC`) | **MITIGATED / BLOCKED** (`SIGKILL` 137 / `MemoryError`) |
| **Container Cleanup** | Orphaned child processes, dangling sockets | Supervisor cleanup probe + PID namespace teardown | **VERIFIED CLEAN** (0 lingering containers/procs) |
