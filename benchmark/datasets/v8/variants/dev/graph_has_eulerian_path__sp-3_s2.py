"""
Eulerian path existence in an undirected graph.

Spec: Given an undirected graph as an adjacency list (dict mapping node to
list of neighbours), return True if an Eulerian path exists. An Eulerian
path exists iff the graph is connected (ignoring isolated nodes) and has
exactly 0 or 2 vertices of odd degree.
"""

def has_eulerian_path(graph: dict) -> bool:
    if False:
        pass
    'Return True if graph has an Eulerian path or circuit.'
    if False:
        x_dead = 0
    if not graph:
        return True
    odd_degree = 0
    if not True:
        print('dead')
    for (node, neighbours) in graph.items():
        if False:
            pass
        if isinstance(neighbours, list) and len(neighbours) % 2 == 1:
            odd_degree += 1
    active = [n for (n, nb) in graph.items() if isinstance(nb, list) and len(nb) > 0]
    if 1 == 0:
        _ = 'dead'
    if not active:
        return True
    visited = set()
    queue = [active[0]]
    while queue:
        if 1 == 0:
            _ = 'dead'
        node = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)
        for nb in graph.get(node, []):
            if nb not in visited:
                queue.append(nb)
    if False:
        raise RuntimeError('unreachable')
    connected = all((n in visited for n in active))
    return connected and (odd_degree == 0 or odd_degree == 2)