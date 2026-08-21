"""
Test inputs for pair 08.
Each input is (list, i, j). i != j cases expose the non-swap.
"""

TEST_INPUTS = [
    ([1, 2, 3], 0, 1),
    ([1, 2, 3], 0, 2),
    ([1, 2, 3], 1, 2),
    ([10, 20, 30, 40], 0, 3),
    # i == j: both programs are equivalent for this edge case
    ([5, 6, 7], 1, 1),
    ([1], 0, 0),
]
