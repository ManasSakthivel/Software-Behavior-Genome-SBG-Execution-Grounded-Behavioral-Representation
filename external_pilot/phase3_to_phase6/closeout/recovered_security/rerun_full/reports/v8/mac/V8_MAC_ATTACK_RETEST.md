# V8 macOS attack retest (2026-11-18)

Reproduce: `python -m sbgv8 forge-test --out out.json` (macOS, Python 3.13, config r_det 2 / r_replay 2 / k_alt 1). Before: `results/v8_mac_security/attack_suite_before.json` (original suite, untouched code). After: `results/v8_mac_security/attack_suite_after.json`. The original 15 attack definitions (A01-A08, P01-P07) are unchanged; A16, A17, P08, P09 are new ids. The suite now creates a throw-away anchor key held only by the suite process (controller); no attack except P08 is given it.

| Id | Before | After | Mechanism that now fires |
|---|---|---|---|
| H00 control | no effect | no effect | all checks pass, anchor ok |
| A01 patch canonicaliser | detected (shadow) | detected (shadow) | unchanged |
| A02 forge via harness finish | detected (shadow) | detected (shadow) | unchanged |
| A03 os._exit | blocked | blocked | unchanged |
| A04 garbage on result fd | blocked | blocked | unchanged |
| A05 close result fd | blocked | blocked | unchanged |
| A06 forged line on stdout | no effect | no effect | unchanged |
| A07 sense harness | detected (shadow) | detected (shadow) | unchanged |
| **A08** hide stdout via `Cap.write` | **SUCCEEDS** | **DETECTED** | `independent_capture`: harness claims "" , parent tee saw "extra output"; V8 verdict INSUFFICIENT |
| P01 edit observation | detected | detected | chain, verify |
| P02 edit verdict + re-chain | detected | detected | verify, sidecar, capture, anchor |
| P03 drop verdict.json | detected | detected | provenance + anchor |
| **P04** edit unverified field + re-chain + re-bind sidecar | **SUCCEEDS** | **DETECTED** | `anchor_mac` (key held by controller) and capture binding (head/timings) |
| P05 tamper sidecar hits | detected | detected | sidecar, anchor |
| P06 substitute another program's evidence | detected (needs expected_sources) | same | source_binding; still only with `expected_sources` |
| P07 re-chain without re-binding | detected | detected | sidecar, capture, anchor |
| A16 (new) close fd 2, patch Cap, print | n/a | DETECTED | record incomplete (no close record) |
| A17 (new) forged tee record, guessed nonce | n/a | DETECTED | foreign record -> untrusted (fail safe; can deny a true divergence, never fake a clean one) |
| P08 (new) key-holding writer re-chains and re-anchors everything | n/a | **SUCCEEDS (open, by design)** | nothing in the directory; needs an out-of-band pinned head (`trust.check(pinned_head=)` detects it, tested) |
| P09 (new) strip the anchor | n/a | DETECTED if a key or `require_anchor` is supplied | `anchor_mac` (absent but expected) |

Totals after: 20 rows = control + 19 attacks; detected 14, blocked by the engine 3, no effect 1 (A06), still succeeds 1 (P08). Original 15: 0 open.

## Why A08 and P04 are not over-claimed
- A08 is detected because the *Cap-level* hiding leaves the parent's independent record intact. A program that replaces `sys.stdout` entirely inside its own process emits nothing to harness, tee or fd 1; there is nothing to disagree and the run stays trusted (test `test_known_limit_...`). A program that reads the nonce from its argv and forges consistent records is likewise undetected. Same-address-space adversaries remain out of scope (red-team M-4).
- P04 is detected only where (a) the verifier holds the key (`anchor_key` / `SBGV8_ANCHOR_KEY`) and (b) the writer does not. Without a key the report says `unverified_no_key`. P08 shows the boundary.

## Residual (not done, not claimed)
Linux/VM isolation; a genuinely out-of-process harness (canonicalisation outside the program's process, M-4 recommendation); key custody beyond "controller process memory / env"; byte-exact binary stdout; `sandbox-exec` is deprecated by Apple.
