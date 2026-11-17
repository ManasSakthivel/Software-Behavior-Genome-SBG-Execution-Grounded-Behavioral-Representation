# V7-B result protocol (D-02)

Status: local protocol-correctness fix. It is **not** a security isolation guarantee against a determined adversary that shares the
child's address space.

## Trust boundaries
- Trusted: the parent supervisor (`sbgv7/isolation.py`, `runner.py`), the child bootstrap (`_child.py`) and `harness.py` up to the point
  where the evaluated module is imported/called.
- Untrusted: the evaluated program (both versions) and anything it spawns. It runs in the same process as `harness.py`.

## Protocol
1. Parent creates a random 32-byte per-run key, a result pipe and a key pipe; writes the key to the key pipe and closes its write end.
2. `_child.py` (before any user code) drains and closes the key fd, then passes `(result_fd, key)` to `harness.py` via `init_globals`;
   `harness.py` pops it into module state. Neither appears in argv, env, stdout or a file.
3. At the end `harness.py` writes exactly one frame `SBGV7F1 <len> <hmac-sha256-hex(key, payload)>\n<payload>` to the result fd and exits.
4. Parent reads the pipe to EOF and `isolation.parse_frame` accepts only: one frame, nothing before/after, length within cap, valid MAC.
   Otherwise `Result.protocol_error` is one of `missing, malformed, truncated, oversized, duplicate, trailing, bad_mac`.
5. stdout/stderr are never parsed as protocol. `runner.py` treats any protocol error, or exit without a frame that was not a signal
   (e.g. `os._exit`), as tamper: the run has no observation, the input is `NO_RUN`, `Evidence.tampered` is set and the blocker is
   `unsafe_program` (rank 3), so neither NO_DIVERGENCE_OBSERVED nor DIVERGENT can be issued from such a run. Signal deaths remain
   parent-observed `crashed` observations. A user closing/redirecting the result fd makes the harness write fail -> `missing` (fail closed).
6. The previously dead `Evidence(tampered=False)` is now `ctx.tampered`; the harness monitoring-state flag feeds it too.

## What this does not stop (Phase 3, Linux adversarial validation)
- Code that reads harness state (`sys.modules['__main__']`, frame/`gc` inspection, closure cells) can recover the key and result fd and
  forge a valid frame, or patch `os.write`/`hmac`. Same address space means no real boundary.
- Fd enumeration finds the result pipe (discoverable, but unusable without the key).
- Needed: run the harness out of process from the untrusted code (supervisor-side tracing or a separate trusted process driving a
  sandboxed child), hostile fixtures on Linux containers (seccomp, no ptrace, PID/user namespaces), `setsid`/subprocess escape tests,
  and verification that user code cannot reach the key.
