"""
baselines/b01_token.py
========================
B1: Token / TF-IDF similarity baseline.

Normalization steps (documented):
1. Strip comments and docstrings using Python tokenize module
2. Extract NAME, NUMBER, OP, STRING token types only
3. Lowercase all tokens
4. Remove Python keywords (import, def, class, return, if, for, while, etc.)
5. TF-IDF with corpus IDF built from training split base programs

Scoring convention: HIGH score → EQUIVALENT, LOW → CHANGED
"""
import collections
import io
import json
import keyword
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

ARTIFACT_DIR = str(ARTIFACTS_DIR / "B01")

_KEYWORDS = set(keyword.kwlist) | {"None", "True", "False"}
_KEEP_TYPES = {tokenize.NAME, tokenize.NUMBER, tokenize.OP, tokenize.STRING}


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def _tokenize_source(source: str) -> list:
    """Extract normalized token list from Python source."""
    tokens = []
    try:
        gen = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok_type, tok_str, _, _, _ in gen:
            if tok_type in _KEEP_TYPES:
                normalized = tok_str.lower()
                if normalized not in _KEYWORDS:
                    tokens.append(normalized)
    except tokenize.TokenError:
        pass
    return tokens


def _token_counts(source: str) -> dict:
    toks = _tokenize_source(source)
    counts = collections.Counter(toks)
    return dict(counts)


# ---------------------------------------------------------------------------
# Similarity A: Jaccard on token sets
# ---------------------------------------------------------------------------

def token_set_similarity(src_a: str, src_b: str) -> float:
    toks_a = set(_tokenize_source(src_a))
    toks_b = set(_tokenize_source(src_b))
    if not toks_a and not toks_b:
        return 1.0
    union = toks_a | toks_b
    inter = toks_a & toks_b
    return len(inter) / len(union)


# ---------------------------------------------------------------------------
# Similarity B: TF-IDF cosine similarity (primary)
# ---------------------------------------------------------------------------

class TFIDFModel:
    def __init__(self):
        self.idf: dict = {}
        self.vocab: set = set()

    def fit(self, sources: list):
        """Build IDF from a corpus of sources."""
        N = len(sources)
        df = collections.Counter()
        for src in sources:
            vocab = set(_tokenize_source(src))
            for tok in vocab:
                df[tok] += 1
        self.idf = {tok: math.log((N + 1) / (count + 1)) + 1.0
                    for tok, count in df.items()}
        self.vocab = set(self.idf)

    def transform(self, source: str) -> dict:
        """Return TF-IDF weighted vector as dict."""
        counts = _token_counts(source)
        total = sum(counts.values()) or 1
        vec = {}
        for tok, cnt in counts.items():
            tf = cnt / total
            idf = self.idf.get(tok, math.log(2.0) + 1.0)  # default IDF for unseen tokens
            vec[tok] = tf * idf
        return vec


def _cosine(v1: dict, v2: dict) -> float:
    if not v1 or not v2:
        return 0.0
    keys = set(v1) | set(v2)
    dot = sum(v1.get(k, 0.0) * v2.get(k, 0.0) for k in keys)
    norm1 = math.sqrt(sum(x * x for x in v1.values()))
    norm2 = math.sqrt(sum(x * x for x in v2.values()))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


_tfidf_model = None


def tfidf_cosine_similarity(src_a: str, src_b: str) -> float:
    global _tfidf_model
    if _tfidf_model is None:
        raise RuntimeError("Call fit_tfidf_model first")
    v_a = _tfidf_model.transform(src_a)
    v_b = _tfidf_model.transform(src_b)
    return _cosine(v_a, v_b)


def fit_tfidf_model(train_pairs: list):
    global _tfidf_model
    sources = []
    for p in train_pairs:
        try:
            sources.append(load_source(p["base_path"]))
        except Exception:
            pass
    # Also add unique variant sources
    seen = set()
    for p in train_pairs:
        try:
            src = load_source(p["variant_path"])
            h = hash(src[:200])
            if h not in seen:
                sources.append(src)
                seen.add(h)
        except Exception:
            pass
    _tfidf_model = TFIDFModel()
    _tfidf_model.fit(sources)
    print(f"[B01] TF-IDF model fitted on {len(sources)} sources, vocab={len(_tfidf_model.vocab)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def score_fn(src_a: str, src_b: str) -> float:
    return tfidf_cosine_similarity(src_a, src_b)


if __name__ == "__main__":
    dev_pairs = load_pairs("dev")
    test_pairs = load_pairs("test")
    train_pairs = load_pairs("train")

    # Fit IDF on training data only
    fit_tfidf_model(train_pairs)

    dev_m, test_m, threshold = run_baseline(
        "B01", score_fn, dev_pairs, test_pairs,
        artifact_dir=ARTIFACT_DIR
    )

    # Also save Jaccard results for comparison
    print("\n[B01] Also computing Jaccard (secondary)...")
    dev_labels = pairs_to_labels(dev_pairs)
    dev_jac = []
    for p in dev_pairs:
        try:
            s = token_set_similarity(load_source(p["base_path"]), load_source(p["variant_path"]))
        except Exception:
            s = 0.5
        dev_jac.append(s)

    jac_thresh = find_optimal_threshold(dev_jac, dev_labels)
    jac_dev_m = compute_metrics(dev_jac, dev_labels, jac_thresh)

    test_labels = pairs_to_labels(test_pairs)
    test_jac = []
    for p in test_pairs:
        try:
            s = token_set_similarity(load_source(p["base_path"]), load_source(p["variant_path"]))
        except Exception:
            s = 0.5
        test_jac.append(s)
    jac_test_m = compute_metrics(test_jac, test_labels, jac_thresh)

    save_results("B01", "dev_jaccard", {"baseline": "B01_JACCARD", "split": "dev",
                  "threshold": jac_thresh, "metrics": jac_dev_m}, ARTIFACT_DIR)
    save_results("B01", "test_jaccard", {"baseline": "B01_JACCARD", "split": "test",
                  "threshold": jac_thresh, "metrics": jac_test_m}, ARTIFACT_DIR)

    print(f"\n=== B1 Token/TF-IDF Baseline ===")
    print(f"  [TF-IDF] DEV  F1={dev_m['f1']:.4f} AUROC={dev_m['auroc']:.4f}")
    print(f"  [TF-IDF] TEST F1={test_m['f1']:.4f} AUROC={test_m['auroc']:.4f} "
          f"[{test_m['ci_f1_lower']:.3f}–{test_m['ci_f1_upper']:.3f}]")
    print(f"  [Jaccard] TEST F1={jac_test_m['f1']:.4f} AUROC={jac_test_m['auroc']:.4f}")
