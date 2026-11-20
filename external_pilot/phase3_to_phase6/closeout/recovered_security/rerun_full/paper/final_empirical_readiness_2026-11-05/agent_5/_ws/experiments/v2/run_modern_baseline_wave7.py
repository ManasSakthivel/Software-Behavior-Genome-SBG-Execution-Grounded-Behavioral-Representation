"""
experiments/v2/run_modern_baseline_wave7.py
=============================================
Phase 4 Wave 7 — Modern pretrained code-representation baseline.

Priority (per Phase 4 mandate): 1. CodeBERT  2. GraphCodeBERT  3. other.

Infrastructure check performed BEFORE writing this script:
  - `pip3` IS available (/usr/bin/pip3, pip 26.0.1) — contradicts an
    earlier, incorrect Wave-0-era assumption that pip was unavailable.
    That earlier assumption was based on `which pip` failing; `pip3`
    (the correct binary for this Python 3.9 environment) was never
    checked at the time. This is corrected here.
  - `transformers` was NOT installed; installed via `pip3 install --user
    transformers` (succeeded, ~12MB download, no huge infra footprint).
  - `microsoft/codebert-base` (~500MB) downloaded successfully from
    HuggingFace Hub on the first call and is now cached locally
    (subsequent loads take ~4s). Internet access IS available in this
    environment.
  - GraphCodeBERT (`microsoft/graphcodebert-base`) was NOT attempted:
    CodeBERT succeeded on the first try and produces a valid embedding
    baseline; per the "do not spend excessive time installing huge
    infrastructure" mandate, a second, more complex model (GraphCodeBERT
    requires a full DFG/AST preprocessing pipeline for its intended use,
    though it CAN also be used as a plain encoder) was not pursued once
    a working modern baseline was obtained.

Protocol
--------
1. Encode BOTH files of every pair with CodeBERT (mean-pooled last hidden
   state over up to 512 tokens — a standard, simple, no-fine-tuning
   embedding baseline; NOT fine-tuned on this benchmark in any way).
2. Similarity = cosine similarity of the two embeddings, in [-1, 1],
   rescaled to [0, 1] via (cos+1)/2 for consistency with the existing
   score convention (baselines.common expects similarity in [0,1]).
3. Evaluate on the SAME DEV/TEST split, SAME pairs, SAME metrics as
   H7-H10 (find_optimal_threshold on DEV only, evaluate on TEST with
   that frozen threshold — NO tuning on TEST).
4. No fine-tuning of any kind is performed. This is the standard
   "off-the-shelf embedding similarity" baseline, consistent with how
   B01 (TF-IDF) and B02 (AST) are also used off-the-shelf.
"""
from __future__ import annotations

import json
import pathlib
import sys
from typing import List

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from baselines.common import (  # noqa: E402
    load_pairs, load_source, pairs_to_labels, find_optimal_threshold,
    compute_metrics, save_results,
)

ARTIFACT_PATH = REPO_ROOT / "artifacts" / "v2" / "MODERN_BASELINE_RESULTS.json"
MODEL_NAME = "microsoft/codebert-base"
MAX_LENGTH = 512


def _load_model():
    import torch
    from transformers import AutoTokenizer, AutoModel
    tok = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
    model.eval()
    return tok, model, torch


_TOK, _MODEL, _TORCH = None, None, None
_EMBED_CACHE = {}


def _get_model():
    global _TOK, _MODEL, _TORCH
    if _MODEL is None:
        _TOK, _MODEL, _TORCH = _load_model()
    return _TOK, _MODEL, _TORCH


def _embed(source: str, cache_key: str):
    if cache_key in _EMBED_CACHE:
        return _EMBED_CACHE[cache_key]
    tok, model, torch = _get_model()
    with torch.no_grad():
        inputs = tok(source, return_tensors="pt", truncation=True, max_length=MAX_LENGTH)
        out = model(**inputs)
        emb = out.last_hidden_state.mean(dim=1).squeeze(0)
    _EMBED_CACHE[cache_key] = emb
    return emb


def _cosine_similarity(src_a: str, src_b: str, key_a: str, key_b: str) -> float:
    import torch
    ea = _embed(src_a, key_a)
    eb = _embed(src_b, key_b)
    cos = torch.nn.functional.cosine_similarity(ea.unsqueeze(0), eb.unsqueeze(0)).item()
    return max(0.0, min(1.0, (cos + 1.0) / 2.0))


def score_split(pairs: List[dict], split: str) -> List[float]:
    sims = []
    for i, p in enumerate(pairs):
        src_a = load_source(p["base_path"])
        src_b = load_source(p["variant_path"])
        try:
            s = _cosine_similarity(src_a, src_b, p["base_path"], p["variant_path"])
        except Exception as e:
            print(f"  [WARN] {p['pair_id']}: {e}")
            s = 0.5
        sims.append(s)
        if (i + 1) % 100 == 0:
            print(f"  [{split}] {i+1}/{len(pairs)} scored")
    return sims


def main():
    print("[Wave7-ModernBaseline] Model:", MODEL_NAME)
    print("[Wave7-ModernBaseline] Loading model (first call downloads ~500MB, cached after)...")
    _get_model()
    print("[Wave7-ModernBaseline] Model loaded successfully.")

    dev_pairs = load_pairs("dev")
    test_pairs = load_pairs("test")

    print(f"[Wave7-ModernBaseline] Scoring {len(dev_pairs)} DEV pairs...")
    dev_labels = pairs_to_labels(dev_pairs)
    dev_sims = score_split(dev_pairs, "dev")
    threshold = find_optimal_threshold(dev_sims, dev_labels)
    dev_metrics = compute_metrics(dev_sims, dev_labels, threshold)
    print(f"[Wave7-ModernBaseline] DEV threshold={threshold:.4f} AUROC={dev_metrics['auroc']:.4f}")

    print(f"[Wave7-ModernBaseline] Scoring {len(test_pairs)} TEST pairs (threshold frozen from DEV)...")
    test_labels = pairs_to_labels(test_pairs)
    test_sims = score_split(test_pairs, "test")
    test_metrics = compute_metrics(test_sims, test_labels, threshold)
    print(f"[Wave7-ModernBaseline] TEST AUROC={test_metrics['auroc']:.4f} "
          f"CI=[{test_metrics['ci_auroc_lower']:.4f},{test_metrics['ci_auroc_upper']:.4f}]")

    result = {
        "baseline_name": "MODERN_BASELINE_CODEBERT",
        "model": MODEL_NAME,
        "method": "Mean-pooled last_hidden_state embedding, cosine similarity, "
                  "NO fine-tuning, off-the-shelf (same usage pattern as B01/B02)",
        "infrastructure_note": (
            "pip3 IS available in this environment (contradicts an earlier "
            "Wave-0-era assumption that only checked `pip`, not `pip3`). "
            "transformers installed via `pip3 install --user transformers`. "
            "microsoft/codebert-base (~500MB) downloaded successfully from "
            "HuggingFace Hub — internet access is available. No huge "
            "infrastructure installation was required beyond a single pip "
            "install; total setup time was under 5 minutes."
        ),
        "graphcodebert_attempted": False,
        "graphcodebert_reason": (
            "CodeBERT succeeded on first attempt and produced a valid, "
            "reproducible modern baseline. Per the Phase 4 mandate to not "
            "spend excessive time on infrastructure once ANY modern "
            "baseline is available, a second model was not pursued."
        ),
        "protocol": {
            "dev_split": "benchmark/datasets/pairs_dev.jsonl (frozen, 615 pairs)",
            "test_split": "benchmark/datasets/pairs_test.jsonl (frozen, 744 pairs)",
            "threshold_selection": "find_optimal_threshold on DEV ONLY; frozen threshold applied to TEST (no tuning on test)",
            "fine_tuning": "NONE - off-the-shelf pretrained weights only",
            "max_token_length": MAX_LENGTH,
        },
        "dev_metrics": dev_metrics,
        "test_metrics": test_metrics,
        "threshold": threshold,
        "comparison_context": {
            "B02_AST_test_auroc_reference": 0.5528,
            "B07_dynamic_v2_test_auroc_reference": "0.5292 (Wave 1, entry-point-corrected) / 0.5310 (historical Phase 3B)",
            "note": "Directly comparable — same 744 TEST pairs, same DEV-frozen-threshold protocol.",
        },
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT_PATH, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n[Wave7-ModernBaseline] Wrote {ARTIFACT_PATH}")
    return result


if __name__ == "__main__":
    main()
