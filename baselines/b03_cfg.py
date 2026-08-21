"""
baselines/b03_cfg.py — B3: Control-Flow Graph Similarity Baseline (SBG Phase 3).

Builds a simplified CFG from a Python AST (no execution required) and computes
two structural similarity measures between program pairs.

CFG construction
----------------
1. Parse source with ast.parse.
2. Walk top-level and function bodies to build basic blocks:
   - A basic block is a maximal sequence of straight-line statements.
   - New blocks are created at: function definitions, if/else branches,
     for/while loops (body + orelse), try/except/finally clauses, and
     the implicit merge point after each branching construct.
3. Node features: each block records only AST node-type names (no values,
   no variable names).  Literals are replaced with a canonical
   "<Literal>" token; variable names with "<Name>".
4. Edges carry a type drawn from {seq, true, false, loop, except}.

Known limitations (static analysis cannot capture)
--------------------------------------------------
- Dynamic dispatch: method resolution depends on runtime types.
- Higher-order functions: which callable is actually invoked is unknown.
- Runtime polymorphism: conditional branches guarded by runtime values
  may always take one path, but static analysis treats both as reachable.
- Generator/coroutine suspension points are approximated as plain calls.
- Import-time side-effects and eval/exec are ignored.

These limitations mean the CFG over-approximates reachable paths and
may produce false similarities when dynamic control-flow diverges.

Similarity functions
--------------------
A. cfg_node_distribution_similarity(src_a, src_b) -> float
   Jaccard on the set of unique block "signatures" (tuple of node-type tokens).

B. cfg_structure_similarity(src_a, src_b) -> float
   0.5 * size_similarity + 0.5 * edge_type_jaccard
   where size_similarity = 1 - |size_a - size_b| / max(size_a, size_b, 1)
   and edge_type_jaccard compares edge-type count histograms.

Primary score: cfg_structure_similarity.
"""

import ast
import json
import math
import pathlib
import sys
from collections import Counter, defaultdict

# ---------------------------------------------------------------------------
# Repo root so relative paths in pair records resolve correctly
# ---------------------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "baselines"))
from common import load_pairs, compute_metrics, find_optimal_threshold, save_results

OUTPUT_DIR = REPO_ROOT / "artifacts" / "phase3" / "B03"

# ---------------------------------------------------------------------------
# AST normalisation helpers
# ---------------------------------------------------------------------------

_LITERAL_TYPES = (
    ast.Constant, ast.Num, ast.Str, ast.Bytes, ast.NameConstant, ast.Ellipsis
)


def _node_token(node: ast.AST) -> str:
    """Return a normalised string token for an AST node.

    All variable names → "<Name>"; all literals → "<Literal>";
    everything else → the AST class name.
    """
    if isinstance(node, ast.Name):
        return "<Name>"
    if isinstance(node, _LITERAL_TYPES):
        return "<Literal>"
    return type(node).__name__


# ---------------------------------------------------------------------------
# CFG data structures
# ---------------------------------------------------------------------------

class BasicBlock:
    """A basic block: a sequence of straight-line statements."""

    __slots__ = ("idx", "node_types", "stmts")

    def __init__(self, idx: int):
        self.idx = idx
        self.node_types: list = []   # list of normalised token strings
        self.stmts: list = []        # raw ast statement nodes (for edge building)

    def signature(self) -> tuple:
        return tuple(self.node_types)


class CFG:
    """A simplified control-flow graph."""

    def __init__(self):
        self.blocks: list = []       # list[BasicBlock]
        self.edges: list = []        # list of (src_idx, dst_idx, edge_type)
        self._next_idx = 0

    def new_block(self) -> BasicBlock:
        b = BasicBlock(self._next_idx)
        self._next_idx += 1
        self.blocks.append(b)
        return b

    def add_edge(self, src: BasicBlock, dst: BasicBlock, etype: str):
        if src is not None and dst is not None:
            self.edges.append((src.idx, dst.idx, etype))


# ---------------------------------------------------------------------------
# CFG Builder
# ---------------------------------------------------------------------------

class CFGBuilder(ast.NodeVisitor):
    """Builds a simplified CFG by walking an AST module."""

    # Statement node types that do NOT introduce new blocks on their own
    _PLAIN_STMT_TYPES = frozenset({
        "Assign", "AugAssign", "AnnAssign", "Return", "Delete",
        "Expr", "Pass", "Break", "Continue", "Raise", "Assert",
        "Import", "ImportFrom", "Global", "Nonlocal",
    })

    def __init__(self):
        self.cfg = CFG()
        self._current: BasicBlock = None

    # ------------------------------------------------------------------
    # Block management
    # ------------------------------------------------------------------

    def _new_block(self, predecessor: BasicBlock = None,
                   etype: str = "seq") -> BasicBlock:
        b = self.cfg.new_block()
        if predecessor is not None:
            self.cfg.add_edge(predecessor, b, etype)
        return b

    def _add_stmt_token(self, node: ast.AST):
        if self._current is not None:
            self._current.node_types.append(_node_token(node))
            # Also record sub-expression tokens (non-recursive to avoid explosion)
            for child in ast.iter_child_nodes(node):
                self._current.node_types.append(_node_token(child))

    # ------------------------------------------------------------------
    # Statement dispatch
    # ------------------------------------------------------------------

    def _visit_stmts(self, stmts: list, entry: BasicBlock) -> BasicBlock:
        """Walk a statement list; return the exit block (may differ from entry)."""
        self._current = entry
        for stmt in stmts:
            self._current = self._visit_stmt(stmt)
        return self._current

    def _visit_stmt(self, node: ast.AST) -> BasicBlock:
        """Dispatch a single statement; return the block that follows it."""
        type_name = type(node).__name__
        if type_name in self._PLAIN_STMT_TYPES:
            self._add_stmt_token(node)
            return self._current

        method = f"_stmt_{type_name}"
        if hasattr(self, method):
            return getattr(self, method)(node)

        # Unknown statement — record type and continue in current block
        self._add_stmt_token(node)
        return self._current

    # ------------------------------------------------------------------
    # Compound statements
    # ------------------------------------------------------------------

    def _stmt_If(self, node: ast.If) -> BasicBlock:
        """Build blocks for if / elif / else."""
        test_block = self._current
        test_block.node_types.append("If")

        # True branch
        true_entry = self._new_block(test_block, "true")
        true_exit = self._visit_stmts(node.body, true_entry)

        # False / else branch
        if node.orelse:
            false_entry = self._new_block(test_block, "false")
            false_exit = self._visit_stmts(node.orelse, false_entry)
        else:
            false_entry = self._new_block(test_block, "false")
            false_exit = false_entry

        # Merge block
        merge = self._new_block()
        self.cfg.add_edge(true_exit, merge, "seq")
        self.cfg.add_edge(false_exit, merge, "seq")
        return merge

    def _stmt_For(self, node: ast.For) -> BasicBlock:
        return self._build_loop(node, "For")

    def _stmt_While(self, node: ast.While) -> BasicBlock:
        return self._build_loop(node, "While")

    def _build_loop(self, node: ast.AST, label: str) -> BasicBlock:
        header = self._current
        header.node_types.append(label)

        # Body
        body_entry = self._new_block(header, "loop")
        body_exit = self._visit_stmts(node.body, body_entry)
        # Back-edge
        self.cfg.add_edge(body_exit, header, "loop")

        # orelse (executed when loop condition is False / exhausted)
        if node.orelse:
            orelse_entry = self._new_block(header, "false")
            orelse_exit = self._visit_stmts(node.orelse, orelse_entry)
        else:
            orelse_exit = None

        # Exit block
        exit_block = self._new_block(header, "seq")
        if orelse_exit is not None:
            self.cfg.add_edge(orelse_exit, exit_block, "seq")
        return exit_block

    def _stmt_Try(self, node: ast.Try) -> BasicBlock:
        """Approximate try/except/else/finally."""
        header = self._current
        header.node_types.append("Try")

        # Try body
        try_entry = self._new_block(header, "seq")
        try_exit = self._visit_stmts(node.body, try_entry)

        exits = [try_exit]

        # Handlers
        for handler in node.handlers:
            h_entry = self._new_block(header, "except")
            h_entry.node_types.append("ExceptHandler")
            h_exit = self._visit_stmts(handler.body, h_entry)
            exits.append(h_exit)

        # orelse (runs if no exception)
        if node.orelse:
            or_entry = self._new_block(try_exit, "seq")
            or_exit = self._visit_stmts(node.orelse, or_entry)
            exits.append(or_exit)

        # finally
        if node.finalbody:
            fin_entry = self._new_block()
            for ex in exits:
                self.cfg.add_edge(ex, fin_entry, "seq")
            fin_exit = self._visit_stmts(node.finalbody, fin_entry)
            merge = self._new_block(fin_exit, "seq")
        else:
            merge = self._new_block()
            for ex in exits:
                self.cfg.add_edge(ex, merge, "seq")

        return merge

    def _stmt_FunctionDef(self, node: ast.FunctionDef) -> BasicBlock:
        return self._build_funcdef(node)

    def _stmt_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> BasicBlock:
        return self._build_funcdef(node)

    def _build_funcdef(self, node) -> BasicBlock:
        # Record the def in the current block
        self._current.node_types.append("FunctionDef")

        # Build a sub-CFG for the function body (disconnected from caller CFG)
        saved = self._current
        func_entry = self._new_block()
        self._visit_stmts(node.body, func_entry)
        # Restore current; the function def is a statement in the enclosing block
        self._current = saved
        return self._current

    def _stmt_ClassDef(self, node: ast.ClassDef) -> BasicBlock:
        self._current.node_types.append("ClassDef")
        # Process class body methods as sub-CFGs
        saved = self._current
        cls_entry = self._new_block()
        self._visit_stmts(node.body, cls_entry)
        self._current = saved
        return self._current

    def _stmt_With(self, node: ast.With) -> BasicBlock:
        self._current.node_types.append("With")
        exit_block = self._visit_stmts(node.body, self._current)
        return exit_block

    def _stmt_AsyncWith(self, node: ast.AsyncWith) -> BasicBlock:
        return self._stmt_With(node)

    def _stmt_AsyncFor(self, node: ast.AsyncFor) -> BasicBlock:
        return self._build_loop(node, "AsyncFor")


def _build_cfg(source: str) -> CFG:
    """Parse *source* and return its CFG. Returns an empty CFG on parse error."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return CFG()

    builder = CFGBuilder()
    entry = builder.cfg.new_block()
    builder._visit_stmts(tree.body, entry)
    return builder.cfg


def _read_source(path: str) -> str:
    full = REPO_ROOT / path
    return full.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Similarity functions
# ---------------------------------------------------------------------------

def cfg_node_distribution_similarity(src_a: str, src_b: str) -> float:
    """Jaccard similarity on the sets of unique block signatures.

    Each signature is a tuple of normalised node-type tokens for one basic block.
    Returns a value in [0, 1].
    """
    cfg_a = _build_cfg(src_a)
    cfg_b = _build_cfg(src_b)

    sigs_a = set(b.signature() for b in cfg_a.blocks if b.node_types)
    sigs_b = set(b.signature() for b in cfg_b.blocks if b.node_types)

    if not sigs_a and not sigs_b:
        return 1.0
    inter = len(sigs_a & sigs_b)
    union = len(sigs_a | sigs_b)
    return inter / union if union > 0 else 0.0


def cfg_structure_similarity(src_a: str, src_b: str) -> float:
    """Combined structural size + edge-type histogram similarity.

    size_similarity = 1 - |size_a - size_b| / max(size_a, size_b, 1)
    where size = |V| + |E| for each CFG.

    edge_type_jaccard = Jaccard on edge-type count histograms, treating each
    (edge_type, count) as a multiset element.

    Returns: 0.5 * size_similarity + 0.5 * edge_type_jaccard  ∈ [0, 1].
    """
    cfg_a = _build_cfg(src_a)
    cfg_b = _build_cfg(src_b)

    size_a = len(cfg_a.blocks) + len(cfg_a.edges)
    size_b = len(cfg_b.blocks) + len(cfg_b.edges)

    denom = max(size_a, size_b, 1)
    size_sim = 1.0 - abs(size_a - size_b) / denom

    # Edge-type histograms
    def edge_hist(cfg: CFG) -> Counter:
        return Counter(etype for (_, _, etype) in cfg.edges)

    hist_a = edge_hist(cfg_a)
    hist_b = edge_hist(cfg_b)

    # Multiset Jaccard: sum of mins / sum of maxes
    all_types = set(hist_a) | set(hist_b)
    if all_types:
        intersection = sum(min(hist_a[t], hist_b[t]) for t in all_types)
        union_ms = sum(max(hist_a[t], hist_b[t]) for t in all_types)
        edge_jaccard = intersection / union_ms if union_ms > 0 else 1.0
    else:
        edge_jaccard = 1.0

    return 0.5 * size_sim + 0.5 * edge_jaccard


# ---------------------------------------------------------------------------
# Scoring over a split
# ---------------------------------------------------------------------------

def score_pairs(pairs: list) -> list:
    """Return primary similarity scores (cfg_structure_similarity) for *pairs*."""
    scores = []
    for pair in pairs:
        try:
            src_a = _read_source(pair["base_path"])
            src_b = _read_source(pair["variant_path"])
            s = cfg_structure_similarity(src_a, src_b)
        except Exception:
            s = 0.0
        scores.append(s)
    return scores


# ---------------------------------------------------------------------------
# __main__
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # --- Dev split: find optimal threshold ---
    print("B3 CFG Baseline — loading dev split …")
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
        "baseline": "B03_CFG",
        "split": "dev",
        "threshold": threshold,
        "metrics": dev_metrics,
        "predictions": dev_preds,
    }, OUTPUT_DIR / "dev")

    # --- Test split: apply threshold found on dev ---
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
        "baseline": "B03_CFG",
        "split": "test",
        "threshold": threshold,
        "metrics": test_metrics,
        "predictions": test_preds,
    }, OUTPUT_DIR / "test")

    print(f"  Results saved to {OUTPUT_DIR}")
