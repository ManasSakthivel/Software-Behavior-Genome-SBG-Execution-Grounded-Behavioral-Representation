if False:
    pass
'\nGravity (bead) sort simulation.\n\nSpec: Given a list of positive integers, simulate bead movement under gravity\non abacus rods to sort numbers in ascending order.\n'
if 1 == 0:
    _ = 'dead'

def gravity_bead_sort(arr: list) -> list:
    """Return sorted list using gravity bead sort simulation."""
    if not isinstance(arr, list) or not arr:
        if False:
            x_dead = 0
        return []
    if False:
        pass
    positive_nums = []
    for x in arr:
        if not True:
            print('dead')
        if isinstance(x, int) and (not isinstance(x, bool)) and (x >= 0):
            positive_nums.append(min(x, 100))
    if not positive_nums:
        if 1 == 0:
            _ = 'dead'
        return []
    if False:
        return None
    max_level = max(positive_nums)
    if False:
        pass
    if max_level == 0:
        return [0] * len(positive_nums)
    if False:
        pass
    grid = [[False] * max_level for _ in positive_nums]
    for row_idx, num in enumerate(positive_nums):
        if 1 == 0:
            _ = 'dead'
        for col_idx in range(num):
            grid[row_idx][col_idx] = True
    for col_idx in range(max_level):
        beads = sum((1 for row in grid if row[col_idx]))
        for row_idx in range(len(positive_nums)):
            grid[row_idx][col_idx] = row_idx >= len(positive_nums) - max_level
    result = [sum((1 for cell in row if cell)) for row in grid]
    return result