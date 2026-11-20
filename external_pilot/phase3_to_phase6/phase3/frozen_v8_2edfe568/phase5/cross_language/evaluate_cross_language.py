"""
phase5/cross_language/evaluate_cross_language.py
=================================================
Phase 5: Cross-Language Equivalence Evaluation.

Evaluates whether SBG features can recognize equivalent behavior
across Python and Java implementations.

The key challenge: AST node types differ completely between Python and Java.
We evaluate two strategies:
  1. LANGUAGE_SPECIFIC: use each language's AST directly (expected to fail)
  2. NORMALIZED_CONTROL_FLOW: normalize to language-agnostic features
     - cyclomatic_complexity (V(G))
     - loop count
     - condition count
     - function count
     - call count

For strategy 2, we extract Python features using SBG extractors and
Java features using regex/heuristic parsing (no Java AST parser available).

H4 evaluation: does normalized representation produce higher similarity
for EQUIVALENT cross-language pairs than CHANGED cross-language pairs?
"""
import ast
import json
import math
import pathlib
import random
import sys
import time
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from phase5.cross_language.generate_corpus import PYTHON_PROGRAMS, JAVA_CHANGED
from baselines.b02_ast import score_fn as python_ast_fn
from baselines.b01_token import score_fn as python_token_fn, fit_tfidf_model
from baselines.common import load_pairs
from sbg.extraction.static.extractor import ControlGenomeExtractor, canonicalize as canon_ctrl, distance as ctrl_dist

PAIRS_DIR = REPO_ROOT / "phase5" / "cross_language" / "pairs"
CORPUS_DIR = REPO_ROOT / "phase5" / "cross_language" / "corpus"
ARTIFACT_DIR = REPO_ROOT / "artifacts" / "phase5"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42


# ---------------------------------------------------------------------------
# Language-agnostic feature extraction
# ---------------------------------------------------------------------------

def extract_python_features(source: str) -> dict:
    """Extract language-agnostic control-flow features from Python."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    features = {
        "n_functions": 0,
        "n_loops": 0,
        "n_conditions": 0,
        "n_calls": 0,
        "cyclomatic_complexity": 1,
        "max_nesting_depth": 0,
        "has_recursion": False,
        "return_types_present": False,
        "has_exception_handling": False,
    }

    function_names = set()
    call_names = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            features["n_functions"] += 1
            function_names.add(node.name)
        elif isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
            features["n_loops"] += 1
            features["cyclomatic_complexity"] += 1
        elif isinstance(node, ast.If):
            features["n_conditions"] += 1
            features["cyclomatic_complexity"] += 1
        elif isinstance(node, ast.Call):
            features["n_calls"] += 1
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
        elif isinstance(node, ast.ExceptHandler):
            features["has_exception_handling"] = True
            features["cyclomatic_complexity"] += 1
        elif isinstance(node, ast.Return):
            features["return_types_present"] = True

    # Check recursion
    features["has_recursion"] = bool(function_names & call_names)
    return features


def extract_java_features_heuristic(java_source: str) -> dict:
    """
    Extract language-agnostic control-flow features from Java using heuristics.
    Since we don't have a Java AST parser, we use regex patterns.
    This is an approximation — precise for the simple programs in our corpus.
    """
    features = {
        "n_functions": 0,
        "n_loops": 0,
        "n_conditions": 0,
        "n_calls": 0,
        "cyclomatic_complexity": 1,
        "max_nesting_depth": 0,
        "has_recursion": False,
        "return_types_present": False,
        "has_exception_handling": False,
    }

    # Count method definitions (public/private/protected/static ... type name(...))
    method_pattern = re.compile(
        r'(public|private|protected|static|final)\s+[\w\[\]<>]+\s+(\w+)\s*\(', re.MULTILINE
    )
    method_names = set()
    for m in method_pattern.finditer(java_source):
        features["n_functions"] += 1
        method_names.add(m.group(2))

    # Count loops
    features["n_loops"] = len(re.findall(r'\b(for|while)\s*\(', java_source))
    features["cyclomatic_complexity"] += features["n_loops"]

    # Count conditionals
    features["n_conditions"] = len(re.findall(r'\bif\s*\(', java_source))
    features["cyclomatic_complexity"] += features["n_conditions"]

    # Count method calls (patterns like name(...))
    call_pattern = re.compile(r'(\w+)\s*\(')
    call_names = set(m.group(1) for m in call_pattern.finditer(java_source)
                     if m.group(1) not in {'if', 'while', 'for', 'switch', 'catch'})
    features["n_calls"] = len(call_names)

    # Exception handling
    if 'catch' in java_source or 'throw' in java_source:
        features["has_exception_handling"] = True
        features["cyclomatic_complexity"] += 1

    # Return statement
    features["return_types_present"] = bool(re.search(r'\breturn\b', java_source))

    # Recursion: method calls itself
    features["has_recursion"] = bool(method_names & call_names)

    return features


def feature_similarity(f_a: dict, f_b: dict) -> float:
    """
    Compute similarity between two feature dicts.
    Uses normalized L1 distance on numeric features,
    Jaccard for boolean features.
    """
    numeric_keys = [
        "n_functions", "n_loops", "n_conditions", "n_calls", "cyclomatic_complexity"
    ]
    bool_keys = ["has_recursion", "return_types_present", "has_exception_handling"]

    if not f_a or not f_b:
        return 0.5  # neutral

    # Numeric: normalized absolute difference
    numeric_diffs = []
    for k in numeric_keys:
        va = f_a.get(k, 0)
        vb = f_b.get(k, 0)
        max_val = max(va, vb, 1)
        numeric_diffs.append(abs(va - vb) / max_val)

    numeric_sim = 1.0 - (sum(numeric_diffs) / len(numeric_diffs)) if numeric_diffs else 0.5

    # Boolean: Jaccard agreement
    bool_matches = sum(1 for k in bool_keys if f_a.get(k) == f_b.get(k))
    bool_sim = bool_matches / len(bool_keys) if bool_keys else 0.5

    return 0.6 * numeric_sim + 0.4 * bool_sim


def run():
    print("=" * 60)
    print("Phase 5: Cross-Language Equivalence Evaluation")
    print("=" * 60)

    # Initialize TF-IDF
    train_pairs = load_pairs("train")
    fit_tfidf_model(train_pairs)

    # Load pair manifest
    manifest_path = PAIRS_DIR / "cross_language_pairs.json"
    with open(manifest_path) as f:
        pairs = json.load(f)

    print(f"  Loaded {len(pairs)} cross-language pairs")
    n_equiv = sum(1 for p in pairs if p["semantic_relation"] == "EQUIVALENT")
    n_changed = sum(1 for p in pairs if p["semantic_relation"] == "CHANGED")
    print(f"  {n_equiv} EQUIVALENT, {n_changed} CHANGED")

    # For each pair, score using multiple methods
    results = []
    equiv_scores = {"normalized_control_flow": [], "python_ast_vs_python_ast": []}
    changed_scores = {"normalized_control_flow": [], "python_ast_vs_python_ast": []}

    for pair in pairs:
        pair_id = pair["pair_id"]
        relation = pair["semantic_relation"]

        # Load Python source
        py_path = REPO_ROOT / pair["python_path"]
        java_path = REPO_ROOT / pair["java_path"]

        try:
            py_src = py_path.read_text()
        except Exception as e:
            print(f"  Warning: could not read {py_path}: {e}")
            continue

        try:
            java_src = java_path.read_text()
        except Exception as e:
            print(f"  Warning: could not read {java_path}: {e}")
            continue

        # Method 1: Language-agnostic normalized control flow features
        py_features = extract_python_features(py_src)
        java_features = extract_java_features_heuristic(java_src)
        cl_sim = feature_similarity(py_features, java_features)

        # Method 2: For comparison — Python AST vs Python AST (same-language baseline)
        # Use Python source vs Python source to get same-language score for reference
        py_ctrl = None
        try:
            py_ctrl_genome = canon_ctrl(ControlGenomeExtractor().extract(py_src))
            py_ctrl = py_ctrl_genome
        except Exception:
            pass

        pair_result = {
            "pair_id": pair_id,
            "semantic_relation": relation,
            "category": pair.get("category"),
            "python_features": py_features,
            "java_features": java_features,
            "normalized_cf_similarity": round(cl_sim, 4),
            "python_cyclomatic_complexity": py_features.get("cyclomatic_complexity"),
            "java_cyclomatic_complexity": java_features.get("cyclomatic_complexity"),
        }

        results.append(pair_result)

        if relation == "EQUIVALENT":
            equiv_scores["normalized_control_flow"].append(cl_sim)
        else:
            changed_scores["normalized_control_flow"].append(cl_sim)

        print(f"  {pair_id} ({relation}): cf_sim={cl_sim:.4f} "
              f"[py_cc={py_features.get('cyclomatic_complexity')}, "
              f"java_cc={java_features.get('cyclomatic_complexity')}]")

    # Compute AUROC for normalized control flow
    from baselines.common import compute_auroc
    all_sims = [r["normalized_cf_similarity"] for r in results]
    all_labels = [0 if r["semantic_relation"] == "EQUIVALENT" else 1 for r in results]

    if len(set(all_labels)) > 1:
        auroc = compute_auroc(all_sims, all_labels)
    else:
        auroc = None

    # Mean similarities
    eq_mean = sum(equiv_scores["normalized_control_flow"]) / max(1, len(equiv_scores["normalized_control_flow"]))
    ch_mean = sum(changed_scores["normalized_control_flow"]) / max(1, len(changed_scores["normalized_control_flow"]))

    print(f"\n  EQUIV mean_sim = {eq_mean:.4f}")
    print(f"  CHANGED mean_sim = {ch_mean:.4f}")
    auroc_str = f"{auroc:.4f}" if auroc is not None else "N/A"
    print(f"  AUROC = {auroc_str}")

    # H4 verdict
    # For H4, we need AUROC > 0.5 and EQUIV_mean > CHANGED_mean
    h4_supported = (
        auroc is not None and
        auroc > 0.5 and
        eq_mean > ch_mean
    )

    summary = {
        "experiment": "E9_cross_language_phase5",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hypothesis_addressed": ["H4"],
        "n_pairs": len(results),
        "n_equivalent": n_equiv,
        "n_changed": n_changed,
        "method": "normalized_control_flow_features",
        "feature_keys": ["n_functions", "n_loops", "n_conditions", "n_calls",
                         "cyclomatic_complexity", "has_recursion", "return_types_present",
                         "has_exception_handling"],
        "equiv_mean_sim": round(eq_mean, 4),
        "changed_mean_sim": round(ch_mean, 4),
        "inversion": ch_mean > eq_mean,
        "auroc": round(auroc, 4) if auroc is not None else None,
        "h4_verdict": {
            "status": "PARTIALLY_SUPPORTED" if h4_supported else
                      ("NOT_SUPPORTED" if auroc is not None else "INSUFFICIENT_EVIDENCE"),
            "interpretation": (
                    f"Normalized control-flow features: EQUIV_mean={eq_mean:.4f}, "
                    f"CHANGED_mean={ch_mean:.4f}, AUROC={auroc_str}. "
                    f"H4 is {'PARTIALLY_SUPPORTED' if h4_supported else 'NOT fully supported'}. "
                    f"Small corpus (n={len(results)}) limits statistical power. "
                    "Full H4 evaluation requires larger corpus (50+ pairs per category)."
                ),
        },
        "pair_results": results,
        "limitation": (
            "Java features extracted via regex heuristics, not a Java AST parser. "
            f"Corpus size: {len(results)} pairs — too small for robust AUROC estimates. "
            "Java semantic equivalence validated by manual inspection only. "
            "This is a preliminary Phase 5 result; full H4 requires larger corpus."
        ),
        "seed": SEED,
    }

    out_path = ARTIFACT_DIR / "cross_language_results.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n  H4 verdict: {summary['h4_verdict']['status']}")
    print(f"  {summary['h4_verdict']['interpretation']}")
    print(f"\n  Results saved to: {out_path}")
    return summary


if __name__ == "__main__":
    run()
