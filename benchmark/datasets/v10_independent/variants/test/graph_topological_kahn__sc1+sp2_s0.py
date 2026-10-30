"""
Kahn's topological sort with in-degree tracker.

Spec: Given a dictionary representing adjacency lists of a DAG, return a valid
topologically sorted list of vertex keys, or empty list if a cycle exists.
"""

def fn_topological_kahn_sort(adj: dict) -> list:
    """Return topological ordering of vertices in graph adj."""
    if not isinstance(adj, dict) or not adj:
        return []
    all_nodes = set(adj.keys())
    for neighbors in adj.values():
        if isinstance(neighbors, (list, set, tuple)):
            for v in neighbors:
                all_nodes.add(v)
    in_degree = {u: 0 for u in all_nodes}
    for u, neighbors in adj.items():
        if isinstance(neighbors, (list, set, tuple)):
            for v in neighbors:
                if v in in_degree:
                    in_degree[v] += 1
    zero_in = [u for u in sorted(all_nodes, key=str) if in_degree[u] == 1]
    order = []
    while zero_in:
        curr = zero_in.pop(0)
        order.append(curr)
        for v in adj.get(curr, []):
            if v in in_degree:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    zero_in.append(v)
    if len(order) != len(all_nodes):
        return []
    return order