# Formal Mathematical Model — Software Behavior Genome (SBG)

**Agent:** 0B  
**Date:** 2025  
**Status:** Working draft — definitions are precise where theory permits; approximations and idealizations are explicitly flagged.

---

## Preamble

This document provides the mathematical foundation for the Software Behavior Genome (SBG) project. It defines all primary objects, functions, relations, and hypotheses in precise notation. Where complete formalization is not currently achievable (e.g., due to undecidability, oracle problems, or engineering trade-offs), the approximation is named and its consequences stated.

**Notation conventions:**

- Sets are denoted by calligraphic capitals: $\mathcal{P}, \mathcal{I}, \mathcal{G}$
- Functions are denoted by Greek or Roman letters: $\tau, \Phi, D$
- Sequences are angle-bracketed: $\langle a_1, a_2, \ldots, a_n \rangle$
- Multisets are denoted with double braces: $\{\!\{ \cdot \}\!\}$
- Power sets: $2^X$
- The set of all finite sequences over $X$: $X^*$
- The set of non-negative reals: $\mathbb{R}_{\geq 0}$
- The closed unit interval: $[0, 1]$
- Partial functions: $f : X \rightharpoonup Y$

---

## Part I — Core Objects

### Definition 1 — Computational Environment $\mathcal{E}$

A **computational environment** is a tuple:

$$\mathcal{E} = \langle \mathcal{OS}, \mathcal{HW}, \mathcal{RT}, \mathcal{L}, \mathcal{SYS} \rangle$$

where:

- $\mathcal{OS}$ is the operating system identity (name, version, kernel version)
- $\mathcal{HW}$ is the hardware profile (ISA, word size, memory model, clock)
- $\mathcal{RT}$ is the runtime environment (interpreter version, JVM version, native ABI)
- $\mathcal{L}$ is the set of loaded shared libraries with versions
- $\mathcal{SYS}$ is the system configuration state (locale, timezone, file system layout)

> **Assumption A1 (Environment Stability):** For any single execution, $\mathcal{E}$ is fixed and does not change during program execution. This excludes hot-patching, live kernel module updates, and hardware faults.

---

### Definition 2 — Program $P$

A **program** is a tuple:

$$P = \langle \Sigma, \mathcal{Q}, q_0, \delta, F, \mathcal{M}, \mathcal{A}, \mathcal{E}_P \rangle$$

where:

- $\Sigma$ is the alphabet of observable input/output values
- $\mathcal{Q}$ is the (possibly infinite, possibly uncountable) set of internal states
- $q_0 \in \mathcal{Q}$ is the initial state (parameterized by input)
- $\delta : \mathcal{Q} \times \Sigma \rightharpoonup \mathcal{Q}$ is the (partial) transition function
- $F \subseteq \mathcal{Q}$ is the set of accepting/terminal states
- $\mathcal{M}$ is the memory model (address space layout, heap allocator, stack discipline)
- $\mathcal{A}$ is the set of observable side effects (system calls, IPC, network, file I/O)
- $\mathcal{E}_P \in \mathcal{E}$ is the environment against which $P$ was compiled or interpreted

> **Note N1 (Idealization):** This definition abstracts over implementation details. In practice $P$ is represented as a source artifact, bytecode, or machine-code binary. The abstract state space $\mathcal{Q}$ may be non-computable in its full generality. All practical SBG computations operate on finite approximations obtained from execution traces (see Definition 4).

> **Notation:** $\mathcal{P}$ denotes the universe of all well-formed programs over a fixed $\mathcal{E}$.

---

### Definition 3 — Program Version History $\mathcal{H}(P)$

For a software artifact with identity $\mathbf{id}$, its **version history** is:

$$\mathcal{H}(P) = \langle P^{(0)}, P^{(1)}, \ldots, P^{(n)} \rangle$$

a totally ordered sequence of programs indexed by release time $t^{(0)} < t^{(1)} < \cdots < t^{(n)}$, where each $P^{(k)}$ is as in Definition 2 and shares the semantic intent of $\mathbf{id}$.

> **Assumption A2 (Identity Continuity):** The mapping from version index to semantic intent is given externally (e.g., by repository history, package registries). SBG does not define what makes two versions "of the same program" — it accepts this as a human-supplied relation.

---

### Definition 4 — Input Distribution $\mathcal{I}$

An **input distribution** for program $P$ is a probability space:

$$\mathcal{I} = \langle \Omega_I, \mathcal{F}_I, \mu_I \rangle$$

where:

- $\Omega_I$ is the input sample space (the set of all valid inputs to $P$)
- $\mathcal{F}_I \subseteq 2^{\Omega_I}$ is a $\sigma$-algebra over $\Omega_I$
- $\mu_I : \mathcal{F}_I \to [0, 1]$ is a probability measure with $\mu_I(\Omega_I) = 1$

An individual input is $i \sim \mu_I$, denoted $i \in \mathcal{I}$ by abuse of notation.

**Canonical input distributions:**

| Name | Definition | Use case |
|---|---|---|
| Uniform random $\mathcal{I}_U$ | $\mu_I$ is the uniform measure over $\Omega_I$ | Theoretical baseline |
| Production trace $\mathcal{I}_\text{prod}$ | $\mu_I$ estimated from logged production inputs | Behavioral fidelity |
| Coverage-guided $\mathcal{I}_\text{cov}$ | $\mu_I$ shaped by coverage feedback (e.g., AFL) | Rare-path exposure |
| Adversarial $\mathcal{I}_\text{adv}$ | $\mu_I$ concentrates on boundary/edge inputs | Stress testing |

> **Assumption A3 (Input Independence):** Individual inputs $i_1, i_2, \ldots$ drawn from $\mathcal{I}$ are mutually independent. This excludes session-stateful protocols without explicit session modeling.

> **Assumption A4 (Input Measurability):** $\Omega_I$ is a measurable space. For programs accepting arbitrary byte strings, $\Omega_I = \{0,1\}^*$ with the Borel $\sigma$-algebra over the Cantor space topology.

---

### Definition 5 — Execution Trace $\tau(P, i)$

For program $P$ and input $i \in \mathcal{I}$, the **execution trace** is:

$$\tau(P, i) = \langle e_1, e_2, \ldots, e_k \rangle \in \mathcal{T}^*$$

where each **trace event** $e_j \in \mathcal{T}$ is a tuple:

$$e_j = \langle \ell_j,\ op_j,\ v_j^\text{in},\ v_j^\text{out},\ \sigma_j,\ t_j \rangle$$

with components:

- $\ell_j \in \mathcal{L}$ — program location (file, procedure, line, basic block, or bytecode offset)
- $op_j \in \mathcal{OP}$ — operation type (arithmetic, comparison, branch, call, return, load, store, syscall, ...)
- $v_j^\text{in} \in \mathcal{V}^*$ — sequence of input values to the operation
- $v_j^\text{out} \in \mathcal{V}$ — output value produced (or $\bot$ for void operations)
- $\sigma_j \in \mathcal{Q}$ — program state snapshot at $e_j$ (register file + heap digest + stack frame)
- $t_j \in \mathbb{R}_{\geq 0}$ — wall-clock timestamp

**Side-effect events:** For system calls and external interactions, $e_j$ is extended with:

$$e_j^{\text{ext}} = \langle e_j,\ \text{syscall\_nr},\ \text{args},\ \text{return\_code},\ \text{errno} \rangle$$

**Termination:** A trace $\tau(P, i)$ is:
- **Normal** if the last event $e_k$ corresponds to a state $q_k \in F$
- **Abnormal** if execution halts with an exception, signal, or timeout
- **Divergent** (denoted $\tau(P, i) = \bot$) if $P$ does not terminate on $i$

> **Assumption A5 (Finite Traces):** All traces considered in SBG are finite. Divergent executions ($\tau = \bot$) are excluded from genome extraction. This is an idealization: in practice a timeout $T_\max$ is imposed and $\tau(P, i)$ is truncated at $T_\max$.

> **Assumption A6 (Determinism):** For a fixed input $i$ and environment $\mathcal{E}$, the trace $\tau(P, i)$ is deterministic. Programs with internal non-determinism (PRNG, concurrent threads) require a **canonical execution policy** (fixed seed, serialized scheduling) as an additional parameter.

---

### Definition 6 — Observable Behavior $B(P, \mathcal{I})$

The **observable behavior** of program $P$ under input distribution $\mathcal{I}$ is the function:

$$B(P, \mathcal{I}) : \Omega_I \to \mathcal{O}$$

where $\mathcal{O}$ is the **observation domain**:

$$\mathcal{O} = \mathcal{O}_{\text{output}} \times \mathcal{O}_{\text{side-effect}} \times \mathcal{O}_{\text{resource}} \times \mathcal{O}_{\text{temporal}}$$

with:

- $\mathcal{O}_{\text{output}}$: the final output values produced (return codes, written bytes, printed strings)
- $\mathcal{O}_{\text{side-effect}}$: the ordered sequence of observable side effects (file writes, network packets, signal deliveries)
- $\mathcal{O}_{\text{resource}}$: resource consumption profile (CPU cycles, memory peak, file descriptors opened)
- $\mathcal{O}_{\text{temporal}}$: timing profile (inter-event latencies, total wall time)

**Observable behavior distribution:** Since $i \sim \mu_I$, the observable behavior is a random variable:

$$\mathbf{B}(P, \mathcal{I}) = B(P, \cdot) \circ \mu_I$$

> **Remark R1:** Two programs $P, P'$ are **extensionally equivalent** if $B(P, \mathcal{I}) = B(P', \mathcal{I})$ pointwise for all $i$. This is stronger than the semantic equivalence relation $\equiv_S$ defined in Definition 16.

> **Remark R2:** $B(P, \mathcal{I})$ is **unobservable in full generality** due to Rice's theorem and the oracle problem. SBG approximates $B(P, \mathcal{I})$ from a finite sample of traces. All subsequent definitions refer to this finite approximation unless stated otherwise.

---

## Part II — Genome Structure

### Definition 7 — Genome Extraction Function $\Phi$

The **genome extraction function** is:

$$\Phi : \mathcal{P} \times \mathcal{I} \to \mathcal{G}$$

defined as:

$$\Phi(P, \mathcal{I}) = \mathcal{A}\!\left(\left\{\!\!\left\{ \phi\!\left(\tau(P, i)\right) : i \sim \mu_I,\ i \in \mathcal{S} \right\}\!\!\right\}\right)$$

where:

- $\mathcal{S} \subseteq \Omega_I$ is a finite sample of $N$ inputs drawn from $\mathcal{I}$ (i.e., $|\mathcal{S}| = N$)
- $\phi : \mathcal{T}^* \to \mathcal{G}_\text{raw}$ is the **trace projection function** mapping a single trace to a raw feature vector
- $\mathcal{A} : \mathcal{G}_\text{raw}^N \to \mathcal{G}$ is the **aggregation operator** (see Definition 21)

**Decomposition:** $\Phi$ decomposes along the 8 genome dimensions (Definitions 9–17):

$$\Phi(P, \mathcal{I}) = \langle \Phi_C, \Phi_D, \Phi_S, \Phi_R, \Phi_T, \Phi_E, \Phi_X, \Phi_U \rangle$$

where subscripts denote CONTROL, DATA, STATE, RESOURCE, TEMPORAL, ERROR, INTERACTION, EXECUTION respectively.

> **Assumption A7 (Sample Sufficiency):** The sample size $N$ is large enough that the empirical distribution over traces converges to the true distribution in each genome dimension. Formally: $\|\hat{\mu}_N - \mu_I\|_\text{TV} \leq \epsilon$ for some acceptable total-variation tolerance $\epsilon > 0$. The required $N$ is dimension-dependent and program-dependent; no universal bound is claimed.

---

### Definition 8 — Genome $G(P)$

The **behavioral genome** of program $P$ under distribution $\mathcal{I}$ is:

$$G(P) = \Phi(P, \mathcal{I}) \in \mathcal{G}$$

The **genome space** $\mathcal{G}$ is the Cartesian product of 8 dimension spaces:

$$\mathcal{G} = \mathcal{G}_C \times \mathcal{G}_D \times \mathcal{G}_S \times \mathcal{G}_R \times \mathcal{G}_T \times \mathcal{G}_E \times \mathcal{G}_X \times \mathcal{G}_U$$

Each component space carries its own metric (see Definition 18). The genome is written as an 8-tuple:

$$G(P) = \langle g_C,\ g_D,\ g_S,\ g_R,\ g_T,\ g_E,\ g_X,\ g_U \rangle$$

> **Remark R3:** $G(P)$ is implicitly parameterized by $\mathcal{I}$ and $\mathcal{E}_P$. When comparing genomes, both must be held fixed or explicitly normalized (see Definition 22).

---

## Part III — The 8 Genome Dimensions

### Definition 9 — CONTROL Dimension $g_C$

The **CONTROL dimension** characterizes the control-flow structure of $P$'s execution.

**Raw features from trace $\tau$:**

- **Execution frequency vector:** $f_C : \mathcal{L} \to \mathbb{R}_{\geq 0}$, where $f_C(\ell)$ = normalized visit count of location $\ell$
- **Branch probability vector:** $p_C : \mathcal{B} \to [0,1]$, where $\mathcal{B}$ is the set of conditional branches and $p_C(b)$ = empirical probability of taking the true branch at $b$
- **Dynamic call graph:** $\text{DCG}(P, i) = (V, E)$, where $V$ = called procedures, $E$ = observed caller–callee edges with multiplicities
- **Loop iteration distribution:** for each back-edge $e \in \mathcal{B}_\text{back}$, a distribution over iteration counts $k \in \mathbb{N}$

**Aggregated CONTROL feature:**

$$g_C = \left\langle \bar{f}_C,\ \bar{p}_C,\ \overline{\text{DCG}},\ \bar{\Lambda} \right\rangle$$

where bars denote aggregation over $\mathcal{S}$ (see Definition 21) and $\bar{\Lambda}$ is the vector of mean loop iteration counts.

**Space:** $\mathcal{G}_C \subseteq \mathbb{R}^{|\mathcal{L}|} \times [0,1]^{|\mathcal{B}|} \times \mathcal{G}_\text{graph} \times \mathbb{R}^{|\mathcal{B}_\text{back}|}$

---

### Definition 10 — DATA Dimension $g_D$

The **DATA dimension** characterizes value flows and computational patterns.

**Raw features from trace $\tau$:**

- **Value range histograms:** for each defined variable or register $x$, a histogram $H_x$ over the empirical distribution of $x$'s values across the trace
- **Data-flow edge activation:** $\text{DFA} : \mathcal{L} \times \mathcal{L} \to \mathbb{R}_{\geq 0}$, where $\text{DFA}(\ell_1, \ell_2)$ = frequency of observed def-use chains from $\ell_1$ to $\ell_2$
- **Type frequency:** $\text{TF} : \mathcal{T}_\text{type} \to \mathbb{R}_{\geq 0}$, count of values belonging to each primitive type
- **Null/zero prevalence:** $\text{NZP} : \mathcal{L} \to [0,1]$, fraction of executions where $\ell$ produces null or zero

**Aggregated DATA feature:**

$$g_D = \left\langle \overline{H},\ \overline{\text{DFA}},\ \overline{\text{TF}},\ \overline{\text{NZP}} \right\rangle$$

**Space:** $\mathcal{G}_D$ — a space of empirical distributions and frequency maps.

> **Remark R4:** Full value distributions are expensive to store. In practice, $H_x$ is compressed to moments (mean, variance, skewness) or quantile summaries (e.g., $t$-digest). This is an **engineering approximation** of the idealized definition.

---

### Definition 11 — STATE Dimension $g_S$

The **STATE dimension** characterizes heap and memory state evolution.

**Raw features from trace $\tau$:**

- **Heap topology sequence:** $\text{HTS}(\tau) = \langle h_0, h_1, \ldots, h_k \rangle$ where $h_j$ is an abstract heap graph snapshot at event $e_j$ (nodes = live heap objects, edges = pointer references, labels = types and sizes)
- **Stack depth profile:** $\text{SDP} : \mathbb{N} \to \mathbb{R}_{\geq 0}$, empirical distribution over call-stack depths
- **State transition frequency:** $\text{STF} : \mathcal{Q}_\text{abs} \times \mathcal{Q}_\text{abs} \to \mathbb{R}_{\geq 0}$, where $\mathcal{Q}_\text{abs}$ is an abstract state space (e.g., heap-size buckets, active-flag tuples)
- **Heap growth rate:** $\gamma = |\text{live objects at }e_k| / |\text{live objects at }e_1|$ (scalar per trace)

**Aggregated STATE feature:**

$$g_S = \left\langle \overline{\text{HTS}}_\text{abs},\ \overline{\text{SDP}},\ \overline{\text{STF}},\ \bar{\gamma} \right\rangle$$

where $\overline{\text{HTS}}_\text{abs}$ uses the **abstract heap summary** (e.g., shape graph or reference-counting summary) rather than raw pointer values, to achieve portability across runs.

**Space:** $\mathcal{G}_S$ — a space of abstract heap summaries and distribution vectors.

> **Assumption A8 (Heap Abstraction Soundness):** The chosen heap abstraction $\mathcal{Q}_\text{abs}$ is **sufficiently expressive** to distinguish programs with meaningfully different memory behaviors. The choice of abstraction is a tunable parameter of the SBG system and is not fixed by this definition.

---

### Definition 12 — RESOURCE Dimension $g_R$

The **RESOURCE dimension** characterizes consumption of computational resources.

**Raw features from trace $\tau$:**

- **CPU instruction count:** $\text{IC}(\tau) = |\tau|$ (trace length as proxy for compute work)
- **Memory peak:** $\text{MEM}_\text{peak}(\tau) = \max_{j} |\text{live heap}(\sigma_j)|$ (in bytes)
- **I/O volume:** $\text{IOV}(\tau) = \sum_{j : op_j \in \mathcal{OP}_\text{IO}} |v_j^\text{in}|$ (bytes transferred)
- **System call count vector:** $\text{SCV} : \text{syscalls} \to \mathbb{N}$, count per system call number
- **File descriptor count:** $\text{FDC}(\tau)$, peak file descriptor usage
- **Network byte count:** $\text{NBC}(\tau)$ (if applicable)

**Aggregated RESOURCE feature:**

$$g_R = \left\langle \bar{\text{IC}},\ \bar{\text{MEM}}_\text{peak},\ \bar{\text{IOV}},\ \overline{\text{SCV}},\ \bar{\text{FDC}},\ \bar{\text{NBC}} \right\rangle \in \mathbb{R}^{m_R}$$

for $m_R = 4 + |\text{syscalls}|$ dimensions.

**Space:** $\mathcal{G}_R \subseteq \mathbb{R}_{\geq 0}^{m_R}$

> **Note N2:** Resource features are environment-dependent ($\mathcal{E}$-sensitive). Comparisons across different hardware require normalization (see Definition 22).

---

### Definition 13 — TEMPORAL Dimension $g_T$

The **TEMPORAL dimension** characterizes the timing structure of execution.

**Raw features from trace $\tau$:**

- **Inter-event latency distribution:** $\text{IEL}(\tau)$, the empirical distribution over $\{t_{j+1} - t_j : j = 1,\ldots,k-1\}$
- **Phase timing:** $\text{PT} : \mathcal{L}_\text{phase} \to \mathbb{R}_{\geq 0}$, time spent in each identified phase (e.g., initialization, main loop, teardown)
- **Call latency vector:** $\text{CLV} : V_\text{proc} \to \mathbb{R}_{\geq 0}$, mean inclusive execution time per procedure $v \in V_\text{proc}$
- **Total execution time:** $T_\text{total}(\tau) = t_k - t_1$

**Aggregated TEMPORAL feature:**

$$g_T = \left\langle \overline{\text{IEL}},\ \overline{\text{PT}},\ \overline{\text{CLV}},\ \bar{T}_\text{total} \right\rangle$$

**Space:** $\mathcal{G}_T$ — a space of distributions and non-negative real vectors.

> **Assumption A9 (Clock Resolution):** Timestamps $t_j$ are measured with sufficient resolution that $t_{j+1} > t_j$ for most consecutive events. Sub-nanosecond resolution is assumed available; jitter from OS scheduling is treated as noise.

> **Remark R5:** TEMPORAL features are highly sensitive to $\mathcal{E}$ (hardware speed, OS load). **Relative temporal features** (ratios of phase times, normalized latency distributions) are preferred for cross-environment comparisons.

---

### Definition 14 — ERROR Dimension $g_E$

The **ERROR dimension** characterizes error-handling and exception behavior.

**Raw features from trace $\tau$:**

- **Exception type frequency:** $\text{ETF} : \mathcal{T}_\text{exn} \to \mathbb{N}$, count of each thrown/caught exception type
- **Error propagation depth:** $\text{EPD}(\tau)$, distribution over the stack depth at which exceptions are raised
- **Catch coverage:** $\text{CC} = |\{j : op_j = \text{catch}\}| / |\{j : op_j \in \{\text{throw}, \text{catch}\}\}|$ — fraction of thrown exceptions that are caught
- **Retry/recovery pattern:** $\text{RRP} : \mathcal{L}_\text{handler} \to \mathbb{N}$, frequency of each exception handler being invoked
- **Assertion violation rate:** $\text{AVR} = |\{i \in \mathcal{S} : \tau(P,i) \text{ triggers assertion}\}| / |\mathcal{S}|$
- **Abnormal termination rate:** $\text{ATR} = |\{i \in \mathcal{S} : \tau(P,i) \text{ is abnormal}\}| / |\mathcal{S}|$

**Aggregated ERROR feature:**

$$g_E = \left\langle \overline{\text{ETF}},\ \overline{\text{EPD}},\ \bar{\text{CC}},\ \overline{\text{RRP}},\ \text{AVR},\ \text{ATR} \right\rangle$$

**Space:** $\mathcal{G}_E \subseteq \mathbb{R}_{\geq 0}^{m_E}$ for $m_E = |\mathcal{T}_\text{exn}| + |\mathcal{L}_\text{handler}| + 4$

---

### Definition 15 — INTERACTION Dimension $g_X$

The **INTERACTION dimension** characterizes the program's interface with external systems.

**Raw features from trace $\tau$:**

- **System call sequence distribution:** $\text{SSD}(\tau)$, distribution over $n$-grams of system call numbers for $n \in \{1,2,3\}$
- **IPC pattern:** $\text{IPC}(\tau)$, set of inter-process communication endpoints opened (socket addresses, named pipes, shared memory keys) with access patterns
- **File system access pattern:** $\text{FSAP} : \mathcal{L}_\text{fs} \times \{\text{read,write,exec,delete}\} \to \mathbb{N}$
- **Signal handling:** $\text{SH} : \text{Signals} \to \{0,1\}$, which signals are handled vs. defaulted
- **Output byte distribution:** $\text{OBD}$, byte-level distribution of output written to stdout/files

**Aggregated INTERACTION feature:**

$$g_X = \left\langle \overline{\text{SSD}},\ \overline{\text{IPC}},\ \overline{\text{FSAP}},\ \overline{\text{SH}},\ \overline{\text{OBD}} \right\rangle$$

**Space:** $\mathcal{G}_X$ — a heterogeneous space including n-gram distributions and access maps.

> **Remark R6 (Relationship to Prior Art):** $\text{SSD}$ is analogous to the system-call n-gram representation of Bayer et al. [5]. SBG extends this to the full 8-dimensional genome, and targets correctness analysis rather than malware triage.

---

### Definition 16 — EXECUTION Dimension $g_U$

The **EXECUTION dimension** characterizes runtime execution metadata.

**Raw features from trace $\tau$:**

- **Code coverage vector:** $\text{COV} : \mathcal{L} \to \{0, 1\}$, which locations were reached
- **Instruction type histogram:** $\text{ITH} : \mathcal{OP} \to \mathbb{R}_{\geq 0}$, frequency of each operation type
- **Hot path signature:** $\text{HPS}$, the set of top-$k$ most frequently executed basic-block sequences (abstracted to location IDs)
- **Compilation artifact features:** $\text{CAF}$, when available — optimization flags, inlining decisions (from debug symbols or DWARF info)
- **Parallelism profile:** $\text{PP}$, thread count over time, synchronization event frequency

**Aggregated EXECUTION feature:**

$$g_U = \left\langle \overline{\text{COV}},\ \overline{\text{ITH}},\ \overline{\text{HPS}},\ \text{CAF},\ \overline{\text{PP}} \right\rangle$$

**Space:** $\mathcal{G}_U \subseteq \{0,1\}^{|\mathcal{L}|} \times \mathbb{R}_{\geq 0}^{|\mathcal{OP}|} \times \cdots$

---

## Part IV — Distance and Equivalence

### Definition 17 — Dimension-Level Distance Functions

For each dimension $d \in \{C, D, S, R, T, E, X, U\}$, a **dimension distance** $d_d : \mathcal{G}_d \times \mathcal{G}_d \to \mathbb{R}_{\geq 0}$ is defined.

**Per-dimension distance specifications:**

| Dim | Space type | Distance $d_d$ | Justification |
|---|---|---|---|
| $C$ | Frequency vectors + graph | Weighted $\ell_1$ for freq; graph edit distance for DCG | $\ell_1$ is natural for frequency comparison; GED for call graphs |
| $D$ | Distributions | Jensen-Shannon divergence $\text{JSD}$ | Symmetric, bounded $[0,1]$, valid for empirical distributions |
| $S$ | Abstract heap summaries | Structural graph distance (isomorphism-based) | Captures memory layout differences |
| $R$ | Non-negative vectors | Normalized $\ell_2$: $\|g_R - g_R'\|_2 / \max(\|g_R\|_2, \|g_R'\|_2)$ | Scale-invariant comparison |
| $T$ | Distributions + vectors | Wasserstein-1 distance $W_1$ for distributions; $\ell_2$ for vectors | $W_1$ captures shape differences in timing |
| $E$ | Mixed vectors | Weighted $\ell_1$ | Error types deserve equal weight unless domain-weighted |
| $X$ | n-gram distributions + maps | JSD for n-grams; Jaccard for access maps | Distribution-appropriate |
| $U$ | Vectors + sets | Hamming for coverage; $\ell_1$ for histograms | Coverage is binary; histograms are frequency |

**Metric properties required:** Each $d_d$ must satisfy:
1. $d_d(g, g) = 0$ (identity)
2. $d_d(g, g') = d_d(g', g)$ (symmetry)
3. $d_d(g, g'') \leq d_d(g, g') + d_d(g', g'')$ (triangle inequality)
4. $d_d(g, g') \geq 0$ (non-negativity)

> **Note N3:** Property 4 + property 1 do not together imply $d_d(g,g') = 0 \Rightarrow g = g'$ (positive definiteness). Genome equality is defined semantically (Definition 19), not representationally; two distinct genome representations may encode the same behavior.

---

### Definition 18 — Behavioral Distance $D(G_1, G_2)$

The **behavioral distance** between two genomes $G_1 = \Phi(P_1, \mathcal{I})$ and $G_2 = \Phi(P_2, \mathcal{I})$ is:

$$D(G_1, G_2) = \mathcal{F}\!\left(d_C(g_{1C}, g_{2C}),\ d_D(g_{1D}, g_{2D}),\ d_S(g_{1S}, g_{2S}),\ d_R(g_{1R}, g_{2R}),\ d_T(g_{1T}, g_{2T}),\ d_E(g_{1E}, g_{2E}),\ d_X(g_{1X}, g_{2X}),\ d_U(g_{1U}, g_{2U})\right)$$

where $\mathcal{F}$ is the **aggregation function** (Definition 20) and each $d_d$ is normalized to $[0, 1]$.

**Metric properties of $D$:**

**Proposition 1 (Metric properties of $D$):** *If each $d_d$ satisfies Definition 17's four properties and $\mathcal{F}$ is a monotone, symmetric, zero-preserving function of its arguments, then $D$ is a pseudometric on $\mathcal{G}$, i.e., it satisfies non-negativity, symmetry, and the triangle inequality, but not necessarily positive definiteness.*

*Proof sketch:* Each $d_d$ is a pseudometric by hypothesis. The aggregation $\mathcal{F}$ preserves the triangle inequality provided $\mathcal{F}$ is subadditive and monotone in each argument. The weighted sum (Definition 20) satisfies these conditions. $\square$

**Bounds:**

$$0 \leq D(G_1, G_2) \leq 1$$

with $D(G_1, G_2) = 0$ iff $G_1$ and $G_2$ are **genome-equivalent** (Definition 19), and $D(G_1, G_2) = 1$ iff they are maximally behaviorally divergent on the observed dimensions.

---

### Definition 19 — Semantic Equivalence Relation $\equiv_S$

Two programs $P_1, P_2 \in \mathcal{P}$ are **semantically equivalent** with respect to distribution $\mathcal{I}$ and environment $\mathcal{E}$, written:

$$P_1 \equiv_S P_2 \quad [\mathcal{I}, \mathcal{E}]$$

iff for all inputs $i \in \Omega_I$ (with probability 1 under $\mu_I$):

$$B(P_1, i) = B(P_2, i)$$

i.e., their observable behaviors (outputs, side effects, resource consumption up to environment noise) are identical on every input.

**Properties of $\equiv_S$:**

**Proposition 2:** $\equiv_S$ is an equivalence relation on $\mathcal{P}$ (reflexive, symmetric, transitive). *Proof: Immediate from the equality of functions.* $\square$

**Relationship to genome distance:**

$$P_1 \equiv_S P_2 \implies D(G(P_1), G(P_2)) = 0$$

The converse does **not** hold in general (the genome is an approximation). If $D(G(P_1), G(P_2)) = 0$ and the sample $\mathcal{S}$ is sufficiently representative, this provides **empirical evidence** for $P_1 \equiv_S P_2$ but not a formal proof.

**SBG Operational Equivalence:** For engineering purposes, SBG uses the weaker notion:

$$P_1 \equiv_S^\epsilon P_2 \quad \text{iff} \quad D(G(P_1), G(P_2)) < \epsilon$$

for a threshold $\epsilon \in (0, 1)$ chosen by the application context.

> **Remark R7 (Rice's Theorem):** Full semantic equivalence ($\equiv_S$) is undecidable for Turing-complete languages. SBG explicitly does not claim to decide $\equiv_S$; it computes an empirical approximation $\equiv_S^\epsilon$ which is decidable given finite traces.

---

## Part V — Aggregation and Normalization

### Definition 20 — Aggregation Function $\mathcal{F}$

The **aggregation function** $\mathcal{F} : [0,1]^8 \to [0,1]$ maps 8 per-dimension distances to a scalar behavioral distance.

**Standard form — Weighted $L^p$ aggregation:**

$$\mathcal{F}(\mathbf{d}) = \left( \sum_{k=1}^{8} w_k \cdot d_k^p \right)^{1/p}$$

where:
- $\mathbf{d} = (d_C, d_D, d_S, d_R, d_T, d_E, d_X, d_U) \in [0,1]^8$
- $w_k \geq 0$ are **dimension weights** with $\sum_k w_k = 1$
- $p \geq 1$ is the **aggregation exponent**

**Special cases:**

| $p$ | $\mathcal{F}$ form | Interpretation |
|---|---|---|
| $p = 1$ | Weighted average | All dimensions contribute equally to total distance |
| $p = 2$ | Weighted Euclidean | Penalizes large divergence in any single dimension |
| $p \to \infty$ | Weighted max | Distance dominated by most divergent dimension |

**Default weights $\mathbf{w}^*$:** The default weight vector is uniform:

$$w_k^* = 1/8 \quad \forall k$$

Application-specific weight vectors are defined for each hypothesis in Part VI.

**Normalization requirement:** Each $d_k$ must be pre-normalized to $[0,1]$ before applying $\mathcal{F}$ (see Definition 22).

**Proposition 3 (Range preservation):** *For $p \geq 1$ and $\sum_k w_k = 1$ with $w_k \geq 0$ and $d_k \in [0,1]$: $\mathcal{F}(\mathbf{d}) \in [0,1]$.* *Proof: By Jensen's inequality and the convexity of $x^p$ on $[0,1]$.* $\square$

---

### Definition 21 — Trace Aggregation Operator $\mathcal{A}$

Given $N$ raw genome vectors $\{g_\text{raw}^{(j)}\}_{j=1}^N$ extracted from traces $\{\tau(P, i_j)\}_{j=1}^N$, the **aggregation operator** $\mathcal{A}$ computes:

$$\mathcal{A}\!\left(\{g_\text{raw}^{(j)}\}\right) = g$$

For numerical features, $\mathcal{A}$ computes the **empirical mean**:

$$\bar{g}_k = \frac{1}{N} \sum_{j=1}^N g_{\text{raw},k}^{(j)}$$

For distributional features (histograms, n-gram distributions), $\mathcal{A}$ computes the **mixture distribution**:

$$\bar{H} = \frac{1}{N} \sum_{j=1}^N H^{(j)}$$

For structural features (graphs, sets), $\mathcal{A}$ uses **frequency-weighted union**:

$$\overline{\text{DCG}} = \left( \bigcup_j V_j,\ \left\{\left(e, \frac{1}{N}\sum_j \text{mult}_j(e)\right)\right\}_{e \in \bigcup_j E_j} \right)$$

> **Remark R8 (Variance):** The aggregation discards within-program variance across inputs. A richer genome representation would include variance estimates (e.g., confidence intervals on $\bar{g}_k$). This is noted as an extension opportunity (see Open Problem OP-3).

---

### Definition 22 — Normalization and Canonicalization Operators

**Normalization** adjusts genome components to be comparable across programs or environments.

**Definition 22a — Scalar normalization $\mathcal{N}_\text{scalar}$:**

$$\mathcal{N}_\text{scalar}(x; \mu, \sigma) = \frac{x - \mu}{\sigma}$$

Applied to resource and temporal features that are sensitive to $\mathcal{E}$. Parameters $\mu, \sigma$ are estimated from a corpus of reference programs.

**Definition 22b — Distribution normalization $\mathcal{N}_\text{dist}$:**

$$\mathcal{N}_\text{dist}(H) = H / \|H\|_1$$

Converts count histograms to probability distributions.

**Definition 22c — Environment canonicalization $\mathcal{C}_{\mathcal{E}}$:**

$$\mathcal{C}_{\mathcal{E}} : \mathcal{G} \to \mathcal{G}$$

maps a genome extracted under environment $\mathcal{E}$ to a canonical form independent of $\mathcal{E}$. Applied to RESOURCE and TEMPORAL dimensions using reference-machine normalization:

$$\mathcal{C}_{\mathcal{E}}(g_R) = g_R / \text{SPEC}_{\mathcal{E}}$$

where $\text{SPEC}_\mathcal{E}$ is a scalar performance index for environment $\mathcal{E}$ (e.g., SPECint score).

**Definition 22d — Version canonicalization $\mathcal{C}_v$:**

$$\mathcal{C}_v(G(P^{(k)})) = \mathcal{C}_v(G(P^{(k')}))$$

ensures that genome components that are invariant to versioning conventions (e.g., location identifiers) are aligned across $P^{(k)}$ and $P^{(k')}$ using a **location alignment map** $\alpha : \mathcal{L}^{(k)} \to \mathcal{L}^{(k')}$ derived from diff tools or function-signature matching.

> **Assumption A10 (Alignment Completeness):** The alignment map $\alpha$ covers all locations that are shared between versions. New or deleted locations are assigned zero weight in the distance computation.

---

## Part VI — Hypotheses H1–H6

The following hypotheses are the central empirical claims of the SBG project, stated formally in terms of the definitions above.

---

### Hypothesis H1 — Behavioral Genome Stability

**Informal statement:** A program's behavioral genome is stable under semantics-preserving transformations (refactoring, dead-code elimination, code style changes).

**Formal statement:**

Let $P$ and $P'$ be two programs such that $P \equiv_S P'$. Then:

$$D(G(P), G(P')) < \epsilon_\text{stable}$$

for a small threshold $\epsilon_\text{stable}$ (empirically: $\epsilon_\text{stable} \leq 0.05$ on standard benchmarks under $\mathcal{I}_\text{prod}$).

**Testable prediction:** Given a corpus of known-equivalent program pairs (e.g., refactored versions confirmed equivalent by regression tests), the empirical distribution of $D(G(P), G(P'))$ is concentrated near zero, with mean $< \epsilon_\text{stable}$.

**Caveats:**
- Stability is asserted only for dimensions not sensitive to the transformation (e.g., TEMPORAL and RESOURCE may change under loop unrolling even when semantics are preserved).
- The threshold $\epsilon_\text{stable}$ is dimension-dependent.

---

### Hypothesis H2 — Structured SBG Discriminative Power Over Baselines

**Informal statement:** A semantic change (behavioral regression, bug introduction, feature addition) produces a statistically detectable change in the genome; the structured multi-dimensional SBG distance outperforms source-level, token-level, AST-level, and CFG-level similarity baselines for semantic-equivalence discrimination.

**Formal statement:**

Let $P^{(k)}$ and $P^{(k+1)}$ be consecutive versions in $\mathcal{H}(P)$, and let $\Delta$ be a set of inputs witnessing a semantic difference (i.e., $\exists i \in \Delta : B(P^{(k)}, i) \neq B(P^{(k+1)}, i)$). Then:

$$D\!\left(G(P^{(k)}), G(P^{(k+1)})\right) > \epsilon_\text{detect}$$

for a detection threshold $\epsilon_\text{detect} > 0$.

**Testable prediction:** On Defects4J [28] or equivalent benchmark, the distribution of $D$ over known-buggy version pairs is stochastically greater than the distribution over known-equivalent pairs, and the AUC of $D$ exceeds the AUC of all non-behavioral baseline similarity metrics.

**Formal dependency:** H2 depends on the sample $\mathcal{S}$ covering the inputs in $\Delta$. If $\mu_I(\Delta) \approx 0$ (the bug is triggered by extremely rare inputs), H2 may fail for $\mathcal{I}_\text{prod}$ but succeed for $\mathcal{I}_\text{adv}$.

---

### Hypothesis H3 — Behavioral Genome Robustness Under Refactoring

**Informal statement:** The behavioral genome is robust under semantics-preserving transformations including renaming, method inlining, loop restructuring, and compiler optimization; genome distance $D$ remains small across all such transformations.

**Formal statement:**

Let $\mathcal{T}_\text{SP}$ be the set of semantics-preserving transformations (renaming, inlining, loop normalization, dead-code elimination, compiler optimization). For any $t \in \mathcal{T}_\text{SP}$ and program $P$, let $P' = t(P)$. Then:

$$D\!\left(G(P),\ G(P')\right) < \epsilon_\text{robust}$$

for a robustness threshold $\epsilon_\text{robust}$, where the expectation is over the transformation distribution and input distribution $\mathcal{I}$.

**Stronger form:** The genome distance is bounded uniformly across the full transformation taxonomy $\mathcal{T}_\text{SP}$:

$$\sup_{t \in \mathcal{T}_\text{SP}} \mathbb{E}_{\mathcal{I}}\!\left[D(G(P), G(t(P)))\right] < \epsilon_\text{robust}$$

**Testable prediction:** On a corpus of program pairs produced by applying $\mathcal{T}_\text{SP}$ transformations (renaming, inlining, restructuring, optimization), $D(G(P), G(P'))$ is concentrated near zero with mean $< \epsilon_\text{robust} \leq 0.05$.

**Formal dependency:** H3 extends H1 by requiring stability across a named taxonomy of transformation types, not just semantic equivalence in the abstract.

---

### Hypothesis H4 — Cross-Language Behavioral Generalization

**Informal statement:** Semantically equivalent programs in different languages receive the same behavioral genome (up to environment normalization), for the language-portable genome dimensions.

**Formal statement:**

Let $P_1 \in \mathcal{P}_{\text{Python}}$ and $P_2 \in \mathcal{P}_{\text{Java}}$ implement the same algorithm with $P_1 \equiv_S P_2$ (verified by shared test oracle). Let $\mathcal{C}_\mathcal{E}$ be the environment canonicalization of Definition 22c. Then:

$$D\!\left(\mathcal{C}_\mathcal{E}(G(P_1)),\ \mathcal{C}_\mathcal{E}(G(P_2))\right) < \epsilon_\text{xlang}$$

for a cross-language equivalence threshold $\epsilon_\text{xlang}$, restricted to the confirmed portable dimensions $\{g_D, g_X\}$.

**Caveats:**
- EXECUTION dimension ($g_U$) will differ systematically across languages (Python bytecode instructions vs. JVM opcodes vs. native x86) and must be excluded or separately normalized in cross-language comparisons.
- TEMPORAL and RESOURCE dimensions require strong normalization.
- DATA ($g_D$) and INTERACTION ($g_X$) are the **confirmed portable dimensions** for this hypothesis.
- CONTROL ($g_C$): **[EXPLORATORY/PRELIMINARY]** — cross-language alignment of $g_C$ requires a formal procedure correspondence map across language boundaries (e.g., Python `sort()` ↔ Java `Collections.sort()`), which is an unresolved open problem (OP-4). The $g_C$ claim is exploratory only and is excluded from the primary confirmatory test of H4 until OP-4 is resolved.

---

### Hypothesis H5 — Behavioral Genome Regression Detection

**Informal statement:** The behavioral genome provides a test-suite-free regression detection oracle: genome divergence predicts behavioral regression with high recall and acceptable precision.

**Formal statement:**

Let $\mathcal{R} \subseteq \mathcal{H}(P)^2$ be the set of version pairs confirmed to have a behavioral regression (by a gold-standard test suite $\mathcal{T}^*$). Let $\hat{\mathcal{R}}_\theta = \{(P^{(k)}, P^{(k+1)}) : D(G^{(k)}, G^{(k+1)}) > \theta\}$ be the SBG regression predictor at threshold $\theta$.

Define:
$$\text{Recall}(\theta) = \frac{|\hat{\mathcal{R}}_\theta \cap \mathcal{R}|}{|\mathcal{R}|}, \quad \text{Precision}(\theta) = \frac{|\hat{\mathcal{R}}_\theta \cap \mathcal{R}|}{|\hat{\mathcal{R}}_\theta|}$$

**H5 claims:** There exists a $\theta^*$ such that $\text{Recall}(\theta^*) \geq 0.80$ and $\text{Precision}(\theta^*) \geq 0.70$ on a held-out software corpus.

**Formal dependency:** H5 depends on H2 (discriminative sensitivity) and on $\mathcal{I}$ covering inputs that trigger the regressions in $\mathcal{R}$. Under $\mathcal{I}_\text{adv}$, recall is expected to increase.

---

### Hypothesis H6 — Multi-Dimensional Behavioral Value

**Informal statement:** Combining multiple behavioral dimensions provides measurable discriminative value over any single dimension alone; the structured 8-dimensional genome outperforms all individual dimension baselines.

**Formal statement:**

For programs $P_1, P_2 \in \mathcal{P}$, let $D^{(d)}(G(P_1), G(P_2)) = d_d(g_d(P_1), g_d(P_2))$ denote the single-dimension distance for dimension $d \in \{C,D,S,R,T,E,X,U\}$. Then:

$$\text{AUC}\!\left(D(\cdot,\cdot)\right) > \max_{d} \text{AUC}\!\left(D^{(d)}(\cdot,\cdot)\right)$$

on the semantic-equivalence discrimination task over the benchmark corpus.

**Empirical targets:** The full $D$ achieves AUC improvement $\geq 0.03$ over the best single-dimension baseline; dimension ablation confirms each dimension contributes a non-zero marginal improvement.

**Caveat:** If one dimension dominates all others, the multi-dimensional architecture is justified on interpretability grounds even if the AUC improvement is small. The hypothesis is falsified only if $D$ is strictly worse than the best single-dimension baseline.

---

## Part VII — Open Problems and Approximation Notes

### Open Problem OP-1 — Optimal Sample Size $N$

For a given program $P$, input distribution $\mathcal{I}$, and acceptable error $\epsilon$, what is the minimum sample size $N^*(\epsilon)$ such that:

$$\mathbb{E}\!\left[\|G_N(P) - G_\infty(P)\|_\mathcal{G}\right] \leq \epsilon$$

where $G_N$ uses $N$ traces and $G_\infty$ is the population-limit genome? This depends on the variance of behavioral features across inputs and is currently unknown in general.

---

### Open Problem OP-2 — Decidability of $\equiv_S^\epsilon$

Is $\equiv_S^\epsilon$ decidable for all $\epsilon > 0$ when restricted to finite-terminating programs? The answer depends on the complexity of the underlying genome features (some are NP-hard to compute exactly, e.g., graph edit distance for $g_C$).

---

### Open Problem OP-3 — Confidence-Weighted Genome Distance

The current distance $D$ does not account for uncertainty in genome estimation (finite-sample variance). A confidence-weighted distance:

$$D_\text{conf}(G_1, G_2) = \frac{D(G_1, G_2)}{\sqrt{\hat{\sigma}_{G_1}^2 + \hat{\sigma}_{G_2}^2}}$$

(analogous to a Welch $t$-statistic) may yield better-calibrated regression detection thresholds. Formal development of this is left as future work.

---

### Open Problem OP-4 — Cross-Language Alignment of $g_C$

The CONTROL dimension encodes dynamic call graphs using procedure identifiers. Cross-language alignment requires matching procedures across language boundaries (e.g., Python `sort()` ↔ Java `Collections.sort()`). A formal cross-language procedure equivalence mapping is not defined in this document and constitutes a significant open problem for H3.

---

### Open Problem OP-5 — Heap Abstraction Selection

Definition 11 (STATE dimension) parameterizes over an abstract heap domain $\mathcal{Q}_\text{abs}$. The choice of abstraction trades expressiveness against computational cost. A principled method for selecting the minimal-sufficient abstraction for a given comparison task is not defined here.

---

### Open Problem OP-6 — Temporal Normalization Across Architectures

Definition 22c uses SPECint scores for RESOURCE normalization. For TEMPORAL features (Definition 13), the appropriate normalization is less clear when comparing programs across radically different architectures (e.g., interpreted Python vs. native Rust). A formal temporal equivalence metric that is architecture-agnostic remains open.

---

## Summary of Definitions

| # | Name | Symbol |
|---|---|---|
| 1 | Computational Environment | $\mathcal{E}$ |
| 2 | Program | $P$ |
| 3 | Version History | $\mathcal{H}(P)$ |
| 4 | Input Distribution | $\mathcal{I}$ |
| 5 | Execution Trace | $\tau(P, i)$ |
| 6 | Observable Behavior | $B(P, \mathcal{I})$ |
| 7 | Genome Extraction Function | $\Phi$ |
| 8 | Behavioral Genome | $G(P)$ |
| 9 | CONTROL Dimension | $g_C$ |
| 10 | DATA Dimension | $g_D$ |
| 11 | STATE Dimension | $g_S$ |
| 12 | RESOURCE Dimension | $g_R$ |
| 13 | TEMPORAL Dimension | $g_T$ |
| 14 | ERROR Dimension | $g_E$ |
| 15 | INTERACTION Dimension | $g_X$ |
| 16 | EXECUTION Dimension | $g_U$ |
| 17 | Dimension-Level Distance | $d_d$ |
| 18 | Behavioral Distance | $D(G_1, G_2)$ |
| 19 | Semantic Equivalence | $\equiv_S$ |
| 20 | Aggregation Function | $\mathcal{F}$ |
| 21 | Trace Aggregation Operator | $\mathcal{A}$ |
| 22 | Normalization / Canonicalization | $\mathcal{N}, \mathcal{C}$ |

## Summary of Propositions

| # | Statement |
|---|---|
| 1 | $D$ is a pseudometric on $\mathcal{G}$ |
| 2 | $\equiv_S$ is an equivalence relation |
| 3 | $\mathcal{F}$ maps $[0,1]^8 \to [0,1]$ |

## Summary of Assumptions

| ID | Statement |
|---|---|
| A1 | Environment stability during execution |
| A2 | Version identity supplied externally |
| A3 | Input independence |
| A4 | Input measurability |
| A5 | All traces are finite (timeout-bounded) |
| A6 | Execution is deterministic given fixed input and environment |
| A7 | Sample sufficiency for distributional convergence |
| A8 | Heap abstraction is sufficiently expressive |
| A9 | Clock resolution is sufficient |
| A10 | Location alignment map is complete for shared locations |

---

*This document was produced by Agent 0B for the SBG project. Mathematical definitions are precise where theory permits; approximations are explicitly named. This is a living document — propositions are stated without full proof where proofs require empirical validation (H1–H6) or are left as open problems (OP-1–OP-6).*
