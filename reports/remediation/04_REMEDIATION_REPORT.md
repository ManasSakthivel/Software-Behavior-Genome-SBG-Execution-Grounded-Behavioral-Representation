# 04. Remediation report: what is fixed and what remains

Branch `remediation/ieee-access-audit` (local, not pushed), from `dc09fe4`.
Detail: `01_ISSUE_INVENTORY.md` (findings), `02_CLAIMS_AND_PROTOCOL.md` (numbers),
`03_EVALUATION_PLAN.md` (next steps), `05_CHANGELOG.md` (files).

## Bottom line

The code and documentation defects that could be fixed safely are fixed and
covered by regression tests. **The scientific position has not improved**: the
test split is observed (not held out), the benchmark has a label defect, and the
headline AUROC (0.60 on 7 programs) is within noise and confounded by edit size.
**The paper is not publication-ready.** The evidence-driven gate reports 8/20 PASS,
12 BLOCKED.

## Validation (actual results)

| Check | Result | Log |
|---|---|---|
| `pytest sbg/ tests/`, Python 3.13 | **732 passed**, exit 0 (baseline 657) | `logs/final_pytest_py313.txt` |
| `pytest sbg/ tests/`, Python 3.9 | **732 passed**, exit 0 (baseline 2 failed) | `logs/final_pytest_py39.txt` |
| `consistency_check.py` | **10/10 pass**, exit 0, ~0.2 s (baseline: ~28 min, 9/10) | run at end |
| `audit_recompute.py` | six reference AUROCs reproduce within 1e-5, exit 0 | `results/audit_recompute.json` |
| `verify_v6_unchanged.py` | 13 programs, 0 violations, no nondeterminism, exit 0 | `logs/verify_v6_unchanged_after_fix.txt` |
| Clean checkout (`git clone` of commit `d9d6380` into a temp dir, py313) | `pytest sbg/ tests/`: **732 passed**, exit 0; `consistency_check.py`: **10/10**, exit 0 | run at commit time |
| `make check-reproduction`, `make reproduce-*` | **not run** | n/a |

Warnings: 3 (3.13) and 6 (3.9), all pre-existing (a pytest deprecation in
`sbg/extraction/static/test_error_genome.py` and a `SyntaxWarning` inside a
benchmark variant file). Plain `pytest` at the repo root still fails at
collection (fixtures under `benchmark/v5/`); the supported invocation is
`sbg/ tests/`.

## Fixed

| ID | What | Test |
|---|---|---|
| E2 | Gate/consistency fork bomb (`C1` matched `C10`). | fails against old code, passes now |
| E3 | C7 now checks per-pair entries, strictly for new artifacts. | `test_c7_*` |
| H | Python 3.9 stdlib detection. | `test_stdlib_*` |
| A3 | Input aliasing: extraction is order-independent. | `test_repeated_extraction_is_order_independent` |
| I | Machine-specific paths in two scripts. | n/a |
| A | Entry-point policy `output_free_v8` implemented (not scored). | 37 tests |
| D | Unsupported "fixed in advance" wording removed; provenance documented. | `test_threshold_provenance.py` |
| E | Hard-coded gate archived with disclaimer; `STANFORD_GATE.json` regenerated; C10 passes. | consistency C10 |
| J | Claims registry extended (C016–C023) with evidence classes and legacy annotations. | `test_claims_registry.py` |
| G | Citations checked; 3 of 4 suspect entries flagged; two missing works identified. | `CITATION_VERIFICATION.md` |
| A2 | SP-2 label defect **detected** (75 pairs; 70 fail in execution) and documented. | `test_data_integrity.py` |

## Not fixed, and why

| Item | Why it remains | Needs |
|---|---|---|
| Test split is observed (B) | Cannot be undone by code. | New programs, or exploratory labelling (owner decision). |
| SP-2 generator still emits non-equivalent variants (A2) | Fixing it changes the benchmark; relabelling or dropping pairs is prohibited. | New benchmark version, then a fresh split. |
| v8 coverage on class-based programs | 580 explicit failures on train/dev/val EQUIVALENT pairs. Trade-off, not a bug. | Owner choice among the three options in the plan. |
| Historical AUROCs affected by A, A2, A3 | Quantifying them means re-scoring the observed test split under a rule chosen after seeing it. | Fresh split. |
| τ = 0.08 provenance | No derivation artifact exists. | Authors' notes or re-derivation on dev. |
| τ\* (0.072905) inherits 9 driver-tracing dev pairs | Re-deriving would change a frozen artifact. | Re-derive under v8 on dev, new freeze. |
| Edit-size confound (C2) | Benchmark design: CHANGED edits are small, EQUIVALENT edits are large. | Generator that overlaps edit sizes across classes. |
| Learned execution-trace baseline | Design only; needs a new dependency. | Owner approval. |
| CI for 7 clusters | Percentile bootstrap unreliable. | More programs; report LOCO and per-cluster AUROC meanwhile. |
| Citations 33, 17, 39 and heading 36 content | Corrections require reading the sources. | Authors. The matrix carries flags; the JSON artifact is untouched. |
| External validity (QuixBugs/BugsInPy v7, Java, weight fitting) | Stages 2a–2f pending (`STATUS.md`). | Run after the freeze. |
| 12 of 20 gate categories BLOCKED | Evidence does not exist yet. | Above. |
| Absolute paths inside historical artifacts | Evidence; left alone. | n/a |
| Audit document | Not found; its extra findings, if any, were not checked. | Supply it. |

## Not done

* No re-execution of the committed evaluations (`make reproduce-*`,
  `make check-reproduction`). The clean-checkout run above checks the code and
  tests, not that the committed artifacts regenerate bit-for-bit; that remains
  unverified here (Python-version sensitivity applies, see `PYTHON_VERSIONS.md`).
* DBLP could not be queried (HTTP 429); Crossref and arXiv were used instead. No
  full text of any cited work was read.
* No v7 or v8 test evaluation; no v8 AUROC on any split.

## Decisions required from the experiment owner

1. Source of the fresh test programs (or accept exploratory labelling).
2. Class-program policy for v8.
3. Approval of a learned-baseline dependency.
4. Approval to repair SP-2 and bump the benchmark version.
5. Sign-off on `docs/current/EVALUATION_PLAN_V8.md` and the freeze record.
