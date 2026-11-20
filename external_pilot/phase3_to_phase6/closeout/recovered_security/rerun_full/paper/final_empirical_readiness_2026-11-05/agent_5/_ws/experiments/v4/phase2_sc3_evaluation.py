"""
experiments/v4/phase2_sc3_evaluation.py
========================================
Phase 2 — Evaluate SBG V3 on Corrected SC-3 Pairs (38 verified pairs)

SCIENTIFIC QUESTION:
  Does SBG V3 correctly distinguish integer-constant mutations (true semantic
  change) from the base program?

CONTEXT:
  - v2 SC-3 benchmark: 76.9% were cosmetic quote changes (confirmed bug)
  - v3 SC-3: 38 pairs where integer constants were mutated by text substitution
  - The mutation IS behaviorally significant (verified during benchmark generation)

METHODOLOGY:
  - Load 38 verified SC-3v3 pairs from benchmark/v3/sc3_corrected/
  - Score each pair with SBG V3 distance_v3()
  - Compare with AST similarity, token similarity
  - Compute AUROC on these 38 pairs alone
  - Compare per-difficulty level (EASY/MEDIUM/HARD)
  - This is EXPLORATORY — not a held-out evaluation

OUTPUT: artifacts/v4/SC3_CORRECTED_EVALUATION.json
"""
from __future__ import annotations

import importlib.util
import io
import json
import pathlib
import sys
import types
from typing import Any, Callable, Dict, List, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sbg.v2.execution.runner import SandboxRunner
from sbg.v3.genome import DynamicGenomeExtractorV3, distance_v3
from sbg.v3.metrics import compute_auroc_v3, bootstrap_auroc_ci, permutation_test_auroc

PAIRS_FILE = REPO_ROOT / "benchmark" / "v3" / "sc3_corrected" / "sc3_corrected_pairs.jsonl"
ARTIFACT_OUT = REPO_ROOT / "artifacts" / "v4" / "SC3_CORRECTED_EVALUATION.json"

V3_INPUTS: List[Any] = [
    [], [1], [3, 1, 4, 1, 5, 9, 2, 6], [10, 9, 8, 7, 6, 5],
    [0, 0, 0, 0], [2, 1], [-3, 0, 3], list(range(8)),
    list(range(3)), list(range(16)),
]

_runner = SandboxRunner()
_extractor = DynamicGenomeExtractorV3()
_genome_cache: Dict[str, Any] = {}


def _load_fn(path: str) -> Optional[Callable]:
    p = pathlib.Path(path)
    if not p.exists():
        return None
    spec = importlib.util.spec_from_file_location("_sc3prog", str(p))
    if not spec or not spec.loader:
        return None
    mod = types.ModuleType("_sc3prog")
    old = sys.stdout; sys.stdout = io.StringIO()
    try:
        spec.loader.exec_module(mod)  # type: ignore
    except Exception:
        sys.stdout = old
        return None
    finally:
        sys.stdout = old
    import inspect
    for nm in ("sort", "search", "run", "main", "solve", "process", "compute",
               "encode", "decode", "parse", "validate", "execute"):
        fn = getattr(mod, nm, None)
        if callable(fn) and isinstance(fn, types.FunctionType):
            return fn
    for nm, obj in inspect.getmembers(mod, inspect.isfunction):
        if not nm.startswith("_") and getattr(obj, "__module__", None) == "_sc3prog":
            return obj
    return None


def _extract_genome(path: str) -> Optional[Any]:
    if path in _genome_cache:
        return _genome_cache[path]
    fn = _load_fn(path)
    if fn is None:
        _genome_cache[path] = None
        return None
    import inspect
    try:
        n_p = len(inspect.signature(fn).parameters)
    except Exception:
        n_p = 1
    fn_to_trace = fn if n_p > 0 else (lambda inp: fn())
    inputs_to_use = V3_INPUTS if n_p > 0 else [None]
    pid = pathlib.Path(path).stem
    try:
        sr = _runner.run(pid, fn_to_trace, inputs_to_use, n_runs=3, seed=42, max_events=3_000)
        genome = _extractor.extract_from_traces(pid, sr.traces)
    except Exception:
        genome = None
    _genome_cache[path] = genome
    return genome


def _ast_similarity(p1: str, p2: str) -> float:
    """Simple AST node-type histogram similarity."""
    import ast
    def _node_hist(src: str) -> Dict[str, int]:
        try:
            tree = ast.parse(src)
            hist: Dict[str, int] = {}
            for node in ast.walk(tree):
                k = type(node).__name__
                hist[k] = hist.get(k, 0) + 1
            return hist
        except Exception:
            return {}
    try:
        h1 = _node_hist(pathlib.Path(p1).read_text())
        h2 = _node_hist(pathlib.Path(p2).read_text())
        all_keys = set(h1) | set(h2)
        if not all_keys:
            return 1.0
        total = sum(max(h1.get(k, 0), h2.get(k, 0)) for k in all_keys)
        match = sum(min(h1.get(k, 0), h2.get(k, 0)) for k in all_keys)
        return match / total if total > 0 else 1.0
    except Exception:
        return 1.0


def _token_similarity(p1: str, p2: str) -> float:
    """Token overlap Jaccard similarity."""
    import tokenize, io as _io
    def _tokens(src: str):
        toks = set()
        try:
            for tok in tokenize.generate_tokens(_io.StringIO(src).readline):
                if tok.type in (1, 2):  # NAME or NUMBER
                    toks.add(tok.string)
        except Exception:
            pass
        return toks
    try:
        t1 = _tokens(pathlib.Path(p1).read_text())
        t2 = _tokens(pathlib.Path(p2).read_text())
        union = t1 | t2
        if not union:
            return 1.0
        return len(t1 & t2) / len(union)
    except Exception:
        return 1.0


def main() -> None:
    print("\n" + "="*60)
    print("PHASE 2 — SC-3 CORRECTED PAIRS EVALUATION")
    print("="*60)

    if not PAIRS_FILE.exists():
        print(f"ERROR: SC-3 pairs file not found: {PAIRS_FILE}")
        sys.exit(1)

    pairs = []
    with open(PAIRS_FILE) as fh:
        for line in fh:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))
    print(f"Loaded {len(pairs)} SC-3v3 verified pairs.\n")

    per_pair = []
    for i, p in enumerate(pairs):
        base_path = str(REPO_ROOT / p["base_path"])
        var_path = str(REPO_ROOT / p["variant_path"])
        difficulty = p.get("difficulty", "UNKNOWN")
        expected_label = 1  # All SC-3 pairs are CHANGED

        g1 = _extract_genome(base_path)
        g2 = _extract_genome(var_path)
        if g1 is not None and g2 is not None:
            sbg_sim = 1.0 - distance_v3(g1, g2)
            sbg_ok = True
        else:
            sbg_sim = 0.5
            sbg_ok = False

        ast_sim = _ast_similarity(base_path, var_path)
        tok_sim = _token_similarity(base_path, var_path)

        per_pair.append({
            "pair_id": p.get("pair_id", f"sc3v3_{i}"),
            "base_id": p.get("base_id"),
            "difficulty": difficulty,
            "sbg_v3_similarity": round(sbg_sim, 6),
            "sbg_v3_predicts_changed": sbg_sim < 0.5,
            "sbg_v3_extracted": sbg_ok,
            "ast_similarity": round(ast_sim, 6),
            "token_similarity": round(tok_sim, 6),
            "label": expected_label,
        })
        if (i+1) % 10 == 0:
            print(f"  {i+1}/{len(pairs)} pairs scored", flush=True)

    # All pairs are CHANGED (label=1), so AUROC = P(sim_changed < 0.5)
    # which requires at least some EQUIV pairs for meaningful AUROC.
    # Instead we report: fraction correctly predicted as CHANGED (detection rate)
    # and compare mean similarities to a notional threshold of 0.5.

    sbg_sims = [r["sbg_v3_similarity"] for r in per_pair if r["sbg_v3_extracted"]]
    ast_sims = [r["ast_similarity"] for r in per_pair]
    tok_sims = [r["token_similarity"] for r in per_pair]

    sbg_detection_rate = sum(1 for s in sbg_sims if s < 0.5) / len(sbg_sims) if sbg_sims else 0.0
    ast_detection_rate = sum(1 for s in ast_sims if s < 0.5) / len(ast_sims) if ast_sims else 0.0
    tok_detection_rate = sum(1 for s in tok_sims if s < 0.5) / len(tok_sims) if tok_sims else 0.0

    # Per-difficulty breakdown
    by_difficulty: Dict[str, Dict] = {}
    for diff in ["EASY", "MEDIUM", "HARD"]:
        subset = [r for r in per_pair if r["difficulty"] == diff]
        if not subset:
            continue
        s_sims = [r["sbg_v3_similarity"] for r in subset if r["sbg_v3_extracted"]]
        by_difficulty[diff] = {
            "n": len(subset),
            "sbg_mean_sim": round(sum(s_sims)/len(s_sims), 6) if s_sims else None,
            "sbg_detection_rate": sum(1 for s in s_sims if s < 0.5) / len(s_sims) if s_sims else 0.0,
        }

    summary = {
        "experiment": "PHASE2_SC3_CORRECTED_EVALUATION",
        "version": "v4",
        "n_pairs": len(pairs),
        "n_pairs_sbg_extracted": len(sbg_sims),
        "note": "All SC-3v3 pairs are CHANGED — detection rate at threshold=0.5 reported",
        "sbg_v3": {
            "mean_similarity": round(sum(sbg_sims)/len(sbg_sims), 6) if sbg_sims else None,
            "detection_rate_at_0_5": round(sbg_detection_rate, 6),
            "n_extracted": len(sbg_sims),
        },
        "ast_baseline": {
            "mean_similarity": round(sum(ast_sims)/len(ast_sims), 6) if ast_sims else None,
            "detection_rate_at_0_5": round(ast_detection_rate, 6),
        },
        "token_baseline": {
            "mean_similarity": round(sum(tok_sims)/len(tok_sims), 6) if tok_sims else None,
            "detection_rate_at_0_5": round(tok_detection_rate, 6),
        },
        "by_difficulty": by_difficulty,
        "per_pair_results": per_pair,
        "interpretation": (
            "SC-3v3 detection rate measures whether SBG V3 correctly assigns"
            " lower similarity to integer-mutated variants. Higher is better."
            " AST similarity should catch integer literal changes; SBG should"
            " also catch if the mutation affects execution paths."
        )
    }

    ARTIFACT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT_OUT, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[PHASE2] Saved → {ARTIFACT_OUT}")
    print(f"SBG V3 detection rate: {sbg_detection_rate:.3f} ({len(sbg_sims)} pairs)")
    print(f"AST detection rate:    {ast_detection_rate:.3f}")
    print(f"Token detection rate:  {tok_detection_rate:.3f}")
    print(f"By difficulty: {by_difficulty}")


if __name__ == "__main__":
    main()
