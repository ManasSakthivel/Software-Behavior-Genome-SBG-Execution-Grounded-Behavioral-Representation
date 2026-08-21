"""
benchmark/transformations/preserving/transformer.py

Central orchestrator for the semantics-PRESERVING transformation system (Agent 1B).

Public API
----------
apply_transformation(program_path, transformation_type, seed) -> (new_source, metadata)
generate_variant(program_path, transformation_type, seed) -> VariantRecord

VariantRecord shape
-------------------
{
    "base_id": "<stem of program file>",
    "variant_id": "<base_id>__<SP-X>__s<seed>",
    "transformation_type": "SP-X",
    "semantic_relation": "EQUIVALENT",
    "generator": "transformer.py",
    "seed": N,
    "expected_label": "EQUIVALENT"
}
"""

from __future__ import annotations

import ast
import hashlib
import json
import random
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple, Type

# ---------------------------------------------------------------------------
# Import all transformation classes
# ---------------------------------------------------------------------------
from benchmark.transformations.preserving.transformations.sp1_variable_rename import (
    VariableRenameTransformation,
)
from benchmark.transformations.preserving.transformations.sp2_function_rename import (
    FunctionRenameTransformation,
)
from benchmark.transformations.preserving.transformations.sp3_dead_code_insert import (
    DeadCodeInsertTransformation,
)
from benchmark.transformations.preserving.transformations.sp4_comment_strip import (
    CommentStripTransformation,
)
from benchmark.transformations.preserving.transformations.sp5_loop_rewrite import (
    LoopRewriteTransformation,
)
from benchmark.transformations.preserving.transformations.sp6_condition_rewrite import (
    ConditionRewriteTransformation,
)
from benchmark.transformations.preserving.transformations.sp7_inline_function import (
    InlineFunctionTransformation,
)
from benchmark.transformations.preserving.transformations.sp8_extract_function import (
    ExtractFunctionTransformation,
)
from benchmark.transformations.preserving.transformations.sp9_constant_fold import (
    ConstantFoldTransformation,
)
from benchmark.transformations.preserving.transformations.sp10_format_normalize import (
    FormatNormalizeTransformation,
)
from benchmark.transformations.preserving.transformations.sp11_equiv_data_structure import (
    EquivalentDataStructureTransformation,
)
from benchmark.transformations.preserving.transformations.sp12_algebraic_rewrite import (
    AlgebraicRewriteTransformation,
)

# ---------------------------------------------------------------------------
# Protocol / base type (duck-typed — no ABC to keep it lightweight)
# ---------------------------------------------------------------------------

class TransformationBase:
    """Informal protocol that every transformation class implements."""
    id: str        # e.g. "SP-1"
    name: str      # e.g. "VARIABLE_RENAME"

    def apply(self, source_code: str, seed: int) -> str:  # pragma: no cover
        raise NotImplementedError

    def validate(self, original: str, transformed: str) -> bool:  # pragma: no cover
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class TransformationRegistry:
    """
    Holds all registered transformation classes keyed by their ID (e.g. "SP-1")
    and also by their name (e.g. "VARIABLE_RENAME").
    """

    def __init__(self) -> None:
        self._by_id: Dict[str, TransformationBase] = {}
        self._by_name: Dict[str, TransformationBase] = {}

    def register(self, cls: Type) -> None:
        instance = cls()
        self._by_id[instance.id] = instance
        self._by_name[instance.name] = instance

    def get(self, key: str) -> Optional[TransformationBase]:
        """Look up by SP-X id or by name."""
        return self._by_id.get(key) or self._by_name.get(key.upper())

    def all_ids(self) -> list[str]:
        return sorted(self._by_id.keys())

    def __repr__(self) -> str:  # pragma: no cover
        return f"TransformationRegistry({list(self._by_id.keys())})"


# Build the global registry
registry = TransformationRegistry()
for _cls in [
    VariableRenameTransformation,
    FunctionRenameTransformation,
    DeadCodeInsertTransformation,
    CommentStripTransformation,
    LoopRewriteTransformation,
    ConditionRewriteTransformation,
    InlineFunctionTransformation,
    ExtractFunctionTransformation,
    ConstantFoldTransformation,
    FormatNormalizeTransformation,
    EquivalentDataStructureTransformation,
    AlgebraicRewriteTransformation,
]:
    registry.register(_cls)


# ---------------------------------------------------------------------------
# VariantRecord
# ---------------------------------------------------------------------------

@dataclass
class VariantRecord:
    base_id: str
    variant_id: str
    transformation_type: str
    semantic_relation: str
    generator: str
    seed: int
    expected_label: str
    # Optional provenance fields
    base_hash: str = ""
    variant_hash: str = ""
    transformed: bool = True
    timestamp: str = ""
    validation_passed: bool = False
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def _sha256_snippet(source: str) -> str:
    """Return first 16 hex chars of SHA-256 of source."""
    return hashlib.sha256(source.encode()).hexdigest()[:16]


def apply_transformation(
    program_path: str | Path,
    transformation_type: str,
    seed: int,
) -> Tuple[str, dict]:
    """
    Apply a single transformation to the source file at `program_path`.

    Parameters
    ----------
    program_path     : path to the source .py file
    transformation_type : SP-X id (e.g. "SP-1") or name (e.g. "VARIABLE_RENAME")
    seed             : integer seed for deterministic output

    Returns
    -------
    (new_source, metadata) where metadata is a plain dict with provenance info.

    Raises
    ------
    ValueError  if transformation_type is unknown
    FileNotFoundError if program_path does not exist
    """
    program_path = Path(program_path)
    if not program_path.exists():
        raise FileNotFoundError(f"Program not found: {program_path}")

    transformation = registry.get(transformation_type)
    if transformation is None:
        raise ValueError(
            f"Unknown transformation '{transformation_type}'. "
            f"Valid keys: {registry.all_ids()}"
        )

    source = program_path.read_text(encoding="utf-8")

    random.seed(seed)  # Belt-and-suspenders global seed
    new_source = transformation.apply(source, seed)

    validation_passed = transformation.validate(source, new_source)

    metadata = {
        "program_path": str(program_path),
        "transformation_id": transformation.id,
        "transformation_name": transformation.name,
        "seed": seed,
        "validation_passed": validation_passed,
        "base_hash": _sha256_snippet(source),
        "variant_hash": _sha256_snippet(new_source),
        "source_lines": source.count("\n") + 1,
        "variant_lines": new_source.count("\n") + 1,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    return new_source, metadata


def generate_variant(
    program_path: str | Path,
    transformation_type: str,
    seed: int,
) -> VariantRecord:
    """
    Apply a transformation and return a fully-populated VariantRecord.

    The transformed source is NOT written to disk by this function;
    call the returned record's `to_json()` and write it yourself,
    or use `write_variant()` below.
    """
    program_path = Path(program_path)
    base_id = program_path.stem  # e.g. "bubble_sort" from "bubble_sort.py"

    new_source, metadata = apply_transformation(program_path, transformation_type, seed)

    transformation = registry.get(transformation_type)
    assert transformation is not None  # already validated inside apply_transformation

    variant_id = f"{base_id}__{transformation.id.replace('-', '')}__s{seed}"

    return VariantRecord(
        base_id=base_id,
        variant_id=variant_id,
        transformation_type=transformation.id,
        semantic_relation="EQUIVALENT",
        generator="transformer.py",
        seed=seed,
        expected_label="EQUIVALENT",
        base_hash=metadata["base_hash"],
        variant_hash=metadata["variant_hash"],
        transformed=metadata["validation_passed"],
        timestamp=metadata["timestamp"],
        validation_passed=metadata["validation_passed"],
        notes=(
            ""
            if metadata["validation_passed"]
            else "WARNING: transformation did not change source (may be a no-op for this input)"
        ),
    )


def write_variant(
    program_path: str | Path,
    transformation_type: str,
    seed: int,
    output_dir: str | Path | None = None,
) -> Tuple[Path, Path, VariantRecord]:
    """
    Apply a transformation, write the transformed .py file and a JSON sidecar.

    Returns (variant_py_path, sidecar_json_path, variant_record).
    """
    program_path = Path(program_path)
    if output_dir is None:
        output_dir = program_path.parent / "variants"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    record = generate_variant(program_path, transformation_type, seed)
    new_source, _ = apply_transformation(program_path, transformation_type, seed)

    variant_py = output_dir / f"{record.variant_id}.py"
    variant_py.write_text(new_source, encoding="utf-8")

    sidecar = output_dir / f"{record.variant_id}.json"
    sidecar.write_text(record.to_json(), encoding="utf-8")

    return variant_py, sidecar, record
