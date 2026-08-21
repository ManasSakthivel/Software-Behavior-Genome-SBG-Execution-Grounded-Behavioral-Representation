#!/usr/bin/env python3
"""
sbg/cli.py
===========
SBG command-line interface.

Commands:
  extract  <program.py> [--output genome.json]
  compare  <genome_a.json> <genome_b.json> [--dimensions CONTROL DATA ERROR]
  validate <genome.json>

Usage:
  python3 -m sbg.cli extract myprogram.py
  python3 -m sbg.cli compare a.json b.json
  python3 -m sbg.cli validate genome.json
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Make sure sbg is importable when called as a module
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from sbg.serialization import GenomeBundle, GenomeBundleSerializer, ProvenanceTracker
from sbg.extraction.static.extractor import ControlGenomeExtractor, canonicalize as canon_control
from sbg.extraction.static.data_genome import DataGenomeExtractor, canonicalize as canon_data
from sbg.extraction.static.error_genome import ErrorGenomeExtractor, canonicalize as canon_error
import dataclasses


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _to_dict(obj) -> dict:
    """Convert a dataclass to a plain dict (JSON-safe)."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    return obj if isinstance(obj, dict) else {}


# ---------------------------------------------------------------------------
# extract
# ---------------------------------------------------------------------------

def cmd_extract(args) -> int:
    src_path = Path(args.program)
    if not src_path.exists():
        print(f"ERROR: File not found: {src_path}", file=sys.stderr)
        return 1

    source = src_path.read_text(encoding="utf-8")
    prog_id = src_path.stem

    # Extract static genomes only (MVP — no dynamic tracing required)
    try:
        ctrl = ControlGenomeExtractor().extract(source)
        ctrl = canon_control(ctrl)
    except Exception as e:
        print(f"WARNING: CONTROL extraction failed: {e}", file=sys.stderr)
        ctrl = None

    try:
        data = DataGenomeExtractor().extract(source)
        data = canon_data(data)
    except Exception as e:
        print(f"WARNING: DATA extraction failed: {e}", file=sys.stderr)
        data = None

    try:
        error = ErrorGenomeExtractor().extract(source)
        error = canon_error(error)
    except Exception as e:
        print(f"WARNING: ERROR extraction failed: {e}", file=sys.stderr)
        error = None

    genomes = {}
    if ctrl is not None:
        genomes["CONTROL"] = _to_dict(ctrl)
    if data is not None:
        genomes["DATA"] = _to_dict(data)
    if error is not None:
        genomes["ERROR"] = _to_dict(error)

    provenance = ProvenanceTracker.create_provenance(
        source_file=str(src_path),
        inputs=[],
        n_traces=0,
        flags={"static_only": True},
    )

    bundle = GenomeBundle(
        program_id=prog_id,
        source_hash=_sha256(source),
        extraction_timestamp=datetime.now(timezone.utc).isoformat(),
        genomes=genomes,
        provenance=provenance,
        metadata={"source_lines": len(source.splitlines())},
    )

    output = GenomeBundleSerializer.to_json(bundle)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        print(f"Genome written to: {out_path}", file=sys.stderr)
    else:
        print(output)

    return 0


# ---------------------------------------------------------------------------
# compare
# ---------------------------------------------------------------------------

def cmd_compare(args) -> int:
    try:
        bundle_a = GenomeBundleSerializer.load(args.genome_a)
        bundle_b = GenomeBundleSerializer.load(args.genome_b)
    except Exception as e:
        print(f"ERROR loading genome: {e}", file=sys.stderr)
        return 1

    dims = args.dimensions if args.dimensions else list(bundle_a.genomes.keys())

    from sbg.distance import behavioral_distance, DEFAULT_WEIGHTS

    # Convert dict genomes back into dataclass instances for distance computation
    # For the CLI MVP, we work at the dict level using a simple distance proxy
    def dict_l1(d1: dict, d2: dict) -> float:
        """Simple symmetric L1 distance between two flat dicts."""
        keys = set(d1) | set(d2)
        total = 0.0
        for k in keys:
            v1 = float(d1.get(k, 0))
            v2 = float(d2.get(k, 0))
            total += abs(v1 - v2)
        norm = max(sum(abs(float(v)) for v in d1.values()) +
                   sum(abs(float(v)) for v in d2.values()), 1.0)
        return min(total / norm, 1.0)

    dimension_distances = {}
    for dim in dims:
        g_a = bundle_a.genomes.get(dim)
        g_b = bundle_b.genomes.get(dim)
        if g_a is None or g_b is None:
            dimension_distances[dim] = None
            continue
        # Use simple flat-dict L1 distance as proxy (full distance requires dataclass instances)
        flat_a = {k: v for k, v in (g_a if isinstance(g_a, dict) else {}).items()
                  if isinstance(v, (int, float))}
        flat_b = {k: v for k, v in (g_b if isinstance(g_b, dict) else {}).items()
                  if isinstance(v, (int, float))}
        dimension_distances[dim] = dict_l1(flat_a, flat_b)

    active = {k: v for k, v in dimension_distances.items() if v is not None}
    if active:
        weights = {k: DEFAULT_WEIGHTS.get(k, 1.0 / len(active)) for k in active}
        w_sum = sum(weights.values())
        total_distance = sum(weights[k] * active[k] for k in active) / w_sum
    else:
        total_distance = 0.0

    result = {
        "program_a": bundle_a.program_id,
        "program_b": bundle_b.program_id,
        "total_distance": round(total_distance, 6),
        "dimension_distances": {k: (round(v, 6) if v is not None else None)
                                  for k, v in dimension_distances.items()},
        "dimensions_compared": list(active.keys()),
        "missing_dimensions": [k for k, v in dimension_distances.items() if v is None],
    }
    print(json.dumps(result, indent=2))
    return 0


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

def cmd_validate(args) -> int:
    try:
        bundle = GenomeBundleSerializer.load(args.genome)
    except Exception as e:
        print(f"ERROR: Cannot load {args.genome}: {e}", file=sys.stderr)
        return 1

    issues = []
    required_fields = ["program_id", "source_hash", "extraction_timestamp",
                       "genome_version", "genomes", "provenance"]
    d = GenomeBundleSerializer.to_dict(bundle)
    for field in required_fields:
        if field not in d or d[field] is None:
            issues.append(f"Missing required field: {field}")

    expected_dims = ["CONTROL", "DATA", "STATE", "RESOURCE", "TEMPORAL",
                     "ERROR", "INTERACTION", "EXECUTION"]
    present_dims = list(bundle.genomes.keys())
    missing_dims = [d for d in expected_dims if d not in present_dims]

    result = {
        "program_id": bundle.program_id,
        "genome_version": bundle.genome_version,
        "present_dimensions": present_dims,
        "missing_dimensions": missing_dims,
        "field_issues": issues,
        "valid": len(issues) == 0,
    }
    print(json.dumps(result, indent=2))
    return 0 if len(issues) == 0 else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="sbg",
        description="SBG — Software Behavior Genome CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    # extract
    p_extract = subparsers.add_parser("extract", help="Extract genome from a Python program")
    p_extract.add_argument("program", help="Path to Python source file")
    p_extract.add_argument("--output", "-o", help="Output JSON file (default: stdout)")

    # compare
    p_compare = subparsers.add_parser("compare", help="Compare two genome bundles")
    p_compare.add_argument("genome_a", help="First genome JSON file")
    p_compare.add_argument("genome_b", help="Second genome JSON file")
    p_compare.add_argument("--dimensions", nargs="+",
                           help="Dimensions to compare (default: all present)")

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate a genome bundle")
    p_validate.add_argument("genome", help="Genome JSON file to validate")

    args = parser.parse_args(argv)

    if args.command == "extract":
        return cmd_extract(args)
    elif args.command == "compare":
        return cmd_compare(args)
    elif args.command == "validate":
        return cmd_validate(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
