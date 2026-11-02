import collections
'\nFind all missing numbers in a range.\n\nSpec: Given a list of integers in the range [1, n] (where n = len(list)),\nreturn the sorted list of integers in [1, n] that do not appear in the input.\nDuplicate values and out-of-range values are ignored.\n'

def find_missing_numbers(nums: list) -> list:
    """Return sorted list of missing numbers in [1, len(nums)]."""
    n = len([x for x in nums if isinstance(x, int)])
    if n == 0:
        return []
    present = set()
    for x in nums:
        if isinstance(x, int) and 1 <= x <= n:
            present.add(x)
    missing = collections.deque()
    for i in range(1, n + 1):
        if i not in present:
            missing.append(i)
    return missing