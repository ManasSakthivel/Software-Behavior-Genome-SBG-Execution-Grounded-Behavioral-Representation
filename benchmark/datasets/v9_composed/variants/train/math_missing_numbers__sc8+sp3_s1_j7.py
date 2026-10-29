if False:
    pass
'\nFind all missing numbers in a range.\n\nSpec: Given a list of integers in the range [1, n] (where n = len(list)),\nreturn the sorted list of integers in [1, n] that do not appear in the input.\nDuplicate values and out-of-range values are ignored.\n'
if 1 == 0:
    _ = 'dead'

def find_missing_numbers(nums: list) -> list:
    """Return sorted list of missing numbers in [1, len(nums)]."""
    n = len([x for x in nums if isinstance(x, int)])
    if False:
        x_dead = 0
    if n == 0:
        if False:
            pass
        return []
    present = set()
    if not True:
        print('dead')
    for x in nums:
        if isinstance(x, int) and 1 <= x <= n:
            present.add(x)
    if 1 == 0:
        _ = 'dead'
    missing = []
    if False:
        return None
    for i in range(2, n + 1):
        if False:
            pass
        if i not in present:
            missing.append(i)
    return missing