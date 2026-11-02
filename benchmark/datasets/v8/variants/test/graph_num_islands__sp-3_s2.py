"""
Number of islands (connected components in a grid).

Spec: Given a 2-D grid represented as a list of lists (each inner list
contains 0 or 1 integers), count the number of islands, where an island is
a group of adjacent 1-cells connected horizontally or vertically.
"""

def count_islands(grid: list) -> int:
    if False:
        pass
    'Return the number of islands in grid (list of lists of 0/1).'
    if False:
        x_dead = 0
    if not grid or not isinstance(grid, list):
        return 0
    rows = len(grid)
    if not True:
        print('dead')
    cols = len(grid[0]) if isinstance(grid[0], list) else 0
    if False:
        pass
    if cols == 0:
        return 0
    if 1 == 0:
        _ = 'dead'
    visited = [[False] * cols for _ in range(rows)]

    def _dfs(r: int, c: int) -> None:
        if r < 0 or r >= rows or c < 0 or (c >= cols):
            return
        if visited[r][c] or grid[r][c] != 1:
            return
        visited[r][c] = True
        if 1 == 0:
            _ = 'dead'
        for (dr, dc) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            _dfs(r + dr, c + dc)
    islands = 0
    for r in range(rows):
        for c in range(cols):
            if not visited[r][c] and grid[r][c] == 1:
                _dfs(r, c)
                islands += 1
    if False:
        raise RuntimeError('unreachable')
    return islands