# Evidence Integrity & Security Remediation Report

## 1. Executive Summary

This report documents the architectural security remediations implemented in SBG V8 on Linux. Specifically, we detail the root-cause analysis, engineering fixes, and validation tests for attacks A01–A08, P01–P09, evaluation-awareness sensing (A07c), and unverified field manipulation (P04).

---

## 2. Detailed Root-Cause Analysis & Remediations

### A. Attack A07c — Evaluation-Awareness Sensing Remediation
- **Attack Vector**: The evaluated variant inspected `sys.argv[0]` or process invocation arguments looking for strings like `'harness'` or `'shadow'` to detect that it was being evaluated inside an automated test harness rather than standard execution. When detected, it executed identical behavior to suppress divergence; in real execution, it diverged.
- **Root Cause**: The child process harness in `sbgv7/harness.py` and `sbgv8/trust.py` initialized Python with the harness script path as `sys.argv[0]`, exposing evaluation context to the target script.
- **Architectural Fix**: In `sbgv7/harness.py` and `sbgv8/trust.py`, the target execution environment explicitly sanitizes `sys.argv = [a["src"]]` prior to importing or executing the target entrypoint. The program observes only its own file path in `sys.argv`, neutralizing harness-sensing heuristics.
- **Verification**: Retested against `A07c`. The variant now executes its real behavioral code path, producing divergent outputs that are correctly recorded and classified as `DIVERGENT_OBSERVABLE`.

### B. Attack A08 — Stdout Suppression Attack Remediation
- **Attack Vector**: Variant monkeypatched `Cap.write` inside `sys.modules['__main__']` to suppress in-memory StringIO capture.
- **Architectural Fix**: Implemented `procsep.Supervisor` and `_tee_child.py`. Stdout is intercepted at the `sys.stdout.write` level and streamed over an out-of-band pipe descriptor (`fd 2`) directly to the parent process supervisor before handing bytes to user space. If `Cap.write` is patched, the parent supervisor detects the mismatch between the child frame and the parent tee stream, flagging `capture.trusted = false` and forcing `INSUFFICIENT` verdict.

### C. Attack P04 — Unverified Metadata Tampering Remediation
- **Attack Vector**: Attacker altered `Run.meta.cpu_s`, `Run.meta.wall_s`, or `status` and recomputed the hash chain in `evidence.jsonl`.
- **Architectural Fix**: Implemented `v8_capture.json` and HMAC-SHA256 `v8_anchor.json`. The validator performs bidirectional cross-validation between `v8_capture.json` (recorded by the parent supervisor) and `evidence.jsonl`. Any alteration of timings, run statuses, nonces, or exit codes results in immediate validation failure (`reasons: ["run 0: timings differ from the log"]`).

### D. Attack Substitution — Cross-Pair Evidence Substitution
- **Attack Vector**: Genuine evidence from a different evaluation was placed in the target pair's directory.
- **Architectural Fix**: `trust.check` verifies the recorded `sha256` of base and variant sources against the caller's `expected_sources`. If the evidence was generated from a different file, it is rejected with `"provenance: recorded program source differs from the expected file"`.

---

## 3. Security Remediation Regression Matrix

| Attack ID | Threat Mechanism | Pre-Remediation Outcome | Post-Remediation Outcome | Enforcement Subsystem |
|---|---|---|---|---|
| **A01** | In-process result frame forgery | Open / Forged | **DETECTED / MITIGATED** | Parent Tee + Shadow Run |
| **A02** | Pipe FD hijacking | Open / Forged | **DETECTED / MITIGATED** | Channel Secret / Shadow Run |
| **A07** | Process memory tampering | Open / Forged | **DETECTED / MITIGATED** | Parent Supervisor + Shadow |
| **A07c** | Evaluation-awareness (`sys.argv` sensing) | Bypassed (NDO) | **DETECTED / REMEDIATED** | `sys.argv` Namespace Sanitization |
| **A08** | Stdout monkeypatching (`Cap.write`) | Bypassed (NDO) | **DETECTED / BLOCKED** | Parent Supervisor `_tee_child` |
| **P01** | Missing evidence file | Crash | **DETECTED** | Schema Validator (`validate_dir`) |
| **P04** | Metadata editing & re-chaining | Bypassed | **DETECTED** | HMAC Anchor + Capture Binding |
| **SUBST** | Cross-pair evidence substitution | Bypassed | **DETECTED** | Source Digest Binding |
