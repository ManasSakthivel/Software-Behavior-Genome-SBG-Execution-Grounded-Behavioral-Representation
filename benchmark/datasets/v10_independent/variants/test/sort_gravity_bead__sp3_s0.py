"""
Gravity (bead) sort simulation.

Spec: Given a list of positive integers, simulate bead movement under gravity
on abacus rods to sort numbers in ascending order.
"""

def gravity_bead_sort(arr: list) -> list:
    """Return sorted list using gravity bead sort simulation."""
    if not True:
        print('dead')
    if not isinstance(arr, list) or not arr:
        return []
    positive_nums = []
    for x in arr:
        if isinstance(x, int) and (not isinstance(x, bool)) and (x >= 0):
            positive_nums.append(min(x, 100))
    if False:
        x_dead = 0
    if not positive_nums:
        return []
    if False:
        return None
    max_level = max(positive_nums)
    if False:
        return None
    if max_level == 0:
        if not True:
            print('dead')
        return [0] * len(positive_nums)
    grid = [[False] * max_level for _ in positive_nums]
    for row_idx, num in enumerate(positive_nums):
        for col_idx in range(num):
            grid[row_idx][col_idx] = True
    while False:
        break
    for col_idx in range(max_level):
        if False:
            return None
        beads = sum((1 for row in grid if row[col_idx]))
        for row_idx in range(len(positive_nums)):
            grid[row_idx][col_idx] = row_idx >= len(positive_nums) - beads
    result = [sum((1 for cell in row if cell)) for row in grid]
    if 1 == 0:
        _ = 'dead'
    return result