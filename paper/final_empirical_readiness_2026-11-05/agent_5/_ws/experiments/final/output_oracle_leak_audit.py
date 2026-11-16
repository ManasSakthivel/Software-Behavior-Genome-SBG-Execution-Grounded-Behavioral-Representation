"""
experiments/final/output_oracle_leak_audit.py
=============================================
Establishes, statically, that the published execution protocol violates the
output-free constraint it claims to satisfy.

The claim under test
--------------------
The README states that the distance function "is output-free -- it never reads
program outputs, only execution structure. This prevents a form of leakage
where a comparison method is really just checking whether outputs match." The
V5 safeguard audit reports 9/9 checks passing, and its checks are sound as far
as they go: no SBG code path reads a return value.

The defect
----------
The leak is not in the distance function. It is in the choice of what to
execute. ``baselines/v5/b07_dynamic_v5.py`` discovers its entry function in
three steps, the second of which is ``compute_program_identity``'s call-graph
root -- documented as "the function not called by any other module-level
function". In this corpus that function is the program's own ``test_*`` self-
test driver, because a driver calls everything and nothing calls it.

Tracing a self-test driver puts the driver's ``assert`` statements inside the
traced region. A mutant that breaks an assertion raises ``AssertionError``
there, so ``exception_rate`` and ``exception_type_set`` record "this program's
own unit tests failed" -- an output comparison, arrived at indirectly.

That matters for the headline comparison. The README reports that
``exception_fraction`` alone (0.593) beats the full SBG genome (0.551) and
reads this as evidence that the representation fails to beat a cheap shortcut.
If the entry point is a self-test driver, ``exception_fraction`` is not a
shortcut: it is a leaked output oracle, and the comparison does not support
that reading.

This audit is purely static -- it parses sources and never executes them -- so
its verdict cannot depend on any measured score.

Output: artifacts/final/OUTPUT_ORACLE_LEAK_AUDIT.json
"""
from __future__ import annotations

import ast
import json
import pathlib
import sys
from typing import Dict, List, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sbg.v5.invariant_identity import compute_program_identity   # noqa: E402
from experiments.final.protocol import PRIORITY_NAMES, _is_scaffolding  # noqa: E402

CORPUS_DIR = REPO_ROOT / "benchmark" / "corpus" / "base_programs"
SPLITS_PATH = REPO_ROOT / "benchmark" / "splits" / "split_assignment.json"


def published_entry_name(source: str) -> Optional[str]:
    """Reproduces b07_dynamic_v5.py::_load_entry_fn_v5 without executing."""
    tree = ast.parse(source)
    top_level = [node.name for node in tree.body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for name in PRIORITY_NAMES:
        if name in top_level:
            return name
    try:
        identity = compute_program_identity(source)
        if top_level and 0 <= identity.root_index < len(top_level):
            return top_level[identity.root_index]
    except Exception:                                            # noqa: BLE001
        pass
    public = sorted(n for n in top_level if not n.startswith("_"))
    return public[0] if public else None


def assertions_in(tree: ast.Module, function_name: str) -> int:
    for node in tree.body:
        if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == function_name):
            return sum(1 for sub in ast.walk(node) if isinstance(sub, ast.Assert))
    return 0


def audit_program(path: pathlib.Path) -> Dict:
    source = path.read_text()
    tree = ast.parse(source)
    entry = published_entry_name(source)
    row = {
        "program": path.stem,
        "path": str(path.relative_to(REPO_ROOT)),
        "published_entry_function": entry,
        "entry_is_self_test_driver": bool(entry and _is_scaffolding(entry)),
        "assert_statements_in_entry": assertions_in(tree, entry) if entry else 0,
        "n_top_level_functions": sum(
            1 for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))),
        "n_top_level_classes": sum(1 for n in tree.body if isinstance(n, ast.ClassDef)),
    }
    row["entry_traces_assertions"] = (row["entry_is_self_test_driver"]
                                      and row["assert_statements_in_entry"] > 0)
    try:
        parameters = 0
        for node in tree.body:
            if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == entry):
                parameters = len(node.args.args)
        row["entry_parameter_count"] = parameters
        row["canonical_inputs_used"] = parameters > 0
    except Exception:                                            # noqa: BLE001
        row["entry_parameter_count"] = None
        row["canonical_inputs_used"] = None
    return row


def main() -> int:
    splits = json.loads(SPLITS_PATH.read_text())["splits"]
    assigned = {name: split for split, names in splits.items() for name in names}

    rows: List[Dict] = []
    for path in sorted(CORPUS_DIR.glob("*.py")):
        row = audit_program(path)
        row["split"] = assigned.get(path.stem)
        rows.append(row)

    def summarise(subset: List[Dict]) -> Dict:
        n = len(subset)
        leaking = [r for r in subset if r["entry_traces_assertions"]]
        return {
            "n_programs": n,
            "n_entry_is_self_test_driver": sum(1 for r in subset
                                               if r["entry_is_self_test_driver"]),
            "n_entry_traces_assertions": len(leaking),
            "fraction_leaking": round(len(leaking) / n, 4) if n else None,
            "n_canonical_inputs_unused": sum(1 for r in subset
                                             if r["canonical_inputs_used"] is False),
            "total_assert_statements_traced": sum(r["assert_statements_in_entry"]
                                                  for r in leaking),
            "leaking_programs": sorted(r["program"] for r in leaking),
        }

    payload = {
        "audit": "OUTPUT_ORACLE_LEAK_AUDIT",
        "method": "static AST analysis; no program is executed",
        "finding": (
            "The published protocol's entry-function discovery selects the "
            "call-graph root, which in this corpus is the program's own self-test "
            "driver. Tracing it places the driver's assert statements inside the "
            "traced region, so exception_rate and exception_type_set encode "
            "whether the program's own tests passed. The output-free constraint "
            "is therefore violated by the execution protocol, not by the distance "
            "function that the 9/9 safeguard audit checked."
        ),
        "consequence_for_published_claims": (
            "The reported exception_fraction AUROC (0.567 standalone, 0.593 for "
            "the V3 exception component) is not a shortcut baseline. Any "
            "conclusion of the form 'a simple shortcut beats the SBG "
            "representation' is unsupported while the entry point is a self-test "
            "driver."
        ),
        "remedy": (
            "PROTOCOL output_free_v6 in experiments/final/protocol.py excludes "
            "scaffolding from entry-function discovery and synthesises inputs "
            "from parameter annotations."
        ),
        "corpus_summary": summarise(rows),
        "by_split": {split: summarise([r for r in rows if r["split"] == split])
                     for split in ("train", "dev", "val", "test")},
        "programs": rows,
    }

    out = REPO_ROOT / "artifacts" / "final" / "OUTPUT_ORACLE_LEAK_AUDIT.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")

    summary = payload["corpus_summary"]
    print(f"corpus: {summary['n_programs']} programs")
    print(f"  entry is a self-test driver : {summary['n_entry_is_self_test_driver']}")
    print(f"  entry traces assertions     : {summary['n_entry_traces_assertions']} "
          f"({summary['fraction_leaking']:.1%})")
    print(f"  assert statements traced    : {summary['total_assert_statements_traced']}")
    print(f"  canonical inputs never used : {summary['n_canonical_inputs_unused']}")
    for split, block in payload["by_split"].items():
        print(f"  [{split:5s}] leaking {block['n_entry_traces_assertions']}"
              f"/{block['n_programs']}")
    print(f"wrote {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
