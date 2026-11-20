# Java Infrastructure Design — SBG v5

**Artifact:** `artifacts/v5/JAVA_INFRASTRUCTURE_DESIGN.json`  
**Status:** Design complete, 3 of 10 cross-language pairs implemented.

---

## Motivation

The SBG project defines 10 Python programs with Java equivalents documented in
`benchmark/cross_language/` (`p01`–`p10`). Until v5, no actual Java source files
or Java execution pipeline existed.

This infrastructure enables extraction of **DynamicGenome-compatible behavioral
signatures** from Java programs using the same feature schema as the Python
`sys.settrace` tracer — so Python and Java programs can be compared directly
using the existing `distance()` function in `sbg/v2/execution/genome.py`.

**Hard constraint:** no third-party Java parsing libraries, no bytecode
instrumentation (ASM/Javassist). Must work with JDK 17 at `/usr/bin/javac`
and Python `subprocess` only.

---

## Architecture

```
java_source.java
      │
      ▼
┌─────────────────────┐
│  JavaInstrumenter   │  Detects pre-instrumented files (skips re-injection).
│  instrument()       │  String-level regex: injects callDepth++ / try-finally
│                     │  at each method boundary. Writes instrumented .java to
│                     │  a temp dir.
└─────────┬───────────┘
          │ instrumented source
          ▼
     /usr/bin/javac → .class files in temp dir
          │
          ▼
┌─────────────────────┐
│   JavaExecutor      │  subprocess.run(java …, stdin=input, stderr=PIPE)
│   run_single()      │  Parses stderr for TRACE ENTER/EXIT/EXCEPTION lines.
│                     │  Returns List[JavaTraceEvent].
└─────────┬───────────┘
          │ all_traces (one per input)
          ▼
┌─────────────────────┐
│   extract_genome()  │  Mirrors TraceNormalizer logic exactly.
│                     │  Returns dict matching DynamicGenome.to_dict().
└─────────────────────┘
```

---

## Trace Instrumentation Protocol

Each instrumented Java method emits to **stderr** (never stdout):

```
TRACE ENTER <method_name> depth=<N>
TRACE EXIT  <method_name> depth=<N>
TRACE EXCEPTION <ExceptionType> depth=<N>
```

- `depth` is a static counter on the class, incremented at `ENTER` and
  decremented in the `finally` block.
- Stderr is captured via `subprocess(stderr=PIPE)`, completely separated from
  the program's functional stdout.

### Pre-instrumented benchmark files

`benchmark/v5/java_programs/` files are manually instrumented. The
`JavaInstrumenter` detects the `TRACE ENTER` marker and passes them through
unchanged, avoiding double-instrumentation.

---

## Genome Schema

All keys mirror [`DynamicGenome.to_dict()`](sbg/v2/execution/genome.py) so the
existing `distance()` function works across languages without modification.

| Key | Type | Description |
|-----|------|-------------|
| `program_id` | str | Java class name (file stem) |
| `coverage_size` | int | Unique structural coverage tokens across all traces |
| `coverage_consistency` | float | Mean pairwise Jaccard of per-trace coverage sets |
| `anon_call_freq` | Dict[str,float] | Normalised call freq, keyed by first-call-order index |
| `hot_path_hash` | str | 16-hex SHA-256 of top-5 anon indices by frequency |
| `exception_type_set` | List[str] | Sorted unique Java exception class names |
| `exception_rate` | float | Fraction of input traces with an exception |
| `call_depth_mean` | float | Mean max call depth across traces |
| `call_depth_max` | float | Maximum call depth observed |
| `trace_length_mean` | float | Mean event count per trace |
| `trace_length_std` | float | Std of event count per trace |
| `n_unique_functions` | int | Count of distinct instrumented methods called |

---

## Anonymization

Mirrors [`TraceNormalizer`](sbg/v2/execution/normalizer.py) exactly:

- Functions are indexed in **first-call order** (index 0 = first method called).
- `anon_call_freq` is keyed by integer index, not name → **rename-invariant**.
- **Filtered methods** (never included): `main`, `<clinit>`, `<init>`, `java.*`

---

## Coverage Proxy

Java execution traces carry no source line numbers. The structural analogue used
here:

```
coverage_token = depth_bucket × 1000 + anon_method_index
```

Two ENTER events at the same method and depth produce the same token (stable).
Two different methods at the same depth produce different tokens (discriminative).
The token is **rename-invariant** because it uses `anon_method_index`, not the
method name.

---

## Benchmark Programs

| File | Pairs with | Algorithm | stdin | stdout |
|------|-----------|-----------|-------|--------|
| [`BubbleSort.java`](benchmark/v5/java_programs/BubbleSort.java) | `p01_bubble_sort.py` | In-place bubble sort | space-separated ints | sorted ints |
| [`BinarySearch.java`](benchmark/v5/java_programs/BinarySearch.java) | `p03_binary_search.py` | Iterative binary search | line 1 = sorted ints, line 2 = target | index or -1 |
| [`LinkedList.java`](benchmark/v5/java_programs/LinkedList.java) | *(new)* | Singly-linked list | `add X` / `remove X` / `contains X` | true/false per query |

---

## Design Decisions

### 1 — String-level instrumentation, not ASM/Javassist

Benchmark programs are simple (no nested anonymous classes, no lambdas in hot
paths). String-level regex manipulation avoids a third-party dependency and keeps
the instrumenter auditable in 50 lines of Python.

### 2 — Pre-instrumented Java files in `benchmark/v5/java_programs/`

For benchmark programs, manual instrumentation is more readable and verifiable
than auto-generated code. `JavaInstrumenter.instrument()` detects the
`TRACE ENTER` marker and skips re-injection.

### 3 — stderr for trace, stdout for functional output

Allows `subprocess` to capture both streams independently with no interleaving
risk. Functional correctness can be checked from stdout; the behavioral trace is
read from stderr.

### 4 — Mirroring `TraceNormalizer` anonymization exactly

First-call-order anonymization ensures `anon_call_freq` keying is semantically
equivalent between Python and Java genomes, making `distance()` meaningful
across languages.

---

## Limitations

- String-level instrumenter does not handle: nested anonymous classes, lambda
  expressions in hot paths, multi-catch blocks, or methods with non-trivial
  generics.
- Coverage proxy (depth × anon_idx) is a structural approximation — not
  equivalent to Python's `sys.settrace` line coverage.
- `callDepth` is a `static` field: not thread-safe. Acceptable for
  single-threaded benchmark programs.
- Only 3 of the 10 cross-language pairs have Java implementations in this
  version.

---

## Future Work

1. Add Java files for `p02` (insertion sort), `p04`–`p10` to complete the
   10-pair cross-language corpus.
2. Cross-language distance evaluation: run Python and Java genomes through
   `distance()`, validate `d < 0.3` for equivalent algorithm pairs.
3. Replace string-level instrumenter with a proper `JavaParser`-based
   instrumenter for richer, real-world programs.
