"""
baselines/b02_ast.py
======================
B2: AST structural similarity baseline.

Normalization steps (documented):
1. Parse with ast.parse
2. Strip docstrings (leading Expr(Constant(str)) from bodies)
3. Normalize variable names: scope-aware positional labels VAR_0, VAR_1...
4. Normalize function names: FN_0, FN_1 in definition order
5. Normalize string literals → <STR>
6. Keep numeric literals (semantically significant)

Two similarity functions:
A. Node-type histogram similarity (Jaccard + L1)
B. Linearized AST sequence edit-distance similarity (primary)

Scoring: HIGH → EQUIVALENT, LOW → CHANGED
"""
import ast
import collections
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from baselines.common import (
    load_pairs, load_source, run_baseline, pairs_to_labels,
    find_optimal_threshold, compute_metrics, save_results,
    REPO_ROOT, ARTIFACTS_DIR
)

ARTIFACT_DIR = str(ARTIFACTS_DIR / "B02")
MAX_SEQ_LEN = 500  # cap for edit distance tractability


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

class _Normalizer(ast.NodeTransformer):
    """
    Scope-aware normalizer:
    - Variable names in each scope → VAR_N in encounter order
    - Function/class names → FN_N in definition order
    - String literals → <STR>
    """
    def __init__(self):
        self.fn_counter = 0
        self.fn_map: dict = {}
        self.scope_stack: list = [{}]  # stack of {original_name: normalized_name}
        self.var_counter = 0

    def _scope(self):
        return self.scope_stack[-1]

    def _normalize_name(self, name: str) -> str:
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        label = f"VAR_{self.var_counter}"
        self.var_counter += 1
        self.scope_stack[-1][name] = label
        return label

    def visit_FunctionDef(self, node):
        if node.name not in self.fn_map:
            self.fn_map[node.name] = f"FN_{self.fn_counter}"
            self.fn_counter += 1
        node.name = self.fn_map[node.name]
        self.scope_stack.append({})
        self.generic_visit(node)
        self.scope_stack.pop()
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        if node.name not in self.fn_map:
            self.fn_map[node.name] = f"CLS_{self.fn_counter}"
            self.fn_counter += 1
        node.name = self.fn_map[node.name]
        self.scope_stack.append({})
        self.generic_visit(node)
        self.scope_stack.pop()
        return node

    def visit_Name(self, node):
        node.id = self._normalize_name(node.id)
        return node

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            node.value = "<STR>"
        return node


def _strip_docstrings(tree):
    """Remove docstrings from module, function, class bodies."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if (node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                node.body = node.body[1:]
    return tree


def normalize_ast(source: str):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    tree = _strip_docstrings(tree)
    normalizer = _Normalizer()
    return normalizer.visit(tree)


# ---------------------------------------------------------------------------
# Similarity A: node-type histogram
# ---------------------------------------------------------------------------

def _node_type_histogram(tree) -> dict:
    if tree is None:
        return {}
    counts = collections.Counter()
    for node in ast.walk(tree):
        counts[type(node).__name__] += 1
    return dict(counts)


def ast_node_type_similarity(src_a: str, src_b: str) -> float:
    tree_a = normalize_ast(src_a)
    tree_b = normalize_ast(src_b)
    h_a = _node_type_histogram(tree_a)
    h_b = _node_type_histogram(tree_b)
    # Jaccard on key sets
    keys_a = set(h_a)
    keys_b = set(h_b)
    all_keys = keys_a | keys_b
    if not all_keys:
        return 1.0
    jaccard = len(keys_a & keys_b) / len(all_keys)
    # Normalized L1 on counts
    total = sum(h_a.values()) + sum(h_b.values())
    if total == 0:
        l1 = 0.0
    else:
        l1 = sum(abs(h_a.get(k, 0) - h_b.get(k, 0)) for k in all_keys) / total
    return 0.5 * jaccard + 0.5 * (1.0 - l1)


# ---------------------------------------------------------------------------
# Similarity B: linearized sequence edit distance (primary)
# ---------------------------------------------------------------------------

def _linearize_ast(tree) -> list:
    """Depth-first preorder traversal of node type names."""
    if tree is None:
        return []
    result = []
    for node in ast.walk(tree):
        result.append(type(node).__name__)
    return result[:MAX_SEQ_LEN]


def _edit_distance(seq_a: list, seq_b: list) -> int:
    """Wagner-Fischer edit distance (substitution cost=1)."""
    n, m = len(seq_a), len(seq_b)
    if n == 0:
        return m
    if m == 0:
        return n
    # Use 1-row rolling approach
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        curr = [i] + [0] * m
        for j in range(1, m + 1):
            if seq_a[i - 1] == seq_b[j - 1]:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev = curr
    return prev[m]


def ast_sequence_similarity(src_a: str, src_b: str) -> float:
    tree_a = normalize_ast(src_a)
    tree_b = normalize_ast(src_b)
    seq_a = _linearize_ast(tree_a)
    seq_b = _linearize_ast(tree_b)
    if not seq_a and not seq_b:
        return 1.0
    max_len = max(len(seq_a), len(seq_b))
    dist = _edit_distance(seq_a, seq_b)
    return 1.0 - dist / max_len


# Primary: combined
def score_fn(src_a: str, src_b: str) -> float:
    return ast_sequence_similarity(src_a, src_b)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    dev_pairs = load_pairs("dev")
    test_pairs = load_pairs("test")

    dev_m, test_m, threshold = run_baseline(
        "B02", score_fn, dev_pairs, test_pairs,
        artifact_dir=ARTIFACT_DIR
    )

    print(f"\n=== B2 AST Similarity Baseline ===")
    print(f"  DEV  F1={dev_m['f1']:.4f} AUROC={dev_m['auroc']:.4f}")
    print(f"  TEST F1={test_m['f1']:.4f} AUROC={test_m['auroc']:.4f} "
          f"[{test_m['ci_f1_lower']:.3f}–{test_m['ci_f1_upper']:.3f}]")
