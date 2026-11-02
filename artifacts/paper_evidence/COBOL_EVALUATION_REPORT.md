# COBOL evaluation report (FINAL SPRINT, Part 5)

## Verdict

**The corpus cannot presently support either a valid external evaluation or a justified exploratory predictive study.**
At most it supports a *negative feasibility statement* (and a short qualitative note), for four independent reasons,
each sufficient on its own:

1. **No executable programs.** All 85 `.cbl` files are Db2 embedded-SQL precompiler test snippets (`CBL SQL,LIB`,
   `EXEC SQL … END-EXEC`). 0 / 85 pass `cobc -fsyntax-only` as-is (free or fixed form); they require a Db2
   precompiler and database, neither of which is available (no `db2`, `db2cob`, `ocesql`).
2. **Almost no program logic to observe.** Only 20 / 85 files contain any non-SQL procedure statement (totals: MOVE 27,
   DISPLAY 41, EVALUATE 22, IF 4, PERFORM 4, CLOSE 2); the rest are SQL statement sequences whose behaviour lives in the
   database, not in COBOL control flow, calls or local state — the things SBG represents.
3. **No oracle.** No tests, fixtures, expected outputs, variants or labels exist (0 found), so behaviour-changing and
   behaviour-preserving pairs cannot be labelled without inventing a database and an oracle.
4. **No COBOL instrumentation.** The SBG tracer uses `sys.settrace` and is Python-only. Evaluating SBG on COBOL would
   require a new tracer for GnuCOBOL (e.g. instrumented C emitted by `cobc -C`, or a `COB_` runtime hook) and a new
   state-abstraction layer — a new, unvalidated subsystem, not a use of the existing representation.

Classification: **not a valid external evaluation; not a justified exploratory evaluation; a qualitative feasibility
negative.** Do not label this as a successful or attempted external benchmark in the manuscript.

## What was done

All commands are recorded in `COBOL_CORPUS_INVENTORY.md` §4 and `experiments/final/cobol_inventory.py`.

```bash
cobc --version                                     # cobc (GnuCOBOL) 3.2.0
python3 experiments/final/cobol_inventory.py       # inventory, SHA-256, verb census, cobc probes -> COBOL_CORPUS_INVENTORY.json
# inside the script, per file, in a temp directory (corpus untouched):
cobc -fsyntax-only -free  p.cbl                    # 0 / 85
cobc -fsyntax-only -fixed p.cbl                    # 0 / 85
cobc -fsyntax-only -fixed s.cbl                    # 72 / 85 after the mechanical EXEC SQL -> CONTINUE stub
```

* Corpus location: `/Users/manassakthivel/Desktop/COBOLSRC` (95 files: 85 `.cbl`, 84 unique digests, 10 `.cpy`). The
  directory named in the brief (`…/cobol`) contains **1** file; the ≈ 70-file expectation is not met by any directory.
* No transformation was generated, no label was constructed, no SBG score was computed, and **no AUROC is reported**.
* The corpus has not influenced SBG: no feature, threshold or code in the frozen evaluation was changed after
  inspecting it. (If COBOL support is added later, this corpus must be disclosed as having been inspected.)

## Options considered (Part 5C)

| Option | Feasible? | Reason |
|---|---|---|
| A — existing labelled variants | **No** | no variants, tests or outputs; 84 unique files are different SQL tests, not versions of the same program |
| B — controlled paired transformations | **No (not defensible)** | the only 7 parsing programs with ordinary logic (`cosql01/27/28/59/77/78/79`) have 1–3 `MOVE`/`DISPLAY` statements (`cosql28`: 2 `IF` + 2 `PERFORM`); the SQL parts cannot be executed; at most 1–2 pairs per program would exist, with no meaningful trace. A set of < 10 hand-built pairs would give an AUROC with an uninformative confidence interval and a label oracle that we would have to author ourselves |
| C — qualitative cross-language case study | **Only as a feasibility statement** | the pipeline cannot parse, instrument or trace COBOL; there is no SBG representation of COBOL traces to show |

Even a hypothetical "stub the SQL and compare" experiment would measure the stub, not the programs: replacing
`EXEC SQL` by `CONTINUE` defines behaviour the programs never had (the stub is used in this sprint only to count
non-SQL statements).

## What this result establishes and does not

* **Establishes:** this local corpus is a parsing/precompilation test set, not a behavioural benchmark; evaluating SBG on
  it is blocked by missing Db2, missing oracles, and missing COBOL instrumentation. The brief's "≈ 70 files" expectation
  was incorrect for the path given.
* **Does not establish:** anything about SBG's cross-language applicability, positive or negative. Nothing here supports or
  weakens a generality claim.

## Placement in the paper

* **Main paper:** no COBOL results.
* **Limitations/future work (one sentence):** SBG's implementation is Python-specific (`sys.settrace`); its
  representation (abstract value domain, call-order function indices) is conceptually language-agnostic, but this has
  not been tested. A COBOL evaluation would need (i) an executable corpus with regression suites (e.g. GnuCOBOL's
  own testsuite or NIST COBOL85 test programs — **not** inspected or verified in this sprint), (ii) a GnuCOBOL tracer,
  (iii) a new oracle.
* **Appendix:** not recommended; a negative inventory adds no evidence.

## Constraints to preserve

* Do not copy the corpus into the repository: provenance/licence unknown. Local path and SHA-256 digests are recorded in
  [`COBOL_CORPUS_INVENTORY.json`](COBOL_CORPUS_INVENTORY.json).
* Do not report any "COBOL AUROC" in manuscript text, and do not compare it with V10.
