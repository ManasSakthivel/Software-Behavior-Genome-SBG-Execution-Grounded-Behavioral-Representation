"""
experiments/final/class_driver.py
=================================
The class tier of PROTOCOL ``output_free_v7``: a general, program-independent
driver that exercises class-based APIs through bounded method sequences.

The full rule is in docs/current/PHASE2_PREREGISTRATION.md §1. In short:

  * It applies only when the v6 function tier finds nothing, so every program
    v6 already covered keeps its v6 entry and inputs unchanged.
  * Eligibility is decided from the AST, with two runtime filters that the AST
    cannot see reliably: ``BaseException`` subclasses and abstract classes. The
    static audit (benchmark/scripts/observability_audit_v7.py) uses the same AST
    function, so the audit and the protocol agree on what is driven.
  * One trace per (eligible class, battery index i). The trace constructs the
    class from battery values at index i (v6 zip rule), then makes L = 8 calls:
    step k calls methods[(i + k) % len(methods)] with battery values at index
    (i + k) % 11. Each call's arguments are fresh copies. An exception ends
    the trace, exactly as in the function tier.
  * The driver never reads a return value or an attribute, so it is output-free
    by construction. Its own frames are registered in the tracer's
    ``HARNESS_CODE`` set and do not appear in any trace.

Arguments are copied with ``pickle`` rather than ``copy.deepcopy``: every
battery value is a builtin, pickle round-trips builtins in C, and so the copy
produces no traced Python frames. ``copy.deepcopy`` would inject stdlib frames
into every trace.

Out of scope, recorded as ``unsupported_signature``:
  * a required constructor or method parameter whose annotation has no battery;
  * a class whose constructor is inherited from a base outside the module
    (its signature cannot be read from the program's source);
  * exception classes, abstract classes, private and ``Test*`` classes.
"""
from __future__ import annotations

import ast
import pickle
import types
from typing import Any, Callable, Dict, List, Optional, Tuple

from experiments.final.protocol import BATTERIES, BATTERY_SIZE, annotation_family
from sbg.extraction.dynamic.tracer import HARNESS_CODE

STEPS_PER_TRACE = 8

_EXCEPTION_BASE_NAMES = ("BaseException", "Exception", "Error", "Warning")
_PROPERTY_DECORATORS = ("property", "cached_property")
_ACCESSOR_ATTRS = ("setter", "getter", "deleter")


# ---------------------------------------------------------------------------
# Static eligibility (shared with the v7 validity audit)
# ---------------------------------------------------------------------------

def _decorator_names(node: ast.FunctionDef) -> List[str]:
    names = []
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name):
            names.append(dec.id)
        elif isinstance(dec, ast.Attribute):
            names.append(dec.attr)
        elif isinstance(dec, ast.Call):
            target = dec.func
            names.append(target.id if isinstance(target, ast.Name)
                         else getattr(target, "attr", ""))
    return names


def _required_annotations(node: ast.FunctionDef, drop_first: bool) -> List[Optional[str]]:
    """Annotation text of the parameters that must be supplied positionally.

    Same rule as protocol._function_signature, after dropping ``self``/``cls``.
    """
    args = node.args
    positional = list(args.posonlyargs) + list(args.args)
    n_required = len(positional) - len(args.defaults)
    required = positional[:max(0, n_required)]
    if drop_first:
        if not positional:
            return None                       # a method with no self: unusable
        required = required[1:] if required and required[0] is positional[0] else required
    return [ast.unparse(a.annotation) if a.annotation else None for a in required]


def _base_names(node: ast.ClassDef) -> List[str]:
    names = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            names.append(base.id)
        elif isinstance(base, ast.Attribute):
            names.append(base.attr)
        else:
            names.append(ast.unparse(base))
    return names


def _mro(name: str, classes: Dict[str, ast.ClassDef]) -> List[str]:
    """In-module classes in lookup order (depth-first, left to right)."""
    order, stack, seen = [], [name], set()
    while stack:
        current = stack.pop(0)
        if current in seen or current not in classes:
            continue
        seen.add(current)
        order.append(current)
        stack = [b for b in _base_names(classes[current]) if b in classes] + stack
    return order


def _looks_like_exception(name: str, classes: Dict[str, ast.ClassDef]) -> bool:
    for cls in _mro(name, classes):
        for base in _base_names(classes[cls]):
            if base in classes:
                continue
            if any(base == b or base.endswith(b) for b in _EXCEPTION_BASE_NAMES):
                return True
    return False


def _has_external_base(name: str, classes: Dict[str, ast.ClassDef]) -> bool:
    for cls in _mro(name, classes):
        for base in _base_names(classes[cls]):
            if base not in classes and base not in ("object", "ABC", "Generic",
                                                    "Protocol"):
                return True
    return False


def eligible_classes(tree: ast.Module) -> List[dict]:
    """Every class the class tier would drive, in the order it drives them.

    Each entry: {"name", "ctor": [annotation text], "methods": [(name, [annotation
    text], is_static)], "abstract_methods": bool}. A class is omitted when any
    rule in the module docstring excludes it; the reason is in ``ineligible``.
    """
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    out, ineligible = [], {}
    for name in sorted(classes):
        if name.startswith("_") or name.startswith("Test"):
            ineligible[name] = "private_or_test_class"
            continue
        if _looks_like_exception(name, classes):
            ineligible[name] = "exception_class"
            continue

        functions: Dict[str, ast.FunctionDef] = {}
        for cls in reversed(_mro(name, classes)):     # later (derived) overrides earlier
            for sub in classes[cls].body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions[sub.name] = sub

        if any("abstractmethod" in _decorator_names(f) for f in functions.values()):
            ineligible[name] = "abstract_class"
            continue

        init = functions.get("__init__")
        if init is None:
            if _has_external_base(name, classes):
                ineligible[name] = "constructor_inherited_from_external_base"
                continue
            ctor: List[Optional[str]] = []
        else:
            ctor = _required_annotations(init, drop_first=True)
            if ctor is None:
                ineligible[name] = "constructor_without_self"
                continue
        if any(annotation_family(text) is None for text in ctor):
            ineligible[name] = "constructor_parameter_not_synthesisable"
            continue

        methods = []
        for method_name in sorted(functions):
            node = functions[method_name]
            if method_name.startswith("_") or isinstance(node, ast.AsyncFunctionDef):
                continue
            decorators = _decorator_names(node)
            if any(d in _PROPERTY_DECORATORS or d in _ACCESSOR_ATTRS for d in decorators):
                continue
            is_static = "staticmethod" in decorators
            annotations = _required_annotations(node, drop_first=not is_static)
            if annotations is None:
                continue
            if any(annotation_family(text) is None for text in annotations):
                continue
            methods.append((method_name, annotations, is_static))
        out.append({"name": name, "ctor": ctor, "methods": methods})
    eligible_classes.last_ineligible = ineligible      # type: ignore[attr-defined]
    return out


def ineligible_reasons(tree: ast.Module) -> Dict[str, str]:
    eligible_classes(tree)
    return dict(eligible_classes.last_ineligible)      # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def _values(annotations: List[Optional[str]], index: int) -> tuple:
    families = [annotation_family(text) for text in annotations]
    return tuple(BATTERIES[f][index % len(BATTERIES[f])] for f in families)


def build_plan(module: types.ModuleType, tree: ast.Module
               ) -> Tuple[List[Any], Dict[str, str], List[str]]:
    """(inputs, runtime_exclusions, driven_class_names).

    Each input is an opaque, fully precomputed plan for one trace: the class
    object and pickled argument tuples for the constructor and every step.
    Precomputing means the traced driver does nothing but unpickle and call.
    """
    runtime_excluded: Dict[str, str] = {}
    driven: List[Tuple[type, dict]] = []
    for spec in eligible_classes(tree):
        cls = getattr(module, spec["name"], None)
        if not isinstance(cls, type):
            runtime_excluded[spec["name"]] = "not_a_class_at_runtime"
            continue
        if issubclass(cls, BaseException):
            runtime_excluded[spec["name"]] = "exception_class"
            continue
        if getattr(cls, "__abstractmethods__", None):
            runtime_excluded[spec["name"]] = "abstract_class"
            continue
        driven.append((cls, spec))

    inputs: List[Any] = []
    for cls, spec in driven:
        methods = spec["methods"]
        for i in range(BATTERY_SIZE):
            ctor_blob = pickle.dumps(_values(spec["ctor"], i))
            steps = []
            if methods:
                for k in range(STEPS_PER_TRACE):
                    name, annotations, _ = methods[(i + k) % len(methods)]
                    steps.append((name, pickle.dumps(_values(annotations, (i + k) % BATTERY_SIZE))))
            inputs.append(_Plan(cls, ctor_blob, tuple(steps), f"{spec['name']}[{i}]"))
    return inputs, runtime_excluded, [spec["name"] for _, spec in driven]


class _Plan:
    __slots__ = ("cls", "ctor_blob", "steps", "label")

    def __init__(self, cls, ctor_blob, steps, label):
        self.cls, self.ctor_blob, self.steps, self.label = cls, ctor_blob, steps, label

    def __repr__(self) -> str:
        # The tracer stores repr(input); keep it free of addresses so runs are
        # byte-identical.
        return f"ClassPlan({self.label})"


def drive(plan: "_Plan") -> None:
    """Construct, then call each planned method. Never inspects a result."""
    loads = pickle.loads
    instance = plan.cls(*loads(plan.ctor_blob))
    for name, blob in plan.steps:
        getattr(instance, name)(*loads(blob))


HARNESS_CODE.add(drive.__code__)


def select_class_entry(module: types.ModuleType, source: str
                       ) -> Tuple[Optional[Callable], Optional[str], Optional[List[Any]], dict]:
    """Class-tier entry for PROTOCOL output_free_v7.

    Returns (traced_fn, discovery, inputs, detail). ``detail`` records which
    classes were driven and why others were not.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None, None, None, {"reason": "syntax_error"}
    inputs, runtime_excluded, driven = build_plan(module, tree)
    detail = {
        "driven_classes": driven,
        "static_exclusions": ineligible_reasons(tree),
        "runtime_exclusions": runtime_excluded,
    }
    if not inputs:
        return None, None, None, detail
    return drive, "class:" + ",".join(driven), inputs, detail
