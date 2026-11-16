"""
sbg.extraction.static.error_genome
=====================================
Error Genome extraction from Python source code (static AST analysis).

Formal grounding
----------------
* ErrorGenome     ↔  g_E              (Definition 14, FORMAL_MODEL.md)
* extract         ↔  Φ_E              (Definition 7)
* distance        ↔  d_E              (Definition 17)
* canonicalize    ↔  𝒩_dist / 𝒞_ε   (Definition 22b)

Constraints
-----------
* No third-party imports.
* No code is executed — all analysis is purely structural / AST-based.
"""

from __future__ import annotations

import ast
import math
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set


_TOOL_VERSION = "sbg-error-genome-0.1.0"
_PYTHON_VERSION = f"cpython-{sys.version_info.major}.{sys.version_info.minor}"


# ---------------------------------------------------------------------------
# ErrorGenome  (g_E — Definition 14)
# ---------------------------------------------------------------------------

@dataclass
class ErrorGenome:
    """
    Static ERROR-dimension genome — g_E per Definition 14.

    Fields
    ------
    exception_types_raised:
        Sorted list of unique exception type names in ``raise`` statements.
        Bare ``raise`` contributes "<re-raise>".
    exception_types_caught:
        Sorted list of unique exception type names in ``except`` handlers.
    bare_except_count:
        Number of ``except:`` clauses without an explicit type.
    try_block_count:
        Total number of ``try`` blocks.
    finally_block_count:
        Number of ``try`` blocks that include a ``finally`` clause.
    assertion_count:
        Number of ``assert`` statements (AVR proxy).
    error_propagation_pattern:
        Dominant error-handling strategy: "raise", "return_none",
        "return_sentinel", "mixed", or "none".
    error_coverage_score:
        Fraction of function definitions containing at least one try/except.
        Corresponds to CC (catch coverage) in Definition 14.
    provenance:
        Metadata dictionary.
    """

    exception_types_raised: List[str]
    exception_types_caught: List[str]
    bare_except_count: int
    try_block_count: int
    finally_block_count: int
    assertion_count: int
    error_propagation_pattern: str
    error_coverage_score: float
    provenance: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# _extract_exc_name
# ---------------------------------------------------------------------------

def _extract_exc_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Call):
        return _extract_exc_name(node.func)
    if isinstance(node, ast.Tuple):
        names = [_extract_exc_name(elt) for elt in node.elts]
        return ", ".join(n for n in names if n)
    return ""


# ---------------------------------------------------------------------------
# _ErrorVisitor
# ---------------------------------------------------------------------------

class _ErrorVisitor(ast.NodeVisitor):
    """Single-pass AST walker collecting all ErrorGenome features."""

    def __init__(self) -> None:
        self._raised: Set[str] = set()
        self._caught: Set[str] = set()
        self._bare_except: int = 0
        self._try_count: int = 0
        self._finally_count: int = 0
        self._assert_count: int = 0

        # propagation pattern signals
        self._has_raise: bool = False
        self._has_return_none: bool = False
        self._has_return_sentinel: bool = False

        # coverage tracking
        self._function_names: List[str] = []
        self._functions_with_try: Set[str] = set()
        self._current_func_stack: List[str] = []
        self._in_except_depth: int = 0

    # --- scope helpers ---

    def _push_func(self, name: str) -> None:
        qualified = "/".join(self._current_func_stack + [name])
        self._function_names.append(qualified)
        self._current_func_stack.append(qualified)

    def _pop_func(self) -> None:
        self._current_func_stack.pop()

    def _current_func(self) -> "str | None":
        return self._current_func_stack[-1] if self._current_func_stack else None

    def _mark_try_in_current_func(self) -> None:
        fn = self._current_func()
        if fn is not None:
            self._functions_with_try.add(fn)

    # --- visitors ---

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._push_func(node.name)
        self.generic_visit(node)
        self._pop_func()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._push_func(node.name)
        self.generic_visit(node)
        self._pop_func()

    def visit_Try(self, node: ast.Try) -> None:
        self._try_count += 1
        self._mark_try_in_current_func()
        if node.finalbody:
            self._finally_count += 1

        for child in node.body:
            self.visit(child)
        for handler in node.handlers:
            self._visit_handler(handler)
        for child in node.orelse:
            self.visit(child)
        for child in node.finalbody:
            self.visit(child)

    # Python 3.11+ except*
    if hasattr(ast, "TryStar"):
        def visit_TryStar(self, node: Any) -> None:  # type: ignore[override]
            self._try_count += 1
            self._mark_try_in_current_func()
            for child in node.body:
                self.visit(child)
            for handler in node.handlers:
                self._visit_handler(handler)
            for child in node.orelse:
                self.visit(child)
            for child in node.finalbody:
                self.visit(child)

    def _visit_handler(self, handler: ast.ExceptHandler) -> None:
        if handler.type is None:
            self._bare_except += 1
        else:
            name = _extract_exc_name(handler.type)
            if name:
                self._caught.add(name)
        self._in_except_depth += 1
        for child in handler.body:
            self.visit(child)
        self._in_except_depth -= 1

    def visit_Raise(self, node: ast.Raise) -> None:
        if node.exc is None:
            self._raised.add("<re-raise>")
        else:
            name = _extract_exc_name(node.exc)
            if name:
                self._raised.add(name)
        if self._in_except_depth > 0:
            self._has_raise = True
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        self._assert_count += 1
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        if self._in_except_depth > 0:
            if node.value is None:
                self._has_return_none = True
            elif isinstance(node.value, ast.Constant) and node.value.value is None:
                self._has_return_none = True
            else:
                self._has_return_sentinel = True
        self.generic_visit(node)

    # --- result accessors ---

    @property
    def exception_types_raised(self) -> List[str]:
        return sorted(self._raised)

    @property
    def exception_types_caught(self) -> List[str]:
        return sorted(self._caught)

    @property
    def error_propagation_pattern(self) -> str:
        n_active = sum([self._has_raise, self._has_return_none, self._has_return_sentinel])
        if n_active == 0:
            return "none"
        if n_active > 1:
            return "mixed"
        if self._has_raise:
            return "raise"
        if self._has_return_none:
            return "return_none"
        return "return_sentinel"

    @property
    def error_coverage_score(self) -> float:
        total = len(self._function_names)
        if total == 0:
            return 0.0
        return len(self._functions_with_try) / total


# ---------------------------------------------------------------------------
# ErrorGenomeExtractor
# ---------------------------------------------------------------------------

def _safe_parse(source_code: str) -> ast.Module:
    try:
        return ast.parse(source_code)
    except SyntaxError as exc:
        raise ValueError(f"Syntax error in source: {exc}") from exc


class ErrorGenomeExtractor:
    """
    Implements Φ_E: str (source code) → ErrorGenome.
    All extraction is by single-pass AST walk.  No code is executed.
    """

    def extract(self, source_code: str) -> ErrorGenome:
        tree = _safe_parse(source_code)
        v = _ErrorVisitor()
        v.visit(tree)

        provenance: Dict[str, Any] = {
            "tool_version": _TOOL_VERSION,
            "python_version": _PYTHON_VERSION,
            "extraction_timestamp": time.time(),
        }

        return ErrorGenome(
            exception_types_raised=v.exception_types_raised,
            exception_types_caught=v.exception_types_caught,
            bare_except_count=v._bare_except,
            try_block_count=v._try_count,
            finally_block_count=v._finally_count,
            assertion_count=v._assert_count,
            error_propagation_pattern=v.error_propagation_pattern,
            error_coverage_score=v.error_coverage_score,
            provenance=provenance,
        )


# ---------------------------------------------------------------------------
# distance  (Definition 17, row E)
# ---------------------------------------------------------------------------

def distance(g1: ErrorGenome, g2: ErrorGenome) -> float:
    """
    Pseudometric on ErrorGenome in [0, 1].

    d = 0.4 * jaccard(raised∪caught sets)
      + 0.3 * normalised_L1(count vector)
      + 0.3 * pattern_mismatch
    """
    # Jaccard on combined exception type sets
    set1 = set(g1.exception_types_raised) | set(g1.exception_types_caught)
    set2 = set(g2.exception_types_raised) | set(g2.exception_types_caught)
    union_size = len(set1 | set2)
    jaccard_dist = 0.0 if union_size == 0 else 1.0 - len(set1 & set2) / union_size

    # Normalised L1 on counts
    def _nd(a: float, b: float) -> float:
        return abs(a - b) / max(abs(a), abs(b), 1.0)

    count_dist = sum([
        _nd(float(g1.bare_except_count),   float(g2.bare_except_count)),
        _nd(float(g1.try_block_count),      float(g2.try_block_count)),
        _nd(float(g1.finally_block_count),  float(g2.finally_block_count)),
        _nd(float(g1.assertion_count),      float(g2.assertion_count)),
        _nd(float(len(g1.exception_types_raised)), float(len(g2.exception_types_raised))),
        _nd(float(len(g1.exception_types_caught)),  float(len(g2.exception_types_caught))),
    ]) / 6.0

    pattern_dist = 0.0 if g1.error_propagation_pattern == g2.error_propagation_pattern else 1.0

    return 0.4 * jaccard_dist + 0.3 * count_dist + 0.3 * pattern_dist


# ---------------------------------------------------------------------------
# canonicalize  (Definition 22b)
# ---------------------------------------------------------------------------

def canonicalize(g: ErrorGenome) -> ErrorGenome:
    """
    Return a canonical form of *g* (idempotent).

    * exception_types_raised / caught: sorted, deduplicated.
    * All counts clamped to ≥ 0.
    * error_coverage_score clamped to [0, 1].
    * provenance gains a ``canonicalized`` marker.
    """
    prov = dict(g.provenance)
    prov["canonicalized"] = True

    return ErrorGenome(
        exception_types_raised=sorted(set(g.exception_types_raised)),
        exception_types_caught=sorted(set(g.exception_types_caught)),
        bare_except_count=max(0, int(g.bare_except_count)),
        try_block_count=max(0, int(g.try_block_count)),
        finally_block_count=max(0, int(g.finally_block_count)),
        assertion_count=max(0, int(g.assertion_count)),
        error_propagation_pattern=g.error_propagation_pattern,
        error_coverage_score=max(0.0, min(1.0, float(g.error_coverage_score))),
        provenance=prov,
    )
