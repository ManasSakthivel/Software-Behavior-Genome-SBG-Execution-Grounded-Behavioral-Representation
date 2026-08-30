# SBG — External Dataset Selection Table
## Multi-Corpus Empirical Validation Sprint

**Created:** 2025  
**Sprint:** A+ Multi-Corpus External Validity Sprint  
**Status:** FROZEN — written before any new evaluation run  
**Supersedes:** N/A (new document for multi-corpus sprint)

---

## Dataset Selection Policy

Datasets are included only if **all six conditions** hold:

1. **Provenance is credible** — peer-reviewed, publicly documented, institutionally maintained
2. **Program versions are available** — both buggy and fixed versions retrievable
3. **Execution is reproducible** — programs can be run deterministically under controlled conditions
4. **Labels are defensible** — bug labels originate from original authors, not automated mining alone
5. **Output-free compatibility** — EEP can be applied without reading outputs, test verdicts, or patch contents
6. **Independent reproduction is possible** — another researcher can acquire and run the dataset

Datasets failing **any** condition are excluded and the reason is documented.  
Datasets that are **technically ambiguous** are assessed and the assessment is recorded.

---

## Full Dataset Selection Table

| Dataset | Language | Projects | Bugs | Real? | Bug Labels | Buggy/Fixed Versions | Tests | License | Output-Free Compatible | Included? | Reason |
|---------|----------|----------|------|-------|------------|---------------------|-------|---------|----------------------|-----------|--------|
| **Synthetic corpus (SBG)** | Python | 1 (inline) | 38 | No | Author-created | Yes (function pairs) | Yes (inline inputs) | N/A | ✓ Yes | ✓ **Yes** | Primary dev corpus; hyperparameter source |
| **QuixBugs** | Python | 31 programs | 31 | Yes | Authors (Koppel et al.) | Yes | Yes (JSON) | MIT | ✓ Yes | ✓ **Yes** | First external validation; zero-shot; already evaluated |
| **BugsInPy** | Python | 17 projects | 493 | Yes | Commit-linked real fixes | Yes (git checkout) | Yes (pytest) | Apache-2.0 | ✓ Yes (with adapter) | ✓ **Yes** | Primary Tier 1 target; real multi-project Python |
| **Defects4J** | Java | 17 projects | 835 | Yes | Real bug reports, patches | Yes (MVN checkout) | Yes (JUnit) | Apache-2.0 | ⚠ Requires Java adapter | ✓ **Yes (analysis only)** | Formally analyzed for EEP-Java feasibility; full evaluation requires non-trivial Java instrumentation |
| **ManySStuBs4J (100)** | Java | 100 projects | 10,231 | Mixed | Mining-based (single-statement) | Yes (git) | Partial | Apache-2.0 | ⚠ Java only | ⚠ **Feasibility analysis only** | Java language barrier; mining methodology introduces label ambiguity; no Python version |
| **ManySStuBs4J (1000)** | Java | 1,000 projects | 153,652 | Mixed | Mining-based (single-statement) | Yes (git) | Partial | Apache-2.0 | ⚠ Java only | ⚠ **Feasibility analysis only** | Same as above; scale does not resolve language barrier |
| **SWE-bench** | Python | 12 repos | 2,294 | Yes | GitHub issues + PRs | Yes (git) | Yes | Apache-2.0 | ⚠ Partial — large programs, multi-file | ❌ **Excluded** | Multi-file patches; programs too large for single-function EEP; execution environment complexity exceeds scope |
| **CoCoNuT benchmark** | Python | Various | ~100 | Mixed | Automated patch generation test | Partial | Partial | Research | ✓ Potentially yes | ❌ **Excluded** | Not independently publicly archived; patches are generated, not real bugs; provenance unclear |
| **BugsJS** | JavaScript | 8 projects | 453 | Yes | Real bugs | Yes (npm) | Yes | Apache-2.0 | ❌ No — requires JS tracer | ❌ **Excluded** | JavaScript only; no Python EEP adapter possible without substantial new instrumentation |
| **Bears** | Java | 72 projects | 251 | Yes | CI failures | Yes (Docker) | Yes | Apache-2.0 | ⚠ Java only | ❌ **Excluded** | Java only; Docker-based reproduction not feasible in current scope; covered by Defects4J analysis |
| **IntroClassJava** | Java | 6 programs | ~1,000 | No (student) | Student submissions | Yes | Yes | MIT | ⚠ Java only | ❌ **Excluded** | Student programs (not real software); Java only |
| **Codeflaws** | C | 3,902 cases | 3,902 | No (contest) | Online judge | Yes | Yes | Research | ❌ No — C language | ❌ **Excluded** | C language; EEP requires Python sys.settrace; no cross-language adapter |
| **MuBench** | Java | — | 90 | Yes | API misuse only | Yes | Partial | Apache-2.0 | ⚠ Java only | ❌ **Excluded** | API misuse defects only (narrow scope); Java only |

---

## Included Datasets Summary

| Dataset | Role | N Programs/Projects | N Bugs | Language | Zero-shot? |
|---------|------|---------------------|--------|----------|-----------|
| Synthetic corpus | Hyperparameter source; dev corpus | 1 corpus | 38 | Python | No (training corpus) |
| QuixBugs | First external validation (complete) | 31 programs | 28 evaluated | Python | ✓ Yes |
| BugsInPy | Primary Tier 1 external corpus | 17 projects | 493 total | Python | ✓ Yes |
| Defects4J | Language generalization analysis | 17 projects | 835 total | Java | Analysis only |

---

## Excluded Dataset Details

### SWE-bench — Excluded

**Reason:** SWE-bench contains multi-file patches to large real repositories (Django, Flask, NumPy, etc.).
EEP operates on single Python callables with known function names and bounded inputs.
SWE-bench bugs typically require:
- Multi-file instrumentation
- Module-level state initialization
- Complex test harness setup
- Environment installation (OS packages, databases, etc.)

These requirements are outside EEP's current instrumentation scope. A legitimate extension
to SWE-bench would require a fundamentally different module-level EEP adapter that is a
separate research contribution. Including SWE-bench without that adapter would produce
incorrect, misleading results.

**Decision:** Documented as a limitation and future work, not silently skipped.

### BugsJS — Excluded

**Reason:** BugsJS is a JavaScript corpus. EEP uses Python's `sys.settrace` for structural
execution tracing. A JavaScript equivalent would require a JS tracer (e.g., V8 inspector,
node --inspect, or a custom tracing wrapper). Such an adapter does not exist in this
codebase and would constitute a separate research contribution. Unlike the Defects4J/Java
case (where formal feasibility analysis is performed), no partial analysis of JS compatibility
is available.

### CoCoNuT, Bears, IntroClassJava, Codeflaws, MuBench — Excluded

Each excluded for a combination of: wrong language, non-real bugs, incomplete provenance,
or scope mismatch with EEP's function-level instrumentation model. See table above for
per-dataset reasons.

---

## BugsInPy Assessment

### Selection Criteria for BugsInPy Bugs

A BugsInPy bug is **INCLUDED** in EEP evaluation if all hold:

1. The project has a Python version ≥ 3.6 (required for EEP's `sys.settrace`)
2. A failing test exists that is linked to the bug
3. The failing test calls a **single top-level function** (or can be reduced to one)
4. The function can be imported from the bug's source tree
5. The test inputs can be extracted from the pytest call (no external I/O required)
6. Both buggy and fixed versions execute within 3.0s timeout per input
7. The function does not require database, network, or filesystem access at the test level

A BugsInPy bug is **EXCLUDED** if:
- The test requires mocking of complex external systems
- The bug manifests only in class initialization (no callable function)
- The test inputs cannot be parsed from pytest arguments
- The function requires OS-specific behavior not portable to evaluation environment

**Exclusions are reported** — every excluded bug is listed with reason.

### BugsInPy Projects Targeted

Projects selected to maximize diversity (algorithm, data structure, string processing,
numerical, web utility):

| Project | Domain | N Bugs | Priority |
|---------|--------|--------|---------|
| `pandas` | Data analysis | 165 | High |
| `ansible` | Automation | 18 | High |
| `black` | Code formatting | 23 | High |
| `luigi` | Workflow | 33 | High |
| `scrapy` | Web scraping | 40 | High |
| `httpie` | HTTP client | 5 | High |
| `keras` | Deep learning | 45 | Medium |
| `matplotlib` | Plotting | 30 | Medium |
| `cookiecutter` | Project templates | 4 | Medium |
| `fastapi` | Web framework | 16 | Medium |
| `sanic` | Web framework | 5 | Low |
| `spacy` | NLP | 10 | Low |
| `thefuck` | Command correction | 32 | Medium |
| `tornado` | Web framework | 17 | Medium |
| `tqdm` | Progress bars | 9 | Medium |
| `youtube-dl` | Downloader | 43 | Low |
| `PySnooper` | Debugging | 3 | High |

**Key insight:** Many BugsInPy bugs will be excluded because they require complex
test environments (database connections, network calls, OS-specific behavior). This is
expected and scientifically honest. We report all exclusions.

---

## Defects4J Feasibility Assessment

### Language-Independent Components of EEP

The following EEP features are **language-independent in principle**:

| Feature | Language independence | Requires for Java |
|---------|----------------------|-------------------|
| `d_exc_frac` | ✓ Independent | Java exception detection via instrumentation |
| `d_exc_jaccard` | ✓ Independent | Java exception type names |
| `d_trace_length` | ✓ Independent | Java method call counting (JVMTI or AspectJ) |
| `d_line_seq` | ⚠ Partial | Requires Java source line mapping |
| `d_sequential_drift` | ✓ Independent | Repeated execution detection |

### Java Instrumentation Requirements

To apply EEP to Defects4J programs, the following are required:

1. **Java execution tracer** — capturing method enter/exit events per test input
2. **Source line mapping** — to compute relative line numbers (equivalent to `co_firstlineno`)
3. **Exception capture** — exception type at each call
4. **Timeout enforcement** — Java process-level timeout
5. **Test input extraction** — from JUnit test methods

An existing partial infrastructure exists in [`docs/v5/JAVA_INFRASTRUCTURE_DESIGN.md`](v5/JAVA_INFRASTRUCTURE_DESIGN.md)
using string-level instrumentation and stderr tracing. This demonstrates feasibility for
simple programs but is not yet validated for the full complexity of Defects4J programs.

### Feasibility Conclusion for Defects4J

**Status:** Feasibility analysis complete; full evaluation technically valid but
requires Java adapter completion and validation.

**Decision:** Formal feasibility analysis is included in the multi-corpus report.
Full numerical evaluation of Defects4J bugs is documented as future work with specific
technical prerequisites identified.

---

## ManySStuBs4J Assessment

### Bug Label Reliability

ManySStuBs4J bugs are mined using pattern matching from git commits. The mining
methodology introduces the following ambiguities:

1. **False positives in labels**: Not all pattern-matched commits are actual bug fixes;
   some may be refactoring with superficially similar diffs
2. **Severity bias**: The corpus is biased toward simple single-statement changes
3. **Context dependency**: Whether a change is a "bug fix" depends on project context
   not captured in the diff pattern

### Decision

ManySStuBs4J is retained for feasibility analysis to understand its potential value
for EEP evaluation at scale. Full evaluation is not included in this sprint due to:
1. Java-only corpus (same barrier as Defects4J)
2. Label reliability concerns that would complicate interpretation

---

*Document frozen before any multi-corpus evaluation run.*  
*Any changes to this selection table must be accompanied by scientific justification.*
