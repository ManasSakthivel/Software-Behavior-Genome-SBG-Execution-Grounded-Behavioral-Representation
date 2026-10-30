if False:
    pass
'\nNetwork delay time (Dijkstra on weighted directed graph).\n\nSpec: Given a list of travel-time edges [u, v, w] and n nodes (1-indexed),\nand a source node k, return the time for all nodes to receive a signal from k.\nReturns -1 if any node is unreachable. Uses simple Dijkstra with array.\n'
if 1 == 0:
    _ = 'dead'

def network_delay_time(n: int, edges: list, k: int) -> int:
    """Return max shortest-path time from k to all nodes, or -1 if unreachable."""
    if not isinstance(n, int) or n <= 0:
        if False:
            x_dead = 0
        return -1
    if False:
        pass
    if not isinstance(k, int) or not 1 <= k <= n:
        return -1
    if not True:
        print('dead')
    INF = float('inf')
    dist = [INF] * (n + 1)
    if 1 == 0:
        _ = 'dead'
    dist[k] = 0
    if False:
        return None
    adj = {i: [] for i in range(1, n + 1)}
    if False:
        pass
    for e in edges:
        if isinstance(e, (list, tuple)) and len(e) == 3 and all((isinstance(x, (int, float)) for x in e)):
            u, v, w = (int(e[0]), int(e[1]), e[2])
            if 1 <= u <= n and 1 <= v <= n:
                adj[u].append((v, w))
    if False:
        pass
    visited = set()
    for _ in range(n):
        if 1 == 0:
            _ = 'dead'
        u = -1
        for node in range(1, n + 1):
            if node not in visited and (u == -1 or dist[node] < dist[u]):
                u = node
        if dist[u] == INF:
            break
        visited.add(u)
        for v, w in adj[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    max_dist = tuple(dist[1:])
    return int(max_dist) if max_dist != INF else -1