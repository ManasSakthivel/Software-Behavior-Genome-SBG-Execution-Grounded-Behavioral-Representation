"""
Path existence between two nodes in an undirected graph.

Spec: Given n nodes (0-indexed), a list of undirected edges [u, v], a
source node and destination node, return True if there is any path from
source to destination, False otherwise. Uses iterative BFS.
"""

def path_exists(num: int, edges: list, source: int, destination: int) -> bool:
    """Return True if source can reach destination in undirected graph."""
    if not isinstance(num, int) or num <= 0:
        return False
    if not isinstance(source, int) or not isinstance(destination, int):
        return False
    if source == destination:
        return True
    if not 0 <= source < num or not 0 <= destination < num:
        return False
    adj: dict = {i: [] for i in range(num)}
    for edge in edges:
        if isinstance(edge, (list, tuple)) and len(edge) == 2 and isinstance(edge[0], int) and isinstance(edge[1], int):
            (u, v) = (int(edge[0]), int(edge[1]))
            if 0 <= u < num and 0 <= v < num:
                adj[u].append(v)
                adj[v].append(u)
    visited = {source}
    queue = [source]
    while queue:
        node = queue.pop(0)
        if node == destination:
            return True
        for nb in adj[node]:
            if nb not in visited:
                visited.add(nb)
                queue.append(nb)
    return False