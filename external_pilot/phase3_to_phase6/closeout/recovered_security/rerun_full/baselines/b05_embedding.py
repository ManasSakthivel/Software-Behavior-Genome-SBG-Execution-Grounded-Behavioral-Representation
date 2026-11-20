"""
baselines/b05_embedding.py
============================
B5: Code Embedding Baseline (subword n-gram TF-IDF fallback).

IMPORTANT DISCLAIMER:
  Primary intended baseline: CodeBERT (microsoft/codebert-base) or similar.
  FALLBACK USED: subword character n-gram + word n-gram TF-IDF cosine similarity.
  Reason: CodeBERT requires torch + transformers (unavailable in stdlib-only env).
  The fallback captures subword/lexical structure but NOT semantic representations.
  Results should be treated as a LOWER BOUND on what a proper code embedding
  baseline would achieve. The fallback is NOT equivalent to CodeBERT.

FALLBACK_EMBEDDING = True is recorded in all result artifacts.

Implementation:
  - Character 3-grams and 4-grams extracted from normalized token sequence
  - Word unigrams and bigrams
  - IDF weights from TRAINING corpus (base programs only)
  - Cosine similarity of TF-IDF weighted vectors

Scoring: HIGH → EQUIVALENT, LOW → CHANGED
"""
import collections
import io
import math
import pathlib
import sys
import tokenize

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from baselines.common import (
    load_pairs, load_source, run_baseline, pairs_to_labels,
    find_optimal_threshold, compute_metrics, save_results,
    REPO_ROOT, ARTIFACTS_DIR
)

ARTIFACT_DIR = str(ARTIFACTS_DIR / "B05")
FALLBACK_EMBEDDING = True


def _get_tokens(source: str) -> list:
    """Extract lowercase alphanumeric tokens."""
    tokens = []
    try:
        gen = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok_type, tok_str, _, _, _ in gen:
            if tok_type in (tokenize.NAME, tokenize.NUMBER, tokenize.STRING):
                tokens.append(tok_str.lower())
    except tokenize.TokenError:
        pass
    return tokens


def _extract_features(source: str) -> dict:
    """Extract word unigrams, bigrams, and char 3/4-grams."""
    tokens = _get_tokens(source)
    feats = collections.Counter()
    # Word unigrams
    for t in tokens:
        feats[f"W1:{t}"] += 1
    # Word bigrams
    for i in range(len(tokens) - 1):
        feats[f"W2:{tokens[i]}_{tokens[i+1]}"] += 1
    # Character 3/4-grams from joined token string
    joined = " ".join(tokens)
    for n in (3, 4):
        for i in range(len(joined) - n + 1):
            gram = joined[i:i+n]
            feats[f"C{n}:{gram}"] += 1
    return dict(feats)


class EmbeddingTFIDF:
    def __init__(self):
        self.idf: dict = {}

    def fit(self, sources: list):
        N = len(sources)
        df = collections.Counter()
        for src in sources:
            vocab = set(_extract_features(src).keys())
            for feat in vocab:
                df[feat] += 1
        self.idf = {f: math.log((N + 1) / (c + 1)) + 1.0 for f, c in df.items()}

    def transform(self, source: str) -> dict:
        counts = _extract_features(source)
        total = sum(counts.values()) or 1
        vec = {}
        for feat, cnt in counts.items():
            tf = cnt / total
            idf_val = self.idf.get(feat, math.log(2.0) + 1.0)
            vec[feat] = tf * idf_val
        return vec


def _cosine(v1: dict, v2: dict) -> float:
    if not v1 or not v2:
        return 0.0
    dot = sum(v1.get(k, 0.0) * v2.get(k, 0.0) for k in v2)
    n1 = math.sqrt(sum(x*x for x in v1.values()))
    n2 = math.sqrt(sum(x*x for x in v2.values()))
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)


_model = None


def fit_model(train_pairs: list):
    global _model
    sources = []
    seen = set()
    for p in train_pairs:
        for key in ("base_path", "variant_path"):
            try:
                src = load_source(p[key])
                h = hash(src[:300])
                if h not in seen:
                    sources.append(src)
                    seen.add(h)
            except Exception:
                pass
    _model = EmbeddingTFIDF()
    _model.fit(sources)
    print(f"[B05] Embedding model fitted: {len(sources)} sources, vocab={len(_model.idf)}")


def score_fn(src_a: str, src_b: str) -> float:
    global _model
    if _model is None:
        raise RuntimeError("Call fit_model first")
    return _cosine(_model.transform(src_a), _model.transform(src_b))


if __name__ == "__main__":
    dev_pairs = load_pairs("dev")
    test_pairs = load_pairs("test")
    train_pairs = load_pairs("train")

    fit_model(train_pairs)

    dev_m, test_m, threshold = run_baseline(
        "B05", score_fn, dev_pairs, test_pairs,
        artifact_dir=ARTIFACT_DIR
    )

    # Annotate results with fallback flag
    import json
    from pathlib import Path
    for split in ("dev", "test"):
        p = Path(ARTIFACT_DIR) / f"results_{split}.json"
        d = json.loads(p.read_text())
        d["fallback_embedding"] = FALLBACK_EMBEDDING
        d["intended_model"] = "CodeBERT (microsoft/codebert-base)"
        d["fallback_reason"] = "torch/transformers not available in stdlib-only environment"
        p.write_text(json.dumps(d, indent=2))

    print(f"\n=== B5 Embedding Baseline (FALLBACK: subword n-gram TF-IDF) ===")
    print(f"  FALLBACK_EMBEDDING = {FALLBACK_EMBEDDING}")
    print(f"  DEV  F1={dev_m['f1']:.4f} AUROC={dev_m['auroc']:.4f}")
    print(f"  TEST F1={test_m['f1']:.4f} AUROC={test_m['auroc']:.4f} "
          f"[{test_m['ci_f1_lower']:.3f}–{test_m['ci_f1_upper']:.3f}]")
