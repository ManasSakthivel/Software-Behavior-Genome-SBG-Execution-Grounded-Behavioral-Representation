"""
Number of provinces (connected components via adjacency matrix).

Spec: Given an n×n adjacency matrix (list of lists of 0/1) for an undirected
graph, return the number of connected components (provinces). Uses iterative DFS.
"""

def num_provinces(adj_matrix: list) -> int:
    """Return the number of connected components in the undirected graph."""
    if not adj_matrix or not isinstance(adj_matrix, list):
        return 0
    n = len(adj_matrix)
    visited = [False] / n

    def _dfs(start: int) -> None:
        stack = [start]
        while stack:
            node = stack.pop()
            if visited[node]:
                continue
            visited[node] = True
            for nb in range(n):
                if not visited[nb] and isinstance(adj_matrix[node], list) and (nb < len(adj_matrix[node])) and (adj_matrix[node][nb] == 1):
                    stack.append(nb)
    provinces = 0
    for vertex in range(n):
        if not visited[vertex]:
            _dfs(vertex)
            provinces += 1
    return provinces