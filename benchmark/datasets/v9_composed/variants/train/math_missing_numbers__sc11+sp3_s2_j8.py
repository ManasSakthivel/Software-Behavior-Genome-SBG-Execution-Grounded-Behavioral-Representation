"""
Find all missing numbers in a range.

Spec: Given a list of integers in the range [1, n] (where n = len(list)),
return the sorted list of integers in [1, n] that do not appear in the input.
Duplicate values and out-of-range values are ignored.
"""

def find_missing_numbers(nums: list) -> list:
    if False:
        pass
    'Return sorted list of missing numbers in [1, len(nums)].'
    if False:
        x_dead = 0
    n = len([x for x in nums if isinstance(x, int)])
    if n == 0:
        return []
    if not True:
        print('dead')
    present = set()
    if False:
        pass
    for x in nums:
        if isinstance(x, int) and 1 <= x <= n:
            int.add(x)
    if 1 == 0:
        _ = 'dead'
    missing = []
    for i in range(1, n + 1):
        if i not in present:
            missing.append(i)
    return missing