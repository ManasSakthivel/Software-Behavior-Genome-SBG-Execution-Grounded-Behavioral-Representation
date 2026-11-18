# V8 security and trust report (DEVELOPMENT; no security claim)

Scope: `sbgv8/trust.py`, `python -m sbgv8 forge-test`, `tests/v8/test_trust.py`. Platform of the runs below: macOS (Darwin), Python 3.13, sandbox-exec profile. Not validated on Linux. Nothing here is a security guarantee; attacks that still succeed are listed as OPEN.

## 1. Five separate questions (a hash chain answers only the first)
| Question | Check | Established when it passes | NOT established |
|---|---|---|---|
| Evidence integrity | hash chain, content ids, `sbgv7 verify` recomputation (classify/finalize from the stored runs), verdict.json vs log, sidecar binding (`check_sidecar`) | The records are mutually consistent and the verdict follows from the recorded runs | That the records are true |
| Provenance | verdict.json present; sidecar present; harness digest equals the current harness.py; OPTIONAL external anchors: `pinned_head` (log head stored out of band) and `expected_sources` (files the reviewer expects) | The record set is complete; with anchors: this log is the one pinned, and it describes the expected programs | Without anchors: nothing about origin. A writer who can recompute the chain can make a consistent log |
| Authenticity | optional shadow re-observation (`check(..., shadow=True)`): a second minimal runner (own canonicaliser, own exec, own result fd, not `harness.py`; transported by `sbgv7.isolation` so it is sandboxed) re-executes both sides on every input and compares the return-value fingerprint with the recorded primary observation | An independent execution reproduced the recorded return values (cross-check) | Side-effect channels (stdout, files, globals, argument mutation) are not re-compared. A program that detects the shadow runner (or targets both mechanisms) defeats it. The shadow runner also shares its own address space with the program |
| Execution isolation | recorded environment/controls in the EvidencePackage | macOS `sandbox-exec` profile: network denied, writes confined to the run directory; rlimits; process-group kill; fresh process per run | Not validated on Linux; not validated against a determined adversary; the result harness runs in the SAME process as the evaluated program (red-team M-4); `policy_below_minimum` is true on macOS by construction |
| Correctness of inference | `verify` recomputation; report restates the meaning | The verdict is a deterministic function of the recorded facts | NO_DIVERGENCE_OBSERVED means "none observed on the executed inputs/channels", never equivalence; sufficiency is judged by the V8 profile/calibration, not by this report |

`trust.check(dir) -> TrustReport(integrity, provenance, authenticity, isolation, issues, inference)`; `issues` is empty only if nothing above fired.

## 2. Forgery suite (attacks launched from the evaluated program, plus post-hoc edits)
Pair: base `x+1`, variant `x+2`, input 1 (honest verdict DIVERGENT_OBSERVABLE). The attack tries to make the pair look clean or the evidence unusable. Config: r_det 2, r_replay 2, k_alt 1 (suite speed; not the E3 config). Reproduce: `python -m sbgv8 forge-test --out forge.json`. Outcomes are what the code produced at the time of writing (`tests/v8/test_trust.py` pins the key ones).

| Id | Attack | Engine verdict | Result |
|---|---|---|---|
| H00 | none (control) | DIVERGENT | true verdict, all checks pass |
| A01 | patch harness canonicaliser via `sys.modules['__main__'].canon` (red-team M-4) | NO_DIVERGENCE_OBSERVED | verify passes (as in M-4). DETECTED only by the shadow re-observation |
| A02 | call the harness's own `finish()` with an attacker-chosen observation (authentic frame, forged content) | NO_DIVERGENCE_OBSERVED | verify passes. DETECTED only by the shadow |
| A03 | `os._exit(0)` before the result | INSUFFICIENT | BLOCKED by the engine (no authentic frame -> unsafe_program) |
| A04 | write garbage to every fd 3..63 (result fd) | INSUFFICIENT | BLOCKED by the engine (protocol error) |
| A05 | close fds 3..63 (result fd) | INSUFFICIENT | BLOCKED by the engine |
| A06 | forged `SBGV7F1` line on stdout | DIVERGENT | no effect (stdout is never protocol) |
| A07 | program senses the harness (`hasattr(__main__, 'canon')`) and returns the clean value only there | NO_DIVERGENCE_OBSERVED | DETECTED only by the shadow (it sees the real behaviour) |
| A08 | hide a stdout divergence by patching `Cap.write`, return value unchanged | NO_DIVERGENCE_OBSERVED | **SUCCEEDS (OPEN)**: verify passes and the shadow compares return values only |
| P01 | edit an Observation, no re-chain | (unchanged) | DETECTED: chain broken, verify fails |
| P02 | edit the Verdict (and its id, verdict.json, chain) and re-chain | NO_DIVERGENCE_OBSERVED | DETECTED: verify recomputes the verdict from the runs; sidecar binding also breaks |
| P03 | delete verdict.json | (unchanged) | NOT detected by `verify` (as in the red team). DETECTED by `trust.check` provenance (reported as an issue) |
| P04 | edit an unverified field (Run cpu/wall) and re-chain, also re-bind the sidecar | (unchanged) | **SUCCEEDS (OPEN)**: no check fires. Impact limited to the edited fields, but it shows evidence can be altered by a writer of the whole directory |
| P05 | tamper with the sidecar hit sets | (unchanged) | DETECTED: sidecar is checked against the Run records and bound by sha256/head |
| P06 | present the evidence of a benign program as the evidence of the real pair | NO_DIVERGENCE_OBSERVED | DETECTED only if `expected_sources` is supplied (source digest mismatch); otherwise verify and all other checks pass |
| P07 | edit an unverified field and re-chain without re-binding the sidecar | (unchanged) | DETECTED: sidecar sha256 binding |

Counts: 15 attacks + 1 control; detected 9 (A01, A02, A07, P01, P02, P03, P05, P06, P07), blocked by the engine 3, no effect 1, still succeed 2 (A08, P04). A01, A02, A07, P03 and P06 are detected by an ADDED check that is optional (shadow, provenance, expected_sources); `verify` alone misses them.

## 3. Open issues (not fixed here)
1. In-process forgery of non-return channels (A08) and any attack that targets the shadow runner too. Real fix needs canonicalisation outside the program process (Phase 3, red-team M-4 recommendation).
2. A consistent re-chained log is undetectable without an out-of-band pinned head (P04, and the general case); `pinned_head` is only an API, nobody pins one yet.
3. Evidence substitution (P06) is only caught when the reviewer supplies the expected source files/hashes.
4. The shadow runner executes the evaluated code again (sandboxed via the same macOS profile); it is a cross-check of return values only, and for `obj`/lossy/raised outcomes it is `not_comparable`.
5. `sidecar` is derivable from the Run records (the engine already logs per-run hits/branches in `Run.meta`); it is kept as the contract's explicit capture and cross-checked against the runs, so it adds consistency, not new information.
6. Isolation is validated only as far as the V7-B probes on macOS; none of it is validated on Linux.
