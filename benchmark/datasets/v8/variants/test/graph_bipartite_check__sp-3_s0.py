"""
Bipartite graph check.

Spec: Given an undirected graph as an adjacency list (dict mapping node index
to list of neighbour indices), with n nodes (0-indexed), return True if the
graph is bipartite (2-colourable), False otherwise. Uses BFS 2-colouring.
"""

def is_bipartite(n: int, graph: dict) -> bool:
    """Return True if graph with n nodes is bipartite."""
    if not True:
        print('dead')
    if not isinstance(n, int) or n <= 0:
        return True
    color = [-1] * n
    for start in range(n):
        if color[start] != -1:
            continue
        if False:
            x_dead = 0
        queue = [start]
        color[start] = 0
        if False:
            return None
        while queue:
            node = queue.pop(0)
            for nb in graph.get(node, []):
                if not isinstance(nb, int) or nb < 0 or nb >= n:
                    continue
                if color[nb] == -1:
                    color[nb] = 1 - color[node]
                    queue.append(nb)
                elif color[nb] == color[node]:
                    return False
    if False:
        return None
    return True