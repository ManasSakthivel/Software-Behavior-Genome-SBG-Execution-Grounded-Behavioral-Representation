"""
benchmark/scripts/observability_audit.py
========================================
Benchmark validity audit for the SBG pair benchmark.

MOTIVATION
----------
The SBG execution protocol traces ONE entry function per program over a fixed
set of canonical inputs. A labelled pair is only evidence about a behavioural
representation if the transformation that defines its label is *reachable* from
that entry function. Two defects in the original generators break this:

  1. SP-3 (DEAD_CODE_INSERT) could emit ``return None`` at module or class
     scope, producing variants that do not compile.
  2. The mutation operators selected their mutation site by walking the whole
     module in BFS order. Site 0 therefore lands on module-level scaffolding
     (the ``if __name__ == '__main__'`` guard, the module docstring, or a
     ``test_*`` driver) far more often than on the program's functional code.
     Such a mutant is labelled CHANGED but is behaviourally identical when the
     entry function is executed.

This script measures both defects. It is purely static and never consults any
method's score, so applying its verdict as an inclusion filter cannot bias a
comparison between methods.

DEFINITIONS
-----------
compilable        both files pass ``compile(src, path, 'exec')``
entry function    the function the protocol would trace (same discovery rule as
                  ``baselines/v5/b07_dynamic_v5.py``: priority list, then first
                  public function in alphabetical order)
reachable         transitive closure of name-resolved call edges from the entry
                  function over module-level functions and class methods. The
                  resolution is deliberately over-approximate (any Name or
                  Attribute matching a definition name is an edge), so the set
                  is a superset of the truly reachable code and the filter is
                  conservative: it can only mark MORE pairs observable.
observable        the AST difference between base and variant intersects
                  reachable code, or changes module-level state that the entry
                  function could read. Module docstrings and the ``__main__``
                  guard block are excluded: neither is executed by the protocol
                  loader, and neither is part of the program's functional code.

OUTPUT
------
artifacts/final/BENCHMARK_VALIDITY_AUDIT.json
"""
from __future__ import annotations

import ast
import collections
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

# Same priority list as baselines/v5/b07_dynamic_v5.py::_load_entry_fn_v5
PRIORITY_NAMES = (
    "sort", "search", "run", "main", "solve", "process", "compute",
    "encode", "decode", "parse", "validate", "execute", "transform",
    "merge", "split", "compress", "decompress", "insert", "remove",
    "add", "find", "build", "evaluate",
)

SPLITS = ("train", "dev", "val", "test")


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

def normalised_tree(source: str) -> ast.Module:
    """Round-trip through ast.unparse so formatting differences vanish."""
    return ast.parse(ast.unparse(ast.parse(source)))


def collect_definitions(tree: ast.Module) -> dict:
    """qualname -> AST node, for module-level functions, classes and methods."""
    out: dict = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = node
        elif isinstance(node, ast.ClassDef):
            out[node.name] = node
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[f"{node.name}.{sub.name}"] = sub
    return out


def referenced_names(node: ast.AST) -> set:
    names = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            names.add(n.id)
        elif isinstance(n, ast.Attribute):
            names.add(n.attr)
    return names


def discover_entry(tree: ast.Module) -> str | None:
    top_level = {
        n.name for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for name in PRIORITY_NAMES:
        if name in top_level:
            return name
    public = sorted(n for n in top_level if not n.startswith("_"))
    return public[0] if public else None


def reachable_from(defs: dict, entry: str) -> set:
    by_short = collections.defaultdict(list)
    for qual in defs:
        by_short[qual.split(".")[-1]].append(qual)

    seen: set = set()
    stack: list = []
    if entry in defs:
        seen.add(entry)
        stack.append(entry)

    while stack:
        current = stack.pop()
        for name in referenced_names(defs[current]):
            for qual in by_short.get(name, []):
                if qual not in seen:
                    seen.add(qual)
                    stack.append(qual)
            # Instantiating a class pulls in every one of its methods.
            if name in defs and isinstance(defs[name], ast.ClassDef):
                for qual in defs:
                    if qual.startswith(name + ".") and qual not in seen:
                        seen.add(qual)
                        stack.append(qual)
    return seen


def _is_main_guard(node: ast.stmt) -> bool:
    return isinstance(node, ast.If) and "__name__" in ast.unparse(node.test)


def executable_module_statements(tree: ast.Module) -> list:
    """Module-level statements the protocol loader actually executes and whose
    effect the entry function could observe.

    Excludes imports, definitions, the module docstring and the ``__main__``
    guard (the loader gives the module a private name, so the guard body is
    dead under the protocol).
    """
    out = []
    for index, node in enumerate(tree.body):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                             ast.Import, ast.ImportFrom)):
            continue
        if _is_main_guard(node):
            continue
        if (index == 0 and isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            continue  # module docstring
        out.append(ast.dump(node))
    return out


# ---------------------------------------------------------------------------
# Per-pair analysis
# ---------------------------------------------------------------------------

def analyse_pair(base_source: str, variant_source: str) -> dict:
    base_tree = normalised_tree(base_source)
    variant_tree = normalised_tree(variant_source)

    base_defs = collect_definitions(base_tree)
    variant_defs = collect_definitions(variant_tree)

    entry = discover_entry(base_tree)
    if entry is None:
        return {"observable": None, "exclusion_reason": "no_entry_function",
                "entry_function": None, "changed_definitions": [],
                "n_reachable_definitions": 0, "module_state_changed": None}

    reach = reachable_from(base_defs, entry)

    changed = sorted(
        qual for qual in set(base_defs) | set(variant_defs)
        if (ast.dump(base_defs[qual]) if qual in base_defs else None)
        != (ast.dump(variant_defs[qual]) if qual in variant_defs else None)
    )
    changed_reachable = [
        q for q in changed if q in reach or q.split(".")[0] in reach
    ]
    module_state_changed = (
        executable_module_statements(base_tree)
        != executable_module_statements(variant_tree)
    )

    return {
        "observable": bool(changed_reachable) or module_state_changed,
        "exclusion_reason": None,
        "entry_function": entry,
        "changed_definitions": changed,
        "changed_definitions_reachable": changed_reachable,
        "n_reachable_definitions": len(reach),
        "module_state_changed": module_state_changed,
    }


def audit_split(split: str, dataset_dir: pathlib.Path) -> list:
    rows = []
    path = dataset_dir / f"pairs_{split}.jsonl"
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        pair = json.loads(line)
        row = {
            "pair_id": pair["pair_id"],
            "base_id": pair["base_id"],
            "split": split,
            "transformation_type": pair["transformation_type"],
            "semantic_relation": pair["semantic_relation"],
        }
        base_path = REPO_ROOT / pair["base_path"]
        variant_path = REPO_ROOT / pair["variant_path"]
        try:
            base_source = base_path.read_text()
            variant_source = variant_path.read_text()
        except OSError as exc:
            row.update(status="file_missing", detail=str(exc))
            rows.append(row)
            continue

        compiles_ok = True
        for tag, source, path_for_msg in (("base", base_source, base_path),
                                          ("variant", variant_source, variant_path)):
            try:
                compile(source, str(path_for_msg), "exec")
                row[f"{tag}_compiles"] = True
            except SyntaxError as exc:
                row[f"{tag}_compiles"] = False
                row[f"{tag}_syntax_error"] = exc.msg
                compiles_ok = False
        if not compiles_ok:
            row["status"] = "uncompilable"
            row["exclusion_reason"] = "uncompilable_variant"
            rows.append(row)
            continue

        try:
            row.update(analyse_pair(base_source, variant_source))
            row["status"] = "ok"
        except Exception as exc:                      # noqa: BLE001 - audit must not abort
            row["status"] = "analysis_error"
            row["detail"] = f"{type(exc).__name__}: {exc}"
        rows.append(row)
    return rows


def summarise(rows: list) -> dict:
    summary = {}
    for split in SPLITS:
        subset = [r for r in rows if r["split"] == split]
        uncompilable = [r for r in subset if r.get("status") == "uncompilable"]
        no_entry = [r for r in subset if r.get("exclusion_reason") == "no_entry_function"]
        analysable = [r for r in subset
                      if r.get("status") == "ok" and r.get("observable") is not None]
        changed = [r for r in analysable if r["semantic_relation"] != "EQUIVALENT"]
        equivalent = [r for r in analysable if r["semantic_relation"] == "EQUIVALENT"]
        changed_unobservable = [r for r in changed if not r["observable"]]
        equivalent_noop = [r for r in equivalent if not r["observable"]]
        summary[split] = {
            "n_pairs": len(subset),
            "n_uncompilable": len(uncompilable),
            "n_no_entry_function": len(no_entry),
            "n_analysable": len(analysable),
            "n_changed": len(changed),
            "n_equivalent": len(equivalent),
            "n_changed_unobservable": len(changed_unobservable),
            "n_equivalent_noop": len(equivalent_noop),
            "n_observable_valid": len(analysable) - len(changed_unobservable),
            "changed_unobservable_by_operator": dict(sorted(collections.Counter(
                r["transformation_type"] for r in changed_unobservable).items())),
            "uncompilable_by_operator": dict(sorted(collections.Counter(
                r["transformation_type"] for r in uncompilable).items())),
            "no_entry_function_by_program": dict(sorted(collections.Counter(
                r["base_id"] for r in no_entry).items())),
        }
    return summary


def main(argv: list) -> int:
    dataset_dir = REPO_ROOT / "benchmark" / "datasets"
    out_path = REPO_ROOT / "artifacts" / "final" / "BENCHMARK_VALIDITY_AUDIT.json"
    if len(argv) > 1:
        dataset_dir = pathlib.Path(argv[1])
    if len(argv) > 2:
        out_path = pathlib.Path(argv[2])

    rows = []
    for split in SPLITS:
        rows.extend(audit_split(split, dataset_dir))

    summary = summarise(rows)
    payload = {
        "audit": "BENCHMARK_VALIDITY_AUDIT",
        "dataset_dir": str(dataset_dir.relative_to(REPO_ROOT))
        if dataset_dir.is_relative_to(REPO_ROOT) else str(dataset_dir),
        "method": "static; never reads any method's score",
        "criteria": {
            "uncompilable": "compile(source) raises SyntaxError for base or variant",
            "no_entry_function": "no module-level function discoverable by the protocol",
            "changed_unobservable": (
                "CHANGED-labelled pair whose AST difference does not intersect code "
                "reachable from the entry function nor executable module-level state"
            ),
            "equivalent_noop": (
                "EQUIVALENT-labelled pair whose normalised AST is unchanged in "
                "reachable code (trivially equivalent)"
            ),
        },
        "summary": summary,
        "pairs": rows,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n")

    for split in SPLITS:
        s = summary[split]
        print(f"[{split}] n={s['n_pairs']:5d}  uncompilable={s['n_uncompilable']:3d}  "
              f"no_entry_fn={s['n_no_entry_function']:3d}  "
              f"CHANGED_unobservable={s['n_changed_unobservable']:3d}/{s['n_changed']:3d}  "
              f"EQUIV_noop={s['n_equivalent_noop']:3d}/{s['n_equivalent']:3d}  "
              f"valid={s['n_observable_valid']:4d}")
    print(f"\nwrote {out_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
