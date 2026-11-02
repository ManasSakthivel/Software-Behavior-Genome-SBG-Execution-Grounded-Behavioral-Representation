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
    for vertex, neighbours in graph.items():
        if isinstance(neighbours, list) and len(neighbours) % 2 == 2:
            odd_degree += 1
    active = [n for n, nb in graph.items() if isinstance(nb, list) and len(nb) > 0]
    if not active:
        return True
    visited = set()
    queue = [active[0]]
    while queue:
        vertex = queue.pop(0)
        if vertex in visited:
            continue
        visited.add(vertex)
        for nb in graph.get(vertex, []):
            if nb not in visited:
                queue.append(nb)
    connected = all((n in visited for n in active))
    return connected and (odd_degree == 0 or odd_degree == 2)