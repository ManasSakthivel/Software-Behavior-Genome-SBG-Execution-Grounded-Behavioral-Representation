# Benchmark Design — Software Behavior Genome (SBG)

**Agent:** 0F  
**Date:** 2025  
**Status:** Working draft — methodology is grounded in the formal model (FORMAL_MODEL.md) and prior art matrix (PRIOR_ART_MATRIX.md); all sample-size decisions are explicitly justified.

---

## Overview

This document specifies the benchmark and ground-truth protocol for testing whether the SBG behavioral genome can reliably distinguish **semantics-preserving** program transformations (where the behavioral genome should remain stable: Hypothesis H1) from **semantics-changing** mutations (where the genome should detect the change: Hypothesis H2).

The benchmark also provides evaluation ground for H3 (cross-language equivalence), H5 (genome as regression oracle), and H6 (genome uniqueness).

**Primary evaluation task:** Binary classification — given a pair of programs (P, P'), predict whether they are semantically equivalent under a defined input distribution I and environment E.

---

## Part 1 — Corpus Design

### 1.1 Categories of Base Programs

A base program is an independently authored, complete, runnable program with well-defined inputs, deterministic behavior under fixed seed, and oracle-checkable outputs. Programs are drawn from real-world codebases and algorithmic corpora, not synthetically generated.

| # | Category | Rationale | Representative Sources |
|---|---|---|---|
| C1 | **Sorting and Order Statistics** | Dense control flow, data-dependent branching, well-studied mutation space; extensive prior art (Defects4J, mutation testing literature). | stdlib sort variants, open-source implementations of quicksort, mergesort, heapsort, timsort, radix sort |
| C2 | **String Processing and Parsing** | Character-level data flow; many meaningful mutations (off-by-one, wrong delimiter, case folding errors). Rich DATA dimension variation. | JSON parsers (small), CSV tokenizers, string matchers, URI parsers |
| C3 | **Graph Algorithms** | Complex control flow, path-dependent behavior, loop iteration distributions are semantically significant. Tests CONTROL dimension. | BFS, DFS, shortest path (Dijkstra, Bellman-Ford), topological sort, connected components |
| C4 | **Numerical / Scientific Computation** | Data flow is numerically sensitive; small mutations in arithmetic change output distributions. Tests DATA and ERROR dimensions. | FFT kernels, matrix multiply, numerical integration (Simpson, trapezoid), linear system solvers |
| C5 | **Data Structure Operations** | State transitions are semantically significant (heap topology, stack depth). Tests STATE dimension. | Binary search tree insert/delete/search, hash table implementations, priority queues, union-find |
| C6 | **File and Stream I/O Processing** | System call patterns and I/O volumes are observationally meaningful. Tests INTERACTION and RESOURCE dimensions. | Log file processors, CSV aggregators, binary file readers, line-count utilities |
| C7 | **Concurrent / Parallel Programs** | Thread interleaving, shared-state access; TEMPORAL and EXECUTION dimensions stressed. Non-determinism is controlled via fixed scheduling seeds. | Producer-consumer, parallel reduce, worker pools (deterministic via fixed thread count + seed) |
| C8 | **Cryptographic Primitives** | Bit-level correctness; minimal correct mutations exist; high sensitivity to any semantic change. Provides true hard negatives. | SHA-256, AES-128 (reference implementations), CRC32, HMAC |
| C9 | **Compression Algorithms** | Interplay of DATA, RESOURCE, and INTERACTION dimensions; known-equivalent implementations exist across languages. | LZ77 encoder, Huffman coder, run-length encoding, zlib-compatible DEFLATE subset |
| C10 | **Search and Constraint Satisfaction** | Backtracking, pruning, solution enumeration; control flow structure is semantically critical. | N-queens, Sudoku solver, binary search, k-NN |
| C11 | **System / OS Interface Programs** | System call vocabulary, resource usage patterns — directly exercises INTERACTION and RESOURCE dimensions. | Process monitors, file walkers, directory diff utilities, socket ping clients |
| C12 | **Compiler / Interpreter Front-Ends (Small)** | Complex, multi-phase control flow with well-defined I/O; many known equivalent implementations exist. | Expression evaluators, Brainfuck interpreters, simple stack-based VMs, regex matchers |

> **Note:** Categories C7 and C11 are included despite additional complexity because they are necessary to evaluate the TEMPORAL and INTERACTION genome dimensions. All C7 programs must be deterministic under a fixed thread count and PRNG seed.

### 1.2 Programs per Category

| Category | Minimum Programs | Justification |
|---|---|---|
| C1–C5 (core algorithmic) | 8 per category | Sufficient diversity of control structures within category |
| C6–C8 (I/O, concurrent, crypto) | 6 per category | Higher implementation cost; lower syntactic diversity needed |
| C9–C12 (specialized) | 5 per category | Narrower semantic space; diminishing returns beyond 5 |

**Total base programs:** (5 × 8) + (3 × 6) + (4 × 5) = 40 + 18 + 20 = **78 base programs**

See Section 7 for statistical justification of this minimum.

### 1.3 Diversity Criteria

For each category, the selected programs must satisfy:

1. **Algorithmic diversity:** No two programs in the same category may implement the same algorithm (e.g., cannot have two quicksort programs in C1 unless one is iterative and one recursive and they are semantically distinct in structure).
2. **Language diversity:** At least 3 languages represented across each category; for cross-language pairs (H3), at least 2 languages per category.
3. **Scale diversity:** Mix of small (< 100 LOC), medium (100–500 LOC), and large (500–2000 LOC) programs. No single program > 2000 LOC (untestable criterion, see 1.4).
4. **Provenance diversity:** Mix of independently authored programs (not derived from each other) and known-equivalent re-implementations (e.g., Python vs. Java re-implementations of the same algorithm from algorithm textbooks). Provenance must be documented for ground-truth validity.
5. **Input distribution diversity:** At least 3 distinct canonical input distribution types per category (uniform random, boundary/edge case, production-representative).

### 1.4 Exclusion Criteria

A program is **excluded** from the corpus if any of the following apply:

| Criterion | Rule | Reason |
|---|---|---|
| **Too simple** | Fewer than 3 distinct reachable paths under any non-trivial input | Genome is degenerate; H6 (uniqueness) is trivially violated |
| **Too complex** | > 2000 LOC in a single compilation unit, or cyclomatic complexity > 150 | Genome extraction is computationally intractable within budget |
| **Untestable** | No oracle exists for output correctness (e.g., programs that produce "best effort" non-deterministic output without a ground-truth reference) | Ground truth for semantic equivalence cannot be established |
| **Non-deterministic** | Behavior is not reproducible under fixed seed and fixed environment, even after applying the determinism policy from Assumption A6 | Genome extraction produces inconsistent results; per A6, programs where scheduling non-determinism cannot be canonicalized are excluded |
| **External state dependent** | Behavior depends on live network, system clock, user interaction, or mutable global state not controllable by the test harness | Input distribution I cannot be closed; behavioral equivalence is undefined |
| **Trivially equivalent** | The program pair is syntactically identical or differs only in whitespace/comments | Ground truth is trivially correct; provides no discriminative signal |
| **License-incompatible** | Source is not available under an OSI-approved license or is commercially proprietary | Corpus cannot be distributed for reproducibility |

### 1.5 Minimum Viable Corpus Size — Statistical Justification

**Requirement:** We need sufficient programs to produce enough pairs for the classification task to have statistically sound evaluation.

Let:
- $n_B$ = number of base programs
- $n_{SP}$ = semantics-preserving pairs (positive class)
- $n_{SC}$ = semantics-changing pairs (negative class)
- Target precision on test set: 0.70 (per H5 threshold)
- Target recall on test set: 0.80 (per H5 threshold)
- Confidence interval target: ±0.05 on precision/recall at 95% confidence

**Sample size for proportion estimation:**  
For a proportion $p$ with margin of error $e = 0.05$ at $z = 1.96$:
$$n \geq \frac{z^2 \cdot p(1-p)}{e^2} = \frac{1.96^2 \cdot 0.25}{0.0025} \approx 384$$

This is the minimum number of test pairs. With a 20% held-out test fraction, the full labeled dataset requires at least **1,920 pairs**. Allowing for class balance and a safety factor of 1.5, the target is ≥ 2,880 total pairs.

At 78 base programs with an average of ~2.5 transformations per program per transformation type, the planned 3,200 pairs (see Section 7) satisfies this bound with margin.

---

## Part 2 — Transformation Taxonomy

Transformations are applied to a base program $P$ to produce a transformed version $P'$. The benchmark label is determined by whether $P \equiv_S P'$ holds under the ground-truth protocol (Part 3).

### 2.1 Semantics-Preserving Transformations (SP)

A transformation $T$ is **semantics-preserving** if for all inputs $i \in \mathcal{I}$:
$$B(T(P), i) = B(P, i)$$
i.e., all observable outputs and side effects are identical. By H1, $D(G(P), G(T(P))) < \varepsilon_{\text{stable}}$ should hold.

| ID | Type | Formal Definition | Example | Applicability Conditions | Expected SBG Difficulty |
|---|---|---|---|---|---|
| SP-1 | **Rename (Identifier Substitution)** | Replace all occurrences of a variable/function name $x$ with $x'$ consistently | Rename `temp` → `buffer` throughout a function | Applies to any program; purely syntactic | **Easy** — no behavioral signature change |
| SP-2 | **Comment and Documentation Change** | Add, remove, or modify any non-executable annotation | Add docstrings, remove inline comments | Applies to all; affects no runtime behavior | **Easy** — zero genome delta expected |
| SP-3 | **Reorder Independent Statements** | Swap two statements $s_1; s_2 \to s_2; s_1$ when $s_1$ and $s_2$ have no data dependency | Swap two unrelated variable initializations | Requires verified data-independence via PDG analysis | **Moderate** — TEMPORAL dimension may show micro-variation |
| SP-4 | **Loop Normalization** | Transform `for` ↔ `while` loops preserving iteration count and body semantics | `for (i=0; i<n; i++) {...}` → `i=0; while(i<n) {...i++}` | Loop bounds must be statically determinable or equivalent by construction | **Easy** — CONTROL frequencies preserved |
| SP-5 | **Constant Folding / Expression Simplification** | Replace a constant expression with its pre-computed value | `2 * 3 + 1` → `7` | Expression has no side effects | **Easy** — DATA dimension unchanged |
| SP-6 | **Dead Code Elimination** | Remove code that never executes under any reachable input | Remove a branch that is unreachable given preconditions | Requires reachability proof or test coverage confirmation | **Moderate** — EXECUTION coverage vector may change |
| SP-7 | **Extract Method / Inline Method** | Refactor: move code into a new function (or inline a call) without changing execution semantics | Extract `validate()` from a larger function; or inline a one-liner | The called function must have no non-local side effects other than explicit return | **Moderate** — CONTROL call graph structure changes; frequencies preserved |
| SP-8 | **Equivalent Data Structure Substitution** | Replace one data structure with another providing identical semantics for the used operations | Replace `ArrayList` with `LinkedList` where only sequential-access operations are used | Requires proof that all used operations have identical observable behavior; may change RESOURCE/TEMPORAL | **Hard** — RESOURCE and STATE dimensions may legitimately shift |
| SP-9 | **Algorithm Substitution (Equivalent Complexity Class)** | Replace an algorithm with a provably output-equivalent alternative | Replace insertion sort with merge sort producing same sorted output on same input | Requires oracle equivalence test; RESOURCE/TEMPORAL will change | **Very Hard** — multiple dimensions shift; tests whether CONTROL/DATA/INTERACTION still agree |
| SP-10 | **Compiler Optimization Flag Change** | Recompile with `-O0` vs `-O2` flags (or equivalent) | Same C source compiled at different optimization levels | Source code is identical; only binary/bytecode changes | **Hard** — EXECUTION and TEMPORAL dimensions may shift significantly |
| SP-11 | **Exception Handling Refactor (Equivalent)** | Restructure try/catch blocks without changing which exceptions propagate | Convert checked to unchecked exception wrapping with identical propagation | Exception type and propagation path must be provably equivalent | **Moderate** — ERROR dimension should be stable |
| SP-12 | **Logging / Instrumentation Addition (Non-Observable)** | Add logging calls that write to a log sink excluded from the observable output oracle | Add `logger.debug(...)` calls to an algorithm | The log sink must be excluded from the observable output set O | **Easy/Moderate** — INTERACTION dimension may reflect additional syscalls |

> **Note on SP-9 and SP-8:** These are "hard" cases by design. They test whether SBG correctly identifies behavioral equivalence even when surface execution characteristics change. They are the most valuable pairs for validating H1.

### 2.2 Semantics-Changing Mutations (SC)

A transformation $M$ is **semantics-changing** if there exists at least one input $i \in \mathcal{I}$ such that:
$$B(M(P), i) \neq B(P, i)$$
By H2, $D(G(P), G(M(P))) > \varepsilon_{\text{detect}}$ should hold on a suitable input sample.

| ID | Type | Formal Definition | Example | Applicability Conditions | Expected SBG Difficulty |
|---|---|---|---|---|---|
| SC-1 | **Off-by-One Error (Boundary Mutation)** | Change loop bound or array index by ±1 | `i < n` → `i <= n` in a loop | Arrays or loops with terminal boundary conditions | **Hard** — behavioral change is narrow; requires boundary-covering inputs |
| SC-2 | **Arithmetic Operator Replacement** | Replace one binary arithmetic operator with another | `a + b` → `a - b`; `a * b` → `a / b` | Numeric computation present | **Easy** — DATA dimension changes on most inputs |
| SC-3 | **Boolean Condition Negation** | Negate a branch condition | `if (x > 0)` → `if (x <= 0)` | Conditional branch present | **Easy** — CONTROL branch probability vector changes immediately |
| SC-4 | **Wrong Comparison Operator** | Replace `<` with `<=` or `==` in a semantic comparison (not boundary — changes semantics on non-boundary inputs) | `if (a == b)` → `if (a != b)` | Comparison expression with non-trivial distribution | **Moderate** — depends on input distribution coverage |
| SC-5 | **Variable Swap (Data Flow Mutation)** | Replace reference to variable $x$ with reference to variable $y$ at one or more use sites | Use `max` instead of `min` as the loop pivot | Two variables of compatible type exist | **Easy to Moderate** — DATA dimension reflects different value distributions |
| SC-6 | **Return Value Change** | Alter a return statement to return a different value or expression | `return index` → `return index + 1` | Function with meaningful return value | **Easy** — observable output changes |
| SC-7 | **Missing Null / Bounds Check** | Delete an explicit guard condition | Remove `if (ptr != null)` before dereference (or equivalent index check) | Guard conditions present | **Hard** — only detectable on inputs that trigger the removed guard path |
| SC-8 | **Loop Termination Condition Change** | Change a loop to terminate early or not terminate on certain inputs | `while (i < n)` → `while (i < n-1)` affecting last element processing | Loops with data-dependent termination | **Moderate** — CONTROL loop iteration distribution shifts |
| SC-9 | **Algorithm Logic Mutation (Step Omission)** | Remove a logically required step from an algorithm | Skip the final merge step in merge sort | Multi-step algorithms | **Hard** — behavioral difference may only appear on complex inputs |
| SC-10 | **Exception Suppression** | Swallow an exception that should propagate | Replace `throw e` with empty catch block | Exception handling code | **Hard** — ERROR dimension detects this only on inputs that trigger the exception path |
| SC-11 | **State Initialization Change** | Alter initial state or variable initialization value | Initialize accumulator to `1` instead of `0` in a sum | Variables with initial value semantics | **Easy** — DATA dimension reflects the shifted distribution |
| SC-12 | **Resource Leak Introduction** | Remove a resource-release call (file close, memory free, lock release) | Remove `file.close()` after file write | Programs using explicit resource management | **Hard** — RESOURCE dimension detects open handles; TEMPORAL may show blocking behavior |
| SC-13 | **Concurrency Mutation (Race Condition)** | Remove a synchronization primitive | Remove `synchronized` block or mutex lock | Concurrent programs (C7) only | **Very Hard** — detectable only under specific thread schedules; requires adversarial scheduling |
| SC-14 | **Cross-language Semantic Port Error** | Introduce a known semantic difference when porting between languages | Python integer division vs. Java integer division (`//` vs `/` for integers); signed vs. unsigned overflow behavior | Cross-language pair (H3 evaluation) | **Hard** — surface behavior looks correct; edge cases reveal the mutation |

### 2.3 Hard Negative Strategy

Hard negatives are semantics-changing pairs where the behavioral difference is narrow (triggered by a small fraction of the input space) and the surface code change is minimal. The benchmark explicitly allocates 30% of SC pairs as hard negatives:

- **SC-1, SC-7, SC-9, SC-10, SC-12, SC-13** are classified as hard negative sources.
- Hard negatives require: (a) the mutation changes behavior on < 10% of a uniform random input sample, and (b) the mutation is detectable with a targeted boundary or adversarial input.
- For each hard negative pair, the benchmark records both the **uniform input detection rate** and the **adversarial input detection rate** as metadata, enabling analysis of SBG's input-distribution sensitivity.

---

## Part 3 — Ground Truth Protocol

### 3.1 Establishing Semantic Equivalence Ground Truth

Semantic equivalence between a pair $(P, P')$ under input distribution $\mathcal{I}$ is established through a **four-tier provenance chain**. Each label is assigned the highest tier achievable for that pair.

| Tier | Method | Confidence | Applicability |
|---|---|---|---|
| **GT-T1: Formal Proof** | Equivalence is proven via a formal verification tool (Godlin & Strichman regression verification, Lahiri et al. SYMDIFF, or manual proof for simple programs). The proof object is stored as part of the label record. | **Definitive** | Applicable only to simple programs (C1 sort variants, C4 numerical, C5 data structures ≤ 200 LOC) in C/C++ or Java where tooling applies |
| **GT-T2: Differential Testing with Complete Input Coverage** | For finite or enumerable input spaces: all inputs are tested and outputs verified identical. For infinite input spaces with a finite symbolic partition: all partitions are tested. | **High (≥ 0.99)** | Applicable to programs where the input space can be partitioned into a finite, tractable set (e.g., sorting programs over inputs with known boundary cases) |
| **GT-T3: Mutation-Controlled Differential Testing** | The transformation is applied by a certified tool (a compiler optimizer, an automated refactoring tool, a proven-correct source transformation) whose semantic preservation is established by the tool's own correctness guarantee. Then differential testing is run on N ≥ 1,000 inputs. | **High (≥ 0.95)** | Applicable to SP transformations applied by certified tools: compiler optimizations (SP-10), automated renaming (SP-1), dead code elimination via certified analysis (SP-6) |
| **GT-T4: Broad Differential Testing + Expert Review** | N ≥ 1,000 inputs drawn from the canonical input distributions are run on both programs; outputs are compared. Expert reviewer audits the transformation for semantic intent. Label is assigned only if zero output discrepancies are observed AND the transformation falls within a known-SP type. | **Moderate (≥ 0.90)** | Applicable when formal tools are unavailable; used for most SP transformations of complex programs |

**Semantic equivalence is DENIED (labeled as SC) if:**
- Any output discrepancy is observed on any test input, regardless of tier, OR
- The transformation type is inherently semantics-changing (per Section 2.2 taxonomy), even without observed discrepancy (the input coverage may have missed the triggering input — the type is sufficient evidence of SC).

**Semantic equivalence is ASSERTED (labeled as SP) if:**
- No output discrepancy is observed on ≥ 1,000 test inputs AND the transformation type is in the SP taxonomy OR the label is supported by GT-T1/GT-T2/GT-T3.

### 3.2 Provenance Chain per Label

Each labeled pair record stores:

```json
{
  "pair_id": "C1-qsort-v1-SP3-001",
  "base_program_id": "C1-qsort-v1",
  "transformed_program_id": "C1-qsort-v1-SP3-001",
  "transformation_type": "SP-3",
  "label": "SP",
  "ground_truth_tier": "GT-T4",
  "confidence": 0.95,
  "test_inputs_run": 2000,
  "output_discrepancies": 0,
  "input_distributions_tested": ["uniform_random", "boundary"],
  "transformation_tool": "manual",
  "expert_reviewer_id": "R-02",
  "formal_proof_artifact": null,
  "date_labeled": "2025-XX-XX",
  "notes": "Two statements with no data dependency swapped; verified by PDG analysis"
}
```

### 3.3 Validation

Labels are validated as follows:

| Label Type | Primary Validator | Secondary Validator |
|---|---|---|
| SP (GT-T1) | Formal tool output (machine-checkable proof) | Second independent formal tool run or manual proof check |
| SP (GT-T2) | Automated exhaustive test runner | Statistical review of input partition coverage |
| SP (GT-T3) | Tool correctness argument (documented) | Differential test run with N ≥ 1,000 inputs |
| SP (GT-T4) | Expert reviewer | Independent second reviewer for any GT-T4 label in test split |
| SC (all) | Differential test showing at least one discrepancy | Reviewed to confirm discrepancy is not a test harness artifact |

**Cross-validation requirement:** A random 10% sample of SP (GT-T4) labels is selected for GT-T2/GT-T3 re-validation after initial labeling. If > 2% of re-validated labels flip, the GT-T4 batch is rejected and must be re-reviewed.

### 3.4 Confidence Levels per Label Type

| Label Type | Confidence Level | Interpretation |
|---|---|---|
| SP (GT-T1) | ≥ 0.999 | Formal proof; label is definitive given tool soundness |
| SP (GT-T2) | ≥ 0.990 | Complete partition test; label is definitive for tested partitions |
| SP (GT-T3) | ≥ 0.950 | Tool correctness + broad testing; small residual risk from tool bugs |
| SP (GT-T4) | ≥ 0.900 | Expert + testing; residual risk from untested input regions |
| SC (triggered) | ≥ 0.999 | At least one observed discrepancy; label is definitive |
| SC (type-only) | ≥ 0.950 | Transformation is definitionally SC per taxonomy; input may not have triggered it |

---

## Part 4 — Dataset Splits

### 4.1 Split Design

The dataset is divided into four non-overlapping splits:

| Split | Fraction | Purpose | Size (pairs) |
|---|---|---|---|
| **Train** | 50% | Model/threshold learning | ~1,600 |
| **Dev** | 15% | Hyperparameter tuning, early stopping | ~480 |
| **Validation** | 15% | Unbiased intermediate evaluation (frozen after initial use) | ~480 |
| **Test** | 20% | Final held-out evaluation; used once | ~640 |

Total pairs targeted: **3,200** (see Section 7 for justification). These are approximate; exact counts depend on base program corpus construction.

### 4.2 Stratification Strategy

Stratification is applied along four axes simultaneously:

1. **Category stratification:** Each split contains programs from all 12 categories proportionally.
2. **Transformation type stratification:** Each split contains pairs from all SP and SC transformation types (22 types total) proportionally.
3. **Difficulty stratification:** Easy / Moderate / Hard / Very Hard labels (per Section 2) are distributed proportionally across splits. The test split must contain ≥ 25% hard or very-hard pairs.
4. **Ground truth tier stratification:** GT-T1 through GT-T4 are proportionally represented; GT-T4 is capped at 40% of the test split to maintain label reliability.

Stratification is implemented as a multi-label stratified split (e.g., iterative stratification per Sechidis et al. 2011).

### 4.3 Leakage Prevention Rules

| Rule | Description |
|---|---|
| **No base program appears in both train and test** | All pairs derived from the same base program $P$ are assigned to a single split. The split assignment is made at the base program level, not at the pair level. |
| **No transformation-symmetric pairs** | If $(P, P')$ appears in train, then $(P', P)$ (which may be constructed as a separate pair with the same label) does not appear in test. |
| **No shared sub-algorithms** | Two base programs from different categories that share a non-trivial sub-component (e.g., the same sort implementation used internally) are tracked; if one is in train, the other may still be in test only if the shared component is not the subject of any transformation in those pairs. |
| **Cross-language pairs are treated as single units** | For H3 pairs $(P_{\text{Python}}, P_{\text{Java}})$, both members of the pair are assigned to the same split. |
| **Validation and test splits are frozen** | Once initially populated, the validation and test splits are sealed and not modified regardless of corpus additions. Additional programs extend only the train/dev splits. |

### 4.4 Class Balance Requirements

| Split | Target SP:SC Ratio | Tolerance |
|---|---|---|
| Train | 1:1 | ±10% |
| Dev | 1:1 | ±10% |
| Validation | 1:1 | ±5% |
| Test | 1:1 | ±5% |

**Rationale:** Balanced classes are required for unambiguous precision/recall interpretation at a fixed threshold. If natural pair generation produces imbalance, the minority class is oversampled (at the transformation level, not by duplicating programs) until balance is achieved.

Hard negatives (30% of SC pairs) must be present in train, validation, and test splits to ensure the system is evaluated on narrow behavioral differences, not just gross mutations.

---

## Part 5 — Pair Construction

### 5.1 Positive Pairs (Semantics-Preserving)

A positive pair $(P, P')$ is constructed as:
1. Select a base program $P$ from the corpus.
2. Select a transformation type $T_k$ from the SP taxonomy (SP-1 through SP-12).
3. Apply $T_k$ to $P$ to obtain $P'$, ensuring the applicability conditions for $T_k$ are met.
4. Run the ground truth protocol (Part 3) to assign a label and confidence.
5. Accept the pair only if the label is SP with confidence ≥ 0.90.

**Constraints on positive pair diversity:**
- No single base program contributes more than 8 positive pairs (one per applicable SP type; not all types apply to all programs).
- No more than 3 positive pairs from the same (base program, transformation type) combination (i.e., three distinct applications of SP-3 to the same program are acceptable if the swapped statement pairs are distinct; a fourth is not).
- For each SP type, at least 10% of positive pairs must involve "hard" SP cases (SP-8, SP-9, SP-10) to prevent type collapse.

### 5.2 Negative Pairs (Semantics-Changing)

A negative pair $(P, P')$ is constructed as:
1. Select a base program $P$ from the corpus.
2. Select a mutation type $M_k$ from the SC taxonomy (SC-1 through SC-14).
3. Apply $M_k$ to $P$ to produce mutant $P'$.
4. Run a differential test to confirm at least one input $i$ produces $B(P', i) \neq B(P, i)$.  
   - For easy SC types (SC-2, SC-3, SC-6, SC-11): this is confirmed by automated test.
   - For hard SC types (SC-1, SC-7, SC-9, SC-10, SC-12, SC-13): a targeted boundary or adversarial input must be constructed and documented.
5. Accept the pair with label SC.

**Constraints on negative pair construction:**
- Equivalent constraint: no single base program contributes more than 8 negative pairs.
- Mutation must be a minimal change (mutant should differ from the original in ≤ 5 lines of code) to ensure the mutation is the sole source of behavioral difference.
- Cross-program negative pairs (where $P$ and $P'$ are drawn from different base programs) are also included to evaluate H6 (genome uniqueness). These are labeled SC but flagged as "cross-program" in metadata.

### 5.3 Hard Negatives Strategy

Hard negatives are systematically constructed to stress-test SBG's sensitivity (H2) on narrow behavioral differences:

**Construction procedure:**
1. Apply a hard SC mutation type (SC-1, SC-7, SC-9, SC-10, SC-12, SC-13) to base program $P$.
2. Compute the **detection rate** $r_{\text{uniform}}$: fraction of 1,000 uniform random inputs that produce a detectable output difference.
3. Accept as a hard negative only if $r_{\text{uniform}} < 0.10$ (behavioral difference is narrow).
4. Construct a **witness input** $i^*$ that triggers the behavioral difference, and record it in the pair metadata.
5. Record $r_{\text{adversarial}}$: detection rate when the adversarial/boundary input distribution is used.

**Hard negative metadata:**
```json
{
  "hard_negative": true,
  "mutation_type": "SC-7",
  "detection_rate_uniform": 0.03,
  "detection_rate_adversarial": 0.95,
  "witness_input": "<encoded input>",
  "detection_input_distribution": "boundary"
}
```

**Hard negative allocation:**
- 30% of all SC pairs are hard negatives: ~480 hard negative pairs in total dataset.
- At least 20% of test split SC pairs are hard negatives.

### 5.4 Pair Diversity Requirements

| Dimension | Requirement |
|---|---|
| **Category coverage** | Every (category, SP-type) and (category, SC-type) combination that is applicable must appear at least once in the full dataset |
| **Language pair coverage** | For cross-language pairs: at least 6 language pairs represented (Python-Java, Python-C, Java-C, Python-Go, Java-Rust, C-Go) |
| **Scale coverage** | At least 20% of pairs in each size class (small/medium/large) |
| **Ground truth tier coverage** | Test split must contain at least 5% GT-T1 and 10% GT-T2 pairs |
| **Transformation chain pairs** | At least 50 pairs where $P'$ is produced by a composition of two transformations (e.g., SP-1 followed by SP-3) to test transitivity |

---

## Part 6 — Quality Metrics

### 6.1 Benchmark Quality Measurement

The benchmark's own quality is evaluated along four axes:

**Q1 — Label Reliability (LR):**  
$$\text{LR} = \frac{|\text{pairs with confirmed label via cross-validation}|}{|\text{total pairs}|}$$  
Target: LR ≥ 0.95 overall; LR ≥ 0.90 for GT-T4 pairs.

**Q2 — Difficulty Distribution Balance (DDB):**  
Measured as the entropy of the difficulty class distribution (Easy/Moderate/Hard/Very Hard):
$$\text{DDB} = -\sum_{d} p_d \log p_d$$
Target: DDB ≥ 1.5 nats (indicates at least 4 roughly balanced difficulty classes). A benchmark with all Easy pairs has DDB ≈ 0 and is rejected.

**Q3 — Type Coverage Score (TCS):**  
$$\text{TCS} = \frac{|\text{(category, transformation type) pairs represented}|}{|\text{(category, transformation type) pairs applicable}|}$$  
Target: TCS ≥ 0.80. Every applicable combination should appear.

**Q4 — Hard Negative Discriminability (HND):**  
For hard negative pairs, the difference between adversarial and uniform detection rates:
$$\text{HND} = \frac{1}{|HN|} \sum_{p \in HN} (r_{\text{adversarial}}(p) - r_{\text{uniform}}(p))$$  
Target: HND ≥ 0.70. This confirms hard negatives are genuinely hard under uniform inputs but detectable under adversarial inputs, making them meaningful discriminative challenges.

### 6.2 Diversity Metrics

| Metric | Measurement | Target |
|---|---|---|
| **Category entropy** | Shannon entropy of category distribution in each split | ≥ 2.3 nats (≈ uniform over 12 categories) |
| **Language diversity** | Number of distinct languages in corpus | ≥ 6 |
| **SP type coverage** | Fraction of SP types with ≥ 10 pairs each | ≥ 0.90 |
| **SC type coverage** | Fraction of SC types with ≥ 10 pairs each | ≥ 0.90 |
| **Pairwise program similarity** | Mean pairwise LOC-normalized edit distance between base programs within the same category | ≥ 0.30 (prevents redundant near-duplicates) |

### 6.3 Difficulty Distribution Targets

The benchmark targets the following difficulty distribution across all pairs:

| Difficulty | Target Fraction | Definition |
|---|---|---|
| Easy | 25% | SC pairs where $r_{\text{uniform}} > 0.50$; SP pairs from SP-1, SP-2, SP-4, SP-5 |
| Moderate | 35% | SC pairs where $0.10 \leq r_{\text{uniform}} \leq 0.50$; SP pairs from SP-3, SP-6, SP-7, SP-11 |
| Hard | 30% | SC hard negatives ($r_{\text{uniform}} < 0.10$); SP pairs from SP-8, SP-10 |
| Very Hard | 10% | SC-13 (concurrency race), SP-9 (algorithm substitution), cross-language SC-14 |

**Rationale:** This distribution ensures the benchmark does not collapse to trivial difficulty (pure Easy) while keeping Very Hard at 10% to avoid domination by noisy or ambiguous cases.

---

## Part 7 — Minimum Viable Benchmark

### 7.1 Exact Minimum Counts with Statistical Justification

**Required statistical properties:**
1. ±0.05 margin on precision/recall at 95% confidence in the test split.
2. Ability to detect a 0.10 difference between two systems with power ≥ 0.80 (two-sided McNemar test) at Bonferroni-corrected α = 0.0017 (= 0.01/6, for 6 hypotheses H1–H6).
3. Sufficient hard negatives to evaluate narrow-difference sensitivity.

**Derivation:**

**(a) Test set size for precision/recall margin:**
Per Section 1.5: 384 pairs needed for ±0.05 margin at 95% confidence (conservative: $p = 0.5$).
Round up to **400 test pairs** for a safety margin.

**(b) Test set size for McNemar (system comparison) — Bonferroni-corrected α = 0.0017:**

All H1–H6 experiments use Bonferroni-corrected α = 0.01/6 = **0.0017** (not α = 0.05).
The critical z-value at α/2 = 0.00085 is z_{α/2} ≈ **3.12** (two-sided).

**Calculation:**

McNemar minimum discordant pairs at power = 0.80, two-sided:

$$n_\text{discordant} \geq \left(\frac{z_{\alpha/2} + z_\beta}{\delta}\right)^2$$

where $z_\beta = 0.842$ (power = 0.80) and $\delta$ is the effect size among discordant pairs.

- At **α = 0.05**: $(1.960 + 0.842)^2 / 1^2 \approx 7.85$ — requires ~32 discordant pairs for a large effect, or ~80 discordant pairs for 10% system difference (concordance rate 80% → 400 total pairs).
- At **α = 0.0017**: $(3.120 + 0.842)^2 / 1^2 \approx 15.70$ — the required discordant pairs scale by ratio $15.70 / 7.85 \approx 2.0$.

Scaling from the α = 0.05 baseline: ~80 discordant pairs × 2.0 = **~160 discordant pairs** required.
At 20% discordance rate: 160 / 0.20 = **800 minimum test pairs** at α = 0.0017.

For 5% system difference detection at α = 0.0017: 1,600 × 2.0 = **3,200 test pairs** recommended.

**We accept 800 test pairs as the minimum viable position and acknowledge this is powered for 10% system differences at α = 0.0017. The original 400-pair figure was derived at α = 0.05 and is insufficient under the Bonferroni-corrected threshold.**

**(c) Train/dev/validation scaling:**
Given 800 test pairs at 20%: total dataset = 4,000 pairs minimum.
Train: 2,000, Dev: 600, Validation: 600, Test: 800.

**(d) Hard negatives:**
30% of SC pairs = 30% of 2,000 SC pairs = 600 hard negatives. At 20% in test: 120 hard negative test pairs. This is sufficient for a paired Wilcoxon test on narrow-difference sensitivity.

**Minimum Viable Benchmark — Summary:**

| Component | Minimum Count | Justification |
|---|---|---|
| Base programs | 50 | Minimum to achieve category × language coverage; 78 is recommended |
| SP pairs total | 2,000 | 1,000 train + 300 dev + 300 val + 400 test |
| SC pairs total | 2,000 | 1,000 train + 300 dev + 300 val + 400 test |
| Hard negative SC pairs | 600 | 30% of 2,000 SC; 120 in test |
| Transformation types covered (SP) | ≥ 10 of 12 | Minimum coverage of SP taxonomy |
| Transformation types covered (SC) | ≥ 10 of 14 | Minimum coverage of SC taxonomy |
| GT-T1/T2 labeled pairs | ≥ 200 | At least 5% of total for anchor calibration |
| Categories represented | All 12 | Non-negotiable for coverage validity |
| Languages | ≥ 6 | Minimum for H4 evaluation |

**Recommended corpus (statistically powered for 5% system differences at α = 0.0017):**

| Component | Recommended Count |
|---|---|
| Base programs | 78 |
| SP pairs total | 3,200 |
| SC pairs total | 3,200 |
| Hard negative SC pairs | 960 |
| Total pairs | 6,400 |
| Test pairs | 1,280 |

### 7.2 Why These Numbers Are Not Inflated

- The 78 base program count is derived from category × diversity requirements, not from a round number.
- The pair count is derived from the McNemar power analysis at Bonferroni-corrected α = 0.0017 (= 0.01/6), not from "more is always better." The doubling from the original α = 0.05 baseline is a direct consequence of the corrected significance threshold required for 6 simultaneous hypothesis tests.
- The minimum viable benchmark (4,000 pairs, 50 programs, 800 test pairs) is explicitly stated as valid but powered only for 10% system differences at α = 0.0017.
- Hard negative count (30%) is derived from the need to evaluate narrow-difference detection, not from aesthetic preference.

---

## Part 8 — Implementation Notes and Constraints

### 8.1 Determinism Enforcement

All base programs and their transformations must be run under the determinism policy of Assumption A6:
- Fixed PRNG seed (seed = 42 as canonical default).
- Fixed thread scheduler policy for C7 programs (serialized execution order where possible; deterministic round-robin otherwise).
- Fixed locale and timezone (UTF-8, UTC).
- Fixed floating-point rounding mode (IEEE 754 round-to-nearest-even).

Programs that cannot be made deterministic under these constraints are excluded per Section 1.4.

### 8.2 Test Harness Requirements

The test harness must:
1. Execute $P$ and $P'$ with identical inputs from the same input stream.
2. Capture all observable outputs: stdout, stderr, exit code, file outputs (listed in the oracle definition for that program category).
3. For C6/C11 programs: capture the system call trace (INTERACTION dimension) as part of the oracle.
4. Record execution time and peak memory usage for TEMPORAL/RESOURCE ground truth metadata (not used for the binary SP/SC label, but used for dimension-level analysis).
5. Apply a timeout $T_{\max}$ = 30 seconds per run (per Assumption A5).

### 8.3 Tooling Recommendations

| Task | Recommended Tool | Notes |
|---|---|---|
| Formal equivalence (GT-T1) | Godlin-Strichman regression verifier; SYMDIFF; Frama-C Wp plugin | C/C++ programs only; simple to moderate complexity |
| Differential testing | AFL++ in comparison mode; custom harness | 1,000+ inputs per pair |
| Input generation | AFL++, libFuzzer, manual boundary cases | Combine coverage-guided and boundary inputs |
| Mutation application | PIT (Java), mutmut (Python), custom AST transformer | Must record exact mutation coordinates |
| PDG analysis for SP-3 | Joern, Soot, custom PDG | Required to verify statement independence |
| Dataset split stratification | scikit-multilearn iterative stratification | Multi-label stratification |

---

## Summary Tables

### Transformation Type Quick Reference

| Type | ID | Expected Difficulty | SBG Dimension Most Stressed |
|---|---|---|---|
| Rename | SP-1 | Easy | None (syntactic only) |
| Comment change | SP-2 | Easy | None |
| Reorder independent stmts | SP-3 | Moderate | TEMPORAL |
| Loop normalization | SP-4 | Easy | CONTROL |
| Constant folding | SP-5 | Easy | DATA |
| Dead code elimination | SP-6 | Moderate | EXECUTION |
| Extract/inline method | SP-7 | Moderate | CONTROL |
| Equiv. data structure | SP-8 | Hard | STATE, RESOURCE |
| Algorithm substitution | SP-9 | Very Hard | CONTROL, DATA, TEMPORAL |
| Compiler optimization | SP-10 | Hard | EXECUTION, TEMPORAL |
| Exception refactor | SP-11 | Moderate | ERROR |
| Logging addition | SP-12 | Easy/Moderate | INTERACTION |
| Off-by-one | SC-1 | Hard | CONTROL, DATA |
| Arithmetic op replace | SC-2 | Easy | DATA |
| Boolean negation | SC-3 | Easy | CONTROL |
| Wrong comparison op | SC-4 | Moderate | CONTROL |
| Variable swap | SC-5 | Moderate | DATA |
| Return value change | SC-6 | Easy | DATA, INTERACTION |
| Missing guard | SC-7 | Hard | ERROR, CONTROL |
| Loop termination change | SC-8 | Moderate | CONTROL |
| Algorithm step omission | SC-9 | Hard | CONTROL, DATA |
| Exception suppression | SC-10 | Hard | ERROR |
| State init change | SC-11 | Easy | DATA, STATE |
| Resource leak | SC-12 | Hard | RESOURCE |
| Concurrency mutation | SC-13 | Very Hard | TEMPORAL, EXECUTION |
| Cross-language port error | SC-14 | Hard | DATA, INTERACTION |

---

## Provenance

- **Formal model:** FORMAL_MODEL.md (Agent 0B) — Definitions 1–22, Hypotheses H1–H6, Assumptions A1–A10
- **Prior art:** PRIOR_ART_MATRIX.md (Agent 0A) — mutation testing foundations [27–29], regression verification [16, 19], differential testing methodology
- **Statistical methodology:** Standard power analysis for McNemar test; proportion estimation per Fleiss et al.
- **Ground truth tier design:** Inspired by Godlin & Strichman GT-T1/T2; Defects4J [28] for GT-T4 pattern

---

*End of BENCHMARK_DESIGN.md — Agent 0F*
