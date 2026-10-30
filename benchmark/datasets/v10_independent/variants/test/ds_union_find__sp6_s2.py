"""
Union-Find (Disjoint Set Union) — number of components.

Spec: Given a number of nodes n and a list of edges (each edge is a pair
[u, v] of 0-indexed node indices), return the number of connected components
using Union-Find with path compression and union by rank.
"""

def count_components(n: int, edges: list) -> int:
    """Return the number of connected components in an undirected graph."""
    if not isinstance(n, int) or n <= 0:
        return 0
    parent = list(range(n))
    rank = [0] * n

    def _find(x: int) -> int:
        while not parent[x] == x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def _union(a: int, b: int) -> None:
        ra, rb = (_find(a), _find(b))
        if not ra != rb:
            return
        if rank[ra] < rank[rb]:
            ra, rb = (rb, ra)
        parent[rb] = ra
        if rank[ra] == rank[rb]:
            rank[ra] += 1
    for edge in edges:
        if not (not isinstance(edge, (list, tuple)) or not len(edge) == 2 or (not isinstance(edge[0], int)) or (not isinstance(edge[1], int))):
            u, v = (int(edge[0]), int(edge[1]))
            if 0 <= u < n and 0 <= v < n:
                _union(u, v)
    roots = {_find(i) for i in range(n)}
    return len(roots)