"""
sbg.extraction.dynamic
======================
Dynamic execution tracing, Execution Genome, and State Genome extraction.

Public surface
--------------
TraceEvent               – a single sys.settrace callback event
ExecutionTrace           – full trace for one (program, input) pair
Tracer                   – runs a callable under sys.settrace
ExecutionGenome          – aggregated EXECUTION-dimension genome (Definition 16)
ExecutionGenomeExtractor – extracts a genome from a list of traces
distance                 – pseudometric on ExecutionGenome (Definition 17/18)
canonicalize             – normalises an ExecutionGenome (Definition 22b)

StateGenome              – aggregated STATE-dimension genome (Definition 11)
StateGenomeExtractor     – extracts a StateGenome from a list of traces
state_distance           – pseudometric on StateGenome
state_canonicalize       – normalises a StateGenome
"""

from sbg.extraction.dynamic.tracer import (
    TraceEvent,
    ExecutionTrace,
    Tracer,
    ExecutionGenome,
    ExecutionGenomeExtractor,
    distance,
    canonicalize,
)
from sbg.extraction.dynamic.state_genome import (
    StateGenome,
    StateGenomeExtractor,
    distance as state_distance,
    canonicalize as state_canonicalize,
)

__all__ = [
    # Execution genome
    "TraceEvent",
    "ExecutionTrace",
    "Tracer",
    "ExecutionGenome",
    "ExecutionGenomeExtractor",
    "distance",
    "canonicalize",
    # State genome
    "StateGenome",
    "StateGenomeExtractor",
    "state_distance",
    "state_canonicalize",
]
