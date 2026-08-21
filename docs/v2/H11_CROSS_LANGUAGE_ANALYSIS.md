# H11 — Cross-Language Generalization: Phase 4 Wave 5 Final Analysis

**Status:** INSUFFICIENT_EVIDENCE / UNDERPOWERED (pre-registered fallback verdict)
**Script:** `experiments/v2/run_h11_wave5.py`
**Artifact:** `artifacts/v2/H11_CROSS_LANGUAGE_RESULTS.json`
**Builds on:** Wave 0 Agent B (infrastructure audit) and Agent G
(`docs/v2/H11_CROSS_LANGUAGE_DESIGN.md`, `experiments/v2/cross_language_design.py`)

---

## 1. What changed since Wave 0

Wave 0's Agent B/G audit concluded no Java execution was possible and
therefore designed the maximal achievable fallback: an N=12 Python-only
"style diagnostic." Wave 5 re-ran that audit and additionally checked
whether a JDK was actually installed on this machine:

```
$ which javac java
/usr/bin/javac
/usr/bin/java
$ javac -version
javac 17.0.18
$ java -version
openjdk version "17.0.18" 2026-01-20 (IBM Semeru / OpenJ9)
```

**A JDK IS present.** This does *not* change the infrastructure conclusion,
because H11 requires an execution-derived `DynamicGenome` for Java —
i.e. a trace-based feature extractor analogous to
`sbg/extraction/dynamic/tracer.py` (which is built entirely on Python's
`sys.settrace` and has no Java analogue). Having `javac`/`java` available
only means one *could* compile and run a Java program; it provides no
instrumentation, no JVMTI agent, no bytecode rewriter, and no
Java-trace-to-`DynamicGenome` mapping. Building that pipeline is
multi-day-to-multi-week infrastructure work, explicitly out of scope per
the Phase 4 mandate ("DO NOT spend excessive time installing huge
infrastructure if the environment cannot support it"). The correct,
honest conclusion is unchanged from Wave 0: **no legitimate
execution-grounded Python↔Java comparison is possible within Phase 4's
scope**, despite the JDK's presence.

This is recorded explicitly in the artifact's `infrastructure_audit` block
so future work is not misled into thinking "Java is unavailable" — it is
available for *compilation and running*, just not for *DynamicGenome
extraction*.

---

## 2. What WAS executed this wave

Per the Agent-G design, the one achievable, non-fabricated diagnostic was
run to completion using the **production** `DynamicGenomeExtractor` (same
code path as B07), plus Static SBG (V1 proxy, `v1_behavioral_distance`) and
AST similarity (B02) for comparison — all on the same N=12 pairs:

- 11 pairs: same behavioral specification, Python-idiomatic implementation
  vs. a second Python implementation deliberately written in
  Java-idiomatic style (explicit index variables, `while` loops, temp
  variables) — labeled EQUIVALENT.
- 1 pair: a deliberately introduced off-by-one bug in the Java-style
  binary-search implementation — labeled CHANGED.

### 2.1 Results

| Method | AUROC | 95% CI | Permutation p | EQUIV mean sim | CHANGED mean sim |
|---|---|---|---|---|---|
| Dynamic SBG (B07 code path) | 0.1818 | [0.00, 0.50] | 0.413 | 0.898 | 0.957 |
| Static SBG (V1 proxy) | 0.1818 | [0.00, 0.50] | 0.417 | 0.789 | 0.951 |
| AST (B02) | 0.1818 | [0.00, 0.50] | 0.417 | 0.464 | 0.716 |

All three methods point in the **same direction**: the single CHANGED
(off-by-one) pair is scored as *more* similar than most of the 11
EQUIVALENT pairs — an inversion, consistent in direction with Phase 5's
independent AUROC=0.4091 regex-heuristic result and with H9's broader
finding that off-by-one/boundary mutations (SC-3-like) are hard for all
current methods to detect.

### 2.2 Critical caveat — this result is NOT statistically meaningful

**n_changed = 1.** With only one positive example, AUROC is a single
rank statistic (position of one point among 12), not an estimate with
usable precision:

- The bootstrap 95% CI collapses to **[0.00, 0.50]** for every method —
  because most bootstrap resamples either omit the sole CHANGED example
  entirely or duplicate it, both of which trivially bound AUROC away from
  meaningful values.
- The permutation p-value is **≈0.41–0.42 for all three methods** —
  statistically indistinguishable from random label assignment.

**Conclusion: the inversion direction is a suggestive, cross-method-
consistent signal, not a confident finding.** It should be read as "this
diagnostic did not provide reassuring evidence," not as "cross-language
generalization is disproven." With n_changed=1, no verdict stronger than
"non-informative" is defensible. This is recorded in the artifact as
`critical_caveat`.

---

## 3. Statistical power

Per the pre-registration (`docs/v2/H11_CROSS_LANGUAGE_DESIGN.md` §3):

```
Pre-registered target N=15 → ~25% power at α_corrected=0.0042
Required N for 80% power  → ~120-150 pairs
```

Wave 5's own crude re-derivation (documented in the artifact as a
sanity check, not a replacement — see `power_discrepancy_note`) lands in
the same "severely underpowered" regime (~11–14% at N=12–15). The
pre-registered figures are treated as authoritative per Wave 10 discipline
(no new tests invented after seeing results).

**N=12 (achievable) is even smaller than the already-underpowered
pre-registered N=15 target**, and both are roughly an order of magnitude
below the ~120–150 pairs needed for 80% power. No AUROC value obtained
at this N — in either direction — can be interpreted as evidence for or
against H11.

---

## 4. Phase 5 proxy — reconfirmed as invalid H11 evidence

`artifacts/phase5/cross_language_results.json` (N=15, regex-heuristic
Java-source features, AUROC=0.4091) is retained in the final artifact
as `phase5_proxy_context_only`, explicitly marked `valid_h11_evidence:
false`, for the same reasons Agent G documented at Wave 0: not
execution-derived, unreliable recursion-detection heuristic, and CI
spanning nearly the full [0,1] range at N=15.

---

## 5. Final H11 Verdict

```
H11 verdict:          INSUFFICIENT_EVIDENCE / UNDERPOWERED
Formal claim tested:  AUROC(cross_language, test) > 0.6
Java execution:       NOT PERFORMED (no execution-tracing infra; JDK
                       presence does not change this — see §1)
Achievable diagnostic: N=12 Python-style lower bound, AUROC=0.1818,
                        but n_changed=1 → non-informative (CI=[0,0.5],
                        permutation p≈0.41)
Power at N=12:         ~11% (this analysis) / N=15 pre-registered: ~25%
                        (authoritative)
Required N for 80%:    ~120-150 (pre-registered)
Fabrication:            NONE — no Java DynamicGenome was computed
```

This is the pre-registered fallback verdict, not a failure of the
experiment. H11 remains **open**; a real Python↔Java (or Python↔JS)
execution-tracing pipeline with a properly powered corpus (N≥120) is
required future work, explicitly deferred, and explicitly NOT attempted
under time/scope pressure in Phase 4.

---

## 6. Cross-reference

| Document | Relation |
|---|---|
| `docs/v2/H11_CROSS_LANGUAGE_DESIGN.md` | Wave 0 design & infrastructure audit (superseded only on the "is a JDK present" sub-question; verdict unchanged) |
| `experiments/v2/cross_language_design.py` | N=12 pair definitions (unmodified, reused as-is) |
| `experiments/v2/run_h11_wave5.py` | This wave's execution script |
| `artifacts/v2/H11_CROSS_LANGUAGE_RESULTS.json` | Full results, per-pair scores, power analysis |
| `artifacts/phase5/cross_language_results.json` | Non-execution proxy, context only |
