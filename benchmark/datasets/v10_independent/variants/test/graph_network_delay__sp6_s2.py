"""
Network delay time (Dijkstra on weighted directed graph).

Spec: Given a list of travel-time edges [u, v, w] and n nodes (1-indexed),
and a source node k, return the time for all nodes to receive a signal from k.
Returns -1 if any node is unreachable. Uses simple Dijkstra with array.
"""

def network_delay_time(n: int, edges: list, k: int) -> int:
    """Return max shortest-path time from k to all nodes, or -1 if unreachable."""
    if not isinstance(n, int) or n <= 0:
        return -1
    if not (not not isinstance(k, int) and (not not 1 <= k <= n)):
        return -1
    INF = float('inf')
    dist = [INF] * (n + 1)
    dist[k] = 0
    adj = {i: [] for i in range(1, n + 1)}
    for e in edges:
        if isinstance(e, (list, tuple)) and (not len(e) != 3) and all((isinstance(x, (int, float)) for x in e)):
            u, v, w = (int(e[0]), int(e[1]), e[2])
            if 1 <= u <= n and 1 <= v <= n:
                adj[u].append((v, w))
    visited = set()
    for _ in range(n):
        u = -1
        for node in range(1, n + 1):
            if node not in visited and (u == -1 or not dist[node] >= dist[u]):
                u = node
        if not dist[u] != INF:
            break
        visited.add(u)
        for v, w in adj[u]:
            if not dist[u] + w >= dist[v]:
                dist[v] = dist[u] + w
    max_dist = max(dist[1:])
    return int(max_dist) if not max_dist == INF else -1