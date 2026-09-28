"""
experiments/final/protocol.py
=============================
Entry-point selection and input synthesis for the SBG execution protocol.

Two protocols are defined here and both are runnable, because the published
results and the corrected results are not produced by the same procedure and
the difference has to be visible rather than asserted.

PROTOCOL "published"
--------------------
Exactly what ``baselines/v5/b07_dynamic_v5.py`` does: priority-name lookup,
then the invariant-identity call-graph root, then the alphabetically first
public function; zero-argument functions are called once with ``None`` and
everything else is called with the 11 canonical list inputs.

This protocol has a defect that invalidates the output-free claim. The
invariant-identity step returns the *call-graph root*, and in this corpus the
call-graph root is almost always the program's own ``test_*`` self-test driver
(it is the function that calls everything else). Tracing a self-test driver
means the trace contains the driver's ``assert`` statements, so a mutant that
breaks an assertion raises ``AssertionError`` inside the traced region. The
features ``exception_rate`` and ``exception_type_set`` then encode "the
program's own unit tests failed", which is an output comparison. Measured on
the test split, 62 of 64 corpus programs have such a driver.

PROTOCOL "output_free_v6"
-------------------------
Entry candidates exclude scaffolding (``test_*``, ``main``, ``demo*``, and
private names), so no assertion-bearing driver can be traced. Inputs are
synthesised from parameter annotations using one fixed, program-independent
battery per type family. A program whose candidates cannot all be supplied
from the battery is declared out of scope *before* any score is computed;
the rule is static and identical for every method under comparison.

Both the exclusion list and the batteries are fixed constants in this file.
Neither depends on any label or any method's score.
"""
from __future__ import annotations

import ast
import types
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

PRIORITY_NAMES = (
    "sort", "search", "run", "main", "solve", "process", "compute",
    "encode", "decode", "parse", "validate", "execute", "transform",
    "merge", "split", "compress", "decompress", "insert", "remove",
    "add", "find", "build", "evaluate",
)

# Canonical list battery, unchanged from baselines/v5/b07_dynamic_v5.py.
LIST_BATTERY: List[Any] = [
    [], [1], [3, 1, 4, 1, 5, 9, 2, 6], [10, 9, 8, 7, 6, 5], [0, 0, 0, 0],
    [2, 1], [-3, 0, 3], list(range(8)), list(range(1)), list(range(3)),
    list(range(16)),
]

STR_BATTERY: List[str] = [
    "", "a", "abc", "3 + 4 * 2", "racecar", "hello world", "1,2,3",
    "key=value", "  padded  ", "AaBbCc", "0123456789",
]

INT_BATTERY: List[int] = [0, 1, 2, 3, 5, 8, 10, -1, -5, 16, 100]
FLOAT_BATTERY: List[float] = [0.0, 1.0, 2.5, -1.5, 0.5, 10.0, 3.14159,
                              -0.25, 100.0, 0.001, 7.0]
BOOL_BATTERY: List[bool] = [True, False] * 6
DICT_BATTERY: List[dict] = [
    {},
    {"a": []},
    {"a": ["b"], "b": []},
    {"a": ["b", "c"], "b": ["c"], "c": []},
    {1: [2], 2: [3], 3: [1]},
    {"s": ["t"], "t": ["u"], "u": ["s"]},
    {0: [1, 2], 1: [2], 2: []},
    {"x": ["y"], "y": ["z"], "z": ["x"], "w": []},
    {"a": []},
    {1: [], 2: [1]},
    {"n1": ["n2"], "n2": ["n3"], "n3": []},
]

# Annotation string -> battery. Matching is on the unparsed annotation text so
# it works for aliases the corpus defines (Matrix, Poly, BytesLike, DataFrame).
_LIST_ALIASES = ("list", "List", "Sequence", "Matrix", "Poly", "BytesLike",
                 "Tuple", "tuple", "Iterable")
_DICT_ALIASES = ("dict", "Dict", "Mapping", "DataFrame", "Counter")
_UNSUPPORTED = ("Callable", "IO", "TextIO", "Type", "Iterator", "Generator")

BATTERIES = {
    "list": LIST_BATTERY, "str": STR_BATTERY, "int": INT_BATTERY,
    "float": FLOAT_BATTERY, "bool": BOOL_BATTERY, "dict": DICT_BATTERY,
}
BATTERY_SIZE = len(LIST_BATTERY)


def _is_scaffolding(name: str) -> bool:
    """Self-test drivers and private helpers are not part of a program's API."""
    return (name.startswith("test_") or name.startswith("_")
            or name in ("main", "demo", "demo_main", "benchmark"))


def annotation_family(annotation_text: Optional[str]) -> Optional[str]:
    """Map an annotation to a battery key. None annotation defaults to list.

    Returns None when the parameter cannot be supplied from a fixed battery,
    which makes the whole function ineligible.
    """
    if annotation_text is None:
        return "list"
    text = annotation_text.strip()
    if any(token in text for token in _UNSUPPORTED):
        return None
    if text in ("Any", "object"):
        return "list"
    if text.startswith("Optional[") or text.startswith("Union["):
        inner = text[text.index("[") + 1:-1].split(",")[0].strip()
        return annotation_family(inner)
    for alias in _DICT_ALIASES:
        if text == alias or text.startswith(alias + "["):
            return "dict"
    for alias in _LIST_ALIASES:
        if text == alias or text.startswith(alias + "["):
            return "list"
    if text in ("str", "bytes"):
        return "str"
    if text in ("int", "Number"):
        return "int"
    if text == "float":
        return "float"
    if text == "bool":
        return "bool"
    return None                       # unknown custom type: not synthesisable


def _function_signature(node: ast.FunctionDef) -> List[Optional[str]]:
    """Annotation text for each parameter that must be supplied positionally."""
    args = node.args
    positional = list(args.posonlyargs) + list(args.args)
    n_required = len(positional) - len(args.defaults)
    required = positional[:max(0, n_required)]
    return [ast.unparse(a.annotation) if a.annotation else None for a in required]


def synthesise_inputs(annotations: Sequence[Optional[str]]) -> Optional[List[Any]]:
    """One input per battery slot, zipping the per-parameter batteries.

    Zipping (rather than taking a cartesian product) keeps the number of traced
    executions fixed at ``BATTERY_SIZE`` regardless of arity, so a program with
    four parameters is not traced 14 641 times.
    """
    families = [annotation_family(text) for text in annotations]
    if any(family is None for family in families):
        return None
    if not families:
        return [None]                  # zero-argument function
    columns = [BATTERIES[f] for f in families]
    inputs: List[Any] = []
    for index in range(BATTERY_SIZE):
        values = tuple(column[index % len(column)] for column in columns)
        inputs.append(values[0] if len(values) == 1 else values)
    return inputs


def eligible_candidates(tree: ast.Module) -> List[Tuple[str, List[Any], bool]]:
    """(name, inputs, fully_annotated) for every synthesisable API function."""
    out = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if _is_scaffolding(node.name):
            continue
        annotations = _function_signature(node)
        inputs = synthesise_inputs(annotations)
        if inputs is None:
            continue
        out.append((node.name, inputs, all(a is not None for a in annotations)))
    return out


def select_entry_output_free(module: types.ModuleType, source: str
                             ) -> Tuple[Optional[Callable], Optional[str], Optional[List[Any]]]:
    """Deterministic entry selection for PROTOCOL output_free_v6.

    Tier 1  a candidate whose name is in the priority list
    Tier 2  a fully annotated candidate, alphabetically first
    Tier 3  any candidate, alphabetically first

    Annotated candidates are preferred because their inputs are synthesised
    from declared types rather than from the untyped default, which makes the
    execution more likely to exercise the function rather than immediately
    raise. The preference is on the presence of annotations only; it never
    consults an outcome.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None, None, None

    candidates = eligible_candidates(tree)
    if not candidates:
        return None, None, None

    by_name = {name: (inputs, annotated) for name, inputs, annotated in candidates}

    for priority in PRIORITY_NAMES:
        if priority in by_name:
            fn = getattr(module, priority, None)
            if callable(fn):
                return fn, f"priority:{priority}", by_name[priority][0]

    for annotated_only in (True, False):
        for name in sorted(by_name):
            inputs, annotated = by_name[name]
            if annotated is annotated_only:
                fn = getattr(module, name, None)
                if callable(fn):
                    tier = "annotated" if annotated_only else "unannotated"
                    return fn, f"{tier}:{name}", inputs
    return None, None, None
