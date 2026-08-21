# Modern Baseline (CodeBERT): Phase 4 Wave 7 Analysis

**Status:** ATTEMPTED AND SUCCEEDED — CodeBERT evaluated on the full frozen test set.
**Result:** AUROC = 0.3697 (below chance; strong inversion) — a genuine, disclosed negative finding.
**Script:** `experiments/v2/run_modern_baseline_wave7.py`
**Artifact:** `artifacts/v2/MODERN_BASELINE_RESULTS.json`

---

## 1. Infrastructure correction

Earlier phases of this Phase-4 effort (Wave 0/Wave 5/Wave 6 planning)
carried an assumption, based on `which pip` returning nothing, that
`pip` was unavailable in this environment. **This was incorrect.** The
correct binary for this environment's Python 3.9 installation is
`pip3` (`/usr/bin/pip3`, pip 26.0.1), which was never checked. This
error is disclosed here rather than silently corrected, since it means
the earlier "no modern baseline possible" expectation was based on an
incomplete check.

```
$ which pip pip3
pip not found
/usr/bin/pip3
$ pip3 --version
pip 26.0.1 from /Users/manassakthivel/Library/Python/3.9/lib/python/site-packages/pip (python 3.9)
```

## 2. What was installed and run

```
pip3 install --user transformers   # succeeded, ~12MB wheel download
```

`microsoft/codebert-base` (~500MB of weights) was downloaded on first
use directly from the HuggingFace Hub — confirming internet access is
available in this environment — and is now cached locally (~4s load
time on subsequent runs). No GPU was used or required; CPU inference for
1359 total pairs (615 DEV + 744 TEST) completed in a few minutes.

**GraphCodeBERT was NOT attempted.** CodeBERT succeeded on the first
try and produced a complete, valid, reproducible baseline; per the
Phase 4 mandate ("DO NOT spend excessive time installing huge
infrastructure"), a second, more complex model was not pursued once one
modern baseline was working.

## 3. Protocol (identical to H7-H10's methodology)

- Encode both files of every pair with CodeBERT: mean-pooled
  `last_hidden_state` over up to 512 tokens, **no fine-tuning** —
  standard off-the-shelf embedding usage, the same way B01 (TF-IDF) and
  B02 (AST) are used off-the-shelf.
- Similarity = cosine similarity of the two embeddings, rescaled from
  `[-1,1]` to `[0,1]` via `(cos+1)/2` to match the existing similarity
  convention used by `baselines.common`.
- Threshold selected via `find_optimal_threshold` on the **frozen DEV
  split only** (615 pairs); that threshold is then frozen and applied
  to the **frozen TEST split** (744 pairs) — **no tuning on test**, and
  no test-set information used anywhere in threshold selection.

## 4. Results

| Split | AUROC | 95% CI | Precision | Recall | F1 |
|---|---|---|---|---|---|
| DEV (n=615) | 0.3615 | [0.335, 0.425] | 0.512 | 1.000 | 0.677 |
| **TEST (n=744)** | **0.3697** | **[0.345, 0.425]** | 0.464 | 0.754 | 0.574 |

**AUROC = 0.3697 is substantially below chance (0.5) and below every
other baseline evaluated in this project**, including B02_AST
(0.5528), B07 Dynamic SBG (0.5292 corrected / 0.5310 historical), and
even the frozen-file Static SBG V1 (0.4237).

### 4.1 Why CodeBERT performs this poorly here — diagnosed, not hidden

```
EQUIVALENT mean similarity: 0.99846  (n=378)
CHANGED    mean similarity: 0.99950  (n=366)
Similarity range observed:  [0.9813, 0.99999]
Unique similarity values:    36 (out of 744 pairs)
```

Two compounding problems, both genuine properties of raw off-the-shelf
CodeBERT embeddings on this benchmark, not implementation bugs:

1. **Severe inversion**: CHANGED pairs score, on average, *more*
   similar than EQUIVALENT pairs (0.9995 vs 0.9985) — the same
   structural-semantic inversion documented throughout H9/H10, but even
   worse in direction and magnitude than any other method tested.
2. **Extreme score compression**: all 744 pairs' cosine similarities
   fall within a narrow band of ~0.02 (0.981–0.9999). This is a known
   characteristic of raw, non-fine-tuned BERT-family sentence/mean-pooled
   embeddings — they encode mostly generic "this is Python code"
   information rather than fine-grained semantic content, so nearly
   every pair of short, related programs looks highly similar to the
   raw embedding space. A production-grade code-similarity system built
   on CodeBERT would fine-tune on a semantic-equivalence task (e.g. a
   contrastive or classification head); this experiment deliberately
   does NOT fine-tune, both because Phase 4 explicitly forbids tuning
   on/near the test set, and because fine-tuning was out of scope for
   the time budget ("do not spend excessive time").

## 5. Interpretation for Phase 4

This is reported as a genuine, disclosed negative result about
off-the-shelf pretrained code embeddings on THIS specific fine-grained
equivalence-detection task — not a general claim that CodeBERT or
transformer-based code models are ineffective. It is directly
comparable evidence (same 744 test pairs, same threshold-freezing
protocol) that:

- Dynamic SBG (B07, AUROC≈0.53) and static AST similarity (B02,
  AUROC≈0.55) both outperform a modern pretrained embedding baseline on
  this specific structural-semantic-inversion benchmark, when none of
  the methods are fine-tuned on the target task.
- This does NOT establish that SBG is "better than modern code
  representations" in general — a fine-tuned CodeBERT/GraphCodeBERT
  classifier could plausibly outperform all methods here; that
  experiment was not run (out of scope, would itself risk overfitting
  to this small benchmark without a much larger training corpus).

## 6. Cross-reference

| Document | Relation |
|---|---|
| `experiments/v2/run_modern_baseline_wave7.py` | Execution script |
| `artifacts/v2/MODERN_BASELINE_RESULTS.json` | Full DEV/TEST metrics |
| `docs/v2/H10_ROBUSTNESS_ANALYSIS.md` | Comparison baselines (B01/B02/B03/B04/B06/B07/B08) |
