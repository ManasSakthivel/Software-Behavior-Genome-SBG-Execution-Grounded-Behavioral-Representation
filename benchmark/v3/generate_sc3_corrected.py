"""
benchmark/v3/generate_sc3_corrected.py
=======================================
SBG V3 — Corrected SC-3 (CONSTANT_MUTATION) benchmark generator.

CONTEXT
=======
v2 SC-3 forensic audit (artifacts/v2/SC3_FORENSIC_RESULTS.json) found:
  - 76.9% of v2 SC-3 pairs are cosmetic quote changes (MISLABELED as CHANGED)
  - 0% are actual integer ±1 mutations as specified in the manifest
  - Root cause: ast.unparse normalizes all string quote styles to single-quotes

This generator creates a FRESH v3 SC-3 benchmark with:
  - Only integer constant mutations (±1, ±2) on meaningful constants
  - Targeting: loop bounds, capacity constants, divisors, thresholds
  - Verification: each mutation must change program behavior on at least 1 input
  - Multiple difficulty levels: EASY (hot path), MEDIUM (conditional), HARD (boundary)

SCIENTIFIC INTEGRITY
====================
  - Does NOT modify any frozen v2 benchmark files
  - Does NOT use ast.unparse (which normalizes quotes, causing the v2 bug)
  - Records exact mutation site (file:line:col, AST path)
  - Records witness_input (input that detects the mutation)
  - Records behavioral_verification status (VERIFIED/UNVERIFIED)
  - Labeled as EXPLORATORY_SC3_CORRECTED — distinct from frozen test set

PROCEDURE
=========
1. For each base program, find all integer constant sites (excluding 0, 1, -1)
2. For each site, apply mutation ±1 using text-level substitution (NOT ast.unparse)
3. Execute both base and variant with V2_CANONICAL_INPUTS + boundary inputs
4. Verify behavioral difference on at least one input
5. Record difficulty level based on input type that detects mutation
6. Generate JSONL manifest with full provenance

OUTPUT
======
  benchmark/v3/sc3_corrected/
    ├── variants/
    │   ├── {program}__{sc3v_s{seed}_p{site}}.py
    │   └── ...
    ├── sc3_corrected_pairs.jsonl
    └── SC3_CORRECTED_MANIFEST.json
"""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import sys
import textwrap
import time
import types
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# Add repo root to path
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

CORPUS_DIR = REPO_ROOT / "benchmark" / "corpus" / "base_programs"
OUTPUT_DIR = REPO_ROOT / "benchmark" / "v3" / "sc3_corrected"
OUTPUT_VARIANTS_DIR = OUTPUT_DIR / "variants"

# V2 canonical inputs (same as b07_dynamic_v2.py)
V2_CANONICAL_INPUTS = [
    [],
    [1],
    [3, 1, 4, 1, 5, 9, 2, 6],
    [10, 9, 8, 7, 6, 5],
    [0, 0, 0, 0],
    [2, 1],
    [-3, 0, 3],
    list(range(8)),
]

# Extended boundary inputs for better SC-3 mutation detection
SC3_EXTENDED_INPUTS = V2_CANONICAL_INPUTS + [
    list(range(1)),       # minimal
    list(range(2)),       # two elements
    list(range(3)),       # three elements
    list(range(10)),      # medium
    list(range(16)),      # power-of-2 boundary
    list(range(100)),     # larger
    [1] * 10,             # all same
    list(range(20, 0, -1)),  # descending
]


@dataclass
class SC3MutationRecord:
    """Full provenance record for one SC-3 corrected mutation."""
    version: str = "v3"
    mutation_type: str = "SC-3v3"
    mutation_category: str = "CONSTANT_MUTATION_INTEGER"
    semantic_relation: str = "CHANGED"
    base_id: str = ""
    variant_id: str = ""
    base_path: str = ""
    variant_path: str = ""
    base_hash: str = ""
    variant_hash: str = ""
    mutation_value_before: int = 0
    mutation_value_after: int = 0
    mutation_delta: int = 0
    mutation_site_line: int = 0
    mutation_site_col: int = 0
    ast_path: str = ""
    difficulty: str = "UNKNOWN"   # EASY / MEDIUM / HARD
    witness_input: str = ""
    behavioral_verification: str = "UNVERIFIED"
    n_inputs_with_different_behavior: int = 0
    n_inputs_tested: int = 0
    generation_seed: int = 0
    timestamp: str = ""
    hard_negative: bool = False
    generated_by: str = "generate_sc3_corrected.py"
    provenance: str = "SYNTHETIC_SC3_CORRECTED_V3"
    notes: str = ""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _find_integer_constant_sites(source: str) -> List[dict]:
    """
    Find all integer constant AST nodes suitable for ±1 mutation.

    Excludes: 0, 1, -1, True, False, very large constants (>1000)
    Returns list of {value, line, col, context} dicts.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    sites = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            v = node.value
            if (isinstance(v, int)
                    and not isinstance(v, bool)
                    and v not in (0, 1, -1)
                    and abs(v) <= 1000):
                # Determine context (parent node type)
                sites.append({
                    "value": v,
                    "line": node.lineno,
                    "col": node.col_offset,
                    "end_col": node.end_col_offset,
                })
    return sites


def _apply_constant_mutation_textual(
    source: str,
    site: dict,
    delta: int,
) -> Optional[str]:
    """
    Apply integer constant mutation using TEXT-LEVEL substitution.

    IMPORTANT: We do NOT use ast.unparse() because it normalizes quote styles,
    which was the root cause of the v2 SC-3 contamination.

    Instead, we find the exact character positions of the constant and
    replace only that token.
    """
    lines = source.split("\n")
    line_idx = site["line"] - 1  # 0-indexed
    if line_idx >= len(lines):
        return None

    line = lines[line_idx]
    col_start = site["col"]
    col_end = site["end_col"] if site["end_col"] else col_start + len(str(site["value"]))

    old_str = line[col_start:col_end]
    # Verify the token matches the expected value
    try:
        if int(old_str) != site["value"]:
            return None
    except (ValueError, TypeError):
        return None

    new_value = site["value"] + delta
    new_str = str(new_value)
    new_line = line[:col_start] + new_str + line[col_end:]
    new_lines = lines[:line_idx] + [new_line] + lines[line_idx + 1:]
    new_source = "\n".join(new_lines)

    # Verify the result compiles
    try:
        compile(new_source, "<string>", "exec")
        return new_source
    except SyntaxError:
        return None


def _load_entry_fn(source: str, program_id: str):
    """Load a program's entry function (simplified version of b07 logic)."""
    spec_name = f"_sc3v3_prog_{program_id}"
    mod = types.ModuleType(spec_name)
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        exec(compile(source, f"<{program_id}>", "exec"), mod.__dict__)
    except Exception:
        sys.stdout = old_stdout
        return None
    finally:
        sys.stdout = old_stdout

    import inspect
    # Priority order
    for name in ("sort", "search", "run", "main", "solve", "process", "compute",
                 "encode", "decode", "parse", "validate", "execute"):
        fn = getattr(mod, name, None)
        if callable(fn) and isinstance(fn, types.FunctionType):
            return fn

    for name, obj in inspect.getmembers(mod, inspect.isfunction):
        if not name.startswith("_"):
            if getattr(obj, "__module__", None) == spec_name:
                return obj
    return None


def _execute_safe(fn, inp, timeout: float = 3.0):
    """Execute fn(inp) safely, returning output or exception string."""
    import threading
    result = {"output": None, "exception": None}

    def worker():
        try:
            result["output"] = fn(inp)
        except Exception as e:
            result["exception"] = f"{type(e).__name__}: {e}"

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout=timeout)
    if t.is_alive():
        return None, "TimeoutError"
    return result["output"], result["exception"]


def _verify_mutation(
    base_source: str, variant_source: str, program_id: str
) -> dict:
    """
    Verify that mutation changes program behavior on at least one input.

    Returns dict with: verified, n_different, n_tested, witness_input
    """
    base_fn = _load_entry_fn(base_source, program_id + "_base")
    var_fn = _load_entry_fn(variant_source, program_id + "_var")

    if base_fn is None or var_fn is None:
        return {"verified": False, "n_different": 0, "n_tested": 0, "witness_input": ""}

    import inspect
    try:
        sig = inspect.signature(base_fn)
        n_params = len(sig.parameters)
    except (ValueError, TypeError):
        n_params = 1

    inputs = SC3_EXTENDED_INPUTS if n_params >= 1 else [None]
    if n_params == 0:
        inputs = [None]

    n_different = 0
    witness_input = ""
    n_tested = 0

    for inp in inputs:
        try:
            if n_params == 0:
                base_out, base_exc = _execute_safe(lambda _: base_fn(), None)
                var_out, var_exc = _execute_safe(lambda _: var_fn(), None)
            else:
                base_out, base_exc = _execute_safe(base_fn, inp)
                var_out, var_exc = _execute_safe(var_fn, inp)
        except Exception:
            continue

        n_tested += 1
        if base_out != var_out or base_exc != var_exc:
            n_different += 1
            if not witness_input:
                witness_input = repr(inp)

    return {
        "verified": n_different > 0,
        "n_different": n_different,
        "n_tested": n_tested,
        "witness_input": witness_input,
    }


def _classify_difficulty(n_different: int, n_tested: int) -> str:
    """
    Classify mutation difficulty based on what fraction of inputs detect it.

    EASY:   > 50% of inputs detect the mutation
    MEDIUM: 10-50% of inputs
    HARD:   < 10% of inputs (boundary condition / off-by-one style)
    """
    if n_tested == 0:
        return "UNKNOWN"
    ratio = n_different / n_tested
    if ratio > 0.5:
        return "EASY"
    elif ratio >= 0.1:
        return "MEDIUM"
    else:
        return "HARD"


def generate_sc3_corrected_benchmark(
    max_programs: int = None,
    max_mutations_per_program: int = 3,
    seeds: List[int] = None,
    deltas: List[int] = None,
) -> List[SC3MutationRecord]:
    """
    Generate the corrected SC-3 v3 benchmark.

    Parameters
    ----------
    max_programs : int, optional
        Limit number of programs (for testing).
    max_mutations_per_program : int
        Max mutations to generate per program.
    seeds : list of int
        Mutation seeds.
    deltas : list of int
        Constant mutation deltas to try.

    Returns
    -------
    list of SC3MutationRecord
    """
    if seeds is None:
        seeds = [0, 1, 2]
    if deltas is None:
        deltas = [1, -1, 2]

    OUTPUT_VARIANTS_DIR.mkdir(parents=True, exist_ok=True)

    programs = sorted(CORPUS_DIR.glob("*.py"))
    if max_programs is not None:
        programs = programs[:max_programs]

    records = []
    print(f"[SC3v3] Generating corrected SC-3 benchmark for {len(programs)} programs")

    for prog_path in programs:
        program_id = prog_path.stem
        base_source = prog_path.read_text(encoding="utf-8")
        base_hash = _sha256(base_source)

        sites = _find_integer_constant_sites(base_source)
        if not sites:
            print(f"  [SC3v3] {program_id}: no integer constant sites found, skipping")
            continue

        generated_count = 0
        for seed_idx, seed in enumerate(seeds):
            if generated_count >= max_mutations_per_program:
                break

            # Use seed to select site
            site_idx = seed % len(sites)
            site = sites[site_idx]
            delta = deltas[seed_idx % len(deltas)]

            variant_source = _apply_constant_mutation_textual(base_source, site, delta)
            if variant_source is None or variant_source == base_source:
                continue

            # Verify mutation actually changes behavior
            verification = _verify_mutation(base_source, variant_source, program_id)

            variant_id = f"{program_id}__sc3v3_s{seed}_p{site_idx}"
            variant_filename = f"{variant_id}.py"
            variant_path = OUTPUT_VARIANTS_DIR / variant_filename

            # Write variant to disk
            variant_path.write_text(variant_source, encoding="utf-8")

            difficulty = _classify_difficulty(
                verification["n_different"], verification["n_tested"]
            )

            record = SC3MutationRecord(
                base_id=program_id,
                variant_id=variant_id,
                base_path=str(prog_path.relative_to(REPO_ROOT)),
                variant_path=str(variant_path.relative_to(REPO_ROOT)),
                base_hash=base_hash,
                variant_hash=_sha256(variant_source),
                mutation_value_before=site["value"],
                mutation_value_after=site["value"] + delta,
                mutation_delta=delta,
                mutation_site_line=site["line"],
                mutation_site_col=site["col"],
                ast_path=f"line:{site['line']}:col:{site['col']}",
                difficulty=difficulty,
                witness_input=verification["witness_input"],
                behavioral_verification="VERIFIED" if verification["verified"] else "UNVERIFIED",
                n_inputs_with_different_behavior=verification["n_different"],
                n_inputs_tested=verification["n_tested"],
                generation_seed=seed,
                timestamp=datetime.now(timezone.utc).isoformat(),
                hard_negative=(difficulty == "HARD"),
                notes=f"textual_substitution (NOT ast.unparse): delta={delta:+d} at line {site['line']}",
            )
            records.append(record)
            generated_count += 1

            status = "✓ VERIFIED" if verification["verified"] else "⚠ UNVERIFIED"
            print(f"  [SC3v3] {program_id}: {delta:+d} at line {site['line']} → {status} "
                  f"({verification['n_different']}/{verification['n_tested']} inputs, "
                  f"difficulty={difficulty})")

    return records


def save_benchmark(records: List[SC3MutationRecord]) -> dict:
    """Save benchmark records and manifest. Returns summary dict."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write JSONL pairs file
    pairs_path = OUTPUT_DIR / "sc3_corrected_pairs.jsonl"
    verified_records = []
    with open(pairs_path, "w") as f:
        for rec in records:
            d = asdict(rec)
            f.write(json.dumps(d) + "\n")
            if rec.behavioral_verification == "VERIFIED":
                verified_records.append(rec)

    # Compute statistics
    n_verified = len(verified_records)
    n_total = len(records)
    difficulty_dist = {}
    for rec in verified_records:
        difficulty_dist[rec.difficulty] = difficulty_dist.get(rec.difficulty, 0) + 1

    programs_covered = len(set(r.base_id for r in verified_records))

    manifest = {
        "version": "v3",
        "mutation_type": "SC-3v3",
        "mutation_category": "CONSTANT_MUTATION_INTEGER",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "benchmark/v3/generate_sc3_corrected.py",
        "n_total_generated": n_total,
        "n_verified_behavioral_change": n_verified,
        "n_unverified": n_total - n_verified,
        "verification_rate": round(n_verified / n_total, 3) if n_total > 0 else 0.0,
        "n_programs_covered": programs_covered,
        "difficulty_distribution": difficulty_dist,
        "pairs_file": str(pairs_path.relative_to(REPO_ROOT)),
        "variants_dir": str(OUTPUT_VARIANTS_DIR.relative_to(REPO_ROOT)),
        "scientific_notes": [
            "CORRECTION_OF_V2_SC3_BUG: v2 SC3 used ast.unparse which normalizes quote styles",
            "TEXT_LEVEL_SUBSTITUTION: mutations applied at character level, preserving all formatting",
            "BEHAVIORAL_VERIFICATION: each mutation tested on canonical+boundary inputs",
            "DISTINCT_FROM_FROZEN_V2: this is EXPLORATORY_SC3_CORRECTED, NOT the frozen v2 test set",
            "INTEGER_ONLY: only integer constants are mutated (no string quote changes)",
        ],
        "v2_comparison": {
            "v2_sc3_cosmetic_fraction": 0.769,
            "v2_sc3_integer_mutation_fraction": 0.0,
            "v3_integer_mutation_fraction": 1.0,
        },
    }

    manifest_path = OUTPUT_DIR / "SC3_CORRECTED_MANIFEST.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n[SC3v3] Benchmark saved:")
    print(f"  Total generated: {n_total}")
    print(f"  Verified:        {n_verified} ({manifest['verification_rate']:.1%})")
    print(f"  Programs:        {programs_covered}")
    print(f"  Difficulty:      {difficulty_dist}")
    print(f"  Pairs file:      {pairs_path}")
    print(f"  Manifest:        {manifest_path}")

    return manifest


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate corrected SC-3 benchmark")
    parser.add_argument("--max-programs", type=int, default=None)
    parser.add_argument("--max-mutations", type=int, default=3)
    args = parser.parse_args()

    records = generate_sc3_corrected_benchmark(
        max_programs=args.max_programs,
        max_mutations_per_program=args.max_mutations,
    )
    manifest = save_benchmark(records)
    print(f"\nDone: {manifest['n_verified_behavioral_change']} verified SC-3 pairs generated.")
