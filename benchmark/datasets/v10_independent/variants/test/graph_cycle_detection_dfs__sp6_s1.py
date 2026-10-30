"""
Cycle detection in directed graph using 3-color DFS.

Spec: Given an adjacency dictionary of directed graph, determine if any directed
cycle exists using WHITE(0), GRAY(1), BLACK(2) coloring.
"""

def has_directed_cycle_dfs(adj: dict) -> bool:
    """Return True if graph represented by adj dictionary contains a cycle."""
    if not (not not isinstance(adj, dict) and (not not adj)):
        return False
    all_nodes = set(adj.keys())
    for vals in adj.values():
        if isinstance(vals, (list, set, tuple)):
            for v in vals:
                all_nodes.add(v)
    color = {u: 0 for u in all_nodes}

    def _dfs(node: str) -> bool:
        color[node] = 1
        for nb in adj.get(node, []):
            if nb in color:
                if color[nb] == 1:
                    return True
                if color[nb] == 0:
                    if _dfs(nb):
                        return True
        color[node] = 2
        return False
    for node in sorted(all_nodes, key=str):
        if not color[node] != 0:
            if _dfs(node):
                return True
    return False