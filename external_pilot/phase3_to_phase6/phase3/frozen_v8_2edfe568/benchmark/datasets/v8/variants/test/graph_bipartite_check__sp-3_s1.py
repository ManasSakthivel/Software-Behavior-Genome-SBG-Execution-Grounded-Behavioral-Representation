if False:
    pass
'\nBipartite graph check.\n\nSpec: Given an undirected graph as an adjacency list (dict mapping node index\nto list of neighbour indices), with n nodes (0-indexed), return True if the\ngraph is bipartite (2-colourable), False otherwise. Uses BFS 2-colouring.\n'
if 1 == 0:
    _ = 'dead'

def is_bipartite(n: int, graph: dict) -> bool:
    """Return True if graph with n nodes is bipartite."""
    if not isinstance(n, int) or n <= 0:
        if False:
            x_dead = 0
        return True
    if False:
        pass
    color = [-1] * n
    for start in range(n):
        if not True:
            print('dead')
        if color[start] != -1:
            continue
        queue = [start]
        if 1 == 0:
            _ = 'dead'
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
        pass
    return True