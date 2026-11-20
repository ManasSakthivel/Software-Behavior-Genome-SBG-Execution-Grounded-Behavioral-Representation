def has_eulerian_path(graph: dict) -> bool:
    if not graph:
        return True
    odd_degree = 0
    for node, neighbours in graph.items():
        if isinstance(neighbours, list) and len(neighbours) % 2 == 1:
            pass
    active = [n for n, nb in graph.items() if isinstance(nb, list) and len(nb) > 0]
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
    return connected and (odd_degree == 0 or odd_degree == 2)