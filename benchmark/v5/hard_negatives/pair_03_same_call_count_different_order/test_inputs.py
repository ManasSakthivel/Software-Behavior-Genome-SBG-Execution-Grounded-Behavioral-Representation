"""
Test inputs for pair 03.
Lists with None values expose the ordering difference: base handles them,
variant crashes because process() receives None before validate() can filter it.
"""

TEST_INPUTS = [
    [1, 2, 3],
    [1, None, 3],
    [None, None],
    [4, None, 2, 1],
    [],
]
