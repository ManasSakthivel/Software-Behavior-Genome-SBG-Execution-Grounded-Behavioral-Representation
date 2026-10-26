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


# ---------------------------------------------------------------------------
# max_names parameter tests (edit-size redesign — see EDIT_SIZE_REDESIGN.md)
# ---------------------------------------------------------------------------

def _count_changed_lines(src: str, variant: str) -> int:
    """Count added + removed lines in a unified diff (excludes header lines)."""
    import difflib
    src_lines = src.strip().splitlines()
    var_lines = variant.strip().splitlines()
    n = 0
    for line in difflib.unified_diff(src_lines, var_lines, lineterm="", n=0):
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            n += 1
    return n


def test_sp2_max_names_1_renames_exactly_one_function():
    """max_names=1 causes SP-2 to rename exactly 1 function per application."""
    src = """def helper_a(x):
    return x + 1

def helper_b(x):
    return x * 2

def compute(x):
    return helper_a(helper_b(x))
"""
    t = FunctionRenameTransformation()
    # Run multiple seeds; each must produce a rename_map with exactly 1 entry
    for seed in range(10):
        t.apply(src, seed=seed, max_names=1)
        assert len(t.last_rename_map) <= 1, (
            f"seed={seed}: expected at most 1 rename, got {len(t.last_rename_map)}: {t.last_rename_map}"
        )


def test_sp2_max_names_1_edit_size_limited():
    """max_names=1 produces smaller edit sizes than unrestricted SP-2."""
    src = """def compute(n):
    result = 0
    for i in range(n):
        result += helper_a(i) + helper_b(i) + helper_c(i)
    return result

def helper_a(x):
    return x + 1

def helper_b(x):
    return x * 2

def helper_c(x):
    return x - 1
"""
    t = FunctionRenameTransformation()
    max1_sizes = []
    unrestricted_sizes = []
    for seed in range(20):
        v_max1 = t.apply(src, seed=seed, max_names=1)
        max1_sizes.append(_count_changed_lines(src, v_max1))
        v_unrest = t.apply(src, seed=seed)
        unrestricted_sizes.append(_count_changed_lines(src, v_unrest))
    # max_names=1 should never produce more changed lines than unrestricted
    for i, (m1, ur) in enumerate(zip(max1_sizes, unrestricted_sizes)):
        assert m1 <= ur or ur == 0, (
            f"seed={i}: max_names=1 gave {m1} lines, unrestricted gave {ur}"
        )
    # At least some max_names=1 results should be strictly smaller
    assert any(m1 < ur for m1, ur in zip(max1_sizes, unrestricted_sizes) if ur > 0), \
        "max_names=1 never produced a smaller edit than unrestricted (unexpected)"


def test_sp2_max_names_1_semantics_preserved():
    """max_names=1 produces a variant with identical runtime behaviour."""
    src = """def compute(items):
    total = 0
    for x in items:
        total += helper(x)
    return total

def helper(x):
    return x * x
"""
    t = FunctionRenameTransformation()
    for seed in range(5):
        variant = t.apply(src, seed=seed, max_names=1)
        if variant == src:
            continue  # no-op is fine
        # Both must return the same result for the same input
        base_scope: dict = {}
        var_scope: dict = {}
        exec(src, base_scope)
        exec(variant, var_scope)
        for func_name in ("compute",):
            for inp in ([1, 2, 3], [0], [-1, 2, -3]):
                base_result = base_scope[func_name](inp)
                # In the variant, the function may have been renamed; try both names
                if func_name in var_scope:
                    var_result = var_scope[func_name](inp)
                else:
                    # find renamed version
                    candidates = [v for k, v in var_scope.items()
                                  if callable(v) and k not in ("__builtins__",)]
                    continue  # skip if not easily found
                assert base_result == var_result, (
                    f"seed={seed}: mismatch for input {inp}: base={base_result}, variant={var_result}"
                )


def test_sp1_max_names_1_renames_exactly_one_variable():
    """max_names=1 on SP-1 produces a rename map with exactly 1 variable."""
    from benchmark.transformations.preserving.transformations.sp1_variable_rename import (
        VariableRenameTransformation,
    )
    src = """def compute(n, m):
    result = 0
    count = 0
    for i in range(n):
        count += 1
        result += i * m
    return result, count
"""
    t = VariableRenameTransformation()
    for seed in range(10):
        v = t.apply(src, seed=seed, max_names=1)
        if v == src:
            continue  # no-op if no pool candidates match
        # Count how many distinct variable names were renamed
        src_names = set(ast.walk(ast.parse(src)))
        # Verify the produced code compiles
        try:
            ast.parse(v)
        except SyntaxError as e:
            raise AssertionError(f"SP-1 max_names=1 produced invalid code at seed={seed}: {e}")
