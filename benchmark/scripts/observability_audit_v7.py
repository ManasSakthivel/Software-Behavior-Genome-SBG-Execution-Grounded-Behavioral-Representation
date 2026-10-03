"""
benchmark/scripts/observability_audit_v7.py
===========================================
Static validity audit relative to PROTOCOL output_free_v7
(docs/current/PHASE2_PREREGISTRATION.md §2).

Same definitions as observability_audit.py, with one change: "reachable" starts
from the entry the v7 protocol actually traces, not from the published entry
rule.

  function tier   the v6 selection (priority name, then annotated, then
                  unannotated, alphabetical) over synthesisable, non-scaffolding
                  module-level functions -- computed from the AST with the same
                  functions the protocol uses.
  class tier      used only when the function tier is empty: the resolved
                  constructor and every eligible method of every class the
                  driver constructs (experiments/final/class_driver.py's
                  ``eligible_classes``, the same function the protocol uses).

A CHANGED pair is observable iff a changed function or method is reachable, a
driven class's own body statements (class attributes) changed, or executable
module-level state changed. The audit executes nothing and reads no score.

Output: artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7.json
"""
from __future__ import annotations

import ast
import collections
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmark.scripts.observability_audit import (         # noqa: E402
    SPLITS, collect_definitions, executable_module_statements, normalised_tree,
    referenced_names,
)
from experiments.final.class_driver import _mro, eligible_classes  # noqa: E402
from experiments.final.protocol import PRIORITY_NAMES, eligible_candidates  # noqa: E402


def static_entry_v7(tree: ast.Module):
    """("function", name, [seed]) | ("class", driven, [seeds]) | None."""
    candidates = eligible_candidates(tree)
    if candidates:
        by_name = {name: annotated for name, _, annotated in candidates}
        for priority in PRIORITY_NAMES:
            if priority in by_name:
                return "function", priority, [priority]
        for annotated_only in (True, False):
            for name in sorted(by_name):
                if by_name[name] is annotated_only:
                    return "function", name, [name]
    classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
    specs = eligible_classes(tree)
    if not specs:
        return None
    seeds = []
    for spec in specs:
        wanted = ["__init__"] + [m for m, _, _ in spec["methods"]]
        for method in wanted:
            for owner in _mro(spec["name"], classes):
                if any(isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef))
                       and s.name == method for s in classes[owner].body):
                    seeds.append(f"{owner}.{method}")
                    break
    return "class", [s["name"] for s in specs], seeds


def closure(defs: dict, seeds: list) -> set:
    by_short = collections.defaultdict(list)
    for qual in defs:
        by_short[qual.split(".")[-1]].append(qual)
    seen = {s for s in seeds if s in defs}
    stack = list(seen)
    while stack:
        current = stack.pop()
        for name in referenced_names(defs[current]):
            for qual in by_short.get(name, []):
                if qual not in seen:
                    seen.add(qual)
                    stack.append(qual)
            if name in defs and isinstance(defs[name], ast.ClassDef):
                for qual in defs:
                    if qual.startswith(name + ".") and qual not in seen:
                        seen.add(qual)
                        stack.append(qual)
    return seen


def class_body_statements(tree: ast.Module, name: str) -> list:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return [ast.dump(s) for s in node.body
                    if not isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return []


def analyse_pair(base_source: str, variant_source: str) -> dict:
    base_tree = normalised_tree(base_source)
    variant_tree = normalised_tree(variant_source)
    base_defs = collect_definitions(base_tree)
    variant_defs = collect_definitions(variant_tree)

    entry = static_entry_v7(base_tree)
    if entry is None:
        return {"observable": None, "exclusion_reason": "no_entry_under_v7",
                "entry_tier": None, "entry": None, "changed_definitions": []}
    tier, target, seeds = entry
    reach = closure(base_defs, seeds)
    driven = target if tier == "class" else []

    changed = sorted(
        qual for qual in set(base_defs) | set(variant_defs)
        if (ast.dump(base_defs[qual]) if qual in base_defs else None)
        != (ast.dump(variant_defs[qual]) if qual in variant_defs else None)
    )
    changed_reachable = []
    for qual in changed:
        node = base_defs.get(qual) or variant_defs.get(qual)
        if isinstance(node, ast.ClassDef):
            # A class node changes whenever anything inside it changes; count
            # it only if the class is referenced by reachable code (the v6
            # audit's rule) -- driven classes are handled by body statements.
            if qual in reach and qual not in driven:
                changed_reachable.append(qual)
            continue
        if qual in reach or qual.split(".")[0] in reach:
            changed_reachable.append(qual)
    class_body_changed = [c for c in driven
                          if class_body_statements(base_tree, c)
                          != class_body_statements(variant_tree, c)]
    module_state_changed = (executable_module_statements(base_tree)
                            != executable_module_statements(variant_tree))
    return {
        "observable": bool(changed_reachable) or bool(class_body_changed)
        or module_state_changed,
        "exclusion_reason": None,
        "entry_tier": tier,
        "entry": target,
        "changed_definitions": changed,
        "changed_definitions_reachable": changed_reachable,
        "driven_class_body_changed": class_body_changed,
        "n_reachable_definitions": len(reach),
        "module_state_changed": module_state_changed,
    }


def audit_split(split: str, dataset_dir: pathlib.Path) -> list:
    rows = []
    path = dataset_dir / f"pairs_{split}.jsonl"
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        pair = json.loads(line)
        row = {"pair_id": pair["pair_id"], "base_id": pair["base_id"], "split": split,
               "transformation_type": pair["transformation_type"],
               "semantic_relation": pair["semantic_relation"]}
        base_src = (REPO_ROOT / pair["base_path"]).read_text()
        var_src = (REPO_ROOT / pair["variant_path"]).read_text()
        bad = False
        for tag, src in (("base", base_src), ("variant", var_src)):
            try:
                compile(src, tag, "exec")
            except SyntaxError:
                bad = True
        if bad:
            row.update(status="uncompilable", exclusion_reason="uncompilable_variant")
            rows.append(row)
            continue
        try:
            row.update(analyse_pair(base_src, var_src))
            row["status"] = "ok"
        except Exception as exc:                      # noqa: BLE001
            row.update(status="analysis_error", detail=f"{type(exc).__name__}: {exc}")
        rows.append(row)
    return rows


def summarise(rows: list) -> dict:
    out = {}
    for split in SPLITS:
        sub = [r for r in rows if r["split"] == split]
        if not sub:
            continue
        ok = [r for r in sub if r.get("status") == "ok" and r.get("observable") is not None]
        changed = [r for r in ok if r["semantic_relation"] != "EQUIVALENT"]
        unobs = [r for r in changed if not r["observable"]]
        tiers = collections.Counter()
        for r in ok:
            tiers[(r["base_id"], r["entry_tier"])] += 0
        out[split] = {
            "n_pairs": len(sub),
            "n_uncompilable": sum(r.get("status") == "uncompilable" for r in sub),
            "n_no_entry_under_v7": sum(r.get("exclusion_reason") == "no_entry_under_v7"
                                       for r in sub),
            "n_analysable": len(ok),
            "n_changed": len(changed),
            "n_changed_unobservable": len(unobs),
            "n_observable_valid": len(ok) - len(unobs),
            "programs_by_entry_tier": dict(collections.Counter(
                tier for (_, tier) in tiers)),
            "changed_unobservable_by_program": dict(sorted(collections.Counter(
                r["base_id"] for r in unobs).items())),
        }
    return out


def main(argv: list) -> int:
    dataset_dir = REPO_ROOT / "benchmark" / "datasets" / "v6"
    out_path = REPO_ROOT / "artifacts" / "final" / "BENCHMARK_VALIDITY_AUDIT_V7.json"
    if len(argv) > 1:
        dataset_dir = pathlib.Path(argv[1]).resolve()
    if len(argv) > 2:
        out_path = pathlib.Path(argv[2])
    rows = []
    for split in SPLITS:
        rows.extend(audit_split(split, dataset_dir))
    payload = {
        "audit": "BENCHMARK_VALIDITY_AUDIT_V7",
        "protocol": "output_free_v7",
        "dataset_dir": str(dataset_dir.relative_to(REPO_ROOT)),
        "method": "static; executes nothing; never reads any method's score",
        "rule": "docs/current/PHASE2_PREREGISTRATION.md section 2",
        "summary": summarise(rows),
        "pairs": rows,
    }
    out_path.write_text(json.dumps(payload, indent=2) + "\n")
    for split, s in payload["summary"].items():
        print(f"[{split}] n={s['n_pairs']} uncompilable={s['n_uncompilable']} "
              f"no_entry={s['n_no_entry_under_v7']} changed_unobs="
              f"{s['n_changed_unobservable']}/{s['n_changed']} valid={s['n_observable_valid']} "
              f"tiers={s['programs_by_entry_tier']}")
    print(f"wrote {out_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
