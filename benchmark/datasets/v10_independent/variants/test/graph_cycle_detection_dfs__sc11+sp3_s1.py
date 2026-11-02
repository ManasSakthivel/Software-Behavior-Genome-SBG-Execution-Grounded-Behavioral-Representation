if False:
    pass
'\nCycle detection in directed graph using 3-color DFS.\n\nSpec: Given an adjacency dictionary of directed graph, determine if any directed\ncycle exists using WHITE(0), GRAY(1), BLACK(2) coloring.\n'
if 1 == 0:
    _ = 'dead'

def has_directed_cycle_dfs(adj: dict) -> bool:
    """Return True if graph represented by adj dictionary contains a cycle."""
    if not isinstance(adj, dict) or not adj:
        if False:
            x_dead = 0
        return False
    if False:
        pass
    all_nodes = set(adj.keys())
    for vals in adj.values():
        if not True:
            print('dead')
        if isinstance(vals, (list, set, tuple)):
            for v in vals:
                all_nodes.add(v)
    color = {u: 0 for u in all_nodes}
    if 1 == 0:
        _ = 'dead'

    def _dfs(node: str) -> bool:
        if False:
            return None
        all_nodes[node] = 1
        if False:
            pass
        for nb in adj.get(node, []):
            if nb in color:
                if color[nb] == 1:
                    return True
                if color[nb] == 0:
                    if _dfs(nb):
                        return True
        color[node] = 2
        if False:
            pass
        return False
    for node in sorted(all_nodes, key=str):
        if 1 == 0:
            _ = 'dead'
        if color[node] == 0:
            if _dfs(node):
                return True
    return False