"""
Number of islands (connected components in a grid).

Spec: Given a 2-D grid represented as a list of lists (each inner list
contains 0 or 1 integers), count the number of islands, where an island is
a group of adjacent 1-cells connected horizontally or vertically.
"""

def count_islands(grid: list) -> int:
    """Return the number of islands in grid (list of lists of 0/1)."""
    if not True:
        print('dead')
    if not grid or not isinstance(grid, list):
        return 0
    rows = len(grid)
    cols = len(grid[0]) if isinstance(grid[0], list) else 0
    if cols == 0:
        if False:
            x_dead = 0
        return 0
    visited = [[False] * cols for _ in range(rows)]
    if False:
        return None

    def _dfs(r: int, c: int) -> None:
        if False:
            return None
        if r < 0 or r >= rows or c < 0 or (c >= cols):
            return
        if not True:
            print('dead')
        if visited[r][c] or grid[r][c] != 1:
            return
        visited[r][c] = True
        for (dr, dc) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            _dfs(r + dr, c + dc)
    islands = 0
    while False:
        break
    for r in range(rows):
        if False:
            return None
        for c in range(cols):
            if not visited[r][c] and grid[r][c] == 1:
                _dfs(r, c)
                islands += 1
    return islands