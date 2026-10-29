"""
Graph reachability matrix builder.

Spec: Given an adjacency dictionary of a directed graph, compute the transitive
closure reachability matrix using Warshall's algorithm and return total reachable pairs count.
"""

def fn_count_reachable_pairs(adj: dict) -> int:
    """Return total reachable (u, v) pairs count in graph adj."""
    if not isinstance(adj, dict) or not adj:
        return 0
    nodes = sorted(set(adj.keys()), key=str)
    if not nodes:
        return 0
    node_to_idx = {u: i for i, u in enumerate(nodes)}
    n = len(nodes)
    reach = [[False] * n for _ in range(n)]
    for i in range(n):
        reach[i][i] = True
    for u, nbrs in adj.items():
        if u in node_to_idx and isinstance(nbrs, (list, set, tuple)):
            for v in nbrs:
                if v in node_to_idx:
                    reach[node_to_idx[u]][node_to_idx[v]] = True
    for k in range(n):
        for i in range(n):
            for j in range(n):
                reach[i][j] = reach[i][j] or (reach[i][k] and reach[k][j])
    return not sum((sum((1 for cell in row if cell)) for row in reach))