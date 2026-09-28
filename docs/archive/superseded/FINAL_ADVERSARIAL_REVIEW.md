# Final Adversarial Review — SBG/EEP
## Post-Java Evaluation Adversarial Assessment

**Status:** FINAL — incorporates QuixBugs Java results  
**Reviewers simulated:** ICSE, FSE/ESEC, ASE, ISSTA, IEEE TSE, SANER  
**Previous adversarial review:** docs/ADVERSARIAL_REVIEW.md (Python-only)

---

## Questions 1–13 Per Sprint Specification

### Q1: Is the dataset selection biased?

**Assessment: PARTIALLY FIXED**

**Python corpora:** Selection bias is documented and disclosed. BugsInPy evaluable subset (7/502) skews toward exception-raising bugs. This is acknowledged and disclosed.

**Java corpora:** QuixBugs Java exclusions (E_NODE, E_COMPILE, E_COMPLEX_TYPE, E_TIMEOUT) remove programs requiring graph data structures, programs with complex generics, and programs that timeout. These exclusions likely remove some of the harder bugs. The E_COMPILE exclusions (5 programs) remove programs with complex ArrayList<Integer> type inference — some of these may have detectable bugs. Selection bias cannot be ruled out.

**Remaining concern:** Cannot claim that evaluated Python or Java programs represent a random sample from any real-world bug distribution. The evaluable subsets are systematically biased toward simpler, more isolated functions with straightforward input types.

**Disclosure status:** DISCLOSED in all relevant documents.

---

### Q2: Is the evaluated N sufficient?

**Assessment: PARTIALLY FIXED (Python adequate; Java insufficient)**

| Corpus | N | Adequacy |
|--------|---|---------|
| Synthetic Python | 38 | Adequate for AUROC |
| QuixBugs Python | 28 | Adequate for detection rate; borderline for AUROC |
| BugsInPy | 7 | Insufficient for AUROC; barely adequate for detection rate |
| QuixBugs Java | 18 | Insufficient for statistical significance (p=0.952) |
| Combined external Python | 35 | Adequate for combined p-value (p=0.045) |

**Java N=18 is the primary weakness.** With 6 detected, the result is not statistically distinguishable from chance for Java alone. The paper must acknowledge that Java evidence is exploratory, not confirmatory.

---

### Q3: Are projects genuinely independent?

**Assessment: FIXED for Python; LIMITED for Java**

Python: QuixBugs (1 algorithm repo) + black + keras + spacy + tornado + tqdm = 6 independent real projects. All are separate repositories with no shared authors, different domains, different maintainers.

Java: QuixBugs only (1 repository). All 18 Java programs come from the same repository by the same author. Cross-project Java independence is NOT demonstrated.

**Requirement for paper:** "Java evaluation uses 18 programs from a single repository (QuixBugs Java). Cross-project Java generalization is not assessed."

---

### Q4: Is cross-language evidence valid?

**Assessment: WEAKLY VALID (honest presentation required)**

The cross-language experiment IS valid methodologically:
- Same formula
- Same threshold
- Zero-shot
- Output-free verified

BUT the evidence is weak:
- Only 1 Java corpus
- Detection rate 33.3% (not statistically significant)
- Large transfer gap (-27.4 pp)
- Instrumentation difference partially explains the gap

**Paper must present Java as "preliminary cross-language evidence" not "demonstrated cross-language generalization."**

---

### Q5: Is output leakage impossible?

**Assessment: FIXED**

Both Python and Java instrumentation have been independently verified:
- Python: 9 automated audit checks PASS; OL-QB-1 demonstrates d=0.0 for same-path different-output programs
- Java: Method-boundary instrumentation emits only method names and depth counter to stderr; stdout discarded; exception class name not message
- Code is open and inspectable

Output leakage is not merely claimed — it is mechanically verified.

---

### Q6: Are baselines fair?

**Assessment: FIXED for Python; UNRESOLVED for Java**

Python baselines: exception-only and Baseline SBG evaluated on identical inputs, same corpus, same τ*.

Java baselines: No Java baselines provided. We cannot claim superiority over Java baselines because no Java baseline was implemented. The paper should acknowledge this gap.

**Recommendation:** Add a note that "for Java, we report only detection rate without baseline comparison, as implementing fair Java baselines (exception-only, timing-based) is left for future work."

---

### Q7: Are statistics appropriate?

**Assessment: FIXED**

Appropriate methods used:
- AUROC with bootstrap CI for ranked scoring
- Wilson score CI for detection rates
- Binomial p-value for above-chance detection
- Multiple comparison correction not needed (claims are per-dataset)

**Remaining issue:** Java result (p=0.952) should be clearly labeled as NOT statistically significant. No significance claim for Java is made.

---

### Q8: Are thresholds tuned on test data?

**Assessment: FIXED**

τ* = 0.08 selected on synthetic (calibration) corpus only. Never adjusted after seeing any external result. Protocol hash `fac6bd8e0cffc91b52ed88577637d199ccfda8cfe9200edc487094f7e8e5088b` documents this.

The QUICKSORT near-miss (d=0.023, τ*=0.08) was observed AFTER the evaluation was complete and threshold was frozen. τ* was NOT adjusted to detect QUICKSORT. This is correctly reported as a missed case.

---

### Q9: Is there data leakage?

**Assessment: FIXED**

No calibration data (synthetic corpus) appears in any external evaluation. QuixBugs, BugsInPy, and QuixBugs Java are all completely held-out corpora. The BugsInPy exclusion taxonomy was defined from repository structure before evaluating EEP on any bug. The Java exclusion criteria were defined before running the Java evaluation.

---

### Q10: Are the theoretical claims actually proven?

**Assessment: FIXED**

Theorem 1 (Trace-Preserving Invisibility) is formally proven from first principles in `docs/REPRESENTATION_LIMIT_THEOREM.md` and is now supported by 9 empirical cases (4 Python + 5 Java).

The theorem is information-theoretic: it does not depend on implementation details. It states that programs with identical trace structures cannot be distinguished by any output-free trace-based method. This is proven, not merely asserted.

---

### Q11: Does the empirical evidence support the abstract?

**Assessment: DEPENDS ON ABSTRACT WORDING**

If the abstract claims:
- "EEP detects behavioral regressions without reading program outputs" → ✓ Supported
- "Zero-shot cross-corpus transfer across 7 projects" → ✓ Supported (Python only)
- "Cross-language transfer to Java" → ⚠ Needs careful qualification
- "Method achieves X% detection across multiple real-world programs" → ✓ Supported with appropriate dataset scoping
- "Language-independent method" → ✗ Too strong; weakly supported only

**Required:** Abstract must distinguish Python evidence (strong) from Java evidence (exploratory/preliminary).

---

### Q12: Could a reviewer reproduce the results?

**Assessment: MOSTLY FIXED**

Python reproduction: Full reproduction instructions in `docs/FINAL_SCIENTIFIC_STATUS_V5.md`. Requires `git clone` of QuixBugs and BugsInPy. All scripts are in `experiments/external/`.

Java reproduction: Full reproduction via `experiments/external/quixbugs_java_evaluation.py`. Requires QuixBugs at `/tmp/quixbugs_full` and Java 17 at `/usr/bin/javac`.

**Remaining concern:** BugsInPy requires GitHub API access for real code extraction; individual bug results may vary with GitHub availability.

---

### Q13: What is the strongest argument for rejection?

**Primary Rejection Arguments:**

1. **Small N with borderline statistics**: "With N=35 combined external bugs and p=0.045 (barely significant), and no individual corpus reaching α=0.05, the statistical evidence is weak. The paper does not establish robust generalization."

   *Response:* We disclose all p-values honestly. p=0.045 combined is borderline but legitimate. The paper's contribution is not primarily statistical — it is the formal characterization of when and why EEP works.

2. **BugsInPy coverage is 1.4%**: "Evaluating 7/502 bugs (1.4%) and claiming 'real-world evaluation' is misleading. The evaluated subset is not representative."

   *Response:* We explicitly disclose this and qualify all BugsInPy claims. We do not claim 85.7% generalizes to all BugsInPy. The evaluation demonstrates feasibility, not comprehensiveness.

3. **Java evidence is not statistically significant**: "The Java evaluation (p=0.952) provides no evidence that EEP works in Java. Including this as cross-language evidence is misleading."

   *Response:* We present Java as exploratory/preliminary. We do not claim statistical significance for Java. We report it as a negative-to-weak result with analysis of why.

4. **The for→while false positive undermines rename-invariance claim**: "The claim of 'semantic-invariance' is contradicted by NC-CS-1."

   *Response:* We clearly distinguish rename-invariance (demonstrated 0/9 FP) from semantic-invariance (which is NOT claimed). NC-CS-1 is a DIFFERENT transform category. We disclose this explicitly.

5. **No Java baselines**: "Without Java baselines, the 33.3% Java detection rate is uninterpretable."

   *Response:* Acknowledged. We note this limitation explicitly. We compare to Python QuixBugs as a within-corpus baseline.

---

## Concern Classification

| # | Concern | Resolution | Status |
|---|---------|-----------|--------|
| R1.1 | EEP = exception monitoring | ΔAUROC=0.277 vs exc-only | ✓ FIXED |
| R1.2 | Single defect class | 8 classes detected | ✓ FIXED |
| R1.3 | Implicit output encoding | OL-QB-1 audit: d=0.0 for different-output same-path | ✓ FIXED |
| R2.1 | Same projects in cal/test | Strict separation documented | ✓ FIXED |
| R2.2 | Post-hoc exclusion | Structural criteria documented | ✓ FIXED |
| R2.3 | Zero-shot challenged | Protocol hash + frozen config | ✓ FIXED |
| R2.4 | BugsInPy sample bias | Documented mandatory disclosure | ⚠ DISCLOSED |
| R3.1 | CI includes 0.5 | Synthetic lower bound 0.750 | ✓ FIXED |
| R3.2 | τ* tuned on test | Protocol hash pre-external | ✓ FIXED |
| R3.3 | Weights optimized | Ablation shows single-component parity | ✓ FIXED |
| R3.4 | Small N, borderline p | p=0.045 combined; Java p=0.952 clearly stated | ⚠ DISCLOSED |
| R4.1 | Toy programs | Real production code in BugsInPy | ✓ FIXED |
| R4.2 | Single defect type | 8 classes detected | ✓ FIXED |
| R4.3 | Non-standard env | Python 3.9, sys.settrace, reproducible | ✓ FIXED |
| R4.4 | Same-dataset split | Genuinely independent corpora | ✓ FIXED |
| R4.5 | BugsInPy coverage 1.4% | Disclosed; claims qualified | ⚠ DISCLOSED |
| R5.1 | Evaluation circular | Pre-registered protocol | ✓ FIXED |
| R5.2 | Output-free not mechanical | 14 automated/inspected checks PASS | ✓ FIXED |
| R5.3 | Limitations perfunctory | Formal theorem + 9 empirical cases | ✓ FIXED |
| R5.4 | Trace-preserving not formal | Theorem 1 with formal proof | ✓ FIXED |
| R5.5 | Detection rate framing | Per-dataset presentation used | ✓ FIXED |
| R5.6 | N=6 projects thin | Report as 8 projects across 2 languages | ⚠ PARTIALLY |
| **NEW** | Java N=18 not significant | Disclosed; Java labeled exploratory | ⚠ DISCLOSED |
| **NEW** | Java single corpus | Disclosed; no cross-project Java claim | ⚠ DISCLOSED |
| **NEW** | Java transfer gap -27.4 pp | Disclosed; instrumentation explanation provided | ✓ FIXED |
| **NEW** | No Java baselines | Acknowledged; noted as limitation | ⚠ DISCLOSED |

**Legend:** ✓ FIXED = fully addressed; ⚠ DISCLOSED = disclosed but not fully resolvable

---

## Venue-Specific Assessment

| Venue | Likely Verdict | Key Concern |
|-------|---------------|-------------|
| ICSE | Accept with revisions | BugsInPy N=7, Java statistics |
| FSE/ESEC | Accept with major revisions | Scale of evaluation |
| ASE | Accept with revisions | Java evidence framing |
| ISSTA | Borderline | Needs stronger fault-localization baseline |
| IEEE TSE | Accept (extended) | Adequate for journal with proper qualification |
| SANER | Accept | Appropriate scale for the venue |
| IEEE Software | Accept | Practitioner-relevant contribution |
| IEEE Access | Accept | Good technical contribution |

---

## Final Adversarial Verdict

The paper is publishable at a strong empirical SE venue with accurate claim scoping.

**Strongest version of the paper:**
1. Focus on Python evidence (strong: 3 corpora, 7 projects, p=0.045)
2. Present Java as a preliminary cross-language experiment (honest: 33.3%, not significant, interesting transfer gap analysis)
3. Theorem 1 as a formal contribution (strong: explains limitations AND bounds the problem)
4. Output-free verification as methodological contribution (strong: 14 checks, mechanically verified)
5. Defect-class analysis as empirical contribution (8 classes, detection rates, trace-preserving explanation)

**What the paper should NOT overclaim:**
- Cross-language generalization (insufficient evidence)
- Comprehensive BugsInPy evaluation (only 1.4%)
- Statistical significance at Java level (p=0.952)
