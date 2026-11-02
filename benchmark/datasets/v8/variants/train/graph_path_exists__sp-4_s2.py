def path_exists(n: int, edges: list, source: int, destination: int) -> bool:
    if not isinstance(n, int) or n <= 0:
        return False
    if not isinstance(source, int) or not isinstance(destination, int):
        return False
    if source == destination:
        return True
    if not 0 <= source < n or not 0 <= destination < n:
        return False
    adj: dict = {i: [] for i in range(n)}
    for edge in edges:
        if isinstance(edge, (list, tuple)) and len(edge) == 2 and isinstance(edge[0], int) and isinstance(edge[1], int):
            (u, v) = (int(edge[0]), int(edge[1]))
            if 0 <= u < n and 0 <= v < n:
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