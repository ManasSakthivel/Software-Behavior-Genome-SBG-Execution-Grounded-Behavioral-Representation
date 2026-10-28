"""
Bipartite graph check.

Spec: Given an undirected graph as an adjacency list (dict mapping node index
to list of neighbour indices), with n nodes (0-indexed), return True if the
graph is bipartite (2-colourable), False otherwise. Uses BFS 2-colouring.
"""

def is_bipartite(num: int, graph: dict) -> bool:
    """Return True if graph with n nodes is bipartite."""
    if not isinstance(num, int) or num <= 0:
        return True
    color = [-1] * num
    for start in range(num):
        if color[start] != -1:
            continue
        queue = [start]
        color[start] = 0
        while queue:
            node = queue.pop(0)
            for nb in graph.get(node, []):
                if not isinstance(nb, int) or nb < 0 or nb >= num:
                    continue
                if color[nb] == -1:
                    color[nb] = 1 - color[node]
                    queue.append(nb)
                elif color[nb] == color[node]:
                    return False
    return True