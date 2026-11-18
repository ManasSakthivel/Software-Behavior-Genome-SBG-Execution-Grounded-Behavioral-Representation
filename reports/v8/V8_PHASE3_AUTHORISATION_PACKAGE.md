# V8 Phase 3 authorisation package

Per 11, Phase 3 is NO-GO until the user explicitly authorises it. This document lists what would need authorisation; **nothing in it has been done or is authorised by being written down.** Authorise each item separately (A1..A7).

## A1. Linux/Docker validation of the trust layer (V8-A)
Provision a Linux VM or Docker host; run the forgery suite (`sbgv8.trust.forgery_suite`) under real isolation (namespaces/seccomp/read-only mounts, no network); record image digests and kernel. Pass criterion: suite passes with no undetected forgery; otherwise the paper states trust is conditional on non-adversarial programs (fallback F4). Requires: machine access, cost estimate, retention policy for logs. Does not authorise running third-party code.

## A2. Independent repository execution protocol
Third-party repositories run only inside A1-validated containers: pinned commit, no network after dependency install from a hash-locked mirror, CPU/memory/time caps, non-root, read-only source, evidence directory the only writable mount, per-run environment record. Declared entry points and input specs are fixed before execution. Failures and timeouts count as INSUFFICIENT for every system (06); no pair silently dropped. Requires explicit approval of the repository list (A3) and of the execution host.

## A3. External dataset collection
Target (07): >= 60 projects (prefer 80), <= 8 pairs per project; >= 250 divergent, >= 350 non-divergent (>= 100 hard negatives); final holdout >= 20 projects and >= 200 pairs.
Inclusion criteria: public open-source Python project with permissive licence; real version pair with declared entry point and input specification; pair executable under A2; change touches executable code in scope; project not in the development manifest; forks and near-duplicate projects deduplicated.
Exclusion: unreproducible build, nondeterminism that cannot be controlled, no declared entry point, licence forbids use. Every exclusion is logged with a reason in the manifest.
Contamination controls: record membership in public benchmarks (QuixBugs, BugsInPy, others) and plausible LLM-training exposure; no commit-message or issue text in features; adjudicator inputs sealed from system evidence; project-level splits; family rule fixed before collection results are seen; collection done by someone who has not seen any model output.
Requires: network access to named hosts, storage, licence review. Source register in `SOURCE_ACCESS_REGISTER.csv` extended per source.

## A4. Adjudicator recruitment
Recruit at least 3 people (two primaries plus a third for disagreements; more for throughput) with Python experience, independent of the system's authors for primary roles. Instructions: `datasets/v8/adjudication_templates/ADJUDICATOR_INSTRUCTIONS.md`; blinding as in `V8_ADJUDICATION_PROTOCOL.md`. Requires: ethics/consent and compensation decision by the user, conflict-of-interest declaration, training on at most a handful of non-study pairs (never holdout pairs), a rule for who resolves a deadlocked third round (none: stays unresolved). Gate: kappa >= 0.7 on >= 30% double-labelled before any scoring; below it, revise the protocol.

## A5. Final holdout procedure and unlock policy
1. Registration (06) frozen and time-stamped by a third party before any holdout label exists; includes holdout selection seed, analysis scripts' hashes, predictors, c* grid.
2. Holdout rows carry no labels in the manifest; labels live in a separate sealed store. `splits.HoldoutGuard` refuses holdout label reads unless an unlock token file path is supplied and exists; every attempt is logged.
3. The token is created only by the user (a person, not an agent or script in this repository), only after steps 1 and the frozen-code hash check, and is used once. Scoring is run once; the result is reported whatever it is. A second look requires a new, fresh holdout.
4. The access log is published with the paper. The guard is a procedural control, not a security boundary: anyone with file access can bypass it, which is why the registration and the access log matter.

## A6. K5 adequacy assessment (arithmetic from `research/v8_final_design/scripts/sample_size_calc.py`; assumed inputs, not data)
- Issued NDO verdicts for a Wilson half-width 0.05 at R=0.20: 245 iid, 319 with DEFF (m=3, rho=0.15), 539 with DEFF (m=5, rho=0.30); half-width 0.07: 124 / 162 / 273.
- At issuance 0.25 to 0.40, 150 issued verdicts need 375 to 600 pairs; 250 need 625 to 1,000.
- Paired matched-coverage comparison, 80% power: 8pp needs 121 to 243 issued pairs (175 to 353 clustered); 5pp needs 312 to 626 (452 to 908).
- Conclusion (07): K5 (60 projects, 250 divergent) is adequate for a feasibility and risk-coverage study, not for narrow calibration intervals or for confirming a 5pp difference; MDE about 8-10pp at 600 pairs; recommend >= 600 adjudicated pairs from >= 60 (preferably 80) projects, grouped CV as primary inference, holdout as one-shot confirmation. Fallbacks: <400 pairs or <60 projects means a pilot with no calibration or H2 claim; kappa < 0.7 means stop; < 100 issued NDO means the claim reduces to abstention behaviour. The distribution-shift experiment additionally needs >= 3 families (see its protocol). The calculation must be re-run with realised issuance and rho after collection.

## A7. Independent reproduction checklist
- [ ] clean checkout at the registered commit; environment from the lock file; recorded interpreter and platform
- [ ] manifest hash matches the registration (`manifest_hash`); validate() returns no issues
- [ ] evidence archives match recorded sha256; `trust` check passes (or conditional-trust statement present)
- [ ] label files with adjudicator agreement, audit-chain head hash matches the registration; `verify_chain` ok
- [ ] scripts hashed as registered; recomputation of every number in the manuscript from result files by someone other than the author
- [ ] holdout access log shows one scoring, after registration
- [ ] negative and unresolved counts reported; all baselines present

## What is NOT requested here
No execution has started. Starting any of A1 to A5 without the user's explicit instruction is out of bounds for every agent.
