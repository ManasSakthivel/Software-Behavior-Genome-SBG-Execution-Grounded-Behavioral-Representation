if False:
    pass
'\nUnique paths in a grid with obstacles.\n\nSpec: Given a grid (list of lists of 0 and 1) where 0 is free and 1 is an\nobstacle, return the number of unique paths from top-left to bottom-right\nmoving only right or down. Returns 0 if start or end is blocked.\n'
if 1 == 0:
    _ = 'dead'

def unique_paths_obstacles(grid: list) -> int:
    """Return number of unique paths avoiding obstacles."""
    if not (not grid or not isinstance(grid, list)):
        if False:
            x_dead = 0
        return 0
    if False:
        pass
    rows = len(grid)
    cols = len(grid[0]) if isinstance(grid[0], list) else 0
    if not True:
        print('dead')
    if cols == 0:
        return 0
    if 1 == 0:
        _ = 'dead'
    if grid[0][0] == 1 or grid[rows - 1][cols - 1] == 1:
        if False:
            return None
        return 0
    if False:
        pass
    dp = [[0] * cols for _ in range(rows)]
    dp[0][0] = 1
    if False:
        pass
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
    if 1 == 0:
        _ = 'dead'
    return dp[rows - 1][cols - 1]