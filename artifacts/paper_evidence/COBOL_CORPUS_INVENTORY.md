# COBOL corpus inventory (FINAL SPRINT, Part 5A/5B)

Corpus location given in the task: `/Users/manassakthivel/Desktop/COBOLSRC/cobol` (expected ≈ 70 COBOL files).
Read-only audit; **the corpus was not modified and is not copied into the repository.** Full SHA-256 digests,
per-file properties and compiler messages: [`COBOL_CORPUS_INVENTORY.json`](COBOL_CORPUS_INVENTORY.json).

Reproduce: `python3 experiments/final/cobol_inventory.py` (needs `cobc`; it writes only the JSON above and uses
temporary directories for compiler probes).

## 1. What is actually there

**Discrepancy with the brief:** `COBOLSRC/cobol/` contains **exactly one file** (`cosql31.cbl`, 981 bytes, 34 lines).
It is byte-identical to `COBOLSRC/COBBACK/cosql31.cbl`. The sibling directories hold the remainder:

| Directory | Files | Type |
|---|---|---|
| `cobol/` | 1 | `.cbl` (duplicate of `COBBACK/cosql31.cbl`) |
| `COBBACK/` | 84 | `.cbl`, `cosql01`–`cosql84` (none missing) |
| `cpyback/` | 10 | `.cpy` copybooks |
| `cpy/` | 0 | empty |

Totals: **95 files = 85 `.cbl` (84 unique SHA-256) + 10 `.cpy`**.
The ≈ 70 figure does not match any grouping (84 unique programs in `COBBACK`). The `.cbl` files total
5143 lines (min 27, max 432).

## 2. Nature of the files

* **All 85 of 85 `.cbl` files** begin with a `CBL SQL,LIB` compiler directive and contain
  `EXEC SQL … END-EXEC` blocks: they are **IBM Db2 embedded-SQL precompiler test snippets**
  (`MERGE`, array/`FOR n ROWS` host variables, `SELECT … INTO`, …), not self-contained applications.
* `Program-ID` is `"bigint"` in 84 of 85 files; the files are variations on one theme (SQL feature tests).
* The Procedure Division of each file is essentially a sequence of SQL statements. Only **20**
  files contain any non-SQL procedure statement; across the whole corpus these total
  MOVE 27, IF 4, PERFORM 4, DISPLAY 41, EVALUATE 22, CLOSE 2 (counts of verb occurrences; mostly 1–3 lines of `DISPLAY`/`MOVE`).
* File I/O: **0** programs. `COPY` statements: **2**.
  `cpyback/*.cpy` are 3-line fragments containing `EXEC SQL` (not data definitions, 0 define data).
* **No tests, fixtures, expected outputs, README, licence or provenance file** (0 found; none).
  Provenance and licensing are therefore **unknown**; redistribution cannot be assumed.
* All programs depend on a live Db2 database (tables such as `EMPTBL`, `ACCOUNT`, `IBMGRP.MYNAM`) via the Db2
  precompiler's SQL runtime; none is runnable without it.

## 3. Toolchain available

| Item | Result |
|---|---|
| `cobc` | cobc (GnuCOBOL) 3.2.0 (`/opt/homebrew/bin/cobc`) |
| Db2 precompiler / runtime (`db2`, `db2cob`, `ocesql`) | **absent** |
| SBG tracer | `sys.settrace`-based, Python-only; **no COBOL instrumentation exists** |

## 4. Feasibility classification (Part 5B)

| Probe | Command | Result |
|---|---|---|
| As-is syntax, free format | `cobc -fsyntax-only -free p.cbl` | **0 / 85** pass |
| As-is syntax, fixed format | `cobc -fsyntax-only -fixed p.cbl` | **0 / 85** pass (first error for all 85: `syntax error, unexpected Word or Literal, expecting .` at the first `EXEC SQL`) |
| After a *mechanical, behaviour-free* stub (each `EXEC SQL … END-EXEC` → `CONTINUE`; `SQLCODE`/`SQLN`/`SQLD` declared) | `cobc -fsyntax-only -fixed s.cbl` | **72 / 85** parse |

The stub exists only to ask "is there any non-SQL logic at all?" It defines no behaviour and is never used for labels.
The 13 files that still fail after stubbing have `EXEC SQL` in the Data Division or undefined `PAYRATE` host variables.

Classification of the 85 `.cbl` files (the 10 `.cpy` copybooks are category 4 by definition):

| Category | Count | Basis |
|---|---|---|
| 1. Standalone and executable | **0** | none compiles as-is; none runs without Db2 |
| 2. Executable with manageable dependencies | **0** | the only dependency is a Db2 database/precompiler; no substitute preserves the programs' meaning |
| 3. Missing required dependencies | **85** | every `.cbl` needs the Db2 precompiler and database |
| 4. Non-executable fragments or copybooks | 10 (`cpyback/*.cpy`) | 3-line `EXEC SQL` fragments, none defines data |
| 5. Unable to assess | 0 | – |

Subset with any ordinary COBOL logic that also parses after the mechanical stub: 7 programs — `cosql01`, `cosql27`,
`cosql28`, `cosql59`, `cosql77`, `cosql78`, `cosql79` (each ≤ 76 lines; 1–3 `MOVE`/`DISPLAY` statements, `cosql28`: 2 `IF` +
2 `PERFORM`). 13 other programs contain non-SQL statements but fail even after stubbing (`EXEC SQL` in the Data Division, or
undefined host variable `PAYRATE`). 65 files contain SQL only.

## 5. File list with hashes (SHA-256 prefix; full digests in the JSON)

| Path under `COBOLSRC/` | SHA-256 (first 16 hex) | Lines | `EXEC SQL` blocks | Non-SQL verbs | Compile status |
|---|---|---|---|---|---|
| `COBBACK/cosql01.cbl` | `0b9d44e0c23b2258…` | 50 | 7 | 2 | as-is: fails; parses after stub |
| `COBBACK/cosql02.cbl` | `9840dc091f517b65…` | 52 | 2 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql03.cbl` | `eb10af828b91ab7f…` | 33 | 2 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql04.cbl` | `f326e0da619cb38c…` | 33 | 2 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql05.cbl` | `37af9fc94fecbe53…` | 33 | 2 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql06.cbl` | `d029de35fd23b175…` | 33 | 2 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql07.cbl` | `80457cfe4474bf7f…` | 43 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql08.cbl` | `17a49fbee80389bb…` | 50 | 2 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql09.cbl` | `3c2f5377cbd0f234…` | 45 | 4 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql10.cbl` | `8a90e7875edeba71…` | 58 | 6 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql11.cbl` | `5e653fa12a5b4efa…` | 45 | 4 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql12.cbl` | `50c5acdc7ed6e7c4…` | 50 | 4 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql13.cbl` | `f8729b98c45da838…` | 42 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql14.cbl` | `36f4436de869da72…` | 62 | 6 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql15.cbl` | `95cd9670e1c8d8fc…` | 34 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql16.cbl` | `abc1a947314ae43e…` | 34 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql17.cbl` | `5fba269550a535ff…` | 39 | 2 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql18.cbl` | `54c9198b6bd1ea8e…` | 47 | 4 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql19.cbl` | `8e9293b51babc6b4…` | 43 | 4 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql20.cbl` | `bde7556ca622ad44…` | 53 | 4 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql21.cbl` | `d4c1f794612772c1…` | 67 | 6 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql22.cbl` | `740ead7c1e695150…` | 50 | 5 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql23.cbl` | `b3cccc9d1e17f216…` | 57 | 5 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql24.cbl` | `4cee88d50cef0448…` | 39 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql25.cbl` | `d3159c5d7e534511…` | 40 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql26.cbl` | `e480c5bdc347404d…` | 36 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql27.cbl` | `3632e73ff8967d35…` | 61 | 7 | 1 | as-is: fails; parses after stub |
| `COBBACK/cosql28.cbl` | `169a02970cbc002b…` | 76 | 10 | 7 | as-is: fails; parses after stub |
| `COBBACK/cosql29.cbl` | `0fe4d20a756beb10…` | 34 | 5 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql30.cbl` | `2d609f6d539f0f98…` | 72 | 5 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql31.cbl` | `a2e49b10258380f9…` | 34 | 2 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql32.cbl` | `2b392d3989f4525e…` | 34 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql33.cbl` | `d1312ecb91cd4115…` | 27 | 2 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql34.cbl` | `1dc5c835fdeb1fa2…` | 30 | 2 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql35.cbl` | `51aa661c14d3135a…` | 30 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql36.cbl` | `f962b48cc227cd9b…` | 53 | 5 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql37.cbl` | `767c99e2a1c7cf4a…` | 29 | 2 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql38.cbl` | `96770140faf92c95…` | 41 | 5 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql39.cbl` | `4f5255faf654353c…` | 45 | 6 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql40.cbl` | `e08c1178462897b8…` | 31 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql41.cbl` | `244e859495361d77…` | 165 | 33 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql42.cbl` | `a94d678243c41fab…` | 49 | 4 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql43.cbl` | `c59c84f95c708e10…` | 31 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql44.cbl` | `858545d186953503…` | 30 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql45.cbl` | `03d0b7b724b441cc…` | 31 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql46.cbl` | `e293cc11a8b919fc…` | 29 | 2 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql47.cbl` | `63258f6b5111086e…` | 89 | 12 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql48.cbl` | `2bec12b8fd0b8b38…` | 36 | 4 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql49.cbl` | `9c5c0bea152068ab…` | 33 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql50.cbl` | `257eb360286dbbef…` | 33 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql51.cbl` | `30c9961a1ad3b27f…` | 33 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql52.cbl` | `a67ffc2231938273…` | 28 | 2 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql53.cbl` | `4c9b9bf371af692b…` | 33 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql54.cbl` | `d77e35f302bfb349…` | 33 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql55.cbl` | `d38487d7b551341d…` | 55 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql56.cbl` | `604b00666a36462a…` | 121 | 9 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql57.cbl` | `fd4a704687a59fab…` | 180 | 14 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql58.cbl` | `3e5aeefd94748dc0…` | 46 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql59.cbl` | `b3ce5b3afc0ef68b…` | 40 | 4 | 2 | as-is: fails; parses after stub |
| `COBBACK/cosql60.cbl` | `5919ce0df99c8914…` | 189 | 29 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql61.cbl` | `38bde00117fd240c…` | 432 | 39 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql62.cbl` | `92946a2ed1628054…` | 69 | 12 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql63.cbl` | `e13dd6824f25a3a9…` | 61 | 9 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql64.cbl` | `b7eb512da30cd55b…` | 57 | 9 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql65.cbl` | `f1ef1b7bd1cfd836…` | 31 | 2 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql66.cbl` | `091515d3c5c25d2b…` | 84 | 7 | 8 | as-is: fails; fails after stub |
| `COBBACK/cosql67.cbl` | `8edc8e2b5ba7b5b8…` | 66 | 4 | 6 | as-is: fails; fails after stub |
| `COBBACK/cosql68.cbl` | `f03e63277e2c67a9…` | 90 | 6 | 6 | as-is: fails; fails after stub |
| `COBBACK/cosql69.cbl` | `21a6655ec5118a96…` | 64 | 3 | 6 | as-is: fails; fails after stub |
| `COBBACK/cosql70.cbl` | `ff4e3c4b7df42943…` | 75 | 6 | 6 | as-is: fails; fails after stub |
| `COBBACK/cosql71.cbl` | `3bfb57d94a50553c…` | 80 | 5 | 6 | as-is: fails; fails after stub |
| `COBBACK/cosql72.cbl` | `0ac6e5faf3a6f04c…` | 103 | 7 | 6 | as-is: fails; fails after stub |
| `COBBACK/cosql73.cbl` | `e86c0378dec3e91d…` | 85 | 6 | 6 | as-is: fails; fails after stub |
| `COBBACK/cosql74.cbl` | `502b92a9bc688fc7…` | 85 | 5 | 6 | as-is: fails; fails after stub |
| `COBBACK/cosql75.cbl` | `68051c16b8b4c3d6…` | 107 | 6 | 6 | as-is: fails; fails after stub |
| `COBBACK/cosql76.cbl` | `36976d9fc197df6c…` | 107 | 14 | 12 | as-is: fails; fails after stub |
| `COBBACK/cosql77.cbl` | `b32add3b1ca5b672…` | 71 | 4 | 2 | as-is: fails; parses after stub |
| `COBBACK/cosql78.cbl` | `3c2279a21367ff25…` | 57 | 4 | 2 | as-is: fails; parses after stub |
| `COBBACK/cosql79.cbl` | `51f7598afed89bef…` | 57 | 3 | 2 | as-is: fails; parses after stub |
| `COBBACK/cosql80.cbl` | `6cd6e28471d578c5…` | 35 | 3 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql81.cbl` | `54055cefe44e2f28…` | 52 | 6 | 2 | as-is: fails; fails after stub |
| `COBBACK/cosql82.cbl` | `ac584abe9506c470…` | 65 | 7 | 6 | as-is: fails; fails after stub |
| `COBBACK/cosql83.cbl` | `301a060555e91fe8…` | 45 | 6 | 0 | as-is: fails; parses after stub |
| `COBBACK/cosql84.cbl` | `f869a1a80515affe…` | 82 | 14 | 0 | as-is: fails; parses after stub |
| `cobol/cosql31.cbl` | `a2e49b10258380f9…` | 34 | 2 | 0 | as-is: fails; parses after stub |
| `cpyback/close1.cpy` | `8711034e46e9aeb2…` | 3 | 1 | – | copybook (not a program) |
| `cpyback/close2.cpy` | `1eff6e21b997cbd9…` | 2 | 1 | – | copybook (not a program) |
| `cpyback/declare1.cpy` | `41fd93dab2b62489…` | 13 | 2 | – | copybook (not a program) |
| `cpyback/declare2.cpy` | `028834bde08bf82d…` | 11 | 4 | – | copybook (not a program) |
| `cpyback/declgen1.cpy` | `a1f32ad3a10ecd9e…` | 12 | 1 | – | copybook (not a program) |
| `cpyback/emprec.cpy` | `8fbb15ad4eda4bf9…` | 11 | 0 | – | copybook (not a program) |
| `cpyback/execute2.cpy` | `348832c021cbdd99…` | 9 | 3 | – | copybook (not a program) |
| `cpyback/fetch1.cpy` | `7cbc82fa86e69279…` | 5 | 1 | – | copybook (not a program) |
| `cpyback/insert2.cpy` | `81d8a6d1562417a2…` | 4 | 0 | – | copybook (not a program) |
| `cpyback/select2.cpy` | `396afd14e73e19b5…` | 4 | 0 | – | copybook (not a program) |
