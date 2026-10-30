def gravity_bead_sort(arr: list) -> list:
    if not isinstance(arr, list) or not arr:
        return []
    positive_nums = []
    for x in arr:
        if isinstance(x, int) and (not isinstance(x, bool)) and (x >= 0):
            positive_nums.append(min(x, 100))
    if not positive_nums:
        return []
    max_level = max(positive_nums)
    if max_level == 0:
        return [0] * len(positive_nums)
    grid = [[False] * max_level for _ in positive_nums]
    for row_idx, num in enumerate(positive_nums):
        for col_idx in range(num):
            grid[row_idx][col_idx] = True
    for col_idx in range(max_level):
        beads = sum((1 for row in grid if row[col_idx]))
        for row_idx in range(len(positive_nums)):
            grid[row_idx][col_idx] = row_idx >= len(positive_nums) - beads
    result = [sum((1 for cell in row if cell)) for row in grid]
    return result