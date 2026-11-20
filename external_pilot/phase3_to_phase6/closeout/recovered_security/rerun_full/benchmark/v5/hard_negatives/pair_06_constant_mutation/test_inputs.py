"""
Test inputs for pair 06.
Each input is (sorted_array, target).
Absent-target cases expose the -1 vs len(arr) sentinel divergence.
"""

TEST_INPUTS = [
    # Target present — both agree
    ([1, 3, 5, 7, 9], 5),
    ([1, 3, 5, 7, 9], 1),
    ([1, 3, 5, 7, 9], 9),
    ([42], 42),
    ([2, 4, 6, 8], 6),
    ([2, 4, 6, 8], 8),
    # Target absent — DIVERGE: base returns -1, variant returns len(arr)
    ([1, 3, 5, 7, 9], 4),
    ([1, 2], 3),
    ([2, 4, 6, 8], 1),
    ([42], 0),
]
