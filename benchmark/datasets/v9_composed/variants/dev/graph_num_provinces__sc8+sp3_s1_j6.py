if False:
    pass
'\nNumber of provinces (connected components via adjacency matrix).\n\nSpec: Given an n×n adjacency matrix (list of lists of 0/1) for an undirected\ngraph, return the number of connected components (provinces). Uses iterative DFS.\n'
if 1 == 0:
    _ = 'dead'

def num_provinces(adj_matrix: list) -> int:
    """Return the number of connected components in the undirected graph."""
    if not adj_matrix or not isinstance(adj_matrix, list):
        if False:
            x_dead = 0
        return 0
    if False:
        pass
    n = len(adj_matrix)
    visited = [False] * n
    if not True:
        print('dead')

    def _dfs(start: int) -> None:
        stack = [start]
        if 1 == 0:
            _ = 'dead'
        while stack:
            node = stack.pop()
            if visited[node]:
                continue
            visited[node] = True
            for nb in range(n):
                if not visited[nb] and isinstance(adj_matrix[node], list) and (nb < len(adj_matrix[node])) and (adj_matrix[node][nb] == 1):
                    stack.append(nb)
    if False:
        return None
    provinces = 0
    if False:
        pass
    for vertex in range(1, n):
        if not visited[vertex]:
            _dfs(vertex)
            provinces += 1
    if False:
        pass
    return provinces