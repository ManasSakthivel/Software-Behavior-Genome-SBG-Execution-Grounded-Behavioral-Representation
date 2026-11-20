# Agent 5 — Java evaluation readiness (final sprint)

Repo `SBG/` @ `93ef3f38…` (branch `remediation/sbg-v4`), 2026-11-05. JDK: Temurin 21.0.12.1 (HotSpot) first on `PATH`; Python 3.13.5 (`../venvs/py313`).
**This is a readiness assessment. It is not a Java evaluation and not cross-language validation. No Java AUROC, detection rate or accuracy is reported.** The only numbers produced here are (a) test results, (b) a static eligibility count and (c) a 3-program mechanical smoke run that is explicitly descriptive.

Evidence tags: **[R]** re-run by me in this sprint; **[C]** read in committed code; **[P]** taken from the previous report (`paper/empirical_sprint_2026-11-04/agent_6/agent_6_java_feasibility.md`) and *not* re-verified here; **[I]** my estimate/judgement.

## 0. Bottom line

1. The previous report's core claims hold on re-check: `SbgJdiTracer.java` exists (509 lines), emits four event kinds, its output is consumed by the unchanged Python featuriser, and `tests/test_external_java.py` has **12 tests, 12 passed on JDK 21** in an isolated copy. [R][C]
2. A **controlled Java pilot is achievable in ~3–5 working days**, if it is restricted to a descriptive, clearly exploratory scope (≈12–20 fresh programs, paired SP/SC variants, oracle-gated labels, no inference). It is **not** achievable as a confirmatory study in this sprint. [I]
3. A **defensible Java benchmark** (H1–H3-type claims) is **≈5–8 working weeks** for one engineer with ≥30–40 programs; an H4-type incremental claim needs ≈100 programs. This is consistent with the previous estimate (23.5 / 36 / 52.5 days min/likely/max), which I reviewed and find reasonable but not independently derivable. [P][I]
4. **Recommendation: Java is not necessary before manuscript preparation.** State "CPython only; no Java evaluation performed" and keep Java out of every claim. A pilot, if run later, must be labelled exploratory and must never be worded as cross-language validation.

## 1. Verification of the existing report and implementation

| Claim (previous report) | Check | Result |
|---|---|---|
| Tracer is `external/quixbugs_java/tracer/SbgJdiTracer.java`, 509 lines | `wc -l` | **509** [R] |
| Four event types emitted | `grep` of `record("…")` calls: `call` (l.264), `line` (l.287, breakpoint kind `line` l.157), `return` (l.301), `exception` (l.339) | **Confirmed**: `call`, `line`, `return`, `exception` [C] |
| Unwound frames after an exception get a synthetic `return` | `record("return", …)` at l.341 follows the `exception` record (l.339) | Confirmed in code [C] (behaviour on `finally` not re-run; see §2) |
| `experiments/final/external_java.py` 1051 lines; test file 262 lines | `wc -l` | **1051 / 262** [R] |
| Python featuriser consumes Java traces unchanged | `record_from_runs` swaps `X._runner` for `_PreparedRunner` and calls `X._trace_and_record` (`external_java.py:517-528`); test `test_java_traces_featurise_through_python_pipeline` | Confirmed; V3, temporal and state genomes all non-null, `score_pair(r, r)` gives `sbg_v5 == 0.0` [R] |
| 12 tests pass on JDK 21 | Copied `sbg/ experiments/ external/ tests/` into `agent_5/_ws/`, ran `venvs/py313/bin/python -m pytest tests/test_external_java.py -p no:cacheprovider` with `PYTHONDONTWRITEBYTECODE=1` | **12 passed in 7.63 s** [R] |
| 30/40 QuixBugs-Java programs are canonical-input eligible; 10 excluded for unsupported types | `scripts/eligibility.py` (output `eligibility_quixbugs_java.json`) | **30 eligible / 10 ineligible**, the same 10 names as before (BFS, DFS, DETECT_CYCLE, KNAPSACK, MST, REVERSE_LINKED_LIST, SHORTEST_PATHS, SHORTEST_PATH_LENGTH(S), TOPOLOGICAL_ORDERING) [R] |
| No committed Java result artifact | `QUIXBUGS_JAVA_SBG_RESULTS.json` is not among the files I touched; reconfirmed that `git status` is unchanged from baseline | Consistent [R]; deeper `git ls-files` listing is from [P] |
| Overload/lambda/`finally`/line-layout gaps; ~10³× slower per event; 8–10 s per version | Not re-measured | [P] only. I regard them as plausible and consistent with the code (e.g. function identity is `Method.name()`), but they are **unverified in this sprint**. |

What the tests do and do not establish: the parity tests check GCD (recursion, 4 inputs) and one exception-propagation toy against the Python tracer, plus BITCOUNT featurisation. They show **mechanical schema compatibility**, not representational equivalence across constructs such as overloads, `finally`, inner classes, lambdas or generics. [C]

## 2. Is a controlled Java pilot realistic?

**Yes, at pilot scale; no, at confirmatory scale.** Reasons:

*Enabling facts*
- Tracer, harness generator, Java-literal input mapper, javac/JDI orchestration, and the pipeline into `extraction.score_pair` already exist and run on this machine. [R]
- Fresh programs only need: one public static entry method named after the class, parameters among `int/long/double/boolean/String/int[]/ArrayList<Integer>/List<Integer>` (the `java_family` whitelist, `external_java.py:229-247`), deterministic, single-threaded, no I/O. The oracle harness (`oracle_outputs`, l.550-569) already compares return values/exception class per protocol input. [C]
- No new dependency is required for a pilot: SP/SC variants can be written by a small regex/text script for ~3 families (identifier rename, constant/operator mutation), as in my smoke run.

*Blocking / limiting facts for anything beyond a pilot*
- `external_java.py` hard-codes output to `artifacts/final/` (l.76-82). Any run must be in a copied workspace or the paths must be parameterised, otherwise frozen/gate paths are at risk. I used a copy (`agent_5/_ws/`). [C][R]
- The oracle compares only return value / exception class (it prints `String.valueOf` or `Arrays.deepToString`); it does not capture stdout or in-place argument mutation, which the Python V10 oracle does (per [P], `generate_v10_independent.py:18`). A defensible Java oracle must add these.
- Known trace-semantic gaps [P] must be fixed *before* a freeze: overload/inner-class/lambda name collisions, duplicate exception events around `finally`, layout-sensitive line events, `char` rendered as a string. None is exercised by the 12 tests.
- Naïve text-level SP/SC tooling is dangerous; my smoke run hit this (§3).
- Corpus: QuixBugs-Java is MIT, 30 eligible, already used in earlier QuixBugs work, so **not independent**; TheAlgorithms/Java (MIT) is the obvious second source but its usable fraction is unmeasured. [P]
- Single-JDK dependence: bare `java`/`javac` are resolved from `PATH`; this machine also has IBM Semeru/OpenJ9 17 on `PATH` after `/usr/bin`. The vendor/build string must be asserted and recorded. [P][R: `which -a java` shows two entries]

## 3. Mechanical smoke run (descriptive; n = 3; not an evaluation)

Purpose: confirm that fresh, independent Java programs plus oracle-gated variants can flow through the existing bridge end to end, and expose design pitfalls. Scripts: `scripts/pilot_smoke.py`, `scripts/probe_countvowels.py`; programs: `programs/{SUMDIGITS,COUNTVOWELS,MAXRUN}.java` (author-written this sprint, same author as the harness, so **not independent**); outputs: `pilot_smoke_run1_naive_rename.json`, `pilot_smoke_run2_output.json`. All compilation happens in OS temp dirs; the repo's `external/quixbugs_java` was never written (verified: `diff -r` of the repo corpus against the workspace copy is empty; `git status` equals the baseline).

Final run (`pilot_smoke_run2_output.json`, all 3 base programs traced OK, 11 canonical inputs, 55 traces each):

| Program | SP variant (identifier rename; oracle-differing inputs of 11) | V5 distance SP | SC variant (1-line edit; oracle-differing inputs) | V5 distance SC |
|---|---|---|---|---|
| SUMDIGITS | 0 | 0.0 | `m > 0`→`m > 9`; 10 | 0.1253 |
| COUNTVOWELS | 0 | 0.0 | `'u'`→`'y'`; **0** | 0.0 |
| MAXRUN | 0 | 0.0 | `i > 0`→`i > 1`; **1** | 0.0 |

These are **per-pair distances, not performance**. No AUROC is computed; with 3 programs none would be meaningful. Observations that are valid:

1. **Oracle gating is necessary.** COUNTVOWELS "SC" changed `'u'` to `'y'`, but no battery string contains `u`, so oracle-equal on all inputs ⇒ it must be labelled *equivalent on the protocol inputs*, not a behaviour change. Under a family-based label, it would have been a mislabelled positive.
2. **Naïve rename tooling corrupts programs.** Run 1 used a word-boundary regex rename of `i`→`k`, which also rewrote the character literal `'i'` to `'k'`. The oracle flagged 1/11 inputs differing, so the "SP" variant was not behaviour-preserving (`pilot_smoke_run1_naive_rename.json`, `probe_countvowels.py`). Run 2 excluded quoted occurrences. A real pipeline must use an AST-based rewriter (Spoon/JavaParser) plus the oracle gate, as already proposed in [P].
3. **Value-only/low-visibility mutants exist in Java too.** MAXRUN's mutant differs on 1 of 11 inputs yet V5 = 0.0, i.e. it is invisible to the trace abstraction on this battery. I did not analyse why (no trace diff was inspected); this should not be read as representative of failure frequency.
4. **SP distances were exactly 0.0.** Expected for identifier renames given function-name anonymisation and local-variable abstraction; it carries no evidential weight for generality.

The run's V5 weights and code are the unmodified Python ones (the workspace is a byte copy of the repo's `sbg/` and `experiments/`; no edits).

## 4. Pilot design (exploratory; to be run only if time permits after the manuscript decision)

**Label (must not be worded "cross-language validation").** Name it *"Exploratory JVM trace-bridge pilot"*.

| Item | Specification |
|---|---|
| Question | Descriptive only: do oracle-validated CHANGED variants receive larger V5 distance than oracle-validated EQUIVALENT variants of the same Java program, beyond what edit size alone orders? No hypothesis test; report per-program results and exclusions. |
| Programs | 12–20 fresh, single-file, pure-static, deterministic Java methods from ≥2 families, written *before* viewing any SBG score; plus optionally the 30 eligible QuixBugs-Java programs as a dev/parity set only (not independent). Mark authorship. |
| Variants | Per program: ≥2 SP (rename; dead-code insert / comment+format) and ≥2 SC (off-by-one, operator swap) produced by an AST-aware rewriter, or by a fixed hand-written edit list committed before scoring. |
| Labels | Output oracle over the 11 protocol-battery inputs: return value, exception class, stdout, and in-place argument state (extension needed). EQUIVALENT ⇔ equal on all inputs; CHANGED ⇔ differs on ≥1; discard candidates that do not compile; log all discards. Label never depends on SBG output. |
| Matching | Compare each CHANGED/EQUIVALENT pair against the same base program; record line-diff edit size; report edit-size-only baseline (forward and reversed) and an execution-statistics baseline (event counts, coverage size) as for V10, so a high V5 distance cannot be confused with a larger edit. |
| SBG | Unchanged V5 `0.50/0.25/0.25`; no thresholds; no calibration on Java; everything frozen before first scoring (tracer hash, JDK build string, corpus and variant list hashes, input batteries, budgets). |
| Execution | Copy workspace or parameterised output root; never `artifacts/final/`. Run each version twice and require identical fingerprints (determinism gate). |
| Reporting | Per-program table; pair counts per label; exclusions by reason; ranking agreement against edit size; no pooled AUROC unless ≥12 programs have both classes, and then only with program-clustered bootstrap, flagged exploratory. |
| Success/failure | Any outcome is reported. Success is mechanical (pipeline completes, determinism holds, labels validated); it is **not** defined as a high AUROC. |
| Time | 3–5 working days [I]: 0.5 d freeze + pre-pilot hygiene, 1 d programs, 1 d variants + oracle extension, 0.5 d tracer parity fixes for the constructs actually used, 0.5 d run, 0.5–1 d write-up. |

## 5. Estimated effort for a defensible Java benchmark

I reviewed the work breakdown in [P] §7.1. I consider the structure sound; the numbers are judgement, not measurement, and my smoke run only informs items D, H and F qualitatively (programs ran first time; naïve SP tooling failed first time).

| Scope | Programs | Effort (1 engineer) [I] | What it can support |
|---|---|---|---|
| Descriptive pilot (§4) | 12–20 | 3–5 days | Pipeline feasibility and failure modes only |
| Reduced exploratory study | ~30–50 incl. QuixBugs | ~3 weeks [P] | Exploratory profile; no independence claim |
| Confirmatory Java study (H1–H3 analogues) | 30–40 independent | 5–8 weeks (23.5 / 36 / 52.5 days) [P] | Above-chance / beats edit size with program-clustered CIs |
| Incremental (H4 analogue) | ≈100 | beyond the above [P]; the sample-size figure is a normal-approximation borrowed from Python variance [I] | Incremental value over execution statistics |

Required engineering before any confirmatory freeze (all from [P], consistent with the code): disambiguated function keys (overloads/inner classes/lambdas), `finally`/try-with-resources exception dedupe, trace-level invariance gate for each SP family, JDK vendor/build assertion, oracle extension (stdout/argument mutation), AST-based SP/SC generators, replay-from-JSONL so scoring does not need the JVM, and a pre-registered freeze before first score.

Exclusions of Java scope: Java static genomes, cross-language equivalence of the same algorithm, absolute count comparisons across languages, and any JVM beyond HotSpot 21 are out of scope for any near-term claim.

## 6. Decision-relevant conclusions

- **Is Java necessary before manuscript preparation?** No. SBG's existing claims are about CPython traces; the manuscript can state this restriction. Java would add a positive headline only if it succeeds, and a ≤20-program pilot cannot be reported as cross-language validation.
- **Gate consistency item (carried from [P], not re-verified):** `experiments/final/stanford_gate.py` reportedly expects either `QUIXBUGS_JAVA_SBG_RESULTS.json` or a `JAVA_CLAIM_REMOVAL.json`; neither exists. The manuscript should keep Java sentences phrased as non-claims (e.g. "no Java evaluation has been performed"); the main session should decide whether to add the removal record. I did not create one (read-only).
- **Suggested wording:** "Evaluation is restricted to CPython. A JVM tracer emitting the same event schema exists in the repository; no Java evaluation has been performed."

## 7. Limits and blockers

- Not re-verified in this sprint: tracer overhead figures, overload/lambda/`finally`/line-layout findings, TheAlgorithms/Defects4J/Spoon/PIT/Major facts and licences, and the JDK 17/OpenJ9 behaviour (all from [P]).
- Determinism was not re-measured here; the smoke run did not repeat traces.
- The smoke programs and variants were written by the same agent that ran them; they illustrate mechanics and are not independent evidence.
- No blocker for the main sprint. The only non-trivial cross-agent hazard is that `external_java.py evaluate/run/finalize` write to `artifacts/final/` and must not be invoked in the repo tree; I did not call them.

## 8. Integrity statement

All writes are under `paper/final_empirical_readiness_2026-11-05/agent_5/`. `_ws/` is a copy of `sbg/`, `experiments/`, `external/`, `tests/` (and a temporary copy of `artifacts/final` plus an empty `benchmark/` that I removed after the runs). `diff -r external/quixbugs_java <workspace copy>` is empty; HEAD still `93ef3f38…`; `git status --short` shows the same four untracked `artifacts/final/*v8dev*` files plus `paper/` as the baseline. `PYTHONDONTWRITEBYTECODE=1` was set; `__pycache__` directories in the workspace were deleted afterwards. I did not run `sha256` over protected artifacts; the main session's final hash comparison covers that.

## 9. Files

- `agent_5_java_readiness.md` — this report
- `scripts/pilot_smoke.py`, `scripts/probe_countvowels.py`, `scripts/eligibility.py` — scripts (run with `venvs/py313/bin/python`, from `agent_5/`)
- `programs/*.java` — 3 smoke programs
- `pilot_smoke_run1_naive_rename.json`, `pilot_smoke_run2_output.json` — raw smoke outputs (descriptive)
- `eligibility_quixbugs_java.json` — static eligibility (30/10)
- `_ws/` — isolated copy used for test and smoke runs (≈6 MB; deletable)
