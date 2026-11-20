"""
sbg.canonicalization
=====================
Master canonicalization module for the SBG project.

Provides a unified ``canonicalize(genome)`` dispatcher and a
``canonicalize_all(full_genome)`` batch function that operates on the
8-dimensional genome dictionary.

Formal grounding
----------------
* canonicalize    ↔  𝒞_ε / 𝒩_dist  (Definition 22, FORMAL_MODEL.md)
* GENOME_REGISTRY maps dimension keys to (GenomeType, canonicalize_fn) pairs.

Design
------
Each genome module exposes a ``canonicalize`` function that accepts a genome
of its own type and returns a canonical form of the same type.  This module
imports all eight and provides a single dispatch function so callers do not
need to know the type at the call site.

Usage
-----
    from sbg.canonicalization import canonicalize, canonicalize_all

    c_genome = canonicalize(my_control_genome)   # ControlGenome → ControlGenome
    full     = canonicalize_all(full_genome_dict) # all 8 dimensions in one call

Constraints
-----------
* No third-party imports.
* canonicalize is idempotent: canonicalize(canonicalize(g)) == canonicalize(g)
  for every dimension (guaranteed by each module's own implementation).
"""

from __future__ import annotations

from typing import Any, Dict

from sbg.extraction.static.extractor import (
    ControlGenome,
    canonicalize as canon_control,
)
from sbg.extraction.static.data_genome import (
    DataGenome,
    canonicalize as canon_data,
)
from sbg.extraction.static.error_genome import (
    ErrorGenome,
    canonicalize as canon_error,
)
from sbg.extraction.dynamic.tracer import (
    ExecutionGenome,
    canonicalize as canon_exec,
)
from sbg.extraction.dynamic.state_genome import (
    StateGenome,
    canonicalize as canon_state,
)
from sbg.extraction.dynamic.resource_genome import (
    ResourceGenome,
    canonicalize as canon_resource,
)
from sbg.extraction.dynamic.temporal_genome import (
    TemporalGenome,
    canonicalize as canon_temporal,
)
from sbg.extraction.dynamic.interaction_genome import (
    InteractionGenome,
    canonicalize as canon_interaction,
)


# ---------------------------------------------------------------------------
# GENOME_REGISTRY
# ---------------------------------------------------------------------------

GENOME_REGISTRY: Dict[str, tuple] = {
    "CONTROL":     (ControlGenome,     canon_control),
    "DATA":        (DataGenome,        canon_data),
    "STATE":       (StateGenome,       canon_state),
    "RESOURCE":    (ResourceGenome,    canon_resource),
    "TEMPORAL":    (TemporalGenome,    canon_temporal),
    "ERROR":       (ErrorGenome,       canon_error),
    "INTERACTION": (InteractionGenome, canon_interaction),
    "EXECUTION":   (ExecutionGenome,   canon_exec),
}


# ---------------------------------------------------------------------------
# canonicalize — single-genome dispatcher
# ---------------------------------------------------------------------------

def canonicalize(genome: Any) -> Any:
    """
    Return the canonical form of *genome*.

    Dispatches to the correct per-dimension ``canonicalize`` function based
    on the runtime type of *genome*.

    Parameters
    ----------
    genome : any genome type
        An instance of one of the 8 genome classes registered in
        GENOME_REGISTRY.

    Returns
    -------
    Same type as *genome*, in canonical form.

    Raises
    ------
    TypeError
        When *genome* is not a recognised genome type.
    """
    for _dim, (genome_cls, canon_fn) in GENOME_REGISTRY.items():
        if isinstance(genome, genome_cls):
            return canon_fn(genome)

    raise TypeError(
        f"canonicalize: unrecognised genome type {type(genome).__name__!r}. "
        f"Registered types: "
        f"{', '.join(cls.__name__ for cls, _ in GENOME_REGISTRY.values())}"
    )


# ---------------------------------------------------------------------------
# canonicalize_all — full-genome batch canonicalization
# ---------------------------------------------------------------------------

def canonicalize_all(full_genome: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply canonicalization to every dimension present in *full_genome*.

    Parameters
    ----------
    full_genome : dict
        Mapping of dimension key → genome instance.  Keys should be a subset
        of GENOME_REGISTRY keys (e.g. ``"CONTROL"``, ``"DATA"``, …).
        Unknown keys are passed through unchanged with a warning marker.

    Returns
    -------
    dict
        New dict with the same keys; each recognised dimension value is
        replaced by its canonical form.  Unrecognised values are kept as-is.

    Notes
    -----
    * This function does **not** require all 8 dimensions to be present; it
      canonicalizes whatever is available.
    * canonicalize_all is idempotent:
          canonicalize_all(canonicalize_all(g)) == canonicalize_all(g)
    """
    result: Dict[str, Any] = {}
    for key, genome in full_genome.items():
        if key in GENOME_REGISTRY:
            _cls, canon_fn = GENOME_REGISTRY[key]
            result[key] = canon_fn(genome)
        else:
            # Unknown dimension: pass through unchanged
            result[key] = genome
    return result
