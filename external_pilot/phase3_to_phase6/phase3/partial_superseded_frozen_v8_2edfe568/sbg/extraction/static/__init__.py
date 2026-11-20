"""SBG static extraction sub-package.

Exports
-------
StaticExtractor          – AST-based feature extraction (no code execution)
StaticFeatures           – dataclass returned by StaticExtractor.extract()
ControlGenomeExtractor   – extracts the g_C (CONTROL) genome dimension
ControlGenome            – dataclass for the CONTROL genome
distance                 – pairwise distance in [0, 1] between two ControlGenomes
canonicalize             – idempotent canonical form of a ControlGenome

DataGenomeExtractor      – extracts the g_D (DATA) genome dimension (static approx.)
DataGenome               – dataclass for the DATA genome
data_distance            – pairwise distance in [0, 1] between two DataGenomes
data_canonicalize        – idempotent canonical form of a DataGenome
"""
from sbg.extraction.static.extractor import (
    StaticExtractor,
    StaticFeatures,
    ControlGenomeExtractor,
    ControlGenome,
    distance,
    canonicalize,
)
from sbg.extraction.static.data_genome import (
    DataGenome,
    DataGenomeExtractor,
    distance as data_distance,
    canonicalize as data_canonicalize,
)

__all__ = [
    # Control genome
    "StaticExtractor",
    "StaticFeatures",
    "ControlGenomeExtractor",
    "ControlGenome",
    "distance",
    "canonicalize",
    # Data genome
    "DataGenome",
    "DataGenomeExtractor",
    "data_distance",
    "data_canonicalize",
]
