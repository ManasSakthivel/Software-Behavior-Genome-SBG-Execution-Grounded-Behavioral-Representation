"""
Find all missing numbers in a range.

Spec: Given a list of integers in the range [1, n] (where n = len(list)),
return the sorted list of integers in [1, n] that do not appear in the input.
Duplicate values and out-of-range values are ignored.
"""

def find_missing_numbers(nums: list) -> list:
    """Return sorted list of missing numbers in [1, len(nums)]."""
    n = len([x for x in nums if isinstance(x, int)])
    if n == 0:
        return []
    present = set()
    for x in nums:
        if isinstance(x, int) and 1 <= x <= n:
            present.add(x)
    missing = []
    for idx in range(1, n + 1):
        if idx not in present:
            missing.append(idx)
    return missing