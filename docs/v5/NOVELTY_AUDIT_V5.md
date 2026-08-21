# SBG Novelty Audit V5 — Grounded in V4 Experimental Results

**Version:** v5  
**Agent:** Bob (IBM)  
**Date:** 2025  
**Basis:** `docs/research/PRIOR_ART_MATRIX.md`, `docs/research/NOVELTY_ANALYSIS.md`, `docs/v4/V4_FINAL_SCIENTIFIC_REPORT.md`, `artifacts/v2/NOVELTY_AUDIT_V2.json`

---

## Preface

This audit differs from V2 in one critical respect: **V4 experimental results are now frozen.** The V2 audit evaluated novelty on a theoretical basis — whether the SBG architecture was novel in principle. The V5 audit evaluates novelty in light of what SBG *actually demonstrated*: AUROC=0.546, CI lower bound=0.477 (below 0.5), exception_fraction as the single dominant feature, and 7.5% detection rate on SC-3 constant mutations.

Novelty assessed against positive expected results differs from novelty assessed against near-chance actual results. This audit addresses both.

---

## A. Novelty Matrix — 10 Specific Works

The following table provides a compact comparison for each of the 10 works under audit. Detailed analysis follows.

| # | Work | Representation | Static/Dynamic | Temporal? | State? | Lang-Agnostic? | Regression? | Benchmark | Key Difference from SBG |
|---|------|---------------|----------------|-----------|--------|----------------|-------------|-----------|--------------------------|
| 1 | **EvoSuite + DynaMOSA** | Branch coverage vectors, call counts, exception signals as evolutionary fitness | DYNAMIC (per-generation execution) | NO | PARTIAL (exception/coverage) | NO (JVM only) | NO (test generation, not detection) | SF110 corpus, Defects4J mutation score | SBG's `g_U` is structurally EvoSuite's coverage fitness function; task is test generation vs. version comparison; V4 shows `only_coverage` AUROC=0.539 — consistent with EvoSuite's known coverage-signal weakness |
| 2 | **SYMDIFF** (Lahiri et al., 2012) | Verification conditions over matched path pairs; Z3 SMT | STATIC (symbolic) | NO | YES (symbolic heap via Boogie) | PARTIAL (requires Boogie IR frontend) | YES (semantic regression detection) | Windows drivers, LibPNG | SBG is concrete+scalable vs. SYMDIFF's sound+small; SYMDIFF would detect all SC-2/SC-3/SC-5/SC-7 mutations that SBG misses (sim≈0.999); SBG covers Python/interpreted — SYMDIFF requires Boogie compilation |
| 3 | **TTAnalyze** (Bayer et al., 2009) | Syscall n-grams + API call sequences | DYNAMIC (sandboxed VM) | NO | NO (OS interface only) | YES (OS-level) | NO (malware clustering) | 75,000 malware samples | SBG's `g_X` ≅ TTAnalyze's syscall n-grams; V4: `only_call_bigrams`=0.545 ≈ noise (0.538); SBG's 8-dim model provides no measurable lift over TTAnalyze-style features; domain distinction (malware triage vs. regression) is real |
| 4 | **Jalangi2** (Sen et al., 2013) | Shadow values per JS variable; dynamic taint + type inference via callback API | DYNAMIC (instrumented JS engine) | NO | YES (per-variable shadow state) | NO (JS only) | NO (single-version bug detection) | Sunspider, Octane | Jalangi2 is a dynamic analysis PLATFORM for JS; SBG's Python tracer is architecturally analogous (`sys.settrace` ≅ Jalangi2 callbacks); SBG's 'language-agnosticism' applies to distance function D, not trace extraction infrastructure |
| 5 | **Piech et al.** (ICML 2015) | Execution trace feature vectors; neural embedding for program similarity | DYNAMIC (concrete execution on fixed test inputs) | NO | YES (I/O state sequences) | NO (Python/Scheme student programs) | NO (feedback propagation, not regression) | Stanford CS1 ~3000 submissions | **MOST DANGEROUS OVERLAP**: identical pipeline (run program → trace features → distance between vectors); SBG's only structural differentiator is SAFEGUARD-2 (output-excluded) + formal pseudometric + version-comparison framing; V4 undermines SAFEGUARD-2 by showing exception_fraction (output-proximate) beats output-free model |
| 6 | **CodeBERT / GraphCodeBERT** | Transformer over tokens (CodeBERT) + static data-flow edges (GraphCodeBERT) | STATIC | NO | NO (static approx. only) | PARTIAL (6 languages, source required) | NO (pre-trained for search/summarization) | CodeSearchNet, BigCloneBench | Both are near-chance on SBG benchmark (CodeBERT≈0.37, SBG V3=0.546); structural-semantic inversion (NC-01) affects CodeBERT too; '0.37 is zero-shot' framing is accurate but understates pre-training advantage; SBG advantage: no source code required at runtime |
| 7 | **code2vec / code2seq** | Bag of AST path-contexts; attention-weighted dense vector / LSTM over AST paths | STATIC | NO | NO | NO (Java-centric; parser required) | NO (method name prediction) | 14M Java methods GitHub | SBG call bigrams ≅ AST path-contexts in motivation but differ in content (dynamic call sequences vs. static AST paths); V4: `only_call_bigrams`=0.545 ≈ noise; code2vec paths are richer structurally but static; SBG advantage: execution-grounded equivalence for Type-4 clones |
| 8 | **Equivalence Partitioning** (Myers 1979, Howden 1980) | Input space partitioned into expected-behavior classes; one test per class | HYBRID (static partition + dynamic execution) | NO | NO (input domain, not program state) | YES (conceptually) | INDIRECT (test adequacy) | Theoretical; any test adequacy evaluation | Not the same concept: EP partitions INPUT SPACE; SBG characterizes PROGRAM PAIR DISTANCE; V4 SC-3 failures (7.5%) attributable to inadequate EP-style input coverage, not to overlap with EP |
| 9 | **Differential Testing** (McKeeman 1998, Klees 2018) | Two implementations run on same inputs; binary output divergence | DYNAMIC (concrete execution, binary comparison) | NO | NO (output only) | YES (conceptually) | INDIRECT (catches behavioral divergence) | Compilers (C, FORTRAN); fuzzing benchmarks | SBG computes graded distance D∈[0,1]; differential testing computes binary divergence; V4 undermines SBG's advantage: binary exception-fraction (0.593) beats graded 8-dim distance (0.546); McKeeman 1998 **still missing from PRIOR_ART_MATRIX.md** (flagged V2, persists to V4) |
| 10 | **Sumner et al.** (OOPSLA 2011) | Execution traces of version pairs; dynamic slice comparison; side-effect detection via trace alignment | DYNAMIC (concrete execution, lossless trace comparison) | NO | YES (heap state at call sites) | NO (C/LLVM only) | YES (behavioral regression detection) | Linux system utilities | **MOST DIRECT PRIOR ART**: explicitly runs paired versions, compares execution traces, characterizes behavioral differences; SBG delta: compressed feature vector (scalable) vs. lossless trace (precise); SBG trade-off is lossy — SC-3 mutations trivially detectable by Sumner; **completely absent from all SBG prior-art documents** |

---

## B. Per-Work Detailed Analysis

### B.1 — EvoSuite + DynaMOSA

EvoSuite uses execution traces as a search signal for test generation. Its coverage fitness function — branch coverage vectors normalized per class — is structurally equivalent to SBG's `g_U` (EXECUTION) dimension. DynaMOSA extends this with multi-objective optimization over uncovered branches.

**How different is SBG from EvoSuite's behavioral coverage metrics?**  
The representation overlap with `g_U` is real. SBG's `g_U` does not improve on EvoSuite's coverage model; it repurposes it in a different task frame. V4 Phase 8 confirms this: `only_coverage` AUROC=0.539 — below noise floor (0.538) by a trivial margin. Removing coverage from SBG *improves* performance (`no_coverage`=0.560). EvoSuite's internal experience with coverage signals is directly relevant: coverage is a weak behavioral discriminator unless augmented with semantic oracles, which is exactly EvoSuite's conclusion and SBG's V4 finding.

**SBG delta that survives:** Task distinction (test generation vs. version comparison) and language-agnosticism. What does not survive: any claim that SBG's `g_U` advances on EvoSuite's coverage representation.

---

### B.2 — SYMDIFF (Lahiri et al., 2012)

SYMDIFF generates verification conditions over matched program path pairs and uses Z3 to prove equivalence or find counterexamples. It is **sound**: a proof of equivalence is correct.

**SBG is concrete execution; SYMDIFF is symbolic. Advantages/disadvantages?**

| Dimension | SYMDIFF | SBG V4 |
|-----------|---------|--------|
| Soundness | YES — correct equivalence proofs | NO — empirical approximation |
| Scalability | LIMITED — straight-line code regions only | YES — arbitrary programs |
| Language scope | C/Boogie (requires compilation) | Python (requires interpreter trace) |
| Detection of SC-3 (constant mutations) | YES — SMT solver finds counterexample directly | FAILS — 7.5% detection rate |
| Detection of SC-2, SC-5, SC-7 | YES | FAILS — sim≈0.999 |
| Interpreted language support | NO | YES |

The V4 results make SYMDIFF's advantage starkly clear: the mutations SBG cannot detect (SC-2, SC-3, SC-5, SC-7) are precisely the mutations that symbolic execution handles trivially. SBG's scalability advantage is real but must be accompanied by an honest acknowledgment that it purchases scalability at the cost of very low precision on subtle semantic mutations.

---

### B.3 — TTAnalyze (Bayer et al., 2009)

TTAnalyze records system-call n-grams from malware execution and clusters samples by behavioral similarity. Its `g_X`-equivalent representation (syscall sequences) is the most important single behavioral signal in SBG.

**V4 ablation finding:** `only_call_bigrams` AUROC=0.545, barely above noise (0.538). TTAnalyze's richer n-gram representation (tri-grams, 4-grams) on a malware clustering task with 75,000 samples would likely outperform SBG's call bigrams on the SBG task if applied at proper depth. The multi-dimensional SBG genome provides zero measurable lift over the call-bigram baseline in V4.

**What survives:** Domain distinction (regression detection vs. malware triage) and the version-history framing. What does not survive: the claim that SBG's 8-dimensional structure provides useful information beyond TTAnalyze-style call sequence features on the current benchmark.

---

### B.4 — Jalangi2 (Sen et al., 2013)

Jalangi2 is the JavaScript analog of what SBG does for Python: it instruments JavaScript execution with a callback-based API and provides shadow-value tracking for dynamic analysis.

**How does SBG differ from Jalangi-style tracing?**  
SBG's Python trace extraction (via `sys.settrace`/`sys.setprofile`) is architecturally analogous to Jalangi2's source instrumentation. The key difference is PURPOSE, not mechanism: Jalangi2 enables single-version bug detection (type errors, undefined behavior); SBG enables cross-version behavioral comparison. SBG's `language-agnostic` claim must be qualified: the distance function `D` is language-agnostic in principle, but each language requires a language-specific trace extraction layer (Python tracer ≠ Jalangi2 ≠ Java agent). The trace extraction infrastructure is language-specific in every instantiation.

---

### B.5 — Piech et al., 2015 (ICML) — The Critical Comparison

> **⚠ CRITICAL GAP: Piech et al. is completely absent from all 40 entries in `PRIOR_ART_MATRIX.md` and from V2/V4 audit documents. This must be added before any publication.**

**Is SBG essentially the same as Piech et al.?**

Piech et al. (ICML 2015) do the following: (1) run student programs on fixed test inputs; (2) extract execution-derived feature vectors from the resulting traces; (3) train a neural network to embed programs in a semantic space; (4) compute distance between programs using that embedding for automated feedback propagation.

This is operationally the same pipeline as SBG. The differences:

| Dimension | Piech et al. | SBG V4 |
|-----------|-------------|--------|
| Trace feature extraction | Execution traces on fixed tests | Execution traces on fixed tests |
| Embedding | LEARNED (neural network) | HAND-SPECIFIED (8-dim distance) |
| Output included | YES (I/O state sequences) | NO (SAFEGUARD-2) |
| Application | Student feedback clustering | Regression detection |
| Versioned comparison | NO (per-submission) | YES (cross-version pairs) |
| Formal properties | NO | YES (pseudometric) |

SBG is NOT essentially Piech et al. — the output-exclusion design (SAFEGUARD-2), versioned comparison, and formal pseudometric are genuine differentiators. **However**, V4 undermines SAFEGUARD-2's justification: `exception_fraction` (a near-output signal) beats the output-free full model. If output-sensitive features are empirically superior, the SAFEGUARD-2 exclusion may need to be relaxed, which would narrow the gap with Piech further. Any SBG publication must cite Piech et al. and precisely articulate these four differentiators.

---

### B.6 — CodeBERT / GraphCodeBERT

**Is the 0.37 CodeBERT result really zero-shot?**

Partially. CodeBERT was not fine-tuned on SBG benchmark labels — in that sense, yes, it is zero-shot. However, CodeBERT's pre-training on 6-language CodeSearchNet encodes substantial code-semantic knowledge. The 0.37 AUROC (below chance) is best explained by the structural-semantic inversion (NC-01): CodeBERT's static token embeddings treat semantics-preserving refactors as high-distance and semantics-changing mutations as low-distance, just like all other static representations.

A fine-tuned CodeBERT on the SBG training split would likely approach SBG V3's 0.546, because the inversion is a property of static representations generally — fine-tuning on labeled pairs would correct for it. The comparison should be framed as: both methods fail near-chance on this benchmark; CodeBERT fails because of static representation + inversion; SBG fails because of exception-dominance and SC-3 impermeability.

---

### B.7 — code2vec / code2seq

**Are SBG's call graph features similar to code2vec paths?**

Superficially similar in motivation; different in content. code2vec's AST path-contexts encode the structural path between two leaf nodes in an AST (variable names, operator types, structural context). SBG's call bigrams encode observed function-to-function call transitions weighted by execution frequency.

The two encode different information: code2vec captures static code structure; SBG's call features capture which functions were actually called and in what sequence. For Type-4 clones (same behavior, different structure), code2vec paths diverge while SBG call bigrams may converge — this is SBG's theoretical advantage. V4 shows this advantage does not materialize on the current benchmark (`only_call_bigrams`=0.545). The representations are not the same.

---

### B.8 — Equivalence Partition Testing

**Is SBG just a distance-based generalization of equivalence partitions?**

No. Equivalence partitioning is a test DESIGN technique for the input space: identify input classes that should produce equivalent outputs, then select one representative test per class. SBG is a program-pair DISTANCE measurement technique: given a test suite (of any provenance), characterize how behaviorally distant two program versions are.

The connection is indirect: SBG's detection failures (SC-3: 7.5%) are partly attributable to the 16-test oracle not covering the equivalence classes that trigger constant-mutation behavioral changes — a limitation that EP-informed test design would address. But this makes EP a potential IMPROVEMENT to SBG's evaluation methodology, not a conceptual overlap with SBG.

---

### B.9 — Differential Testing (McKeeman 1998, Klees 2018)

> **⚠ PUBLICATION BLOCKER: McKeeman 1998 was flagged as MISSING in V2 audit (RISK-02, severity SERIOUS). It is still absent from `PRIOR_ART_MATRIX.md` in V4. Must be added before any external submission.**

**Is SBG's graded distance sufficient to differentiate from differential testing's binary equality check?**

In principle, yes. In V4 empirical results, no. The graded 8-dimensional distance (AUROC=0.546) is beaten by the binary exception-fraction signal (0.593). Differential testing's binary divergence, if applied to exception behavior specifically, would likely achieve similar or better performance than SBG V4 on the current benchmark.

The theoretical argument for graded distance — it characterizes HOW MUCH and IN WHICH DIMENSION behavior changed — is sound and provides real interpretability value. But this is an interpretability advantage, not a detection-performance advantage, and must be framed as such.

---

### B.10 — Sumner et al., 2011 (OOPSLA)

> **⚠ CRITICAL GAP: Completely absent from all SBG prior-art documents. This is the most direct academic ancestor of SBG's regression detection claim. Any OOPSLA or ISSTA reviewer will ask about this work immediately.**

Sumner et al. (OOPSLA 2011) explicitly perform: paired concrete execution of two program versions → execution trace comparison → dynamic slice alignment → side-effect characterization. This is the lossless, statement-level version of what SBG does at the compressed-feature-vector level.

**Why SBG is not equivalent to Sumner et al.:**

| Dimension | Sumner et al. | SBG V4 |
|-----------|--------------|--------|
| Trace comparison | Lossless (full trace alignment) | Lossy (feature vector compression) |
| Granularity | Statement-level (identifies which statement) | Genome-level (identifies which dimension) |
| Detection of constant mutations | YES (trace differs at mutation site) | NO (7.5% detection) |
| Scalability | LIMITED by trace storage | YES (no trace storage) |
| Multi-language | NO (C/LLVM only) | YES (Python; extensible) |
| Formal distance | NO | YES (pseudometric) |

SBG's compression is simultaneously its scalability advantage and its precision limitation. Sumner et al. would detect all of SBG V4's SC-3 failures trivially. This must be acknowledged honestly.

---

## C. Novelty Verdict

**Verdict: INCREMENTALLY_NOVEL**

SBG applies execution-trace-derived behavioral fingerprinting — established by TTAnalyze (2009), Sumner (2011), Piech (2015), and differential testing (1998) — to a new formulation: a multi-dimensional, formally specified, cross-version behavioral distance for regression detection without a test suite.

The components are not novel. The combination is novel in framing. The combination does not produce emergent improvement over individual components in V4 results — which means the novelty rests entirely on the architectural framing and the benchmark, not on demonstrated performance advantage.

**Novel claims that survive all attacks:**

1. **NC-01 (Structural-semantic inversion):** First named and quantified observation that semantics-preserving transforms produce larger structural distance than semantics-changing mutations across all representations tested. Survives all attacks. Supported by V2+V4 data.

2. **Benchmark:** 3577 labeled pairs, 24 transform types, honest negative results. Independently valuable regardless of SBG's own performance.

3. **SAFEGUARD-2 (output-free behavioral genome):** Architecturally distinguishes SBG from Piech et al. and differential testing. Weakened but not invalidated by V4's exception dominance finding.

**Claims that do not survive V4:**

- 8-dimensional genome architecture: `exception_fraction` alone (one component, AUROC=0.593) beats the full 8-component model (0.550). The architecture is not empirically justified.
- Regression oracle hypothesis (H12): NOT_SUPPORTED. Accuracy=0.50 on real regressions.
- Cross-language equivalence (H11): UNEVALUATED. V4 cross-formulation result AUROC=0.225 (inverted) is actively damaging.

---

## D. Strongest Defensible Novelty Claim

Given AUROC=0.546 with CI lower bound=0.477, affirmative performance claims are not defensible at α=0.05 after Holm-Bonferroni correction.

**Selected claim: (b) + (c) combined**

> **(b)** "We provide the first systematic benchmark for behavioral change detection with 3577 labeled pairs, covering 13 programs, 11 semantics-preserving transforms, and 13 semantics-changing mutation types, enabling reproducible evaluation of any behavioral similarity method."

> **(c)** "We establish negative results: execution-volume shortcuts — specifically, exception-rate features (AUROC=0.593) — consistently dominate richer multi-dimensional behavioral representations (AUROC=0.546), and integer constant mutations (SC-3) are essentially undetectable by trace-level features (7.5% detection rate at sim<0.5 threshold). These findings suggest fundamental limitations of current execution-trace abstractions for fine-grained semantic change detection."

**Why not (a):** The margin (0.546 vs. 0.538 noise floor) is within CI lower bound 0.477 — statistically indistinguishable from zero at corrected alpha.

**Why not (d):** No stable positive condition for temporal representation advantage was identified. V4 Phase 8 shows temporal features underperform exception_fraction individually; per-program variance (DEV range 0.424–0.686) is confounded by program structure, not temporal feature quality.

---

## E. Venue Recommendation

### Primary: MSR (Mining Software Repositories)

**Why MSR is optimal:**
- MSR explicitly values benchmark/dataset contributions and empirical studies with honest methodology
- MSR welcomes negative/null results when methodology is rigorous
- SBG V4's pre-registration, cluster bootstrap, Holm-Bonferroni correction, and forensic self-audits (SC-3 bug, SP-2 bug) demonstrate the methodological rigor MSR rewards
- MSR does not penalize near-chance AUROC if the benchmark and negative findings are well-characterized

### Secondary: ISSTA (International Symposium on Software Testing and Analysis)

**Why ISSTA:**
- ISSTA publishes rigorous behavioral analysis evaluations
- The structural-semantic inversion (NC-01) is directly relevant to the testing community
- ISSTA reviewers will understand and value the SC-3/SP-2 failure mode characterization
- **Pre-submission requirement:** Add McKeeman 1998, Piech 2015, Sumner 2011 to related work

### Rejected Venues

| Venue | Reason |
|-------|--------|
| ICSE | AUROC=0.546, CI [0.477, 0.624] does not support affirmative claims. NC-01 could qualify but requires independent replication first. |
| FSE | Same barrier as ICSE. FSE requires strong affirmative empirical support. |
| NeurIPS Negative Results | Mismatched community; expects ML-specific framing and baselines SBG lacks. |
| OOPSLA | Possible but risky — Sumner et al. OOPSLA 2011 is the direct predecessor and must be cited/differentiated before OOPSLA submission. |
| ICST | Alternative lower-bar venue; accepts benchmark + negative result papers; consider if ISSTA submission fails. |

---

## F. P0 Publication Blockers

These gaps were either flagged in V2 and persist to V4, or are newly identified in V5:

| Gap ID | Missing Citation | Status in V4 | Severity |
|--------|-----------------|--------------|----------|
| GAP-V5-01 | Piech et al. ICML 2015 | **NEW GAP** — Absent from all prior art | CRITICAL |
| GAP-V5-02 | Sumner et al. OOPSLA 2011 | **NEW GAP** — Absent from all prior art | CRITICAL |
| GAP-V5-03 | McKeeman 1998 (Differential Testing) | **PERSISTS** from V2 RISK-02 | CRITICAL |
| GAP-V5-04 | EvoSuite (Fraser & Arcuri 2011) | NEW | HIGH |
| GAP-V5-05 | Jiang & Su ISSTA 2009 | **PERSISTS** from V2 RISK-01 | CRITICAL |
| GAP-V5-06 | Klees et al. CCS 2018 | NEW | MEDIUM |

All four CRITICAL gaps must be resolved — citations added to `PRIOR_ART_MATRIX.md` with explicit SBG deltas — before any external submission.

---

## G. Recommended Abstract First Sentence

> "We present a systematic benchmark of 3,577 labeled program pairs for behavioral change detection, and report that execution-volume shortcuts — specifically exception-rate features — consistently dominate richer multi-dimensional behavioral representations, establishing fundamental limitations of current trace-level abstractions for semantic mutation detection."

This framing is:
- Fully supported by V4 evidence
- Defensible against reviewer scrutiny
- Honest about the negative results
- Positions the benchmark as the primary contribution
- Does not require the AUROC claim to carry the novelty argument

---

*Novelty audit completed by Bob (IBM), grounded in V4 frozen experimental evidence. All findings are traceable to specific experimental results in `docs/v4/V4_FINAL_SCIENTIFIC_REPORT.md` and prior audit documents.*
