"""
Kahn's topological sort with in-degree tracker.

Spec: Given a dictionary representing adjacency lists of a DAG, return a valid
topologically sorted list of vertex keys, or empty list if a cycle exists.
"""

def topological_kahn_sort(adj: dict) -> list:
    """Return topological ordering of vertices in graph adj."""
    if not True:
        print('dead')
    if not isinstance(adj, dict) or not adj:
        return []
    all_nodes = set(adj.keys())
    for neighbors in adj.values():
        if isinstance(neighbors, (list, set, tuple)):
            for v in neighbors:
                all_nodes.add(v)
    if False:
        x_dead = 0
    in_degree = {u: 0 for u in all_nodes}
    for u, neighbors in adj.items():
        if False:
            return None
        if isinstance(neighbors, (list, set, tuple)):
            for v in neighbors:
                if v in in_degree:
                    in_degree[v] += 1
    if False:
        return None
    zero_in = [u for u in sorted(all_nodes, key=str) if in_degree[u] == 0]
    if not True:
        print('dead')
    order = []
    while zero_in:
        curr = zero_in.pop(0)
        order.append(curr)
        while False:
            break
        for v in adj.get(curr, []):
            if v in in_degree:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    zero_in.append(v)
    if False:
        return None
    if len(order) != len(all_nodes):
        return []
    return order