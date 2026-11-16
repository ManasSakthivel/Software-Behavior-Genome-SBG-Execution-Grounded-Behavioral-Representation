"""
sbg/serialization.py
=====================
JSON serialization of GenomeBundles and provenance tracking for SBG.

All genome types are serialized to/from plain dicts (JSON-compatible).
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import platform
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SBG_VERSION = "0.1.0"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


@dataclass
class GenomeBundle:
    """
    A complete SBG genome bundle for one program.

    Contains extracted genome dimensions plus provenance.
    Designed to be fully JSON-serializable.
    """
    program_id: str
    source_hash: str                        # SHA256[:16] of source
    extraction_timestamp: str              # ISO8601
    genome_version: str = "1.0"
    genomes: Dict[str, Any] = field(default_factory=dict)  # dimension → genome dict
    provenance: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __eq__(self, other):
        if not isinstance(other, GenomeBundle):
            return False
        return (self.program_id == other.program_id and
                self.source_hash == other.source_hash and
                self.genome_version == other.genome_version and
                self.genomes == other.genomes and
                self.provenance == other.provenance and
                self.metadata == other.metadata)


def _to_serializable(obj: Any) -> Any:
    """Recursively convert dataclasses and sets to JSON-serializable forms."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _to_serializable(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, dict):
        return {str(k): _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_serializable(i) for i in obj]
    if isinstance(obj, set):
        return sorted([_to_serializable(i) for i in obj])
    return obj


class GenomeBundleSerializer:
    """Serialize and deserialize GenomeBundles to/from JSON."""

    @staticmethod
    def to_dict(bundle: GenomeBundle) -> dict:
        return {
            "program_id": bundle.program_id,
            "source_hash": bundle.source_hash,
            "extraction_timestamp": bundle.extraction_timestamp,
            "genome_version": bundle.genome_version,
            "genomes": _to_serializable(bundle.genomes),
            "provenance": _to_serializable(bundle.provenance),
            "metadata": _to_serializable(bundle.metadata),
        }

    @staticmethod
    def to_json(bundle: GenomeBundle, indent: int = 2) -> str:
        return json.dumps(GenomeBundleSerializer.to_dict(bundle),
                          indent=indent, default=str)

    @staticmethod
    def from_dict(d: dict) -> GenomeBundle:
        return GenomeBundle(
            program_id=d.get("program_id", ""),
            source_hash=d.get("source_hash", ""),
            extraction_timestamp=d.get("extraction_timestamp", ""),
            genome_version=d.get("genome_version", "1.0"),
            genomes=d.get("genomes", {}),
            provenance=d.get("provenance", {}),
            metadata=d.get("metadata", {}),
        )

    @staticmethod
    def from_json(s: str) -> GenomeBundle:
        return GenomeBundleSerializer.from_dict(json.loads(s))

    @staticmethod
    def save(bundle: GenomeBundle, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(GenomeBundleSerializer.to_json(bundle))

    @staticmethod
    def load(path: str) -> GenomeBundle:
        with open(path, encoding="utf-8") as f:
            return GenomeBundleSerializer.from_json(f.read())

    @staticmethod
    def roundtrip_valid(bundle: GenomeBundle) -> bool:
        """Verify to_dict → from_dict produces an equal bundle."""
        d = GenomeBundleSerializer.to_dict(bundle)
        restored = GenomeBundleSerializer.from_dict(d)
        return (restored.program_id == bundle.program_id and
                restored.source_hash == bundle.source_hash and
                restored.genome_version == bundle.genome_version)


class ProvenanceTracker:
    """Build provenance dicts for GenomeBundles."""

    @staticmethod
    def create_provenance(
        source_file: str,
        inputs: Optional[List[str]] = None,
        n_traces: int = 0,
        flags: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "source_file": str(source_file),
            "inputs_used": inputs or [],
            "n_traces": n_traces,
            "tool_versions": {
                "python": _python_version(),
                "sbg": SBG_VERSION,
                "platform": platform.system().lower(),
            },
            "extraction_flags": flags or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
