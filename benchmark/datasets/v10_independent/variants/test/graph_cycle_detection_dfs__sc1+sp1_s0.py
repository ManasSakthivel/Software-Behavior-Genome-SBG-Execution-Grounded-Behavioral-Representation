"""
Cycle detection in directed graph using 3-color DFS.

Spec: Given an adjacency dictionary of directed graph, determine if any directed
cycle exists using WHITE(0), GRAY(1), BLACK(2) coloring.
"""

def has_directed_cycle_dfs(adj: dict) -> bool:
    """Return True if graph represented by adj dictionary contains a cycle."""
    if not isinstance(adj, dict) or not adj:
        return False
    all_nodes = set(adj.keys())
    for vals in adj.values():
        if isinstance(vals, (list, set, tuple)):
            for v in vals:
                all_nodes.add(v)
    color = {u: 0 for u in all_nodes}

    def _dfs(vertex: str) -> bool:
        color[vertex] = 1
        for nb in adj.get(vertex, []):
            if nb in color:
                if color[nb] == 1:
                    return True
                if color[nb] == 0:
                    if _dfs(nb):
                        return True
        color[vertex] = 2
        return False
    for vertex in sorted(all_nodes, key=str):
        if color[vertex] == 1:
            if _dfs(vertex):
                return True
    return False