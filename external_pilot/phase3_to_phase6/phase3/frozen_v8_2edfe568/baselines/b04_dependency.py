"""
baselines/b04_dependency.py — B4: Data/Control Dependency Approximation (SBG Phase 3).

IMPORTANT: This is a static use-def approximation, NOT a full PDG.

A full Program Dependence Graph (PDG) requires:
  - Precise def-use chains with reaching-definition analysis.
  - Data-flow equations solved to a fixed point across basic blocks.
  - Precise control-dependence computation (post-dominance frontiers).

This implementation approximates those properties using AST walks alone:
  - Def sites  = all names that appear as assignment targets (lvalue positions).
  - Use sites  = all names that appear in load (rvalue) positions.
  - Data dep edges = (def_name, use_name) pairs within a function where a name
    is both defined and later read.  No ordering or reaching-definition check is
    performed; the set is conservative (over-approximate).
  - Control dep depth = maximum nesting level at which an assignment appears
    inside if/for/while bodies.  A deeper nesting level hints at stronger
    control dependence, but without post-dominator analysis this is an
    approximation.
  - Cross-function dependencies = (callee_name, arg_name) pairs capturing
    which names are passed as arguments to which functions.

Results should be interpreted as an upper bound on what a full PDG baseline
could achieve.  This approximation cannot capture:
  - Aliasing (two names bound to the same object).
  - Dynamic dependencies (attribute accesses, subscripts at runtime).
  - Precise control dependence (only nesting depth is available).
  - Inter-procedural data flow beyond explicit call-argument capture.
  - Generator/coroutine dependency chains.

Similarity functions
--------------------
A. dep_feature_similarity(src_a, src_b) -> float
   L1 distance on a normalised feature vector built from program-level
   dependency statistics.  Returns 1 - normalised_L1 ∈ [0, 1].

B. dep_graph_similarity(src_a, src_b) -> float
   Jaccard similarity on the union of all data-dep edge sets across all
   functions.  Returns |A ∩ B| / |A ∪ B| ∈ [0, 1].

Primary score: 0.5 * dep_feature_similarity + 0.5 * dep_graph_similarity.
"""

import ast
import json
import math
import pathlib
import sys
from collections import Counter, defaultdict

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "baselines"))
from common import load_pairs, compute_metrics, find_optimal_threshold, save_results

OUTPUT_DIR = REPO_ROOT / "artifacts" / "phase3" / "B04"


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

def _names_in_targets(targets: list) -> set:
    """Collect all Name ids that appear in assignment target nodes."""
    names = set()
    for t in targets:
        for node in ast.walk(t):
            if isinstance(node, ast.Name):
                names.add(node.id)
    return names


def _names_in_value(node: ast.AST) -> set:
    """Collect all Name ids used in load context within *node*."""
    names = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            names.add(n.id)
    return names


# ---------------------------------------------------------------------------
# Per-function dependency extraction
# ---------------------------------------------------------------------------

class FunctionDepVisitor(ast.NodeVisitor):
    """Extract use-def info from a single function body."""

    def __init__(self):
        self.defs: set = set()           # names assigned (def sites)
        self.uses: set = set()           # names read (use sites)
        self._max_depth: int = 0         # max nesting depth of assignments
        self._depth: int = 0             # current control-nesting depth
        self.cross_calls: list = []      # (callee_name, arg_name) pairs

    # ------------------------------------------------------------------
    # Statement visitors
    # ------------------------------------------------------------------

    def visit_Assign(self, node: ast.Assign):
        self.defs |= _names_in_targets(node.targets)
        self.uses |= _names_in_value(node.value)
        self._max_depth = max(self._max_depth, self._depth)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign):
        if isinstance(node.target, ast.Name):
            self.defs.add(node.target.id)
            self.uses.add(node.target.id)   # augmented assign also reads
        self.uses |= _names_in_value(node.value)
        self._max_depth = max(self._max_depth, self._depth)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if node.value is not None:
            if isinstance(node.target, ast.Name):
                self.defs.add(node.target.id)
            self.uses |= _names_in_value(node.value)
            self._max_depth = max(self._max_depth, self._depth)

    def visit_For(self, node: ast.For):
        self.defs |= _names_in_targets([node.target])
        self.uses |= _names_in_value(node.iter)
        self._depth += 1
        for stmt in node.body + node.orelse:
            self.visit(stmt)
        self._depth -= 1

    def visit_If(self, node: ast.If):
        self.uses |= _names_in_value(node.test)
        self._depth += 1
        for stmt in node.body + node.orelse:
            self.visit(stmt)
        self._depth -= 1

    def visit_While(self, node: ast.While):
        self.uses |= _names_in_value(node.test)
        self._depth += 1
        for stmt in node.body + node.orelse:
            self.visit(stmt)
        self._depth -= 1

    def visit_Call(self, node: ast.Call):
        # Capture (callee_name, arg_name) for all Name arguments
        callee = None
        if isinstance(node.func, ast.Name):
            callee = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee = node.func.attr

        if callee:
            for arg in node.args:
                for n in ast.walk(arg):
                    if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                        self.cross_calls.append((callee, n.id))

        self.generic_visit(node)

    # Prevent descending into nested function defs (handled separately)
    def visit_FunctionDef(self, node):
        pass

    def visit_AsyncFunctionDef(self, node):
        pass


def _extract_function_deps(func_node: ast.FunctionDef) -> dict:
    """Run FunctionDepVisitor over a function AST node."""
    visitor = FunctionDepVisitor()
    for stmt in func_node.body:
        visitor.visit(stmt)

    defs = visitor.defs
    uses = visitor.uses
    total = len(defs) + len(uses)
    def_use_ratio = len(defs) / total if total > 0 else 0.0

    # Data-dep edges: (def_name, use_name) where name is both defined and used
    dep_edges = set()
    for d in defs:
        for u in uses:
            if d == u:
                dep_edges.add((d, u))
            # Also capture explicit flow: a name defined then another name uses it
            # (conservative: all cross-pairs)
            else:
                dep_edges.add((d, u))

    return {
        "variable_definitions": defs,
        "variable_uses": uses,
        "def_use_ratio": def_use_ratio,
        "data_dep_edges": dep_edges,
        "control_dep_depth": visitor._max_depth,
        "cross_function_deps": set(visitor.cross_calls),
    }


# ---------------------------------------------------------------------------
# Module-level dependency extraction
# ---------------------------------------------------------------------------

def _extract_module_deps(source: str) -> dict:
    """Parse *source* and return program-level dependency features.

    Returns a dict with:
      functions       : list of per-function dicts
      total_def_use_ratio
      avg_control_dep_depth
      data_dep_edge_count
      inter_function_dep_count
      all_data_dep_edges   (set of (def, use) across all functions)
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {
            "functions": [],
            "total_def_use_ratio": 0.0,
            "avg_control_dep_depth": 0.0,
            "data_dep_edge_count": 0,
            "inter_function_dep_count": 0,
            "all_data_dep_edges": set(),
        }

    # Collect all function defs (including nested, using walk)
    func_nodes = [
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    func_deps = [_extract_function_deps(fn) for fn in func_nodes]

    # Module-level statements (non-function) treated as an implicit "module" function
    module_stmts = [
        s for s in tree.body
        if not isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef,
                               ast.ClassDef))
    ]
    if module_stmts:
        # Synthetic function node for module-level code
        synthetic = ast.FunctionDef(
            name="<module>",
            args=ast.arguments(
                posonlyargs=[], args=[], vararg=None,
                kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]
            ),
            body=module_stmts,
            decorator_list=[],
            returns=None,
        )
        ast.fix_missing_locations(synthetic)
        func_deps.append(_extract_function_deps(synthetic))

    if not func_deps:
        return {
            "functions": [],
            "total_def_use_ratio": 0.0,
            "avg_control_dep_depth": 0.0,
            "data_dep_edge_count": 0,
            "inter_function_dep_count": 0,
            "all_data_dep_edges": set(),
        }

    total_def_use_ratio = sum(f["def_use_ratio"] for f in func_deps) / len(func_deps)
    avg_control_dep_depth = (
        sum(f["control_dep_depth"] for f in func_deps) / len(func_deps)
    )
    all_edges: set = set()
    for f in func_deps:
        all_edges |= f["data_dep_edges"]
    inter_deps: set = set()
    for f in func_deps:
        inter_deps |= f["cross_function_deps"]

    return {
        "functions": func_deps,
        "total_def_use_ratio": total_def_use_ratio,
        "avg_control_dep_depth": avg_control_dep_depth,
        "data_dep_edge_count": len(all_edges),
        "inter_function_dep_count": len(inter_deps),
        "all_data_dep_edges": all_edges,
    }


# ---------------------------------------------------------------------------
# Similarity functions
# ---------------------------------------------------------------------------

def dep_feature_similarity(src_a: str, src_b: str) -> float:
    """L1-distance similarity on normalised dependency feature vectors.

    Feature vector (4 components):
      [total_def_use_ratio, avg_control_dep_depth (norm), data_dep_edge_count (norm),
       inter_function_dep_count (norm)]

    Each component is normalised to [0, 1] by dividing by the max across the pair.
    L1 distance ∈ [0, 4] is mapped to similarity = 1 - L1/4.
    Returns value in [0, 1].
    """
    da = _extract_module_deps(src_a)
    db = _extract_module_deps(src_b)

    def _norm_pair(va, vb):
        m = max(va, vb, 1e-9)
        return va / m, vb / m

    feats = [
        ("total_def_use_ratio",     da["total_def_use_ratio"],     db["total_def_use_ratio"]),
        ("avg_control_dep_depth",   da["avg_control_dep_depth"],   db["avg_control_dep_depth"]),
        ("data_dep_edge_count",     da["data_dep_edge_count"],     db["data_dep_edge_count"]),
        ("inter_function_dep_count",da["inter_function_dep_count"],db["inter_function_dep_count"]),
    ]

    l1 = 0.0
    for _, va, vb in feats:
        na, nb = _norm_pair(va, vb)
        l1 += abs(na - nb)

    return 1.0 - l1 / 4.0


def dep_graph_similarity(src_a: str, src_b: str) -> float:
    """Jaccard similarity on the sets of data-dependency edges.

    Edges are (def_name, use_name) pairs from use-def analysis across all
    functions.  Returns |A ∩ B| / |A ∪ B| ∈ [0, 1].
    """
    da = _extract_module_deps(src_a)
    db = _extract_module_deps(src_b)

    edges_a = da["all_data_dep_edges"]
    edges_b = db["all_data_dep_edges"]

    if not edges_a and not edges_b:
        return 1.0
    inter = len(edges_a & edges_b)
    union = len(edges_a | edges_b)
    return inter / union if union > 0 else 0.0


def dep_combined_similarity(src_a: str, src_b: str) -> float:
    """Primary score: 0.5 * dep_feature_similarity + 0.5 * dep_graph_similarity."""
    return 0.5 * dep_feature_similarity(src_a, src_b) + \
           0.5 * dep_graph_similarity(src_a, src_b)


# ---------------------------------------------------------------------------
# Scoring over a split
# ---------------------------------------------------------------------------

def _read_source(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def score_pairs(pairs: list) -> list:
    """Return primary similarity scores for *pairs*."""
    scores = []
    for pair in pairs:
        try:
            src_a = _read_source(pair["base_path"])
            src_b = _read_source(pair["variant_path"])
            s = dep_combined_similarity(src_a, src_b)
        except Exception:
            s = 0.0
        scores.append(s)
    return scores


# ---------------------------------------------------------------------------
# __main__
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("B4 Dependency Baseline — loading dev split …")
    dev_pairs = load_pairs("dev")
    dev_scores = score_pairs(dev_pairs)

    threshold = find_optimal_threshold(dev_pairs, dev_scores)
    print(f"  Optimal threshold (dev): {threshold:.4f}")

    dev_metrics = compute_metrics(dev_pairs, dev_scores, threshold)
    print(f"  Dev  — F1: {dev_metrics['f1']:.4f}  "
          f"[{dev_metrics['f1_ci_low']:.4f}, {dev_metrics['f1_ci_high']:.4f}]  "
          f"AUC≈{dev_metrics['auc_approx']:.4f}")

    dev_preds = []
    for pair, score in zip(dev_pairs, dev_scores):
        dev_preds.append({
            "pair_id": pair["pair_id"],
            "score": round(score, 6),
            "predicted_label": "EQUIVALENT" if score >= threshold else "NON_EQUIVALENT",
            "expected_label": pair["expected_label"],
        })

    save_results({
        "baseline": "B04_DEPENDENCY",
        "split": "dev",
        "threshold": threshold,
        "metrics": dev_metrics,
        "predictions": dev_preds,
    }, OUTPUT_DIR / "dev")

    print("  Loading test split …")
    test_pairs = load_pairs("test")
    test_scores = score_pairs(test_pairs)

    test_metrics = compute_metrics(test_pairs, test_scores, threshold)
    print(f"  Test — F1: {test_metrics['f1']:.4f}  "
          f"[{test_metrics['f1_ci_low']:.4f}, {test_metrics['f1_ci_high']:.4f}]  "
          f"AUC≈{test_metrics['auc_approx']:.4f}")

    test_preds = []
    for pair, score in zip(test_pairs, test_scores):
        test_preds.append({
            "pair_id": pair["pair_id"],
            "score": round(score, 6),
            "predicted_label": "EQUIVALENT" if score >= threshold else "NON_EQUIVALENT",
            "expected_label": pair["expected_label"],
        })

    save_results({
        "baseline": "B04_DEPENDENCY",
        "split": "test",
        "threshold": threshold,
        "metrics": test_metrics,
        "predictions": test_preds,
    }, OUTPUT_DIR / "test")

    print(f"  Results saved to {OUTPUT_DIR}")
