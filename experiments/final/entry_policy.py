"""
experiments/final/entry_policy.py
=================================
Structural, rename-invariant entry-point selection (PROTOCOL ``output_free_v8``).

Why this module exists
----------------------
``protocol.select_entry_output_free`` (v6/v7) decides *which function to trace*
from function **names**: a ``test_*`` / ``_private`` / ``main`` / ``demo*``
exclusion list, a 23-name priority list, and "alphabetically first". The
benchmark's SP-2 transformation renames functions (mostly by prefixing ``fn_``),
and every one of those decisions then changes:

  * ``test_heapsort``  -> ``fn_test_heapsort``   no longer matches ``test_*``,
    so the *self-test driver* (with its ``assert`` statements) is selected;
  * ``_sift_down``     -> ``fn__sift_down``       no longer private, so it is
    selected as an entry instead of ``heapsort``;
  * ``parse_int``      -> ``decode_int``         alphabetical order changes;
  * ``evaluate``       -> ``fn_evaluate``         the priority-name hit is lost.

On the committed v6 test artifact, 11 EQUIVALENT pairs trace a different
function in the variant than in the base, and 2 of them trace a renamed
self-test driver. Excluding those 11 pairs moves SBG V5 AUROC on the 259-pair
subset from 0.6013 to 0.6410 (``reports/remediation/results``), so the
protocol's instability is large enough to change the headline.

Policy
------
Nothing below reads an identifier's spelling. Every rule is a property of the
AST that a semantics-preserving rename cannot change.

1. **Self-test drivers are excluded structurally.** A top-level function with no
   required parameters that either contains an ``assert`` statement or is
   called from the ``if __name__ == "__main__":`` block is scaffolding.
2. **Helpers are excluded structurally.** A function referenced by another
   non-driver function is a helper. The remaining *roots* of the module-level
   call graph are the entry candidates. (Calls made by drivers do not count:
   a driver calls everything, which is exactly why the old call-graph-root
   rule selected drivers.)
3. **Synthesisability.** Candidates whose parameters cannot all be supplied
   from the fixed batteries (``protocol.annotation_family``) are discarded.
4. **Deterministic tie-break ladder**, each key a structural property:
   (a) larger transitive call closure, (b) fully annotated, (c) larger
   required arity.
5. **Ambiguity is an error.** If candidates are still tied after (c) and their
   name-free structural fingerprints differ, no defensible choice exists and
   :class:`AmbiguousEntryPoint` is raised. Identical fingerprints (exact
   duplicates) are interchangeable and the first in source order is used.

Limitations (see ``docs/current/ENTRY_POINT_POLICY.md``)
--------------------------------------------------------
* Transformations that change the call graph can legitimately change the
  answer: SP-7 (inline) may delete the function that was the entry, SP-8
  (extract) adds helpers. :func:`interfaces_correspond` lets an evaluation
  *detect* such pairs and exclude them by a pre-declared rule instead of
  scoring two different functions as if they were one program.
* ``interfaces_correspond`` is a necessary condition for "same entry", not a
  sufficient one.
* The class tier (``class_driver.py``) still orders classes and methods
  alphabetically and is **not** rename-invariant; see the test marked ``xfail``.
* A zero-parameter function called from the main guard is treated as a driver
  even if it is a genuine API; none exists in the committed corpus.
"""
from __future__ import annotations

import ast
import copy
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from experiments.final.protocol import _function_signature, synthesise_inputs

POLICY_ID = "v8:structural"


class EntryPointError(Exception):
    """The protocol cannot establish an entry point. ``kind`` is a ledger bucket."""
    kind = "no_entry_function"

    def __init__(self, message: str, candidates: Optional[List[str]] = None):
        super().__init__(message)
        self.candidates = candidates or []


class NoEntryPoint(EntryPointError):
    kind = "no_entry_function"


class UnsupportedSignature(EntryPointError):
    kind = "unsupported_signature"


class AmbiguousEntryPoint(EntryPointError):
    kind = "ambiguous_entry_point"


@dataclass
class EntryDecision:
    name: str
    inputs: list
    structural_id: str
    interface: Tuple
    arity: int
    fully_annotated: bool
    closure_size: int
    n_roots: int
    excluded_drivers: List[str] = field(default_factory=list)
    policy: str = POLICY_ID

    def detail(self) -> dict:
        """Name-free record for the result artifact (no identifier appears)."""
        return {"policy": self.policy, "structural_id": self.structural_id,
                "interface": [list(self.interface[0]), self.interface[1]],
                "arity": self.arity, "fully_annotated": self.fully_annotated,
                "closure_size": self.closure_size, "n_roots": self.n_roots,
                "n_drivers_excluded": len(self.excluded_drivers)}


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

def _required_params(fn: ast.FunctionDef) -> int:
    positional = list(fn.args.posonlyargs) + list(fn.args.args)
    return max(0, len(positional) - len(fn.args.defaults))


def _contains_assert(fn: ast.FunctionDef) -> bool:
    return any(isinstance(node, ast.Assert) for node in ast.walk(fn))


def _is_main_guard(node: ast.stmt) -> bool:
    if not (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)):
        return False
    test = node.test
    sides = [test.left] + list(test.comparators)
    names = {s.id for s in sides if isinstance(s, ast.Name)}
    consts = {s.value for s in sides if isinstance(s, ast.Constant)}
    return "__name__" in names and "__main__" in consts


def _main_guard_calls(tree: ast.Module) -> Set[str]:
    called: Set[str] = set()
    for node in tree.body:
        if _is_main_guard(node):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                    called.add(sub.func.id)
    return called


def _name_loads(fn: ast.FunctionDef) -> Set[str]:
    """Every identifier read inside ``fn`` (calls and first-class references)."""
    return {n.id for n in ast.walk(fn)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


class _Normaliser(ast.NodeTransformer):
    """Erase the spelling of every identifier a rename could change."""

    def __init__(self, module_functions: Set[str], local_names: Set[str]):
        self.module_functions = module_functions
        self.local_names = local_names
        self.slots: Dict[str, str] = {}

    def _slot(self, name: str) -> str:
        return self.slots.setdefault(name, f"v{len(self.slots)}")

    def visit_FunctionDef(self, node):
        node.name = "F"
        node.returns = self.visit(node.returns) if node.returns else None
        node.args = self.visit(node.args)
        node.decorator_list = [self.visit(d) for d in node.decorator_list]
        node.body = [self.visit(s) for s in node.body]
        return node

    def visit_arg(self, node):
        node.arg = self._slot(node.arg)
        node.annotation = self.visit(node.annotation) if node.annotation else None
        return node

    def visit_Name(self, node):
        if node.id in self.module_functions:
            node.id = "<fn>"
        elif node.id in self.local_names:
            node.id = self._slot(node.id)
        return node


def _local_names(fn: ast.FunctionDef) -> Set[str]:
    names = {a.arg for a in ast.walk(fn.args) if isinstance(a, ast.arg)}
    for node in ast.walk(fn):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            names.add(node.id)
    return names


def structural_id(fn: ast.FunctionDef, module_functions: Set[str]) -> str:
    """Name-free fingerprint: invariant under variable and function renaming."""
    clone = copy.deepcopy(fn)
    if (clone.body and isinstance(clone.body[0], ast.Expr)
            and isinstance(getattr(clone.body[0], "value", None), ast.Constant)
            and isinstance(clone.body[0].value.value, str)):
        clone.body = clone.body[1:] or [ast.Pass()]
    normaliser = _Normaliser(module_functions, _local_names(clone))
    dumped = ast.dump(normaliser.visit(clone), annotate_fields=False)
    return hashlib.sha256(dumped.encode()).hexdigest()[:16]


def _interface(fn: ast.FunctionDef) -> Tuple:
    annotations = tuple(a or "" for a in _function_signature(fn))
    returns = ast.unparse(fn.returns) if fn.returns else ""
    return (annotations, returns)


def _closure_size(start: str, graph: Dict[str, Set[str]]) -> int:
    seen, stack = set(), [start]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(graph.get(current, ()) - seen)
    return len(seen)


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

def select_entry_structural(source: str) -> EntryDecision:
    """Select the entry function from ``source`` or raise :class:`EntryPointError`."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise NoEntryPoint(f"source does not parse: {exc.msg}") from exc

    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    if not functions:
        raise NoEntryPoint("no top-level function")
    by_name = {f.name: f for f in functions}
    module_functions = set(by_name)

    guard_calls = _main_guard_calls(tree)
    drivers = [f for f in functions
               if _required_params(f) == 0
               and (_contains_assert(f) or f.name in guard_calls)]
    driver_names = {f.name for f in drivers}
    non_drivers = [f for f in functions if f.name not in driver_names]
    if not non_drivers:
        raise NoEntryPoint("only self-test drivers are defined")

    graph = {f.name: (_name_loads(f) & module_functions) - {f.name} - driver_names
             for f in non_drivers}
    referenced = set().union(*graph.values()) if graph else set()
    roots = [f for f in non_drivers if f.name not in referenced]
    pool = roots or non_drivers                     # a pure cycle has no root

    synthesisable = []
    for fn in pool:
        inputs = synthesise_inputs(_function_signature(fn))
        if inputs is not None:
            synthesisable.append((fn, inputs))
    if not synthesisable:
        raise UnsupportedSignature(
            "no entry candidate can be supplied from the fixed input batteries",
            [f.name for f in pool])

    def key(item):
        fn, _ = item
        annotated = all(a for a in _function_signature(fn))
        return (-_closure_size(fn.name, graph), not annotated, -_required_params(fn))

    ranked = sorted(synthesisable, key=key)       # stable: ties keep source order
    best_key = key(ranked[0])
    tied = [item for item in ranked if key(item) == best_key]
    fingerprints = {structural_id(fn, module_functions) for fn, _ in tied}
    if len(fingerprints) > 1:
        raise AmbiguousEntryPoint(
            f"{len(tied)} structurally distinct entry candidates are tied after "
            "closure size, annotation and arity; no defensible choice exists",
            [fn.name for fn, _ in tied])

    fn, inputs = tied[0]
    return EntryDecision(
        name=fn.name, inputs=inputs,
        structural_id=structural_id(fn, module_functions),
        interface=_interface(fn), arity=_required_params(fn),
        fully_annotated=all(a for a in _function_signature(fn)),
        closure_size=_closure_size(fn.name, graph), n_roots=len(roots),
        excluded_drivers=sorted(driver_names))


def interfaces_correspond(a: EntryDecision, b: EntryDecision) -> bool:
    """Necessary condition for base and variant to be tracing 'the same' entry.

    Equal parameter annotations and return annotation. Not sufficient: two
    unrelated functions can share an interface. A pair failing this test is
    certainly not tracing corresponding functions.
    """
    return a.interface == b.interface
