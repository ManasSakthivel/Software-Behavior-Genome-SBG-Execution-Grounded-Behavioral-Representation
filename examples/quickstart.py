#!/usr/bin/env python3
"""
quickstart.py — minimal end-to-end SBG example.

Compares two simple programs using the V3 dynamic genome and shows
what the distance score looks like.

Usage:
    python3 examples/quickstart.py
"""
import importlib.util
import inspect
import sys
import tempfile
import os
import pathlib

# Add repo root to path so this works from any directory
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sbg.v2.execution.runner import SandboxRunner
from sbg.v3.genome import DynamicGenomeExtractorV3, distance_v3

runner = SandboxRunner()
extractor = DynamicGenomeExtractorV3()

# Canonical inputs used in the main benchmark (same as b07_dynamic_v3.py)
INPUTS = [[], [1], [3, 1, 4, 1, 5, 9, 2, 6], [0, 0, 0, 0], [2, 1], [-3, 0, 3]]


def extract_genome(source_code: str, program_id: str):
    """Extract a V3 genome from a source code string."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source_code)
        tmp_path = f.name

    try:
        spec = importlib.util.spec_from_file_location("_prog", tmp_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Discover the first public function
        fns = [(n, v) for n, v in inspect.getmembers(mod, inspect.isfunction)
               if v.__module__ == mod.__name__ and not n.startswith('_')]
        if not fns:
            return None

        _, fn = fns[0]
        result = runner.run(program_id, fn, INPUTS, n_runs=3, seed=42)
        return extractor.extract_from_traces(program_id, result.traces)

    except Exception as e:
        print(f"  extraction error for {program_id}: {e}")
        return None
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def compare(name_a: str, src_a: str, name_b: str, src_b: str) -> None:
    g1 = extract_genome(src_a, name_a)
    g2 = extract_genome(src_b, name_b)

    if g1 is None or g2 is None:
        print(f"  {name_a} vs {name_b}: extraction failed")
        return

    dist = distance_v3(g1, g2)
    print(f"  {name_a} vs {name_b}: distance={dist:.4f}")


print("=== SBG quickstart ===\n")

# Case 1: semantics-preserving rename — should score low distance
print("Case 1: variable rename only (semantics-preserving)")
compare(
    "sort_v1", "def sort_list(xs):\n    return sorted(xs)\n",
    "sort_v2", "def order_items(items):\n    return sorted(items)\n",
)

# Case 2: mutation that changes behavior
print("\nCase 2: operator swap (> changed to >=, semantics-changing)")
compare(
    "count_pos_original",
    "def count_pos(xs):\n    return sum(1 for x in xs if x > 0)\n",
    "count_pos_mutated",
    "def count_pos(xs):\n    return sum(1 for x in xs if x >= 0)\n",
)

# Case 3: same algorithm, different structure
print("\nCase 3: return value change (semantics-changing)")
compare(
    "bounded_v1", "def bounded(x, lo, hi):\n    return max(lo, min(hi, x))\n",
    "bounded_v2", "def bounded(x, lo, hi):\n    return min(hi, max(lo, x))\n",  # same behavior
)

print()
print("Distances near 0.0 = similar execution behavior.")
print("Distances near 1.0 = different execution behavior.")
print("The representation doesn't catch all mutations (see README for full results).")
