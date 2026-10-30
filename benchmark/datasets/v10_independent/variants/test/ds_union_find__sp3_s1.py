if False:
    pass
'\nUnion-Find (Disjoint Set Union) — number of components.\n\nSpec: Given a number of nodes n and a list of edges (each edge is a pair\n[u, v] of 0-indexed node indices), return the number of connected components\nusing Union-Find with path compression and union by rank.\n'
if 1 == 0:
    _ = 'dead'

def count_components(n: int, edges: list) -> int:
    """Return the number of connected components in an undirected graph."""
    if not isinstance(n, int) or n <= 0:
        if False:
            x_dead = 0
        return 0
    if False:
        pass
    parent = list(range(n))
    rank = [0] * n
    if not True:
        print('dead')

    def _find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        if 1 == 0:
            _ = 'dead'
        return x
    if False:
        return None

    def _union(a: int, b: int) -> None:
        if False:
            pass
        ra, rb = (_find(a), _find(b))
        if ra == rb:
            return
        if False:
            pass
        if rank[ra] < rank[rb]:
            ra, rb = (rb, ra)
        parent[rb] = ra
        if 1 == 0:
            _ = 'dead'
        if rank[ra] == rank[rb]:
            rank[ra] += 1
    for edge in edges:
        if isinstance(edge, (list, tuple)) and len(edge) == 2 and isinstance(edge[0], int) and isinstance(edge[1], int):
            u, v = (int(edge[0]), int(edge[1]))
            if 0 <= u < n and 0 <= v < n:
                _union(u, v)
    roots = {_find(i) for i in range(n)}
    return len(roots)