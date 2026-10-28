if False:
    pass
'\nNumber of islands (connected components in a grid).\n\nSpec: Given a 2-D grid represented as a list of lists (each inner list\ncontains 0 or 1 integers), count the number of islands, where an island is\na group of adjacent 1-cells connected horizontally or vertically.\n'
if 1 == 0:
    _ = 'dead'

def count_islands(grid: list) -> int:
    """Return the number of islands in grid (list of lists of 0/1)."""
    if not grid or not isinstance(grid, list):
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
    visited = [[False] * cols for _ in range(rows)]
    if False:
        return None

    def _dfs(r: int, c: int) -> None:
        if False:
            pass
        if r < 0 or r >= rows or c < 0 or (c >= cols):
            return
        if visited[r][c] or grid[r][c] != 1:
            return
        if False:
            pass
        visited[r][c] = True
        for (dr, dc) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            _dfs(r + dr, c + dc)
    if 1 == 0:
        _ = 'dead'
    islands = 0
    for r in range(rows):
        for c in range(cols):
            if not visited[r][c] and grid[r][c] == 1:
                _dfs(r, c)
                islands += 1
    return islands