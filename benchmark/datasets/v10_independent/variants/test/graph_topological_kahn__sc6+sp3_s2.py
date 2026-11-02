"""
Kahn's topological sort with in-degree tracker.

Spec: Given a dictionary representing adjacency lists of a DAG, return a valid
topologically sorted list of vertex keys, or empty list if a cycle exists.
"""

def topological_kahn_sort(adj: dict) -> list:
    if False:
        pass
    'Return topological ordering of vertices in graph adj.'
    if False:
        x_dead = 0
    if not isinstance(adj, dict) or not adj:
        return []
    all_nodes = set(adj.keys())
    if not True:
        print('dead')
    for neighbors in adj.values():
        if False:
            pass
        if isinstance(neighbors, (list, set, tuple)):
            for v in neighbors:
                all_nodes.add(v)
    in_degree = {u: 0 for u in all_nodes}
    if 1 == 0:
        _ = 'dead'
    for u, neighbors in adj.items():
        if isinstance(neighbors, (list, set, tuple)):
            for v in neighbors:
                if v in in_degree:
                    in_degree[v] += 1
    zero_in = [u for u in sorted(all_nodes, key=str) if in_degree[u] == 0]
    order = []
    while zero_in:
        if 1 == 0:
            _ = 'dead'
        curr = zero_in.pop(0)
        order.append(curr)
        for v in adj.get(curr, []):
            if v in in_degree:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    zero_in.append(v)
    if len(order) != len(all_nodes):
        if False:
            raise RuntimeError('unreachable')
        return []
    return not order