# V8 macOS process architecture: five roles (2026-11-18)

**Process separation is not an OS-level sandbox.** The evaluated process is contained by the existing V7-B macOS controls (sandbox-exec: network denied, writes confined to the run dir; rlimits CPU/NOFILE/FSIZE (AS best effort); fresh process group + SIGKILL + ESRCH check; RSS watchdog). Linux isolation is unverified. The harness still shares the evaluated program's address space.

```
controller (collect.run_capture)  --argv: harness json + run nonce-->  evaluated process (sandboxed child: _child.py -> _tee_child.py -> harness.py -> program)
      |  owns: session id, anchor key                                      |  real fd 1/2 pipes, result frame (HMAC, V7-B key)
      v                                                                    v
evidence collector (procsep.Supervisor, in the controller process, wraps isolation.run_script)  <- reads fd1, fd2, frame, status, rusage
      | v8_parts.json, v8_capture.json (v8.capture.1)  ->  controller writes v8_anchor.json (HMAC, key never leaves controller)
      v
evidence validator (evidence_schema.validate_dir; or procsep.validate_isolated = fresh interpreter, authenticated reply)
      v   {sidecar, capture, anchor, trusted: True|False|None, reasons}
decision engine (procsep.decide / adapter.load_record) -> effective verdict; untrusted => INSUFFICIENT, integrity_ok=False
```

| Role | Process | Receives | Emits | Failure semantics |
|---|---|---|---|---|
| Controller | parent (V8 CLI / `collect.compare`) | sources, inputs, config, optional anchor key | evidence dir, `verdict.json`, anchor; returns engine dict (verdict forced to INSUFFICIENT if untrusted) | engine exception propagates; patch always restored |
| Evaluated process | fresh sandboxed child per run | harness json arg, per-run nonce (argv), 32-byte frame key via pipe (V7-B), no anchor key (env is an allowlist) | HMAC frame on result fd, stdout/stderr, tee records on fd 2 | timeout/limit/signal/orphans recorded explicitly; no authentic frame => V7-B tamper/limit handling (no observation) |
| Evidence collector | controller process (patched spawn point) | child `Result` (own pipes) | `v8.capture.1` runs: fd1/fd2 digests, tee counters, harness claims, termination, flooding, per-run verdict | missing/foreign/duplicate/gapped/unclosed records, stderr cap, mismatch => run `incomplete`/`mismatch` => capture untrusted; non-harness spawn => "unsupervised" => untrusted |
| Evidence validator | in-process, or separate interpreter (`validate_isolated`, cwd = repo, minimal env) | evidence dir; request `{v, nonce, dir, chan_key, anchor_key, require_anchor}` on stdin | reply `{v, nonce, result, mac=HMAC(chan_key, nonce+result)}` | timeout (default 60 s), crash, garbage, wrong version/nonce (replay), bad MAC, malformed result => `trusted=False` |
| Decision engine | in-process pure function | engine verdict + validation | `{verdict, engine_verdict, untrusted, reasons}` | `trusted is False` => INSUFFICIENT; `None` (legacy dir, nothing to validate) => engine verdict passes through and `meta.capture="not_collected"` says so |

Replay prevention: per-run nonce (capture records are bound to a spawn; duplicates/foreign rejected), per-collection session id (capture and anchor must agree), per-validation nonce + channel key (validator replies), capture bound to the log by head, sha256, config digest and harness digest. Authenticated transfer exists only where the sender holds a key the child lacks: controller -> anchor (MAC) and validator -> controller (MAC). Child -> collector data (tee records) is **not authenticated** (the child knows the nonce): it is checked for consistency against the parent's own pipes and the authentic frame, and a forgery can at best make the run untrusted, except for a full in-process adversary (documented limit).

Resource limits and termination (macOS): inherited from `sbgv7.isolation` (wall timeout, CPU/NOFILE/FSIZE rlimits, 4 MiB output cap that kills the group, RSS watchdog, process-group kill with verification); V8 adds the explicit per-run record (`status`, `detail`, `signal`, `flooded`, `orphans_found`, `cleanup_verified`) and the validator timeout. `setsid` escapes and `sandbox-exec` deprecation are inherited limits.

Not implemented (no test, so not claimed): a separate-process evidence collector (it stays in the controller so it can see the child's pipes), a collector-signed record chain, kernel-level output tracing (dtrace/ES), key storage outside process memory/env, a key-id registry.
