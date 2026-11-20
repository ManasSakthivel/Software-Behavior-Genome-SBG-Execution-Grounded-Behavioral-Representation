# Agent 6 — Java cross-language feasibility (assessment only)

Repo `SBG/` @ `93ef3f3` (branch `remediation/sbg-v4`). Python 3.13.5 (`venvs/py313`). Written 2026-11-04.
**This is a feasibility study. It is not a Java evaluation. No Java AUROC, detection rate or score of any labelled pair was computed or is reported here.**

Conventions
- Paths are relative to the repo root `SBG/`. `file:N` = line N of the committed file at `93ef3f3`.
- Evidence tags: **[C]** read in committed code/docs (cited); **[M]** measured by me on this machine (scratch scripts + logs in `scratch/`); **[W]** official documentation fetched (URL given); **[I]** my inference/judgement, not verified.
- Evidence protection: no repo file modified; no `make` target; `external_java.py` was **imported** (its helpers `compile_version`, `run_traces`, `trace_version`, `entry_signature`, … write only to `tempfile` dirs) but `vendor`/`run`/`finalize`/`evaluate()` — the only paths that write `artifacts/final/*` — were never called. `git status` after all work equals `_baseline/status_before.txt`; `find . -newer _baseline/time.txt` outside `paper/` and `.git/` is empty.

---

## 0. Bottom line

1. **A Java trace→genome bridge already exists in the repo and works mechanically.** `external/quixbugs_java/tracer/SbgJdiTracer.java` (JDI, 509 lines) emits the same four event kinds with Python-repr-style locals; `experiments/final/external_java.py` feeds them into the *unchanged* Python featuriser. `tests/test_external_java.py`: **12 passed** (my run, 8 s, JDK 21, py313). [C][M]
2. **No Java result artifact exists** (`artifacts/final/QUIXBUGS_JAVA_SBG_RESULTS.json` and `pairs_quixbugs_java.jsonl` absent, not tracked; no `JAVA_CLAIM_REMOVAL.json`). The only Java result file is an older marker-only artifact that the module itself labels *superseded — not an SBG result*. [C][M]
3. **Even if `external_java.py run` were executed, it would not be an evaluation comparable to V9c/V10**: its negatives are bytecode-identical source variants (comment strip / re-indent / `if(false)`), so there is no size-matched, behaviour-validated design; the edit-size confound documented for Python would apply unmodified. [C][I]
4. **A credible Java evaluation is ~5–8 working weeks for one engineer** (my estimate, §7), plus ≥30–40 programs (not pairs) for H1–H3-type claims and ≈100 for an incremental (H4-type) claim. **It cannot be done credibly in one day.**
5. **Recommendation: defer.** In the present IEEE Access study state "Python (CPython) only; no Java result", keep Java out of every claim, and (main session) resolve the gate item (§7.4).

---

## 1. Architecture inspection

### 1.1 What the genomes consume (the plug-in interface)

```mermaid
flowchart LR
  subgraph Python-specific
    A[sys.settrace + frame.f_code/f_locals<br/>tracer.py:299,336-388] --> B[ExecutionTrace / TraceEvent<br/>tracer.py:37-70]
  end
  subgraph Language-neutral (reused for Java today)
    B --> C[SandboxResult-like: .traces List[List[ExecutionTrace]], .error<br/>runner.py:48-81,185-186]
    C --> D[extraction._trace_and_record<br/>experiments/final/extraction.py:336-439]
    D --> E[V3: DynamicGenomeExtractorV3<br/>sbg/v3/genome.py:170-252]
    D --> F[Temporal: extract(events dicts)<br/>sbg/v5/temporal_genome_v5.py:252]
    D --> G[State: StateTransitionGenome.extract(traces)<br/>sbg/v5/state_transition_genome.py:291]
    E & F & G --> H[score_pair: 0.50 V3 + 0.25 temporal + 0.25 state<br/>extraction.py:483,497-552; distance_v5.py:32-34]
  end
  J[JDI tracer SbgJdiTracer.java → JSON lines<br/>external_java.py:447-504] -. already plugs in at ExecutionTrace .-> B
```

The **plug-in interface is the `ExecutionTrace` object list** (and the `SandboxResult`-shaped stand-in `_PreparedRunner`, `external_java.py:507-528`, which replaces `extraction._runner`). Nothing downstream of `ExecutionTrace` imports `sys.settrace`, frames or code objects. [C]

**Fields an event carries** (`sbg/extraction/dynamic/tracer.py:37-45`): `event_type` ∈ {`call`,`return`,`exception`,`line`}, `function_name` (str = `frame.f_code.co_name`, `tracer.py:379`), `lineno`, `local_vars_snapshot: Dict[str,str]` (repr of every `f_locals` entry, truncated to 100 chars, `tracer.py:368-374`), `timestamp_ns`. Per-trace (`tracer.py:52-70`): `input_repr`, `events`, `return_value`, `exception` (`"Type: msg"` string, `tracer.py:302-303`), `stdout`, `execution_time_ms`, `coverage: Set[int]` (**line numbers only, no filename**, `tracer.py:361-362`), `truncated`.

What each genome actually reads [C]:

| Consumer | Reads | Never reads |
|---|---|---|
| V3 (`genome.py`, `normalizer.py`) | `call` events' `function_name` → first-call-order index (`normalizer.py:109-114`; `genome.py:198-202`); `call`/`return` counting for depth (`normalizer.py:137-146`; `genome.py:322-338`); `trace.coverage`; `trace.exception.split(":")[0]` (`normalizer.py:131`; `genome.py:301,384`); `exception` event `function_name`+computed depth (`genome.py:388-396`); `trace.truncated` (`extraction.py:394`) | `return_value`, `stdout` (SAFEGUARD-2, `normalizer.py:84`), snapshots, `timestamp_ns` |
| Temporal (`temporal_genome_v5.py`) | dicts `{event_type, function_name, depth}` (`:262-266`); call sequence (`:292-296`); exception events (`:317-345`) | snapshots, `lineno`, coverage |
| State (`state_transition_genome.py`) | **every pair of consecutive events** (any kind, incl. `line`), their snapshots, `function_name`, `event_type=="exception"` (`:321-332,412-423`) | `lineno`, coverage, exception type string |

Two observations that matter for any new tracer:
- **`depth` is a dead field.** `extraction.py:404` passes `getattr(event,"depth",0)` but `TraceEvent` has no `depth` (`tracer.py:37-45`) → always 0, and the temporal code never uses it. Depth is *reconstructed* by counting `call`/`return` events, so **a tracer must emit a `return` event for every frame unwound by an exception** or depth drifts (`normalizer.py:145-146`). The JDI tracer does this explicitly (`SbgJdiTracer.java:308-350`). [C]
- **Temporal F2 does not use the exception type.** `temporal_genome_v5.py:330` sets `exc_type = ev.get("function_name", …)` — the *function name where the exception event occurred*, although the module docstring (`:16`) says exception type strings are kept. It is therefore not rename-invariant when exceptions occur in renamed functions, in any language. (Out of scope; flagged for the main session.) [C][I]
- The V3/state components therefore need **line events** (coverage, per-input signature, state pairs). A call/return/exception-only tracer (e.g. AspectJ, §3) yields a *different, coarser* state object, not "the same genome". [C][I]

### 1.2 Python-specific dependencies

| # | Dependency | Where | Java consequence |
|---|---|---|---|
| P1 | `sys.settrace` per-thread hook, frame objects (`f_code`, `f_locals`, `f_lineno`) | `tracer.py:299,336-388` | Replace by JDI/JVMTI/bytecode agent |
| P2 | `repr()` as the state serialisation, capped at 100 chars; abstract domain derived by **regex over repr text** | `tracer.py:371-372`; `state_transition_genome.py:87-189` | Java tracer must *render Python-style reprs* (`SbgJdiTracer.java:369-431`) or the abstraction must be re-implemented natively |
| P3 | Function identity = bare `co_name`; anonymisation by first-call name (not code object); code objects used only for `HARNESS_CODE` filtering | `tracer.py:107,357,379`; `normalizer.py:109-114` | Overloads, inner-class methods and all lambdas collapse (measured, §4) |
| P4 | Exception model: `except Exception` around the call; string `"Name: msg"`; CPython's *exception event in every unwound frame + return*; `RecursionError`/`TimeoutError` counted as non-termination | `tracer.py:176-181,302-303`; `normalizer.py:131` | Different hierarchy/names (e.g. `ZeroDivisionError` vs `ArithmeticException`); checked exceptions; `finally` (measured, §4) |
| P5 | Worker thread + wall-clock join, abandoned daemon threads, `sys.stdout` swap | `tracer.py:204-248,255-326` | JDI runs target in a separate JVM that can be `destroyForcibly()`-ed (`SbgJdiTracer.java:101`) — an improvement |
| P6 | Import machinery: `importlib.util.spec_from_file_location`, `exec_module`, `compile()` | `extraction.py:152-173` | `javac` + classpath + class loading |
| P7 | Entry discovery via `ast`, `getattr`, `types.FunctionType`, `inspect.signature`, annotation text via `ast.unparse` | `extraction.py:176-215,246`; `protocol.py:142`; `sbg/v5/invariant_identity.py:23,381` | Replaced in Java by the QuixBugs "method named like the class" convention (`external_java.py:202-223`) — corpus-specific |
| P8 | Fixed input batteries typed by Python annotation families | `experiments/final/protocol.py:60-100` | Mapped by Java parameter type (`external_java.py:229-247`); `Node`, `int[][]`, `Map<…>` unsupported |
| P9 | Benchmark generation: SP-1…12 / SC-1…14 are `ast` transformers; edit size = `ast.unparse` line diff | `benchmark/transformations/*/manifest.json`; `experiments/final/edit_size_analysis.py:27` | Entire transformation/mutation/edit-size stack must be re-built for Java |
| P10 | Label oracle = (return value, exception type, in-place arg mutation, stdout) of the selected Python entry | `benchmark/scripts/generate_v10_independent.py:13-18,71` | Must be re-built (Java harness) |
| P11 | CPython-version sensitivity of event streams (e.g. 8771 vs 8024 events on 3.13 vs 3.9) | `docs/current/PYTHON_VERSIONS.md` | Java analogue: JDK vendor/build must be pinned (see R3) |
| P12 | Static genomes (control/data/error) use `ast.parse` | `sbg/extraction/static/*.py` | Not part of V5 (`distance_v5.py`) — irrelevant to the V5 evaluation |
| P13 | No `hash()` randomisation dependence in genome code; hashes are `hashlib` | grep: only `experiments/final/external_bugsinpy.py:951` (module name) | Hash/address normalisation is a non-issue for V3/V5 (address text only reaches the abstract domain as `NON_NULL`, `state_transition_genome.py:186`) |

### 1.3 Reusable, language-neutral components

`DynamicGenomeV3` + `distance_v3` (`genome.py:79-152,441-539`), `TemporalGenomeV5` + `distance` (`temporal_genome_v5.py:55-125,475-`), `StateTransitionGraph` + `StateTransitionGenome.distance` (`state_transition_genome.py:204-237,443-486`), `distance_v5` weights `0.50/0.25/0.25` (`distance_v5.py:32-34`; `extraction.py:483`), all canonicalisation/serialisation (`sbg/canonicalization.py:94-135`, `sbg/serialization.py:33-70`), and the statistics module `sbg/statistics.py` (cluster bootstrap/permutation, used by `external_java.py:870-889`). All take event streams / `ExecutionTrace`s and contain **no Python-runtime calls**. [C]

---

## 2. What exists in Java today

### 2.1 Inventory (committed) [C][M]

| Item | Facts |
|---|---|
| Corpus `external/quixbugs_java/` | 86 tracked files: 40 `correct/`, 40 `buggy/`, 2 `support/` (`Node`, `WeightedEdge`), `declared_inputs.json`, `LICENSE` (MIT), `MANIFEST.json` (sha256 `46773144…ec1ba`, QuixBugs commit `4257f44b…`), `tracer/SbgJdiTracer.java` |
| Code | `experiments/final/external_java.py` (1051 l.), `tests/test_external_java.py` (262 l., 12 tests); older, superseded: `experiments/external/quixbugs_java_evaluation.py` (887 l.), `experiments/v5/java_executor.py` (568 l., stderr `TRACE ENTER/EXIT` markers), `benchmark/v5/java_programs/{BinarySearch,BubbleSort,LinkedList}.java`, `docs/archive/v5/JAVA_INFRASTRUCTURE_DESIGN.md`, `artifacts/v5/JAVA_INFRASTRUCTURE_DESIGN.json` |
| Result files | `results/external/QUIXBUGS_JAVA_EVALUATION_RESULTS.json` — older "EEP" artifact (`instrumentation_method = method_boundary_TRACE_ENTER_EXIT_stderr`); `external_java.py:997-1012` calls it *"SUPERSEDED — not an SBG result; must not be cited as one"*. `results/phase6_12/CROSS_PROJECT.json` records "N=3 Java programs, no AUROC computed". |
| Absent | `artifacts/final/QUIXBUGS_JAVA_SBG_RESULTS.json`, `artifacts/final/pairs_quixbugs_java.jsonl`, `artifacts/final/JAVA_CLAIM_REMOVAL.json` (`ls`+`git ls-files` empty). The Makefile `java` target (`Makefile:145-147`) would create the first two but has never produced them in this tree. |
| Freeze record | `artifacts/final/PHASE2_FREEZE.json:11-17` has a `quixbugs_java` stage dated 2026-09-28 ("recorded before any Java pair was scored") — a freeze stamp with no downstream result. |
| Policy | `docs/current/PHASE2_PREREGISTRATION.md:165-173` (Java counts as SBG evaluation only with the same V3/temporal/state schema; else claim removed; reduced runs "exploratory"), `:197-198` (gate: SBG-schema artifact *or* claim-removal record). `docs/current/LIMITATIONS.md:74-79`, `README.md:500-503`: Java results unverified, excluded from every claim. Forensic audit `H.3` and lines 720/728/762: "no Java AUROC can be cited". |

### 2.2 What `external_java.py` does — precisely

**It executes Java.** For every program in the manifest and each of two input regimes (canonical = protocol batteries mapped by Java type; declared = input half of QuixBugs `json_testcases`):
1. `javac -g` compiles the program (renamed into package `java_programs`) + generated `SbgHarness` + `SbgMarker` (`external_java.py:330-336,339-398,420-440`).
2. Launches `SbgJdiTracer` which `LaunchingConnector`-starts the harness JVM (`-Xss8m -Xmx512m`), sets class-prepare, method entry/exit, exception requests and a **breakpoint on every line-table location** of `java_programs.*` (`SbgJdiTracer.java:63-91,143-163`), emits JSON per trace (`:497-508`). 11 inputs × 5 runs = 55 traces per program-version; 5000-event cap; 1 s + 3 ms/event budget (`external_java.py:84-97`; `extraction.py:58-59`).
3. Loads JSON into `TraceEvent`/`ExecutionTrace` (`:469-486`) and calls the **Python** `extraction._trace_and_record` via `_PreparedRunner` (`:507-528`) → V3 + temporal + state genomes → `X.score_pair` (`:772`). Weights/code are the Python ones.
4. Pairs: positive = QuixBugs buggy vs correct; negative = correct vs up to three of {J-SP4 comment strip, J-SP10 re-indent/drop blank lines, J-SP3 `if (false) { int sbgDeadCode = 0; }`}, **kept only if `javap -c -p` of all classes is identical** (`:576-675`). SP-1/SP-2 renames "are not implemented for Java and are omitted" (`:971-973`).
5. An *output-reading* reference (`oracle_outputs`, `:550-569`) and a regex Java token baseline (`:682-696`; `static_ast` "not computable", `:973-975`) are added; AUROC/cluster-bootstrap/Holm and detection at frozen τ* are computed per regime (`:842-927`).

**What it would establish if run**: that the existing Python featuriser can consume Java traces and rank "real QuixBugs bug" above "formatting-only variant" on ≤30 eligible programs (see below). **What it does not (and cannot) establish**: (a) any size-matched or behaviour-validated comparison — negatives are zero-edit-in-bytecode by construction, so a trace-based predictor is near-trivially separated; the edit-size confound documented for Python (`docs/current/EDIT_SIZE_REDESIGN.md:57`; `EVALUATION_PLAN_V9.md` §2) is reproduced, not controlled; (b) incremental value over execution statistics (H4); (c) generality beyond a 40-program, one-author-era toy corpus that was also used for Python QuixBugs; (d) anything about labelled mutants (no oracle-validated CHANGED partners other than the 1-line QuixBugs bugs, which may not alter traced behaviour on the battery). [C][I]

**Static eligibility I measured (no execution)** with the repo's own parsers: of 40 programs, **30 canonical-eligible**, 10 excluded for unsupported parameter types (`List<Node>`, `Node`, `Map<…>`, `int[][]`: BREADTH_FIRST_SEARCH, DEPTH_FIRST_SEARCH, DETECT_CYCLE, KNAPSACK, MINIMUM_SPANNING_TREE, REVERSE_LINKED_LIST, SHORTEST_PATHS, SHORTEST_PATH_LENGTH(S), TOPOLOGICAL_ORDERING); declared regime also 30/40 (`scratch/static_eligibility.json`). [M]

### 2.3 What I verified by running the existing machinery (not an evaluation) [M]

- `tests/test_external_java.py`: 12 passed.
- Determinism: for GCD, BITCOUNT, QUICKSORT (correct versions, canonical inputs, 55 traces each) two fresh JVM runs produced **identical** feature fingerprints (event count, call count, coverage size, V3 bigrams, temporal trigrams, state transitions) (`scratch/probe_log.txt`). 3 programs only; says nothing about multithreaded or timing-truncated programs.
- Loop parity BITCOUNT (4 inputs): call/line/return event *counts* identical Java vs Python; **coverage cardinality differs** (Java 3/5/5/5 vs Python 5/7/7/7) because the Python wrapper lambda and `def` lines enter the coverage set. Python traces also carry an extra `<lambda>` call/return frame from `traced_fn = lambda args: entry_fn(*args)` (`extraction.py:279-283,326-329`), which the parity test filters out (`tests/test_external_java.py:116-118`). ⇒ **absolute cross-language comparison of any count-based feature is invalid; only within-language pair distances are meaningful.**

---

## 3. Toolchain and instrumentation options

### 3.1 Local toolchain (verified, nothing installed) [M]

| Item | Result |
|---|---|
| `java`/`javac` | `/usr/bin/java`, `/usr/bin/javac` → **OpenJDK 21.0.12.1 LTS, Eclipse Adoptium Temurin, HotSpot 64-bit Server VM** (`JAVA_HOME=/Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home`) |
| Second JDK | **IBM Semeru Runtime 17.0.18.1 (Eclipse OpenJ9)** at `/Library/Java/JavaVirtualMachines/jdk-17.0.18+8.jdk`; its `bin/` is also on `PATH` (`~/Downloads/jdk-17.0.18+8/Contents/Home/bin`, listed after `/usr/bin` in `which -a`). The tracer shells out to bare `java`/`javac` (`external_java.py:412,436,464`) ⇒ **JVM vendor/version depends on PATH/`JAVA_HOME`** (R3). |
| Modules present | `jdk.jdi`, `jdk.jdwp.agent`, `java.instrument`, `jdk.jfr`, `jdk.attach`, `jdk.jshell`; `jvmti.h` present in JDK 21 `include/` |
| Build/dep tools | `mvn`, `gradle`, `ant` **not found**; no `~/.m2`; no ASM/ByteBuddy/JaCoCo/Spoon/JavaParser/PIT/OpenRewrite jar found under `~/.gradle ~/.m2 /opt /usr/local` (depth ≤4); `ajc`/`aspectjweaver`, `async-profiler` not found; `clang`/`gcc` and Homebrew present |
| Python | `venvs/py313` Python 3.13.5 |

### 3.2 Instrumentation options (docs fetched; effort/overhead judgments are [I] unless marked)

| Option | call / return / exception | arg / return / local / field state | Determinism | Overhead | Effort (1 engineer) | Verdict |
|---|---|---|---|---|---|---|
| **JDI** (current): `MethodEntryRequest`, `MethodExitRequest`, `ExceptionRequest`, `BreakpointRequest`, `StackFrame` | Entry/exit/exception requests exist [W1,W2]. **`MethodExitEvent` is *not* generated when a method ends by exception** [W3] → the tracer reconstructs unwound frames from `catchLocation()` [W4] (`SbgJdiTracer.java:308-350`). Class-name filters are exact or leading/trailing-`*` only [W1]. | Args via `StackFrame.getArgumentValues()` (works without debug info) [W5]; locals via `visibleVariables()` need `-g` LocalVariableTable [W5] (else snapshots silently empty, `SbgJdiTracer.java:260-262,361-363`); return value only if `canGetMethodReturnValues` [W3,W6]; fields need explicit reads | Event order identical in my 2-run test [M]; time-based truncation (1 s + 3 ms/event) is a machine-speed dependence | **[M] ≈180–900 events/s incl. javac+JVM start (GCD 420 ev / 1.1 s; BITCOUNT 1415 / 1.6 s; QUICKSORT 8640 / 17.0 s); Python Tracer on the QuixBugs-Python quicksort: ≈3.8×10⁵ events/s ⇒ ~10³× slower per event.** Extrapolated corpus cost §6.2 | **Exists** (509 l.); hardening 2–5 d | **Keep** for ≤ ~60 programs |
| **JVMTI native agent** (`-agentpath`) | Method entry/exit, exception, breakpoint, single-step events are capabilities of the interface [W7]; but the spec states JVMTI "does not include … full speed method enter and exit events" and recommends bytecode instrumentation [W7] | Local variable access functions exist [W7] | Same as JDI in principle | Lower than JDI (in-process) but entry/exit events are not "full speed" [W7] | C agent + per-platform build; 5–8 d [I] | Not recommended (no gain over ASM) |
| **`java.lang.instrument` + ASM** (load-time bytecode rewriting) | Insert recorder calls at method entry, before `*RETURN`, catch-all handler for exceptions, at line labels (`visitLineNumber`, `visitMethodInsn`, `visitTryCatchBlock`, `visitLocalVariable` are in `MethodVisitor`) [W8,W9]. The JVMTI spec notes that instrumentation is ordinary bytecode that the VM can optimise at full speed [W7] | Args/locals via emitted loads (need scope ranges from `visitLocalVariable`; reading a not-yet-assigned slot would fail verification; calling `size()` on program objects can have side effects or throw) [I] | High; JIT/inlining does not remove bytecode instrumentation [W7] | Low (≈10–100× faster than JDI) [I] | 8–12 d incl. state capture and exception semantic parity [I] | Best if scale ≫100 programs |
| **ByteBuddy** | Home page only confirms it is a runtime code-generation library [W10]; the `AgentBuilder`/`Advice` javadoc page did not render, so **its capabilities are not verified here** | — | — | — | — | Unverified; ASM is the verified route |
| **JaCoCo** | **Coverage only**, no call order. Probe-based: "source code lines with exceptions show no coverage" and line coverage needs debug info [W11] ⇒ lines in exception-terminated paths are lost, unlike `sys.settrace` coverage | none | Deterministic | Low | 1–2 d for per-input dumps (agent remote dump/reset) [W11] | Cannot supply the V3 coverage component faithfully; no use for temporal/state |
| **Java Flight Recorder** | Event/sampling framework designed for ≤1 % overhead [W12]; method data are **samples** (`jdk.ExecutionSample`, [W13]) | none | Sampling ⇒ nondeterministic call sets | ≈1 % | — | **Unsuitable** (no complete call sequence) |
| **AspectJ** | `execution()`, `call()`, `handler()`, `get/set()`, `cflow()`, `args()` and `after() throwing / returning` give call/return/exception and arg/return exposure [W14,W15]; no line-level join point, no locals | args, returned value, field get/set | Deterministic | Moderate | 3–5 d + needs `ajc`/weaver (not installed) | Gives only call/return/exception + args ⇒ **not the same state genome** |
| **async-profiler** | Sampling CPU/heap profiler [W16] | none | Nondeterministic | Low | — | **Unsuitable** |
| `jdb` | CLI front-end to the same JDWP/JDI | — | — | — | — | Not scriptable enough; JDI API already used |

Sources: [W1] `docs.oracle.com/en/java/javase/21/docs/api/jdk.jdi/com/sun/jdi/request/MethodEntryRequest.html`; [W2] `…/request/ExceptionRequest.html`; [W3] `…/event/MethodExitEvent.html`; [W4] `…/event/ExceptionEvent.html`; [W5] `…/com/sun/jdi/StackFrame.html`; [W6] `…/com/sun/jdi/VirtualMachine.html`; [W7] `docs.oracle.com/en/java/javase/21/docs/specs/jvmti.html`; [W8] `docs.oracle.com/en/java/javase/21/docs/api/java.instrument/java/lang/instrument/package-summary.html`; [W9] `asm.ow2.io/javadoc/org/objectweb/asm/MethodVisitor.html` and `asm.ow2.io` (states JaCoCo/Cobertura use ASM for coverage instrumentation); [W10] `bytebuddy.net`; [W11] `jacoco.org/jacoco/trunk/doc/faq.html`; [W12] `openjdk.org/jeps/328`; [W13] `docs.oracle.com/en/java/javase/21/docs/api/jdk.jfr/jdk/jfr/consumer/package-summary.html`; [W14] `eclipse.dev/aspectj/doc/released/progguide/semantics-pointcuts.html`; [W15] `…/semantics-advice.html`; [W16] `github.com/async-profiler/async-profiler`.

**Recommendation on tooling**: JDI (existing, verified end-to-end here) for a pilot and for a corpus of tens of programs; switch to an ASM agent only if the design grows past ~10³ program-versions. JaCoCo/JFR/async-profiler/AspectJ-only are not able to reproduce the schema.

---

## 4. Comparable component semantics (Python ↔ Java)

All comparisons are **within-language** (base-vs-variant both Java); the V5 distance is never computed across languages. Cross-language *equivalence* (Python vs Java of the same algorithm; old H11) is a different question and is not proposed.

| Component (weight in V5) | Python signal | Java signal (existing tracer) | Comparable? | Issue / evidence |
|---|---|---|---|---|
| V3 coverage_size (0.5·0.20), coverage_consistency (0.5·0.05), input_sensitivity (0.5·0.05) | `trace.coverage` ints from `line` events | breakpoint line numbers (`SbgJdiTracer.java:242`) | **Partly** | Needs line events. Line-event *layout sensitivity* differs: a one-line `for(...) total+=n;` yields **3** Java line events vs **9** for the braced multi-line form, whereas Python gives 6 vs 9 (`scratch/probe_oneline_loop_log.txt`, [M]; cause not investigated). Pure reformatting that merges/splits lines can change Java traces although bytecode is identical ⇒ SP validity must be checked at **trace** level, not only `javap` (existing J-SP4/J-SP10 only strip/re-indent and keep one statement per line). |
| V3 call bigrams (0.5·0.25), call freq (0.5·0.20), hot-path/depth | `call` events by `co_name` | `call` by `Method.name()` (`fname`, `SbgJdiTracer.java:211-216`) | **Partly** | **Overloads and same-named methods collide**: synthetic probe emitted calls `[probe, f, f, __init__, f, __init__, applyAsInt, <lambda>]` for `f(int)`, `f(int,int)`, `Inner.f(int)` all named `f` (`probe_semantics_log.txt` [M]). Lambda → `<lambda>` (`SbgJdiTracer.java:214`) but the hidden lambda class (`java_programs.PROBE$$Lambda/0x…` per snapshot) matches the `java_programs.*` filter and adds an `__init__` and `applyAsInt` event [I from [M]]. `Overloads resolve to the first declaration` for the entry (`external_java.py:207-208`). Fix is data-level (emit `Class.method(desc)`), must be decided pre-freeze. |
| V3 exception set/rate (0.5·0.10), causality hash (0.5·0.05) | `trace.exception` text before `:`; `exception` events | harness catches `Throwable`, stores `getSimpleName()` (`external_java.py:388`) | **Within-language yes; across no** | Names differ (`ZeroDivisionError` vs `ArithmeticException`) – irrelevant within a language. **Java `finally` duplicates exception events**: `fin(0)` gave `[…, exception helper, return helper, exception fin, exception fin, return fin]` vs Python `[…, exception fin, return fin]` (`probe_exc_scope_log.txt` [M]) because the compiler's rethrow in the catch-any handler raises a second `ExceptionEvent`. Affects try/finally, try-with-resources, `synchronized`. The shipped parity test covers only plain catch (`tests/test_external_java.py:144-151`). Checked exceptions: `harness.run` has no `throws` (`external_java.py:392`), so an entry declaring a checked exception would not compile [I from JLS; untested]. |
| Temporal trigrams (0.25·0.20), entropy (0.10), causal precedence (0.15), phases (0.10), loops (0.20) | call sequence | call sequence | **Yes, given a faithful call sequence** | Depends only on `call` events' names (`temporal_genome_v5.py:292-296`); inherits the overload/lambda issues above. Python's wrapper `<lambda>` is idx 0 in every Python trace and absent in Java traces (§2.3) – harmless within-language. |
| Temporal exception recovery (0.25·0.10+0.15) | exception events followed by `call` | same | **Fragile** | Uses the duplicated-exception stream above; `exc_type` slot actually holds a function name (`temporal_genome_v5.py:330`). |
| State: int sign/zero, null, bool | `repr` → regex (`state_transition_genome.py:93-132`) | `PrimitiveValue.longValue()` → decimal; bool → `True/False`; `null` → `None` (`SbgJdiTracer.java:390-396`) | **Yes** | `byte/short/int/long` map exactly; `char` becomes a quoted string ⇒ `NON_NULL` even for `'\0'` (`:393`), so char *values* lose sign/zero information that a Python `int` would keep. Floats: `Double.toString` forms like `1.0E16` still match the float regex. |
| State: boxed types | n/a (dynamic) | `Integer/Long/…` unboxed to the same repr (`:407-410`) | **Yes (by collapsing)** | Boxed vs primitive indistinguishable except `null`. |
| State: strings | `''`→EMPTY, else NON_NULL | `pyStr` (`:377-388`) | **Yes** | |
| State: arrays/collections | list/tuple/dict/set repr, size class from top-level commas (`:146-183`) | arrays and `ArrayList`/`Arrays$ArrayList` rendered with up to 40 elements; `LinkedList/ArrayDeque/PriorityQueue/Stack/HashMap/LinkedHashMap/TreeMap/HashSet/TreeSet` rendered as **size-correct placeholders** (`'0'` elements, `:421-424,437-464`) | **Yes for the 4-class abstraction; element content lost** | Any other class → `<Type object>` ⇒ `NON_NULL` (`:425-427`), as arbitrary Python objects (`state_transition_genome.py:186`). **Object fields are invisible in both languages.** Java `Map`s that are `TreeMap`/`HashMap` get `{0: 0, …}`. Size class from rendered text capped at 40 elements / 100 chars — documented for Python's 100-char cap as well. |
| State: object `self` | `repr(self)` → NON_NULL | `this` → `<Type object>` (`:254-255`) | Yes | |
| State: creation/deletion transitions | Python locals persist until function exit | Java locals are visible only inside their block scope (`visibleVariables` from LocalVariableTable [W5]): in my probe `t` appears at line 16 and disappears at the next line; `i` absent after the loop (`probe_exc_scope_log.txt` [M]) | **Semantically different** | Java emits `state_creation`/`state_deletion` transitions at block boundaries; Python does not. Not wrong, but means the *same source-level behaviour* contributes different mass to the state component. Within-language pair comparisons remain valid; cross-language magnitude comparisons do not. |
| Static vs dynamic typing | variables can rebind across types (`None→list`) | typed slots; `null` only for reference types | **Different distribution** | |
| JIT/inlining | n/a | JDI events are VM-level (breakpoints/requests), not bytecode inlining-dependent per spec of the debug interface [W1–W5]; bytecode agents unaffected by JIT [W7] | **Not a threat** [I] | I did not test `-Xint` vs default; the 2-run fingerprint equality [M] is weak evidence only. |
| Threads, `static {}` init, class loading | excluded program class (`runner.py:33-45`); import not traced | `<clinit>` ignored, classes preloaded (`SbgJdiTracer.java:152,246,295`; `external_java.py:355`) | Parity by design | Multi-threaded Java would interleave events (no thread filter on the requests, [W1,W2]) ⇒ exclude. |
| Timeouts | wall-clock join; abandoned thread | wall-clock + 3 ms/event; `destroyForcibly` | Different truncation points ⇒ **budget-dependent features** | Same in kind as Python (`tracer.py:95,342`). |

**Cannot be made comparable (flag)**: (i) Python-`repr`-text abstraction → only an *emulation* for Java (whitelisted types, placeholders); validity of the emulation is checked by 3 unit tests, not by an independent oracle; (ii) function identity under overloading/inner classes/lambdas unless names are disambiguated (changes the data, not the genome code); (iii) exception-event stream around `finally`/`synchronized`/try-with-resources; (iv) block-scoped locals; (v) absolute counts across languages (extra `<lambda>` frame, coverage composition, event density); (vi) char as numeric; (vii) temporal F2 uses function names (language-independent defect).

---

## 5. Controlled Java benchmark (proposal)

### 5.1 Program sources

| Source | Licence (verified) | Size / suitability |
|---|---|---|
| **QuixBugs-Java** (already vendored) | MIT (`external/quixbugs_java/LICENSE`; repo README MIT [W17 `github.com/jkoppel/QuixBugs`]) | 40 programs, 30 canonical-eligible [M]. Already used for the exploratory Python/Java QuixBugs ⇒ **not independent**; use as development/parity set only. Programs are one-line-defect algorithm exercises in package `java_programs`; the repo ships JUnit tests (gradle) whose expected outputs must **not** be read (output-free rule). |
| **TheAlgorithms/Java** | MIT, "Copyright (c) 2021 The Algorithms" (`raw.githubusercontent.com/TheAlgorithms/Java/master/LICENSE`, [W18 `github.com/TheAlgorithms/Java`]) | Master `DIRECTORY.md` (sha `5f8c5ec8…`, saved in `scratch/TA_DIRECTORY.md`) lists **775** `src/main` and **714** `src/test` Java files (my parse). Top packages: datastructures 140, maths 130, dynamicprogramming 54, sorts 50, strings 37, bitmanipulation 35, conversions 35. README: "for educational purposes… may be less efficient" [W18]. Many are static-method utilities (good), many are stateful classes/`Scanner` mains (excluded by eligibility). Expect a small fraction to pass a pure-static-entry + supported-signature filter [I]; the actual yield is unmeasured. Per-file author notices must be retained (MIT). |
| **Defects4J** | MIT (`github.com/rjust/defects4j`, [W19]) | 854 active real bugs, requires Java 11, Perl, svn; project-scale, test-driven. Appropriate only for an *exploratory real-bug* arm analogous to BugsInPy (at/below chance in Python), **not** the controlled benchmark. Not installed here. |
| **Fresh author-written programs** (as V8/V10) | author's | Precedent exists (`docs/current/FRESH_PROGRAM_PROTOCOL.md`), but "same author and generator" caveat persists. |

### 5.2 Behaviour-preserving transformations (SP)

| Tool | Verified facts | Fit |
|---|---|---|
| **Spoon** (INRIA) | Library to analyse/rewrite/transform Java source; supports up to Java 25; Spoon 11.x needs JDK 17+; **dual CeCILL-C / MIT** ([W20] `github.com/INRIA/spoon`, `spoon.gforge.inria.fr`) | Good for structured rewrites (rename, extract/inline method, loop rewrite, constant fold, dead-code); formatting fidelity of output is a design goal "when feasible" (R6 in [W20]) — not tested |
| **JavaParser** | Java 1–25 parser + AST + symbol solver; LGPL-3 / Apache-2 dual ([W21] `github.com/javaparser/javaparser`) | Good for AST edit; lexical-preservation features **not verified here** |
| **OpenRewrite** | Lossless semantic trees, recipes, "minimally invasive changes that honor the original formatting"; recipe distribution is moving to a different registry and requires access configuration ([W22] `docs.openrewrite.org`); licence terms **not read** | Heavy, build-tool-centric; licensing/distribution uncertainty ⇒ avoid |
| Eclipse JDT | Not fetched | Unverified |

Proposed Java SP set mirroring the Python SP-1…12 (`benchmark/transformations/preserving/manifest.json`): local/parameter rename, private-method rename (only if no overload), dead-code insert, comment strip, constant fold, condition rewrite (De Morgan), loop rewrite (`for`↔`while`), extract-method, inline-method, format-normalise, equivalent data-structure swap. Acceptance gate = **compiles + oracle-equal on every protocol input** (as `generate_v10_independent.py:13-18`), *not* bytecode-identity only. Observation [M]: renaming a parameter and a local changes nothing in `javap -c` output; names live only in the `-g` LocalVariableTable.

### 5.3 Behaviour-changing mutations (SC)

| Tool | Verified facts | Fit |
|---|---|---|
| **PIT** | Mutates **bytecode in memory**; "does not produce mutated source code"; requires JUnit/TestNG on the classpath; Java 8+; deterministic output except timeouts/static initialisers ([W23] `pitest.org`, `pitest.org/faq`) | **Poor**: no source ⇒ no source-level edit size, which the matched design requires |
| **Major** | javac compiler plugin; can export source-code mutants, suppress equivalent mutants, compute mutant-test matrices; v3.0.1; instructs to use a **Java-8 compiler** ([W24] `mutation-testing.org`) | Needs a JDK 8 (not present locally); source export is useful |
| **muJava** | "Mutation system for Java programs, including OO mutation operators", Apache-2.0, 19 commits, 71 stars ([W25] `github.com/jeffoffutt/muJava`); JDK compatibility not verified | Low activity; unverified |
| **Own Spoon/JavaParser mutators** | — | **Recommended**: mirror SC-1…14 (`mutations/manifest.json`: off-by-one, operator, constant, boundary removal, condition negate, return, exception suppression, loop bound, ordering, missing update, wrong variable, resource leak, condition removal, state-constant) so families align with Python and edit size is computable. |

### 5.4 Harness, inputs, oracle, matched design

- **Inputs**: fixed battery per parameter type, same `BATTERY_SIZE`=11 (`protocol.py:94`), extended beyond `int/long/double/boolean/String/int[]/ArrayList<Integer>` (`external_java.py:229-298`) to `char[]`, `String[]`, `List<String>`, `int[][]` where needed. 5 runs × 11 inputs (`extraction.py:58`).
- **Harness**: generated `main` driver calling the entry once per input and discarding the result (`external_java.py:378-398`; `test_harness_never_reads_the_entry_result`, `tests/test_external_java.py:191-196`); add `throws Throwable` to `run`.
- **Oracle** (labels; not SBG input): per program-version × input, record (return value via `Arrays.deepToString`/`String.valueOf`, exception class, stdout, in-place argument state) as in `generate_v10_independent.py:18` and `external_java.py:550-569` (currently one JVM launch per input per version). EQUIVALENT ⇔ oracle-equal on all inputs; CHANGED ⇔ differs on ≥1 input and the composed partner equals the pure mutant on all inputs.
- **Edit-size-aware matched design** (V9c/V10, `docs/current/EVALUATION_PLAN_V9.md` §3,§5,§6): for each EQUIVALENT `SP_t,s(p)` a CHANGED partner `SP_t,s(SC_k(p))`; compare both to `p`; report `edit` forward/reversed, M_E, M_ES, M_EX, M_ESX, cluster bootstrap by program. Java edit size = line diff of a canonical pretty-print (Spoon/JavaParser printer) — the analogue of `ast.unparse` (`edit_size_analysis.py:27`).

### 5.5 Sample sizes (programs = clusters, not pairs)

Reference from Python: V10 had **19 programs / 638 pairs / 319 matched sets** (≈34 pairs, ≈17 matched sets per program; forensic audit §H-summary, lines 30-37). Per-program V5 AUROC (read from `agent_1/per_program_auroc.csv`): V10 mean 0.893, SD 0.076 (n=19); V9c-val mean 0.752, SD 0.077 (n=11). Pooled V10 CI half-width ≈0.03; H4 CI [−0.069, +0.068] (half-width ≈0.07).

| Goal | Programs needed (normal approx, [I]) |
|---|---|
| Pilot, descriptive only, no inference | 12–20 |
| Mean per-program AUROC to ±0.05 / ±0.03 (SD 0.076 borrowed from Python) | ≈9 / ≈25 |
| H1–H3 analogues (above chance, adds to edit size, beats forward edit size) with program-level CIs | **30–40** |
| H4 analogue: detect an increment of ±0.03 beyond execution statistics (CI half-width ∝ 1/√n from 19→?) | **≈100** |

At ~34 pairs/program: 40 programs ≈ 1,350 pairs ≈ 1,400 traced program-versions; 100 programs ≈ 3,400 pairs. QuixBugs-Java supplies ≤30 eligible programs; reaching 40–100 requires a second source (TheAlgorithms) and/or fresh programs.

---

## 6. What qualifies as a genuine cross-language evaluation

### 6.1 Qualifying criteria (all required)

1. **Execution**: every program-version is compiled and executed under a tracer producing per-input `ExecutionTrace`s (events + coverage + exception + truncation). Parsing/lexing Java source is not an evaluation.
2. **Same representation code**: traces enter `extraction._trace_and_record`/`score_pair` (or a byte-identical successor); weights 0.50/0.25/0.25 and every genome constant unchanged; no Java-specific weights, thresholds or fitted models; code hashes and the Python commit recorded.
3. **Schema parity evidence**: unit tests + a parity check on ≥N programs (call/return/exception structure, line counts, snapshots) incl. `finally`, overloads, lambdas, nested classes — the current suite does not cover these (§4).
4. **Frozen protocol before scoring**: manifest/licence hashes, input batteries, budgets, transformation and mutation lists + seeds, oracle definition, hypotheses (H1–H4 analogues, Holm family), exact JDK vendor/build string, tracer source hash — committed *before* any labelled score, as `PHASE2_FREEZE.json`/`FREEZE_V10.json`.
5. **Labels from the execution oracle**, not from transformation family; rejected candidates logged.
6. **Edit-size-aware matched design** with forward/reversed edit size and incremental models.
7. **Program-level clustering**; programs disjoint from anything used to develop or debug the tracer; no post-hoc tracer change after the freeze.
8. **Full denominators** (ALL vs EVALUABLE, failure ledger with kinds) and wording "withheld, same author" if applicable.

### 6.2 Does **not** qualify

Static token/AST statistics of Java source (e.g. `java_token_multiset`, `external_java.py:682-696`); marker-only ENTER/EXIT traces (`experiments/v5/java_executor.py`, the superseded EEP artifact); reduced schemas (`PHASE2_PREREGISTRATION.md:171` calls these exploratory); QuixBugs-only runs with bytecode-identical negatives; any comparison across languages of counts or distances.

---

## 7. Minimal implementation plan, effort, recommendation

### 7.1 Work breakdown (one engineer, 8-hour days; **estimates [I]**, not measured)

| # | Work item | Min | Likely | Max |
|---|---|---|---|---|
| A | Harden JDI tracer: pin/assert JDK build+vendor, `function_key` (overload/inner-class disambiguation), hidden-lambda-class filtering, `finally` double-exception dedupe, optional real `depth`, scope policy, parity tests | 2 | 3 | 5 |
| B | Event serialisation: schema version, on-disk JSONL + hashes, replay-without-JVM loader | 0.5 | 1 | 1.5 |
| C | State abstraction: validate/extend Python-repr emulation or native typed mapping; equivalence tests incl. `char`, boxed, nested arrays | 1 | 2 | 3 |
| D | Driver harness + input mapping (arrays, strings, collections, user types), checked-exception harness, stdout/exception capture | 2 | 3 | 4 |
| E | Corpus curation (≥60 candidates → ≥40 eligible), licence manifest, eligibility ledger | 2 | 3 | 5 |
| F | SP suite (≥6 families) on Spoon/JavaParser incl. toolchain bootstrap (no Maven/Gradle installed) + trace-level invariance tests | 4 | 6 | 9 |
| G | SC suite (≥8 operators) + equivalent-mutant filtering | 3 | 4 | 6 |
| H | Oracle harness + validation gates + label ledger | 2 | 3 | 4 |
| I | Edit-size metric, composed matched-set generator, selection audit | 2 | 3 | 4 |
| J | Pre-registration text, freeze tooling, single-run evaluator (reuse `sbg/statistics.py`) | 2 | 3 | 4 |
| K | Compute run (est. 4–6 h: ≈1,400 versions × ~10–17 s [M-extrapolated]), failure triage | 1 | 2 | 3 |
| L | Tests, docs, reproduction script, paper text | 2 | 3 | 4 |
| | **Total** | **23.5 d** | **36 d** | **52.5 d** |

→ **credible confirmatory Java study ≈ 5–8 working weeks**; a reduced exploratory study (QuixBugs + ~20 TheAlgorithms programs, 4 SP + 6 SC, no H4) ≈ 3 weeks.

### 7.2 What could be done at smaller scales

| Budget | Deliverable | Value |
|---|---|---|
| **1 day** | Documentation only: limitation sentence; record that a JDI prototype with 12 passing parity tests exists but no Java evaluation was run. No tracer changes, no scored pairs. | Honest, prevents an unsupported generality claim |
| **3–5 days (pilot, "clearly labelled exploratory", in a *copy* of the repo with output paths redirected — `external_java.py` hard-codes `artifacts/final`, `:76-82`)** | Items A (subset) + parity checks on 8–10 programs; run the existing pipeline on the 30 eligible QuixBugs programs (compute est. 1–3 h); descriptive profile (events, exclusions, determinism). **If scores are produced they are exploratory per `PHASE2_PREREGISTRATION.md:171`, not citable as validation, and — because negatives are bytecode-identical — not comparable with V9c/V10.** | Evidence of mechanical feasibility |
| 5–8 weeks | Full study per §6 | The only route to a claim |

### 7.3 Recommendation

**Defer to future work; do not include Java in the present IEEE Access study.** Reasons: (1) no Java result exists; (2) the infrastructure's negatives do not support an edit-size-aware conclusion; (3) four known trace-semantic gaps (§4) must be fixed *before* a freeze; (4) even a well-run Java study needs ≥30–40 programs for H1–H3 and ≈100 for incremental claims, beyond the 40-program QuixBugs corpus; (5) the paper's existing H4 result is null, so a Java replication would not add a positive headline for a day's work. Suggested wording: *"The evaluation is restricted to CPython; a JVM tracer emitting the same event schema exists in the repository but no Java evaluation has been performed."* (no number).

### 7.4 Note for the main session (gate consistency)

`experiments/final/stanford_gate.py:265-274` marks external validation as missing unless `QUIXBUGS_JAVA_SBG_RESULTS.json` **or** `JAVA_CLAIM_REMOVAL.json` exists, and `_java_claims()` (`:278-286`) flags any current document line mentioning "java" that lacks one of "removed|withdrawn|not an sbg|exploratory|no java claim". Neither artifact exists; I did not create one (read-only constraint). Any manuscript sentence about Java should avoid tripping that regex or the removal record should be added by the owner.

---

## 8. Risk list

| ID | Risk | L | I | Mitigation |
|---|---|---|---|---|
| R1 | Overload/inner-class/lambda collisions corrupt function indices (§4) | H | H | Emit disambiguated `function_key`; freeze rule; filter hidden lambda classes |
| R2 | Java `finally`/try-with-resources/`synchronized` yield duplicate exception events ⇒ temporal F2, V3 causality distorted | M | M | Dedupe in tracer; add parity tests for these constructs |
| R3 | JVM vendor/version drift (Temurin HotSpot 21 vs Semeru OpenJ9 17 on PATH; bare `java`/`javac` calls) | M | H | Assert exact `java.vm.name`/version in the tracer, record in freeze |
| R4 | State abstraction is an emulation of Python repr; mismatch for `char`, nested/large arrays, user classes | M | M | Native typed mapping or validated shim; independent unit oracle |
| R5 | Layout-sensitive line events (3 vs 9 line events for one-line vs braced loop) make format-only SP non-invariant at trace level | M | H | Trace-level invariance gate on every SP; avoid line-merging transforms |
| R6 | Edit-size confound re-created (bytecode-identical negatives, 1-line bugs) | H | H | Composed matched design with oracle gating (§5.4) |
| R7 | Overhead ~10³× Python; 5000-event cap + 1 s + 3 ms/event may truncate machine-dependently | M | M | ASM agent if scale grows; fixed budgets frozen; log truncation |
| R8 | Corpus too small/non-independent (QuixBugs 30 eligible; reused) | H | H | Second source + fresh programs; declare same-author |
| R9 | Missing tooling (no Maven/Gradle, no Spoon/JavaParser/PIT jars; Major needs JDK 8) and dependency/licence handling | H | M | Bootstrap offline jars with checksums; keep own SC mutators |
| R10 | Non-determinism from threads, `HashMap` iteration order, `System.nanoTime`/`Random` in candidate programs | M | M | Exclusion rule + determinism check (≥2 runs identical fingerprint, as in §2.3) |
| R11 | Governance: results written into `artifacts/final` overwrite frozen evidence; gate requirements (§7.4) | M | H | Separate output root; copy of repo |
| R12 | Over-claiming "cross-language generality" from a Java pilot | M | H | Wording rule; keep Java out of claims until §6 met |
| R13 | License attribution (MIT notices in TheAlgorithms files; CeCILL-C/MIT for Spoon; LGPL/Apache for JavaParser; OpenRewrite licence unread) | L | M | Manifest with licence per file; avoid OpenRewrite |
| R14 | Exceptions are `Throwable` in Java (incl. `StackOverflowError`) vs Python `Exception` (`tracer.py:302`); `-Xss8m` vs Python recursion limit ⇒ different non-termination classification | M | L | Document; freeze limits |

---

## 9. What cannot be established now

- Any Java detection/AUROC statement, positive or negative, for V5 or any component.
- Whether the Python findings (V10 H1–H3 supported, H4 null) transfer to Java; whether a null in Java H4 would be informative at <100 programs.
- Whether the Java state abstraction is equivalent to the Python one beyond the whitelisted types tested; behaviour on user-defined classes and large collections.
- Robustness across JVM vendors/versions (only Temurin 21 was exercised; OpenJ9 17 present but untested), `-Xint` vs JIT, or on multi-threaded code.
- Correctness of the tracer for `finally`, try-with-resources, synchronized, inner/anonymous classes, generics-heavy code (probes show gaps for the first and for overload/lambda naming).
- Throughput at benchmark scale (only 3 program-versions timed; 1,400-version cost is extrapolation).
- Capabilities of ByteBuddy/muJava/Eclipse JDT/OpenRewrite licensing (not verified); AspectJ/ASM behaviour was taken from documentation, not tested.
- Cross-language equivalence (Python↔Java same algorithm) — not studied, and counts are not comparable (§2.3, §4).

---

## 10. Evidence index

Scratch (all under `agent_6/scratch/`, read-only w.r.t. repo): `probe_overhead.py` (+`probe_log.txt`), `probe_static_eligibility.py` (+`static_eligibility.json`), `probe_loop_parity.py`, `probe_semantics.py` (+`probe_semantics_log.txt`), `probe_exc_scope.py` (+`probe_exc_scope_log.txt`), `probe_oneline_loop.py` (+`probe_oneline_loop_log.txt`), `probe_py_speed.py` (+`probe_py_speed_log.txt`), `TA_DIRECTORY.md` (sha256 prefix `5f8c5ec89e4971b0`). Scratch scripts compile synthetic classes in OS temp dirs, trace them, print structure, and score nothing.

Environment: macOS 26.6.2 arm64; Temurin 21.0.12.1 (HotSpot); Python 3.13.5; `external/quixbugs_java/MANIFEST.json` sha256 `46773144b124678d958f4ca24cd2b56090809df40621c4dd9433790dbf5ec1ba` (matches `PHASE2_FREEZE.json:13`).

Web [W17–W25]: [W17] `https://github.com/jkoppel/QuixBugs`; [W18] `https://github.com/TheAlgorithms/Java`; [W19] `https://github.com/rjust/defects4j`; [W20] `https://github.com/INRIA/spoon`; [W21] `https://github.com/javaparser/javaparser`; [W22] `https://docs.openrewrite.org/`; [W23] `https://pitest.org/`, `https://pitest.org/faq/`; [W24] `https://mutation-testing.org/`; [W25] `https://github.com/jeffoffutt/muJava`.
