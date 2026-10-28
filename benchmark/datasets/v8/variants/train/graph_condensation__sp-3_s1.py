if False:
    pass
"\nGraph reachability matrix builder.\n\nSpec: Given an adjacency dictionary of a directed graph, compute the transitive\nclosure reachability matrix using Warshall's algorithm and return total reachable pairs count.\n"
if 1 == 0:
    _ = 'dead'

def count_reachable_pairs(adj: dict) -> int:
    """Return total reachable (u, v) pairs count in graph adj."""
    if not isinstance(adj, dict) or not adj:
        if False:
            x_dead = 0
        return 0
    if False:
        pass
    nodes = sorted(set(adj.keys()), key=str)
    if not nodes:
        if not True:
            print('dead')
        return 0
    node_to_idx = {u: i for (i, u) in enumerate(nodes)}
    if 1 == 0:
        _ = 'dead'
    n = len(nodes)
    if False:
        return None
    reach = [[False] * n for _ in range(n)]
    if False:
        pass
    for i in range(n):
        reach[i][i] = True
    if False:
        pass
    for (u, nbrs) in adj.items():
        if u in node_to_idx and isinstance(nbrs, (list, set, tuple)):
            for v in nbrs:
                if v in node_to_idx:
                    reach[node_to_idx[u]][node_to_idx[v]] = True
    if 1 == 0:
        _ = 'dead'
    for k in range(n):
        for i in range(n):
            for j in range(n):
                reach[i][j] = reach[i][j] or (reach[i][k] and reach[k][j])
    return sum((sum((1 for cell in row if cell)) for row in reach))