"""
sbg/extraction/static/data_genome.py
======================================
Static extraction of the DATA genome dimension g_D.

Formal grounding
----------------
* DataGenome  <->  g_D             (Definition 10, FORMAL_MODEL.md)
* distance    <->  d_D             (Definition 17, row D)
* canonicalize <->  N_dist         (Definition 22)

Design notes
------------
g_D is formally defined over execution traces (dynamic value flows), but
this module provides a **static approximation** extracted purely from AST:

  value_type_histogram        - Constant literal types used in the source
  constant_value_profile      - Normalised density of each scalar constant kind
  container_usage             - AST-level occurrences of list/dict/set/tuple
  arithmetic_op_histogram     - Counts of BinOp operators
  comparison_op_histogram     - Counts of Compare operators
  data_flow_complexity        - (# assignments) / (# total statements)

Uses only Python stdlib.  No code is executed.
"""

from __future__ import annotations

import ast
import hashlib
import math
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


_TOOL_VERSION = "sbg-data-genome-0.1.0"
_PYTHON_VERSION = "cpython-{}.{}".format(sys.version_info.major, sys.version_info.minor)

_ARITH_OPS = ("Add", "Sub", "Mul", "Div", "Mod", "FloorDiv", "Pow")
_CMP_OPS = ("Eq", "NotEq", "Lt", "LtE", "Gt", "GtE", "In", "NotIn")

_ARITH_OP_MAP = {
    "Add": "Add",
    "Sub": "Sub",
    "Mult": "Mul",
    "Div": "Div",
    "Mod": "Mod",
    "FloorDiv": "FloorDiv",
    "Pow": "Pow",
}

_CMP_OP_MAP = {
    "Eq": "Eq",
    "NotEq": "NotEq",
    "Lt": "Lt",
    "LtE": "LtE",
    "Gt": "Gt",
    "GtE": "GtE",
    "In": "In",
    "NotIn": "NotIn",
}


@dataclass
class DataGenome:
    """
    Static approximation of the DATA genome dimension g_D (Definition 10).

    Fields
    ------
    value_type_histogram : Dict[str, int]
        Count of constant literals by type (int, str, float, bool, None).

    constant_value_profile : Dict[str, float]
        Fraction of scalar constants of each kind, normalised to sum <= 1.
        Keys: int_count, str_count, float_count, bool_count.

    container_usage : Dict[str, int]
        AST-level count of list/dict/set/tuple literals plus comprehensions.

    arithmetic_op_histogram : Dict[str, int]
        Counts of BinOp operator types: Add, Sub, Mul, Div, Mod, FloorDiv, Pow.

    comparison_op_histogram : Dict[str, int]
        Counts of Compare operator types: Eq, NotEq, Lt, LtE, Gt, GtE, In, NotIn.

    data_flow_complexity : float
        Ratio of assignment statements to total statements, in [0, 1].

    provenance : Dict
        Source hash, tool version, Python runtime, extraction timestamp.
    """

    value_type_histogram: Dict[str, int] = field(default_factory=dict)
    constant_value_profile: Dict[str, float] = field(default_factory=dict)
    container_usage: Dict[str, int] = field(default_factory=dict)
    arithmetic_op_histogram: Dict[str, int] = field(default_factory=dict)
    comparison_op_histogram: Dict[str, int] = field(default_factory=dict)
    data_flow_complexity: float = 0.0
    provenance: Dict[str, Any] = field(default_factory=dict)


class _DataGenomeVisitor(ast.NodeVisitor):
    """Single-pass AST visitor collecting all DataGenome raw counts."""

    def __init__(self):
        self._int_count = 0
        self._str_count = 0
        self._float_count = 0
        self._bool_count = 0
        self._none_count = 0
        self._list_count = 0
        self._dict_count = 0
        self._set_count = 0
        self._tuple_count = 0
        self._arith = {op: 0 for op in _ARITH_OPS}
        self._cmp = {op: 0 for op in _CMP_OPS}
        self._total_stmts = 0
        self._assign_stmts = 0

    def visit_Constant(self, node):
        v = node.value
        if isinstance(v, bool):
            self._bool_count += 1
        elif isinstance(v, int):
            self._int_count += 1
        elif isinstance(v, float):
            self._float_count += 1
        elif isinstance(v, str):
            self._str_count += 1
        elif v is None:
            self._none_count += 1
        self.generic_visit(node)

    # Python < 3.8 compatibility
    def visit_Num(self, node):
        n = getattr(node, "n", None)
        if isinstance(n, bool):
            self._bool_count += 1
        elif isinstance(n, int):
            self._int_count += 1
        elif isinstance(n, float):
            self._float_count += 1
        self.generic_visit(node)

    def visit_Str(self, node):
        self._str_count += 1
        self.generic_visit(node)

    def visit_NameConstant(self, node):
        v = getattr(node, "value", None)
        if v is None:
            self._none_count += 1
        elif isinstance(v, bool):
            self._bool_count += 1
        self.generic_visit(node)

    def visit_List(self, node):
        self._list_count += 1
        self.generic_visit(node)

    def visit_Dict(self, node):
        self._dict_count += 1
        self.generic_visit(node)

    def visit_Set(self, node):
        self._set_count += 1
        self.generic_visit(node)

    def visit_Tuple(self, node):
        self._tuple_count += 1
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self._list_count += 1
        self.generic_visit(node)

    def visit_DictComp(self, node):
        self._dict_count += 1
        self.generic_visit(node)

    def visit_SetComp(self, node):
        self._set_count += 1
        self.generic_visit(node)

    def visit_BinOp(self, node):
        op_name = type(node.op).__name__
        canonical = _ARITH_OP_MAP.get(op_name)
        if canonical is not None:
            self._arith[canonical] = self._arith.get(canonical, 0) + 1
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        op_name = type(node.op).__name__
        canonical = _ARITH_OP_MAP.get(op_name)
        if canonical is not None:
            self._arith[canonical] = self._arith.get(canonical, 0) + 1
        self._total_stmts += 1
        self._assign_stmts += 1
        self.generic_visit(node)

    def visit_Compare(self, node):
        for op in node.ops:
            op_name = type(op).__name__
            canonical = _CMP_OP_MAP.get(op_name)
            if canonical is not None:
                self._cmp[canonical] = self._cmp.get(canonical, 0) + 1
        self.generic_visit(node)

    def visit_Assign(self, node):
        self._total_stmts += 1
        self._assign_stmts += 1
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        self._total_stmts += 1
        if node.value is not None:
            self._assign_stmts += 1
        self.generic_visit(node)

    def _count_stmt(self, node):
        self._total_stmts += 1
        self.generic_visit(node)

    visit_Expr = _count_stmt
    visit_Return = _count_stmt
    visit_Delete = _count_stmt
    visit_Pass = _count_stmt
    visit_Break = _count_stmt
    visit_Continue = _count_stmt
    visit_Raise = _count_stmt
    visit_Assert = _count_stmt
    visit_Import = _count_stmt
    visit_ImportFrom = _count_stmt
    visit_If = _count_stmt
    visit_For = _count_stmt
    visit_While = _count_stmt
    visit_With = _count_stmt
    visit_Try = _count_stmt
    visit_FunctionDef = _count_stmt
    visit_AsyncFunctionDef = _count_stmt
    visit_ClassDef = _count_stmt
    visit_Global = _count_stmt
    visit_Nonlocal = _count_stmt


class DataGenomeExtractor:
    """
    Extracts the DATA genome dimension (g_D) from Python source code.

    All analysis is static (AST-only).  No code is executed.
    """

    def extract(self, source_code):
        # type: (str) -> DataGenome
        """Parse source_code and return a DataGenome."""
        try:
            tree = ast.parse(source_code)
        except SyntaxError as exc:
            raise ValueError("Syntax error in source: {}".format(exc)) from exc

        v = _DataGenomeVisitor()
        v.visit(tree)

        vth = {
            "int": v._int_count,
            "str": v._str_count,
            "float": v._float_count,
            "bool": v._bool_count,
            "None": v._none_count,
        }

        scalar_total = v._int_count + v._str_count + v._float_count + v._bool_count
        if scalar_total > 0:
            cvp = {
                "int_count": v._int_count / scalar_total,
                "str_count": v._str_count / scalar_total,
                "float_count": v._float_count / scalar_total,
                "bool_count": v._bool_count / scalar_total,
            }
        else:
            cvp = {
                "int_count": 0.0,
                "str_count": 0.0,
                "float_count": 0.0,
                "bool_count": 0.0,
            }

        container_usage = {
            "list": v._list_count,
            "dict": v._dict_count,
            "set": v._set_count,
            "tuple": v._tuple_count,
        }

        arith = dict(v._arith)
        cmp_hist = dict(v._cmp)

        dfc = (v._assign_stmts / v._total_stmts) if v._total_stmts > 0 else 0.0

        src_hash = hashlib.sha256(source_code.encode()).hexdigest()[:16]
        provenance = {
            "source_hash": src_hash,
            "tool": _TOOL_VERSION,
            "python_runtime": _PYTHON_VERSION,
            "analysis": "static_ast",
            "extraction_timestamp": time.time(),
        }

        return DataGenome(
            value_type_histogram=vth,
            constant_value_profile=cvp,
            container_usage=container_usage,
            arithmetic_op_histogram=arith,
            comparison_op_histogram=cmp_hist,
            data_flow_complexity=dfc,
            provenance=provenance,
        )


def _to_distribution(counts):
    total = sum(counts.values())
    if total == 0:
        return {k: 0.0 for k in counts}
    return {k: v / total for k, v in counts.items()}


def _js_divergence_dicts(a, b):
    """Jensen-Shannon divergence between two integer-count histograms, in [0, 1]."""
    all_keys = set(a) | set(b)
    if not all_keys:
        return 0.0

    a_counts = {k: a.get(k, 0) for k in all_keys}
    b_counts = {k: b.get(k, 0) for k in all_keys}

    total_a = sum(a_counts.values())
    total_b = sum(b_counts.values())

    if total_a == 0 and total_b == 0:
        return 0.0

    n = len(all_keys)
    p = {k: (a_counts[k] / total_a) if total_a > 0 else 1.0 / n for k in all_keys}
    q = {k: (b_counts[k] / total_b) if total_b > 0 else 1.0 / n for k in all_keys}
    m = {k: (p[k] + q[k]) / 2.0 for k in all_keys}

    def _kl(dist_p, dist_m):
        total = 0.0
        for k in all_keys:
            pk = dist_p[k]
            mk = dist_m[k]
            if pk > 0.0 and mk > 0.0:
                total += pk * math.log2(pk / mk)
        return total

    jsd = (_kl(p, m) + _kl(q, m)) / 2.0
    return math.sqrt(max(0.0, min(1.0, jsd)))


def _l1_normalised(p1, p2):
    """Normalised L1 distance between two float-valued dicts, in [0, 1]."""
    all_keys = set(p1) | set(p2)
    if not all_keys:
        return 0.0
    raw_l1 = sum(abs(p1.get(k, 0.0) - p2.get(k, 0.0)) for k in all_keys)
    return min(1.0, raw_l1 / 2.0)


def distance(g1, g2):
    # type: (DataGenome, DataGenome) -> float
    """
    Symmetric distance in [0, 1] between two DataGenomes.

    Six components averaged equally:
      1. JS divergence on value_type_histogram
      2. L1 distance on constant_value_profile
      3. JS divergence on arithmetic_op_histogram
      4. JS divergence on comparison_op_histogram
      5. JS divergence on container_usage
      6. |data_flow_complexity1 - data_flow_complexity2|

    Properties: distance(g, g) == 0, symmetric, in [0, 1].
    """
    d_vth = _js_divergence_dicts(g1.value_type_histogram, g2.value_type_histogram)
    d_cvp = _l1_normalised(g1.constant_value_profile, g2.constant_value_profile)
    d_arith = _js_divergence_dicts(g1.arithmetic_op_histogram, g2.arithmetic_op_histogram)
    d_cmp = _js_divergence_dicts(g1.comparison_op_histogram, g2.comparison_op_histogram)
    d_cont = _js_divergence_dicts(g1.container_usage, g2.container_usage)
    d_dfc = abs(g1.data_flow_complexity - g2.data_flow_complexity)
    return (d_vth + d_cvp + d_arith + d_cmp + d_cont + d_dfc) / 6.0


def canonicalize(g):
    # type: (DataGenome) -> DataGenome
    """
    Return a canonical form of g per Definition 22.

    - All dict keys sorted lexicographically.
    - All float values rounded to 4 decimal places.
    - data_flow_complexity rounded to 4 dp and clamped to [0, 1].
    - Provenance gains a 'canonicalized' marker.

    Idempotent: canonicalize(canonicalize(g)) == canonicalize(g).
    """
    def _sort_round_int(d):
        return {k: max(0, int(d[k])) for k in sorted(d)}

    def _sort_round_float(d):
        return {k: round(float(d[k]), 4) for k in sorted(d)}

    prov = dict(g.provenance)
    prov["canonicalized"] = True

    return DataGenome(
        value_type_histogram=_sort_round_int(g.value_type_histogram),
        constant_value_profile=_sort_round_float(g.constant_value_profile),
        container_usage=_sort_round_int(g.container_usage),
        arithmetic_op_histogram=_sort_round_int(g.arithmetic_op_histogram),
        comparison_op_histogram=_sort_round_int(g.comparison_op_histogram),
        data_flow_complexity=round(max(0.0, min(1.0, g.data_flow_complexity)), 4),
        provenance=prov,
    )
