"""
sbg/extraction/static/extractor.py
====================================
Static analysis extraction for the SBG engine.

Implements:
  - StaticExtractor  →  StaticFeatures
  - ControlGenomeExtractor  →  ControlGenome
  - distance(g1, g2)   → float  in [0, 1]
  - canonicalize(g)    → ControlGenome  (idempotent)

Uses only Python stdlib (ast, math, collections).  No external dependencies.
No code is executed — all analysis is purely structural / AST-based.

Design notes
------------
The CONTROL dimension (g_C, Definition 9 of FORMAL_MODEL.md) requires:
  • branch probability profile   → static approximation: normalised branch-type
                                    frequency counts over the AST
  • call graph edges              → static caller → callee pairs from Call nodes
  • loop nesting profile          → depth histogram of For/While/AsyncFor nodes
  • cyclomatic complexity         → McCabe formula V(G) = E - N + 2P
  • control-flow entropy          → Shannon entropy of branch-type distribution

McCabe approximation from the AST (no explicit CFG built):
  V(G) = 1 + number of binary-branching predicates
       = 1 + If + While + For + AsyncFor + ExceptHandler
           + comprehension_ifs + BoolOp(And/Or) terms
"""

from __future__ import annotations

import ast
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TOOL_VERSION = "sbg-static-extractor-0.1.0"
_PYTHON_VERSION = f"cpython-{sys.version_info.major}.{sys.version_info.minor}"


def _safe_parse(source_code: str) -> ast.Module:
    """Parse source, raising ValueError with a clean message on syntax error."""
    try:
        return ast.parse(source_code)
    except SyntaxError as exc:
        raise ValueError(f"Syntax error in source: {exc}") from exc


# ---------------------------------------------------------------------------
# StaticFeatures — raw structural features
# ---------------------------------------------------------------------------

@dataclass
class StaticFeatures:
    """Low-level structural features extracted from Python source via AST."""

    # ---- CFG approximation ----
    cfg_node_count: int = 0        # approximate: one node per statement
    cfg_edge_count: int = 0        # approximate: sequential + branch edges

    # ---- Branch / control ----
    branch_count: int = 0          # if / elif / else / while / for / try branches
    loop_count: int = 0            # for + while + async for
    function_count: int = 0        # def + async def (top-level and nested)

    # ---- Call sites ----
    call_sites: List[str] = field(default_factory=list)  # callee names (best-effort)

    # ---- Complexity ----
    cyclomatic_complexity: int = 1  # McCabe V(G), lower-bound 1
    max_nesting_depth: int = 0

    # ---- Error handling ----
    exception_handlers: int = 0    # except / except* clauses

    # ---- Return / recursion ----
    return_sites: int = 0
    has_recursion: bool = False

    # ---- Imports ----
    import_names: List[str] = field(default_factory=list)  # top-level module names

    # ---- Variables ----
    global_variables: List[str] = field(default_factory=list)  # global-scope Name stores
    local_variable_count: int = 0  # Name stores inside function scopes

    # ---- AST histogram ----
    ast_node_type_histogram: Dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# _StaticVisitor — single-pass AST walker
# ---------------------------------------------------------------------------

class _StaticVisitor(ast.NodeVisitor):
    """
    Single-pass AST visitor that collects all StaticFeatures data.

    Tracks:
      • statement count              → cfg_node_count proxy
      • branch count & loop count
      • function defs (incl. nested)
      • call-site names
      • McCabe complexity predicates
      • nesting depth (control structures only)
      • exception handlers
      • return statements
      • imports
      • global / local variable stores
      • node-type histogram
      • recursion detection
    """

    # AST node types that count as a CFG node (one per statement/expression-stmt)
    _STMT_TYPES = (
        ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Expr,
        ast.Return, ast.Delete, ast.Pass, ast.Break, ast.Continue,
        ast.Raise, ast.Assert, ast.Global, ast.Nonlocal,
        ast.Import, ast.ImportFrom,
        ast.If, ast.For, ast.While, ast.With, ast.AsyncWith,
        ast.AsyncFor, ast.Try, ast.FunctionDef, ast.AsyncFunctionDef,
        ast.ClassDef,
    )
    # Python 3.11+ TryStar
    if hasattr(ast, "TryStar"):
        _STMT_TYPES = _STMT_TYPES + (ast.TryStar,)  # type: ignore[attr-defined]

    def __init__(self) -> None:
        # raw accumulators
        self._stmt_count: int = 0
        self._branch_count: int = 0
        self._loop_count: int = 0
        self._func_names: List[str] = []        # names of all FunctionDef nodes
        self._call_sites: List[str] = []
        self._complexity_predicates: int = 0    # extra branches for McCabe
        self._exception_handlers: int = 0
        self._return_sites: int = 0
        self._import_names: List[str] = []
        self._global_stores: List[str] = []     # module-level Name store targets
        self._local_stores: int = 0             # Name store targets inside funcs
        self._node_type_counts: Counter = Counter()

        # depth tracking (control structures only)
        self._current_nesting: int = 0
        self._max_nesting: int = 0

        # scope tracking for global vs local variable distinction
        self._func_depth: int = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _enter_ctrl(self) -> None:
        self._current_nesting += 1
        if self._current_nesting > self._max_nesting:
            self._max_nesting = self._current_nesting

    def _leave_ctrl(self) -> None:
        self._current_nesting -= 1

    def _enter_func(self) -> None:
        self._func_depth += 1

    def _leave_func(self) -> None:
        self._func_depth -= 1

    def _count_node(self, node: ast.AST) -> None:
        name = type(node).__name__
        self._node_type_counts[name] += 1

    def _extract_call_name(self, node: ast.Call) -> str:
        """Best-effort extraction of a callee name from a Call node."""
        func = node.func
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            # e.g. obj.method  →  "method"
            return func.attr
        return "<anonymous>"

    # ------------------------------------------------------------------
    # Visitor methods
    # ------------------------------------------------------------------

    def visit(self, node: ast.AST) -> None:  # type: ignore[override]
        self._count_node(node)
        if isinstance(node, self._STMT_TYPES):
            self._stmt_count += 1
        super().visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._func_names.append(node.name)
        self._enter_func()
        self.generic_visit(node)
        self._leave_func()

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Don't count class body as a new function scope for variable purposes,
        # but do recurse.
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self._branch_count += 1
        # Each elif / else body is an additional branch
        if node.orelse:
            self._branch_count += 1
        self._complexity_predicates += 1
        self._enter_ctrl()
        self.generic_visit(node)
        self._leave_ctrl()

    def visit_While(self, node: ast.While) -> None:
        self._loop_count += 1
        self._branch_count += 1
        self._complexity_predicates += 1
        self._enter_ctrl()
        self.generic_visit(node)
        self._leave_ctrl()

    def visit_For(self, node: ast.For) -> None:
        self._loop_count += 1
        self._branch_count += 1
        self._complexity_predicates += 1
        self._enter_ctrl()
        self.generic_visit(node)
        self._leave_ctrl()

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._loop_count += 1
        self._branch_count += 1
        self._complexity_predicates += 1
        self._enter_ctrl()
        self.generic_visit(node)
        self._leave_ctrl()

    def visit_Try(self, node: ast.Try) -> None:
        self._branch_count += 1
        self._complexity_predicates += 1
        self._exception_handlers += len(node.handlers)
        self._enter_ctrl()
        self.generic_visit(node)
        self._leave_ctrl()

    # Python 3.11+ except*
    def visit_TryStar(self, node: ast.AST) -> None:  # type: ignore[override]
        handlers = getattr(node, "handlers", [])
        self._branch_count += 1
        self._complexity_predicates += 1
        self._exception_handlers += len(handlers)
        self._enter_ctrl()
        self.generic_visit(node)
        self._leave_ctrl()

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        # Already counted in visit_Try; just recurse.
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        self._enter_ctrl()
        self.generic_visit(node)
        self._leave_ctrl()

    visit_AsyncWith = visit_With  # type: ignore[assignment]

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        # Each 'and'/'or' short-circuit adds a branch predicate.
        # n values → n-1 binary decisions.
        self._complexity_predicates += len(node.values) - 1
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        # Ternary expression counts as 1 branch predicate.
        self._complexity_predicates += 1
        self.generic_visit(node)

    # List / set / dict / generator comprehensions — each 'if' is a branch.
    def _visit_comprehension_filters(self, generators: list) -> None:
        for gen in generators:
            self._complexity_predicates += len(gen.ifs)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self._visit_comprehension_filters(node.generators)
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self._visit_comprehension_filters(node.generators)
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self._visit_comprehension_filters(node.generators)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self._visit_comprehension_filters(node.generators)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        self._call_sites.append(self._extract_call_name(node))
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        self._return_sites += 1
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            # Keep top-level module name (before any dot)
            self._import_names.append(alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self._import_names.append(node.module.split(".")[0])
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store):
            if self._func_depth == 0:
                self._global_stores.append(node.id)
            else:
                self._local_stores += 1
        self.generic_visit(node)

    # ------------------------------------------------------------------
    # Post-processing helpers (called after traversal)
    # ------------------------------------------------------------------

    def _detect_recursion(self, tree: ast.Module) -> bool:
        """
        Check if any function calls itself (direct recursion only).
        Indirect recursion would require a call graph; omitted here.
        """
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fname = node.name
                for child in ast.walk(node):
                    if (
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Name)
                        and child.func.id == fname
                    ):
                        return True
        return False

    def _approx_cfg_edges(self) -> int:
        """
        Rough CFG edge count.
        Sequential edges: stmt_count - 1 (chain of statements).
        Branch edges: each branch predicate adds 2 edges (true/false).
        Exception edges: each handler is an additional edge.
        """
        sequential = max(0, self._stmt_count - 1)
        branch_edges = self._complexity_predicates * 2
        return sequential + branch_edges


# ---------------------------------------------------------------------------
# StaticExtractor
# ---------------------------------------------------------------------------

class StaticExtractor:
    """
    Extracts structural features from Python source code using the ``ast`` module.

    No code is executed.  Only Python source is currently supported.
    """

    def extract(self, source_code: str, language: str = "python") -> StaticFeatures:
        """
        Parse *source_code* and return a :class:`StaticFeatures` instance.

        Parameters
        ----------
        source_code : str
            Raw Python source text.
        language : str
            Language identifier.  Only ``"python"`` is supported; passing any
            other value raises :exc:`NotImplementedError`.

        Returns
        -------
        StaticFeatures
        """
        if language.lower() != "python":
            raise NotImplementedError(
                f"StaticExtractor currently supports 'python' only, got {language!r}"
            )

        tree = _safe_parse(source_code)

        visitor = _StaticVisitor()
        visitor.visit(tree)

        has_recursion = visitor._detect_recursion(tree)

        # Deduplicate import names (preserve order via dict)
        import_names = list(dict.fromkeys(visitor._import_names))

        # Deduplicate global variable stores
        global_vars = list(dict.fromkeys(visitor._global_stores))

        # McCabe cyclomatic complexity: V(G) = 1 + decision points
        cc = 1 + visitor._complexity_predicates

        cfg_nodes = visitor._stmt_count
        cfg_edges = visitor._approx_cfg_edges()

        return StaticFeatures(
            cfg_node_count=cfg_nodes,
            cfg_edge_count=cfg_edges,
            branch_count=visitor._branch_count,
            loop_count=visitor._loop_count,
            function_count=len(visitor._func_names),
            call_sites=visitor._call_sites,
            cyclomatic_complexity=cc,
            max_nesting_depth=visitor._max_nesting,
            exception_handlers=visitor._exception_handlers,
            return_sites=visitor._return_sites,
            has_recursion=has_recursion,
            import_names=import_names,
            global_variables=global_vars,
            local_variable_count=visitor._local_stores,
            ast_node_type_histogram=dict(visitor._node_type_counts),
        )


# ---------------------------------------------------------------------------
# ControlGenome — the g_C genome dimension (Definition 9)
# ---------------------------------------------------------------------------

@dataclass
class ControlGenome:
    """
    Static approximation of the CONTROL genome dimension g_C.

    Derived purely from AST analysis; dynamic quantities (actual branch
    probabilities, loop iteration counts) are approximated from structural
    frequency counts.

    Fields
    ------
    branch_probability_profile : Dict[str, float]
        Normalised frequency of each branch-statement type
        (If, For, While, AsyncFor, Try).  Values sum to 1.0 (or are all 0.0
        if no branches are present).

    call_graph_edges : List[Tuple[str, str]]
        Static caller → callee pairs.  Each entry is ``(caller_fn, callee_fn)``
        where *caller_fn* is the name of the enclosing FunctionDef (or
        ``"<module>"`` for top-level calls), and *callee_fn* is the best-effort
        resolved callee name.

    loop_nesting_profile : List[int]
        Histogram of loop depths.  ``loop_nesting_profile[d]`` is the number of
        loops (For/While/AsyncFor) whose nesting depth is exactly ``d``.
        Index 0 is unused (loops start at depth ≥ 1).

    cyclomatic_complexity : int
        McCabe complexity V(G) = 1 + decision-points.

    control_flow_entropy : float
        Shannon entropy of ``branch_probability_profile`` in bits.
        Zero when there is only one branch type.

    provenance : Dict
        Metadata: source hash, tool version, Python version, etc.
    """

    branch_probability_profile: Dict[str, float] = field(default_factory=dict)
    call_graph_edges: List[Tuple[str, str]] = field(default_factory=list)
    loop_nesting_profile: List[int] = field(default_factory=list)
    cyclomatic_complexity: int = 1
    control_flow_entropy: float = 0.0
    provenance: Dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# _ControlGenomeVisitor — detailed visitor for ControlGenome
# ---------------------------------------------------------------------------

class _ControlGenomeVisitor(ast.NodeVisitor):
    """
    Collects data needed to build a ControlGenome.

    Tracks:
      • branch-type counts (If / For / While / AsyncFor / Try)
      • static caller→callee edges
      • loop nesting depth per loop node
      • McCabe complexity predicates
    """

    # Branch types tracked for the branch probability profile.
    BRANCH_TYPES = ("If", "For", "While", "AsyncFor", "Try", "TryStar")

    def __init__(self) -> None:
        # branch type raw counts
        self._branch_type_counts: Counter = Counter()

        # call graph: list of (caller_name, callee_name)
        self._cg_edges: List[Tuple[str, str]] = []

        # nesting stack: element = (type, depth)
        # depth = number of control-flow structures above current node
        self._ctrl_depth: int = 0

        # loop depths: list of (depth, loop_type)
        self._loop_depth_records: List[int] = []  # depth values for loops

        # function scope stack (names, innermost last)
        self._func_stack: List[str] = ["<module>"]

        # McCabe predicates
        self._complexity_predicates: int = 0

    # ---- scope management ----

    @property
    def _current_func(self) -> str:
        return self._func_stack[-1]

    def _push_func(self, name: str) -> None:
        self._func_stack.append(name)

    def _pop_func(self) -> None:
        if len(self._func_stack) > 1:
            self._func_stack.pop()

    def _push_ctrl(self) -> None:
        self._ctrl_depth += 1

    def _pop_ctrl(self) -> None:
        self._ctrl_depth -= 1

    # ---- visitors ----

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._push_func(node.name)
        self.generic_visit(node)
        self._pop_func()

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def _visit_loop(self, node: ast.AST, branch_type: str) -> None:
        self._branch_type_counts[branch_type] += 1
        self._complexity_predicates += 1
        # Record loop depth BEFORE entering (depth of parent + 1)
        loop_depth = self._ctrl_depth + 1
        self._loop_depth_records.append(loop_depth)
        self._push_ctrl()
        self.generic_visit(node)
        self._pop_ctrl()

    def visit_For(self, node: ast.For) -> None:
        self._visit_loop(node, "For")

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._visit_loop(node, "AsyncFor")

    def visit_While(self, node: ast.While) -> None:
        self._visit_loop(node, "While")

    def visit_If(self, node: ast.If) -> None:
        self._branch_type_counts["If"] += 1
        self._complexity_predicates += 1
        self._push_ctrl()
        self.generic_visit(node)
        self._pop_ctrl()

    def visit_Try(self, node: ast.Try) -> None:
        self._branch_type_counts["Try"] += 1
        self._complexity_predicates += 1
        self._push_ctrl()
        self.generic_visit(node)
        self._pop_ctrl()

    def visit_TryStar(self, node: ast.AST) -> None:  # type: ignore[override]
        self._branch_type_counts["TryStar"] += 1
        self._complexity_predicates += 1
        self._push_ctrl()
        self.generic_visit(node)
        self._pop_ctrl()

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self._complexity_predicates += len(node.values) - 1
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self._complexity_predicates += 1
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        callee = _extract_call_name_simple(node)
        self._cg_edges.append((self._current_func, callee))
        self.generic_visit(node)

    def _visit_comprehension_filters(self, generators: list) -> None:
        for gen in generators:
            self._complexity_predicates += len(gen.ifs)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self._visit_comprehension_filters(node.generators)
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self._visit_comprehension_filters(node.generators)
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self._visit_comprehension_filters(node.generators)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self._visit_comprehension_filters(node.generators)
        self.generic_visit(node)

    # ---- result accessors ----

    def branch_probability_profile(self) -> Dict[str, float]:
        """Return normalised branch-type frequency dict."""
        total = sum(self._branch_type_counts.values())
        if total == 0:
            return {}
        return {k: v / total for k, v in sorted(self._branch_type_counts.items())}

    def loop_nesting_profile(self) -> List[int]:
        """
        Return a histogram list where index d holds the count of loops at depth d.
        Index 0 is always 0 (loops start at depth ≥ 1).
        """
        if not self._loop_depth_records:
            return []
        max_depth = max(self._loop_depth_records)
        hist = [0] * (max_depth + 1)   # index 0 … max_depth
        for d in self._loop_depth_records:
            hist[d] += 1
        return hist

    def cyclomatic_complexity(self) -> int:
        return 1 + self._complexity_predicates

    def call_graph_edges(self) -> List[Tuple[str, str]]:
        return list(self._cg_edges)


def _extract_call_name_simple(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return "<anonymous>"


# ---------------------------------------------------------------------------
# ControlGenomeExtractor
# ---------------------------------------------------------------------------

class ControlGenomeExtractor:
    """
    Extracts the CONTROL genome dimension (g_C) from Python source code.

    All analysis is static (AST-only).  Dynamic quantities such as branch-taken
    probabilities are approximated by structural frequency counts.
    """

    def extract(self, source_code: str) -> ControlGenome:
        """
        Parse *source_code* and return a :class:`ControlGenome`.

        Parameters
        ----------
        source_code : str
            Raw Python source text.

        Returns
        -------
        ControlGenome
        """
        import hashlib

        tree = _safe_parse(source_code)
        v = _ControlGenomeVisitor()
        v.visit(tree)

        bpp = v.branch_probability_profile()
        entropy = _shannon_entropy(list(bpp.values()))
        cc = v.cyclomatic_complexity()
        lnp = v.loop_nesting_profile()
        cg_edges = v.call_graph_edges()

        src_hash = hashlib.sha256(source_code.encode()).hexdigest()[:16]

        provenance: Dict = {
            "source_hash": src_hash,
            "tool": _TOOL_VERSION,
            "python_runtime": _PYTHON_VERSION,
            "analysis": "static_ast",
            "branch_types_observed": sorted(
                k for k, cnt in v._branch_type_counts.items() if cnt > 0
            ),
        }

        return ControlGenome(
            branch_probability_profile=bpp,
            call_graph_edges=cg_edges,
            loop_nesting_profile=lnp,
            cyclomatic_complexity=cc,
            control_flow_entropy=entropy,
            provenance=provenance,
        )


# ---------------------------------------------------------------------------
# distance
# ---------------------------------------------------------------------------

def distance(g1: ControlGenome, g2: ControlGenome) -> float:
    """
    Compute a symmetric distance in [0, 1] between two ControlGenomes.

    Formula
    -------
    distance = 0.5 * L1_branch + 0.5 * (1 - Jaccard_cg)

    where:
      L1_branch  = normalised L1 distance between branch probability profiles
                   (maximum possible L1 for two probability distributions = 2,
                    so divide by 2 to map to [0, 1]).

      Jaccard_cg = Jaccard similarity of call-graph edges treated as sets.
                   Jaccard(A, B) = |A ∩ B| / |A ∪ B|  (0.0 when both empty)

    Both components are in [0, 1] so the weighted sum is in [0, 1].

    Properties:
      • distance(g, g) == 0
      • distance(g1, g2) == distance(g2, g1)  (symmetric)
      • distance ∈ [0, 1]
    """
    l1 = _l1_branch_distance(g1.branch_probability_profile,
                              g2.branch_probability_profile)
    jacc = _jaccard_cg(g1.call_graph_edges, g2.call_graph_edges)
    # (1 - Jaccard) maps similarity to distance
    return 0.5 * l1 + 0.5 * (1.0 - jacc)


def _l1_branch_distance(p1: Dict[str, float], p2: Dict[str, float]) -> float:
    """
    Normalised L1 distance between two branch probability profiles.

    Both profiles are probability distributions (values sum to ≤ 1).
    The maximum L1 between two distributions is 2 (all mass on disjoint keys),
    so dividing by 2 gives a value in [0, 1].
    """
    all_keys = set(p1.keys()) | set(p2.keys())
    if not all_keys:
        return 0.0
    raw_l1 = sum(abs(p1.get(k, 0.0) - p2.get(k, 0.0)) for k in all_keys)
    # Maximum L1 for probability distributions = 2.0
    return min(1.0, raw_l1 / 2.0)


def _jaccard_cg(
    edges1: List[Tuple[str, str]], edges2: List[Tuple[str, str]]
) -> float:
    """
    Jaccard similarity of call-graph edge sets.

    Returns 1.0 when both sets are empty (identical empty graphs).
    Returns 0.0 when the sets are disjoint.
    """
    s1 = set(edges1)
    s2 = set(edges2)
    union_size = len(s1 | s2)
    if union_size == 0:
        return 1.0  # both empty → identical → similarity 1
    return len(s1 & s2) / union_size


# ---------------------------------------------------------------------------
# canonicalize
# ---------------------------------------------------------------------------

def canonicalize(g: ControlGenome) -> ControlGenome:
    """
    Return a canonical form of *g* that is stable and comparable.

    Operations:
      • Sort ``call_graph_edges`` lexicographically.
      • Sort keys of ``branch_probability_profile``; round values to 4 dp.
      • Round ``control_flow_entropy`` to 4 decimal places.
      • Trim trailing zeros from ``loop_nesting_profile``.

    This function is idempotent:
        canonicalize(canonicalize(g)) == canonicalize(g)

    The ``provenance`` dict is preserved unchanged.
    """
    # Branch probability profile: sorted keys, rounded values
    bpp = {
        k: round(v, 4)
        for k, v in sorted(g.branch_probability_profile.items())
    }

    # Call graph edges: sort list of tuples
    cg = sorted(g.call_graph_edges)

    # Loop nesting profile: remove trailing zeros for canonical form
    lnp = list(g.loop_nesting_profile)
    while lnp and lnp[-1] == 0:
        lnp.pop()

    entropy = round(g.control_flow_entropy, 4)

    return ControlGenome(
        branch_probability_profile=bpp,
        call_graph_edges=cg,
        loop_nesting_profile=lnp,
        cyclomatic_complexity=g.cyclomatic_complexity,
        control_flow_entropy=entropy,
        provenance=g.provenance,
    )


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _shannon_entropy(probabilities: List[float]) -> float:
    """
    Shannon entropy H = -Σ p·log2(p) in bits.

    Zero-probability entries are skipped (0·log(0) = 0 by convention).
    """
    h = 0.0
    for p in probabilities:
        if p > 0.0:
            h -= p * math.log2(p)
    return h
