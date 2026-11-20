"""benchmark/ground_truth — SBG ground-truth validation package."""

from .validator import (
    DifferentialResult,
    DifferentialTester,
    GroundTruthRecord,
    GroundTruthValidator,
    InputGenerator,
    PairValidator,
    ProgramSpec,
)

__all__ = [
    "DifferentialResult",
    "DifferentialTester",
    "GroundTruthRecord",
    "GroundTruthValidator",
    "InputGenerator",
    "PairValidator",
    "ProgramSpec",
]
