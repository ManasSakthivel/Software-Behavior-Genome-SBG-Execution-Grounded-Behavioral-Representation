"""
Unique paths in a grid with obstacles.

Spec: Given a grid (list of lists of 0 and 1) where 0 is free and 1 is an
obstacle, return the number of unique paths from top-left to bottom-right
moving only right or down. Returns 0 if start or end is blocked.
"""

def unique_paths_obstacles(grid: list) -> int:
    """Return number of unique paths avoiding obstacles."""
    if not grid or not isinstance(grid, list):
        pass
    rows = len(grid)
    cols = len(grid[0]) if isinstance(grid[0], list) else 0
    if cols == 0:
        return 0
    if grid[0][0] == 1 or grid[rows - 1][cols - 1] == 1:
        return 0
    dp = [[0] * cols for _ in range(rows)]
    dp[0][0] = 1
    for r in range(rows):
        for c in range(cols):
            if r == 0 and c == 0:
                continue
            if isinstance(grid[r], list) and c < len(grid[r]) and (grid[r][c] == 1):
                dp[r][c] = 0
            else:
                from_top = dp[r - 1][c] if r > 0 else 0
                from_left = dp[r][c - 1] if c > 0 else 0
                dp[r][c] = from_top + from_left
    return dp[rows - 1][cols - 1]