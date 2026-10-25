"""
Regression and verification tests for SP-2 FunctionRenameTransformation repair.

Verifies that:
- Method definitions and attribute references (e.g. self.method()) are both renamed consistently
- Bare function calls (free functions) continue to be renamed properly without regression
- Multiple class methods in the same class are renamed consistently
- Standard library / object attributes (like list.append, dict.update) are not falsely renamed
- Transformed classes execute at runtime without raising AttributeError
- Newly generated SP-2 pairs produced with the repaired transformer pass data_integrity.py with 0 defects
"""
from __future__ import annotations

import ast
import copy
import json
import pathlib
import sys
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "final"))

from benchmark.transformations.preserving.transformations.sp2_function_rename import (
    FunctionRenameTransformation,
    _FunctionRenamer,
    _collect_function_names,
)
import data_integrity as di


def test_attribute_reference_is_renamed():
    """Class with self.old() becomes self.new()."""
    src = """class Counter:
    def allow(self, x):
        return x > 0

    def check_all(self, items):
        return all(self.allow(i) for i in items)
"""
    t = FunctionRenameTransformation()
    tree = ast.parse(src)
    rename_map = {"allow": "fn_allow"}
    new_tree = _FunctionRenamer(rename_map).visit(copy.deepcopy(tree))
    ast.fix_missing_locations(new_tree)
    res = ast.unparse(new_tree)

    assert "def fn_allow(self, x):" in res
    assert "self.fn_allow(i)" in res
    assert "self.allow" not in res
    assert "def allow(" not in res


def test_bare_function_call_still_works():
    """foo() -> fn_foo() is not regressed for bare function calls."""
    src = """def helper(x):
    return x * 2

def compute(x):
    return helper(x) + 1
"""
    tree = ast.parse(src)
    rename_map = {"helper": "fn_helper", "compute": "calculate"}
    new_tree = _FunctionRenamer(rename_map).visit(copy.deepcopy(tree))
    ast.fix_missing_locations(new_tree)
    res = ast.unparse(new_tree)

    assert "def fn_helper(x):" in res
    assert "def calculate(x):" in res
    assert "return fn_helper(x) + 1" in res
    assert "return helper(x)" not in res


def test_class_with_multiple_methods_renamed():
    """Multiple method renames in a class are all applied consistently."""
    src = """class MathEngine:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b

    def compute(self, a, b):
        return self.add(a, self.multiply(a, b))
"""
    rename_map = {"add": "fn_add", "multiply": "fn_multiply", "compute": "calculate"}
    tree = ast.parse(src)
    new_tree = _FunctionRenamer(rename_map).visit(copy.deepcopy(tree))
    ast.fix_missing_locations(new_tree)
    res = ast.unparse(new_tree)

    assert "def fn_add" in res
    assert "def fn_multiply" in res
    assert "def calculate" in res
    assert "self.fn_add(a, self.fn_multiply(a, b))" in res
    assert "self.add" not in res
    assert "self.multiply" not in res


def test_no_false_positives_on_library_attrs():
    """Standard library and object methods (list.append, dict.update) are not renamed."""
    src = """def process_items(items):
    out = []
    d = {}
    for item in items:
        out.append(item)
        d.update({item: True})
    return out, d
"""
    t = FunctionRenameTransformation()
    res = t.apply(src, seed=42)
    assert ".append(" in res
    assert ".update(" in res
    assert "append" not in getattr(t, "last_rename_map", {})
    assert "update" not in getattr(t, "last_rename_map", {})
    assert t.validate(src, res)


def test_transformed_class_runs_without_attribute_error():
    """Execute transformed class code at runtime to verify no AttributeError is raised."""
    src = """class RateLimiter:
    def __init__(self, limit):
        self.limit = limit
        self.count = 0

    def allow(self, amount=1):
        if self.count + amount <= self.limit:
            self.count += amount
            return True
        return False

    def request_batch(self, batch_sizes):
        return [self.allow(s) for s in batch_sizes]

limiter = RateLimiter(5)
res1 = limiter.request_batch([2, 2, 2])
"""
    t = FunctionRenameTransformation()
    for seed in range(5):
        transformed = t.apply(src, seed=seed)
        scope = {}
        # Must execute cleanly without AttributeError
        exec(transformed, scope)
        assert scope["res1"] == [True, True, False]


def test_data_integrity_detects_zero_sp2_defects_on_repaired_pairs(tmp_path):
    """Prospective test: Re-applying SP-2 to base programs produces 0 defects in data_integrity."""
    corpus_dir = REPO_ROOT / "benchmark" / "corpus" / "base_programs"
    programs_to_test = [
        "api_rate_limiter.py",
        "ds_stack_queue.py",
        "fsm_traffic_light.py",
        "api_event_bus.py",
        "conc_read_write_lock.py",
    ]

    t = FunctionRenameTransformation()
    rows = []
    files = {}

    for idx, prog_name in enumerate(programs_to_test):
        prog_path = corpus_dir / prog_name
        if not prog_path.exists():
            continue
        base_src = prog_path.read_text()
        base_rel = f"base_{idx}.py"
        files[base_rel] = base_src

        for seed in [0, 1, 2]:
            variant_src = t.apply(base_src, seed=seed)
            var_rel = f"var_{idx}_s{seed}.py"
            files[var_rel] = variant_src

            # Check direct dangling method references
            dangling = di.dangling_method_references(base_src, variant_src)
            assert dangling == [], f"Dangling references {dangling} found in {prog_name} seed {seed}"

            rows.append({
                "pair_id": f"pair_{idx}_{seed}",
                "base_id": prog_name.replace(".py", ""),
                "base_path": base_rel,
                "variant_path": var_rel,
                "transformation_type": "SP-2",
                "semantic_relation": "EQUIVALENT",
                "expected_label": "EQUIVALENT",
                "split": "train",
            })

    # Write synthetic dataset and run full check_dataset
    ds_dir = tmp_path / "synthetic_ds"
    ds_dir.mkdir()
    for split in ("train", "dev", "val", "test"):
        (ds_dir / f"pairs_{split}.jsonl").write_text(
            "\n".join(json.dumps(r) for r in rows if r["split"] == split)
        )
    for name, content in files.items():
        (tmp_path / name).write_text(content)

    report = di.check_dataset(ds_dir, repo=tmp_path)
    assert report["defect_counts"].get("sp2_dangling_method_reference", 0) == 0
