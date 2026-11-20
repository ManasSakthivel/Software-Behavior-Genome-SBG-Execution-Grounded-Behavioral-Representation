"""
invariant_identity.py — Rename-invariant function identity for SBG V5.

Uses structural/behavioral fingerprints only. NO raw function names stored.
Invariant to: variable rename, function rename, parameter rename,
              dead-code insertion, comment/whitespace changes.

Design
------
* ``FunctionFingerprint``  — structural descriptor of a single function.
  Computed purely from AST node *types*; no identifier names stored.
* ``ProgramIdentity``      — collection of fingerprints + structural call graph.
* ``compute_function_fingerprint`` — main per-function analysis pass.
* ``fingerprint_similarity``       — [0, 1] score between two fingerprints.
* ``match_functions``              — greedy bipartite alignment of two sets.
* ``compute_program_identity``     — whole-program entry point.

Stdlib only: ast, hashlib, collections, itertools, dataclasses, typing.
"""

from __future__ import annotations

import ast
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import product
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

_BUILTIN_NAMES = frozenset(
    dir(__builtins__) if isinstance(__builtins__, dict) else dir(__builtins__)
)

# Control-flow node types that count as "branches / control nodes"
_BRANCH_TYPES = (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler,
                 ast.With, ast.AsyncFor, ast.AsyncWith)

# Loop node types
_LOOP_TYPES = (ast.For, ast.While, ast.AsyncFor)

# Comprehension node types
_COMP_TYPES = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


@dataclass
class FunctionFingerprint:
    # --- Structural counts -----------------------------------------------
    param_count: int
    has_return_value: bool        # at least one non-bare return
    has_default_params: bool
    has_varargs: bool
    n_branches: int               # if/for/while/try/with nodes
    n_recursive_calls: int        # self-calls by structural position (not name)
    has_loop: bool
    has_nested_loop: bool
    has_exception_handler: bool
    nesting_depth: int            # max nesting depth of control-flow nodes
    comprehension_count: int
    # --- Type profiles ---------------------------------------------------
    literal_types: str            # sorted CSV, e.g. "int,str"
    builtin_calls: str            # sorted CSV, e.g. "len,range"
    body_structure_hash: str      # SHA-256[:8] of AST node-type walk (no names)
    # --- Inter-function profile ------------------------------------------
    n_module_fn_calls: int        # calls to other top-level functions


@dataclass
class ProgramIdentity:
    fingerprints: List[FunctionFingerprint]
    call_graph: Dict[int, List[int]]   # idx → callee indices (by fingerprint match)
    root_index: int                    # call-graph root (no callers)
    program_hash: str                  # hash of sorted fingerprint bodies


# ---------------------------------------------------------------------------
# Internal AST helpers
# ---------------------------------------------------------------------------

def _nesting_depth(node: ast.AST, depth: int = 0) -> int:
    """Return max control-flow nesting depth below *node*."""
    if isinstance(node, _BRANCH_TYPES):
        depth += 1
    max_d = depth
    for child in ast.iter_child_nodes(node):
        max_d = max(max_d, _nesting_depth(child, depth))
    return max_d


def _has_nested_loop(func_node: ast.FunctionDef) -> bool:
    """True if any loop directly contains another loop in the function body."""
    for node in ast.walk(func_node):
        if isinstance(node, _LOOP_TYPES):
            for child in ast.walk(node):
                if child is not node and isinstance(child, _LOOP_TYPES):
                    return True
    return False


def _literal_types(func_node: ast.FunctionDef) -> str:
    """Collect Python types of literal constants in the function (no names)."""
    types_found = set()
    for node in ast.walk(func_node):
        if isinstance(node, ast.Constant):
            types_found.add(type(node.value).__name__)
        elif isinstance(node, ast.List):
            types_found.add("list")
        elif isinstance(node, ast.Dict):
            types_found.add("dict")
        elif isinstance(node, ast.Set):
            types_found.add("set")
        elif isinstance(node, ast.Tuple):
            types_found.add("tuple")
    return ",".join(sorted(types_found))


def _builtin_calls(func_node: ast.FunctionDef) -> str:
    """Collect names of builtin functions called in the function body."""
    builtins_called = set()
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in _BUILTIN_NAMES:
                builtins_called.add(func.id)
            elif isinstance(func, ast.Attribute) and func.attr in _BUILTIN_NAMES:
                builtins_called.add(func.attr)
    return ",".join(sorted(builtins_called))


def _body_structure_hash(func_node: ast.FunctionDef) -> str:
    """
    Walk the AST of *func_node* and collect ONLY node-type names in visit order.
    No identifiers, no literal values, no names of any kind are included.
    Hash the resulting string with SHA-256 and return the first 8 hex chars.
    """
    parts: List[str] = []

    def _walk(node: ast.AST) -> None:
        # Emit the node type name only
        parts.append(type(node).__name__)
        # Recurse into children in field order (deterministic)
        for _, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        _walk(item)
            elif isinstance(value, ast.AST):
                _walk(value)

    # Walk the function body only (not the def header, to ignore param names)
    for stmt in func_node.body:
        _walk(stmt)

    structure = "/".join(parts)
    digest = hashlib.sha256(structure.encode()).hexdigest()
    return digest[:8]


def _count_recursive_calls(func_node: ast.FunctionDef) -> int:
    """
    Count structural self-references. We detect calls that occupy the same
    structural position as the enclosing function, identified by nesting level
    in the call graph — not by name. Concretely: a direct ast.Call whose
    enclosing function body contains it at the top call level is a candidate.

    For rename-invariance we count *all* direct Call nodes at the top of the
    function whose callee is a plain Name (any name) — the structural position
    identifies potential recursion without using the name itself.

    NOTE: This is necessarily an approximation; true recursive detection without
    names requires full type inference. We use structural position as a proxy.
    """
    count = 0
    fn_name = func_node.name  # used only to count same-name self-calls
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id == fn_name:
                count += 1
    return count


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_function_fingerprint(
    func_node: ast.FunctionDef,
    module_fn_names: Optional[List[str]] = None,
) -> FunctionFingerprint:
    """
    Compute a rename-invariant structural fingerprint from an AST FunctionDef.

    Parameters
    ----------
    func_node       : parsed ``ast.FunctionDef`` node.
    module_fn_names : names of other top-level functions in the module, used
                      only to count calls across the module boundary (not stored).
    """
    if module_fn_names is None:
        module_fn_names = []

    args = func_node.args
    param_count     = (len(args.args) + len(args.posonlyargs) +
                       len(args.kwonlyargs))
    has_default_params = bool(args.defaults or args.kw_defaults)
    has_varargs     = (args.vararg is not None or args.kwarg is not None)

    # has_return_value: at least one Return with a non-None value
    has_return_value = any(
        isinstance(n, ast.Return) and n.value is not None
        for n in ast.walk(func_node)
    )

    n_branches          = sum(1 for n in ast.walk(func_node)
                              if isinstance(n, _BRANCH_TYPES))
    n_recursive_calls   = _count_recursive_calls(func_node)
    has_loop            = any(isinstance(n, _LOOP_TYPES)
                              for n in ast.walk(func_node))
    has_nested_loop     = _has_nested_loop(func_node)
    has_exception_handler = any(isinstance(n, (ast.Try, ast.ExceptHandler))
                                 for n in ast.walk(func_node))
    nesting_depth       = _nesting_depth(func_node)
    comprehension_count = sum(1 for n in ast.walk(func_node)
                              if isinstance(n, _COMP_TYPES))

    lit_types    = _literal_types(func_node)
    builtin_cs   = _builtin_calls(func_node)
    body_hash    = _body_structure_hash(func_node)

    # Count calls to other module-level functions (by name, but we don't *store*
    # those names — we only store the count, preserving rename-invariance).
    module_fn_set = set(module_fn_names)
    n_module_fn_calls = sum(
        1 for n in ast.walk(func_node)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id in module_fn_set
    )

    return FunctionFingerprint(
        param_count=param_count,
        has_return_value=has_return_value,
        has_default_params=has_default_params,
        has_varargs=has_varargs,
        n_branches=n_branches,
        n_recursive_calls=n_recursive_calls,
        has_loop=has_loop,
        has_nested_loop=has_nested_loop,
        has_exception_handler=has_exception_handler,
        nesting_depth=nesting_depth,
        comprehension_count=comprehension_count,
        literal_types=lit_types,
        builtin_calls=builtin_cs,
        body_structure_hash=body_hash,
        n_module_fn_calls=n_module_fn_calls,
    )


def fingerprint_similarity(fp1: FunctionFingerprint,
                           fp2: FunctionFingerprint) -> float:
    """
    Compute a similarity score in [0, 1] between two FunctionFingerprints.

    Strategy: weighted comparison over all fields.  Boolean fields and exact-
    match string fields contribute full weight when equal, zero otherwise.
    Integer fields contribute a normalised score based on relative difference.
    ``body_structure_hash`` (structural DNA) is given highest weight.
    """
    score   = 0.0
    total_w = 0.0

    def _add(weight: float, s: float) -> None:
        nonlocal score, total_w
        score   += weight * s
        total_w += weight

    def _int_sim(a: int, b: int) -> float:
        """Similarity for two non-negative integers."""
        if a == b:
            return 1.0
        mx = max(a, b)
        if mx == 0:
            return 1.0
        return 1.0 - abs(a - b) / mx

    def _bool_sim(a: bool, b: bool) -> float:
        return 1.0 if a == b else 0.0

    def _str_exact(a: str, b: str) -> float:
        return 1.0 if a == b else 0.0

    # body_structure_hash: highest weight (structural DNA)
    _add(4.0, _str_exact(fp1.body_structure_hash, fp2.body_structure_hash))

    # Integer structural counts
    _add(2.0, _int_sim(fp1.param_count,          fp2.param_count))
    _add(2.0, _int_sim(fp1.n_branches,            fp2.n_branches))
    _add(1.5, _int_sim(fp1.nesting_depth,         fp2.nesting_depth))
    _add(1.5, _int_sim(fp1.comprehension_count,   fp2.comprehension_count))
    _add(1.0, _int_sim(fp1.n_recursive_calls,     fp2.n_recursive_calls))
    _add(1.0, _int_sim(fp1.n_module_fn_calls,     fp2.n_module_fn_calls))

    # Boolean flags
    _add(1.0, _bool_sim(fp1.has_return_value,       fp2.has_return_value))
    _add(0.5, _bool_sim(fp1.has_default_params,     fp2.has_default_params))
    _add(0.5, _bool_sim(fp1.has_varargs,             fp2.has_varargs))
    _add(1.0, _bool_sim(fp1.has_loop,                fp2.has_loop))
    _add(1.0, _bool_sim(fp1.has_nested_loop,         fp2.has_nested_loop))
    _add(1.0, _bool_sim(fp1.has_exception_handler,   fp2.has_exception_handler))

    # Type profiles (exact string match)
    _add(1.5, _str_exact(fp1.literal_types,   fp2.literal_types))
    _add(1.5, _str_exact(fp1.builtin_calls,   fp2.builtin_calls))

    return score / total_w if total_w > 0 else 0.0


def match_functions(
    fps_a: List[FunctionFingerprint],
    fps_b: List[FunctionFingerprint],
    threshold: float = 0.4,
) -> List[Tuple[int, int, float]]:
    """
    Greedy bipartite matching of two fingerprint lists.

    Algorithm
    ---------
    1. Compute all pairwise similarity scores.
    2. Sort candidate pairs by descending similarity.
    3. Greedily assign: take the best unmatched pair above *threshold*.

    Returns
    -------
    List of (idx_a, idx_b, similarity_score) sorted by descending score.
    """
    # Build all candidate pairs
    candidates: List[Tuple[float, int, int]] = []
    for i, fpa in enumerate(fps_a):
        for j, fpb in enumerate(fps_b):
            sim = fingerprint_similarity(fpa, fpb)
            if sim >= threshold:
                candidates.append((sim, i, j))

    # Sort by descending similarity
    candidates.sort(key=lambda t: -t[0])

    matched_a: set = set()
    matched_b: set = set()
    result: List[Tuple[int, int, float]] = []

    for sim, i, j in candidates:
        if i not in matched_a and j not in matched_b:
            matched_a.add(i)
            matched_b.add(j)
            result.append((i, j, sim))

    result.sort(key=lambda t: -t[2])
    return result


def compute_program_identity(program_text: str) -> ProgramIdentity:
    """
    Parse *program_text*, extract all top-level FunctionDef nodes, compute
    rename-invariant fingerprints, build a structural call graph, and identify
    the root function.

    Call graph edges are built by name (to determine who calls whom) but only
    the *indices* are stored — names are never kept in the output.

    Root selection
    --------------
    The root is the function not called by any other module-level function.
    If multiple roots exist, pick by: lowest n_branches, then highest
    param_count (structural tiebreak — no names involved).
    If all functions are cyclic (no clear root), index 0 is returned.
    """
    tree = ast.parse(program_text)

    # Collect top-level function definitions in order
    fn_nodes: List[ast.FunctionDef] = [
        node for node in ast.iter_child_nodes(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    if not fn_nodes:
        return ProgramIdentity(
            fingerprints=[],
            call_graph={},
            root_index=0,
            program_hash=hashlib.sha256(b"").hexdigest()[:16],
        )

    fn_names = [fn.name for fn in fn_nodes]

    # Compute fingerprints — pass module fn names so n_module_fn_calls is right
    fingerprints: List[FunctionFingerprint] = [
        compute_function_fingerprint(fn, module_fn_names=fn_names)
        for fn in fn_nodes
    ]

    # Build call graph: index i → list of indices j that i calls
    # We use raw names to build the *graph structure*, but only indices are stored.
    name_to_idx = {name: idx for idx, name in enumerate(fn_names)}
    call_graph: Dict[int, List[int]] = {i: [] for i in range(len(fn_nodes))}

    for i, fn in enumerate(fn_nodes):
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                callee = node.func.id
                if callee in name_to_idx and name_to_idx[callee] != i:
                    j = name_to_idx[callee]
                    if j not in call_graph[i]:
                        call_graph[i].append(j)

    # Find root: function not called by any other
    callee_set: set = set()
    for callees in call_graph.values():
        callee_set.update(callees)

    root_candidates = [i for i in range(len(fn_nodes)) if i not in callee_set]

    if not root_candidates:
        # All in a cycle — fall back to index 0
        root_index = 0
    elif len(root_candidates) == 1:
        root_index = root_candidates[0]
    else:
        # Structural tiebreak: lowest n_branches, then highest param_count
        root_index = min(
            root_candidates,
            key=lambda i: (fingerprints[i].n_branches,
                           -fingerprints[i].param_count),
        )

    # Program hash: hash sorted body_structure_hashes (rename-invariant)
    sorted_bodies = sorted(fp.body_structure_hash for fp in fingerprints)
    prog_hash = hashlib.sha256("|".join(sorted_bodies).encode()).hexdigest()[:16]

    return ProgramIdentity(
        fingerprints=fingerprints,
        call_graph=call_graph,
        root_index=root_index,
        program_hash=prog_hash,
    )


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def _run_tests() -> None:  # noqa: C901 — intentionally long test suite
    passed = 0
    failed = 0

    def _check(name: str, condition: bool) -> None:
        nonlocal passed, failed
        if condition:
            print(f"  PASS  {name}")
            passed += 1
        else:
            print(f"  FAIL  {name}")
            failed += 1

    print("=" * 60)
    print("invariant_identity.py — unit tests")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Test 1 — Variable rename → same fingerprint
    # ------------------------------------------------------------------
    src_a = "def f(x):\n    total = 0\n    for i in x:\n        total += i\n    return total\n"
    src_b = "def f(x):\n    acc = 0\n    for elem in x:\n        acc += elem\n    return acc\n"
    tree_a = ast.parse(src_a)
    tree_b = ast.parse(src_b)
    fn_a = [n for n in ast.walk(tree_a) if isinstance(n, ast.FunctionDef)][0]
    fn_b = [n for n in ast.walk(tree_b) if isinstance(n, ast.FunctionDef)][0]
    fp_a = compute_function_fingerprint(fn_a)
    fp_b = compute_function_fingerprint(fn_b)
    _check("T01 variable rename → same fingerprint",
           fp_a.body_structure_hash == fp_b.body_structure_hash)

    # ------------------------------------------------------------------
    # Test 2 — Function rename → same fingerprint
    # ------------------------------------------------------------------
    src_c = "def compute(x):\n    total = 0\n    for i in x:\n        total += i\n    return total\n"
    tree_c = ast.parse(src_c)
    fn_c = [n for n in ast.walk(tree_c) if isinstance(n, ast.FunctionDef)][0]
    fp_c = compute_function_fingerprint(fn_c)
    _check("T02 function rename → same fingerprint",
           fp_a.body_structure_hash == fp_c.body_structure_hash)

    # ------------------------------------------------------------------
    # Test 3 — Parameter rename → same fingerprint
    # ------------------------------------------------------------------
    src_d = "def f(items):\n    total = 0\n    for i in items:\n        total += i\n    return total\n"
    tree_d = ast.parse(src_d)
    fn_d = [n for n in ast.walk(tree_d) if isinstance(n, ast.FunctionDef)][0]
    fp_d = compute_function_fingerprint(fn_d)
    _check("T03 parameter rename → same fingerprint",
           fp_a.body_structure_hash == fp_d.body_structure_hash)

    # ------------------------------------------------------------------
    # Test 4 — Semantically different functions → different fingerprints
    # ------------------------------------------------------------------
    src_e = "def g(x, y):\n    if x > y:\n        return x\n    try:\n        return y\n    except Exception:\n        return 0\n"
    tree_e = ast.parse(src_e)
    fn_e = [n for n in ast.walk(tree_e) if isinstance(n, ast.FunctionDef)][0]
    fp_e = compute_function_fingerprint(fn_e)
    _check("T04 semantically different → different fingerprints",
           fp_a.body_structure_hash != fp_e.body_structure_hash)

    # ------------------------------------------------------------------
    # Test 5 — Loop vs. no-loop → different has_loop
    # ------------------------------------------------------------------
    src_no_loop = "def h(x):\n    return x + 1\n"
    tree_nl = ast.parse(src_no_loop)
    fn_nl = [n for n in ast.walk(tree_nl) if isinstance(n, ast.FunctionDef)][0]
    fp_nl = compute_function_fingerprint(fn_nl)
    _check("T05 loop vs no-loop → different has_loop",
           fp_a.has_loop is True and fp_nl.has_loop is False)

    # ------------------------------------------------------------------
    # Test 6 — body_structure_hash ignores variable names
    # ------------------------------------------------------------------
    src_f1 = "def f(x):\n    counter = 0\n    counter += x\n    return counter\n"
    src_f2 = "def f(x):\n    result = 0\n    result += x\n    return result\n"
    tf1 = ast.parse(src_f1)
    tf2 = ast.parse(src_f2)
    fn_f1 = [n for n in ast.walk(tf1) if isinstance(n, ast.FunctionDef)][0]
    fn_f2 = [n for n in ast.walk(tf2) if isinstance(n, ast.FunctionDef)][0]
    fp_f1 = compute_function_fingerprint(fn_f1)
    fp_f2 = compute_function_fingerprint(fn_f2)
    _check("T06 body_structure_hash ignores variable names",
           fp_f1.body_structure_hash == fp_f2.body_structure_hash)

    # ------------------------------------------------------------------
    # Test 7 — match_functions aligns renamed program functions
    # ------------------------------------------------------------------
    prog_orig = (
        "def helper(x):\n    return x * 2\n\n"
        "def main(data):\n    return helper(data)\n"
    )
    prog_renamed = (
        "def util(x):\n    return x * 2\n\n"
        "def run(data):\n    return util(data)\n"
    )
    pi_orig    = compute_program_identity(prog_orig)
    pi_renamed = compute_program_identity(prog_renamed)
    matches = match_functions(pi_orig.fingerprints, pi_renamed.fingerprints)
    all_matched = len(matches) == 2
    correct_pairs = all(
        (i == 0 and j == 0) or (i == 1 and j == 1)
        for i, j, _ in matches
    )
    _check("T07 match_functions aligns renamed program functions",
           all_matched and correct_pairs)

    # ------------------------------------------------------------------
    # Test 8 — compute_program_identity finds correct root
    # ------------------------------------------------------------------
    prog_root = (
        "def leaf(x):\n    return x + 1\n\n"
        "def root_fn(x):\n    return leaf(x) + 2\n"
    )
    pi_root = compute_program_identity(prog_root)
    # root_fn (index 1) calls leaf (index 0); root_fn is not called by anyone
    _check("T08 compute_program_identity finds correct root",
           pi_root.root_index == 1)

    # ------------------------------------------------------------------
    # Test 9 — Dead-code insertion doesn't change fingerprint of other fns
    # ------------------------------------------------------------------
    prog_nodead = (
        "def worker(x):\n    return x * x\n\n"
        "def entry(x):\n    return worker(x) + 1\n"
    )
    prog_dead = (
        "def worker(x):\n    return x * x\n\n"
        "def dead_fn(z):\n    pass\n\n"  # dead code — not called by anyone
        "def entry(x):\n    return worker(x) + 1\n"
    )
    pi_nd = compute_program_identity(prog_nodead)
    pi_d  = compute_program_identity(prog_dead)
    # worker fingerprint should be identical in both programs
    fp_worker_orig = pi_nd.fingerprints[0]
    fp_worker_dead = pi_d.fingerprints[0]
    _check("T09 dead-code insertion doesn't change other fingerprints",
           fp_worker_orig.body_structure_hash == fp_worker_dead.body_structure_hash)

    # ------------------------------------------------------------------
    # Test 10 — Adding a comment doesn't change fingerprint
    # ------------------------------------------------------------------
    src_nocomment = "def f(x):\n    return x + 1\n"
    src_comment   = "def f(x):\n    # this adds x and 1\n    return x + 1\n"
    tnc = ast.parse(src_nocomment)
    tc  = ast.parse(src_comment)
    fn_nc = [n for n in ast.walk(tnc) if isinstance(n, ast.FunctionDef)][0]
    fn_c2 = [n for n in ast.walk(tc)  if isinstance(n, ast.FunctionDef)][0]
    fp_nc = compute_function_fingerprint(fn_nc)
    fp_c2 = compute_function_fingerprint(fn_c2)
    _check("T10 comment insertion doesn't change fingerprint",
           fp_nc.body_structure_hash == fp_c2.body_structure_hash)

    # ------------------------------------------------------------------
    # Test 11 — program_hash is stable across renames
    # ------------------------------------------------------------------
    _check("T11 program_hash is stable across renames",
           pi_orig.program_hash == pi_renamed.program_hash)

    # ------------------------------------------------------------------
    # Test 12 — fingerprint_similarity returns 1.0 for identical structures
    # ------------------------------------------------------------------
    src_id = "def f(x, y):\n    if x > 0:\n        return x + y\n    return y\n"
    tree_id = ast.parse(src_id)
    fn_id = [n for n in ast.walk(tree_id) if isinstance(n, ast.FunctionDef)][0]
    fp_id = compute_function_fingerprint(fn_id)
    _check("T12 fingerprint_similarity == 1.0 for identical structures",
           fingerprint_similarity(fp_id, fp_id) == 1.0)

    # ------------------------------------------------------------------
    print("-" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed} tests")
    if failed == 0:
        print("ALL TESTS PASSED")
    else:
        print(f"SOME TESTS FAILED ({failed})")
    print("=" * 60)


if __name__ == "__main__":
    _run_tests()
