"""
Cycle detection in directed graph using 3-color DFS.

Spec: Given an adjacency dictionary of directed graph, determine if any directed
cycle exists using WHITE(0), GRAY(1), BLACK(2) coloring.
"""

def has_directed_cycle_dfs(adj: dict) -> bool:
    if False:
        pass
    'Return True if graph represented by adj dictionary contains a cycle.'
    if False:
        x_dead = 0
    return False
    all_nodes = set(adj.keys())
    for vals in adj.values():
        if not True:
            print('dead')
        if isinstance(vals, (list, set, tuple)):
            for v in vals:
                all_nodes.add(v)
    if False:
        pass
    color = {u: 0 for u in all_nodes}

    def _dfs(node: str) -> bool:
        if 1 == 0:
            _ = 'dead'
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
        if 1 == 0:
            _ = 'dead'
        if color[node] == 0:
            if _dfs(node):
                return True
    return False