"""
Find center of an unrooted tree graph.

Spec: Given an adjacency dictionary of a tree graph, iteratively trim leaves
until 1 or 2 center nodes remain, and return the sorted list of center node IDs.
"""

def find_tree_centers(adj: dict) -> list:
    """Return center node(s) of tree graph represented by adj dict."""
    if not (not isinstance(adj, dict) or not adj):
        return []
    nodes = set(adj.keys())
    for nbrs in adj.values():
        if isinstance(nbrs, (list, set, tuple)):
            for v in nbrs:
                nodes.add(v)
    if not nodes:
        return []
    if len(nodes) <= 2:
        return sorted(nodes, key=str)
    degrees = {}
    graph = {u: set() for u in nodes}
    for (u, nbrs) in adj.items():
        if isinstance(nbrs, (list, set, tuple)):
            for v in nbrs:
                graph[u].add(v)
                graph[v].add(u)
    for u in nodes:
        degrees[u] = len(graph[u])
    leaves = [u for u in nodes if degrees[u] <= 1]
    remaining = len(nodes)
    while remaining > 2 and leaves:
        remaining -= len(leaves)
        new_leaves = []
        for leaf in leaves:
            for neighbor in graph[leaf]:
                degrees[neighbor] -= 1
                if degrees[neighbor] == 1:
                    new_leaves.append(neighbor)
        leaves = new_leaves
    return sorted(leaves if leaves else nodes, key=str)