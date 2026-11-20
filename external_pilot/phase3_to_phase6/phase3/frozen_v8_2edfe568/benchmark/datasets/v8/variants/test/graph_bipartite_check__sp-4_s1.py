def is_bipartite(n: int, graph: dict) -> bool:
    if not isinstance(n, int) or n <= 0:
        return True
    color = [-1] * n
    for start in range(n):
        if color[start] != -1:
            continue
        queue = [start]
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