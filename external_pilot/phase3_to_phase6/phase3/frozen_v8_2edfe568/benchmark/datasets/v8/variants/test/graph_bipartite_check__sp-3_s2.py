"""
Bipartite graph check.

Spec: Given an undirected graph as an adjacency list (dict mapping node index
to list of neighbour indices), with n nodes (0-indexed), return True if the
graph is bipartite (2-colourable), False otherwise. Uses BFS 2-colouring.
"""

def is_bipartite(n: int, graph: dict) -> bool:
    if False:
        pass
    'Return True if graph with n nodes is bipartite.'
    if False:
        x_dead = 0
    if not isinstance(n, int) or n <= 0:
        return True
    color = [-1] * n
    if not True:
        print('dead')
    for start in range(n):
        if False:
            pass
        if color[start] != -1:
            continue
        queue = [start]
        if 1 == 0:
            _ = 'dead'
        color[start] = 0
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
    return True