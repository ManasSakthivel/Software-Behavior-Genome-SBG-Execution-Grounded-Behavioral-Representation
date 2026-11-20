"""
Test inputs for pair 12.
Each input is a list of (op, *args) tuples.
Covers push, pop, peek, size, empty, and error paths.
"""

TEST_INPUTS = [
    # Basic push/pop
    [("push", 1), ("push", 2), ("pop",), ("size",)],
    # Peek without removal
    [("push", 10), ("peek",), ("peek",), ("pop",)],
    # Empty checks
    [("empty",), ("push", 5), ("empty",), ("pop",), ("empty",)],
    # Underflow errors
    [("pop",)],
    [("peek",)],
    # Sequence: push many, pop all
    [("push", i) for i in range(5)] + [("pop",) for _ in range(5)] + [("empty",)],
]
