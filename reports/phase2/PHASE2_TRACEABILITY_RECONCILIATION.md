# Phase 2 traceability reconciliation (135 rules, current status)

Branch `research/v7b-final-validation`, HEAD `a6afa639`. Phase 2, local only: no Linux, Docker or external repository was used, and nothing in `sbgv7/`, `tests/`, `scripts/`, `experiments/`, `results/` or `artifacts/` was changed. This file does not choose between the two earlier counts. It recomputes the status of every rule from the frozen spec against the current code and tests, then explains each difference.

## 1. Inputs, method and limits of this review

| Item | Value |
|---|---|
| Count A | `PHASE_2_SPEC_CONFORMANCE_AUDIT.md` (HEAD `1206312e`): 135 rules = 63 Conforms / 45 Deviates / 23 Not implemented / 4 Unverifiable |
| Count B | earlier `FINAL_V7B_REQUIREMENTS_TRACEABILITY_MATRIX.md` (commit `f2aa9143`, marked unverified): by final disposition 68 Conforms / 23 Mandatory / 17 Specification correction / 15 Deferred / 7 Phase 3 / 5 Optional. Its separate "Status now" column is also compared (section 4). |
| Spec | `reports/final/V7B_FROZEN_SPEC.md` (FS s2-s12) and `reports/v7_design/p0_reconciliation/*`; FS is not edited by this work |
| Code | `sbgv7/*.py` at HEAD, read in full; line numbers were checked with `sed -n`/`grep -n` on the current files |
| Tests | `tests/v7/*.py`, read by `grep -n "def test_"`; every test name cited in this file and in the matrix was checked to exist as a `def` in the named file |
| Code and tests unchanged since the recorded run | `git diff --stat 5efcef74 HEAD -- sbgv7 tests` is empty. The recorded full run is **276 passed, 1 skipped** at `5efcef74` (`MB_SECOND_STAGE_REVIEW.md` s9; the skip is `test_memory_rlimit_as_hard`, RLIMIT_AS unavailable on macOS). |
| Mutation evidence | `scripts/mutation_check_mb.py`: 16/16 mutants killed (recorded in `MB_SECOND_STAGE_REVIEW.md` s4; 11 MB-16 items and 5 second-stage mutants) |
| NOT done in this task | no pytest, no `python -m sbgv7`, no experiment script and no sandboxed process was run (an experiment occupied the machine). The test evidence is therefore the recorded run, not a fresh one. Statuses rest on code reading plus the existence of the cited test, not on re-execution. |

Status scale and rules applied to every row:

| Status | Meaning here |
|---|---|
| Conforming | a code line implements the rule as the spec states it (or as a ratified decision states it) AND a named test that exists exercises it. A rule with code but no test is never Conforming (rows V11 and M3 are rated Partially for that reason). |
| Partially conforming | part of the rule is implemented and tested; a named clause is missing, an open user decision (UD-2) affects it, or the code is right but a test is missing. The row says which. |
| Deviating | the code does something different from the spec text; the deviation is known and documented. |
| Not implemented | no code path exists for the rule (including programme-deferred items). |
| Unverifiable | cannot be decided from code or tests alone, and no local action changes that. |
| Deferred to Phase 3 | the missing part can only be built or validated with Linux/Docker/external inputs, so Phase 2 does not attempt it and nothing local is partially met. Rows with a locally met part (for example I2, I4, I5) are Partially conforming and name Phase 3 as the owner of the rest. |

Ratified and open decisions used (from `FINAL_SPECIFICATION_DECISIONS.md`, "Ratifications"): UD-1 ratified as built; UD-3 option A and UD-4 option A implemented as recommended; Decision A (hash seed fixed) and Decision B (`datetime.now` not virtualised) ratified as limitations; UD-2 and UD-5 open. The `SD-nn` clarifications are implemented as recommended but were not separately ratified, and the FS text has not been edited. A row that depends only on such a clarification is marked Conforming when the code matches the clarification and a test exists, and its disposition says "spec text pending". The exception is B3a, where the literal FS sentence ("an unverified property gives sandbox_failure") is not met on macOS, so it is Partially conforming.

## 2. Current counts (sum check)

| Status | Rows |
|---|---|
| Conforming | 78 |
| Partially conforming | 30 |
| Deviating | 7 |
| Not implemented | 14 |
| Unverifiable | 2 |
| Deferred to Phase 3 | 4 |
| **Total** | **135** |

78 + 30 + 7 + 14 + 2 + 4 = 135. The total is 135 because the rule inventory (13 V, 19 B, 7 O, 15 C, 5 W, 8 P, 5 G, 15 S, 14 E/M, 10 I, 18 F, 6 X) is unchanged from both earlier documents; no rule was added or removed. Of the 30 Partially conforming rows, 2 are test gaps only (V11, M3: code evidence exists, no test).

## 3. Why the two earlier counts disagree, and what they measured

- Count A is a **status** count taken at `1206312e`, before any of the fixes `8f11d3aa` (D-01/D-02), `cc56e029` (D-05/D-06/D-09, lossy SAME) and MB-01..MB-16 (`5efcef74`). Many of its 45 Deviates and 23 Not implemented rows have since been fixed.
- Count B mixes two axes. Its 68/23/17/15/7/5 is a **disposition** count (what to do next), not a status count: a row that is fixed and a row that conforms both fall in "Conforms", while a row that needs a spec edit falls in "Specification correction" even when the code already matches. It was computed at `cc56e029`, before MB-01..16, and was marked unverified.
- The two counts therefore cannot be subtracted from each other. Section 4 compares the new status with A's status and with B's status column and, separately, with B's disposition.

| Status | A (audit) | B "Status now" column | New |
|---|---|---|---|
| Conforming (B: "Conforms" 62 + "Fixed since audit" 14) | 63 | 76 | 78 |
| Partially conforming (B: "Partial") | 0 | 5 | 30 |
| Deviating | 45 | 30 | 7 |
| Not implemented (B: 19, plus "Vacuous" 1 shown separately) | 23 | 19 | 14 |
| B "Vacuous" (G5s) | 0 | 1 | 0 |
| Unverifiable | 4 | 4 | 2 |
| Deferred to Phase 3 | 0 | 0 | 4 |
| **Total** | **135** | **135** | **135** |


## 4. Differences from the two earlier counts

### 4.1 Cross-tabulation (rows)

New status against A:

| A \ New | Conforming | Partially | Deviating | Not impl. | Unverifiable | Deferred P3 | Sum |
|---|---|---|---|---|---|---|---|
| Conforms (63) | 57 | 5 | 0 | 1 | 0 | 0 | 63 |
| Deviates (45) | 17 | 19 | 7 | 0 | 0 | 2 | 45 |
| Not implemented (23) | 4 | 6 | 0 | 13 | 0 | 0 | 23 |
| Unverifiable (4) | 0 | 0 | 0 | 0 | 2 | 2 | 4 |
| **Sum** | **78** | **30** | **7** | **14** | **2** | **4** | **135** |

**56 rows differ from A** (79 unchanged). Six of them are worse than A: V11 and M3 (Conforming in A; code evidence but no test), S2a (vacuous branch coverage still satisfies the floor, UD-2 open), S3 (default and refusal exist, no S3 mechanism), I5 (rule names a Linux path that does not exist) and G5s (A: Conforms as vacuous; nothing implements or tests the rule). The other 50 are improvements through `8f11d3aa`, `cc56e029`, MB-01..16 or the ratifications.

New status against B's "Status now" column:

| B \ New | Conforming | Partially | Deviating | Not impl. | Unverifiable | Deferred P3 | Sum |
|---|---|---|---|---|---|---|---|
| Conforms (62) | 57 | 5 | 0 | 0 | 0 | 0 | 62 |
| Fixed since audit (14) | 9 | 5 | 0 | 0 | 0 | 0 | 14 |
| Deviates (30) | 9 | 12 | 7 | 0 | 0 | 2 | 30 |
| Not implemented (19) | 3 | 3 | 0 | 13 | 0 | 0 | 19 |
| Partial (5) | 0 | 5 | 0 | 0 | 0 | 0 | 5 |
| Vacuous (1) | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| Unverifiable (4) | 0 | 0 | 0 | 0 | 2 | 2 | 4 |

**42 rows differ from B's status column** (93 unchanged; G5s counts as changed because B called it Vacuous). Of those 42: 10 are rows B rated Conforms or Fixed that are only Partially now (V10, V11, B2d, B3b, S1c, S2a, S3, E9, M3, I5); 23 are B Deviates rows (9 now Conforming, 12 Partially, 2 Deferred to Phase 3); 6 are B Not implemented rows (3 Conforming, 3 Partially); 2 are Unverifiable rows now Deferred to Phase 3; 1 is G5s (Vacuous to Not implemented). Most of the B Deviates and Not implemented changes exist because MB-01..16 (`5efcef74`) landed after B was written.

Against B's disposition count (68 Conforms): 62 of those 68 are Conforming now; 6 are Partially conforming (V11, B2d, B3b, E9, M3, I5). 16 rows that B placed in an action bucket are Conforming now: Mandatory (11) V2, V13, B2a, B6, P7, F2, F6, F7, F18, X2, I8; Specification correction (4) B0r, B5, B9, S1g; Optional (1) P2. The other action-bucket rows keep an action (Partially, Deviating, Not implemented or Deferred). 68 - 6 + 16 = 78.

### 4.2 Reconciliation table (all 135 rules)

Columns: `dA` = new status differs from A; `dB` = new status differs from B's "Status now" column. B's cell shows B's status and, after the slash, B's final disposition. The full requirement, code line and test per rule are in `FINAL_V7B_REQUIREMENTS_TRACEABILITY_MATRIX.md`.

| Rule | A: audit | B: matrix (status / disposition) | New | dA | dB | Reason |
|---|---|---|---|---|---|---|
| V1 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| V2 | Conforms | Deviates / Mandatory | Conforming | - | Y | B: assert stripped under -O (mandatory). Fixed by MB-04 in 5efcef74. |
| V3 | Deviates | Deviates / Mandatory | Partially conforming | Y | Y | A,B: leftover evidence.jsonl fixed by MB-08. Remaining scope limit (single file) keeps it at Partially. |
| V4 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| V5 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| V6 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| V7 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| V8 | Not implemented | Not implemented / Deferred | Not implemented | - | - | Unchanged against both. |
| V9 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| V10 | Deviates | Fixed since audit / Spec correction | Partially conforming | Y | Y | A: R-shrinking fixed (cc56e029). B marked it fixed pending ratification. UD-2 still open, so the NDO statement is vacuous for r_empty pairs: Partially. |
| V11 | Conforms | Conforms / Conforms | Partially conforming | Y | Y | A,B: Conforming on code reading/probe. Now rated by the rule 'no Conforming without an existing test'. |
| V12 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| V13 | Deviates | Deviates / Mandatory | Conforming | Y | Y | A,B: KeyError/assert. Fixed by MB-04. |
| B0 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| B0r | Conforms | Conforms / Spec correction | Conforming | - | - | B counted it as a specification correction (tie-break text). Status is Conforming: code and test exist; the spec-text gap does not change conformance. |
| B1 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| B2a | Deviates | Deviates / Mandatory | Conforming | Y | Y | A,B: no test, mandatory. MB-16 added the test and a mutation kill. |
| B2b | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| B2c | Not implemented | Not implemented / Deferred | Not implemented | - | - | Unchanged against both. |
| B2d | Not implemented | Fixed since audit / Conforms | Partially conforming | Y | Y | A: never produced. B: counted Conforms. Produced now, but only for single-file non-executable lines: Partially. |
| B3a | Deviates | Deviates / Mandatory | Partially conforming | Y | Y | A,B: nothing but network gated. MB-06 gates 6 required properties; the literal FS text (all properties) is not met on macOS. |
| B3b | Not implemented | Fixed since audit / Conforms | Partially conforming | Y | Y | A: never produced. B: Conforms. Produced for protocol violation/tamper; policy-violation detection missing: Partially. |
| B4a | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| B4b | Deviates | Deviates / Mandatory | Partially conforming | Y | Y | A,B: random.seed and time.time only. MB-07 widened virtualisation; trigger rule and the two ratified non-virtualised sources keep it Partially. |
| B5 | Deviates | Deviates / Spec correction | Conforming | Y | Y | A: deviation. B: spec correction. UD-4 A ratified after both counts, which fixes the reading. |
| B6 | Deviates | Deviates / Mandatory | Conforming | Y | Y | A,B: every NO_RUN cause mapped to resource_limit. MB-10 carries the cause; UD-4 A ratified. |
| B7a | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| B7b | Not implemented | Not implemented / Mandatory | Partially conforming | Y | Y | A: not implemented. B: mandatory. MB-02 closes the probe-confirmed gap but no blind-spot detector exists: Partially. |
| B8a | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| B8b | Deviates | Fixed since audit / Conforms | Conforming | Y | - | A: deviation (both-bind counted SAME). Fixed cc56e029; UD-1 ratified. |
| B8c | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| B9 | Conforms | Conforms / Spec correction | Conforming | - | - | B counted it as a specification correction (SD-19). Code and tests exist and MB-11 fixed the last-input case; Conforming. |
| O1 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| O2 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| O3 | Deviates | Deviates / Spec correction | Deviating | - | - | Unchanged against both. |
| O4 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| O5 | Deviates | Deviates / Phase 3 | Deferred to Phase 3 | Y | Y | A,B: deviation. Not locally satisfiable or verifiable: Deferred to Phase 3. |
| O6 | Deviates | Deviates / Mandatory | Partially conforming | Y | Y | A,B: bigint probe gave false NDO S2. Fixed by MB-01; reason code differs from the spec text. |
| O7 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| C1 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| C2 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| C3 | Not implemented | Not implemented / Deferred | Not implemented | - | - | Unchanged against both. |
| C4 | Deviates | Fixed since audit / Conforms | Conforming | Y | - | A: deviation, fixed 8f11d3aa. |
| C5 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| C6 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| C7 | Deviates | Deviates / Optional | Deviating | - | - | Unchanged against both. |
| C8 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| C9 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| C10 | Deviates | Fixed since audit / Conforms | Conforming | Y | - | A: deviation, fixed 8f11d3aa. |
| C11 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| C12 | Deviates | Deviates / Mandatory | Partially conforming | Y | Y | A,B: source path leaked (false witness). MB-03 fixed that; the spec's wider list is not covered. |
| C13 | Deviates | Deviates / Spec correction | Deviating | - | - | Unchanged against both. |
| C14 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| C15 | Deviates | Deviates / Spec correction | Deviating | - | - | Unchanged against both. |
| W1 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| W2 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| W3 | Not implemented | Not implemented / Deferred | Not implemented | - | - | Unchanged against both. |
| W4 | Deviates | Fixed since audit / Conforms | Conforming | Y | - | A: ids only. Fixed cc56e029. |
| W5 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| P1 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| P2 | Conforms | Conforms / Optional | Conforming | - | - | B counted it as optional (early stop). Behaviour matches the rule (5/5 reproduce); only cost differs; Conforming. |
| P3 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| P4 | Not implemented | Not implemented / Deferred | Not implemented | - | - | Unchanged against both. |
| P5 | Deviates | Deviates / Mandatory | Partially conforming | Y | Y | A,B: random.seed and time.time only. MB-07 widened it; two ratified exclusions remain. |
| P6 | Not implemented | Not implemented / Optional | Not implemented | - | - | Unchanged against both. |
| P7 | Deviates | Deviates / Mandatory | Conforming | Y | Y | A,B: parent time uncharged, per-input granularity. Fixed by MB-11. |
| P8 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| G1s | Deviates | Deviates / Optional | Partially conforming | Y | Y | A,B: deviation. Compatibility check works; the declared-rename clause is missing, so Partially. |
| G2s | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| G3s | Deviates | Fixed since audit / Conforms | Conforming | Y | - | A: deviation, fixed cc56e029. |
| G4s | Not implemented | Not implemented / Optional | Not implemented | - | - | Unchanged against both. |
| G5s | Conforms | Vacuous / Deferred | Not implemented | Y | Y | A: Conforms (vacuous). B: vacuous. Now Not implemented: nothing implements or tests the rule. |
| S1a | Deviates | Deviates / Mandatory | Partially conforming | Y | Y | A,B: flat hash. MB-12 done; enum extension and no domain separation: Partially. |
| S1b | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| S1c | Deviates | Fixed since audit / Spec correction | Partially conforming | Y | Y | A: R shrunk. B: fixed pending ratification. UD-2 open: Partially. |
| S1d | Deviates | Conforms / Conforms | Conforming | Y | - | A: not in verdict.json. Exposed since cc56e029. |
| S1e | Deviates | Fixed since audit / Conforms | Conforming | Y | - | A: deviation, fixed cc56e029. |
| S1f | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| S1g | Deviates | Deviates / Spec correction | Conforming | Y | Y | A,B: conservative deviation. UD-4 A ratified. |
| S1h | Deviates | Deviates / Spec correction | Partially conforming | Y | Y | A,B: no tier. capture_tier=L0 constant now accepted; no bitmap record. |
| S1i | Deviates | Partial / Mandatory | Partially conforming | Y | - | A: deviation. Truncation and tamper are wired and tested since 8f11d3aa/MB; blind-spot clause missing. Same as B (partial). |
| S2a | Conforms | Conforms / Spec correction | Partially conforming | Y | Y | A,B: Conforms (approximation). Vacuous coverage still satisfies the floor: Partially. |
| S2b | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| S2c | Not implemented | Not implemented / Mandatory | Partially conforming | Y | Y | A: not implemented. B: mandatory. MB-02 closed the known gap; the flag is not computed: Partially. |
| S2d | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| S3 | Conforms | Conforms / Deferred | Partially conforming | Y | Y | A: Conforms. Default conforms but nothing of S3 exists: Partially. |
| S0 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| E1 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| E2 | Deviates | Deviates / Spec correction | Partially conforming | Y | Y | A: absent. Content now present inside EvidencePackage but not as separate kinds: Partially. |
| E3 | Deviates | Fixed since audit / Conforms | Conforming | Y | - | A: ids only. Fixed cc56e029. |
| E4 | Deviates | Fixed since audit / Conforms | Conforming | Y | - | A: no per-input rows. Fixed cc56e029 and MB-12. |
| E5 | Deviates | Partial / Spec correction | Partially conforming | Y | - | A: absent. Partial since cc56e029. |
| E6 | Not implemented | Fixed since audit / Conforms | Conforming | Y | - | A: no recompute. Added in cc56e029. |
| E7 | Unverifiable | Unverifiable / Phase 3 | Unverifiable | - | - | Unchanged against both. |
| E8 | Not implemented | Not implemented / Deferred | Not implemented | - | - | Unchanged against both. |
| E9 | Deviates | Fixed since audit / Conforms | Partially conforming | Y | Y | A: weak verify. B: Conforms. Detects accidental and non-recomputing edits only: Partially. |
| E10 | Not implemented | Not implemented / Spec correction | Not implemented | - | - | Unchanged against both. |
| E11 | Deviates | Partial / Deferred | Partially conforming | Y | - | B: partial. Same. |
| M1 | Not implemented | Partial / Deferred | Partially conforming | Y | - | A: not implemented. B: partial. Same as B. |
| M2 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| M3 | Conforms | Conforms / Conforms | Partially conforming | Y | Y | A,B: Conforms by probe. No test: Partially under the rule. |
| I1 | Deviates | Deviates / Mandatory | Partially conforming | Y | Y | A,B: no profile. MB-07 added it; the -I and 3.13-gate clauses differ: Partially. |
| I2 | Deviates | Deviates / Phase 3 | Partially conforming | Y | Y | A,B: deviation (Phase 3). Locally four of six controls are active and tested: Partially. |
| I3 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| I4 | Deviates | Partial / Phase 3 | Partially conforming | Y | - | A: forgeable channel. D-02 fixed for protocol forgery; adversarial residual remains. |
| I5 | Conforms | Conforms / Conforms | Partially conforming | Y | Y | A,B: Conforms (macOS). The rule names a Linux path that does not exist: Partially. |
| I6 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| I7 | Deviates | Deviates / Phase 3 | Deferred to Phase 3 | Y | Y | A,B: deviation attributed to Phase 3. Not locally satisfiable: Deferred to Phase 3. |
| I8 | Conforms | Conforms / Mandatory | Conforming | - | - | B counted it as mandatory (weak test). MB-16 asserts the flag on darwin and a version test exists; Conforming. |
| I9 | Unverifiable | Unverifiable / Deferred | Unverifiable | - | - | Unchanged against both. |
| I10 | Unverifiable | Unverifiable / Phase 3 | Deferred to Phase 3 | Y | Y | A,B: unverifiable. Scheduled to Phase 3 (Linux hostile fixtures). |
| F1 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| F2 | Not implemented | Not implemented / Mandatory | Conforming | Y | Y | A,B: absent. MB-13. |
| F3 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| F4 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| F5 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| F6 | Not implemented | Not implemented / Mandatory | Conforming | Y | Y | A,B: absent. MB-13. |
| F7 | Not implemented | Not implemented / Mandatory | Conforming | Y | Y | A,B: absent. MB-13. |
| F8 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| F9 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| F10 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| F11 | Not implemented | Not implemented / Deferred | Not implemented | - | - | Unchanged against both. |
| F12 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| F13 | Deviates | Deviates / Spec correction | Deviating | - | - | Unchanged against both. |
| F14 | Deviates | Deviates / Spec correction | Deviating | - | - | Unchanged against both. |
| F15 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| F16 | Not implemented | Not implemented / Deferred | Not implemented | - | - | Unchanged against both. |
| F17 | Not implemented | Not implemented / Deferred | Not implemented | - | - | Unchanged against both. |
| F18 | Deviates | Deviates / Mandatory | Conforming | Y | Y | A,B: r_det=1 and 3 shared a pair id. MB-09. |
| X1 | Unverifiable | Unverifiable / Phase 3 | Deferred to Phase 3 | Y | Y | A,B: unverifiable. Scheduled to Phase 3 evaluation. |
| X2 | Deviates | Deviates / Mandatory | Conforming | Y | Y | A,B: traceback on --out file. MB-14. |
| X3 | Conforms | Conforms / Conforms | Conforming | - | - | Unchanged against both. |
| X4 | Deviates | Deviates / Spec correction | Deviating | - | - | Unchanged against both. |
| X5 | Not implemented | Not implemented / Deferred | Not implemented | - | - | Unchanged against both. |
| X6 | Not implemented | Not implemented / Mandatory | Partially conforming | Y | Y | A: none. B: mandatory. MB-07 implemented the profile; two ratified limits keep it Partially. |

## 5. User decisions UD-1..UD-5 (status at HEAD)

| ID | Decision | Status | Code and test evidence |
|---|---|---|---|
| UD-1 | A-L1: a lossy or degenerate SAME is not evidence | **Ratified, implemented** | `decide.py:56-58`, `runner.py:326`, `harness.py:14,121`; `test_phase2_fixes.py::test_decide_lossy_same_is_not_evidence`, `test_lossy_s1_is_insufficient`, `test_lossy_input_does_not_activate_changed_units`. FS s6 text still says "non-degenerate" only (edit pending). |
| UD-2 | A-U1 + A-16: empty or vacuous changed region | **Open.** A-U1 rules are in code but not ratified; the recommended cap at S1 for `r_empty` (CB-01) is NOT implemented | `runner.py:153-165,344`; `test_phase2_fixes.py::test_docstring_only_is_vacuous_not_a_difference`, `test_non_executable_non_doc_change_is_unmodelled`. Effect: V10, S1c and S2a stay Partially conforming. |
| UD-3 | Observation boundary: fd-level and import-time output | **Option A for fd-level ratified, implemented**; import-time output stays in stdout as built (not separately ratified) | `runner.py:16,113-116` (switch `FOLD_FD1`), `harness.py:160,189-192`; `test_backlog_mb.py::test_mb02_os_write_differs`, `test_mb02_subprocess_output_differs`; `test_second_stage.py::test_buffered_real_stdout_difference_is_observed` |
| UD-4 | Conservative blocking by quarantined and NO_RUN inputs | **Option A ratified, implemented** | `decide.py:50-51`; `test_core.py::test_nondeterministic_quarantined`, `test_no_run_input_blocks_no_divergence`; `test_backlog_mb.py::test_mb10_both_limit_still_resource_limit` |
| UD-5 | K1 on existing development data | **Open; nothing implemented.** K1 is neither declared failed nor cleared; the pre-MB-01..16 numbers are not comparable | see `K1_K5_READINESS_AND_DECISION.md`; X1 is Deferred to Phase 3 |

## 6. MB-01..MB-16 (status and tests)

All 16 are committed in `5efcef74`; code and tests are unchanged at HEAD. "Done" means implemented, with named tests that exist, and recorded green in the 276/1 run. Mutation checks are from `scripts/mutation_check_mb.py` (16/16 killed, recorded).

| MB | Status | Code (HEAD) | Tests (tests/v7) | Residual |
|---|---|---|---|---|
| MB-01 | Done | `harness.py:31,78,226-229`; `baselines` `plain` | `test_backlog_mb.py::test_mb01_huge_ints_differ`, `test_mb01_equal_huge_ints_clean`, `test_mb01_canon_failure_is_tool_error_not_outcome`, `test_mb01_int_precision_and_type_differences_diverge`, `test_mb01_equal_ints_stay_same_and_non_lossy`, `test_mb01_default_digit_limit_is_the_trigger` | canon failure is `tool_error`, not `unobservable_outcome` (O6 Partially) |
| MB-02 | Done (known gap) | `runner.py:16,20-24,113-116`; `harness.py:160`; `compare.py:67` | `test_backlog_mb.py::test_mb02_os_write_differs`, `test_mb02_identical_os_write_is_not_divergent`, `test_mb02_subprocess_output_differs`, `test_mb02_no_fd1_output_leaves_observation_unchanged`; `test_second_stage.py::test_buffered_real_stdout_difference_is_observed`, `test_identical_buffered_real_stdout_is_not_divergent`, `test_closed_real_stdout_does_not_break_the_harness`, `test_print_then_os_exit_is_a_protocol_violation_not_an_observation` | program-created streams on fd 1 (`os.fdopen(1)`) with unflushed data are still lost; no blind-spot detector |
| MB-03 | Done | `harness.py:18-20`; `runner.py:20-24` | `test_backlog_mb.py::test_mb03_source_path_in_message_and_output_is_normalised`, `test_mb03_real_message_change_still_differs` | other absolute paths and default reprs not normalised |
| MB-04 | Done | `records.py:27-32,93-96`; `decide.py:62`; `verify.py:41-45` | `test_backlog_mb.py::test_mb04_invariants_hold_under_python_O`, `test_mb04_unknown_blocker_code_is_insufficient_tool_error`, `test_mb04_verify_names_unknown_code` | none |
| MB-05 | Done | `runner.py:195-202,221-223,246-247,256-257` | `test_backlog_mb.py::test_mb05_all_replays_tampered_gives_no_witness`, `test_mb05_alt_run_not_sandbox_ok_gives_sandbox_failure`, `test_mb05_replay_harness_error_is_tool_error`, `test_mb05_clean_replays_still_confirm` | tests drive scripted runs for replay/alt; the live path is covered only by end-to-end tests |
| MB-06 | Done under SD-07 | `isolation.py:279-280`; `runner.py:70,95` | `test_backlog_mb.py::test_mb06_required_property_unverified_is_sandbox_failure`, `test_mb06_advisory_unavailable_keeps_verdicts_and_flags_policy`, `test_mb06_policy_id_differs_between_capability_sets` | SD-07 not ratified; interpreter 3.13 is a flag, not a gate |
| MB-07 | Done; two ratified limits | `isolation.py:118,269-276`; `harness.py:179-186` | `test_backlog_mb.py::test_mb07_hash_seed_pinned_set_order_is_deterministic`, `test_mb07_pure_random_difference_is_not_a_witness`, `test_mb07_real_env_sensitive_case`, `test_mb07_alt_virtualises_urandom_uuid_and_monotonic`, `test_mb07_profile_is_part_of_policy_id`, `test_mb07_python_minor_version_flags_policy`; `test_second_stage.py::test_child_env_is_exactly_the_allowlist_and_path_is_clean`, `test_child_env_is_built_from_scratch_not_inherited`, `test_hostile_parent_env_does_not_change_verdict_or_ids`, `test_program_directory_cannot_shadow_trusted_modules`, `test_alt_virtualises_secrets_and_systemrandom`, `test_primary_runs_keep_real_entropy`, `test_datetime_now_is_NOT_virtualised_documented_limit` | `datetime.now` not virtualised (Decision B); hash seed not varied (Decision A); depends on private `random._urandom` (register R14) |
| MB-08 | Done | `runner.py:363-364`; `records.py:116` | `test_backlog_mb.py::test_mb08_identical_pair_leaves_nothing_and_is_stable`, `test_mb08_second_compare_into_same_dir_raises_instead_of_truncating` | single-file identity (SD-20) |
| MB-09 | Done | `runner.py:75,80`; `verify.py:64-65` | `test_backlog_mb.py::test_mb09_pair_id_covers_repeat_and_suff_not_budget`, `test_mb09_pair_id_covers_policy` | pair id depends on the policy record (R15) |
| MB-10 | Done under UD-4 A | `runner.py:205-209,227-231`; `decide.py:50-51` | `test_backlog_mb.py::test_mb10_protocol_violation_is_unsafe_program_without_spurious_resource_limit`, `test_mb10_canon_failure_primary_is_tool_error`, `test_mb10_both_limit_still_resource_limit` | policy is UD-4 A (conservative) |
| MB-11 | Done | `runner.py:82-86,271-273,321,372-384` | `test_backlog_mb.py::test_mb11_spent_includes_parent_cpu`, `test_mb11_budget_stops_between_runs_inside_an_input`, `test_mb11_last_input_exhausting_budget_with_unhit_units_is_budget_exhausted` | an in-flight run is not interrupted |
| MB-12 | Done | `records.py:101-106`; `runner.py:346-350` | `test_backlog_mb.py::test_mb12_merkle_root_properties`, `test_mb12_sufficiency_record_has_root_and_factors` | no leaf/node domain separation (R11) |
| MB-13 | Done | `config.py:35-38,50-51` | `test_backlog_mb.py::test_mb13_constants_accepted_and_equal_to_defaults`, `test_mb13_other_values_rejected_not_built` | reserved FS fields (SD-18) are still rejected as unknown keys |
| MB-14 | Done | `__main__.py:10-44` | `test_backlog_mb.py::test_mb14_out_is_a_file_exits_2_no_traceback`, `test_mb14_unwritable_out_exits_2`, `test_mb14_unexpected_exception_exits_1_one_line`, `test_mb14_help_exits_0` | `except Exception` hides internal tracebacks by design |
| MB-15 | Done | `runner.py:27-29,389`; `verify.py:70` | `test_backlog_mb.py::test_mb15_package_records_digest_and_verify_checks_it` | digest covers one V6 file only (R11); old packages without the field are accepted |
| MB-16 | Done (tests only) | none (tests) | `test_conformance_gaps.py::test_loud_not_skipped_sandbox_must_be_active_on_darwin`, `test_capture_truncated_end_to_end`, `test_alignment_failed_via_static_phase`, `test_systemexit_code_is_compared`, `test_stderr_only_difference_is_not_observed`, `test_witness_locus_unlocalised`, `test_defaults_table_item6`, `test_policy_below_minimum_true_on_darwin`, `test_s2_coverage_two_branches`, `test_s2_coverage_loop_for_iter`, `test_deleted_and_inserted_line_units`, `test_record_kinds_have_documented_evidence_class`, `test_trace_raises_chain_error_on_dangling_ref` | item 7 platform clause weakly verified (R10); item 4 test was vacuous at first and was fixed |

## 7. Code deviation register D-01..D-23 (status at HEAD)

| ID | Original severity | Status at HEAD | Evidence |
|---|---|---|---|
| D-01 | Blocking | Fixed (`8f11d3aa`); residual NF-01 fixed by MB-01 | `harness.py:94-126`; `test_harness_canon.py::test_contents_difference_is_divergent`, `test_equal_contents_of_all_supported_types_reach_s2`; MB-01 tests |
| D-02 | Blocking | Fixed for protocol forgery; same-address-space adversary remains (Phase 3, R3) | `isolation.py:49-67`, `harness.py:159-171`; `test_result_protocol.py::test_forged_or_broken_result_is_unsafe_program`, `test_protocol_violations`, `test_nonce_differs_per_run` |
| D-03 | Major | Fixed under SD-07 (required set gates); literal FS text (all properties) not met on macOS | `isolation.py:279-280`; `runner.py:70,95`; MB-06 tests |
| D-04 | Moderate | Fixed (MB-10: cause carried); conservative policy is UD-4 A | `runner.py:205-209`; `decide.py:50-51`; MB-10 tests |
| D-05 | Major | Fixed (`cc56e029`); UD-2 open | `runner.py:153-165`; `test_phase2_fixes.py::test_docstring_only_is_vacuous_not_a_difference`, `test_non_executable_non_doc_change_is_unmodelled` |
| D-06 | Major | Fixed (`cc56e029`) | `runner.py:232-234`; `test_phase2_fixes.py::test_symmetric_binding_failure_is_not_a_same` |
| D-07 | Moderate | Fixed (MB-01) | `harness.py:226-229`; `test_backlog_mb.py::test_mb01_canon_failure_is_tool_error_not_outcome` |
| D-08 | Moderate | Open; Deferred to Phase 3 (harness-limit MemoryError and sandbox denial are program outcomes) | `harness.py:224-225` |
| D-09 | Major | Fixed with residuals: no event stream, no separate record kinds, unkeyed chain (R6) | `runner.py:386-395`; `verify.py:32-98`; `test_phase2_fixes.py::test_package_holds_evidence_not_just_hashes` |
| D-10 | Moderate | Fixed (MB-09) | `runner.py:75,80`; MB-09 tests |
| D-11 | Moderate | Partially fixed (MB-13: constants accepted; reserved FS fields still rejected) | `config.py:35-38,47-57`; MB-13 tests |
| D-12 | Moderate | Fixed (MB-08) | `runner.py:363-364`; `records.py:116`; MB-08 tests |
| D-13 | Moderate | Fixed (MB-11); granularity is one run | `runner.py:82-86,271-273`; MB-11 tests |
| D-14 | Moderate | Partially fixed (MB-07); `datetime.now` and hash seed excluded by Decisions B and A (R1, R2) | `isolation.py:269-276`; `harness.py:179-186`; MB-07 tests |
| D-15 | Minor | Open (documented spec choice SD-11; as-built `exited(code)`) | `harness.py:222-223`; `test_conformance_gaps.py::test_systemexit_code_is_compared` |
| D-16 | Moderate | Fixed for the known fd-1 gap (MB-02); `decide.py:72` flag is still a constant, no detector | `runner.py:113-116`; MB-02 tests |
| D-17 | Minor | Open (optional; default 0) | `compare.py:21-22` |
| D-18 | Minor | Fixed (MB-04) | `records.py:27-32` |
| D-19 | Moderate | Fixed for the source path (MB-03); normaliser narrower than the spec list | `harness.py:18-20`; MB-03 tests |
| D-20 | Minor | Open (cost; secondary ordering SD-12) | `runner.py:242-251`; `records.py:98` |
| D-21 | Moderate | Fixed (`cc56e029`); chain stays unkeyed (R6) | `verify.py:35-57`; `test_phase2_fixes.py::test_verify_detects_plain_edit_and_truncation` |
| D-22 | Minor | Partially fixed: `r_empty` exposed; stop reasons `inputs_exhausted` and `budget_mid_input` are outside the SPEC enum | `runner.py:344,350,398` |
| D-23 | Minor | Partially fixed (MB-15 digest of one V6 file, R11) | `runner.py:27-29,389`; `verify.py:70`; `test_backlog_mb.py::test_mb15_package_records_digest_and_verify_checks_it` |

Counts: Fixed 11 (D-01, D-02 for protocol forgery, D-04, D-05, D-06, D-07, D-10, D-12, D-13, D-18, D-21); Fixed with a named residual 4 (D-03, D-09, D-16, D-19); Partially fixed 4 (D-11, D-14, D-22, D-23); Open 3 (D-15, D-17, D-20); Deferred to Phase 3 1 (D-08). 11 + 4 + 4 + 3 + 1 = 23.

## 8. Specification ambiguities A-01..A-18 (status at HEAD)

The frozen spec was not edited. "Implemented" means the code follows the recommended clarification; "ratified" means a user instruction ratified it.

| ID | Status | Basis |
|---|---|---|
| A-01 | Implemented per SD-07 (MB-06), not ratified | `isolation.py:279-280` |
| A-02 | Resolved by ratified UD-4 A (spec text pending) | `decide.py:50-51` |
| A-03 | Implemented per SD-08, tied to open UD-2 | `runner.py:153-165` |
| A-04 | Resolved by ratified UD-4 A ("may have hit" = always) | `decide.py:50` |
| A-05 | Implemented per SD-08 (L0 + hit-line set), not ratified | `config.py:51`; `runner.py:128-129` |
| A-06 | Implemented per SD-12 (s5 wins), not ratified | `runner.py:302` |
| A-07 | Implemented per SD-12 (alphabetical tie-break), not ratified | `decide.py:85` |
| A-08 | Implemented per SD-11, not ratified | `harness.py:222-223` |
| A-09 | Implemented (MB-07); limits ratified as Decisions A and B | `isolation.py:269-276` |
| A-10 | Documentation-only (SD-14), not ratified; no per-run event chain exists | `records.py:113-135` |
| A-11 | Implemented per SD-13 (MB-14), not ratified | `__main__.py:10-44` |
| A-12 | Implemented per SD-16 (S3 refused), not ratified | `config.py:41-43` |
| A-13 | Implemented per SD-12 (3 runs per side in total), not ratified | `runner.py:274-279` |
| A-14 | Implemented per SD-10 (MB-05), not ratified | `runner.py:195-202,246-247,256-257` |
| A-15 | Implemented per SD-15 (code), FS text pending | `harness.py:94-126` |
| A-16 | **Open** (UD-2): vacuous coverage still satisfies the floor | `runner.py:335` |
| A-17 | Implemented per SD-19 (MB-11), not ratified | `runner.py:372-384` |
| A-18 | Implemented per SD-12 (QUARANTINED first), not ratified | `runner.py:225-226` |

Counts: resolved by a ratified decision 2 (A-02, A-04); implemented per a recommended but unratified clarification 15 (all others except A-16; A-09's two limits are separately ratified); open 1 (A-16). 2 + 15 + 1 = 18.

## 9. Open items OI-01..OI-22 (status at HEAD)

| ID | Status | Basis |
|---|---|---|
| OI-01 | Partially: known fd-1 gap closed (MB-02); `decide.py:72` still a constant | MB-02 tests |
| OI-02 | Open (specification only): F4 has no floor; S2 reachable from two inputs | `decide.py:65-74` |
| OI-03 | Not implemented (deferred, E8) | none |
| OI-04 | Done (MB-12); no domain separation (R11) | `records.py:101-106` |
| OI-05 | Not implemented (deferred, V8/W3) | none |
| OI-06 | Partially: `unsafe_program` and `unmodelled_change` produced; `blind_spot_dominant` and `ambiguous_entry` never produced; ChangedRegions folded into the package | `runner.py:299,311` |
| OI-07 | Done for the three constants (MB-13); reserved FS fields still rejected | `config.py:50-51` |
| OI-08 | Partially: identity checked before side effects (MB-08); single-file scope | `runner.py:363-364` |
| OI-09 | Done (MB-10) | `runner.py:205-209` |
| OI-10 | Resolved by ratified UD-4 A (code unchanged) | `decide.py:50` |
| OI-11 | Deferred (stratified reporting is evaluation-side; `r_empty` exposed at `runner.py:398`) | none |
| OI-12 | Partially (MB-07; R1, R2) | `harness.py:179-186` |
| OI-13 | Not implemented (deferred, P4) | none |
| OI-14 | Deferred to Phase 3 (SD-07 split done locally) | `isolation.py:279-280` |
| OI-15 | Not implemented (optional) | none |
| OI-16 | Done (MB-11) | `runner.py:372-384` |
| OI-17 | Open (documentation/spec; multi-branch tests exist) | `runner.py:331-335` |
| OI-18 | Partially (L0 constant and hit-line set; no tier field) | `config.py:51` |
| OI-19 | Open outside this task's files: reports quoting 74/75/85/91 are stale. Current recorded count: 276 passed, 1 skipped (277 tests) at `5efcef74`, unchanged at HEAD | `MB_SECOND_STAGE_REVIEW.md` s9 |
| OI-20 | Partially: protocol tamper fixed, fd-1 bypass closed; adversarial residual is Phase 3 (R3) | MB-02, `test_result_protocol.py` |
| OI-21 | Open (UD-5) | none |
| OI-22 | Done | `records.py:12,35-48`; `test_conformance_gaps.py::test_record_kinds_have_documented_evidence_class` |

Counts: Done 5 (OI-04, 07, 09, 16, 22); resolved by a ratified decision 1 (OI-10); Partially 6 (OI-01, 06, 08, 12, 18, 20); Open 4 (OI-02, 17, 19, 21); Not implemented 4 (OI-03, 05, 13, 15); Deferred 1 (OI-11, evaluation-side); Deferred to Phase 3 1 (OI-14). 5 + 1 + 6 + 4 + 4 + 1 + 1 = 22.

## 10. Risks

The single current risk register is `docs/architecture/V7B_RISK_REGISTER.md` (it supersedes section 6 of `MB_SECOND_STAGE_REVIEW.md`; IDs R1..R13 are kept so that review stays traceable). The risks that this task had to document, with the register entry:

| Topic | Register ID | Status |
|---|---|---|
| R3 harness shares the process with the program (D-02 is result-channel protocol correctness only) | R3 | open, Phase 3 |
| R4 `-I` dropped; flags visible; no kernel/loader hardening | R4 | accepted |
| R6 plaintext, unkeyed hash chain forgeable by its writer (evidence trust-anchor limitation) | R6 | open, Phase 3 |
| R11 Merkle root without leaf/node domain separation; `v6_digest` hashes one file | R11 | open, low |
| R12 macOS-only, deprecated sandbox-exec; no Linux/Docker; no validated OS-level isolation | R12 | open, Phase 3 |
| R13 `-X` options, `sys.orig_argv`, `__CF_USER_TEXT_ENCODING` visible to the program | R13 | accepted |
| Dependency on private `random._urandom` (CPython 3.13 specific, `harness.py:186`) | R14 | new, open |
| Merkle leaf/node domain separation | R11 | open, low |
| Pair id depends on the policy record (`runner.py:80`) | R15 | new, accepted |
| `datetime.now()/today()` not virtualised (Decision B) | R2 | ratified limitation |
| `PYTHONHASHSEED` fixed, hash-order sensitivity untested (Decision A) | R1 | ratified limitation |
| Platform and Python-version limits (macOS, CPython 3.13, `sys.monitoring`) | R16 | new, open |
| Result channel is protocol correctness only | R3 | open, Phase 3 |

## 11. Classification notes and what was not checked

- Every one of the 135 rules received a status; none was left unclassified.
- Twelve classifications are judgement calls that depend on how a clause is read; each is stated in its row: B3a (literal FS sentence versus SD-07), B5, S1g and B6 (valid only under ratified UD-4 A), O6 (reason code `tool_error` versus the spec's `unobservable_outcome`), S3 (default present, mechanism absent), I5 (Linux clause), G5s (vacuous), B2a (defensive, tested only through a monkeypatch), V11 and M3 (code correct, no test), S2a (vacuous coverage). A different reading would move at most these 12 rows (Conforming/Partially/Deviating).
- Not re-run: any test, mutation check or probe (machine reserved). Not checked: Linux behaviour, third-party code, the legacy V5/V6 documents, `experiments/` and `scripts/` beyond the existence of `scripts/mutation_check_mb.py`, and whether the recorded 276/1 still reproduces today on this machine. The next full run should confirm it.
- Prior documents that still quote older counts (the audit's 63/45/23/4, the earlier matrix's 68/23/17/15/7/5, and test counts 74/75/85/91/168) are outside this task's ownership and are not edited.
