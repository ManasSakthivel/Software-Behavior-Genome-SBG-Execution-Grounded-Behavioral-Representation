"""
Find all missing numbers in a range.

Spec: Given a list of integers in the range [1, n] (where n = len(list)),
return the sorted list of integers in [1, n] that do not appear in the input.
Duplicate values and out-of-range values are ignored.
"""

def _extracted_0_4(n, nums, present):
    for x in nums:
        if isinstance(x, int) and 1 <= x <= n:
            present.add(x)
    missing = []
    for i in range(1, n + 1):
        if i not in present:
            missing.append(i)
    return missing

def find_missing_numbers(nums: list) -> list:
    """Return sorted list of missing numbers in [1, len(nums)]."""
    n = len([x for x in nums if isinstance(x, int)])
    if n == 0:
        return []
    present = set()
    missing = _extracted_0_4(n, nums, present)
    return missing