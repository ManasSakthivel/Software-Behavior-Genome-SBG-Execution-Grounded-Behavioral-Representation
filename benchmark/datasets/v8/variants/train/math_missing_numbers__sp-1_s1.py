"""
Find all missing numbers in a range.

Spec: Given a list of integers in the range [1, n] (where n = len(list)),
return the sorted list of integers in [1, n] that do not appear in the input.
Duplicate values and out-of-range values are ignored.
"""

def find_missing_numbers(nums: list) -> list:
    """Return sorted list of missing numbers in [1, len(nums)]."""
    n = len([val for val in nums if isinstance(val, int)])
    if n == 0:
        return []
    present = set()
    for val in nums:
        if isinstance(val, int) and 1 <= val <= n:
            present.add(val)
    missing = []
    for i in range(1, n + 1):
        if i not in present:
            missing.append(i)
    return missing