# Agent 7 — COBOL cross-language feasibility (assessment only)

Repo HEAD `93ef3f3`, branch `remediation/sbg-v4` (checked with `git rev-parse --short HEAD` and `git branch --show-current`, read-only).
Date of runs: 2026-11-04 (per `cobc` listing timestamps). No repo file was modified. `cobol_inventory.py` was **read, not executed**.
All toy programs and binaries are under `agent_7/scratch/`. **No COBOL AUROC, score or label was produced, and none is reported.**

> **One-line verdict.** A GnuCOBOL tracer is technically obtainable (paragraph and statement events, coverage and per-item value-change hooks all work here), but a *valid* cross-language evaluation needs a new corpus, a new state abstraction, a new oracle and a new transformation/mutation engine. Realistic cost is about 3 person-weeks. **Defer it; do not put it in the present study.** The toy runs below prove that tracing is possible, not that SBG works on COBOL.

---

## 1. Existing COBOL code and artifacts in the repo

### 1.1 Where COBOL appears (`grep -ril cobol`, 16 files)

Primary evidence files:
- [`experiments/final/cobol_inventory.py`](../../../experiments/final/cobol_inventory.py:1)
- `artifacts/paper_evidence/COBOL_CORPUS_INVENTORY.{json,md}`
- `artifacts/paper_evidence/COBOL_EVALUATION_REPORT.md`

The other 13 hits are documentation that repeats the same conclusion: `README.md:39-40`, `docs/current/REPRODUCTION.md:124,127`, `FINAL_SPRINT_REPORT.md:83-92`, `CLAIM_TO_EVIDENCE_MATRIX.md:26,41,43`, `FINAL_MANUSCRIPT_BLUEPRINT.md:35,71,109`, `FINAL_NOVELTY_POSITION.md:93`, `REPRESENTATION_CASE_STUDIES.md:236`, `PRACTICAL_SIGNIFICANCE_ASSESSMENT.md:109`, `MANUSCRIPT_CLAIMS_CHECKLIST.md:214`, `FINAL_PROJECT_HANDOFF.md:78`.

The forensic audit (`SBG_CURRENT_STATE_FORENSIC_AUDIT_2026-11-04.md:510-512`, §H.3) says: "COBOL: 0 executable programs. All 85 `.cbl` files are Db2 precompiler snippets. No AUROC exists. **Must not be cited as evidence of generality.**" Its other COBOL mentions are at lines 96, 616, 720, 728 and 762.

### 1.2 What `cobol_inventory.py` does (read-only, never executed by me)

- It walks `/Users/manassakthivel/Desktop/COBOLSRC` (default `--root`, line 69).
- For each `.cbl` file it records sha256, size, line count, program-id, a verb census (`PROC_VERBS`, lines 28-29) and the `EXEC SQL` block count (lines 83-97).
- It runs `cobc -fsyntax-only -free/-fixed` on the file as-is (line 94).
- It runs the same check again after a mechanical stub that turns `EXEC SQL … END-EXEC` into `CONTINUE` (lines 43-54, 95-97). The docstring (lines 9-12, 46) says this stub is a syntax probe only and "never used for labels".
- It runs in `tempfile` scratch directories and writes only `artifacts/paper_evidence/COBOL_CORPUS_INVENTORY.json` (lines 27, 124). No program is executed (line 13).

### 1.3 Finding confirmed: 85 `.cbl` Db2 embedded-SQL snippets

Repo claims, from [`COBOL_CORPUS_INVENTORY.json` `summary`](../../../artifacts/paper_evidence/COBOL_CORPUS_INVENTORY.json:3):
- `n_files` is 95.
- `n_cbl` is 85, of which 84 are unique by SHA-256 (`COBBACK/cosql31.cbl` duplicates `cobol/cosql31.cbl`).
- `n_cpy` is 10.
- `n_cbl_with_exec_sql` is 85.
- `n_cbl_with_any_non_sql_procedure_verb` is 20.
- `cobc_as_is_syntax_ok_free` and `_fixed` are both 0.
- `cobc_after_stub_syntax_ok_fixed` is 72.
- `n_test_or_fixture_files` is 0.
- The verb totals are MOVE 27, IF 4, PERFORM 4, DISPLAY 41, EVALUATE 22, CLOSE 2.
- Prose version: `COBOL_CORPUS_INVENTORY.md:12-38`; verdict: `COBOL_EVALUATION_REPORT.md:3-22`.

I confirmed these against the live corpus with read-only listing and `grep`:

| Check (corpus at `~/Desktop/COBOLSRC`) | Observed |
|---|---|
| `COBBACK/` / `cobol/` / `cpy/` / `cpyback/` file counts | 84 / 1 / 0 / 10 |
| `*.cbl` total, `*.cpy` total | 85, 10 |
| `.cbl` files lacking `EXEC SQL` (`grep -L`) | **0** |
| `.cbl` files with a `CBL SQL,LIB` first-line directive | **85** |
| Header of `cosql28.cbl` | `CBL  SQL,LIB`, `Program-ID. "bigint"` |

The corpus path in the repo is the same as the one I listed. The `cobol/` directory still holds 1 file. Its mtime is 4 Nov 17:25, after the 28 Oct dates of the other directories, but the count is unchanged versus `COBOL_CORPUS_INVENTORY.md:12`.

I re-derived nothing from the corpus beyond those counts and did not run the script. If someone wants byte-level confirmation they can compare the sha256 values in the JSON.

### 1.4 Other local COBOL sources (listing and counts only; no content read)

`find` by extension (`.cbl .cob .cobol .cpy`, case-insensitive) under `~/Desktop`:

| Location | `.cbl` | `.cpy` | `.cob`/`.cobol` | Contains `EXEC SQL`/`EXEC CICS` (`grep -rli` on `*.cbl`) |
|---|---|---|---|---|
| `COBOLSRC` (the audited corpus) | 85 | 10 | 0 | 85 (all) |
| `workspace` | 152 | 238 | 0 | 98 of 152 |
| `workspace-IBM` | 1724 | 214 | 0 | 379 of 1724 |
| `GM` (top-level; same tree is duplicated inside `workspace`, `workspace/GM 2`, and `workspace-IBM/SHIFT LEFT/GM`) | 76 | 119 | 0 | 49 of 76 |
| `Assembler optimized` (`AD_Projects`, `ATLAS_ASM`, `Scanner_Legacy`) | 8 | 0 | 0 | not checked |
| `AD-ANALYZE` | 0 | 0 | 0 | – |
| `Banker` | 0 | 1 | 0 | – |

- Distinct contents (sha256 of all `.cbl`/`.cpy` under `workspace`, `workspace-IBM`, `GM`, `Banker`, `Assembler optimized`): **1843 unique**. There is heavy duplication across the nested copies.
- Directory names (`GM/zOS Cobol`, `GM/Cobol Include`, `SHIFT LEFT`, `REGRESSION_TEST_DATA`) suggest **client or employer mainframe code**. I did not read any of it.
- **Provenance and licence are unknown and probably proprietary.** Do not use it in a public paper without explicit permission.
- Even if permitted, `EXEC SQL`/`EXEC CICS` appear in roughly one third to one half of the programs. Those need Db2 or CICS and are not runnable under GnuCOBOL.
- No test oracles are known for this code. The `REGRESSION_TEST_DATA` directory might contain some, but I did not inspect it.

---

## 2. Local environment

### 2.1 Tooling (commands in appendix A)

| Item | Result |
|---|---|
| `/opt/homebrew/bin/cobc` | symlink → `../Cellar/gnucobol/3.2_1/bin/cobc` |
| `cobc --version` | `cobc (GnuCOBOL) 3.2.0`, built Jul 28 2023, C compiler `Apple LLVM 21.0.0` |
| `cobcrun --version` | `cobcrun (GnuCOBOL) 3.2.0` (runtime present) |
| libcob | `/opt/homebrew/lib/libcob.dylib` and `.4.dylib`, `libcob.a`, header `libcob.h` (installed) |
| `cob-config` | present |
| Homebrew | `gnucobol 3.2_1`, `License: GPL-3.0-or-later` (`brew info`) |
| Platform | macOS 26.6.2, arm64; `native EBCDIC: no`, `little-endian`, `64bit-mode: yes` (`cobc --info`) |
| Absent (expected) | `cobol` (Micro Focus), `mfcobol`, `cobrun`, `ilcobol`; no IBM Enterprise COBOL, no Db2 precompiler |
| Java / Maven | `openjdk 21.0.12.1`; `javac` present; `mvn` **not found** (relevant to ProLeap, §5) |
| `gcov` | `/usr/bin/gcov` is **Apple LLVM** gcov, not GNU gcov (see §3.4) |

### 2.2 Licence facts (verified)

- **Installed locally.** `COPYING` and `COPYING.LESSER` ship in `/opt/homebrew/Cellar/gnucobol/3.2_1/`. The `sbom.spdx.json` reports `licenseConcluded: GPL-3.0-or-later`. `libcob.h` states "The GnuCOBOL runtime library is free software… GNU Lesser General Public License… version 3 or any later version."
- **Upstream `README`** (<https://raw.githubusercontent.com/OCamlPro/gnucobol/gnucobol-3.x/README>, fetched): "All programs except those in lib and libcob are distributed under the GNU General Public License… Programs in lib and libcob are distributed under the GNU Lesser General Public License."
- **Project page** (<https://gnucobol.sourceforge.io/>, fetched): "GnuCOBOL 3.2 … Released 28 July 2023"; "19 COBOL dialects"; "Over 9740 NIST COBOL 85 test suite tests passed, over 37000 tests in nearly 1300 internal test groups".
- Summary: compiler **GPL-3.0-or-later**, runtime **LGPL-3.0-or-later**. I make no legal claim about the licence of generated binaries.

### 2.3 Can an executable COBOL program be compiled and run here? **Yes**

Toy program `scratch/toy.cob` (COMPUTE inside a `PERFORM VARYING` loop, DISPLAY, `ON SIZE ERROR`, `CALL … ON EXCEPTION`, an OCCURS table, `RETURN-CODE`):

```cobol
       PROCEDURE DIVISION.
       MAIN-PARA.
           PERFORM LOOP-PARA VARYING WS-I FROM 1 BY 1 UNTIL WS-I > 5
           DISPLAY "SUM=" WS-SUM
           PERFORM OVF-PARA
           CALL "NOSUCHPROG"
               ON EXCEPTION DISPLAY "CALL-EXC"
           END-CALL
           MOVE "ABC" TO WS-NAME
           ...
           MOVE 3 TO RETURN-CODE
           STOP RUN.
       LOOP-PARA.
           COMPUTE WS-SUM = WS-SUM + WS-I * 2.
       OVF-PARA.
           COMPUTE WS-SMALL = WS-SUM * 5
               ON SIZE ERROR DISPLAY "SIZE-ERR"
               NOT ON SIZE ERROR DISPLAY "NO-SIZE-ERR"
           END-COMPUTE.
```

Run: `cobc -x -o toy_plain toy.cob && ./toy_plain; echo rc=$?` gives exactly:

```
SUM=030
SIZE-ERR
CALL-EXC
NAME=[ABC   ]
TAB=000700
rc=3
```

- `SUM=030` is 2×(1+2+3+4+5).
- `WS-SUM*5 = 150` does not fit `PIC 9(2)`, so SIZE-ERR fired.
- The missing `NOSUCHPROG` fired `ON EXCEPTION`.
- `RETURN-CODE` 3 became the process exit status.
- stdout and rc are deterministic: 3 repeated runs gave an identical SHA-256 prefix (`d276a28e1fed7930`).

One probe run before the final edit (multiplier `*2`, no overflow) printed `NO-SIZE-ERR`. The `*5` edit that follows was deliberate, to exercise the SIZE ERROR branch.

---

## 3. Instrumentation and trace extraction options (all run in this version)

`cobc --help` (3.2.0) lists the flags used below: `-d/--debug`, `-ftrace`, `-ftraceall`, `-fsource-location`, `-fstack-extended`, `-fdump=<scope>`, `-fstack-check`, `-fdebugging-mode=`, `-C`, `-A`, `--coverage`, `-g`, `--save-temps`, `-t`.

### 3.1 Paragraph/section tracing: `-ftrace` + `COB_SET_TRACE`

- `-ftrace` alone does **nothing** at run time. My first run printed no trace.
- The trace is enabled by environment (`runtime.cfg:112-117`): `COB_SET_TRACE=Y`. Destination and format are `COB_TRACE_FILE` (default stderr) and `COB_TRACE_FORMAT` (default `"%P %S Line: %L"`; `%P` program, `%I` id, `%L` line, `%S` statement type and name, `%F` source file).
- Scope per `cobc --help`: `-ftrace` = "executed SECTION/PARAGRAPH"; `-ftraceall` = "executed SECTION/PARAGRAPH/STATEMENTS".

Sample (`COB_SET_TRACE=Y ./toy_trace`, toy program, stderr):

```
Source: 'toy.cob'
Program-Id:  TOY
Program-Id:  TOY                  Entry: TOY                             Line:     12
Program-Id:  TOY              Paragraph: MAIN-PARA                       Line:     12
Program-Id:  TOY              Paragraph: LOOP-PARA                       Line:     25
  … (×5 LOOP-PARA)
Program-Id:  TOY              Paragraph: OVF-PARA                        Line:     27
```

### 3.2 Statement-level tracing: `-ftraceall`

`COB_SET_TRACE=Y COB_TRACE_FILE=./traceall.txt ./toy_traceall` produced 39 lines (full file: `scratch/traceall.txt`). Excerpt:

```
Paragraph: MAIN-PARA                    Line: 12
           PERFORM                      Line: 13
           UNTIL                        Line: 13
Paragraph: LOOP-PARA                    Line: 25
           COMPUTE                      Line: 26
           VARYING                      Line: 26
           UNTIL                        Line: 13
   … (×5)
           DISPLAY                      Line: 14
           PERFORM                      Line: 15
Paragraph: OVF-PARA                     Line: 27
           COMPUTE                      Line: 28
           DISPLAY                      Line: 29       <- the ON SIZE ERROR branch
           CALL                         Line: 16
           DISPLAY                      Line: 17       <- the ON EXCEPTION branch
           MOVE …                       Line: 19-23
           STOP RUN                     Line: 24
```

What this gives, and what it does not:

| Event type | Obtainable? | How |
|---|---|---|
| Paragraph/section entry (PERFORM or fall-through) | **Yes** | `Paragraph: NAME Line: n` |
| `PERFORM` statement, loop `UNTIL`/`VARYING` | **Yes** (`-ftraceall`) | statement events |
| Paragraph **return** / PERFORM exit | **No direct event** | no "exit" line exists in the trace. It is visible only in the generated C as "Implicit PERFORM return" (`toy.c`, lines ~160-182). Call depth and return events must be reconstructed from the static PERFORM structure or from C-level hooks. |
| `CALL` | **Yes** | `CALL` statement line; callee entry shows as `Entry:` for a COBOL callee (the toy's callee did not exist) |
| `ON EXCEPTION` / `ON SIZE ERROR` | **Inferred only** | there is no "exception occurred" event. The branch taken is inferred from the next statement's line number (L29 vs L30; L17). |
| Runtime error (bad subscript, non-numeric data) | **Yes, as program abort** | with `-debug` the program aborts, `libcob: crash.cob:12: error: 'WS-E' … not numeric`, rc=1. It cannot be caught as an exception. |
| File status errors | **Observable** | `OPEN` of a missing file set `FS=35`; execution continued; `-ftraceall` shows `OPEN L16`, `DISPLAY L17`. |
| GO TO | **Yes** | `gt.cob`: `Paragraph: P1` repeated 3×, then `P2`. |
| Working-storage values at an event | **Not from the trace itself** | see 3.3 |

### 3.3 Working-storage value snapshots (three partial routes)

1. **`USE FOR DEBUGGING` + `DEBUGGING MODE`** (`scratch/dbg.cob`, compiled with `-fdebugging-mode=ok`, run with `COB_SET_DEBUG=Y`) gives a callback on every change of named items, with `DEBUG-NAME`, `DEBUG-LINE`, `DEBUG-CONTENTS`:

   ```
   DBG name=WS-I   line=    19 contents=[01 …] WS-SUM=000
   DBG name=WS-SUM line=    20 contents=[002 …] WS-SUM=002
   DBG name=WS-I   line=    20 contents=[02 …] WS-SUM=002
   ```
   This is real per-update value data for chosen items. **Caveats**: you must edit the source (add DECLARATIVES and the SOURCE-COMPUTER clause), which changes the artefact under study; `COB_SET_DEBUG` must be set at runtime; `DEBUG-CONTENTS` is the raw field image; the same assignment can emit duplicate callbacks (WS-I appears twice per iteration); I did not test the DEBUGGING facility on `OCCURS`/group items.

2. **`-fdump=<scope>` / `-debug`** prints WORKING-STORAGE **only on abort** (verified with `crash.cob`: dump of RETURN-CODE, `WS-T`, `WS-E (1)…`, `WS-I`, `WS-N`). It gives a final-state snapshot, not a time series.

3. **C-level instrumentation.** `cobc -C -o toy.c toy.cob` emits 358 lines of readable C with `/* Line: n : STMT */` markers and the storage as `b_NN` byte buffers and `f_NN` field descriptors (`toy.c`). Tracing every statement and dumping `b_NN` would work but is **not tested here**: it is a custom pipeline (patch the generated C, link with `libcob`).

I did not test `-A` pass-through instrumentation, gdb scripting, or any libcob hook for per-statement field snapshots. Those remain unverified options.

### 3.4 Coverage

`cobc -x --coverage -o toy_cov toy.cob` builds and runs; a `.gcda`/`.gcno` pair is written. Apple's `gcov toy.gcda` creates `toy.cob.gcov`, which maps cleanly to COBOL source lines, e.g. `5: 25: LOOP-PARA`, `5: 26: COMPUTE`, `#####: 30: NOT ON SIZE ERROR …`. Line coverage of a COBOL file is therefore cheaply available (an analogue of `coverage_size`). `gcov` also reported `cob####_0.c: No such file` for the temporary C file (cosmetic).

### 3.5 Verdict on §3

Paragraph entries, statement order, branch taken, GO TO and coverage are directly obtainable. Return/depth events are not (reconstruct). Exception events are only inferable. Value snapshots need source edits (`USE FOR DEBUGGING`) or custom C instrumentation. **This is a prototype, not a validated tracer.**

---

## 4. Do V3, temporal and state components have COBOL equivalents?

Repo anchors for what SBG consumes:
- Python tracer: [`sbg/extraction/dynamic/tracer.py:38-45`](../../../sbg/extraction/dynamic/tracer.py:38) defines `TraceEvent{event_type ∈ call/return/exception/line, function_name, lineno, local_vars_snapshot (repr, ≤100 chars)}`. The callback at `:336-386` snapshots `frame.f_locals`, and `HARNESS_CODE` frames are skipped (`:357`).
- V3 genome fields: [`sbg/v3/genome.py:106-123`](../../../sbg/v3/genome.py:106) (`coverage_size`, `anon_call_freq`, `hot_path_hash`, `exception_type_set`, `exception_rate`, `call_depth_mean/max`, `call_transition_bigrams`, `exception_causality_hash`, …).
- Combination: [`experiments/final/extraction.py:483`](../../../experiments/final/extraction.py:483) `W_V3, W_TEMPORAL, W_STATE = 0.50, 0.25, 0.25`; `:524` blends them (falls back to V3 alone if temporal/state unavailable).
- State abstraction: [`sbg/v6/state_transition_genome_v6.py:56-72`](../../../sbg/v6/state_transition_genome_v6.py:56) (ZERO/POSITIVE/NEGATIVE/NULL/…/EXCEPTION_STATE), `:131-182` (`_repr_to_abstract` parses **Python reprs**); event kinds at `:81-88` (state_creation, state_deletion, resource_acquire/release, error_transition, …).

| SBG concept | COBOL analogue | Comparable? |
|---|---|---|
| Function = unit of call graph | **Paragraph/section** (or nested/called PROGRAM). Index by first-call order as in `genome.py` | Yes, with a design decision. Paragraphs are not scoped (no locals, no arguments, shared global WS). |
| Call graph / call-order bigrams | PERFORM graph; `PERFORM A THRU B` ranges; fall-through between paragraphs counts as a transition without a PERFORM | **Partial.** Fall-through and `THRU` have no Python analogue. `-Wsuspicious-perform-thru` exists in cobc. |
| Call depth, return events | PERFORM nesting depth | **Not from `-ftrace`** (no exit event). Must be reconstructed. |
| Exceptions (`exception_type_set`, `exception_rate`, `exception_causality_hash`) | `ON SIZE ERROR`, `ON EXCEPTION` (CALL), `AT END`, `INVALID KEY`, FILE STATUS, `RETURN-CODE`, runtime abort/ABEND | **Structurally different.** COBOL errors are inline control flow or terminations, not typed exceptions that propagate. The "type" set would have to be invented (e.g. size-error / call-exception / file-status code). Under GnuCOBOL a runtime check failure kills the process (rc=1); on z/OS it would be an abend with a different code. |
| Coverage | line or paragraph coverage via `--coverage` | Yes. |
| Return value | `RETURN-CODE` + stdout | Yes (used as oracle, §6). |
| Local-variable snapshot | all of WORKING-STORAGE (global, static) | **Different semantics.** Python frames expose only live locals; COBOL WS is the whole program state at every event. |
| `state_creation` / `state_deletion` / scope lifetime | none (static storage; `LOCAL-STORAGE` only in subprograms) | **Mostly vacuous.** Only `mutation`/`data_flow`-like events remain. File `OPEN`/`CLOSE` ≈ resource acquire/release. |
| Abstract value: numeric sign/zero | `PIC 9(n)` DISPLAY (unsigned, zoned), `PIC S9`, `COMP`, `COMP-3` | **Requires a new parser** for field images; unsigned fields are never NEGATIVE; `V` implies a scale; a `PIC 9(3)` of "030" is not the Python int 30 unless decoded. |
| Abstract value: string/length | `PIC X(n)` fixed length | `STR_LEN` is **constant** (always n). Use trimmed length or blank-vs-non-blank instead; this is a different abstraction. |
| Abstract value: collections | `OCCURS n` table, `OCCURS DEPENDING ON` | Fixed-size by definition; `COL_LEN` carries no information except through ODO. |
| Static typing | all types fixed at compile time | The Python value domain's "type-varying" behaviour is absent. |
| Recursion | Not standard for PERFORM; observed **allowed** in GnuCOBOL 3.2 (`rec.cob`, `-debug`: `PERFORM A-PARA` recursed 3 deep, printed `A done N=3` three times, rc=0). I did not verify IBM Enterprise COBOL behaviour. | Differs from Python's "recursion is normal" assumption; treat recursion as out of scope. |
| `GO TO` | unconditional branch; `trace` shows it as a repeated `Paragraph` entry | No Python analogue (V3 would see a loop of paragraph entries). |
| Fixed-point decimals | `PIC 9V99`, `COMPUTE` rounding/truncation | Python floats vs COBOL decimals: abstraction `POSF=<round(v,2)>` has no analogue. |

### 4.1 Dialect and platform differences that make GnuCOBOL non-comparable with IBM Enterprise COBOL

Observed locally (scratch programs, `-std=ibm` vs default):

| Probe | Default | `-std=ibm` | Source |
|---|---|---|---|
| `DISPLAY` of `PIC 9V99` = 10/3 | `R=3.33` | `R=333` (decimal point suppressed) | `scratch/packed.cob` |
| `DISPLAY` of `COMP-3 S9(5)V99` -123.45 | `P=-00123.45` | `P=-0012345` | same |
| `DISPLAY` of signed zoned -123.45 | `D=-00123.45` | `D=0012345-` | same |
| `MOVE 70000 TO PIC S9(4) COMP` | `A=+0000` (binary truncation on) | `A=+04464` (no truncation) | `scratch/ibmonly.cob`; `-std=mf` gave `+4464`, `-fno-trunc` gave `+04464` |
| `IF "a" < "A"` | `a>A (ASCII order)`; `"1" < "A"` true | with `-fdefault-colseq=EBCDIC`: `a<A`, `1>A` | `scratch/col.cob` |
| IBM `CBL TRUNC(BIN),ARITH(EXTEND)` compiler-option card | **ignored with a warning**: `ignoring unknown directive` | same | `scratch/ibmonly.cob` |
| Bytes of signed zoned `-0012345` | `HEX-OF = 30303132333475` (sign in last digit nibble `7`/`u`) | same | `packed.cob` |
| Packed decimal `-123.45` | `0012345D` (sign nibble D) | same | `packed.cob` |

Dialect configs exist for `ibm`, `ibm-strict`, `mvs`, `mf`, `acu`, `bs2000`, `rm` etc. under `…/share/gnucobol/config/`. `cobc -info` shows `native EBCDIC: no`. Storage is ASCII bytes even when only the collating sequence is set to EBCDIC, so any byte-level or hex comparison with z/OS output is **not** reproducible here. This matters only if the study claims to represent IBM-style COBOL; for a self-consistent GnuCOBOL benchmark the issue is limited to the label "COBOL" in the paper.

### 4.2 What cannot be made comparable

1. **Exception semantics** (no typed propagation; abends vs abort; GnuCOBOL has no ABEND codes).
2. **Call-depth and return events** (not emitted by the runtime tracer).
3. **Value domain** (fixed-width fields; unsigned numerics; implied decimals; fixed-length strings). The state component would be a **new instrument**, not the existing one.
4. **Creation/deletion/scope lifetime events** (static storage).
5. **Z/OS-specific behaviour** (EBCDIC, Db2/CICS, JCL, VSAM, ABEND). Not reproducible with `cobc` here.
6. **Comparing AUROC across languages** — different label definitions, program sizes and base rates make the numbers incomparable even if everything else worked.

---

## 5. Proposed small controlled benchmark

### 5.1 Candidate sources (existence and licence verified as stated; content mostly NOT inspected)

| Source | What I verified | Licence / provenance finding | Fit |
|---|---|---|---|
| **GnuCOBOL internal testsuite**, `tests/testsuite.src/*.at` in <https://github.com/OCamlPro/gnucobol> (branch `gnucobol-3.x`) | GitHub API listing shows ~40 autotest `.at` files (e.g. `run_fundamental.at` 405 KB, `run_misc.at` 545 KB, `run_functions.at` 143 KB) plus `tutorial.cob` and `numeric-display.cob`. Project page states >37000 tests in ~1300 groups. | GPL (repo `README`). Programs and **expected output are embedded in the `.at` files**, so each snippet carries an oracle. | Most oracles of any candidate, but they are compiler unit tests: tiny, feature-isolating, many exercise errors or extensions; needs a custom `.at` extractor. |
| **NIST CCVS85 (`newcob.val`)** | Official NIST URL now redirects to the generic `nist.gov/itl/` (HEAD probe, 301). GnuCOBOL's own `tests/cobol85/Makefile.am` says "currently down, leading to server error with HTTPS" and uses a Wayback copy. HEAD probes returned **HTTP 200** for `https://gnucobol.sourceforge.io/files/newcob.val.tar.gz` (3,368,733 B) and the Wayback URL (4,417,395 B). Not downloaded or inspected by me. | Koopa's `testsuite/cobol85/README.txt` says only "I am unsure of the license, but it seems to be in the public domain." This is **not** an authoritative licence statement. | Programs self-report PASS/FAIL (native oracle), but they are conformance tests, repetitive and unrepresentative of application code. |
| **ProLeap COBOL parser repo** (test resources) | <https://github.com/uwol/proleap-cobol-parser> README fetched: MIT licence; "passes the NIST test suite"; test files come from the Koopa repo. | MIT (parser code); test inputs inherit the NIST question above. | Parser, not a program corpus. |
| **OpenMainframeProject `cobol-programming-course`** | GitHub API: repo exists, licence `CC-BY-4.0`, 3,669 stars, language COBOL. The tree listing I fetched was truncated before any source files, so I **did not verify** it contains runnable `.cbl`. | CC-BY-4.0 | Unverified; course labs target z/OS (JCL, datasets), so expect porting work. |
| **GnuCOBOL `tests/cobol85` expected-output files** (`NC.txt`, `IF.txt`, …) | Listed via API. | GPL | Provide expected module reports only. |
| Local proprietary trees (§1.4) | Counts only. | Unknown, probably proprietary | Not usable publicly; Db2/CICS dependence. |

I did not find, and did not verify, any open corpus of *independent, input-driven, application-style* COBOL programs with regression tests. A small hand-authored or LLM-assisted set (with disclosure) would probably be needed to reach "business-logic-like" programs; that has its own validity risks.

### 5.2 Design (small, controlled)

- **Programs.** 40-60 independent single-file programs, each ≤ ~150 lines, reading ACCEPT/stdin or a fixed input file, using paragraphs, `PERFORM VARYING`, IF/EVALUATE, arithmetic, a table, at least one SIZE ERROR path. No `EXEC SQL/CICS`. Source: GnuCOBOL `.at` snippets that read stdin, NIST modules chosen for logic rather than I/O, and a small authored set.
- **Behaviour-preserving transformations (oracle-verified)**, with the same stdout and rc on every input: paragraph rename; paragraph reordering (valid only for GO TO-free sequences, with care for fall-through); `PERFORM` inline ↔ out-of-line; `EVALUATE` ↔ nested `IF` (demonstrated in `scratch/bench/t1.cob`); data-name rename.
- **Behaviour-changing mutations**, oracle-verified to differ on ≥1 input: arithmetic operator swap; comparison operator swap (`<` ↔ `<=`); PIC size change (e.g. `9(3)` → `9(2)`, which overflows differently); constant tweak.
- **Fixed inputs.** 4-8 stdin values per program (the toy accepted `ACCEPT WS-N` from a pipe).
- **Oracle.** exact stdout + process exit code (`RETURN-CODE`), with a fixed `-std` setting, same binary flags. Label rule: *same oracle on the whole input set ⇒ preserving; differs on ≥ 1 input ⇒ changing*. Equivalent mutants are possible; the label is "changed on this input set".
- **Tooling.**
  - Compiler/runtime: `cobc` 3.2.0 (present).
  - Tracer: `-ftraceall` + custom parser of the trace file (§3), plus either `USE FOR DEBUGGING` or C-level snapshots for values.
  - Source transformation: needs a parser. Options: **ProLeap** (ANTLR4; AST/ASG; build requires JDK 17 and Maven 3; here we have JDK 21 and **no `mvn`**), or **GnuCOBOL's own front end**. `cobc --help` shows no AST or parse-tree dump option, only `-E` preprocessed source, `-t` listing, `-C` generated C. I did not find a parse-tree export in cobc 3.2.0. A hand-rolled regex transformer is possible for a few tightly-controlled idioms but fragile (see the column-72 trap below).
  - Python adapter that converts a COBOL trace into SBG's `ExecutionTrace` objects (new code; no existing code to reuse, per `COBOL_EVALUATION_REPORT.md:17-19`).

**Fixed-format trap (observed twice):** columns 73+ are silently discarded in fixed format. Renaming `ADD-PARA` → `ACCUMULATE-STEP` pushed a `PERFORM … UNTIL` line past col. 72 and produced `error: invalid expression: unfinished expression` (`t1.cob` first build failed). Fixing the name length repaired it (`ACC-STEP`). Any rename or inline transform must be column-aware or use free format (`-free`).

### 5.3 Demonstration that the oracle and transformations work mechanically (not a result)

`scratch/bench/a.cob` (base) vs `t1.cob` (rename + EVALUATE), inputs 3, 4, 6, 9, 12: stdout and rc were identical in all five. Mutants m1 (`<`→`<=`), m2 (`+ WS-I`→`+ WS-I * 2`) and m3 (`PIC 9(3)`→`9(2)`) produced different stdout on at least one of inputs 3/4/6/9 (e.g. input 4: base `CLASS=MID`, m1 `CLASS=SMALL`; input 6: base `SUM=021`, m2 `SUM=042 CLASS=LARGE`; input 12 on m3 wasn't run). Paragraph-name multisets differ only by the renamed names (`a.trc` vs `t1.trc`). This shows the pipeline pieces exist; **it is not a benchmark**, there are no scores, and no SBG distance was computed.

### 5.4 Sample size and statistics

- 40-60 programs × ~4 preserving variants and ~4 changing mutants ⇒ roughly 160-240 pairs per class (before dropping non-compiling or non-discriminating variants).
- Pairs from one program are correlated, so use program-level cluster bootstrap or leave-one-program-out, as the Python study does (I did not re-verify the Python protocol here; mirror whatever the frozen protocol specifies).
- Pre-register: label rule, tokens for transformation and mutation families, the state-abstraction for COBOL, and any threshold choice **before** looking at SBG scores. Disclose that the local Db2 corpus was inspected (`COBOL_EVALUATION_REPORT.md:40-42` already requires this).

---

## 6. Effort estimate, recommendation, qualification criteria

### 6.1 Effort for one engineer (rough, my judgement, not measured)

| Task | Estimate |
|---|---|
| Trace-file parser → SBG `ExecutionTrace` events (paragraph entry as call, reconstructed return/depth, branch-taken inference) | 2-3 days |
| Value snapshots (decide `USE FOR DEBUGGING` vs C-instrumentation; implement; validate) | 3-5 days |
| COBOL state abstraction (new `_repr_to_abstract` for zoned/packed/binary/X/OCCURS; unit tests) | 2-3 days |
| Corpus assembly: extract/author 40-60 compilable, input-driven programs; licence review | 4-6 days |
| Transformation + mutation engine with column-72 safety; oracle runner; label verification | 4-6 days |
| Evaluation, CI, baselines (output-diff, coverage), write-up and threats | 2-3 days |
| Review/reproduction buffer | 2 days |
| **Total** | **≈ 19-28 working days (roughly 3-5 weeks); a bare proof-of-concept tracer on 5 programs is ≈ 1-2 days** |

### 6.2 Recommendation: **defer; do not include in the present study**

Reasons:
1. The current paper's evidence base is frozen and audited; adding an unvalidated second-language instrument now cannot be properly pre-registered or reviewed in time.
2. The existing COBOL corpus provides nothing (verified in §1).
3. The pieces that carry SBG's V3/temporal/state signal (exception types, call depth/return, scoped creation/deletion, value abstraction) have **no direct COBOL counterpart** (§4); the COBOL study would test a modified method, so a positive or negative result would not validate the Python study.
4. Gains: one sentence in Limitations is already planned (`FINAL_MANUSCRIPT_BLUEPRINT.md:71`; `COBOL_EVALUATION_REPORT.md:66-71`). That can stay, and can be updated to say that GnuCOBOL tracing was shown to be technically feasible in a toy prototype but not evaluated.

### 6.3 What the toy tracing does and does not show (honest limit)

- **Shows:** `cobc` 3.2.0 compiles and runs COBOL here; `-ftrace/-ftraceall` + `COB_SET_TRACE` yield paragraph/statement order; `--coverage` yields line counts; `USE FOR DEBUGGING` yields value-change events; stdout + `RETURN-CODE` are a deterministic oracle.
- **Does not show:** that SBG's representation captures any behaviour change in COBOL; that traces are stable under transformations beyond the 5-input toy; that results are comparable with the Python study; anything about real COBOL (z/OS, EBCDIC, Db2/CICS, copybooks, file I/O at scale). A parser or tracer is **not** behavioural validation.

### 6.4 What would qualify as a genuine cross-language evaluation

1. A pre-registered protocol (label rule, features, thresholds fixed before scoring), registered in the repo before any COBOL score is computed.
2. An independent, licensed corpus of ≥ ~40 executable programs with per-program regression inputs/oracles, not authored by the SBG developers solely for this test (or, if authored, disclosed as such with a held-out portion).
3. A tracer that produces events for the same concepts as the Python tracer, with an explicit, reviewed mapping (§4) and tests proving determinism across repeated runs and compiler flags.
4. Labels from executed oracles, balanced preserving/changing pairs, equal difficulty controls (e.g. matched edit size, as the Python study did).
5. Same baselines as the Python study (execution statistics, output-difference, coverage) re-implemented for COBOL.
6. Program-level clustered uncertainty, plus per-transformation breakdown.
7. Written statement of which SBG components were adapted and how (a different abstraction = a different method).
8. Separate treatment of dialect: either IBM-compatible results (needs IBM Enterprise COBOL on z/OS or a documented equivalent) or an explicit "GnuCOBOL-only" claim.

### 6.5 Risks and unknowns

- Column-72 and fixed-format fragility in any source-to-source transformer (observed).
- `-ftrace` shows entries but not returns; reconstruction may be error-prone (`GO TO`, `THRU`, fall-through).
- Whether the `USE FOR DEBUGGING` route behaves for group items, tables, `COMP-3` and REDEFINES is untested.
- Recursive `PERFORM` is silently allowed in GnuCOBOL 3.2 here; behaviour in other compilers unverified.
- NIST suite: licence status uncertain, official host unreliable; content not inspected by me.
- ProLeap needs Maven (absent) and JDK 17+; version compatibility with JDK 21 not tested.
- Proprietary local code cannot be published; any results on it would be unreproducible.
- Equivalent-mutant noise: labels are relative to the chosen input set.
- Risk of post-hoc tuning: the local Db2 corpus has already been inspected (disclosure needed).

---

## 7. Evidence-protection notes

- I wrote only under `agent_7/` (report plus `scratch/`). I did not run `cobol_inventory.py` or any `make` target, and I issued no state-changing git command.
- `git status --porcelain` shows untracked `artifacts/final/pairs_dev_output_free_v8.jsonl`, `pairs_v8dev_output_free_v8.jsonl`, `programs_dev_output_free_v8.json`, `programs_v8dev_output_free_v8.json` and `paper/`. **None was created by my commands** (I ran nothing that writes to `artifacts/`). I did not investigate their origin; flagging them for the coordinator.
- `/Users/manassakthivel/Desktop/SBG FINAL` was not touched.
- Local directory listings of proprietary trees reported counts only; I read no file contents there. The only COBOL source I opened was the first 12 lines of `COBOLSRC/COBBACK/cosql28.cbl` (a header; the corpus already audited).

---

## Appendix A — Commands run (and key output)

```
# repo / evidence
git rev-parse --short HEAD && git branch --show-current          -> 93ef3f3 / remediation/sbg-v4
grep -ril cobol <repo>                                           -> 16 files (see §1.1)
python3 -c "json.load(COBOL_CORPUS_INVENTORY.json)['summary']"   -> n_cbl=85, unique=84, cpy=10, exec_sql=85, stub_ok=72 ...
# corpus (read-only)
find COBOLSRC -type f -name '*.cbl' | wc -l                      -> 85
find COBOLSRC -type f -name '*.cpy' | wc -l                      -> 10
grep -L 'EXEC SQL' COBOLSRC/COBBACK/*.cbl COBOLSRC/cobol/*.cbl | wc -l   -> 0
grep -l -E '^ *CBL +SQL,LIB' COBOLSRC/COBBACK/*.cbl COBOLSRC/cobol/*.cbl | wc -l -> 85
head -12 COBOLSRC/COBBACK/cosql28.cbl                            -> "CBL SQL,LIB" / Program-ID. "bigint"
# other local sources (counts only; see §1.4)
find <dir> -type f \( -iname '*.cbl' -o -iname '*.cob' -o -iname '*.cobol' -o -iname '*.cpy' \) | wc -l
grep -rli -E 'EXEC +(SQL|CICS)' --include='*.cbl' <dir> | wc -l
# toolchain
which -a cobc cobcrun cob-config; cobc --version; cobcrun --version; cobc --info
brew info gnucobol | grep License                                -> GPL-3.0-or-later
cobc --help | grep -i -E 'trace|debug|coverage|-C|-fdump|stack'
# toy program
cd agent_7/scratch
cobc -x -o toy_plain toy.cob && ./toy_plain; echo rc=$?          -> (output in §2.3), rc=3
cobc -x -ftrace -o toy_trace toy.cob && ./toy_trace              -> no trace (env not set)
COB_SET_TRACE=Y ./toy_trace                                      -> paragraph trace (§3.1)
cobc -x -ftraceall -o toy_traceall toy.cob && COB_SET_TRACE=Y COB_TRACE_FILE=./traceall.txt ./toy_traceall
cobc -x -debug -fdump=ws -o crash crash.cob && ./crash           -> libcob error, WS dump, rc=1
cobc -x -fdebugging-mode=ok -o dbg dbg.cob && COB_SET_DEBUG=Y ./dbg
cobc -C -o toy.c toy.cob                                         -> 358-line C file with /* Line: n */ markers
cobc -x --coverage -o toy_cov toy.cob && ./toy_cov && gcov toy.gcda -> toy.cob.gcov (88.27% of C lines; COBOL lines mapped)
cobc -x -t toy.lst -o /dev/null toy.cob; cobc -E toy.cob        -> listing / preprocessed source only (no AST dump option found)
# dialect probes
cobc -x -o packed packed.cob && ./packed
cobc -x -std=ibm -o packed_ibm packed.cob && ./packed_ibm
cobc -x {,-std=ibm,-std=mf,-fno-trunc} ibmonly.cob               -> A=+0000 / +04464 / +4464 / +04464
cobc -x -fdefault-colseq=EBCDIC -o col_eb col.cob                -> ordering flips
cobc -x -o fs fs.cob && ./fs                                     -> FS=35
cobc -x -debug -o rec rec.cob && ./rec                           -> "A done N=3" x3, rc=0
cobc -x -ftrace -o gtprog gt.cob (copy of goto.cob; 'goto' is a rejected C-keyword base name)
# benchmark mechanics
cd bench; cobc -x a/t1/m1/m2/m3.cob; for inp in 3 4 6 9 12; echo $inp | ./a ; echo $inp | ./t1 ...
# web verifications (web_fetch / curl -I)
https://gnucobol.sourceforge.io/                                 (3.2 released 28 Jul 2023; NIST/internal test counts)
https://raw.githubusercontent.com/OCamlPro/gnucobol/gnucobol-3.x/README        (GPL / LGPL split)
https://raw.githubusercontent.com/OCamlPro/gnucobol/gnucobol-3.x/tests/cobol85/README, Makefile.am
https://api.github.com/repos/OCamlPro/gnucobol/contents/tests{,/testsuite.src,/cobol85}?ref=gnucobol-3.x
https://github.com/uwol/proleap-cobol-parser                     (MIT; JDK 17 + Maven 3; NIST suite)
https://github.com/krisds/koopa/tree/master/testsuite/cobol85    ("unsure of the license … public domain")
https://api.github.com/repos/openmainframeproject/cobol-programming-course   (CC-BY-4.0)
curl -sIL https://www.itl.nist.gov/div897/ctg/suites/newcob.val.Z -> 301 -> https://www.nist.gov/itl
curl -sIL https://gnucobol.sourceforge.io/files/newcob.val.tar.gz -> 200, 3368733 bytes
curl -sIL https://web.archive.org/web/20240322143655if_/https://www.itl.nist.gov/div897/ctg/suites/newcob.val.Z -> 200, 4417395 bytes
```

## Appendix B — Files produced

All under `agent_7/scratch/`: `toy.cob`, `toy.c`, `traceall.txt`, `stdout_traceall.txt`, `dbg.cob`, `crash.cob`, `rec.cob`, `goto.cob`/`gt.cob`, `fs.cob`, `packed.cob`, `ibmonly.cob`, `col.cob`, `cov/toy.cob.gcov`, `bench/{a,t1,m1,m2,m3}.cob` and the compiled binaries. Binaries and intermediate C/`.gcda` files can be deleted without loss.
