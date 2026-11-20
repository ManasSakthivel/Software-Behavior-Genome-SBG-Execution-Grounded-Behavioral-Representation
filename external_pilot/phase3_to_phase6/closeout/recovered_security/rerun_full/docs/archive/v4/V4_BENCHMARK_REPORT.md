# SBG V4 Benchmark Report

**Version:** v4 (Flagship Sprint)
**Status:** EVIDENCE FROZEN

---

## 1. Benchmark Specification

| Property | Value |
|---------|-------|
| Programs (total corpus) | 64 |
| Programs (test split) | 13 |
| Programs (dev split) | 10 |
| Programs (val split) | 9 |
| Programs (train split) | 28 |
| Test pairs (frozen) | 744 |
| Dev pairs | 615 |
| Val pairs | 527 |
| Languages | Python 3.11 |
| Transformation types | 25 (SP-1 through SP-12, SC-1 through SC-13) |

## 2. Split Assignment

- Stratified by program category (12 categories)
- Seed 42
- Test set frozen from project start, never modified
- Train/dev/val used only for model development

## 3. Transformation Types

### Semantics-Preserving (EQUIVALENT label)
| Type | Description |
|------|-------------|
| SP-1 | Dead code insertion |
| SP-2 | Function rename |
| SP-3 | Variable rename |
| SP-4 | Whitespace normalization |
| SP-5 | Comment insertion |
| SP-6 | Docstring change |
| SP-7 | Type hint change |
| SP-8 | Import alias change |
| SP-9 | Constant alias rename |
| SP-10 | Equivalent expression |
| SP-11 | Loop reordering |
| SP-12 | Trivial refactor |

### Semantics-Changing (CHANGED label)
| Type | Description |
|------|-------------|
| SC-1 | Operator mutation |
| SC-2 | Comparator mutation |
| SC-3 | Constant mutation |
| SC-4 | Off-by-one mutation |
| SC-5 | Boolean logic mutation |
| SC-6 | Return value mutation |
| SC-7 | Conditional negation |
| SC-8 | Loop bound mutation |
| SC-9 | Exception mutation |
| SC-10 | Method swap |
| SC-11 | Infinite recursion injection |
| SC-12 | Data structure mutation |
| SC-13 | Assignment mutation |

## 4. Benchmark Quality Audit

### 4.1 SC-3 Bug (Resolved in v3)
**Problem:** v2 SC-3 used `ast.unparse()` which normalizes all quote styles.
76.9% of supposed SC-3 mutations were cosmetic quote changes.
**Fix:** Text-level integer constant substitution at character positions.
**Status:** RESOLVED — 179 integer mutations generated, detection rate 7.5%.

### 4.2 SP-2 Entry Function Bug (Resolved in v3)
**Problem:** v2 SP-2 alphabetical fallback selected wrong entry function after rename.
**Fix:** Call-graph root selector using bytecode analysis.
**Status:** RESOLVED — but SP-2 mean_sim=0.587 still shows partial invariance failure.

### 4.3 Label Validity (Phase 4 Oracle)
**Finding:** Oracle agreement rate 69.6% (135 evaluable pairs).
**Limitation:** 65 pairs had load failures; 35 oracle false negatives.
**Interpretation:** Labels are approximately correct but may have ~30% label noise.
**Status:** PARTIALLY_CONFIRMED (not fully validated).

### 4.4 Leakage Audit
- Train/dev/test programs are disjoint (by design, seed=42 split)
- No program appears in more than one split
- Transformation types appear in both train and test (no type-level holdout)
- Threshold selected on DEV (no test peeking)

## 5. SC-3 Corrected Benchmark (v3)

| Property | Value |
|---------|-------|
| Total generated | 179 |
| Difficulty EASY | 34 |
| Difficulty MEDIUM | 1 |
| Difficulty HARD | 126 |
| Programs covered | 18 |
| All integer mutations | YES (no quote changes) |
| SBG V3 detection rate | 7.5% |

Key finding: SBG fails to detect integer constant mutations. Mean similarity for
HARD mutations = 0.992 (virtually identical in SBG representation).

## 6. Benchmark Limitations

1. **Size:** 13 test programs is below FSE/ICSE standards (~50-200)
2. **Domain:** Educational/algorithmic programs only; no real-world code
3. **Language:** Python only (Java infrastructure not built)
4. **Ground truth:** Transformation metadata, not independent oracle
5. **Hard negatives:** Not evaluated separately
6. **Concurrency:** conc_producer_consumer excluded (non-deterministic)
