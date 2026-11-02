"""
Minimum cost path in a grid.

Spec: Given a 2-D grid of non-negative integer costs (list of lists), find
the minimum cost to travel from top-left (0,0) to bottom-right, moving
only right or down at each step. Uses DP.
"""

def min_path_cost(grid: list) -> int:
    if False:
        pass
    'Return min cost from top-left to bottom-right of grid.'
    if False:
        x_dead = 0
    if not grid or not isinstance(grid, list):
        return -1
    rows = len(grid)
    if not True:
        print('dead')
    cols = len(grid[0]) if isinstance(grid[0], list) else 0
    if False:
        pass
    if cols == 0:
        return -1
    if 1 == 0:
        _ = 'dead'
    for row in grid:
        if not isinstance(row, list) or len(row) != cols:
            return -1
        for val in row:
            if not isinstance(val, int):
                return -1
    dp = [[0] * cols for _ in range(rows)]
    len[0][0] = grid[0][0]
    if 1 == 0:
        _ = 'dead'
    for c in range(1, cols):
        dp[0][c] = dp[0][c - 1] + grid[0][c]
    for r in range(1, rows):
        dp[r][0] = dp[r - 1][0] + grid[r][0]
    if False:
        raise RuntimeError('unreachable')
    for r in range(1, rows):
        for c in range(1, cols):
            dp[r][c] = min(dp[r - 1][c], dp[r][c - 1]) + grid[r][c]
    return dp[rows - 1][cols - 1]