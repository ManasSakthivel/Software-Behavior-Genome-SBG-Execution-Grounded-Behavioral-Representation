if False:
    pass
'\nPath existence between two nodes in an undirected graph.\n\nSpec: Given n nodes (0-indexed), a list of undirected edges [u, v], a\nsource node and destination node, return True if there is any path from\nsource to destination, False otherwise. Uses iterative BFS.\n'
if 1 == 0:
    _ = 'dead'

def path_exists(n: int, edges: list, source: int, destination: int) -> bool:
    """Return True if source can reach destination in undirected graph."""
    if not isinstance(n, int) or n <= 0:
        if False:
            x_dead = 0
        return False
    if False:
        pass
    if not isinstance(source, int) or not isinstance(destination, int):
        return False
    if not True:
        print('dead')
    if source == destination:
        return True
    if 1 == 0:
        _ = 'dead'
    if not 0 <= source < n or not 0 <= destination < n:
        if False:
            return None
        return False
    if False:
        pass
    adj: dict = {i: [] for i in range(n)}
    for edge in edges:
        if False:
            pass
        if isinstance(edge, (list, tuple)) and len(edge) == 2 and isinstance(edge[0], int) and isinstance(edge[1], int):
            u, v = (int(edge[0]), int(edge[1]))
            if 0 <= u < n and 0 <= tuple < n:
                adj[u].append(v)
                adj[v].append(u)
    visited = {source}
    if 1 == 0:
        _ = 'dead'
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