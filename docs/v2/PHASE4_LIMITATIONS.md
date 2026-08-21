# Phase 4 Limitations

This document consolidates all genuine, disclosed limitations discovered
during Phase 4. It excludes resolved issues and includes only limitations
that remain open at the close of Phase 4. Severity tags (P0/P1/P2) and
type tags (implementation bug / scientific limitation / benchmark
limitation / genuine negative result) follow the Wave 11 hostile-review
consensus; see `docs/v2/PHASE4_GATE_REPORT.md` §5 for the full
attribution table.

## Corpus / Benchmark Scale

- The underlying benchmark contains 13 base programs. This is categorically
  too small to support cross-transformation-type, cross-language, or
  cross-regression generalization claims **in principle**, independent of
  the specific numeric results obtained. Established empirical software
  engineering venues (ICSE/FSE/ASE) typically expect corpora of 50–500+
  programs for generalization claims of this kind. *(P0, benchmark
  limitation)*

## RQ1 — Transformation-Type Generalization (H10)

- H10 is NOT_SUPPORTED for every evaluated method, including B07. The
  per-SP-type AUROC spread (0.286) is nearly 3x the pre-registered
  generalization criterion (0.10). *(P0, genuine negative result)*
- SC-3's failure is traced to a benchmark construction defect: 76.9% of
  labeled "SC-3" pairs are cosmetic quote-changes rather than the
  specified integer mutation. This is a benchmark limitation, not
  evidence about the representation's capability. *(P1, benchmark
  limitation)*
- SP-2's failure is only partially explained (entry-point mismatch
  recovers +0.03 AUROC of a much larger gap); the majority of the
  SP-2 inversion remains unexplained. *(P2, scientific limitation)*
- `sbg/extraction/dynamic/tracer.py` records only line coverage via
  `sys.settrace`, never branch coverage. This is a plausible mechanistic
  explanation for blindness to boundary/off-by-one-style mutations and
  remains unaddressed. *(P1, scientific limitation)*

## RQ2 — Cross-Language Generalization (H11)

- No real Java or JavaScript execution-tracing infrastructure exists in
  this repository. The only available diagnostic is an N=12 Python-only
  proxy (AUROC=0.182, n_changed=1), which is not statistically meaningful.
  *(P0, benchmark limitation)*
- H11 is underpowered under both the achievable design (power ≈10.7%)
  and the original pre-registered design (power ≈25%). Approximately
  120–150 pairs would be required for 80% power. No language-agnostic
  claim is made or supportable at this N. *(P2, statistical limitation)*

## RQ3 — Real Regression Detection (H12)

- No real in-repository or methodologically-approved public version-history
  corpus was available within scope; the H12 corpus is synthetic, and its
  39 control pairs are derived from the same 13 base programs via the same
  SP-transform machinery used elsewhere in the benchmark. This limits how
  "real-world" the regression-detection claim can be. *(P1, benchmark
  limitation)*
- On this corpus, the AST baseline (0.7739) substantially outperforms
  Dynamic SBG (0.5706) — the opposite of H12's motivating premise.
  *(P0, genuine negative result)*
- The point-estimate "weakly supported" reading of H12 does not survive
  Holm-Bonferroni family-wise correction (raw p=0.0659 vs corrected
  α=0.005 at Holm rank 3). Both readings are reported with equal
  prominence to avoid selective disclosure. *(P1, statistical limitation)*

## RQ4 — Observability Boundaries

- Aggregate B07 AUROC (0.528–0.529) falls entirely within the
  random-label noise-floor 95% CI ([0.461, 0.544]). Any claim of
  general, universal behavioral-equivalence detection is unsupported by
  the evidence. *(P0, genuine negative result)*
- Confound audit (Wave 9) found that wall_time_ms — a feature independent
  of B07's own DynamicGenome formula — matches B07's own discrimination
  (AUROC 0.5706 vs 0.5292). Three additional features that match or beat
  B07 (call_count_total, n_functions_called, exception_fraction) are
  near-direct constituents already fused into B07's distance formula, so
  they are not independent confounds, but their dominance suggests the
  representation is not adding value beyond simple execution-volume
  statistics. *(P0, scientific limitation)*
- Feature ablation (Wave 8) found that no single DynamicGenome dimension,
  and no leave-one-out combination (0/16 configurations total), exceeds
  the noise floor. STATE is the most load-bearing dimension by
  leave-one-out drop, but no dimension or combination independently
  demonstrates the aggregate signal is meaningful. *(P1, scientific
  limitation)*
- Entry-point discovery heuristics (name-priority list, alphabetical
  fallback, reflection-based class adapter) were engineered against this
  specific 13-program corpus and are not demonstrated to generalize to
  other codebases. *(P1, scientific limitation)*

## Methodology / Infrastructure

- `baselines/common.py::compute_auroc()` (lines 53–84) performs a naive
  stable-sort AUROC sweep with **no tie-averaging**. Impact on the main
  744-pair test set is small (naive 0.5304 vs tie-corrected 0.5434), but
  severe on H12's small/duplicated corpus (naive 0.9515 vs tie-corrected
  0.5706). This was disclosed and corrected locally within Phase 4
  analysis scripts, but deliberately **left unfixed at the shared-module
  level** to avoid silently altering frozen Phase 3B (H7–H9) results
  without re-review. This is an open item for any future phase. *(P1,
  implementation bug)*
- The modern baseline (CodeBERT) was evaluated zero-shot / off-the-shelf
  only, with no task-specific fine-tuning. Its result (AUROC=0.3697) is
  weak evidence in either direction about pretrained code representations
  generally. *(P1, scientific limitation)*
- Wave 8's feature ablation used the legacy 8-dimension v1 genome
  definition rather than V2's actual 5-field `DynamicGenome` schema,
  disclosed inline as a `methodology_note`. Not a fabrication, but an
  inconsistency that should be reconciled before any future publication
  attempt. *(P2, implementation limitation)*
- Memory and CPU usage were not tested as shortcut candidates in Wave 9
  because no such instrumentation exists in `tracer.py` / `runner.py`.
  Explicitly disclosed as UNAVAILABLE rather than imputed or omitted
  silently. *(P2, scientific limitation)*

## What Remains Genuinely Unresolved

- Whether SC-3's underlying phenomenon (semantic changes invisible to
  execution traces) exists independently of the benchmark mislabeling
  that was found — the mislabeling explains most, not necessarily all,
  of the SC-3 gap.
- Whether a properly powered, real (not synthetic) cross-language corpus
  would show a materially different H11 result.
- Whether a properly powered, real (not synthetic-control) regression
  corpus would change the H12 finding that AST outperforms Dynamic SBG.
- Whether branch-coverage instrumentation (not currently implemented)
  would resolve any portion of the SC-3/SP-2 failures.

These are documented as open questions, not resolved by Phase 4, and are
explicitly out of scope for further action within Phase 4 per the
mission's stop condition.
