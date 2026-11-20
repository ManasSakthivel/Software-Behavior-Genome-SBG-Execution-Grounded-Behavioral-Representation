# SBG V8: security and threat-model reconciliation (audit)

Audited tree: `research/v8-linux-validation` @ `07ecd5b7`. The audit was read-only on repo code and results. All outcome rows are in `audit/security_outcomes.json`, built by `scripts/build_security_outcomes.py`. Each row carries:
- `attack_id` and `class`;
- `reported_outcome` and the audited `outcome`;
- `evidence_status`;
- `source`.

Evidence-status vocabulary:
- **executed-with-raw-evidence**: a result JSON produced by code that drives the real collector (`trust._engine` → `collect.run_capture` → V7-B engine in the sandbox).
- **test-code-only**: an asserting test exists but no stored result.
- **report-text-only**: prose only. No code in the repo produces the claim.

**New evidence from this audit.** `scripts/audit_security_rerun.py` re-ran `trust.forgery_suite()` and six sensing probes at HEAD `07ecd5b7` on **macOS 26.7 arm64 / Python 3.13 / sandbox-exec**. Output: `audit/security_rerun_darwin.json`. The run took 8.6 s, and the capability probe reported:
- network_denial, write_confinement, rlimit_cpu, rlimit_nofile and rlimit_fsize ACTIVE;
- rlimit_as and rlimit_nproc UNAVAILABLE.

This is the only post-`2edfe568` re-test that has an artefact. It was **not** run on Linux.

---

## 1. Original attack suite (in-program and post-hoc forgery, `sbgv8/trust.py:209-226, 275-323`)

The pair is base `x+1` and variant `x+2` on input 1, so the honest verdict is DIVERGENT. Outcome labels come from `trust._classify` (`trust.py:259-272`):

| Label | Meaning |
|---|---|
| DETECTED | some check fired |
| BLOCKED | the engine degraded the verdict to INSUFFICIENT |
| NO EFFECT | the true verdict was kept |
| SUCCEEDS | a false verdict, or altered evidence with no check firing |

| Id | Class | Mac before (`results/v8_mac_security/attack_suite_before.json`) | Mac after (`…_after.json`, @8e28f601) | Audit rerun HEAD, darwin | Detected by | Prevents false verdict? |
|---|---|---|---|---|---|---|
| H00 | control | no effect (DIV) | no effect | no effect | n/a | n/a |
| A01 patch `__main__.canon` | in-process tamper | detected | detected | detected | shadow re-observation | **No**: effective verdict stays NDO unless the reviewer runs `trust.check(shadow=True)` |
| A02 forge via harness `finish()` | in-process tamper | detected | detected | detected | shadow | **No** (same reason) |
| A03 `os._exit` | result channel | blocked | blocked | blocked | engine (no frame) | yes (INS) |
| A04 garbage to fds | result channel | blocked | blocked | blocked | engine (protocol error) | yes (INS) |
| A05 close fds | result channel | blocked | blocked | blocked | engine | yes (INS) |
| A06 forged frame on stdout | result channel | no effect | no effect | no effect | stdout is not protocol | yes |
| A07 sense `canon` in `__main__` | sensing | detected | detected | detected | shadow | **No** (same reason) |
| A07c sense argv for harness/shadow | sensing | n/a (not in mac suite) | n/a | **no effect (DIV)** | argv sanitisation (`harness.py:12`) | yes |
| A08 patch `Cap.write`, hide stdout diff | in-process tamper | **succeeds** | detected | detected | independent capture (tee) | yes (effective INS) |
| A16 close fd 2, then A08 | in-process tamper | n/a | detected | detected | independent capture (incomplete record) | yes (INS) |
| A17 forge tee record with guessed nonce | in-process tamper | n/a | detected | detected | independent capture (foreign record) | yes, but a **true DIV becomes INS** (denial of a true divergence) |
| P01 edit observation, no re-chain | post-hoc | detected | detected | detected | chain, verify | yes (INS) |
| P02 edit verdict + re-chain | post-hoc | detected | detected | detected | verify, sidecar, capture, anchor | yes |
| P03 delete verdict.json | post-hoc | detected | detected | detected | anchor, verdict_json_absent | yes |
| P04 edit unverified field + re-chain + re-bind sidecar | post-hoc | **succeeds** | detected | detected | capture binding, anchor MAC | yes, if the verifier holds the key |
| P05 tamper sidecar hits | post-hoc | detected | detected | detected | sidecar, anchor | yes |
| P06 substitute evidence of another program | substitution | detected | detected | detected | source binding (`expected_sources`) | **No**: effective verdict stays NDO. Detection requires the reviewer to supply expected sources |
| P07 re-chain without re-binding sidecar | post-hoc | detected | detected | detected | sidecar, capture, anchor | yes |
| P08 re-chain and re-anchor **with the key** | post-hoc (key holder) | n/a | **succeeds** | **succeeds** | none (by design) | no: out of scope, needs an out-of-band pinned head |
| P09 strip anchor | post-hoc | n/a | detected | detected | anchor (key/require supplied) | yes, only if the verifier passes a key or `require_anchor` |

Counts:
- **Before, mac:** 15 attacks. 9 detected, 3 blocked, 1 no effect, 2 succeeded (A08, P04).
- **After, mac:** 19 attacks. 14 detected, 3 blocked, 1 no effect, 1 succeeded (P08, the key-holder boundary).
- **HEAD rerun:** 20 attacks including A07c. 14 detected, 3 blocked, 2 no effect, 1 succeeded (P08).

**The "forgery attacks fixed in mac hardening"** are A08 and P04. They are fixed (detected, verdict forced to INSUFFICIENT) on macOS. There is raw evidence for both, and `tests/v8/test_trust.py:75-89` pins them. That test passes in this audit's run (247 passed).

---

## 2. Linux expanded suite (`scripts/run_expanded_security_suite.py` → `results/v8/linux/expanded_security_suite_results.json`)

**Evidence status: executed-with-raw-evidence, with caveats.** The script drives the real collector (`trust._engine`, `trust._row`, `ES.validate_dir`, `trust.check`). However, the JSON contains:
- no host, platform or kernel field;
- no timestamps or commit id;
- no record of which sandbox (bwrap, unshare or none) was active;
- no H00 honest control.

That it ran on the Linux VM is therefore asserted only in the report text. The file was committed in `d88b6986` and has not been regenerated since `2edfe568`.

### 2.1 Container probes (74)

The reported and JSON counts agree: **65 BLOCKED, 8 MITIGATED, 1 SUCCESSFUL**. The per-category split in `LINUX_ADVERSARIAL_TEST_REPORT.md` §3 does **not** match the JSON:

| Category | JSON | Report |
|---|---|---|
| FS | 6 blocked + 4 mitigated | "10/10 blocked" |
| NET | 8 blocked | 8 blocked |
| PROC | 10 blocked | 10 blocked |
| RES | 7 blocked + 1 mitigated (8 probes) | "10 probes" |
| FD | 10 blocked | "8" |
| PY | 11 blocked + 3 mitigated (14 probes) | absent |
| SENSE | 13 blocked + 1 succeeded (14 probes) | "10" |
| CHAN | absent | "8" |

**What "BLOCKED" means in this suite.** The label comes from `trust._classify`'s "BLOCKED by engine (verdict degraded to INSUFFICIENT)". It means the final verdict was INSUFFICIENT. It is **not** a record of an OS denial: no errno, capability or probe output is stored. All 65 BLOCKED rows share a pattern:
- shadow `not_comparable`;
- capture `ok`;
- `issues=[]`;
- duration ≈ 0.2 s, against 0.7–3.1 s for the 9 rows that reached a verdict.

Probes whose code returns `x+2` unconditionally under the reported environment also landed in BLOCKED:
- `SENSE07_sense_time_delay` (always `x+2`);
- `SENSE13_sense_uid_gid` (uid ≠ 0 → `x+2`);
- `PROC10`, `PY04 gc.disable` and others.

Each of these should yield DIVERGENT. In this audit's darwin rerun, the identical `SENSE07` code gave **DIVERGENT** in a normal run.

Conclusion: most or all of the 65 INSUFFICIENT verdicts are runs that never reached a decision. The likely causes are engine or sandbox failure under the 8-worker `ProcessPoolExecutor` (`run_expanded_security_suite.py:134`) or a missing sandbox capability. The data cannot tell which.

They are **fail-safe**: no false NDO. They are **not** evidence that the attack was blocked by isolation. This audit records them as `insufficient_unexplained`.

The 8 MITIGATED rows (FS02, FS04, FS05, FS07, RES05, PY02, PY06, PY09) kept the true DIV verdict, with shadow `match`. The attack had no effect on the verdict. Whether the OS denied the write, symlink or mknod is not recorded.

**SENSE04** (`'variant' in __file__`) gave **NO_DIVERGENCE_OBSERVED with no check firing**, including the shadow, because the shadow at that time also set `__file__ = src`. This is a successful false assurance on pre-`2edfe568` code.

### 2.2 Tamper probes (51)

All 51 are **DETECTED**, meaning `validate_dir.trusted == False` or `trust.check` issues ≠ ∅. The real attacker and the real validator were exercised.

The 51 rows contain only **24 distinct operations** (`run_expanded_security_suite.py:218-263`):

| Group | Distinct operations | Rows | Identical "else" rows |
|---|---|---|---|
| EV | 7 | 15 | EV_07–15 append the same fake line |
| CAP | 7 | 15 | CAP_07–15 set the same config_sha256 |
| PART | 5 | 10 | PART_05–10 flip the same outcome |
| ANC | 4 | 6 | ANC_04–06 zero the same file digest |
| SUBST | 1 | 5 | all identical |

None of the 51 is a **key-holding** or **consistent re-chain + re-bind + re-anchor** forgery. Only EV_06 re-chains, and it does not re-bind capture or anchor. So the 51/51 says nothing about the P08 boundary.

SUBST is detected only because `expected_sources` was supplied (`trust.check`). In the default verdict path, substitution is not detected (see P06).

---

## 3. Specific remediations

| Item | Fix (code) | Re-test evidence | Status |
|---|---|---|---|
| A08 stdout hiding | `procsep.Supervisor` + `_tee_child.py` tee to the real fd 2; parent `judge` compares with the harness stdout (`procsep.py:65-83, 106-134`) | mac after JSON, audit rerun (darwin), `test_security_capture.py:46` | **Fixed on macOS (executed).** Limit: a program that replaces `sys.stdout` itself is invisible. `test_security_capture.py:70` pins this as a known limit, so A08 is mitigated only against `Cap.write` patching |
| P04 evidence-field manipulation | `v8_capture.json` per-run binding + HMAC anchor (`evidence_schema.py:142-194, 104-135`) | mac after JSON, audit rerun, Linux CAP/ANC rows | **Fixed (detected) when the verifier holds the key.** P08 (key holder) still succeeds |
| A07c argv sensing | `harness.py:12` `sys.argv=["target_program.py"]` (2edfe568; before: `[SRC]`, the variant's real path); shadow likewise (`trust.py:20`) | Linux: **report-text-only** (`EVIDENCE_INTEGRITY_REMEDIATION.md` quotes the wrong code, `sys.argv=[a["src"]]`). Audit rerun darwin @HEAD: **no effect (true DIV)** | Mitigated on macOS (executed here). Linux unverified |
| SENSE04 `__file__` sensing | 2edfe568: `mod.__file__="target_program.py"` (`harness.py:192`), shadow `__file__`/`__name__` (`trust.py:36`) | Linux: **none** (the commit touches code only; the results JSON predates it). Audit rerun darwin: SENSE04 **no effect (true DIV)** | **Partially remediated.** The audit's variant **SENSE04b** (`'variant' in f.__code__.co_filename`) **SUCCEEDS**: a false NDO with no check firing, because `compile`/`spec_from_file_location` keep the real path in `co_filename`. **SENSE04c** (`__spec__.origin`) gives a false engine NDO, caught only by the optional shadow. The real fix is anonymised temp file names (per the report's own recommendation); it is not implemented |
| Cross-pair substitution | `trust.check(expected_sources=…)` sha256 binding (`trust.py:173-179`) | P06 in mac JSONs and audit rerun; Linux SUBST ×5 (one operation) | **Detected only when the reviewer supplies expected sources. Not prevented**: integrity_ok and the effective verdict ignore it |
| Shadow re-observation | `trust.shadow_run/shadow_check` (`trust.py:91-129`) | A01/A02/A07 detected in all three runs | **Detection only; optional; return values only.** Does not compare stdout, files, globals or argmut. Defeated by a program that behaves the same in the harness and the shadow (SENSE04b) |
| Container isolation / resource controls | bwrap `--unshare-net --ro-bind / /` + rlimits (`isolation.py:71-78, 118-123`) | Podman ISO-01..10: **report-text-only**. No code invokes podman. PID namespace, seccomp, nproc and cgroups are not in the code. Linux FS/NET/PROC/RES rows: verdict-level only | **Unverified on Linux.** On macOS the capability self-probe shows network denial and write confinement ACTIVE (audit rerun) |

**Were post-remediation re-tests executed on Linux?**

| Claim | Linux artefact |
|---|---|
| A07c "now detected" | none |
| SENSE04 fix | none |
| "Original 15 + A16/A17 verified via forgery_suite()" | none |
| "608 tests, 593 passed" (`FULL_REGRESSION_REPORT.md`) | none (no junit or log) |

All four are **report-text-only**. The only post-fix artefact is this audit's macOS rerun.

---

## 4. Outcome counts (for the figure; `security_outcomes.json`)

| Suite (rows) | blocked | detected | mitigated (no effect) | succeeded | insufficient_unexplained | unresolved (report-only) |
|---|---|---|---|---|---|---|
| mac_original_before (16 incl. control) | 3 | 9 | 2 | 2 | – | – |
| mac_original_after (20 incl. control) | 3 | 14 | 2 | 1 | – | – |
| audit_rerun_head_darwin (27 incl. control + 6 sensing) | 3 | 15 | 7 | 2 (P08, SENSE04b) | – | – |
| linux_container_74 | 0 | 0 | 8 | 1 (SENSE04) | 65 | – |
| linux_tamper_51 (24 distinct) | 0 | 51 | 0 | 0 | – | – |
| linux_podman_isolation (ISO-01..10) | – | – | – | – | – | 10 |
| linux_report_claims (A07c-Linux, SENSE04-Linux, ORIG15-Linux, REG608) | – | – | – | – | – | 4 |

"Mitigated" counts include the H00 control and A06 for the mac suites.

---

## 5. Threat model as supported by the evidence

**In scope (and what the system achieves):**

1. **Adversarial evaluated program, in-process Python, same uid, inside the sandbox.**
   - *Prevented (fail-safe INSUFFICIENT):* result-channel attacks (A03–A05); stdout hiding by patching `Cap` (A08, A16); forged or foreign tee records (A17). A17 can turn a true divergence into INSUFFICIENT; this is a denial, not a false assurance.
   - *Detected only, with an optional check:* harness canonicaliser or result forgery and `__main__` sensing (A01, A02, A07). These need `trust.check(shadow=True)`, and the default verdict remains a false NDO.
   - *Not handled:* file-path sensing through `co_filename` (SENSE04b; executed here, succeeds); a program that replaces `sys.stdout`/`os.write` or reads the nonce from argv and forges consistent tee records (documented, `procsep.py:13-15`); any divergence in non-return channels combined with shadow evasion.
2. **Post-hoc evidence writer without the anchor key.**
   - *Detected*, which forces INSUFFICIENT through `validate_dir` → `integrity_ok`: log edits, re-chains, sidecar and capture edits, anchor stripping (when the verifier requires an anchor or passes a key), and verdict.json deletion. There is executed evidence on macOS, plus Linux tamper rows covering 24 distinct operations.
3. **Evidence substitution (another pair's genuine evidence).**
   - *Detected only* when the reviewer supplies `expected_sources`. Not part of the verdict path.

**Out of scope:**
- **Key holders**, including any writer running as the controller user who can read `SBGV8_ANCHOR_KEY`. P08 succeeds; only an out-of-band pinned head, which nobody currently supplies, would detect it.
- **Host root, kernel or container-runtime compromise.**
- **Native-code attacks** on the tee or harness in the same address space (ctypes memory writes). PY10 and PY11 rows are INSUFFICIENT with no recorded cause.
- **Side channels and timing.**
- **Sandbox escape on Linux**: no executed evidence of PID, user or seccomp confinement, and Podman is not used by the code.

**Final verified security position (for the paper).** On macOS, with the sandbox-exec profile active, every attack in the original 15-attack suite that originally produced a false or altered result is now either:
- **prevented**, meaning the effective verdict is forced to INSUFFICIENT (A03–A05, A08, A16, A17, P01–P05, P07, P09); or
- **detected only** by optional reviewer-side checks (A01, A02, A07, P06).

The exceptions are the key-holder forgery P08, which is out of scope, and a newly found file-path sensing bypass (SENSE04b), which is open.

On Linux the code ran through bwrap or unshare, not Podman. The suite completed: 1 false assurance (SENSE04, pre-fix), 51/51 tamper rows detected (24 distinct operations), and 73 container probes with no false NDO. However, 65 of those 73 are unexplained INSUFFICIENT verdicts, so they do not demonstrate isolation. No post-remediation Linux re-test artefact exists.

The paper should claim **fail-safe evidence integrity against non-key-holding writers** and **detection (not prevention) of in-process harness forgery**. It should **not** claim:
- Podman isolation;
- PID or seccomp confinement;
- "guaranteed host isolation";
- "guaranteed against child monkeypatching" (contradicted by `procsep.py:13-15` and `test_security_capture.py:70`).

---
## Reproduction

All commands below run on macOS, from the repo root.

1. Re-run the attacks and probes (writes `audit/security_rerun_darwin.json`):
   `PYTHONPATH=. /Users/manassakthivel/Desktop/SBG-V6/.venv/bin/python paper/IEEE_ACCESS_V8_FINAL/scripts/audit_security_rerun.py`
2. Build the outcome table (writes `audit/security_outcomes.json`, 202 rows):
   `python3 paper/IEEE_ACCESS_V8_FINAL/scripts/build_security_outcomes.py`
3. Draw the figures (writes `figures/fig_*.pdf`):
   `/Users/manassakthivel/Desktop/SBG-V6/.venv/bin/python paper/IEEE_ACCESS_V8_FINAL/scripts/make_diagrams.py`
