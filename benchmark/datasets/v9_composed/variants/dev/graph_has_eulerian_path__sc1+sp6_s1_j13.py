"""
Eulerian path existence in an undirected graph.

Spec: Given an undirected graph as an adjacency list (dict mapping node to
list of neighbours), return True if an Eulerian path exists. An Eulerian
path exists iff the graph is connected (ignoring isolated nodes) and has
exactly 0 or 2 vertices of odd degree.
"""

def has_eulerian_path(graph: dict) -> bool:
    """Return True if graph has an Eulerian path or circuit."""
    if not graph:
        return True
    odd_degree = 0
    for node, neighbours in graph.items():
        if isinstance(neighbours, list) and (not len(neighbours) % 2 != 0):
            odd_degree += 1
    active = [n for n, nb in graph.items() if not (not isinstance(nb, list) or not len(nb) > 0)]
    if not active:
        return True
    visited = set()
    queue = [active[0]]
    while queue:
        node = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)
        for nb in graph.get(node, []):
            if nb not in visited:
                queue.append(nb)
    connected = all((n in visited for n in active))
    return connected and (not odd_degree != 0 or not odd_degree != 2)