"""
experiments/phase4/utils.py
============================
Shared utilities for Phase 4 experiments.

Provides:
- token_fn_initialized(): returns token score_fn with TF-IDF fitted on train data
- Lazy initialization to avoid reloading on every import
"""
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

_token_initialized = False


def ensure_token_initialized():
    """Initialize the TF-IDF model for b01_token if not already done."""
    global _token_initialized
    if _token_initialized:
        return
    from baselines.common import load_pairs
    from baselines.b01_token import fit_tfidf_model
    train_pairs = load_pairs("train")
    fit_tfidf_model(train_pairs)
    _token_initialized = True
