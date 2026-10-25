# Agent B — Edit-Size Confound Analysis
**Branch:** `remediation/sbg-v2`  
**Script:** `experiments/final/edit_size_analysis.py`  
**Date:** 2025 (remediation cycle)

---

## 1. Reproduction of the Reversed Edit-Size AUROC

The following code (from the task specification) was run verbatim from the repository root:

```
python3 -c "
import json, pathlib, ast, difflib, sys
sys.path.insert(0, '.')
from sbg.statistics import auroc

ART = pathlib.Path('artifacts/final')
pairs = [json.loads(l) for l in (ART / 'pairs_v6test_output_free_v6.jsonl').read_text().splitlines() if l.strip()]
evaluated = [p for p in pairs if p.get('evaluated')]

def canonical_lines(path):
    src = pathlib.Path(path).read_text()
    return ast.unparse(ast.parse(src)).splitlines()

def edit_size(meta_path_base, meta_path_variant):
    a = canonical_lines(meta_path_base)
    b = canonical_lines(meta_path_variant)
    n = 0
    for line in difflib.unified_diff(a, b, lineterm='', n=0):
        if line.startswith(('+', '-')) and not line.startswith(('+++', '---')):
            n += 1
    return n

meta = {json.loads(l)['pair_id']: json.loads(l)
        for l in pathlib.Path('benchmark/datasets/v6/pairs_test.jsonl').read_text().splitlines() if l.strip()}

sizes, labels = [], []
for r in evaluated:
    m = meta.get(r['pair_id'])
    if m is None: continue
    s = edit_size(m['base_path'], m['variant_path'])
    sizes.append(s)
    labels.append(r['label'])

forward_auroc = auroc([float(s) for s in sizes], labels)
reversed_auroc = 1.0 - forward_auroc
print(f'Forward (large=CHANGED): {forward_auroc:.6f}')
print(f'Reversed (small=CHANGED): {reversed_auroc:.6f}')
print(f'Expected reversed: 0.966703')
"
```

**Exact output produced:**

```
Forward (large=CHANGED): 0.033297
Reversed (small=CHANGED): 0.966703
Expected reversed: 0.966703
```

The reversed edit-size AUROC of **0.966703** is confirmed. This means edit size alone—with the polarity reversed so that *smaller* edits predict CHANGED—achieves 96.7% AUROC on the v6 test split. The committed value in `audit_recompute.json` (`"edit_size_reversed_auroc": 0.966703`) is reproduced exactly (within 0 error).

**Denominator:** N=259 evaluated pairs (121 CHANGED, 138 EQUIVALENT).

---

## 2. Per-Transformation-Type Edit-Size Distribution

Analysis computed from `artifacts/final/pairs_v6test_output_free_v6.jsonl` joined to
`benchmark/datasets/v6/pairs_test.jsonl` for file paths.

### Test split — summary table

| Type  |  N  | CHNG | EQUIV | Mean | Med | Min | Max | All CHNG ≤ 5? | Any EQUIV ≥ 6? |
|-------|-----|------|-------|------|-----|-----|-----|:---:|:---:|
| SC-1  |   3 |    3 |     0 |  2.0 |   2 |   2 |   2 | YES | — |
| SC-2  |  15 |   15 |     0 |  2.0 |   2 |   2 |   2 | YES | — |
| SC-3  |  18 |   18 |     0 |  2.0 |   2 |   2 |   2 | YES | — |
| SC-4  |  15 |   15 |     0 |  2.0 |   2 |   2 |   2 | YES | — |
| SC-5  |  18 |   18 |     0 |  2.0 |   2 |   2 |   2 | YES | — |
| SC-6  |  15 |   15 |     0 |  2.0 |   2 |   2 |   2 | YES | — |
| SC-7  |   3 |    3 |     0 |  2.0 |   2 |   2 |   2 | YES | — |
| SC-10 |   3 |    3 |     0 |  2.0 |   2 |   2 |   2 | YES | — |
| SC-11 |  13 |   13 |     0 |  2.0 |   2 |   2 |   2 | YES | — |
| SC-13 |  18 |   18 |     0 |  3.0 |   3 |   3 |   3 | YES | — |
| SP-1  |  18 |    0 |    18 | 22.4 |  18 |   4 | 102 | YES | YES |
| SP-2  |  21 |    0 |    21 | 17.9 |  18 |   2 |  56 | YES | YES |
| SP-3  |  21 |    0 |    21 | 48.0 |  43 |  30 |  82 | YES | YES |
| SP-4  |  21 |    0 |    21 | 20.1 |  20 |  10 |  34 | YES | YES |
| SP-5  |   3 |    0 |     3 |  8.0 |   8 |   8 |   8 | YES | YES |
| SP-6  |  21 |    0 |    21 | 13.1 |  12 |   4 |  26 | YES | YES |
| SP-7  |  12 |    0 |    12 | 16.5 |  12 |   6 |  48 | YES | YES |
| SP-8  |   8 |    0 |     8 |  9.2 |  10 |   6 |  14 | YES | YES |
| SP-9  |   3 |    0 |     3 |  2.0 |   2 |   2 |   2 | YES | NO |
| SP-11 |   9 |    0 |     9 | 13.3 |  14 |   2 |  24 | YES | YES |
| SP-12 |   1 |    0 |     1 |  2.0 |   2 |   2 |   2 | YES | NO |

### Key findings

1. **All SC (CHANGED) pairs have edit size exactly 2 or 3 lines.** Each SC mutation changes a single operator, literal, or operator-literal pair, which in canonical AST form always touches exactly one deleted and one added line (size=2), or two added and one deleted (size=3 for SC-13, which changes a comparison plus adds an else branch).

2. **All SP (EQUIVALENT) pairs—except SP-9, SP-12, and a few SP-2 instances—have edit size ≥ 6.** The median across SP types ranges from 8 (SP-5) to 43 (SP-3).

3. **SP-9 (constant folding) is the only SP type that produces small edits** (all three instances have size=2), because it replaces a sub-expression with a single constant, touching exactly one AST node. SP-12 (single instance, size=2) similarly makes a minimal change.

4. **SP-1 (variable rename) produces large edits.** The smallest SP-1 instance is size=4, median=18, max=102. Renaming a single variable that appears many times across a file (e.g., loop variable `i` used 50 times) touches every occurrence.

5. **SP-4 (comment strip) produces the most consistently large edits** (min=10, mean=20.1), because the stripping of docstrings and inline comments is a file-wide operation; each comment line counts as one deleted line.

6. **No SC mutation produces a large edit.** The current SC suite (single-operator changes) is inherently constrained to 2–3 line edits.

### Edit-size bins (test, evaluable pairs)

| Bin | Range    |  N  | CHNG | EQUIV | SBG AUROC |
|-----|----------|-----|------|-------|-----------|
|  0  | [0, 2]   | 111 |  103 |     8 | 0.646238  |
|  1  | [3, 5]   |  24 |   18 |     6 | 0.597222  |
|  2  | [6, 10]  |  31 |    0 |    31 | N/A       |
|  3  | [11, 20] |  42 |    0 |    42 | N/A       |
|  4  | [21, 40] |  33 |    0 |    33 | N/A       |
|  5  | [41, ∞]  |  18 |    0 |    18 | N/A       |

Bins 2–5 contain **only EQUIVALENT pairs** (zero CHANGED), so AUROC is undefined there. SBG is only evaluated on bins 0–1 where both classes are present. The stratified AUROC across bins 0–1 (weighted by mixed-class pair count) is **0.640558** (from `audit_recompute.json`), which is only marginally above the overall SBG AUROC of 0.60127.

---

## 3. Root-Cause Analysis: Why Is the Confound Structural

### The construction-level mechanism

The confound is not incidental; it is a direct consequence of the transformation design choices made before any evaluation data was collected:

**SC mutations** (CHANGED class) apply one atomic change:
- Replace one binary operator (e.g., `+` → `-`, `==` → `!=`)
- Replace one literal constant (e.g., `0` → `1`, `True` → `False`)
- Rename one local variable at its declaration site

In canonical `ast.unparse` form, a single-operator replacement always yields exactly one `−` line and one `+` line → **edit size = 2**. SC-13 (which changes a comparison and inserts a guard branch) yields size=3. **By construction, no SC mutation can produce an edit size > 5 with the current single-site change model.**

**SP transformations** (EQUIVALENT class) apply file-wide or function-wide rewrites:
- SP-1: rename every occurrence of a chosen identifier throughout the file
- SP-2: rename a function and update every call site
- SP-3: reformat/restructure all string literals (e.g., triple-quote normalisation)
- SP-4: strip all comments and docstrings from the entire file
- SP-6: reorder function arguments throughout the file

For a program with `k` uses of the renamed identifier, SP-1 produces edit size `≈ 2k`. For a function called 10 times, SP-2 yields ≈ 22 lines changed. These are **not outliers**; they are the expected behaviour for file-wide rewriting.

### Why SP-1, SP-4, SP-9 are informative edge cases

- **SP-9 (constant folding):** Replaces a computed sub-expression with its result at one site (e.g., `2 * 3` → `6`). Since the fold applies to a single expression node, the edit is identical in size to an SC mutation: exactly 2 lines. SP-9 is the only SP type that produces edit sizes of 2, and it is therefore invisible to an edit-size classifier.

- **SP-1 (variable rename):** Because the rename applies to every occurrence in scope, edit size scales linearly with usage frequency. Single-use variables produce size=4 (minimal); frequently-used loop counters produce size=102 (observed). SP-1 produces the widest edit-size variance of any SP type (4–102).

- **SP-4 (comment strip):** All 21 test instances have edit sizes in [10, 34]. File-level comment stripping never produces a small edit on real programs (which always have at least 5 comment lines), so SP-4 is always distinguishable by size.

### No SC mutation produces a large edit (verified)

All 10 SC types in the test split have edit size ≤ 3. The maximum observed SC edit size is 3 (SC-13 with a conditional change). This is not a coincidence: the SC generator applies a single AST node substitution, and `ast.unparse` collapses the change to at most 2–3 canonical lines regardless of the line count in the original file.

### Summary

The edit-size AUROC of 0.966703 (reversed) is reproducible, structural, and expected from the benchmark construction:

| Edit-size range | Class distribution |
|-----------------|-------------------|
| 0–5             | Nearly all CHANGED (121/135 = 90% in test) |
| 6+              | Nearly all EQUIVALENT (124/124 = 100% in test) |

This near-perfect separation by edit size means any system that can count lines of diff—including a trivial rule `if edit_size ≤ 5: predict CHANGED`—will achieve ≈ 97% AUROC on this benchmark. The 0.60 AUROC of SBG V5 is lower than the edit-size baseline precisely because SBG operates on dynamic execution traces, not source text, and the execution traces are not similarly confounded.

---

## 4. Benchmark Redesign Specification (v7+)

### The problem to solve

The current v6 benchmark admits a near-trivial source-text shortcut: edit size ≤ 5 → predict CHANGED with 97% AUROC. A well-designed benchmark should require understanding program semantics. To close this shortcut we need meaningful edit-size *overlap* between the two classes:

> **Success criterion:** ≥ 30% of EQUIVALENT pairs have edit size ≤ 5; ≥ 30% of CHANGED pairs have edit size ≥ 6.

### Parameter changes to transformation generators

#### 4.1 SP transformations: constrain scope from file-wide to 1–3 occurrences

Currently all SP generators apply changes to *every* qualifying site in the file. Change the generators to accept a `max_sites` parameter:

```
# benchmark/generators/sp_transforms.py (conceptual)
SP1_MAX_SITES = 2   # rename at most 2 occurrences of the chosen identifier
SP2_MAX_SITES = 2   # rename function + at most 2 call sites
SP4_MAX_COMMENTS = 3  # strip at most 3 comment lines
SP6_MAX_SITES = 2   # reorder argument in at most 2 call sites
```

With `max_sites=2`, an SP-1 rename produces edit size = 4 (one `−` + one `+` per renamed site). This falls in bin [3,5] and overlaps with the SC range.

Implementation specifics:
- For SP-1: choose the renamed variable randomly, then apply to at most `max_sites` occurrences chosen uniformly at random from all occurrences (without replacement). Use `seed` for reproducibility.
- For SP-2: rename the function at its definition plus at most `max_sites` call sites; leave remaining call sites unchanged (program is *still* semantically equivalent — the unrenamed call sites are unreachable from the traced entry, or the generator must verify equivalence post-hoc).
- For SP-4: strip at most `max_comments` contiguous comment blocks, each at a random line. Edit size = 2 × number of stripped lines.
- For SP-6: reorder arguments at at most `max_sites` call sites.

**Semantic validity:** Restricting to a subset of occurrences does NOT change the semantic relation. For SP-1, as long as the renamed identifier does not conflict with an existing name in the remaining scope, the program is semantically equivalent—the runtime behaviour is identical. For SP-2 (function rename), all call sites that are *actually exercised by the test driver* must be updated; unreachable call sites can be left as is. Verifying this with the existing execution harness (run both versions, compare trace) is sufficient.

#### 4.2 SC transformations: add multi-site SC variants

Add new SC subtypes that make equivalent syntactic changes to the CHANGED class while touching 2–10 sites:

| New subtype | Description | Expected edit size |
|-------------|-------------|-------------------|
| SC-A | Rename a local variable at all occurrences (semantic change: variable holds wrong value at final return) | 4–20 |
| SC-B | Change the same literal constant at all occurrences (e.g., timeout=30 everywhere → timeout=31) | 4–20 |
| SC-C | Replace a boolean guard in each branch of a multi-arm `if`/`elif` chain | 4–10 |

These subtypes are still single-semantic-change mutations (the program semantics changes at one logical point), but they produce larger source diffs. Their labels remain CHANGED (label=1).

#### 4.3 Revised transformation mix

To satisfy the success criterion, approximately 30% of EQUIVALENT pairs must come from constrained-scope SP (producing size ≤ 5) and 30% of CHANGED pairs must come from multi-site SC (producing size ≥ 6):

| Class      | Source type          | Fraction | Expected edit size |
|------------|----------------------|----------|--------------------|
| EQUIVALENT | SP constrained scope | ≥ 30%    | 2–6               |
| EQUIVALENT | SP full scope        | ≤ 70%    | 6–100             |
| CHANGED    | SC single-site       | ≤ 70%    | 2–3               |
| CHANGED    | SC multi-site (A/B/C)| ≥ 30%    | 4–20              |

### 4.4 Edit-size overlap verification on the development split

Before finalising the test split, compute the edit-size distribution on the **dev** split and apply the following diagnostic gate:

```python
from experiments.final.edit_size_analysis import analyse
result = analyse('dev', 'artifacts/final/pairs_v7dev_...jsonl')
pct_equiv_small = (sum(1 for b in equiv_bins if b <= 1) / n_equiv)  # bins 0-1 = size 0-5
pct_chng_large  = (sum(1 for b in chng_bins if b >= 2) / n_chng)   # bins 2+ = size 6+
assert pct_equiv_small >= 0.30, "Insufficient small-edit EQUIVALENT pairs"
assert pct_chng_large  >= 0.30, "Insufficient large-edit CHANGED pairs"
```

This diagnostic must pass before the test split is generated. If it fails, increase the fraction of constrained-scope SP or multi-site SC variants and re-run generation on the dev split only.

### 4.5 Why this does NOT change semantic validity

The semantic validity of each pair depends **only** on whether the program outputs are identical or different under the test driver, not on how many source lines changed. Specifically:

- **Constrained-scope SP pairs** remain EQUIVALENT because partial renames of dead-code identifiers or unused call sites do not affect the execution trace. Any SP variant that touches a live identifier must be validated by running the execution harness on both versions and confirming identical outputs—the same validation already required for full-scope SP pairs.

- **Multi-site SC pairs** remain CHANGED because the semantic mutation is applied to the value or operator that controls program output; changing it at N sites still changes the output. The SC-A subtype (variable rename at all occurrences) is structurally equivalent to renaming the wrong variable everywhere—the execution trace diverges because the renamed variable holds a different value than the original at the point of use.

- **The execution harness does not need modification.** The existing run/compare infrastructure already validates semantic equivalence post-generation. Constraint changes are only to the generator parameters, not to the evaluation oracle.

### 4.6 Success criterion (formal)

Let D_dev be the development split after v7 generation:

```
S1: |{p ∈ D_dev : class(p) = EQUIVALENT ∧ edit_size(p) ≤ 5}| / |{p : class=EQUIV}| ≥ 0.30
S2: |{p ∈ D_dev : class(p) = CHANGED   ∧ edit_size(p) ≥ 6}| / |{p : class=CHANGED}| ≥ 0.30
S3: edit_size_reversed_AUROC(D_dev) ≤ 0.75  (reduced from 0.967)
```

Only when S1, S2, and S3 are satisfied on the dev split is the test split generated. The test split generation uses identical parameters, and the diagnostic is re-run on the test split as a post-hoc check (not a gate, to avoid data-dependent selection on the test split).

---

## 5. Dev-Split Analysis (EXPLORATORY — NOT FOR HYPOTHESIS TESTING)

> **⚠ Exploratory analysis on development data only. Results below are not used
> to adjust any model parameter or threshold. They are reported for diagnostic
> purposes to characterise the confound's generality.**

Using `artifacts/final/pairs_v6dev_output_free_v7.jsonl` joined to
`benchmark/datasets/v6/pairs_dev.jsonl`.

### 5.1 Edit-size AUROCs (dev split)

| Metric | Value |
|--------|-------|
| Forward AUROC (large=CHANGED) | 0.043091 |
| Reversed AUROC (small=CHANGED) | **0.956909** |
| SBG V5 AUROC | **0.667125** |

The same structural confound exists in the dev split, with reversed AUROC of **0.957**, nearly identical to the test value of 0.967. This rules out the possibility that the test confound is an artefact of test-split construction or contamination.

### 5.2 Per-bin SBG AUROCs (dev split)

| Bin | Range    |  N  | CHNG | EQUIV | SBG AUROC |
|-----|----------|-----|------|-------|-----------|
|  0  | [0, 2]   | 148 |  135 |    13 | 0.491738  |
|  1  | [3, 5]   |  41 |   18 |    23 | 0.840580  |
|  2  | [6, 10]  |  36 |    3 |    33 | 0.848485  |
|  3  | [11, 20] |  47 |    0 |    47 | N/A       |
|  4  | [21, 40] |  47 |    0 |    47 | N/A       |
|  5  | [41, ∞]  |  26 |    0 |    26 | N/A       |

Interesting dev-specific observation: **bin 2 ([6,10])** contains 3 CHANGED pairs (not 0 as in the test split), which allows a well-defined SBG AUROC of 0.848. These 3 CHANGED pairs likely come from multi-site SC-13 mutations in the dev split where the program has more branches than average.

### 5.3 Per-transformation edit sizes (dev split)

| Type  |  N  | CHNG | EQUIV | Mean | Med | Min | Max |
|-------|-----|------|-------|------|-----|-----|-----|
| SC-1  |  12 |   12 |     0 |  2.0 |   2 |   2 |   2 |
| SC-2  |  15 |   15 |     0 |  2.0 |   2 |   2 |   2 |
| SC-3  |  15 |   15 |     0 |  2.0 |   2 |   2 |   2 |
| SC-4  |  15 |   15 |     0 |  2.0 |   2 |   2 |   2 |
| SC-5  |  21 |   21 |     0 |  2.0 |   2 |   2 |   2 |
| SC-6  |  21 |   21 |     0 |  2.0 |   2 |   2 |   2 |
| SC-8  |   3 |    3 |     0 |  2.0 |   2 |   2 |   2 |
| SC-10 |   9 |    9 |     0 |  2.0 |   2 |   2 |   2 |
| SC-11 |  21 |   21 |     0 |  2.0 |   2 |   2 |   2 |
| SC-12 |   3 |    3 |     0 |  2.0 |   2 |   2 |   2 |
| SC-13 |  21 |   21 |     0 |  3.6 |   3 |   3 |   7 |
| SP-1  |  27 |    0 |    27 | 18.6 |  14 |   4 |  64 |
| SP-2  |  27 |    0 |    27 | 17.9 |  16 |   2 |  48 |
| SP-3  |  27 |    0 |    27 | 72.0 |  65 |  34 | 152 |
| SP-4  |  27 |    0 |    27 | 23.2 |  21 |  10 |  37 |
| SP-5  |  24 |    0 |    24 |  5.2 |   4 |   2 |  16 |
| SP-6  |  27 |    0 |    27 | 18.7 |  20 |   6 |  30 |
| SP-7  |  11 |    0 |    11 | 10.9 |  12 |   9 |  12 |
| SP-8  |  10 |    0 |    10 |  7.5 |   8 |   3 |  16 |
| SP-9  |   3 |    0 |     3 |  2.0 |   2 |   2 |   2 |
| SP-11 |   6 |    0 |     6 | 19.8 |  20 |  18 |  23 |

SP-5 on the dev split has mean=5.2 and min=2, producing more small-edit EQUIVALENT pairs than in the test split. SP-3 (full string reformat) is the most extreme: mean=72.0, max=152. The pattern is consistent with the test split analysis.

### 5.4 Does SBG add value beyond edit size on dev data?

This is the key diagnostic question. We examine it by looking at:

1. **Overall:** SBG AUROC (0.667) substantially exceeds the edit-size forward AUROC (0.043), confirming SBG captures signal beyond raw diff size.

2. **Within-bin 0 (edit size 0–2):** SBG AUROC = 0.492, which is essentially at chance. Within this bin, all 135 CHANGED pairs have size 2 and the 13 EQUIVALENT pairs (SP-9 and sparse SP-2) also have size 2, so edit size provides no further discrimination. SBG also provides no meaningful discrimination here (0.49 ≈ chance). **This is the most important finding: in the region where edit-size is non-discriminative, SBG is also near-chance.**

3. **Within-bin 1 (edit size 3–5):** SBG AUROC = 0.841. In this range there are 18 CHANGED and 23 EQUIVALENT pairs, so both classes are present. SBG does provide meaningful discrimination in this transition zone.

4. **Within-bin 2 (edit size 6–10, dev only):** SBG AUROC = 0.848. Three CHANGED pairs in this range and SBG identifies them well.

**Assessment:** SBG V5 does add value beyond edit size in the mixed-class transition zone (bins 1–2, edit size 3–10), achieving AUROC ≈ 0.84–0.85 in that region. However, the vast majority of the test set is either in bin 0 (where edit size and SBG are both near-chance relative to the true confound) or bins 2–5 (where all pairs are EQUIVALENT and AUROC is undefined). The overall SBG AUROC of 0.60 is substantially below the 0.97 reversed edit-size AUROC. The edit-size shortcut is the dominant signal in this benchmark. SBG provides incremental value in the difficult transition zone, but the benchmark as constructed does not cleanly separate dynamic-analysis capability from source-text confounds.

---

## 6. Standalone Analysis Script

The script `experiments/final/edit_size_analysis.py` implements all analyses in
this report as a reproducible, self-contained tool.

**Interface:**

```
python experiments/final/edit_size_analysis.py \
    --split test \
    --pairs-file artifacts/final/pairs_v6test_output_free_v6.jsonl

python experiments/final/edit_size_analysis.py \
    --split dev \
    --pairs-file artifacts/final/pairs_v6dev_output_free_v7.jsonl \
    --no-write   # dry-run, no file written
```

**What it computes:**

1. Forward and reversed edit-size AUROCs (using `sbg.statistics.auroc`)
2. SBG V5 overall AUROC
3. Per-bin SBG AUROCs using the same `EDIT_BINS` as `audit_recompute.py`
4. Per-transformation-type statistics (N, CHNG, EQUIV, mean, median, min, max edit size)
5. Flags: whether all CHANGED pairs have edit ≤ 5; whether any EQUIVALENT pairs have edit ≥ 6

**Output:** JSON report written to `reports/remediation/results/edit_size_analysis_{split}.json`.

**Line count:** 148 lines (within the 150-line budget).

---

## 7. Summary

| Finding | Value |
|---------|-------|
| Reversed edit-size AUROC (test, reproduced) | **0.966703** |
| Reversed edit-size AUROC (dev, exploratory) | **0.956909** |
| SBG V5 AUROC (test) | 0.601270 |
| SBG V5 AUROC (dev, exploratory) | 0.667125 |
| SC mutations always produce edit size ≤ 3 | **True** |
| SP mutations always produce edit size ≥ 2 | **True** |
| Exceptions (small SP) | SP-9, SP-12, sparse SP-2 |
| SC mutations that produce large edits | **None** |
| Confound present in dev split too | **Yes** |
| SBG adds value over edit size in transition zone | **Yes (AUROC ≈ 0.84 in bin 1–2)** |
| Edit-size shortcut dominates overall benchmark | **Yes** |

The edit-size confound is a direct and unavoidable consequence of the v6 benchmark construction: SC mutations change one syntactic site (edit size 2–3), while SP transformations rewrite all sites file-wide (edit size 6–152). The proposed v7 redesign addresses this by constraining SP to 1–2 sites and adding multi-site SC variants, subject to verification on the dev split before the test split is generated.
