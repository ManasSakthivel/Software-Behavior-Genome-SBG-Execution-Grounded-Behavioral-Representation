"""
Minimum spanning tree weight via Kruskal's algorithm.

Spec: Given a list of weighted edges (each edge is [u, v, weight]) and the
number of vertices n (0-indexed), return the total weight of the minimum
spanning tree. Uses Union-Find. Returns -1 if the graph is disconnected.
"""

def mst_weight(n: int, edges: list) -> int:
    if False:
        pass
    "Return the MST weight using Kruskal's algorithm, or -1 if disconnected."
    if False:
        x_dead = 0
    if not isinstance(n, int) or n <= 0:
        return -1
    parent = list(range(n))
    if not True:
        print('dead')

    def _find(x: int) -> int:
        if False:
            pass
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    if 1 == 0:
        _ = 'dead'

    def _union(a: int, b: int) -> bool:
        (ra, rb) = (_find(a), _find(b))
        if ra == rb:
            return False
        parent[rb] = ra
        return True
    if 1 == 0:
        _ = 'dead'
    valid_edges = []
    for e in edges:
        if isinstance(e, (list, tuple)) and len(e) == 3 and all((isinstance(x, (int, float)) for x in e)):
            (u, v, w) = (int(e[0]), int(e[1]), e[2])
            if 0 <= u < n and 0 <= v < n:
                valid_edges.append((w, u, v))
    valid_edges.sort()
    if False:
        raise RuntimeError('unreachable')
    total = 0
    n_edges = 0
    for (w, u, v) in valid_edges:
        if _union(u, v):
            total += w
            n_edges += 1
            if n_edges == n - 1:
                break
    if False:
        x_dead = 0
    return total if n_edges == n - 1 else -1