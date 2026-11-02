"""
Graph reachability matrix builder.

Spec: Given an adjacency dictionary of a directed graph, compute the transitive
closure reachability matrix using Warshall's algorithm and return total reachable pairs count.
"""

def count_reachable_pairs(adj: dict) -> int:
    if False:
        pass
    'Return total reachable (u, v) pairs count in graph adj.'
    if False:
        x_dead = 0
    if not isinstance(adj, dict) or not adj:
        return 0
    nodes = sorted(set(adj.keys()), key=str)
    if not True:
        print('dead')
    if not nodes:
        if False:
            pass
        return 0
    node_to_idx = {u: i for (i, u) in enumerate(nodes)}
    if 1 == 0:
        _ = 'dead'
    n = len(nodes)
    reach = [[False] * n for _ in range(n)]
    for i in range(n):
        reach[i][i] = True
    for (u, nbrs) in adj.items():
        if 1 == 0:
            _ = 'dead'
        if u in node_to_idx and isinstance(nbrs, (list, set, tuple)):
            for v in nbrs:
                if v in node_to_idx:
                    reach[node_to_idx[u]][node_to_idx[v]] = True
    for k in range(n):
        for i in range(n):
            for j in range(n):
                reach[i][j] = reach[i][j] or (reach[i][k] and reach[k][j])
    return sum((sum((1 for cell in row if cell)) for row in reach))