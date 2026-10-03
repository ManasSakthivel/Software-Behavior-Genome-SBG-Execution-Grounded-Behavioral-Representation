# Phase 2 pre-registration

Written 2026-09-28, before any Phase 2 result existed. Every rule below is fixed
before the data it governs is scored. Its SHA-256 is recorded in
`artifacts/final/PHASE2_FREEZE.json`. Where an artifact later departs from this
document, the artifact must say so and why.

## 1. Protocol `output_free_v7`

`output_free_v6` plus one extra tier for programs whose API is class-based.

- **Tier order.** The v6 function selection runs first, unchanged. The class
  tier runs **only** when v6 finds no eligible function. Every program v6
  already covers keeps its exact v6 entry and inputs, so its v6 results
  reproduce.
- **Eligible classes.** Top-level `ClassDef`s defined in the module. Excluded:
  a leading underscore, a name starting with `Test`, subclasses of
  `BaseException`, and classes with unimplemented abstract methods. A
  constructor's required positional parameters must all map to a battery under
  the v6 `annotation_family` rule. As in v6, an unannotated parameter maps to
  the list battery.
- **Eligible methods.** Public (no leading underscore) callables defined on the
  class or on a base class defined in the same module, with every required
  parameter synthesisable under the same rule. Properties are excluded. Methods
  are ordered alphabetically.
- **Driver.** One trace per (eligible class `C`, battery index `i`,
  `i = 0..10`). Classes are ordered alphabetically. The steps are:
  1. Construct `C` from battery values at index `i`, using v6's zip rule.
  2. Run `L = 8` steps. Step `k` calls `methods[(i + k) % len(methods)]` with
     battery values at index `(i + k) % 11`.
  3. Deep-copy every argument before each call.
  4. Let an exception propagate and end the trace, exactly as in the function
     tier.

  The driver never reads a return value or an attribute. It is output-free by
  construction. The driver is harness code and is identical for base and
  variant.
- **Out of scope.** A program with no eligible function and no eligible class
  is `unsupported_signature`, as in v6.
- **Budgets.** Unchanged from v6: 1 s per trace, 60 s per program, and
  non-termination after 2 timeouts.
- **No per-program drivers.** Hand-written drivers are used only in the
  driver-synthesis validation suite, never as evaluation input.

## 2. Validity set under v7

A CHANGED pair is statically valid iff its mutation lies in code statically
reachable from the v7 entry, using a within-module call graph resolved by name:

- For a function entry, reachability starts from the entry function.
- For a class entry, it starts from the driven constructors and eligible
  methods.

Uncompilable pairs are invalid, as before. The rule is computed without
executing anything and without reference to any score.

## 3. Threshold τ\*

- Derived on the **dev** split of `benchmark/datasets/v6`, statistically valid
  pairs only, under `output_free_v7`, from SBG V5 distances.
- **Rule:** maximise Youden's J = TPR − FPR over candidate thresholds (the
  midpoints between consecutive sorted unique distances). Ties go to the
  smaller threshold.
- The value is frozen to `artifacts/final/THRESHOLD_FROZEN.json` together with
  the SHA-256 of the dev pair file. No test-split or external label is read
  while deriving it.
- A cluster bootstrap of τ\* over dev programs is reported as a stability
  diagnostic only. It is never used to choose τ\*.

## 4. Weighting

The models are fitted on **train**-split valid pairs only, under
`output_free_v7`.

- **M0.** V5 with its fixed weights (0.50 / 0.25 / 0.25). This is the
  reference.
- **M1.** Logistic regression on `[sbg_v3, sbg_temporal, sbg_state]`.
- **M2.** Logistic regression on nine execution features: `sbg_v3`,
  `sbg_temporal`, `sbg_state`, `exception_fraction`, `exception_component_v3`,
  `exception_type_jaccard`, `call_count`, `n_functions`, `coverage_size`.

Fitting procedure:

- Features are standardised with train mean and standard deviation.
- The loss is mean log-loss plus `1.0 * ||w||^2 / n_train`.
- Optimisation is full-batch gradient descent: learning rate 0.5, 5000
  iterations, zero initialisation. It is deterministic and needs no seed.
- The code is pure Python, with no numpy.

Selection and reporting:

- The model is chosen on **dev** AUROC among M0, M1 and M2.
- **Test is scored once.** All three models are reported, whichever is chosen.
- If the chosen model is not M0, the claim uses it only if its paired ΔAUROC
  over M0 on test is significant after Holm correction. Otherwise the claim
  stays with M0 and says so.

## 5. Primary test evaluation

- Data: `benchmark/datasets/v6`, test split, under `output_free_v7`. Scored
  once.
- Sets and statistics are unchanged from v6:
  - the three denominators (ALL, EVALUABLE, VALID);
  - a cluster bootstrap by base program;
  - within-cluster permutation with the (b+1)/(m+1) estimator;
  - a label-shuffle noise floor.
- The Holm family contains paired ΔAUROC of SBG V5 against six comparators:
  `static_ast`, `static_token`, `exception_fraction`, `call_count`, `sbg_v3`
  and the dev-selected model.

## 6. External corpora (real programs)

The common rules apply to every corpus.

**Freeze before scoring.** The corpus is pinned to an upstream commit. The
manifest is written and hashed before any pair is scored, and the hash is
recorded in the result artifact. Each manifest entry records: id, source
repository, commit, path, license, interface, eligibility, exclusion reason and
split. Split is `external_test` for every program, so none is used for
development.

**Positives.** The real bug: the buggy version against its fixed version.

**Negatives.** The fixed version against semantics-preserving variants of
itself, made by the repository's SP transformers.

- Up to three variants per program.
- Transformations are tried in the fixed order SP-1, SP-2, SP-4, SP-6, SP-10,
  SP-3, SP-5, SP-9, with seed 0.
- The first three that compile and whose AST differs from the original are
  kept.

The negatives are generated before any score is computed.

**Metrics.**

- SBG V5 AUROC with a cluster bootstrap by program.
- Detection rate of positives and false-positive rate of negatives at the
  frozen τ\*, each with a Wilson interval.
- Every execution predictor and both static baselines, with paired ΔAUROC and
  Holm correction.
- An output-reading reference, labelled as such and never attributed to SBG.

### QuixBugs (Python)

- **Canonical input regime (primary).** Protocol inputs.
- **Declared input regime (secondary).** Only the input half of QuixBugs'
  `json_testcases`. Expected outputs are discarded when the file is loaded.
- The `*_test.py` harness files and `node.py` are scaffolding and are never
  scored.

### BugsInPy

- **Unit.** Function-level. Each function changed by the fix is extracted at
  the buggy commit and at the fixed commit.
- **Eligibility.** Static. The extracted unit must reference only builtins,
  the standard library, and names defined inside the unit. It must also be
  executable under `output_free_v7`.
- **Exclusions.** Every bug in the upstream list is accounted for, with a
  reason.
- **Inputs.** The canonical regime only.

### Java (QuixBugs Java)

Java counts as an **SBG** evaluation only if Java traces produce the same
feature schema: the V3 genome, the temporal genome and the state genome.

- If they do not, the Python-to-Java generalisation claim is removed.
- Any reduced-representation Java run is reported as exploratory and outside
  the SBG claims.
- Inputs must not come from, or be checked against, expected outputs.

## 7. Evidence-driven gate

`experiments/final/stanford_gate.py` decides each category from artifacts on
disk. There is no hard-coded verdict. PASS means the required evidence exists
and its integrity checks pass. It does **not** require SBG to perform well: a
measured negative result can pass. BLOCKED means required evidence is missing.
The labels "scoped", "framework ready" and "conditional" do not exist.

Evidence-volume floors are fixed here, before the data exists:

- **Real-program validity.** At least one external real-program corpus is
  scored, with at least 20 evaluated programs.
- **Stateful validity.** At least 3 test-split programs are evaluated through
  the class tier. The driver-synthesis validation suite passes.
- **Benchmark quality.**
  - Every excluded program carries a failure kind.
  - Across the main test split and the external corpora, at least 40 programs
    are evaluated, of which at least 20 are real.
  - Program-disjointness checks pass.
- **External validation.**
  - A QuixBugs artifact and a BugsInPy artifact exist, and each covers its
    full frozen manifest.
  - For Java, either an SBG-schema artifact exists, or a claim-removal record
    exists and no current document makes a Java claim.
